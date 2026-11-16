"""调机阶段（**业务数据**）—— 「这一轮处在调机的第几步」。

阶段 = **缺陷族**（要解决的问题），不是「工艺组」（注射 / 保压 / 计量…）。
划分依据（2026-11-12 拍板）：阶段的进入/达成信号必须是**可观测量**
（缺陷码 + 重量缺口），而"保压参数"不可观测 ⇒ 阶段按缺陷族划分。

三个阶段（用户口径：「先把产品打到差不多 → 再补缩 → 最后针对性处理外观缺陷」）：

===================  ==================  ==================================
阶段码                目标                归属缺陷码
===================  ==================  ==================================
``filling``           充填到位            ``SHORTSHOT``
``shrinking``         尺寸与形状达标      ``SHRINKAGE`` ``UNDERSIZE``
                                           ``OVERSIZE`` ``WARPING``
``appearance``        表面质量达标        其余 12 类（外观类）
===================  ==================  ==================================

⚠️ **阶段状态不落库** —— 阶段由**本轮反馈的缺陷构成**推导（纯函数）：
换模 / 轮次失败 / 反馈缺失都自动自愈，不会出现"状态卡在某一步"。
将来若要「人工锁定阶段」，再引入可空的 ``stage_override``（当前不建）。

⚠️ **本文件是业务知识（数据），不是逻辑** —— 缺陷码归属与阶段顺序都摆在这里。
:mod:`process.algorithms.defect_selection`（选哪个缺陷）与
:mod:`process.algorithms.strategies`（调什么）**共读同一份**，
才不会选出 A 阶段的缺陷却命中 B 阶段的策略。

⚠️ **未知缺陷码不臆造归属** —— 归到 :data:`UNKNOWN_STAGE`（排末位），
既不塞进已知阶段，也不丢。
"""

from typing import Any, List, Mapping, Optional, Sequence, Tuple

#: 阶段优先级（**升序 = 推进顺序**）：打足 → 补缩 → 外观。
STAGE_ORDER: Tuple[str, ...] = ('filling', 'shrinking', 'appearance')

#: 未知缺陷码的兜底阶段（排在所有已知阶段之后）。
UNKNOWN_STAGE: str = 'unknown'

#: 缺陷码 → 阶段（**17 类全覆盖**）。
DEFECT_STAGE: Mapping[str, str] = {
    # —— S1 打足（充填）——
    'SHORTSHOT': 'filling',
    # —— S2 补缩（尺寸与形状；根因在收缩与冷却，不是表面）——
    'SHRINKAGE': 'shrinking',
    'UNDERSIZE': 'shrinking',
    'OVERSIZE': 'shrinking',
    'WARPING': 'shrinking',
    # —— S3 外观（表面质量）——
    'WATERRIPPLE': 'appearance',
    'GASVEINS': 'appearance',
    'TOPWHITE': 'appearance',
    'HARDDEMOLDING': 'appearance',
    'ABERRATION': 'appearance',
    'WELDLINE': 'appearance',
    'FLASH': 'appearance',
    'AIRTRAP': 'appearance',
    'MATERIALFLOWER': 'appearance',
    'BURN': 'appearance',
    'GATEMARK': 'appearance',
    'SHADING': 'appearance',
}


def stage_of(defect_code: Optional[str]) -> str:
    """缺陷码 → 阶段码；未知或空 ⇒ :data:`UNKNOWN_STAGE`（不臆造归属）。"""
    if not defect_code:
        return UNKNOWN_STAGE
    return DEFECT_STAGE.get(str(defect_code), UNKNOWN_STAGE)


def stage_rank(stage: str) -> int:
    """阶段码 → 推进次序；未知阶段排**末位**（不早于任何已知阶段）。"""
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return len(STAGE_ORDER)


def order_defects(
    defects: Sequence[Any],
) -> List[Tuple[int, Any]]:
    """按阶段优先级给缺陷列表排序，返回 ``[(原始下标, 缺陷项), ...]``。

    - 阶段顺序见 :data:`STAGE_ORDER`；
    - **同阶段内保持原始顺序**（稳定排序 —— 同阶段缺陷的先后是用户的判断，不改）；
    - 无 ``keyword_name`` 的项与未知缺陷码归末位（**不丢**，交给选取环节跳过）。

    ⚠️ 返回**原始下标**是刻意的：留痕里的 ``index`` 要能指回用户提交的那一项，
    重排后的下标会指错位置。
    """
    decorated: List[Tuple[int, int, Any]] = []
    for index, item in enumerate(defects or ()):
        code = item.get('keyword_name') if isinstance(item, Mapping) else None
        decorated.append((stage_rank(stage_of(code)), index, item))
    decorated.sort(key=lambda row: (row[0], row[1]))
    return [(index, item) for _, index, item in decorated]


__all__ = [
    'DEFECT_STAGE',
    'STAGE_ORDER',
    'UNKNOWN_STAGE',
    'order_defects',
    'stage_of',
    'stage_rank',
]