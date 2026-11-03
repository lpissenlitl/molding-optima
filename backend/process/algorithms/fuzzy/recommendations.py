"""推荐结果层 —— 推理层的逐条调整量 → 对外的 AlgorithmRecommendation。

**依赖边界**：本模块只依赖 `process.algorithms.base.AlgorithmRecommendation`，
不 import ORM、不 import 推理内核 ⇒ 是一层纯函数。
（间接依赖 Django：父包 `process/algorithms/__init__.py` 会 import 全部引擎触发注册。）

数据流：

    推理层                          聚合层                         输出
    ─────                          ─────                         ────
    RuleAdjustment (数值)     ──┐
                                ├──► aggregate() ──► AggregatedAdjustment ──┐
    RuleAdjustment (提示数值) ──┘                                           ├──► to_recommendations()
    RuleAdjustment (文本建议) ─────────────────────────────────────────────┘        │
                                                                                  ▼
                                                                            AlgorithmRecommendation[]
                                                                            └─ conflict 视图（仅方向相反时）

**"层"按结论形态划分**（这条规则的结论能不能算出数值），与规则库层级无关。

两种层：
- 数值层（numeric）：能算出数值的结论（``X_add_3.8`` / ``X_reduce_30%``）
- 提示层（advisory）：检查/弹窗类文本结论（``X_adjust_请检查锁模力是否不合理。``）

⚠️ **conflict 视图的纪律**（2026-10-28 用户拍板：只加标记、不改数值）：
   冲突信息**只在建议值 / 方向算完之后额外产出**，**不参与**它们的计算
   ⇒ 加它不影响任何一个推荐数值，只多一层"给前端选的视图"。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from process.algorithms.base import AlgorithmRecommendation


# ============================================================================
# 方向判定的浮点容差
# ============================================================================
#
# ⚠️ **为什么需要容差**：方向原本用**精确浮点比较**判定
#   （``adjusted_delta > 0`` → increase / ``< 0`` → decrease / ``== 0`` → hold）。
#   而 ``adjusted_delta`` 是**加权平均**的结果 —— 当同参数的多条规则给出
#   相反方向且量级相近时（如 +1.5 与 -1.5），数学上应抵消为 0，实际却会留下
#   **约 1e-17 的浮点残差**（实测 -5.551115123125783e-17）。
#   后果：推荐值与当前值**逐位相等**（5.0 → 5.0），方向却被判成 `decrease`
#   ⇒ 输出**自相矛盾**（“不动”却标成“调低”）。
#
# ⚠️ **ε 的取值依据（2026-10-28 实测）**：全 51 场景扫描，
#   |adjusted_delta| 落在 (0, 1e-6) 的**仅 1 条**（那条浮点残差）；
#   真实的方向依据最小是 **0.5**（prod）/ **0.531965**（min）
#   ⇒ ε=1e-6 与真实量级之间有 **5 个数量级**的余量，不会误伤真实方向。
DIRECTION_EPSILON = 1e-6


# ============================================================================
# 中间态数据类型
# ============================================================================

@dataclass
class RuleAdjustment:
    """单条规则对单个参数产生的调整量（推理层产出）。

    Attributes:
        param_name: 参数名（算法侧字段名，如 ``IV0``）。
        delta: 调整量。数值层 = 结论值 × 该条规则的**组内占比**；
            提示层数值 = 结论值。
        activation: 该条规则的**组内占比** —— 即「它在它所属的输出参数组里
            占多少」。同一组内所有规则的占比之和恒为 1（已剔除无效项后
            重新归一化）⇒ 聚合层裸累加 delta 等价于**加权平均**。
        raw_activation: 该条规则的**原始激活度** $a_i$（前件隶属度之积，
            不含 priority / specificity 乘数）—— 表达「这条规则到底匹配得
            多准」，**置信度用它**（组内占比只表达「谁压过谁」，
            两者混用会把“独占一组但几乎没匹配上”的规则报成 100% 置信）。
        layer: 所属推理层 —— ``'numeric'`` / ``'advisory'``（结论形态）。
        rule_str: 产生该调整的规则串（提示层的模糊等级结论无对应规则串，为 None）。
        advice: 文本建议内容（仅检查/弹窗类结论有值；这类不参与数值聚合）。
    """

    param_name: str
    delta: float
    activation: float
    layer: str
    raw_activation: float = 0.0
    rule_str: Optional[str] = None
    advice: Optional[str] = None


@dataclass
class AggregatedAdjustment:
    """同一参数的多条规则汇总后（聚合层产出）。

    Attributes:
        param_name: 参数名（算法侧字段名）。
        delta: 原始调整量之和（**未乘迭代趋势系数**；系数在
            :func:`to_recommendations` 里乘，便于区分"规则给的量"和"趋势给的量"）。
            ⚠️ 因为每条规则的 delta 已经乘过**组内占比**，这里的“之和”
            实际是**组内加权平均**。
        activation_sum: 命中该参数的规则**组内占比之和**（≈ 1）。
        raw_activation_sum: 命中该参数的规则**原始激活度之和**（$a_i$），
            是**置信度**的唯一来源。
        rule_count: 命中该参数的规则条数。
        sources: 来源层列表（如 ``['numeric']`` 或 ``['numeric', 'advisory']``）。
            ⚠️ 键名保持 ``sources``：它会原样出现在 ``AlgorithmRecommendation.reason`` 里
            （``模糊推理 (sources=['numeric'])``），是对外可见的字符串契约。
        advisory_reference: 提示层对同一参数的调整量（仅作注释，不参与数值聚合）。
        positive_weight: 该参数上**结论为正**（"调高"）的规则，其**组内占比**之和。
        negative_weight: 该参数上**结论为负**（"调低"）的规则，其**组内占比**之和。
        positive_rules / negative_rules: 两个方向各自命中的规则串（**分歧依据**）。
            ⚠️ 这四个字段**只为 conflict 视图服务**（design §5.5），
            **不参与**任何数值计算 —— 加它们前后的推荐值逐位相同。
            ⚠️ 只统计**数值层**规则：提示层（Mamdani）的 activation 是
            **原始激活度**而非组内占比，权重语义不同质，混算无意义。
    """

    param_name: str
    delta: float
    activation_sum: float
    rule_count: int
    raw_activation_sum: float = 0.0
    sources: List[str] = field(default_factory=list)
    advisory_reference: Optional[float] = None
    positive_weight: float = 0.0
    negative_weight: float = 0.0
    positive_rules: List[str] = field(default_factory=list)
    negative_rules: List[str] = field(default_factory=list)


# ============================================================================
# 聚合
# ============================================================================

def aggregate(
    numeric: List[RuleAdjustment],
    advisory: List[RuleAdjustment],
) -> Tuple[List[AggregatedAdjustment], List[RuleAdjustment]]:
    """同参数聚合（同层聚合 + 跨层覆盖）。

    规则：
    1. 数值层的调整量**裸累加**到同参数上（不做任何折算）。
    2. 提示层的数值结论：若该参数数值层已命中 → 只记为
       ``advisory_reference`` 注释（数值层胜出）；否则作为独立条目。
    3. 提示层的**文本建议**（``advice`` 非空）不参与数值聚合，单独返回。

    ⚠️ 输出顺序即 ``AlgorithmRecommendation`` 的顺序：数值层参数的首次出现顺序在前，
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
                raw_activation_sum=adj.raw_activation,
                rule_count=1,
                sources=['numeric'],
            )
        else:
            merged[p].delta += adj.delta
            merged[p].activation_sum += adj.activation
            merged[p].raw_activation_sum += adj.raw_activation
            merged[p].rule_count += 1

        # ⚠️ 方向明细累计 —— **只加不减，不改任何数值**：
        #    上面四行的 delta / activation_sum / raw_activation_sum / rule_count
        #    算法一字未动 ⇒ 加这段前后推荐值逐位相同。
        #    符号口径与数值层完全一致：``delta = 结论值 × 组内占比``，
        #    结论值符号来自 ``ACTION_MAP``（add=+1 / reduce=-1），
        #    ⇒ **标记与数值必然自洽**：不会出现"标了冲突、净方向其实一边倒"。
        if adj.delta > 0:
            merged[p].positive_weight += adj.activation
            if adj.rule_str:
                merged[p].positive_rules.append(adj.rule_str)
        elif adj.delta < 0:
            merged[p].negative_weight += adj.activation
            if adj.rule_str:
                merged[p].negative_rules.append(adj.rule_str)

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
                raw_activation_sum=adj.raw_activation,
                rule_count=1,
                sources=['advisory'],
            )
        else:
            # 数值层已覆盖，仅作 advisory_reference 注释
            merged[p].advisory_reference = adj.delta
            merged[p].sources.append('advisory')

    return list(merged.values()), advice_items


