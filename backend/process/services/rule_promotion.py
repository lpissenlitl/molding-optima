"""规则晋升 —— 把租户私库里的规则**移动**到全平台公共库。

⚠️ **为什么要有「晋升」这一步**
    挖掘审核通过后，规则先落在**租户自己的私库**里
    （`library_code='rule_miner'`，`owner_type='tenant'`）——
    只有该租户的试模推荐能用它。这是刻意的隔离：
    「某家厂试出来的经验」不等于「对所有人都成立的规律」。

    但经验一旦被验证（审核通过 + 多轮试模有效），就应该能反哺全平台。
    ⇒ 平台超管把验证过的规则**晋升**进公共库
    （`library_code='rule_miner_public'`，`owner_type='system'`），
    之后**所有租户**的试模推荐都会用上它。

⚠️ **晋升是「移动」不是「复制」**
    - **移动**：规则的 `rule_library` 改指向公共库 ⇒ 原私库不再保留该规则
      ⇒ 不会出现「私库一份 + 公共库一份」两条同内容规则同时生效
      （虽然算法侧有跨库去重，但两份数据会各改各的，溯源会失真）；
    - **`company_id` 保留原租户值**：规则自己仍记着「这条经验来自哪家公司」
      ⇒ 溯源信息不丢。**可见性只看库归属**（`owner_type` + 库的 `company_id`），
      规则的 `company_id` 不参与可见性判定 ⇒ 保留它不会造成越权可见。

⚠️ **只有平台超管能晋升**
    公共库是**全平台资产**：租户不得自助把自己的规则塞进公共库
    （否则任何租户都能把任意规则扩散给所有租户）。
    ⇒ view 层 `require_superuser`，service 层再校验一次（双保险：
    service 可能被内部脚本 / 其它 view 直接调用）。

⚠️ **只晋升「租户私库里的模糊规则」**
    - 库类型必须是 `fuzzy` —— 专家规则（`ExpertRule`）走的是另一条链路
      （`ExpertMatcher` / 初始化系数），本模块不碰；
    - 库归属必须是 `tenant` —— 已经在系统库（含公共库）里的规则无需晋升
      （重复晋升只会制造无意义的写入）。
"""

import logging
from typing import Dict, Iterable, List, Optional

from django.db import transaction

from extensions.exceptions import (
    BizException,
    ERROR_ACCESS_LIMIT,
    ERROR_ILLEGAL_ARGUMENT,
)
from process.models import RuleMethod
from process.services.mining_landing import ensure_public_mining_library


_logger = logging.getLogger(__name__)


def _normalize_ids(rule_method_ids: Optional[Iterable[int]]) -> List[int]:
    """把入参归一成去重后的正整数 id 列表（保持原顺序）。"""
    if not rule_method_ids:
        return []
    result: List[int] = []
    for raw in rule_method_ids:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise BizException(
                ERROR_ILLEGAL_ARGUMENT,
                f'规则 id 必须是整数: {raw!r}',
            )
        if value > 0 and value not in result:
            result.append(value)
    return result


@transaction.atomic
def promote_rules_to_public(
    rule_method_ids: Optional[Iterable[int]] = None,
    is_superuser: bool = False,
    operator: str = '',
) -> Dict:
    """把规则**移动**到公共库（全平台公用）。

    Args:
        rule_method_ids: 待晋升的 `RuleMethod` id 列表。
        is_superuser: 操作者是否平台超管（**必须为 True**）。
        operator: 操作者标识（仅用于日志留痕）。

    Returns:
        ```
        {
            'promoted_count': int,      # 实际晋升条数
            'promoted': [int],          # 晋升成功的规则 id
            'skipped': [                # 未晋升的项与原因
                {'rule_method_id': int, 'reason': str},
            ],
            'public_library': {...},    # 公共库档案（id / code / name）
        }
        ```

    Raises:
        BizException: 非平台超管（无权限）或入参非法。
    """
    # --- 1. 权限（service 层二次校验：不依赖调用方一定挂了装饰器）---
    if not is_superuser:
        raise BizException(
            ERROR_ACCESS_LIMIT,
            '仅平台超管可将规则晋升到公共库（公共库是全平台资产）',
        )

    # --- 2. 入参校验 ---
    ids = _normalize_ids(rule_method_ids)
    if not ids:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, '缺少必填字段: rule_method_ids')

    # --- 3. 取规则（带库，避免 N+1）---
    rules = list(
        RuleMethod.objects.filter(
            id__in=ids, is_deleted=False,
        ).select_related('rule_library')
    )
    found_ids = {r.id for r in rules}

    skipped: List[Dict] = []
    for missing in [i for i in ids if i not in found_ids]:
        skipped.append({
            'rule_method_id': missing,
            'reason': '规则不存在或已删除',
        })

    # --- 4. 逐条校验可否晋升 ---
    promotable: List[RuleMethod] = []
    for rule in rules:
        library = rule.rule_library
        if library.library_type != 'fuzzy':
            skipped.append({
                'rule_method_id': rule.id,
                'reason': (
                    f'所属库「{library.library_name}」是专家规则库，'
                    f'本动作只晋升模糊规则'
                ),
            })
            continue
        if library.owner_type != 'tenant':
            skipped.append({
                'rule_method_id': rule.id,
                'reason': (
                    f'所属库「{library.library_name}」已是系统级，'
                    f'无需晋升'
                ),
            })
            continue
        promotable.append(rule)

    if not promotable:
        return {
            'promoted_count': 0,
            'promoted': [],
            'skipped': skipped,
            'public_library': None,
        }

    # --- 5. 目标库（公共库，不存在则建）---
    public_library = ensure_public_mining_library()

    # --- 6. 移动（改库归属；company_id 保留原租户值作溯源）---
    promoted: List[int] = []
    for rule in promotable:
        origin_library = rule.rule_library
        rule.update_info(rule_library=public_library)
        promoted.append(rule.id)
        _logger.info(
            '[RulePromotion] 规则 %s 从库「%s」晋升到公共库「%s」（操作人: %s）',
            rule.id, origin_library.library_code,
            public_library.library_code, operator or '未知',
        )

    return {
        'promoted_count': len(promoted),
        'promoted': promoted,
        'skipped': skipped,
        'public_library': {
            'id': public_library.id,
            'library_code': public_library.library_code,
            'library_name': public_library.library_name,
            'owner_type': public_library.owner_type,
            'company_id': public_library.company_id,
        },
    }


__all__ = ['promote_rules_to_public']
