"""第3层：整合参数 —— 把调整计划变成**物理上自洽**的参数集。

这一层只干一件事：**让参数集自洽**。它不知道参数是怎么来的
（算法建议 / 手工编辑 / 初始化），也不判断合不合理（第4层 ``check_params.py`` 的事）。

三个入口，同一套底座：

.. code-block:: text

    计划落地   apply_plan()         第2层计划 ──▶ 写入 ──▶ 锚点传导
    参数集自洽 integrate()          差分 ──▶ 锚点传导 ──▶ 按差异回填
    锚点传导   propagate()          改了什么 ──▶ 连带算出别的量

**锚点关系**（谁等于谁、哪些量必须递增）只定义一次：

- 字段口径与共用判据在 :mod:`process.services.optimize_chain.anchors`；
- 关系清单（:data:`LINK_RULES`）与传播逻辑在本模块。

【注意】**只对数据负责**：不区分优化还是手工，
只对数据负责 ⇒ 手工编辑提交全量字段、规则优化给「基线 + 覆盖」，
两者走同一套整合。

【注意】**一条规则一个函数** —— 本层的锚点关系数量不多，每条都能一句话说清
（如「储料终止位置 = 末段熔胶位置 + 储后松退距离」）⇒ 采用直白的结构，
而不是通用等式求解器（后者要为一两条规则付出几百行抽象成本，反而更难读）。

字段名：**代码侧**业务字段名（与 ``ProcessParameterSchema`` 对齐），含段号的字段按
实际段数拼出（如 ``met_pos_3``）。

算法/工艺侧的对应命名：

====================  ==========================
算法名                代码字段
====================  ==========================
``MEL``               ``met_end_pos``（计量终止位置）
``ML_N`` / ``ML_i``   ``met_pos_{N}`` / ``met_pos_{i}``（各段熔胶位置）
``DDAM``              ``pst_met_decomp_dist``（熔胶后松退）
``DDBM``              ``pre_met_decomp_dist``（熔胶前松退）
``VPTL``              ``vps_pos``（VP 切换位置）
====================  ==========================

量纲：位置 mm、温度 °C、时间 s、速度 mm/s。
"""

from dataclasses import dataclass, field, replace
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
)

from .anchors import (
    FREEDOM_YIELDS,
    G1_AUTO_FIELD,
    G1_BACKOFF_FIELD,
    FillTarget,
    apply_mel_targets,
    find_chain_break,
    last_stage_field,
    resolve_fill_target,
    resolve_stage_count,
)
from .decide_direction import AdjustmentPlan


# ===========================================================================
# 一、锚点传导（改值）
# ===========================================================================


@dataclass(frozen=True)
class LinkRule:
    """一条联动规则的说明。

    本类是**给人看的清单**（查阅、留痕、写文档），计算逻辑在对应的
    ``_link_*`` 函数里 —— 规则涉及计算，用数据表达反而更难读。

    Attributes:
        rule_id: 规则标识。
        group: 所属分组。
        formula: 规则表达式（字段名 + 人话）。
        auto_field: 本规则的**自动计算量**（由这条关系算出来的一侧，如
            ``MEL`` 在机台上就是自动算的）；空串 = 该规则两侧**各自独立**，
            没有自动计算的一侧。
        note: 口径说明（为什么是这条关系、依据哪个版本）。
    """

    rule_id: str
    group: str
    formula: str
    auto_field: str = ''
    note: str = ''


