"""聚合层 —— 推理层的逐条调整量 → 对外的 Recommendation。

**依赖边界**：本模块只依赖 `process.algorithms.base.Recommendation`，
不 import ORM、不 import 推理内核 ⇒ 是一层纯函数。
（间接依赖 Django：父包 `process/algorithms/__init__.py` 会 import 全部引擎触发注册，
  这是 §6 L8 已记录的既有边界，本次不动。）

数据流：

    推理层                          聚合层                         输出
    ─────                          ─────                         ────
    RuleAdjustment (数值)     ──┐
                                ├──► aggregate() ──► AggregatedAdjustment ──┐
    RuleAdjustment (提示数值) ──┘                                           ├──► to_recommendations()
    RuleAdjustment (文本建议) ─────────────────────────────────────────────┘        │
                                                                                  ▼
                                                                            Recommendation[]

**"层"按结论形态划分**（这条规则的结论能不能算出数值），与规则库层级无关。

两种层：
- 数值层（numeric）：能算出数值的结论（``X_add_3.8`` / ``X_reduce_30%``）
- 提示层（advisory）：检查/弹窗类文本结论（``X_adjust_请检查锁模力是否不合理。``）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from process.algorithms.base import Recommendation


# ============================================================================
# 中间态数据类型
# ============================================================================

@dataclass
class RuleAdjustment:
    """单条规则对单个参数产生的调整量（推理层产出）。

    Attributes:
        param_name: 参数名（算法侧字段名，如 ``IV0``）。
        delta: 调整量。数值层 = 结论值 × 该条规则的激活度；提示层数值 = 结论值。
        activation: 该条规则的激活度。
        layer: 所属推理层 —— ``'numeric'`` / ``'advisory'``（结论形态）。
        rule_str: 产生该调整的规则串（提示层的模糊等级结论无对应规则串，为 None）。
        advice: 文本建议内容（仅检查/弹窗类结论有值；这类不参与数值聚合）。
    """

    param_name: str
    delta: float
    activation: float
    layer: str
    rule_str: Optional[str] = None
    advice: Optional[str] = None


@dataclass
class AggregatedAdjustment:
    """同一参数的多条规则汇总后（聚合层产出）。

    Attributes:
        param_name: 参数名（算法侧字段名）。
        delta: 原始调整量之和（**未乘迭代趋势系数**；系数在
            :func:`to_recommendations` 里乘，便于区分"规则给的量"和"趋势给的量"）。
        activation_sum: 命中该参数的规则激活度之和。
        rule_count: 命中该参数的规则条数。
        sources: 来源层列表（如 ``['numeric']`` 或 ``['numeric', 'advisory']``）。
            ⚠️ 键名保持 ``sources``：它会原样出现在 ``Recommendation.reason`` 里
            （``模糊推理 (sources=['numeric'])``），是对外可见的字符串契约。
        advisory_reference: 提示层对同一参数的调整量（仅作注释，不参与数值聚合）。
    """

    param_name: str
    delta: float
    activation_sum: float
    rule_count: int
    sources: List[str] = field(default_factory=list)
    advisory_reference: Optional[float] = None


# ============================================================================
# 聚合
# ============================================================================

def aggregate(
    numeric: List[RuleAdjustment],
    advisory: List[RuleAdjustment],
) -> Tuple[List[AggregatedAdjustment], List[RuleAdjustment]]:
    """同参数聚合（方案 B：同层聚合 + 跨层覆盖）。

    规则：
    1. 数值层的调整量**裸累加**到同参数上（不做任何折算）。
    2. 提示层的数值结论：若该参数数值层已命中 → 只记为
       ``advisory_reference`` 注释（数值层胜出）；否则作为独立条目。
    3. 提示层的**文本建议**（``advice`` 非空）不参与数值聚合，单独返回。

    ⚠️ 输出顺序即 ``Recommendation`` 的顺序：数值层参数的首次出现顺序在前，
       提示层独有参数在后。

    Args:
        numeric: 数值层产出的逐条调整量。
        advisory: 提示层产出的逐条调整量（含文本建议）。

    Returns:
        ``(aggregated, advice_items)`` —— 前者是可转成推荐的参数级汇总，
        后者是文本建议条目（不进数值聚合）。
    """
    merged: Dict[str, AggregatedAdjustment] = {}
    advice_items: List[RuleAdjustment] = []

    for adj in numeric:
        p = adj.param_name
        if p not in merged:
            merged[p] = AggregatedAdjustment(
                param_name=p,
                delta=adj.delta,
                activation_sum=adj.activation,
                rule_count=1,
                sources=['numeric'],
            )
        else:
            merged[p].delta += adj.delta
            merged[p].activation_sum += adj.activation
            merged[p].rule_count += 1

    for adj in advisory:
        # 检查/弹窗类结论（`X_adjust_提示语`）是**文本建议**：
        # delta 恒为 0，混进数值聚合会产生"保持不变"的假推荐，
        # 必须单独输出（recommended_value=None）。
        if adj.advice:
            advice_items.append(adj)
            continue

        p = adj.param_name
        if p not in merged:
            merged[p] = AggregatedAdjustment(
                param_name=p,
                delta=adj.delta,
                activation_sum=adj.activation,
                rule_count=1,
                sources=['advisory'],
            )
        else:
            # 数值层已覆盖，仅作 advisory_reference 注释
            merged[p].advisory_reference = adj.delta
            merged[p].sources.append('advisory')

    return list(merged.values()), advice_items


# ============================================================================
# 转成对外契约
# ============================================================================

def to_recommendations(
    aggregated: List[AggregatedAdjustment],
    advice_items: List[RuleAdjustment],
    adjustment_factor: float,
    current_params: Dict[str, float],
) -> List[Recommendation]:
    """把聚合结果转成 :class:`Recommendation` 列表。

    计算公式（逐条写明，避免"delta 到底乘没乘系数"的歧义）：

    - ``current_value   = current_params.get(param_name) or 0.0``
      （缺该参数时按 0.0 处理）
    - ``adjusted_delta  = delta * adjustment_factor``
      （``adjustment_factor`` 是迭代趋势系数，来自 ``trend_to_factor``）
    - ``recommended_value = current_value + adjusted_delta``
    - ``confidence      = min(activation_sum / max(rule_count, 1), 1.0)``
      —— ⚠️ 语义上这是**同参数所有命中规则的平均激活度**，不是统计置信度。
    - ``direction``：``adjusted_delta > 0`` → ``increase``；``< 0`` → ``decrease``；
      ``== 0`` → ``hold``。

    文本建议条目（``advice_items``）：``recommended_value=None``、``confidence=None``、
    ``direction='check'``、``source='fuzzy.check'``。

    Args:
        aggregated: :func:`aggregate` 产出的参数级汇总。
        advice_items: :func:`aggregate` 产出的文本建议条目。
        adjustment_factor: 迭代趋势系数。
        current_params: 当前工艺参数（算法侧字段名 → 当前值）。

    Returns:
        Recommendation 列表（数值推荐在前，文本建议在后）。
    """
    recommendations: List[Recommendation] = []

    for info in aggregated:
        raw_current = current_params.get(info.param_name)
        current_value = float(raw_current) if raw_current is not None else 0.0
        adjusted_delta = info.delta * adjustment_factor
        recommended_value = current_value + adjusted_delta

        recommendations.append(Recommendation(
            param_name=info.param_name,
            current_value=current_value,
            recommended_value=recommended_value,
            confidence=min(info.activation_sum / max(info.rule_count, 1), 1.0),
            reason=f"模糊推理 (sources={info.sources})",
            source='fuzzy.numeric' if 'numeric' in info.sources else 'fuzzy.advisory',
            direction=(
                'increase' if adjusted_delta > 0
                else 'decrease' if adjusted_delta < 0
                else 'hold'
            ),
        ))

    # 检查/弹窗类建议：文本建议，不给数值，方向为「检查」
    for adj in advice_items:
        param_name = adj.param_name or ''
        raw_current = current_params.get(param_name)
        recommendations.append(Recommendation(
            param_name=param_name,
            current_value=float(raw_current) if raw_current is not None else 0.0,
            recommended_value=None,
            confidence=None,
            reason=f"模糊推理建议：{adj.advice}",
            source='fuzzy.check',
            direction='check',
        ))

    return recommendations
