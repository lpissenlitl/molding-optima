"""策略装配（编排层）—— 第2层的**数据供给**。

职责：从**策略清单文件**（:mod:`process.algorithms.strategies`）取业务知识，
组装成第2层要的数据形态：

- **实际情况**（``ScenarioContext``）：本轮的缺陷码、实测重量、目标重量、充填缺口
  （从反馈与模具上下文派生，不查库）；
- **命中哪个场景**（``ScenarioPolicy``）：条件求值 + 取第一条命中；
- **字段级优先级表**（``PriorityTable``）：随场景一起来（清单里自带）。

⚠️ **清单里没有 ⇒ 不裁决**（行为与「不接第2层」完全一致）：
读清单失败 / 无命中策略 ⇒ 场景与优先级表为空 ⇒ 第2层照旧不裁决。

⚠️ **本模块不做业务判断** —— 「什么场景、调哪些、留几个」全在清单文件里；
本模块只负责取、匹配、组装。

⚠️ **充填量目标不在这里算** —— 它是「结合实际情况算目标」，属第2层的职责
（:func:`process.algorithms.decide_direction.resolve_direction`）。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from process.algorithms.decide_direction import (
    PriorityTable,
    ScenarioContext,
    ScenarioPolicy,
    build_scenario_context,
    select_policy,
)
from process.algorithms.strategies import load_strategies

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyResolution:
    """策略解析的结果（供编排层直接喂给第2层）。

    Attributes:
        context: **实际情况**（缺陷码 / 实测重量 / 目标重量 / 充填缺口）。
        scenario: 命中的场景策略（``None`` = 无场景 ⇒ 不裁决）。
        priority_table: 字段级优先级表（空表 = 不按字段级排序）。
        trace: 留痕（场景码、命中条件、上下文摘要）。
    """

    context: ScenarioContext = field(default_factory=ScenarioContext)
    scenario: Optional[ScenarioPolicy] = None
    priority_table: Optional[PriorityTable] = None
    trace: Mapping[str, Any] = field(default_factory=dict)


def resolve_policies(
    *,
    feedback: Optional[Mapping[str, Any]] = None,
    mold_info: Optional[Mapping[str, Any]] = None,
    selected_defect: Optional[str] = None,
) -> PolicyResolution:
    """取策略清单 → 判定场景 → 组装第2层要的数据。

    Args:
        feedback: 缺陷反馈（缺陷码 + 实测观察）。
        mold_info: 模具上下文（制品总重）。
        selected_defect: **本轮实际处理的缺陷码**（service 预处理层的整理结果）
            —— 场景条件按它判定（经 ``ScenarioContext.extra`` 注入）。

            ⚠️ **不按 ``defect_codes``（全部缺陷码）判定** —— 多缺陷反馈下
            「反馈里含此缺陷」≠「本轮处理的是这个缺陷」⇒ 会命中错场景。

    Returns:
        :class:`PolicyResolution` —— **无命中 ⇒ 场景与优先级表为空**（不裁决）。
    """
    context = build_scenario_context(
        feedback,
        mold_info,
        extra={'selected_defect': selected_defect},
    )

    try:
        policies = load_strategies()
    except Exception as exc:                  # 读清单失败 ⇒ 不裁决（不阻塞优化）
        _logger.warning('[policy] 读取策略清单失败，本轮不裁决: %s', exc)
        return PolicyResolution(context=context)

    if not policies:
        return PolicyResolution(context=context)

    policy = select_policy(policies, context)
    if policy is None:
        return PolicyResolution(context=context)

    trace = {
        'scenario_code': policy.scenario_code,
        'reason': policy.reason,
        'target_mode': policy.target_mode,
        'max_items': policy.max_items,
        'preferred_params': list(policy.preferred_params),
        'defect_codes': list(context.defect_codes),
        'selected_defect': context.extra.get('selected_defect'),
        'fill_gap': context.fill_gap,
    }
    return PolicyResolution(
        context=context,
        scenario=policy,
        priority_table=policy.priority_table,
        trace=trace,
    )


__all__ = ['PolicyResolution', 'resolve_policies']