#: 联动规则清单。**执行顺序 = :func:`propagate` 里的调用顺序**。
#:
#: **为什么没有 G5（保压组）**：多段保压由 expert 按系数表**一次性分配**
#: （``expert/algorithm_engine.py:2820-2822``），各段保压参数**各自独立**，
#: 段与段之间**没有锚点关系** ⇒ 没有可传导的规则；保压时间是**经验窗口**
#: ⇒ 归第4层校验，不在本清单。
LINK_RULES: Tuple[LinkRule, ...] = (
    LinkRule(
        rule_id='g1.meter_end_position',
        group='G1',
        formula='met_end_pos = met_pos_N + pst_met_decomp_dist',
        auto_field='met_end_pos',
        note='计量终止位置 = **计量最后一段的位置** + 储料后松退距离；'
             '松退是为保障熔胶不流延 ⇒ 「计量位置」与「计量终止位置」是两个量。'
             '（DDAM 是螺杆回抽量，不参与注射量计算；注射量 = ML_N − VPTL）'
             '【注意】与 expert 的已知差：expert 锚单段的 meter_posi，多段时其末段多一个 '
             'replenish_len ⇒ 多段时与本式差 replenish_len（单段无差异）；按业务判断不追；'
             '**先定 ML，再确定 MEL**：MEL 是算法侧的**标**'
             '（由 ML_N + DDAM 算出），机台上真正会被调的是计量位置与储后松退 ⇒ '
             'MEL 目标先翻成决策量（解出 met_pos_N），MEL 再由 met_pos_N 算出',
    ),
    LinkRule(
        rule_id='g2.suckback_chain',
        group='G2',
        formula='met_pos_1 < met_pos_2 < ... < met_pos_N，且 met_pos_1 > vps_pos',
        note='多段计量是螺杆**逐段回抽**，各段终点**各自独立**（不按系数重排）；'
             '系数只是初始化时的一次性划分；'
             '各段都是**独立量**（没有自动计算的一侧）⇒ 改谁都生效，'
             '只受「严格递增」这条**硬约束**约束（违反 ⇒ 该直接改动回退）',
    ),
    LinkRule(
        rule_id='g3.speed_freedom',
        group='G3',
        formula='改 inj_t ⇒ 让位给 inj_spd_1',
        note='注射阶段是速度控制，设定时间只是设定值 ⇒ 时间不由行程反算；'
             '这是**让位**（不是自动计算）⇒ 无自动计算侧',
    ),
)

#: 自由度映射：被让位的量 → 让给谁。
#:
#: 注射阶段实际是**速度控制**（设定时间只是设定值，实际时间会有偏差），
#: 所以改时间的建议让位给速度 —— 留痕且**值回退**（让位 = 不生效）。
#:
#: 【注意】**声明在底座**（:data:`process.services.optimize_chain.anchors.FREEDOM_YIELDS`）——
#: 底座只定义一次，各层各自引用。
# （第2层不掺合参数 ⇒ 不用它做「落不了地」预筛。）
FREEDOM_OVERRIDES: Mapping[str, str] = FREEDOM_YIELDS


@dataclass(frozen=True)
class PropagationResult:
    """联动结果。

    Attributes:
        values: 联动后的完整参数集（业务字段名 → 数值）。
        direct_fields: 被直接改动的字段。
        derived_fields: 本次联动**推导出来**的字段（可能是自动计算量，
            也可能是被反推出来的独立量 —— 取决于改的是哪一侧）。
        superseded_fields: 让位给自由度的直接改动（字段名 → 自由度字段）。
        conflicts: 同时被直接改动、无法判定的字段组合。
    """

    values: Dict[str, float]
    direct_fields: Tuple[str, ...] = ()
    derived_fields: Tuple[str, ...] = ()
    superseded_fields: Mapping[str, str] = field(default_factory=dict)
    conflicts: Tuple[str, ...] = ()
    unresolved: Tuple[str, ...] = ()

    def to_trace(self) -> Dict[str, object]:
        """联动留痕载荷（写进调用方的诊断出口）。"""
        return {
            'direct': list(self.direct_fields),
            'derived': list(self.derived_fields),
            'superseded': dict(self.superseded_fields),
            'conflicts': list(self.conflicts),
            'unresolved': list(self.unresolved),
        }


