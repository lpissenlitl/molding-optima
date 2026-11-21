"""锚点关系的事实：字段口径 + 共用判据（第2层 / 第3层 / 第4层共用）。

为什么单独放一个模块：同一批锚点关系要**被多个方向使用** ——

- **第2层**（``decide_direction.py``）：按调机策略**筛规则**（**不碰参数**）；
- **第3层**（``integrate_params.py``）：按关系**改值**（联动传播）；
- **第4层**（``check_params.py``）：按关系**只读校验**（锚点自检）。

关系本身（谁等于谁、哪些量必须递增、谁的改动要让给谁）只应**定义一次** ⇒
字段口径与共用判据放这里，各层各自引用，不各自复制：

- **字段口径**（本模块）：G1 / G2 / G3 涉及的字段名与模板；
- **共用判据**（本模块）：:func:`find_chain_break`（回抽链断裂判定）、
  :func:`resolve_stage_count`（段数解析）、:func:`last_stage_field`（末段字段名）、
  :func:`unlandable_params`（**落不了地**的物理判据）。

各层**各自**的只有"拿关系做什么"：第3层改值、第4层透传事实。

字段名：**代码侧**业务字段名（与 ``ProcessParameterSchema`` 对齐）；
与算法/工艺侧命名的对照见 ``integrate_params.py`` 模块 docstring。
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


# --- G1 计量终止位置 -------------------------------------------------------

#: 计量终止位置（``MEL``）—— **自动计算量**（由 G1 关系算出）。
G1_AUTO_FIELD = 'met_end_pos'

#: 熔胶后松退距离（``DDAM``）—— G1 关系的另一侧。
G1_BACKOFF_FIELD = 'pst_met_decomp_dist'

#: 末段熔胶位置（``ML_N``）的字段模板（``{last}`` = 实际段数）。
G1_LAST_TEMPLATE = 'met_pos_{last}'


# --- G2 回抽链 -------------------------------------------------------------

#: 各段熔胶位置的字段模板（``{i}`` = 段序，从 1 起）。
G2_CHAIN_TEMPLATE = 'met_pos_{i}'

#: VP 切换位置（``VPTL``）—— 回抽链的起点下界。
G2_VPS_FIELD = 'vps_pos'


#: 计量段数字段（``met_stg``）。
STAGE_COUNT_FIELD = 'met_stg'


# --- G3 自由度让位 ---------------------------------------------------------

#: **自由度让位关系**：被让位的量 → 让给谁（业务字段名 → 业务字段名）。
#:
#: G3 口径（用户口径）：注射阶段是**速度控制**，设定时间只是设定值
#: ⇒ 改「注射时间」没有物理意义，真正起作用的是「注射速度」
#: ⇒ 改时间让位给速度（改速度不联动时间）。
#:
#: 【注意】**本关系由第3层执行**（:mod:`process.algorithms.integrate_params`）：
#:    让位对象本轮不可调（场景禁入 / 基线项）时，被让位的量**也无处可去**
#:    —— 第3层的让位是**值回退**（改了也不生效）⇒ 该量本轮**落不了地**。
#:    ⇒ 关系放**底座**（只定义一次），第3层引用它执行。
#:
#: 【注意】**第2层不预判它**（用户口径：第2层只按调机策略筛规则，
#:    不为单个字段做兜底）⇒ 「让位对象不可调 ⇒ 本量落不了地」由第3层回答。
FREEDOM_YIELDS: Mapping[str, str] = {'inj_t': 'inj_spd_1'}


# --- 共用判据 --------------------------------------------------------------

def resolve_stage_count(params: Mapping[str, object]) -> Optional[int]:
    """计量段数；缺或不可解析 ⇒ ``None``（回落口径：缺数据不臆造）。"""
    raw = params.get(STAGE_COUNT_FIELD)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def last_stage_field(stage_count: int) -> str:
    """末段熔胶位置的字段名（``ML_N``）。"""
    return G1_LAST_TEMPLATE.format(last=stage_count)


def chain_stage_fields(stage_count: int) -> Tuple[str, ...]:
    """各段熔胶位置的字段名（按段序）。"""
    return tuple(G2_CHAIN_TEMPLATE.format(i=index) for index in range(1, stage_count + 1))


def resolve_mel_target(
    params: Mapping[str, object],
    mel_value: object,
    previous: Optional[Mapping[str, object]] = None,
) -> Optional[Tuple[str, float]]:
    """MEL 目标值 ⇒ 决策量（计量末段位置 ``ML_N``）。

    「**先定 ML，再确定 MEL**」（用户口径）：``MEL`` 是算法侧的
    **标**（由 ``ML_N + DDAM`` 算出），落到能决策的量上要先算出 ``ML_N``，
    ``MEL`` 再由 ``ML_N`` 算出。

    **推算只用「旧值 + 调整量」**（用户口径）—— L3 手里没有
    「新值」这个东西，只有**旧值**与**调整量**。两步式：

    .. code-block:: text

        1. ML_N 基准 = 原MEL − 原DDAM
        2. MEL_新    = ML_N + DDAM + ΔDDAM + ΔMEL

    ⇒ 落库的计量位置 = ``原ML_N + ΔMEL``：**``ΔDDAM`` 不叠加到计量位置**，
    它落在 ``MEL`` 那一侧（终止位置随松退距离自然后移）。

    - ``ML_N`` 基准：按 ``原MEL − 原DDAM`` 反推（不取参数集里的 ``ML_N``）；
    - ``ΔMEL``：MEL 目标与旧 MEL 之差。

    【注意】缺**旧值**就算不出调整量 ⇒ 返回 ``None``（不臆造）。

    Args:
        params: 当前参数集（含本轮调整后的值）。
        mel_value: MEL 目标值。
        previous: 旧值基线（现状参数集）；缺则无法推算 ⇒ ``None``。

    Returns:
        ``(末段计量位置字段名, ML 目标值)``；缺段数 / 缺旧值 / 缺 DDAM /
        目标值不可解析 ⇒ ``None``（回落口径：不臆造）。
    """
    stage_count = resolve_stage_count(params)
    if stage_count is None:
        stage_count = resolve_stage_count(previous or {})
    if stage_count is None:
        return None
    last = last_stage_field(stage_count)

    if previous is None:
        return None          # 没有旧值 ⇒ 算不出调整量 ⇒ 不臆造

    old_auto = previous.get(G1_AUTO_FIELD)
    old_backoff = previous.get(G1_BACKOFF_FIELD)
    if old_auto is None or old_backoff is None:
        return None          # 缺原 MEL / 原 DDAM ⇒ 反推不出计量位置 ⇒ 不臆造

    try:
        base_last = float(old_auto) - float(old_backoff)   # 1. 原MEL − 原DDAM
        delta_mel = float(mel_value) - float(old_auto)
    except (TypeError, ValueError):
        return None

    return last, base_last + delta_mel


def apply_mel_targets(
    params: Dict[str, Any],
    mel_targets: Sequence[Any],
    previous: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, ...]:
    """把 **MEL 目标**翻成**决策量**（计量末段位置），就地写入 ``params``。

    「**先定 ML，再确定 MEL**」（用户口径）：``MEL`` 是算法侧的
    **标**（由 ``ML_N + DDAM`` 算出），机台上真正会被调的是计量位置 ⇒ 算法
    说「调 MEL」时，先把目标落成计量位置（决策量），``MEL`` 再由它算出。

    **推算只用「旧值 + 调整量」**（用户口径）：

    .. code-block:: text

        1. ML_N 基准 = 原MEL − 原DDAM
        2. ML_N_新   = 基准 + ΔMEL

    ⇒ ``ΔDDAM`` **不叠加**到计量位置，它落在 ``MEL`` 那一侧。

    【注意】**本函数只负责换算**（纯物理）—— 换不换得出来由数据决定，
    换出来后**记不记账**（进了哪一轮的落地清单）由调用方负责
    ⇒ 第3层（:mod:`process.algorithms.integrate_params`）调用。

    Args:
        params: 参数集（**就地**更新）。
        mel_targets: MEL 目标值序列。
        previous: 旧值基线（现状参数集）—— 推算调整量的依据；缺则不落地。

    Returns:
        实际落地了的字段名（未落地 = 回落：缺段数 / 缺旧值 / 缺储后松退距离 /
        末段计量位置不在参数集里 ⇒ 不臆造）。
    """
    landed: List[str] = []
    for mel_value in mel_targets:
        resolved = resolve_mel_target(params, mel_value, previous=previous)
        if resolved is None:
            continue        # 回落：缺段数 / 缺储后松退距离 ⇒ 不臆造
        field_name, ml_value = resolved
        if field_name not in params:
            continue        # 回落：末段计量位置不在参数集里 ⇒ 没有落点
        params[field_name] = ml_value
        landed.append(field_name)
    return tuple(landed)


@dataclass(frozen=True)
class FillTarget:
    """充填量目标 —— 按**重量比例**解算出的注射行程目标。

    与 :func:`resolve_mel_target` 是**两种口径**：

    - :func:`resolve_mel_target`：**增量**口径（旧 ``MEL`` + ``ΔMEL``）；
    - 本类：**比例**口径（行程 × 重量比）—— 回答「充填量不足，行程该到哪」。

    Attributes:
        field_name: 落点字段名（末段熔胶位置 ``met_pos_N``）。
        target_value: 目标值（末段熔胶位置）。
        current_value: 当前值（末段熔胶位置）。
        current_stroke: 当前实际注射行程（``ML_N − VPTL``）。
        target_stroke: 目标注射行程。
        ratio: 行程比例（= 目标重量 / 实测重量）。
        reason: 依据说明（进留痕，回答「为什么行程该到这个值」）。
    """

    field_name: str
    target_value: float
    current_value: float
    current_stroke: float
    target_stroke: float
    ratio: float
    reason: str = ''


def resolve_fill_target(
    params: Mapping[str, object],
    target_weight: object,
    actual_weight: object,
    previous: Optional[Mapping[str, object]] = None,
) -> Optional[FillTarget]:
    """充填量目标求解：按重量比例解算**注射行程**目标。

    物理口径：充填量 ∝ 制品重量，充填量 ∝ 注射行程 ⇒

    .. code-block:: text

        目标行程 = 当前行程 × (目标重量 / 实测重量)
        ML_N 目标 = VPTL + 目标行程

    （注射行程 = ``ML_N − VPTL``；``DDAM`` 是螺杆回抽量，**不**参与注射量计算。）

    【注意】**这是目标，不是增量** —— 落库的是「改完之后的值」；
    与 :func:`resolve_mel_target` 的「旧 MEL + ΔMEL」不是同一口径。

    【注意】**不静默截断**：解不出来就返回 ``None``（调用方回落到规则增量口径）；
    越限也**照实解算**（由调用方留痕）—— 截断会把「差多少」这个信息吃掉。

    Args:
        params: 当前参数集（业务字段名 → 值）。
        target_weight: 目标制品重量 [g]。
        actual_weight: 实测制品重量 [g]。
        previous: 旧值基线；``params`` 缺字段时从这里回落取。

    Returns:
        :class:`FillTarget`；缺段数 / 缺 VPTL / 缺当前 ML_N / 重量不可用 /
        当前行程非正 ⇒ ``None``（回落口径：不臆造）。
    """
    stage_count = resolve_stage_count(params)
    if stage_count is None:
        stage_count = resolve_stage_count(previous or {})
    if stage_count is None:
        return None

    last = last_stage_field(stage_count)
    current = _pick_value(params, previous, last)
    vps = _pick_value(params, previous, G2_VPS_FIELD)
    if current is None or vps is None:
        return None

    try:
        current_value = float(current)
        vps_value = float(vps)
        target = float(target_weight)
        actual = float(actual_weight)
    except (TypeError, ValueError):
        return None

    if target <= 0 or actual <= 0:
        return None

    current_stroke = current_value - vps_value
    if current_stroke <= 0:
        return None              # 当前行程非正 ⇒ 比例无从谈起

    ratio = target / actual
    target_stroke = current_stroke * ratio
    target_value = vps_value + target_stroke

    return FillTarget(
        field_name=last,
        target_value=target_value,
        current_value=current_value,
        current_stroke=current_stroke,
        target_stroke=target_stroke,
        ratio=ratio,
        reason=(
            f'按充填量比例解算行程：目标重量 {target:g}g / 实测重量 {actual:g}g '
            f'⇒ 行程 {current_stroke:.2f}mm → {target_stroke:.2f}mm'
        ),
    )


def _pick_value(
    params: Mapping[str, object],
    previous: Optional[Mapping[str, object]],
    name: str,
) -> Optional[object]:
    """取一个字段的当前值；``params`` 里没有 ⇒ 从旧值基线回落取。"""
    value = params.get(name)
    if value is None and previous:
        value = previous.get(name)
    return value


def find_chain_break(
    values: Mapping[str, float],
    stage_count: int,
) -> Optional[Tuple[str, str, str]]:
    """回抽链断裂判定（**共用判据**）：返回 ``(较低段, 较高段, 说明)``；无断裂 ⇒ ``None``。

    判据（物理事实）：螺杆分多次往回抽，各段终点必须**严格递增**，
    否则某段变成往前推，回抽过程不成立；第一段还必须大于 ``VPTL``
    （否则首段回抽量 ≤ 0）。

    Args:
        values: 当前参数集（业务字段名 → 数值）。
        stage_count: 计量段数。

    Returns:
        ``(较低段, 较高段, 说明)``；无断裂 ⇒ ``None``。
    """
    names = chain_stage_fields(stage_count)
    present = [name for name in names if name in values]
    if len(present) < 2:
        return None

    for lower, higher in zip(present, present[1:]):
        if values[higher] <= values[lower]:
            return lower, higher, f'{higher}({values[higher]}) ≤ {lower}({values[lower]})'

    first = present[0]
    vps = values.get(G2_VPS_FIELD)
    if vps is not None and values[first] <= vps:
        return G2_VPS_FIELD, first, f'{first}({values[first]}) ≤ {G2_VPS_FIELD}({vps})'
    return None


def unlandable_params(
    blocked_params: Iterable[str] = (),
    available_params: Iterable[str] = (),
) -> Mapping[str, str]:
    """本轮**落不了地**的候选项（让位对象不可调 ⇒ 本量无处可去）。

    背景：:data:`FREEDOM_YIELDS` 声明「被让位的量 → 让给谁」。
    第3层的让位是**值回退**（改了也让位 ⇒ 不生效），
    所以当让位对象本轮**不可调**（场景禁入 / 基线项）时，
    被让位的量**改了也是白改**。

    【注意】**让位对象缺值时不算数**：让位对象在参数集里没有值 ⇒
    第3层不会触发让位（:func:`process.algorithms.integrate_params.propagate`
    的让位前提是让位对象有值）⇒ 本量仍可落地 ⇒ 不排除。

    【注意】**第2层已不再用它做预判**（用户口径：第2层只按调机策略筛规则，
    不为单个字段做兜底）⇒ 本函数是**底座的物理判据**，
    供第3层 / 规则层在需要时引用。

    Args:
        blocked_params: 本轮**不可调**的字段名（场景禁入清单）。
        available_params: 当前参数集里**有值**的字段名。

    Returns:
        落不了地的字段名 → 让位对象字段名（按 :data:`FREEDOM_YIELDS` 声明序）。
    """
    blocked = set(blocked_params or ())
    available = set(available_params or ())
    return {
        name: free
        for name, free in FREEDOM_YIELDS.items()
        if free in blocked and free in available
    }


__all__ = [
    'G1_AUTO_FIELD',
    'G1_BACKOFF_FIELD',
    'G1_LAST_TEMPLATE',
    'G2_CHAIN_TEMPLATE',
    'G2_VPS_FIELD',
    'STAGE_COUNT_FIELD',
    'FillTarget',
    'resolve_stage_count',
    'last_stage_field',
    'chain_stage_fields',
    'resolve_mel_target',
    'apply_mel_targets',
    'resolve_fill_target',
    'find_chain_break',
]
