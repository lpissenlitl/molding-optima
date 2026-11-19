"""策略装配（编排层）—— 第2层的**数据供给**。

职责：从**调机策略模块**（:mod:`process.algorithms.tuning_strategy`）取业务知识，
组装成第2层要的数据形态：

- **实际情况**（``ScenarioContext``）：本轮的缺陷码、实测重量、目标重量、充填缺口
  （从反馈与模具上下文派生，不查库）；
- **命中哪个场景**（``ScenarioPolicy``）：条件求值 + 取第一条命中；
- **字段级优先级表**（``PriorityTable``）：随场景一起来（清单里自带）。

【注意】**清单里没有 ⇒ 不裁决**（行为与「不接第2层」完全一致）：
清单为空 / 无命中策略 ⇒ 场景与优先级表为空 ⇒ 第2层照旧不裁决。

【注意】**本模块不做业务判断** —— 「什么场景、调哪些、留几个」全在策略模块里；
本模块只负责取、匹配、组装。

【注意】**充填量目标不在这里算** —— 它是「结合实际情况算目标」，属第2层的职责
（:func:`process.algorithms.decide_direction.resolve_direction`）。
"""

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Optional

from process.algorithms.decide_direction import (
    PriorityTable,
    ScenarioContext,
    ScenarioPolicy,
    build_scenario_context,
    select_policy,
)
from process.algorithms.tuning_strategy import (
    StageProgress,
    derive_stage_progress,
    sorted_scenario_policies,
)


@dataclass(frozen=True)
class PolicyResolution:
    """策略解析的结果（供编排层直接喂给第2层）。

    Attributes:
        context: **实际情况**（缺陷码 / 实测重量 / 目标重量 / 充填缺口）。
        scenario: 命中的场景策略（``None`` = 无场景 ⇒ 不裁决）。
        priority_table: 字段级优先级表（空表 = 不按字段级排序）。
        stage_progress: **阶段进度**（本轮哪些阶段还有缺陷、当前该推进哪一步）。
            【注意】**只做推导，不做裁决** —— 由场景条件引用（如 ``filling_stage_first``）。
        trace: 留痕（场景码、命中条件、上下文摘要）。
    """

    context: ScenarioContext = field(default_factory=ScenarioContext)
    scenario: Optional[ScenarioPolicy] = None
    priority_table: Optional[PriorityTable] = None
    stage_progress: Optional[StageProgress] = None
    trace: Mapping[str, Any] = field(default_factory=dict)


def _selected_defect_code(feedback: Optional[Mapping[str, Any]]) -> Optional[str]:
    """本轮处理的缺陷码 —— 取自**收敛后**的 ``defects`` 首条。

    无缺陷（或未收敛）⇒ ``None``（条件不命中，不臆造）。
    """
    defects = (feedback or {}).get('defects') or ()
    selected = defects[0] if defects else {}
    if not isinstance(selected, Mapping):
        return None
    return selected.get('keyword_name')


def resolve_policies(
    *,
    feedback: Optional[Mapping[str, Any]] = None,
    mold_info: Optional[Mapping[str, Any]] = None,
) -> PolicyResolution:
    """取策略清单 → 判定场景 → 组装第2层要的数据。

    Args:
        feedback: **收敛后**的缺陷反馈（``defects`` 只含本轮处理的那条，
            另带 ``defect_selection`` 留痕）—— 场景条件按它判定。
        mold_info: 模具上下文（制品总重）。

            【注意】场景按 **``selected_defect``（本轮处理的那条）**判定 ——
            多缺陷反馈下「反馈里含此缺陷」≠「本轮处理的是这个缺陷」
            ⇒ 会命中错场景。

    Returns:
        :class:`PolicyResolution` —— **无命中 ⇒ 场景与优先级表为空**（不裁决）。
    """
    context = build_scenario_context(
        feedback,
        mold_info,
        extra={'selected_defect': _selected_defect_code(feedback)},
    )

    # 阶段进度（**只推导，不裁决**）—— 本轮哪些阶段还有缺陷、当前该推进哪一步。
    # 【注意】``current_stage`` 注入 extra ⇒ 场景条件可引用它；
    #    ``filling_stage_first`` 场景已引用（短射 + 仍在打足阶段 ⇒ 充填量优先）。
    progress = derive_stage_progress(context.defect_codes)
    context = replace(
        context,
        extra={**context.extra, 'current_stage': progress.current},
    )

    policies = sorted_scenario_policies()
    if not policies:
        return PolicyResolution(context=context, stage_progress=progress)

    policy = select_policy(policies, context)
    if policy is None:
        return PolicyResolution(context=context, stage_progress=progress)

    trace = {
        'scenario_code': policy.scenario_code,
        'reason': policy.reason,
        'target_mode': policy.target_mode,
        'max_items': policy.max_items,
        'preferred_params': list(policy.preferred_params),
        'defect_codes': list(context.defect_codes),
        'selected_defect': context.extra.get('selected_defect'),
        'fill_gap': context.fill_gap,
        'stage_progress': progress.to_trace(),
    }
    return PolicyResolution(
        context=context,
        scenario=policy,
        priority_table=policy.priority_table,
        stage_progress=progress,
        trace=trace,
    )


__all__ = ['PolicyResolution', 'resolve_policies']