def _link_g1_meter_end_position(
    direct: Mapping[str, float],
    values: Dict[str, float],
    derived: List[str],
    unresolved: List[str],
    conflicts: List[str],
) -> None:
    """G1 计量终止位置：met_end_pos = met_pos_N + pst_met_decomp_dist。

    业务口径：计量终止位置 = **计量最后一段的位置** + 储料后松退距离。
    松退是为保障熔胶不流延 ⇒ 「计量位置」与「计量终止位置」是两个量。

    ``N`` = 计量段数（``met_stg``）。

    **先定 ML，再确定 MEL**：``MEL`` 是算法侧的**标**，
    表达上永远是「根据 ML 确定 MEL」：

    - 改了**计量终止位置** ⇒ 先解出末段熔胶位置（决策量），再由它定终止位置；
    - 改了**末段熔胶位置**或**后松退距离** ⇒ 重算计量终止位置。

    两种方向算的是同一条等式，区别在**谁先被确定** ⇒ 净效果一样，
    但语义上终止位置始终是**算出来的**。
    """
    stage_count = resolve_stage_count(values)
    if stage_count is None:
        if G1_AUTO_FIELD in direct or G1_BACKOFF_FIELD in direct:
            unresolved.append('G1 计量终止位置：缺 met_stg，无法确定末段是哪个，不联动')
        return
    last = last_stage_field(stage_count)
    if not any(name in direct for name in (G1_AUTO_FIELD, last, G1_BACKOFF_FIELD)):
        return
    if G1_AUTO_FIELD not in values or G1_BACKOFF_FIELD not in values:
        unresolved.append('G1 计量终止位置：缺 met_end_pos 或后松退距离，不联动')
        return

    if G1_AUTO_FIELD in direct and last in direct:
        # 两端同时改 ⇒ 无解 ⇒ **自动计算量优先**：
        # 自动计算量（MEL）是派生量 ⇒ 以独立量（ML_N）为准重算它；
        # 用户填的 MEL 被覆盖 —— 留痕说清楚，不静默。
        conflicts.append(
            f'{G1_AUTO_FIELD} / {last}：两端同时改 ⇒ 按独立量重算自动计算量'
        )
        values[G1_AUTO_FIELD] = values[last] + values[G1_BACKOFF_FIELD]
        derived.append(G1_AUTO_FIELD)
        return
    if G1_AUTO_FIELD in direct:
        values[last] = values[G1_AUTO_FIELD] - values[G1_BACKOFF_FIELD]
        derived.append(last)
        return
    if last in values and (last in direct or G1_BACKOFF_FIELD in direct):
        values[G1_AUTO_FIELD] = values[last] + values[G1_BACKOFF_FIELD]
        derived.append(G1_AUTO_FIELD)


def _check_g2_suckback_chain(
    params: Mapping[str, float],
    direct: Mapping[str, float],
    values: Dict[str, float],
    unresolved: List[str],
) -> None:
    """G2 回抽链校验：各段熔胶位置是**逐段回抽**的终点，必须严格递增。

    物理含义：多段计量是螺杆**分多次往回抽**，每段一个终点绝对位置
    （如 ``vps_pos → 105 → 120``）。各段终点**各自独立设定** ⇒ 谁被改谁生效，
    **不按系数重排** —— 系数只是初始化时的一次性划分
    （expert ``met_pos_i = vps_pos + coef_i × total_len``）。

    硬约束：

    - 各段终点**严格递增**（否则某段变成往前推，回抽过程不成立）；
    - 第一段必须大于 ``vps_pos``（否则首段回抽量 ≤ 0）。

    违反时的处理：

    - **直接改动**造成的 ⇒ 该改动**不生效**（值回退）+ 留痕；
    - **联动推导**造成的 ⇒ 不回退（那是物理必然）+ 留痕告警。
    """
    count = resolve_stage_count(values)
    if count is None or count < 2:
        return                                  # 单段没有回抽链

    broken = find_chain_break(values, count)
    if broken is None:
        return

    lower, higher, detail = broken
    for name in (higher, lower):
        if name in direct and name in params:
            values[name] = params[name]
            unresolved.append(
                f'G2 回抽链：{detail} ⇒ {name} 的直接改动已回退，不生效'
            )
            if find_chain_break(values, count) is not None:
                unresolved.append('G2 回抽链：回退后仍非递增（当前值本身不自洽），未处理')
            return
    unresolved.append(f'G2 回抽链：{detail}（非直接改动造成），未处理')


def _apply_freedom(
    params: Mapping[str, float],
    direct: Mapping[str, float],
    values: Dict[str, float],
    superseded: Dict[str, str],
) -> None:
    """自由度让位：被让位的直接改动**不生效** —— 值回退为当前值。

    只留痕不回退等于「说它没生效，却照样用它的值」。
    """
    for name, free in FREEDOM_OVERRIDES.items():
        if name not in direct or values.get(free) is None:
            continue
        superseded[name] = free
        values[name] = params.get(name)