# ============================================================================
# 冲突视图（design §5.5）
# ============================================================================

def build_conflict_view(
    info: AggregatedAdjustment,
    final_direction: str,
) -> Optional[Dict[str, Any]]:
    """组装 conflict 视图 —— 同参数命中规则**方向相反**时给出分歧依据。

    ⚠️ **只标记、不改数值**（2026-10-28 用户拍板）：
       本函数**不参与**建议值 / 方向的计算，只在它们算完之后
       额外产出**一层视图** ⇒ 前端选不呈现都不影响任何既有行为。

    **判定口径**：

    - **冲突存在** = 同一参数上既有 ``delta > 0`` 的规则（结论"调高"）、
      又有 ``delta < 0`` 的规则（结论"调低"）。
      符号口径与数值层完全一致（``ACTION_MAP``：add=+1 / reduce=-1），
      ⇒ **标记与数值必然自洽**：不会出现"标了冲突、净方向其实一边倒"。
    - **cancelled** = 净方向被抵消（最终方向判成 ``hold``）
      ⇒ **最危险的那种**（design §5.5 说的"静默失败"）：
      输出里有建议、实际什么也不会改。

    ⚠️ **本批只覆盖"方向不一致"**；design §5.5 提到的"目标档位不一致"
      **暂不覆盖** —— 数值层（TSK）的结论是**绝对量**（``add_3.8``），
      没有"目标档位"概念；档位型结论（``X_add_low``）在提示层（Mamdani），
      而规则库当前没有这种结论 ⇒ 该场景实际为空集。

    Args:
        info: 该参数的聚合结果（携带方向明细）。
        final_direction: 最终方向（``increase`` / ``decrease`` / ``hold``）。

    Returns:
        冲突视图 dict；**无冲突时返回 None**（不给噪音）。
    """
    if not info.positive_rules or not info.negative_rules:
        return None

    return {
        'has_conflict': True,
        # ⚠️ 最终方向是 hold ⇒ 净调整量已被 ε 归零 ⇒ 正反两边正好抵消
        'cancelled': final_direction == 'hold',
        'directions': [
            {
                'direction': 'increase',
                # ⚠️ weight = 该方向各规则的**组内占比**之和（数值层口径）
                'weight': info.positive_weight,
                'rule_count': len(info.positive_rules),
                'rules': list(info.positive_rules),
            },
            {
                'direction': 'decrease',
                'weight': info.negative_weight,
                'rule_count': len(info.negative_rules),
                'rules': list(info.negative_rules),
            },
        ],
    }


