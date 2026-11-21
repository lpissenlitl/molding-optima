"""第2层：结合实际情况，确定**明确的调整计划**。

这一层回答一个问题：**算法给的那一堆平级建议，到底这一轮要调哪几个、调到什么值、
按什么次序调、谁让位。**

输入（全是数据，不含业务判断）：
- **实际情况**（:class:`ScenarioContext`）：本轮的缺陷码、实测重量、目标重量、充填缺口；
- **策略数据**（:class:`ScenarioStrategy` + :class:`PriorityTable`）：命中哪个场景、
  允许调哪些、按什么次序、留几个；
- **候选建议**：算法给的平级建议（字段名 + 目标值）。

输出（:class:`AdjustmentPlan`）：**调整计划** —— 一串「字段名 + 目标值」，
加上让位 / 暂缓的理由与依据（留痕）。

【注意】**本层不整合参数**：方向定了之后，「怎么把它落成自洽的参数集」是第3层
（:mod:`process.algorithms.integrate_params`）的事；「合不合理」是第4层
（:mod:`process.algorithms.check_params`）的事。

红线（不变）：**业务判断必须是数据** ——
- 场景是什么、条件是什么、允许调哪些、优先哪个 ⇒ 都在策略表里，本模块只读；
- 物理算式（充填量→行程、MEL 目标→计量位置）⇒ 落代码，因为那是**逻辑**
  （解释规则的方式固定），而**规则本体可增长**；
- 本模块**不内置任何业务次序**。

【重要】**本层不碰参数**（用户口径）—— 本层只做**规则筛选**：

- 候选字段「**本机有没有值**」「当前有没有值」都**不在这里判** ⇒ 本层不读参数集；
- 「**这是不是工艺量**」在**候选准入**判（命名契约：静态字段字典）⇒
  不是工艺量的（``IPOS`` 这类规则库专用参数）**不进候选**，不靠下游兜底
  （兜底 = 掩饰错误）；
- 「改成多少」（MEL 标 → 计量位置的物理换算）⇒ 第3层（它手上有旧值）。

⇒ 第2层的入参只有三类：**候选建议** + **实际情况** + **策略数据**。

字段名：业务字段名，与 ``ProcessParameterSchema`` 对齐。
"""

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from .anchors import (
    G1_AUTO_FIELD,
)
from .fuzzy.field_names import to_business_name


# ===========================================================================
# 实际情况（从反馈与模具上下文派生的本轮事实）
# ===========================================================================

#: 观察项键：实测制品重量（``feedback.observations[].param_key``）
ACTUAL_WEIGHT_KEY = 'actual_product_weight'

#: 制品总重在 ``mold_info`` 里的键（契约见 ``fuzzy/specs.py``）
TARGET_WEIGHT_KEY = 'total_product_weight'

#: 标准派生字段名 → 属性名（**标准字段的取值只有一个出处**，不散落各处）。
_STANDARD_FIELD_ATTRS = {
    'defect_codes': 'defect_codes',
    'actual_weight': 'actual_weight',
    'target_weight': 'target_weight',
    'fill_gap': 'fill_gap',
}

#: 标准派生字段清单（**不是白名单闸门** —— 条件还可引用 ``ScenarioContext.extra``
#: 里注入的任意键；条件里写错字段名 ⇒ 不命中，不静默通过）。
CONTEXT_FIELDS: Tuple[str, ...] = tuple(_STANDARD_FIELD_ATTRS)


@dataclass(frozen=True)
class ScenarioContext:
    """**实际情况** —— 本轮的事实（场景判定的输入）。

    Attributes:
        defect_codes: 推导所用的缺陷码（英文名，如 ``SHORTSHOT``）。
        actual_weight: 实测制品重量 [g]。
        target_weight: 制品总重 [g]。
        fill_gap: 充填缺口 [g]（``target − actual``；缺任一 ⇒ ``None``）。
        extra: **附加字段**（条件可引用的额外键）—— 由调用方注入
            （如 ``selected_defect`` / ``stage``）。
    """

    defect_codes: Tuple[str, ...] = ()
    actual_weight: Optional[float] = None
    target_weight: Optional[float] = None
    fill_gap: Optional[float] = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def value_of(self, field_name: str) -> Any:
        """取一个可参与条件判定的字段值。

        - **标准字段**：4 个派生量（取值只有一个出处，见 :data:`CONTEXT_FIELDS`）；
        - **附加字段**：``extra`` 里注入的任意键；
        - 未知字段名 ⇒ ``None``（⇒ 条件不命中，不臆造）。
        """
        attr_name = _STANDARD_FIELD_ATTRS.get(field_name)
        if attr_name is not None:
            return getattr(self, attr_name)
        if self.extra:
            return self.extra.get(field_name)
        return None