def propagate(
    params: Mapping[str, float],
    direct: Mapping[str, float],
) -> PropagationResult:
    """把直接改动量按物理联动规则传播成自洽参数集。

    Args:
        params: 当前工艺参数（业务字段名 → 数值；``None`` 视为未知）。
        direct: 被**直接改动**的量（业务字段名 → 目标值，非增量）。

    Returns:
        :class:`PropagationResult` —— 联动后的参数集 + 留痕。
    """
    values: Dict[str, float] = {k: v for k, v in params.items() if v is not None}
    values.update({k: v for k, v in direct.items() if v is not None})

    derived: List[str] = []
    superseded: Dict[str, str] = {}
    conflicts: List[str] = []
    unresolved: List[str] = []

    _link_g1_meter_end_position(direct, values, derived, unresolved, conflicts)
    _check_g2_suckback_chain(params, direct, values, unresolved)
    _apply_freedom(params, direct, values, superseded)

    return PropagationResult(
        values={k: v for k, v in values.items() if v is not None},
        direct_fields=tuple(direct.keys()),
        derived_fields=tuple(derived),
        superseded_fields=superseded,
        conflicts=tuple(conflicts),
        unresolved=tuple(unresolved),
    )


# ===========================================================================
# 二、参数集自洽（差分 → 传导 → 按差异回填）
# ===========================================================================

#: 数值相等判定容差（参数是 2 位小数 ⇒ 1e-9 足够滤掉浮点噪声）
_NUMERIC_TOLERANCE = 1e-9


@dataclass(frozen=True)
class IntegratedParams:
    """一次整合的结果。

    Attributes:
        values: 整合后的参数集（业务字段名 → 值；键集与传入的一致）。
        direct_fields: 本次**直接改动**的字段（差分得出）。
        derived_fields: 联动**推导出来**的字段（自动计算量或被反推的独立量）。
        superseded_fields: 让位给自由度的直接改动（字段名 → 让给谁）。
        conflicts: 两端同时改导致无解的字段组合（已按「自动计算量优先」处置）。
        unresolved: 没能联动的说明（缺量 / 口径不适用 / 违反硬约束）。
        landed: 第2层方向**实际写入**的字段（按写入次序）。
        fill_target: 本轮采用的**充填量目标**（``None`` = 没走比例口径）。
        landing_blocked: **本层自检结论** —— 「本该落地却一个量都没动」。
            ``None`` ⇒ 没这个问题；否则为**保留项**（诊断用，供调用方留痕）。
    """

    values: Dict[str, Any]
    direct_fields: Tuple[str, ...] = ()
    derived_fields: Tuple[str, ...] = ()
    superseded_fields: Tuple[Tuple[str, str], ...] = ()
    conflicts: Tuple[str, ...] = ()
    unresolved: Tuple[str, ...] = ()
    landed: Tuple[str, ...] = ()
    fill_target: Optional[FillTarget] = None
    landing_blocked: Optional[Tuple[str, ...]] = None

    @property
    def touched(self) -> bool:
        """本次整合是否**动过**数据（联动 / 让位 / 回退 / 检出冲突）。"""
        return bool(
            self.derived_fields
            or self.superseded_fields
            or self.conflicts
            or self.unresolved
        )

    def summary(self) -> str:
        """一行可读摘要（给日志用）。"""
        fill = self.fill_target.reason if self.fill_target is not None else '-'
        return (
            f'direct={list(self.direct_fields)} '
            f'derived={list(self.derived_fields)} '
            f'superseded={list(self.superseded_fields)} '
            f'conflicts={list(self.conflicts)} '
            f'unresolved={list(self.unresolved)} '
            f'fill_target={fill}'
        )