@dataclass
class FuzzyRecommendation(AlgorithmRecommendation):
    """模糊推理的推荐条目 —— 在基类契约上**多挂一层冲突视图**。

    ⚠️ **为什么用子类、而不是给基类加字段**：
       ``AlgorithmRecommendation`` 是 **fuzzy / llm / empirical 三算法共用**的
       对外契约（``base.py::to_dict()`` 是它们统一的序列化出口）。
       冲突是**模糊推理独有的概念** —— llm / empirical 没有"多条规则互相打架"
       这回事。若改基类，三个算法的输出 dict 都会凭空多一个键
       ⇒ 白白扩大契约变更面。
       子类方案：**只有 fuzzy 的输出多一个 ``conflict`` 键**，
       llm / empirical 的 ``to_dict()`` **逐位不变**。

    Attributes:
        conflict: 冲突视图（仅在**同参数命中规则方向相反**时非 None）；
            结构见 :func:`build_conflict_view`。无冲突时为 None。
    """

    conflict: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """在基类契约上**追加** ``conflict`` 键（不改基类的任何键）。

        ⚠️ 基类的 7 个键的值**逐字不动** ⇒ 既有消费方按原样读取不受影响；
           新增键只承载"有没有冲突 / 分歧依据是什么"，前端可选消费。
        """
        data = super().to_dict()
        data['conflict'] = self.conflict
        return data


# ============================================================================
# 转成对外契约
# ============================================================================

