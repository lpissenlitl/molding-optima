"""候选规则审核流 service —— 列表 / 详情 / 通过 / 驳回。

审核流是「挖掘」与「生效」之间的闸门：

    MiningRule（候选，待审核）
        ↓ approve（管理员）
    RuleMethod（生效，参与试模推荐）

⚠️ **为什么审核与落地要分开两步**
    - 候选规则是**统计关联**（「缺陷 + 参数变更 ⇒ 结果」），未经人工确认
      不能直接当成**工艺因果**写进生效规则库；
    - 但「通过」必须**一步到位**地产生生效规则，否则审核人点完「通过」
      还要再去规则库手工建一条 —— 两步之间必然漂移（谁建、建成什么样）。

⚠️ **为什么「通过」要求规则一定能落地**
    落地翻译器会剔除三类规则：非正向后件（`unqualified` / `worse`）、
    没有参数变更、动作方向与当前档位相悖。
    这类规则「审核通过」在语义上是矛盾的（通过了却没生效）⇒
    服务层直接拒绝，**状态保持 pending**，让管理员去看详情里的落地预览。

⚠️ **租户隔离比规则主数据更严**
    规则关键词会把「系统演示公司」的公共词典并进来（`rule.get_list_of_rule_keyword`），
    但候选规则**必须严格按公司隔离** —— 挖掘语料来自本公司的调机流水，
    混入别家公司的规则既没有依据，也会让置信度失真。
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.db import transaction

from extensions.exceptions import (
    BizException,
    ERROR_ILLEGAL_ARGUMENT,
    ERROR_REQUIRED_FIELD,
)
from process.algorithms.mining.contracts import defect_level, defect_name, normalize_defect
from process.exceptions import (
    ERROR_MINING_RULE_NOT_FOUND,
    ERROR_MINING_RULE_NOT_LANDABLE,
    ERROR_MINING_RULE_REVIEWED,
)
from process.models import MiningRule
from process.services.mining_landing import build_landing_plan, land_mining_rule
from utils.db import parse_ordering, paginate_queryset


_logger = logging.getLogger(__name__)


#: 列表允许排序的字段（白名单，防 SQL 注入）
SORTABLE_FIELDS = {
    'id', 'rule_code', 'support', 'confidence', 'lift',
    'sample_count', 'status', 'created_at', 'updated_at', 'reviewed_at',
}

#: 允许的状态过滤值（与 `MiningRule.STATUS_CHOICES` 一致）
VALID_STATUS = ('pending', 'approved', 'rejected')

#: `landed_description` 字段长度上限（模型 max_length=500）
_LANDED_DESC_MAX = 500


# ============================================================================
# 查询
# ============================================================================

def _scope(queryset, company_id, is_superuser):
    """按公司隔离候选规则。

    ⚠️ **平台超管未接管时（company_id=None）看全部**；
       已接管则一律跟租户走（与 `rule.get_list_of_rule_keyword` 同口径，
       但**不并入系统演示公司** —— 候选规则是本公司挖掘产物）。
    """
    if is_superuser and company_id is None:
        return queryset
    return queryset.filter(company_id=company_id)


def _get_rule(mining_rule_id, company_id, is_superuser) -> MiningRule:
    """取候选规则（带租户隔离）。"""
    rule = _scope(
        MiningRule.objects.filter(id=mining_rule_id),
        company_id, is_superuser,
    ).first()
    if rule is None:
        raise BizException(
            ERROR_MINING_RULE_NOT_FOUND, f"id={mining_rule_id}",
        )
    return rule


def _defect_text(defects) -> str:
    """缺陷列表 → 人类可读文本（``SHORTSHOT(medium)、FLASH``）。"""
    parts: List[str] = []
    for item in defects or []:
        name = defect_name(item)
        if not name:
            continue
        level = defect_level(item)
        parts.append(f'{name}({level})' if level else name)
    return '、'.join(parts)


def serialize_mining_rule(rule: MiningRule, with_evidence: bool = False) -> Dict:
    """候选规则 → 字典（面向前端展示）。

    ⚠️ **不直接用 `to_dict()`**：那会把 `company_id` / `organization_id` /
       `is_deleted` 等内部字段一并吐给前端，且不提供 `defect_text`
       这类展示用聚合字段。
    """
    data = {
        'id': rule.id,
        'rule_code': rule.rule_code,
        'rule_hash': rule.rule_hash,
        'defects': [normalize_defect(d) for d in (rule.defects or [])],
        'defect_text': _defect_text(rule.defects),
        'changes': list(rule.changes or []),
        'consequent': rule.consequent,
        'support': rule.support,
        'confidence': rule.confidence,
        'lift': rule.lift,
        'sample_count': rule.sample_count,
        'corpus_cursor': rule.corpus_cursor,
        'status': rule.status,
        'reviewed_by': rule.reviewed_by,
        'reviewed_at': rule.reviewed_at,
        'review_note': rule.review_note,
        'landed_rule_method_id': rule.landed_rule_method_id,
        'landed_at': rule.landed_at,
        'landed_description': rule.landed_description,
        'landing_note': rule.landing_note,
        'created_at': rule.created_at,
        'updated_at': rule.updated_at,
    }
    if with_evidence:
        data['evidence'] = list(rule.evidence or [])
    return data


def get_mining_rule_list(
    company_id=None,
    is_superuser=False,
    status=None,
    consequent=None,
    keyword=None,
    page_no=1,
    page_size=30,
    sort='-id',
) -> Dict:
    """候选规则列表（审核台）。

    Args:
        company_id: 公司 id（None = 平台超管未接管）。
        is_superuser: 是否超级管理员。
        status: 状态过滤（pending / approved / rejected）。
        consequent: 后件过滤（qualified / unqualified / improved / worse）。
        keyword: 规则编号模糊搜索。
        page_no: 页码。
        page_size: 每页数量。
        sort: 排序（字段白名单见 `SORTABLE_FIELDS`）。

    Returns:
        ``{'total': n, 'items': [...]}``
    """
    if status and status not in VALID_STATUS:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            f"status 只能是 {'/'.join(VALID_STATUS)}，收到 {status}",
        )

    qs = _scope(MiningRule.objects.all(), company_id, is_superuser)
    if status:
        qs = qs.filter(status=status)
    if consequent:
        qs = qs.filter(consequent=consequent)
    if keyword:
        qs = qs.filter(rule_code__icontains=keyword)

    qs = qs.order_by(*parse_ordering(sort or '-id', allowed_fields=SORTABLE_FIELDS))
    pagination = paginate_queryset(qs, page_no, page_size)

    return {
        'total': pagination['total_count'],
        'items': [
            serialize_mining_rule(item) for item in pagination['items']
        ],
    }


def _resolve_company(rule: MiningRule, company_id) -> Optional[int]:
    """算档位要用的公司 id。

    ⚠️ **平台超管未接管时用规则自身的公司** ——
       `RuleKeyword`（量程 / 档位词表）是按公司登记的，
       用超管自己的 company_id（None）算会一条参数都查不到。
    """
    if company_id is not None:
        return company_id
    return rule.company_id


def build_landing_preview(rule: MiningRule, company_id=None) -> Dict:
    """落地预览（**不写库**）。

    让管理员在点「通过」之前看到：这条规则会变成哪几条生效规则、
    哪些条件被剔除了、为什么。

    Returns:
        ``{'landable': bool, 'rules': [...], 'skipped': [...]}``
    """
    target_company = _resolve_company(rule, company_id)
    if target_company is None:
        return {
            'landable': False,
            'rules': [],
            'skipped': [{
                'reason': '未归属公司',
                'detail': '该候选规则没有归属公司，无法计算参数档位',
            }],
        }

    plan = build_landing_plan(rule, target_company)
    return {
        'landable': plan.landable,
        'rules': plan.landing_rules,
        'skipped': plan.skipped,
    }


def get_mining_rule_detail(
    mining_rule_id,
    company_id=None,
    is_superuser=False,
) -> Dict:
    """候选规则详情（含证据与落地预览）。"""
    rule = _get_rule(mining_rule_id, company_id, is_superuser)
    data = serialize_mining_rule(rule, with_evidence=True)
    data['landing_preview'] = build_landing_preview(rule, company_id)
    return data


# ============================================================================
# 审核
# ============================================================================

def _assert_pending(rule: MiningRule) -> None:
    """审核态守卫 —— 只允许审核 pending 的规则。"""
    if rule.status != 'pending':
        raise BizException(
            ERROR_MINING_RULE_REVIEWED,
            f"规则 {rule.rule_code} 当前状态为 {rule.status}，不能重复审核",
        )


def _build_landing_note(plan, created) -> str:
    """落地说明（写入 `landing_note`）。"""
    parts = [f'落地 {len(created)} 条生效规则']
    if plan.skipped:
        reasons = '；'.join(
            f"{item.get('reason')}：{item.get('detail', '')}".rstrip('：')
            for item in plan.skipped
        )
        parts.append(f'跳过 {len(plan.skipped)} 项（{reasons}）')
    return '；'.join(parts)


def approve_mining_rule(
    mining_rule_id,
    company_id=None,
    is_superuser=False,
    reviewer='',
    note='',
) -> Dict:
    """通过候选规则 ⇒ 落地为 `RuleMethod`（`source='rule_miner'`）。

    ⚠️ **通过与落地在同一个事务里** —— 落地失败（翻译不出规则）
       就要整体回滚，状态保持 pending，不能出现「通过了但没生效」的中间态。

    Args:
        mining_rule_id: 候选规则 id。
        company_id: 公司 id。
        is_superuser: 是否超级管理员。
        reviewer: 审核人姓名。
        note: 审核意见。

    Returns:
        审核后的规则详情（含落地预览与落地的规则方法 id 列表）。
    """
    rule = _get_rule(mining_rule_id, company_id, is_superuser)
    _assert_pending(rule)

    target_company = _resolve_company(rule, company_id)
    if target_company is None:
        raise BizException(
            ERROR_MINING_RULE_NOT_LANDABLE,
            f"规则 {rule.rule_code} 没有归属公司，无法落地",
        )

    now = datetime.now()
    with transaction.atomic():
        created, plan = land_mining_rule(rule, target_company)
        if not created:
            reasons = '；'.join(
                f"{item.get('reason')}（{item.get('detail', '')}）"
                for item in plan.skipped
            ) or '未知原因'
            raise BizException(
                ERROR_MINING_RULE_NOT_LANDABLE,
                f"规则 {rule.rule_code} 无法落地：{reasons}",
            )

        descriptions = ' | '.join(item.rule_description for item in created)
        rule.status = 'approved'
        rule.reviewed_by = reviewer or ''
        rule.reviewed_at = now
        rule.review_note = note or ''
        rule.landed_rule_method_id = created[0].id
        rule.landed_at = now
        rule.landed_description = descriptions[:_LANDED_DESC_MAX]
        rule.landing_note = _build_landing_note(plan, created)[:_LANDED_DESC_MAX]
        rule.save(update_fields=[
            'status', 'reviewed_by', 'reviewed_at', 'review_note',
            'landed_rule_method_id', 'landed_at', 'landed_description',
            'landing_note', 'updated_at',
        ])

    _logger.info(
        '[mining/approve] 规则=%s 审核人=%s 落地=%s 条',
        rule.rule_code, rule.reviewed_by, len(created),
    )

    data = serialize_mining_rule(rule, with_evidence=True)
    data['landing_preview'] = build_landing_preview(rule, target_company)
    data['landed_rule_method_ids'] = [item.id for item in created]
    return data


def reject_mining_rule(
    mining_rule_id,
    company_id=None,
    is_superuser=False,
    reviewer='',
    note='',
) -> Dict:
    """驳回候选规则。

    ⚠️ **驳回必须写意见** —— 没有理由的驳回对规则挖掘没有反馈价值，
       也让候选规则表变成只进不出的黑洞。
    """
    rule = _get_rule(mining_rule_id, company_id, is_superuser)
    _assert_pending(rule)

    if not (note or '').strip():
        raise BizException(ERROR_REQUIRED_FIELD, '驳回时必须填写审核意见')

    rule.status = 'rejected'
    rule.reviewed_by = reviewer or ''
    rule.reviewed_at = datetime.now()
    rule.review_note = (note or '').strip()
    rule.save(update_fields=[
        'status', 'reviewed_by', 'reviewed_at', 'review_note', 'updated_at',
    ])

    _logger.info(
        '[mining/reject] 规则=%s 审核人=%s',
        rule.rule_code, rule.reviewed_by,
    )

    data = serialize_mining_rule(rule, with_evidence=True)
    data['landing_preview'] = build_landing_preview(rule, _resolve_company(rule, company_id))
    return data