def is_number(value: Any) -> bool:
    """是不是可参与数值运算的值（``bool`` 是 ``int`` 的子类，先排除）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def numeric_snapshot(instance: Any) -> Dict[str, float]:
    """从 ORM 实例取「数值字段」快照（= 改动前的旧值）。

    鸭子类型：只看 ``_meta.fields``，**不 import models** ⇒ 不会引入循环依赖
    （models → services → algorithms 是环，algorithms → models 就断了）。

    非数值字段（字符串 / 日期 / None）不取 —— 它们不是「量」，不参与差分。
    """
    meta = getattr(instance, '_meta', None)
    fields = getattr(meta, 'fields', None)
    if not fields:
        return {}
    snapshot: Dict[str, float] = {}
    for field in fields:
        if getattr(field, 'is_relation', False):
            continue
        value = getattr(instance, field.name, None)
        if is_number(value):
            snapshot[field.name] = float(value)
    return snapshot


def diff_numeric_fields(
    previous: Optional[Mapping[str, Any]],
    current: Mapping[str, Any],
) -> Dict[str, float]:
    """差分出「这次直接改动了哪些数值字段」。

    Args:
        previous: 改动前的参数集；``None`` = 没有旧值可比。
        current: 改动后的参数集。

    Returns:
        字段名 → 目标值（**非增量**，是改完之后的值）。

    口径：

    - 只认数值字段（字符串 / ``None`` / ``bool`` 不是「量的改动」）；
    - 新出现的字段没有旧值可比 ⇒ **不当作改动**（不臆造）；
    - 旧值不是数值（原来是空）⇒ 同样不当作改动（回落口径）。
    """
    if not previous:
        return {}
    direct: Dict[str, float] = {}
    for name, value in current.items():
        if not is_number(value):
            continue
        old = previous.get(name)
        if not is_number(old):
            continue
        if abs(float(value) - float(old)) > _NUMERIC_TOLERANCE:
            direct[name] = float(value)
    return direct


def integrate(
    values: Mapping[str, Any],
    previous: Optional[Mapping[str, Any]] = None,
) -> IntegratedParams:
    """把一份参数集整合成**物理上自洽**的形态（写入前的数据体检）。

    流程：**差分 → 传导 → 按差异回填**。

    差分为什么必要：写入方给的是**整份参数**（手工编辑提交全量字段，
    规则优化给的是「基线 + 推荐覆盖」），传导层需要的是「这次改动了哪些量」。
    ⇒ 有旧值可比时用差分得到；没有旧值（新建轮次，值由算法产出）⇒ 不臆造改动。

    【注意】**按差异回填**是刻意的：联动推导、让位回退、硬约束回退、
    冲突时的「自动计算量优先」重算，都会体现为「与新值不同」⇒
    一条回填规则覆盖四种情形，且不碰无关字段。

    【注意】**校验不在本层** —— 合不合理是第4层的事
    （:mod:`process.services.optimize_chain.check_params`），本层只管**改值**。

    Args:
        values: 待落库的参数集（业务字段名 → 值）。
        previous: 同一轮次**改动前**的参数集；``None`` = 新建，没有可比对的旧值。

    Returns:
        :class:`IntegratedParams` —— 整合后的参数集 + 留痕。
    """
    current: Dict[str, Any] = dict(values)
    direct = diff_numeric_fields(previous, current)

    if not direct:
        # 没有可比对的旧值（新建）或不涉及数值改动 ⇒ 不传导
        return IntegratedParams(values=current)

    base: Mapping[str, Any] = previous if previous else current
    result = propagate(base, direct)

    # 按差异回填：只写「传导层改过的」字段，其余原样保留
    for name, value in result.values.items():
        if name not in current or not is_number(value):
            continue
        before = current[name]
        if not is_number(before):
            continue
        if abs(float(value) - float(before)) > _NUMERIC_TOLERANCE:
            current[name] = value

    return IntegratedParams(
        values=current,
        direct_fields=tuple(sorted(direct)),
        derived_fields=tuple(result.derived_fields),
        superseded_fields=tuple(sorted(result.superseded_fields.items())),
        conflicts=tuple(result.conflicts),
        unresolved=tuple(result.unresolved),
    )


# ===========================================================================
# 三、计划落地（第2层计划 ──▶ 参数集）
# ===========================================================================


def apply_plan(
    baseline: Mapping[str, Any],
    plan: AdjustmentPlan,
    previous: Optional[Mapping[str, Any]] = None,
    *,
    fill_weights: Optional[Tuple[float, float]] = None,
) -> IntegratedParams:
    """把第2层的**调整计划**整合进参数集（写入 + 锚点传导自洽）。

    流程：**写入计划 → 差分 → 传导 → 按差异回填**。

    - **写入计划**：按计划次序写进基线（先定 ML，再确定 MEL ⇒ ``MEL``
      永远是由计量位置算出来的派生量）；
    - **差分**：写入后才知道「这次改动了哪些量」⇒ 与旧值比；
    - **传导**：按物理联动规则把连带量算出来（:func:`propagate`）。

    【注意】**「改成多少」在这一层算** —— 第2层只给「调哪个 +
    什么口径」；``MEL`` 是算法侧的**标**（由 ``ML_N + DDAM`` 算出）⇒ 这里按
    ``plan.target_mode`` 把它翻成计量位置（决策量）：

    - ``'fill_ratio'``：按充填量比例解算**行程目标**（行程 ∝ 重量），
      需 ``fill_weights``（目标重量, 实测重量）；解不出来 ⇒ **回落增量口径**；
    - 其它（增量口径）：``旧MEL + ΔMEL`` ⇒ 计量位置。

    【注意】**本层不做存在性兜底** —— 「这条规则要调的参数是不是
    工艺量」在**候选准入**就判掉了（命名契约：静态字段字典）⇒ 不是工艺量的
    （``IPOS`` 这类规则库专用参数）**进不来**，本层写到的每一个名字都是
    工艺量 ⇒ 无需再判，也无从掩饰（兜底 = 掩饰错误：规则有误该改规则）。

    【注意】**本层还做一次自检**：「上层裁决出了保留项，但一个量都没动」
    ⇒ 落地被拦住 ⇒ 记在 :attr:`IntegratedParams.landing_blocked`
    （**只留结论，不抛异常** —— 算法层既有风格是「纯计算 + 留痕，不抛异常」）。

    Args:
        baseline: 现状参数集（旧值基线）。
        plan: 第2层给出的**调整计划**（字段名 + 目标值 + 口径）。
        previous: 改动前的参数集；``None`` ⇒ 取 ``baseline``。
        fill_weights: （目标重量, 实测重量）—— 充填量比例口径的输入。

    Returns:
        :class:`IntegratedParams` —— 整合后的参数集 + 留痕。
    """
    values: Dict[str, Any] = dict(baseline)
    landed: List[str] = []
    for name, value in plan.assignments:
        values[name] = value
        landed.append(name)

    # MEL 是算法侧的「标」⇒ 这里按口径换算成可落地的计量位置目标
    fill_target: Optional[FillTarget] = None
    if plan.mel_targets:
        old_values = previous if previous is not None else baseline
        if plan.target_mode == 'fill_ratio' and fill_weights is not None:
            target_weight, actual_weight = fill_weights
            resolved = resolve_fill_target(
                values,
                target_weight=target_weight,
                actual_weight=actual_weight,
                previous=old_values,
            )
            if resolved is not None and resolved.field_name in values:
                values[resolved.field_name] = resolved.target_value
                landed.append(resolved.field_name)
                fill_target = resolved
            else:
                # 比例口径解不出来 ⇒ 回落增量口径
                landed.extend(apply_mel_targets(
                    values, plan.mel_targets, previous=old_values))
        else:
            landed.extend(apply_mel_targets(
                values, plan.mel_targets, previous=old_values))

    outcome = integrate(values, previous if previous is not None else baseline)
    return replace(
        outcome,
        landed=tuple(landed),
        fill_target=fill_target,
        landing_blocked=_detect_zero_landing(baseline, plan, outcome),
    )


def _detect_zero_landing(
    baseline: Mapping[str, Any],
    plan: AdjustmentPlan,
    outcome: IntegratedParams,
) -> Optional[Tuple[str, ...]]:
    """**第3层自检**：本该落地（上层裁决出了保留项）却一个量都没动。

    【注意】**这是第3层的自检** —— 判据是「L3 的产出 vs L3 的入参」，
    参照系完全落在第3层内 ⇒ 调用方不需要提供任何额外信息。

    【注意】**「上层一条候选都没保留」不在本自检范围内** ——
    那说明「本轮该调什么」根本不存在，是另一回事（既有行为：不报错）。

    ⚠️ **不能用** :attr:`IntegratedParams.touched` 判「值到底变没变」
    （它不含 ``direct_fields``，为 True 不代表值真的变了）⇒ 必须用
    :func:`diff_numeric_fields` 逐字段比。

    Args:
        baseline: 改动前的参数集。
        plan: 第2层给出的调整计划（判「本该落地」用它）。
        outcome: 本次整合的结果（判「有没有落地」用它）。

    Returns:
        ``None`` ⇒ 没这个问题；否则返回**保留项**（诊断用，供调用方留痕）。
    """
    if not plan.kept:
        return None
    if diff_numeric_fields(baseline, outcome.values):
        return None
    return tuple(plan.kept)


__all__ = [
    # 锚点传导
    'LINK_RULES',
    'FREEDOM_OVERRIDES',
    'LinkRule',
    'PropagationResult',
    'propagate',
    # 参数集自洽
    'IntegratedParams',
    'integrate',
    'diff_numeric_fields',
    'numeric_snapshot',
    'is_number',
    # 方向落地
    'apply_plan',
]