def to_recommendations(
    aggregated: List[AggregatedAdjustment],
    advice_items: List[RuleAdjustment],
    adjustment_factor: float,
    current_params: Dict[str, float],
) -> List[AlgorithmRecommendation]:
    """把聚合结果转成 :class:`AlgorithmRecommendation` 列表。

    计算公式（逐条写明，避免"delta 到底乘没乘系数"的歧义）：

    - ``current_value   = current_params.get(param_name) or 0.0``
      （缺该参数时按 0.0 处理）
    - ``adjusted_delta  = delta * adjustment_factor``
      （``adjustment_factor`` 是迭代趋势系数，来自 ``trend_to_factor``）
    - ``recommended_value = current_value + adjusted_delta``
    - ``confidence      = min(raw_activation_sum / max(rule_count, 1), 1.0)``
      —— 语义 = **同参数所有命中规则的平均原始激活度**（$a_i$，前件隶属度之积），
      不是统计置信度。组内只有 1 条规则命中时 = 它自己的激活度
      （完美命中 = 1.0）；命中越分散、整体匹配越差，值越小。
      ⚠️ 不用「组内占比」算置信度：占比只表达「谁压过谁」，
         一条「几乎没匹配上（$a_i$≈0.02）但独占一个参数组」的规则会拿到
         占比 1.0 ⇒ 被误报成 100% 置信。
    - ``direction``：``adjusted_delta > ε`` → ``increase``；``< -ε`` → ``decrease``；
      ``|adjusted_delta| <= ε`` → ``hold``（ε = :data:`DIRECTION_EPSILON`）。
      ⚠️ **必须带容差**：相反方向的规则加权平均后数学上抵消为 0，实际会留
      1e-17 级浮点残差；用精确比较会把它判成 increase/decrease，而推荐值
      又与当前值逐位相等 ⇒ 输出自相矛盾。

    文本建议条目（``advice_items``）：``recommended_value=None``、``confidence=None``、
    ``direction='check'``、``source='fuzzy.check'``。

    ⚠️ **conflict 视图不参与本函数的任何计算**（用户 2026-10-28 拍板：
       只加标记、不改数值）—— 建议值 / 方向 / 置信度 / 条序全部沿用
       既有算法；conflict 只是算完之后**额外挂上去**的一层视图。

    Args:
        aggregated: :func:`aggregate` 产出的参数级汇总。
        advice_items: :func:`aggregate` 产出的文本建议条目。
        adjustment_factor: 迭代趋势系数。
        current_params: 当前工艺参数（算法侧字段名 → 当前值）。

    Returns:
        :class:`FuzzyRecommendation` 列表（数值推荐在前，文本建议在后）。
    """
    recommendations: List[FuzzyRecommendation] = []

    for info in aggregated:
        raw_current = current_params.get(info.param_name)
        current_value = float(raw_current) if raw_current is not None else 0.0
        adjusted_delta = info.delta * adjustment_factor
        # ⚠️ 抵消残差视同“无变化”：不仅方向要判 hold，推荐值也**钉在当前值**上
        #   ⇒ 输出严格自洽（hold ⇒ 推荐值与当前值逐位相等），不会出现
        #   “数值没动但方向说要调”的矛盾箭头。
        if abs(adjusted_delta) <= DIRECTION_EPSILON:
            adjusted_delta = 0.0
        recommended_value = current_value + adjusted_delta
        direction = (
            'increase' if adjusted_delta > 0
            else 'decrease' if adjusted_delta < 0
            else 'hold'
        )

        # ⚠️ 冲突视图：**只标记、不改数值** —— 建议值 / 方向 / 置信度
        #   一律沿用上面算出来的结果（用户 2026-10-28 拍板）。
        conflict = build_conflict_view(info, direction)

        recommendations.append(FuzzyRecommendation(
            param_name=info.param_name,
            current_value=current_value,
            recommended_value=recommended_value,
            confidence=min(info.raw_activation_sum / max(info.rule_count, 1), 1.0),
            reason=f"模糊推理 (sources={info.sources})",
            source='fuzzy.numeric' if 'numeric' in info.sources else 'fuzzy.advisory',
            direction=direction,
            conflict=conflict,
        ))

    # 检查/弹窗类建议：文本建议，不给数值，方向为「检查」
    for adj in advice_items:
        param_name = adj.param_name or ''
        raw_current = current_params.get(param_name)
        recommendations.append(FuzzyRecommendation(
            param_name=param_name,
            current_value=float(raw_current) if raw_current is not None else 0.0,
            recommended_value=None,
            confidence=None,
            reason=f"模糊推理建议：{adj.advice}",
            source='fuzzy.check',
            direction='check',
            # ⚠️ 文本建议不是多条规则加权平均出来的 ⇒ 无冲突概念
            conflict=None,
        ))

    return recommendations