def build_scenario_context(
    feedback: Optional[Mapping[str, Any]] = None,
    mold_info: Optional[Mapping[str, Any]] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> ScenarioContext:
    """由反馈与模具上下文构造**实际情况**（派生量的唯一出处）。

    Args:
        feedback: 缺陷反馈（``defects[]`` / ``observations[]``）。
        mold_info: 模具上下文（取 ``total_product_weight``）。
        extra: **附加字段**（条件可引用的额外键，如 ``selected_defect``）。

    Returns:
        :class:`ScenarioContext` —— 缺什么就是 ``None``（不臆造）。
    """
    feedback = feedback or {}
    mold_info = mold_info or {}

    defect_codes: List[str] = []
    for item in feedback.get('defects') or ():
        if not isinstance(item, Mapping):
            continue
        code = item.get('keyword_name')
        if code:
            defect_codes.append(str(code))

    actual_weight = _observation_value(feedback.get('observations'), ACTUAL_WEIGHT_KEY)
    target_weight = _to_float(mold_info.get(TARGET_WEIGHT_KEY))

    fill_gap: Optional[float] = None
    if actual_weight is not None and target_weight is not None:
        fill_gap = target_weight - actual_weight

    return ScenarioContext(
        defect_codes=tuple(defect_codes),
        actual_weight=actual_weight,
        target_weight=target_weight,
        fill_gap=fill_gap,
        extra=dict(extra or {}),
    )


def match_conditions(
    conditions: Sequence[Mapping[str, Any]],
    context: ScenarioContext,
) -> bool:
    """条件求值（**AND**）—— 全部成立才命中；空条件 = 无条件命中。

    【注意】**缺数据 ⇒ 不命中**（不臆造）：引用了拿不到的量 ⇒ 该条不成立。
    【注意】**未知操作符 ⇒ 不命中**（不猜）：条件写错时表现为「这条策略没生效」，
    而不是「静默按默认语义放过」。

    Args:
        conditions: 条件列表（策略表 ``conditions`` 字段）。
        context: 实际情况。

    Returns:
        ``True`` = 命中。
    """
    for condition in conditions or ():
        if not isinstance(condition, Mapping):
            continue
        field_name = condition.get('field')
        operator = condition.get('operator', 'exact')
        target = condition.get('value')

        field_value = context.value_of(field_name) if field_name else None
        if field_value is None:
            return False
        if not _compare(field_value, operator, target):
            return False
    return True


def select_strategy(
    strategies: Sequence['ScenarioStrategy'],
    context: ScenarioContext,
) -> Optional['ScenarioStrategy']:
    """选出**第一条命中**的策略（候选须已按「优先级」排好序）。

    【注意】**取第一条而非合并**：一条策略 = 一套完整的经验组合；
    合并多条的语义（谁覆盖谁）会随条数增加而含糊 ⇒ 留到有需求时再定。

    Args:
        strategies: 候选策略（**已排序**：按优先级升序）。
        context: 实际情况。

    Returns:
        命中的 :class:`ScenarioStrategy`；一条都不命中 ⇒ ``None``
        （⇒ 不裁决，行为与「不接第2层」一致）。
    """
    for strategy in strategies:
        if match_conditions(strategy.conditions, context):
            return strategy
    return None


def _observation_value(
    observations: Optional[Sequence[Mapping[str, Any]]],
    param_key: str,
) -> Optional[float]:
    """从观察项列表里取某个键的实测值；缺 / 不可解析 ⇒ ``None``。"""
    for item in observations or ():
        if not isinstance(item, Mapping):
            continue
        if item.get('param_key') != param_key:
            continue
        value = _to_float(item.get('value'))
        if value is not None:
            return value
    return None


def _to_float(value: Any) -> Optional[float]:
    """转 float；不可解析 / 非数值 ⇒ ``None``（``bool`` 先排除，它是 ``int`` 子类）。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compare(field_value: Any, operator: str, target: Any) -> bool:
    """单条件比较。"""
    if operator == 'exact':
        return field_value == target
    if operator == 'in':
        return _contains(field_value, target)
    if operator == 'not_in':
        return not _contains(field_value, target)
    if operator == 'contains':
        return _contains(field_value, target)
    if operator == 'not_contains':
        return not _contains(field_value, target)
    if operator == 'in_set':
        return _is_in_set(field_value, target)
    if operator == 'not_in_set':
        return not _is_in_set(field_value, target)
    if operator == 'in_any':
        return _any_in_set(field_value, target)

    left = _to_float(field_value)
    right = _to_float(target)
    if left is None or right is None:
        return False
    if operator == 'gt':
        return left > right
    if operator == 'gte':
        return left >= right
    if operator == 'lt':
        return left < right
    if operator == 'lte':
        return left <= right
    return False           # 未知操作符 ⇒ 不命中（不猜）


def _contains(haystack: Any, needle: Any) -> bool:
    """``needle in haystack``；类型不支持 ⇒ ``False``（不抛错）。"""
    try:
        return needle in haystack
    except TypeError:
        return False


def _is_in_set(value: Any, container: Any) -> bool:
    """**单值 ∈ 集合**（与 :func:`_contains` 方向相反：字段值是单值，目标是容器）。

    【注意】**容器不能是字符串** —— 否则 ``'SHO' in 'SHORTSHOT'`` 会变成子串匹配。
    """
    if isinstance(container, (str, bytes, Mapping)):
        return False
    try:
        return value in container
    except TypeError:
        return False


def _any_in_set(field_value: Any, container: Any) -> bool:
    """**集合中任一元素 ∈ 目标集合**（字段值是集合，目标也是集合）。

    【注意】与 :func:`_is_in_set` **方向相反**，两者并存不混：

    - ``in_set``  —— 字段值是**单值**：``'SHRINKAGE' in ('SHRINKAGE', ...)``
    - ``in_any``  —— 字段值是**集合**（如 ``defect_codes``）：
      ``('A','B')`` 与 ``('B',)`` ⇒ 命中（``'B'`` 在里面）

    【注意】**字段值不能是字符串** —— 否则会逐字符匹配（``'SHO'`` 的每个字符）。
    【注意】**容器不能是字符串** —— 否则退化成子串匹配。
    """
    if isinstance(field_value, (str, bytes)) or isinstance(container, (str, bytes, Mapping)):
        return False
    try:
        return any(item in container for item in field_value)
    except TypeError:
        return False


# ===========================================================================
# 策略数据（业务知识 —— 全部来自策略表，本模块只读不判）
# ===========================================================================


@dataclass(frozen=True)
class PriorityEntry:
    """优先级表的一条条目。

    Attributes:
        param_name: 业务字段名（与 ``ProcessParameterSchema`` 对齐）。
        priority: 优先级数值，**越小越优先**。
        group: 业务分组（如 ``filling`` / ``holding``），用于整组语义表达。
        reason: 依据说明（进决策留痕，回答「为什么它排在前面」）。
    """

    param_name: str
    priority: int
    group: str = ''
    reason: str = ''


@dataclass(frozen=True)
class PriorityTable:
    """数据化的参数优先级表。

    表的内容由调用方从策略表 / 配置读入后构造 —— 本模块不内置任何业务次序。

    Attributes:
        entries: 优先级条目。
        default_priority: 表中未列出的字段使用的优先级（数值越大越靠后）。
    """

    entries: Tuple[PriorityEntry, ...] = ()
    default_priority: int = 1000

    def priority_of(self, param_name: str) -> int:
        """字段的优先级数值；表中未列出则返回 :attr:`default_priority`。"""
        for entry in self.entries:
            if entry.param_name == param_name:
                return entry.priority
        return self.default_priority

    def group_of(self, param_name: str) -> str:
        """字段所属业务分组；表中未列出则返回空串。"""
        for entry in self.entries:
            if entry.param_name == param_name:
                return entry.group
        return ''

    def reason_of(self, param_name: str) -> str:
        """字段的优先级依据；表中未列出则返回空串。"""
        for entry in self.entries:
            if entry.param_name == param_name:
                return entry.reason
        return ''

    @classmethod
    def from_entries(cls, entries: Iterable[PriorityEntry]) -> 'PriorityTable':
        """由条目序列构造。"""
        return cls(entries=tuple(entries))


@dataclass(frozen=True)
class ScenarioStrategy:
    """**场景策略** —— 一条经验组合（由调用方从策略清单读出后构造）。

    场景 = 「这一轮属于哪类情形」⇒ 它回答四个问题：

    1. **调哪些**（:attr:`allowed_params`）：不在白名单 ⇒ 让位，理由「本场景不允许」；
    2. **按什么次序**（:attr:`preferred_params`）：场景优先集排在字段级优先级之前；
    3. **留几个**（:attr:`max_items`）：名额用满 ⇒ 暂缓；
    4. **目标怎么算**（:attr:`target_mode`）：按规则增量，还是按充填量比例解算行程。

    【注意】**与优先级表的分工**：优先级表回答「字段之间谁先谁后」（字段级），
    场景策略回答「这一轮是哪种情形」（轮次级）。两者都是**数据**，
    本模块只提供裁决机制。

    Attributes:
        scenario_code: 场景码（如 ``filling_first``）—— 留痕用。
        allowed_params: 准入白名单（**空 = 不限制**，默认全允许）。
        blocked_params: 禁入清单（**空 = 不禁**）—— 不在其内的候选让位，
            理由「基线项 ⇒ 不参与阶段调机」。
            【注意】与 :attr:`allowed_params` 的分工：**白名单是场景范围**（这个场景
            该动哪些），**禁入清单是基线项**（任何场景都不该动，如注射速度）。
            二者不是一回事 —— 白名单可空（不限制），禁入清单独立生效。
        preferred_params: 场景优先集（按序，越前越优先）。
        max_items: 本轮名额（``None`` = 不限）。
        target_mode: 目标求解方式 —— ``'delta'``（按规则增量，默认）
            / ``'fill_ratio'``（按充填量比例解算行程）。
        reason: 依据说明（进留痕，回答「为什么是这个场景、为什么它排前面」）。
        conditions: 触发条件（``field`` / ``operator`` / ``value`` 的列表）。
        priority: 同层内的优先级（数值越小越优先）。
        priority_table: 本场景的**字段级**优先级表（空表 = 不按字段级排序）。
    """

    scenario_code: str = ''
    allowed_params: Tuple[str, ...] = ()
    blocked_params: Tuple[str, ...] = ()
    preferred_params: Tuple[str, ...] = ()
    max_items: Optional[int] = None
    target_mode: str = 'delta'
    reason: str = ''
    conditions: Tuple[Mapping[str, Any], ...] = ()
    priority: int = 100
    priority_table: PriorityTable = field(default_factory=PriorityTable)

    @property
    def uses_fill_ratio(self) -> bool:
        """是否按**充填量比例**解算行程。"""
        return self.target_mode == 'fill_ratio'


@dataclass(frozen=True)
class StrategyDecision:
    """裁决结果（谁保留 / 谁让位 / 谁暂缓）。

    Attributes:
        kept: 保留并执行的候选（按裁决后的次序）。
        kept_reasons: 保留项的**依据**（字段名 → 为什么它排前面 / 被保留）。
        yielded: 让位出去的候选 → 让位理由。
        deferred: 名额用满而暂缓的候选 → 暂缓理由。
        order: 全部候选的优先级次序（含让位与暂缓项）。
        scenario_code: 命中的场景码（空 = 无场景，按字段级优先级裁决）。
    """

    kept: Tuple[str, ...] = ()
    kept_reasons: Mapping[str, str] = field(default_factory=dict)
    yielded: Mapping[str, str] = field(default_factory=dict)
    order: Tuple[str, ...] = ()
    deferred: Mapping[str, str] = field(default_factory=dict)
    scenario_code: str = ''

    def status_of(self, name: str) -> Tuple[Optional[str], str]:
        """候选字段的**裁决状态** → ``(状态, 原因)``。

        状态三取值：

        - ``adopted``：保留并执行 ⇒ 本轮真的调了它（原因 = 保留依据）；
        - ``yielded``：明确让位（原因 = 让位理由）；
        - ``deferred``：名额用满暂缓（原因 = 暂缓理由）。

        【注意】**不在候选集**（没进第2层：零变化 / 译不出 / 不在参数表里）
        ⇒ 返回 ``(None, '')`` ⇒ 调用方据此判断「这条建议没有裁决状态」
        （历史轮次没有裁决状态字段）。
        """
        if name in self.kept:
            return 'adopted', self.kept_reasons.get(name, '')
        if name in self.yielded:
            return 'yielded', self.yielded.get(name, '')
        if name in self.deferred:
            return 'deferred', self.deferred.get(name, '')
        return None, ''

    def to_trace(self) -> Dict[str, object]:
        """决策留痕载荷（写进调用方的诊断出口）。

        【注意】**让位与暂缓都要留痕** —— 二者都是「明确决定不做」，
        少任何一项都会让留痕答不出「它为什么没落地」。

        【注意】**保留项也要带依据** —— 否则反馈回来时只能证伪「调了这些量」，
        证伪不了「为什么按这个次序调」。
        """
        return {
            'kept': list(self.kept),
            'kept_reasons': dict(self.kept_reasons),
            'yielded': dict(self.yielded),
            'deferred': dict(self.deferred),
            'order': list(self.order),
            'scenario_code': self.scenario_code,
        }


def resolve_priority(
    candidates: Sequence[str],
    table: PriorityTable,
    satisfied: Sequence[str] = (),
    max_items: Optional[int] = None,
    *,
    scenario: Optional[ScenarioStrategy] = None,
    veto_params: Optional[Mapping[str, str]] = None,
) -> StrategyDecision:
    """按优先级表 + 场景策略裁决候选调整，并显式让位 / 暂缓未执行的项。

    裁决口径（按先后）：

      1. **场景优先集**（:attr:`ScenarioStrategy.preferred_params`）里的候选排最前；
         同在集合内按集合次序，再按字段级优先级数值（小的在前）；
      2. **禁入**（:attr:`ScenarioStrategy.blocked_params`，非空时才生效）：
         在禁入清单的候选**让位**，理由「基线项 ⇒ 不参与阶段调机」；
      3. **准入**（:attr:`ScenarioStrategy.allowed_params`，非空时才生效）：
         不在白名单的候选**让位**，理由「本场景不允许」；
      4. **落不了地**（``veto_params``，非空时才生效）：本轮注定不生效的候选
         **让位**（理由由调用方给）—— 让位对象本轮不可调 ⇒ 改了也是白改；
      5. 落在 ``satisfied`` 里的候选**让位** —— 目标已达成，无需再调；
      6. **名额**（场景优先，其次 ``max_items``）：保留项超出名额的部分**暂缓**；
      7. 让位与暂缓都是**显式决策并留痕**，不静默丢弃；
      8. 表中未列出的候选排在最后，但**不丢弃**；
      9. **保留项也留依据**（:attr:`StrategyDecision.kept_reasons`）——
         没有依据，反馈回来只能证伪「调了这些量」，证伪不了「为什么按这个次序调」。

    【注意】**禁入排在准入之前**：基线项是**全局**理由（任何场景都不该动），
    比“本场景不允许”更强 ⇒ 同时命中两者时，留痕要写**基线项**，
    否则更强的理由会被场景理由掩盖。

    【注意】**四类让位/暂缓理由分开**：目标已达成 / 本场景不允许 / 基线项 / 名额已满 ——
    「为什么没落地」必须能分辨是哪一类。
    （「本轮落不了地」是第五类，见 ``veto_params``；编排层当前不传。）

    【注意】**无场景 ⇒ 行为与「不接第2层」完全一致**（表为空 ⇒ 全部候选保留、原序）。

    Args:
        candidates: 候选调整的字段名（业务字段名）。
        table: 数据化优先级表。
        satisfied: 已达成目标的字段名。
            【注意】**本模块不判定目标是否达成** —— 那是业务判据，
            必须由调用方从派生输入量表算出后传入。
        max_items: 本轮最多执行的项数（``None`` 表示不限）；
            场景策略里给了名额时，以场景的为准。
        scenario: 场景策略（``None`` = 无场景，只按优先级表裁决）。
        veto_params: **本轮落不了地**的候选 → 让位理由（字段名 → 理由）。
            【注意】判据由调用方给（物理关系在底座
            :func:`process.algorithms.anchors.unlandable_params`）——
            本模块只读，不内置物理知识。
            【注意】**编排层当前不传这一项**（用户口径：第2层不掺合参数、
            不为单个字段做兜底）⇒ 「改了会不会白改」由第3层回答。

    Returns:
        :class:`StrategyDecision` —— 保留项、让位项与暂缓项、完整次序。
    """
    satisfied_set = set(satisfied)
    vetoed = dict(veto_params or {})

    allowed = tuple(scenario.allowed_params) if scenario is not None else ()
    allowed_set = set(allowed)
    blocked = tuple(scenario.blocked_params) if scenario is not None else ()
    blocked_set = set(blocked)
    preferred = tuple(scenario.preferred_params) if scenario is not None else ()
    preferred_rank = {name: index for index, name in enumerate(preferred)}

    effective_max = max_items
    if scenario is not None and scenario.max_items is not None:
        effective_max = scenario.max_items

    indexed = list(enumerate(candidates))
    ordered = sorted(
        indexed,
        key=lambda item: (
            preferred_rank.get(item[1], len(preferred_rank)),
            table.priority_of(item[1]),
            item[0],
        ),
    )

    kept: List[str] = []
    kept_reasons: Dict[str, str] = {}
    yielded: Dict[str, str] = {}
    deferred: Dict[str, str] = {}
    order: List[str] = []

    for _, candidate in ordered:
        order.append(candidate)
        if blocked_set and candidate in blocked_set:
            yielded[candidate] = f'基线项（{candidate}）⇒ 不参与阶段调机'
            continue
        if allowed_set and candidate not in allowed_set:
            reason = (scenario.reason if scenario is not None else '') or '场景准入'
            yielded[candidate] = f'{reason} ⇒ 本场景不允许'
            continue
        if candidate in vetoed:
            yielded[candidate] = vetoed[candidate]
            continue
        if candidate in satisfied_set:
            reason = table.reason_of(candidate) or '目标已达成'
            yielded[candidate] = f'{reason} ⇒ 让位'
            continue
        if effective_max is not None and len(kept) >= effective_max:
            deferred[candidate] = '本轮名额已满 ⇒ 暂缓'
            continue
        kept.append(candidate)
        reason = _kept_reason(candidate, table, scenario, preferred_rank)
        if reason:
            kept_reasons[candidate] = reason

    return StrategyDecision(
        kept=tuple(kept),
        kept_reasons=kept_reasons,
        yielded=yielded,
        order=tuple(order),
        deferred=deferred,
        scenario_code=(scenario.scenario_code if scenario is not None else ''),
    )


def _kept_reason(
    candidate: str,
    table: PriorityTable,
    scenario: Optional[ScenarioStrategy],
    preferred_rank: Mapping[str, int],
) -> str:
    """保留项的**依据**（回答「为什么它排前面 / 为什么它被保留」）。

    依据来源（按可信度）：

    1. **场景优先集** ⇒ 「场景 X 优先」+ 场景依据；
    2. **优先级表**里的字段依据；
    3. 场景存在但非优先项 ⇒ 「场景允许 ⇒ 保留」。
    """
    if scenario is not None:
        base = scenario.reason or f'场景「{scenario.scenario_code}」'
        if candidate in preferred_rank:
            return f'{base} ⇒ 场景优先'
        if scenario.scenario_code:
            return f'{base} ⇒ 场景允许'
    return table.reason_of(candidate)


def priority_table_from_mapping(
    mapping: Mapping[str, int],
    reasons: Optional[Mapping[str, str]] = None,
    groups: Optional[Mapping[str, str]] = None,
) -> PriorityTable:
    """由「字段 → 优先级」的映射构造优先级表。

    供调用方从策略表 / 配置读出数据后便捷构造 —— 业务次序的**唯一来源**是数据，
    本模块不内置任何具体次序。

    Args:
        mapping: 字段 → 优先级数值（越小越优先）。
        reasons: 字段 → 依据说明。
        groups: 字段 → 业务分组。

    Returns:
        :class:`PriorityTable`。
    """
    entries = tuple(
        PriorityEntry(
            param_name=field_name,
            priority=priority,
            group=(groups or {}).get(field_name, ''),
            reason=(reasons or {}).get(field_name, ''),
        )
        for field_name, priority in mapping.items()
    )
    return PriorityTable.from_entries(entries)


# ===========================================================================
# 第2层的统一入口：候选 + 实际情况 + 策略数据 ⇒ 明确的调整方向
# ===========================================================================


@dataclass(frozen=True)
class Candidates:
    """**候选集** —— 能落地的算法建议。

    Attributes:
        names: 候选字段名（业务字段名，保持建议给出的原次序）。
        targets: 字段名 → 目标值。
    """

    names: Tuple[str, ...] = ()
    targets: Mapping[str, Any] = field(default_factory=dict)


def collect_candidates(
    recommendations: Sequence[Mapping[str, Any]],
    name_of: Callable[[str], Optional[str]] = to_business_name,
) -> Candidates:
    """把算法建议翻译成**候选集**（进第2层之前的准备）。

    算法给的 ``param`` 是算法命名空间（``IV0`` / ``BT1``），必须先译回业务
    字段名（``inj_spd_1`` / ``brl_temp_1``）才能命中第2层的候选。

    **筛掉的只有「根本不算建议」的条目**：

    - 没有推荐值（经验推理只给方向不给数值）⇒ 不进；
    - 译不出业务字段名 ⇒ 不进；
    - 同一字段重复建议 ⇒ 以**首次**为准。

    【注意】**「这个字段本机有没有值」不在这儿判**（用户口径）——
    本层不读参数集；「这台机有没有值」与「这是不是工艺量」是**两件事** ⇒
    **是工艺量、但本机没值**（如 ``inj_t`` 为 null）照样进候选、照样落地。

    【注意】**「这是不是工艺量」由调用方的翻译函数判**（命名契约：静态字段
    字典）⇒ 不是工艺量的（``IPOS`` 这类规则库专用参数）翻不出来 ⇒ 不进候选
    ⇒ **下游不需要存在性兜底**（兜底 = 掩饰错误）。

    Args:
        recommendations: 算法建议列表（``param`` + ``recommended_value``）。
        name_of: 算法字段名 → 业务字段名的翻译函数。

    Returns:
        :class:`Candidates`。
    """
    names: List[str] = []
    targets: Dict[str, Any] = {}

    for rec in recommendations:
        if rec.get('recommended_value') is None:
            continue
        raw_name = rec.get('param')
        business_name = name_of(raw_name) if raw_name else None
        if not business_name:
            continue
        if business_name in targets:
            continue
        targets[business_name] = rec.get('recommended_value')
        names.append(business_name)

    return Candidates(names=tuple(names), targets=targets)


@dataclass(frozen=True)
class AdjustmentPlan:
    """**调整计划** —— 第2层的产出。

    【注意】**本层只回答「调哪几个、谁让位、什么口径」**（用户口径）——
    **不碰参数、不求落地值** ⇒ 「改成多少」是第3层的事
    （它手上有旧值，能做物理换算）。

    Attributes:
        selection: 裁决结果（谁保留 / 谁让位 / 谁暂缓 + 依据）。
        assignments: 保留项的「字段名 + 目标值」（按执行次序）——
            **非派生量**的绝对值（可直接落地）。
        mel_targets: ``MEL`` 的目标值（算法侧的「标」）—— **未换算**，
            由第3层按 :attr:`target_mode` 口径翻成计量位置目标。
        target_mode: 目标求解口径（``'fill_ratio'`` = 按充填量比例解算行程；
            ``'delta'`` / ``None`` = 按 ``MEL`` 增量）。
    """

    selection: StrategyDecision = field(default_factory=StrategyDecision)
    assignments: Tuple[Tuple[str, Any], ...] = ()
    mel_targets: Tuple[Any, ...] = ()
    target_mode: Optional[str] = None

    @property
    def kept(self) -> Tuple[str, ...]:
        """保留项（字段名，按次序）。"""
        return self.selection.kept

    @property
    def yielded(self) -> Mapping[str, str]:
        """让位项 → 让位理由。"""
        return self.selection.yielded

    @property
    def deferred(self) -> Mapping[str, str]:
        """暂缓项 → 暂缓理由。"""
        return self.selection.deferred

    @property
    def reasons(self) -> Mapping[str, str]:
        """保留项的依据（为什么它排前面）。"""
        return self.selection.kept_reasons

    @property
    def order(self) -> Tuple[str, ...]:
        """全部候选的次序（含让位与暂缓项）。"""
        return self.selection.order

    @property
    def scenario_code(self) -> str:
        """命中的场景码（空 = 无场景）。"""
        return self.selection.scenario_code

    def to_trace(self) -> Dict[str, object]:
        """留痕载荷（写进调用方的诊断出口）。"""
        trace: Dict[str, object] = dict(self.selection.to_trace())
        trace['assignments'] = [list(item) for item in self.assignments]
        trace['mel_targets'] = list(self.mel_targets)
        trace['target_mode'] = self.target_mode or ''
        return trace


def build_plan(
    candidates: Sequence[str],
    targets: Mapping[str, Any],
    context: Optional[ScenarioContext] = None,
    strategy: Optional[ScenarioStrategy] = None,
    table: Optional[PriorityTable] = None,
    satisfied: Sequence[str] = (),
    max_items: Optional[int] = None,
    veto_params: Optional[Mapping[str, str]] = None,
) -> AdjustmentPlan:
    """候选 + 实际情况 + 策略数据 ⇒ **调整计划**。

    流程：

    1. **裁决**（:func:`resolve_priority`）：准入 / 优先集 / 名额 / 让位 ——
       决定「调哪几个、按什么次序、谁没轮上」；
    2. **带出目标值**：保留项的建议值原样带出（**非派生量**是绝对值，
       可直接落地）；``MEL`` 是算法侧的**标** ⇒ 这里只记「目标值 + 口径」，
       换算成计量位置（决策量）归**第3层**。

    【注意】**本层不碰参数**（用户口径）—— 第2层只回答「调哪几个、谁让位、
    什么口径」；「改成多少」是第3层的事 ⇒ **不需要现状参数集**。

    【注意】**表为空且无场景 ⇒ 不裁决** ⇒ 保留集 = 原候选集、原序
    ⇒ **行为与「不接第2层」完全一致**。

    Args:
        candidates: 候选调整的字段名（业务字段名，已过滤掉落不了地的）。
        targets: 候选的建议目标值（字段名 → 目标值）。
        context: 实际情况（本层只作裁决参照，不参与目标值求解）。
        strategy: 命中的场景策略（``None`` = 无场景）。
        table: 数据化的优先级表（``None`` ⇒ 空表 ⇒ 只按场景裁决）。
        satisfied: 已达成目标的字段名（本模块不判定 ⇒ 由调用方传入）。
        max_items: 本轮最多执行的项数（``None`` = 不限；场景给了名额时以场景为准）。
        veto_params: **本轮落不了地**的候选 → 让位理由（透传给 :func:`resolve_priority`）。

    Returns:
        :class:`AdjustmentPlan` —— 调整计划（调哪些 + 改成多少 + 谁让位 / 暂缓 + 依据）。
    """
    selection = resolve_priority(
        candidates,
        table if table is not None else PriorityTable(),
        satisfied,
        max_items,
        scenario=strategy,
        veto_params=veto_params,
    )

    assignments: List[Tuple[str, Any]] = []
    mel_targets: List[Any] = []
    target_mode: Optional[str] = None

    # 1. 保留项的**非派生量**目标值原样带出（绝对值 ⇒ 可直接落地）
    for name in selection.kept:
        if name == G1_AUTO_FIELD or name not in targets:
            continue
        assignments.append((name, targets[name]))

    # 2. MEL 是算法侧的**标** ⇒ 本层只记「目标值 + 口径」，换算归第3层
    if G1_AUTO_FIELD in selection.kept and G1_AUTO_FIELD in targets:
        mel_targets.append(targets[G1_AUTO_FIELD])
        target_mode = strategy.target_mode if strategy is not None else None

    return AdjustmentPlan(
        selection=selection,
        assignments=tuple(assignments),
        mel_targets=tuple(mel_targets),
        target_mode=target_mode,
    )


__all__ = [
    # 实际情况
    'ACTUAL_WEIGHT_KEY',
    'TARGET_WEIGHT_KEY',
    'CONTEXT_FIELDS',
    'ScenarioContext',
    'build_scenario_context',
    'match_conditions',
    'select_strategy',
    # 策略数据
    'PriorityEntry',
    'PriorityTable',
    'ScenarioStrategy',
    'StrategyDecision',
    'resolve_priority',
    'priority_table_from_mapping',
    # 第2层入口
    'Candidates',
    'collect_candidates',
    'AdjustmentPlan',
    'build_plan',
]
