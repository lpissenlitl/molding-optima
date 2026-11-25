"""**第2层（决策层）** —— 原料 + 算法建议 ⇒ **调整方案**。

【注意】**本文件 = 第2层整体** —— 机制（怎么裁决）、规则（业务经验）、
入口（怎么跑）三部分在**同一个文件**里 ⇒ 目录里「**一个文件 = 一层**」。

这一层回答一个问题：**算法给的那一堆平级建议，到底这一轮要调哪几个、调到什么值、
按什么次序调、谁让位。**

输入（全是数据，不含业务判断）：
- **事实**（映射）：本轮的缺陷码、实测重量、目标重量、充填缺口，
  以及上一轮试模评价与上一轮实际落地的参数 —— 由 :func:`collect_facts`
  从原料挑出后传入；
- **策略数据**（:class:`ScenarioStrategy` + :class:`PriorityTable`）：命中哪个场景、
  允许调哪些、按什么次序、留几个；
- **候选建议**：算法给的平级建议（字段名 + 目标值）。

输出（:class:`AdjustmentScheme`）：**调整方案** —— 一串「字段名 + 目标值」，
加上让位 / 暂缓的理由与依据（留痕）。

【注意】**本层不整合参数**：方向定了之后，「怎么把它落成自洽的参数集」是第3层
（:mod:`process.services.optimize_chain.integrate_params`）的事；「合不合理」是第4层
（:mod:`process.services.optimize_chain.check_params`）的事。

红线（不变）：**业务判断必须是数据** ——
- 场景是什么、条件是什么、允许调哪些、优先哪个 ⇒ 都在策略表里，本模块只读；
- 物理算式（充填量→行程、MEL 目标→计量位置）⇒ 落代码，因为那是**逻辑**
  （解释规则的方式固定），而**规则本体可增长**；
- 本模块**不内置任何业务次序**。

【重要】**本层不碰参数** —— 本层只做**规则筛选**：

- 候选字段「**本机有没有值**」「当前有没有值」都**不在这里判** ⇒ 本层不读参数集；
- 「**这是不是工艺量**」在**候选准入**判（命名契约：静态字段字典）⇒
  不是工艺量的（``IPOS`` 这类规则库专用参数）**不进候选**，不靠下游兜底
  （兜底 = 掩饰错误）；
- 「改成多少」（MEL 标 → 计量位置的物理换算）⇒ 第3层（它手上有旧值）。

⇒ 第2层的入参只有三类：**候选建议** + **实际情况** + **策略数据**。

字段名：业务字段名，与 ``ProcessParameterSchema`` 对齐。
"""

import logging
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
    FILL_RATIO_MODE,
    G1_AUTO_FIELD,
    STEP_DOWN_MODE,
    read_weights,
    to_float,
)
from ..shared.param_naming import to_process_field_name


_logger = logging.getLogger(__name__)


# ===========================================================================
# 条件求值（事实按字段名取值 —— 事实表由决策层入口从原料挑出）
# ===========================================================================


#: 判定「上轮没改善」的试模评价取值（**通用判据**，不随场景变化）。
INEFFECTIVE_TUNING_RESULTS: Tuple[str, ...] = ('unchanged', 'ineffective')


def _failed_params(facts: Optional[Mapping[str, Any]]) -> Mapping[str, str]:
    """派生**上一轮证伪**的参数 → 让位理由（退阶）。

    【注意】**``unchanged``（无变化）与 ``ineffective``（变差）都算没改善** ——
    调机师傅对这两种情况的反应一样：换旋钮再试。
    """
    if not facts:
        return {}
    if facts.get('last_tuning_result') not in INEFFECTIVE_TUNING_RESULTS:
        return {}
    return {
        name: '上轮试过无改善 ⇒ 本轮不再动它'
        for name in facts.get('last_advised_params') or ()
    }


def match_conditions(
    conditions: Sequence[Mapping[str, Any]],
    facts: Mapping[str, Any],
) -> bool:
    """条件求值（**AND**）—— 全部成立才命中；空条件 = 无条件命中。

    【注意】**缺数据 ⇒ 不命中**（不臆造）：引用了拿不到的量 ⇒ 该条不成立。
    【注意】**未知操作符 ⇒ 不命中**（不猜）：条件写错时表现为「这条策略没生效」，
    而不是「静默按默认语义放过」。

    Args:
        conditions: 条件列表（策略表 ``conditions`` 字段）。
        facts: 本轮事实（键名 = 条件可引用的字段名）。

    Returns:
        ``True`` = 命中。
    """
    for condition in conditions or ():
        if not isinstance(condition, Mapping):
            continue
        field_name = condition.get('field')
        operator = condition.get('operator', 'exact')
        target = condition.get('value')

        field_value = facts.get(field_name) if field_name else None
        if field_value is None:
            return False
        if not _compare(field_value, operator, target):
            return False
    return True


def select_strategy(
    strategies: Sequence['ScenarioStrategy'],
    facts: Mapping[str, Any],
) -> Optional['ScenarioStrategy']:
    """选出**第一条命中**的策略（候选须已按「优先级」排好序）。

    【注意】**取第一条而非合并**：一条策略 = 一套完整的经验组合；
    合并多条的语义（谁覆盖谁）会随条数增加而含糊 ⇒ 留到有需求时再定。

    Args:
        strategies: 候选策略（**已排序**：按优先级升序）。
        facts: 本轮事实。

    Returns:
        命中的 :class:`ScenarioStrategy`；一条都不命中 ⇒ ``None``
        （⇒ 不裁决，行为与「不接第2层」一致）。
    """
    for strategy in strategies:
        if match_conditions(strategy.conditions, facts):
            return strategy
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

    left = to_float(field_value)
    right = to_float(target)
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

    场景 = 「这一轮属于哪类情形」⇒ 它回答五个问题：

    1. **调哪些**（:attr:`allowed_params`）：不在白名单 ⇒ 让位，理由「本场景不允许」；
    2. **按什么次序**（:attr:`preferred_params`）：场景优先集排在字段级优先级之前；
    3. **留几个**（:attr:`max_items`）：名额用满 ⇒ 暂缓；
    4. **每个字段的目标怎么算**（:attr:`target_modes`）：字段 → 口径名
       （如 ``met_end_pos`` → ``fill_ratio``）；没声明的字段按规则增量。
    5. **本场景自带哪些候选**（:attr:`candidate_params`）：**算法零产出**时
       仍能有的调机对象（**零产出的成因不止一种**，本能力不挑成因）。

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
        target_modes: **字段 → 口径名**的映射（空 = 全部按规则增量）。
            口径名决定「这个字段的目标值怎么算」（``fill_ratio`` = 按充填量比例
            解算行程）；**算式在第3层**
            （:mod:`process.services.optimize_chain.integrate_params`），
            本层只声明口径名。
        candidate_params: **本场景自带的候选字段**（**不依赖算法建议**）。
            【注意】用于**算法零产出**的情形 —— 零产出的成因不止一种
            （合格态无缺陷、规则库无匹配、引擎不适用……）⇒ 候选只能由场景声明；
            字段的**目标值**仍由
            :attr:`target_modes` 的口径解算（算式在第3层），
            本层**不产建议值**。
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
    target_modes: Mapping[str, str] = field(default_factory=dict)
    candidate_params: Tuple[str, ...] = ()
    reason: str = ''
    conditions: Tuple[Mapping[str, Any], ...] = ()
    priority: int = 100
    priority_table: PriorityTable = field(default_factory=PriorityTable)


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
    failed_params: Optional[Mapping[str, str]] = None,
) -> StrategyDecision:
    """按优先级表 + 场景策略裁决候选调整，并显式让位 / 暂缓未执行的项。

    裁决口径（按先后）：

      1. **场景优先集**（:attr:`ScenarioStrategy.preferred_params`）里的候选排最前；
         同在集合内按集合次序，再按字段级优先级数值（小的在前）；
      2. **禁入**（:attr:`ScenarioStrategy.blocked_params`，非空时才生效）：
         在禁入清单的候选**让位**，理由「基线项 ⇒ 不参与阶段调机」；
      3. **上轮证伪**（``failed_params``，非空时才生效）：上一轮试过且没改善的
         候选**让位**（理由由调用方给）—— 同一旋钮不重复试；
      4. **准入**（:attr:`ScenarioStrategy.allowed_params`，非空时才生效）：
         不在白名单的候选**让位**，理由「本场景不允许」；
         按**旋钮类别**划定白名单，本层**不核对候选的缺陷归属** ——
         前提是调用链上游已把缺陷收敛成一条；
      5. **落不了地**（``veto_params``，非空时才生效）：本轮注定不生效的候选
         **让位**（理由由调用方给）—— 让位对象本轮不可调 ⇒ 改了也是白改；
      6. 落在 ``satisfied`` 里的候选**让位** —— 目标已达成，无需再调；
      7. **名额**（场景优先，其次 ``max_items``）：保留项超出名额的部分**暂缓**；
      8. 让位与暂缓都是**显式决策并留痕**，不静默丢弃；
      9. 表中未列出的候选排在最后，但**不丢弃**；
      10. **保留项也留依据**（:attr:`StrategyDecision.kept_reasons`）——
          没有依据，反馈回来只能证伪「调了这些量」，证伪不了「为什么按这个次序调」。

    【注意】**禁入排在准入之前**：基线项是**全局**理由（任何场景都不该动），
    比“本场景不允许”更强 ⇒ 同时命中两者时，留痕要写**基线项**，
    否则更强的理由会被场景理由掩盖。

    【注意】**六类让位/暂缓理由分开**：基线项 / 上轮证伪 / 本场景不允许 /
    目标已达成 / 名额已满 / 本轮落不了地 —— 「为什么没落地」必须能分辨是哪一类。
    （「本轮落不了地」见 ``veto_params``；编排层当前不传。）

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
            :func:`process.services.optimize_chain.anchors.unlandable_params`）——
            本模块只读，不内置物理知识。
            【注意】**编排层当前不传这一项**（第2层不掺合参数、不为单个字段做兜底）
            ⇒ 「改了会不会白改」由第3层回答。
        failed_params: **上一轮证伪**的候选 → 让位理由（字段名 → 理由）。
            判据由调用方给（事实：上一轮试过且没改善），本模块只读。

    Returns:
        :class:`StrategyDecision` —— 保留项、让位项与暂缓项、完整次序。
    """
    satisfied_set = set(satisfied)
    vetoed = dict(veto_params or {})
    failed = dict(failed_params or {})

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
        if candidate in failed:
            yielded[candidate] = failed[candidate]
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
    name_of: Callable[[str], Optional[str]] = to_process_field_name,
) -> Candidates:
    """把算法建议整理成**候选集**（进第2层之前的准备）。

    算法给的 ``param`` **已是业务字段名**（``inj_spd_1`` / ``brl_temp_1``）
    —— 算法名由算法层在出口译好 ⇒ 这里只判「是不是工艺量」。

    **筛掉的只有「根本不算建议」的条目**：

    - 没有推荐值（经验推理只给方向不给数值）⇒ 不进；
    - 不是 ORM 定义的工艺量（规则库专用参数）⇒ 不进；
    - 同一字段重复建议 ⇒ 以**首次**为准。

    【注意】**「这个字段本机有没有值」不在这儿判** ——
    本层不读参数集；「这台机有没有值」与「这是不是工艺量」是**两件事** ⇒
    **是工艺量、但本机没值**（如 ``inj_t`` 为 null）照样进候选、照样落地。

    【注意】**「这是不是工艺量」由静态字段字典判**（ORM 字段定义）⇒
    不是工艺量的（``IPOS`` 这类规则库专用参数）⇒ 不进候选
    ⇒ **下游不需要存在性兜底**（兜底 = 掩饰错误）。

    Args:
        recommendations: 算法建议列表（``param`` + ``recommended_value``）。
        name_of: 字段名 → 工艺字段名的筛选函数（默认按 ORM 字段字典判）。

    Returns:
        :class:`Candidates`。
    """
    names: List[str] = []
    targets: Dict[str, Any] = {}

    for rec in recommendations:
        if rec.get('recommended_value') is None:
            continue
        raw_name = rec.get('param')
        field_name = name_of(raw_name) if raw_name else None
        if not field_name:
            continue
        if field_name in targets:
            continue
        targets[field_name] = rec.get('recommended_value')
        names.append(field_name)

    return Candidates(names=tuple(names), targets=targets)


@dataclass(frozen=True)
class AdjustmentScheme:
    """**调整方案** —— 第2层的产出。

    【注意】**本层只回答「调哪几个、谁让位、什么口径」** ——
    **不碰参数、不求落地值** ⇒ 「改成多少」是第3层的事
    （它手上有旧值，能做物理换算）。

    Attributes:
        selection: 裁决结果（谁保留 / 谁让位 / 谁暂缓 + 依据）。
        assignments: 保留项的「字段名 + 目标值」（按执行次序）——
            **非派生量**的绝对值（可直接落地）。
        mel_targets: ``MEL`` 的目标值（算法侧的「标」）—— **未换算**，
            由第3层按 :attr:`target_modes` 口径翻成计量位置目标。
        target_modes: **保留项的字段 → 口径名**（由命中的场景策略声明）——
            第3层按口径求解目标值。
            【注意】**只带出保留项的口径** —— 让位 / 暂缓项的口径没有落点。
    """

    selection: StrategyDecision = field(default_factory=StrategyDecision)
    assignments: Tuple[Tuple[str, Any], ...] = ()
    mel_targets: Tuple[Any, ...] = ()
    target_modes: Mapping[str, str] = field(default_factory=dict)

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
        trace['target_modes'] = dict(self.target_modes)
        return trace


def _merge_candidates(
    candidates: Sequence[str],
    strategy: Optional[ScenarioStrategy],
) -> List[str]:
    """合并候选：算法建议的候选 + **场景自带的候选**。

    【注意】**场景候选追加在后** —— 同一字段以算法建议为准（算法给了建议值
    就用算法的；算法没给才走场景声明的口径）。

    【注意】场景候选**不带建议值** ⇒ 不进 :attr:`AdjustmentScheme.assignments`
    ⇒ 目标值由第3层按口径解算。
    """
    merged: List[str] = list(candidates)
    for name in (strategy.candidate_params if strategy is not None else ()):
        if name not in merged:
            merged.append(name)
    return merged


def resolve_scheme(
    candidates: Sequence[str],
    targets: Mapping[str, Any],
    facts: Optional[Mapping[str, Any]] = None,
    strategy: Optional[ScenarioStrategy] = None,
    table: Optional[PriorityTable] = None,
    satisfied: Sequence[str] = (),
    max_items: Optional[int] = None,
    veto_params: Optional[Mapping[str, str]] = None,
) -> AdjustmentScheme:
    """候选 + 事实 + 策略数据 ⇒ **调整方案**。

    流程：

    1. **合候选**：算法建议的候选 + **场景自带的候选**
       （:attr:`ScenarioStrategy.candidate_params`）⇒ 算法零产出时
       仍能有调机对象；
    2. **裁决**（:func:`resolve_priority`）：准入 / 优先集 / 名额 / 上轮证伪 / 让位 ——
       决定「调哪几个、按什么次序、谁没轮上」；
    3. **带出目标值**：保留项的建议值原样带出（**非派生量**是绝对值，
       可直接落地）；``MEL`` 是算法侧的**标** ⇒ 这里只记「目标值 + 口径」，
       换算成计量位置（决策量）归**第3层**；
    4. **带出口径**：按命中场景的声明，带出**保留项**的字段 → 口径名
       （口径的**算式**在第3层，本层只声明用哪个）。

    【注意】**本层不碰参数** —— 第2层只回答「调哪几个、谁让位、
    什么口径」；「改成多少」是第3层的事 ⇒ **不需要现状参数集**。

    【注意】**表为空且无场景 ⇒ 不裁决** ⇒ 保留集 = 原候选集、原序
    ⇒ **行为与「不接第2层」完全一致**。

    Args:
        candidates: 候选调整的字段名（业务字段名，已过滤掉落不了地的）。
        targets: 候选的建议目标值（字段名 → 目标值）。
        facts: 本轮事实（本层只作裁决参照，不参与目标值求解）。
        strategy: 命中的场景策略（``None`` = 无场景）。
        table: 数据化的优先级表（``None`` ⇒ 空表 ⇒ 只按场景裁决）。
        satisfied: 已达成目标的字段名（本模块不判定 ⇒ 由调用方传入）。
        max_items: 本轮最多执行的项数（``None`` = 不限；场景给了名额时以场景为准）。
        veto_params: **本轮落不了地**的候选 → 让位理由（透传给 :func:`resolve_priority`）。

    Returns:
        :class:`AdjustmentScheme` —— 调整方案（调哪些 + 改成多少 + 谁让位 / 暂缓 + 依据）。
    """
    selection = resolve_priority(
        _merge_candidates(candidates, strategy),
        table if table is not None else PriorityTable(),
        satisfied,
        max_items,
        scenario=strategy,
        veto_params=veto_params,
        failed_params=_failed_params(facts),
    )

    assignments: List[Tuple[str, Any]] = []
    mel_targets: List[Any] = []
    target_modes: Dict[str, str] = {}

    # 1. 保留项的**非派生量**目标值原样带出（绝对值 ⇒ 可直接落地）
    for name in selection.kept:
        if name == G1_AUTO_FIELD or name not in targets:
            continue
        assignments.append((name, targets[name]))

    # 2. MEL 是算法侧的**标** ⇒ 本层只记「目标值 + 口径」，换算归第3层
    if G1_AUTO_FIELD in selection.kept and G1_AUTO_FIELD in targets:
        mel_targets.append(targets[G1_AUTO_FIELD])

    # 3. 带出**保留项**的目标值口径（口径名 ⇒ 算式在第3层）
    #    【注意】只带保留项 —— 让位 / 暂缓项的口径没有落点。
    for name in selection.kept:
        mode = (strategy.target_modes or {}).get(name) if strategy is not None else None
        if mode:
            target_modes[name] = mode

    return AdjustmentScheme(
        selection=selection,
        assignments=tuple(assignments),
        mel_targets=tuple(mel_targets),
        target_modes=target_modes,
    )


# ===========================================================================
# 业务规则（一）：阶段模型 —— 阶段 = 缺陷族，不是「工艺组」
# ===========================================================================
#
# 【注意】**本文件是落地场景规则的唯一存放处** —— 改一条经验 = 改这个文件 ⇒
# 随版本走、可评审、可测试、可 diff。
#
# 划分依据：阶段的进入/达成信号必须是**可观测量**（缺陷码 + 重量缺口）
# ——「保压参数」不可观测 ⇒ 阶段按缺陷族划分。三个阶段按下列次序排列
# （「先把产品打到差不多 → 再补缩 → 最后针对性处理外观缺陷」）⇒ 阶段码见
# :data:`STAGE_ORDER`。
#
# - **阶段状态不落库** —— 阶段由**本轮反馈的缺陷构成**推导（纯函数）⇒ 换模 /
#   轮次失败 / 反馈缺失都自动自愈，不会「状态卡在某一步」。
# - **未知缺陷码不臆造归属** —— 归 ``UNKNOWN_STAGE``（排末位），既不塞进已知阶段，
#   也不丢。


#: 阶段优先级（**升序 = 推进顺序**）：``filling`` 打足 → ``shrinking`` 补缩
#: → ``appearance`` 外观。
STAGE_ORDER: Tuple[str, ...] = ('filling', 'shrinking', 'appearance')

#: 未知缺陷码的兜底阶段（排在所有已知阶段之后）。
UNKNOWN_STAGE: str = 'unknown'

#: 缺陷码 → 阶段。
DEFECT_STAGE_MAP: Mapping[str, str] = {
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


def stage_of_defect(defect_code: Optional[str]) -> str:
    """返回缺陷码对应的阶段码；未知或空 ⇒ :data:`UNKNOWN_STAGE`。"""
    if not defect_code:
        return UNKNOWN_STAGE
    return DEFECT_STAGE_MAP.get(str(defect_code), UNKNOWN_STAGE)


def rank_of_stage(stage: str) -> int:
    """返回阶段码的推进次序；未知阶段排**末位**。"""
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return len(STAGE_ORDER)


def sort_defects_by_stage(
    defects: Sequence[Any],
) -> List[Tuple[int, Any]]:
    """返回按阶段优先级排序的 ``[(原始下标, 缺陷项), ...]``。

    - 阶段顺序见 :data:`STAGE_ORDER`；
    - **同阶段内保持原始顺序**（稳定排序 —— 同阶段缺陷的先后是用户的判断，不改）；
    - 无 ``keyword_name`` 的项与未知缺陷码归末位（**不丢**，交给选取环节跳过）。

    【注意】返回**原始下标**是刻意的：留痕里的 ``index`` 要能指回用户提交的那一项，
    重排后的下标会指错位置。
    """
    decorated: List[Tuple[int, int, Any]] = []
    for index, item in enumerate(defects or ()):
        code = item.get('keyword_name') if isinstance(item, Mapping) else None
        decorated.append((rank_of_stage(stage_of_defect(code)), index, item))
    decorated.sort(key=lambda row: (row[0], row[1]))
    return [(index, item) for _, index, item in decorated]


@dataclass(frozen=True)
class StageProgress:
    """阶段进度（**每轮从反馈纯推导**）。

    Attributes:
        defect_codes: 推导所用的缺陷码（去重，保持出现顺序）。
        achieved: **未复现**的阶段（推导所用的缺陷码里没有该阶段的）。
        pending: 仍有缺陷的阶段（**明确未达成**）。
        current: 当前应推进的阶段 = 第一个 ``pending``
            （``None`` = 本轮无已知阶段的缺陷）。
    """

    defect_codes: Tuple[str, ...] = ()
    achieved: Tuple[str, ...] = ()
    pending: Tuple[str, ...] = ()
    current: Optional[str] = None

    def to_trace(self) -> Dict[str, Any]:
        """返回阶段进度的留痕载荷（进第 2 层留痕）。"""
        return {
            'defect_codes': list(self.defect_codes),
            'achieved': list(self.achieved),
            'pending': list(self.pending),
            'current': self.current,
        }


def derive_stage_progress(defect_codes: Sequence[str]) -> StageProgress:
    """由本轮缺陷码推导**阶段进度**（纯函数，不落库、不查库）。

    口径（**阶段达成信号**，见 ``docs/l2-stage-strategy-design.md``）：

    - **达成**：该阶段的**所有**缺陷码在本轮反馈里**都不出现**
      （「这一类缺陷不见了」= 可观测的达成信号）；
    - **未达成（pending）**：本轮反馈里还有该阶段的缺陷码；
    - **当前阶段（current）**：第一个未达成的阶段（按 :data:`STAGE_ORDER` 推进顺序）。

    【注意】**不区分「已解决」与「从未报过」** —— 阶段状态不落库 ⇒ 没有历史可比
    ⇒ 「本轮没报该阶段缺陷」一律记为达成。反馈稀疏时**可能高估达成度**。

    【注意】**推导所用的缺陷码来自收敛后的反馈**（service 预处理层只留本轮
    处理的那条）⇒ ``achieved`` / ``pending`` 只反映**该条**所在阶段，
    不再是「本轮全阶段」视图；``current`` 不受影响（阶段序选中的必然是
    最靠前的未达成阶段）。

    【注意】**本函数只做推导，不做裁决** —— 裁决由**场景清单**做
    （:data:`SCENARIO_STRATEGIES`）：``current`` 由决策层入口
    （:func:`build_adjustment_scheme`）放进事实表 ⇒
    场景条件**可引用**它（如 ``filling_stage_first`` 用 ``current_stage == 'filling'``
    判定「还在打足阶段」）。
    """
    codes: List[str] = []
    for code in defect_codes or ():
        if not code:
            continue
        text = str(code)
        if text not in codes:
            codes.append(text)

    # 阶段 → 本轮该阶段的缺陷码（未知码归 UNKNOWN_STAGE，不影响任何已知阶段）
    by_stage: Dict[str, List[str]] = {}
    for code in codes:
        by_stage.setdefault(stage_of_defect(code), []).append(code)

    pending = tuple(stage for stage in STAGE_ORDER if by_stage.get(stage))
    achieved = tuple(stage for stage in STAGE_ORDER if not by_stage.get(stage))
    return StageProgress(
        defect_codes=tuple(codes),
        achieved=achieved,
        pending=pending,
        current=pending[0] if pending else None,
    )


# ===========================================================================
# 业务规则（二）：场景裁决规则 —— 场景清单（第 2 层的规则来源）
# ===========================================================================
#
# 一条 :class:`ScenarioStrategy` = **一套完整的经验组合** ⇒ 命中即整条采用，
# **不合并**多条（合并语义会随条数增加而含糊）。
#
# - **命中顺序 = 优先级升序，取第一条命中** ⇒ 具体场景排前面、兜底场景排最后。
# - **条件按「本轮实际处理的缺陷」判定** —— service 预处理层已把 feedback **收敛**
#   成只剩本轮处理的那条，由决策层入口（:func:`build_adjustment_scheme`）
#   放进事实表 ⇒ 字段值是**单值** ⇒ 条件用 ``in_set``（落在目标集合内即命中）。
# - **名额（``max_items``）是场景级参数**，不是全局开关：不写 = 不限 ⇒ 多参数输出
#   是现成出口（缺省一轮一个，也能按需放开）。
# - **两类「不可调」不是一回事**：``allowed_params``（白名单）= **场景范围**
#   「这个场景该动哪些旋钮」，不写 = 不限制；``blocked_params``（禁入清单）= **基线项**
#   「任何场景都不该动的旋钮」，独立生效。
# - 条件可引用的字段名 = **事实表的键名**（由
#   :func:`collect_facts` 从原料挑出）⇒ **不写死在代码里**
#   （引用了事实表里没有的键 ⇒ 不命中，不静默通过）。
#
# 【注意】**阶段表与场景规则必须同源** —— 缺陷选取
# （:mod:`process.services.optimize_chain.defect_selection`）与第 2 层
# （本文件）读的是同一份，否则会「选出 A 阶段的缺陷却命中 B 阶段的策略」。
#
# **规则原料**（``U-07`` / ``SK-01`` / ``FL-06`` / ``BN-01`` …）见
# ``backend/process/references/04-defect-adjustment-rules.md``。


#: **基线项**（禁入清单）—— 任何场景都不把它当调机对象。
#:
#: 【注意】**注射速度一般用户为成型周期与保证质量采用较大速度**，
#:    **属基线取值，不参与阶段调机** ⇒ 阶段调机不以它为对象。
BASELINE_BLOCKED_PARAMS: Tuple[str, ...] = (
    'inj_spd_1',
    'inj_spd_2',
    'inj_spd_3',
    'inj_spd_4',
    'inj_spd_5',
    'inj_spd_6',
)

#: 场景清单（按 ``priority`` 升序排列）。
SCENARIO_STRATEGIES: Tuple[ScenarioStrategy, ...] = (
    # --- 合格态：产品已合格 ⇒ 省能耗 ---
    # 【注意】**准入判据 = feedback.tuning_result**（条件引用 ``last_tuning_result``）——
    #    合格与否**只由反馈说了算**，不看引擎有没有产出。
    # 【注意】候选由本场景**自带**（``candidate_params``），不依赖算法建议。
    # 【注意】合格与缺陷互斥 ⇒ 不会与缺陷场景抢；``priority`` 只影响同层排序。
    # 【注意】**口径 = 递减步进**（``step_down``）：目标 = 当前设定 × (1 − 步长)。
    #    「上一模合格」只说明当前设定够用，**不说明能降到哪** ⇒ 只能小步试探，
    #    靠试模反馈逼近够用线（**不依赖任何未标定的物理模型**）。
    # 【注意】**只降不改** —— 合格态产品已打足 ⇒ 不碰充填相关旋钮。
    # 【注意】**名额 1** —— 规则原料 U-01「一次只改一个量」。
    # 【注意】**暂只降压力**（省能耗）；省周期（冷却时间）待口径拍板
    #    （``docs/open-questions.md`` Q12 R4）⇒ 不预先声明死配置。
    ScenarioStrategy(
        scenario_code='qualified_efficiency',
        conditions=(
            {'field': 'last_tuning_result', 'operator': 'exact', 'value': 'qualified'},
        ),
        candidate_params=('inj_pres_1',),
        allowed_params=('inj_pres_1',),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('inj_pres_1',),
        max_items=1,
        target_modes={'inj_pres_1': STEP_DOWN_MODE},
        reason='产品已合格 ⇒ 省能耗：按递减步进下调一段注射压力（靠试模反馈逼近够用线）',
        priority=5,
    ),
    # --- S1 打足：短射 + 重量不足 ⇒ 充填优先 ---
    # 【注意】``fill_gap`` = 目标重量 − 实测重量（**正数 = 缺料**）⇒ ``gt 0``
    #    即「实际重量 < 目标重量」；缺重量数据 ⇒ ``fill_gap`` 为 None ⇒ 不命中。
    # 【注意】``target_modes={'met_end_pos': 'fill_ratio'}`` ⇒ 胶量端走
    #    **充填量比例**口径解算行程（不是 MEL 增量）。
    # 【注意】**口径按字段声明** —— 别的字段没声明 ⇒ 按规则增量。
    # 【注意】**规则原料 U-07**：充填量有两个旋钮、有先后（先胶量端，MEL 偏大后才轮到
    #    VPTL）⇒ 白名单只留胶量端两个旋钮；其余旋钮**让位**（而不是「暂缓」——
    #    含义：这个场景不管它们）。
    ScenarioStrategy(
        scenario_code='filling_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'in_any', 'value': ('SHORTSHOT',)},
            {'field': 'fill_gap', 'operator': 'gt', 'value': 0},
        ),
        allowed_params=('met_end_pos', 'vps_pos'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_end_pos',),   # 首选 MEL（充填量第一旋钮）
        max_items=1,                          # 一轮只调一个量
        target_modes={'met_end_pos': FILL_RATIO_MODE},
        reason='充填量不足 ⇒ 充填优先，并按重量比例重算行程',
        priority=10,
    ),
    # --- S1b 打足（缺重量口径）：短射 + 仍在打足阶段 ⇒ 充填量优先 ---
    # 【注意】**缺实测重量 ⇒ 本条接管**：``filling_first`` 命中依赖 ``fill_gap > 0``
    #    （缺实测重量 ⇒ ``fill_gap`` 为 None ⇒ 不命中）⇒ 短射轮次会落进
    #    **兜底场景**，而兜底**没有优先集** ⇒ 次序完全继承 L1 的输出序
    #    （= 规则库遍历序）⇒ 料筒温度等**间接旋钮**可能排到首位而上位。
    # 【注意】本条**不依赖重量数据**：改用**阶段进度**（``current_stage``）判定
    #    「还在打足阶段」—— 阶段由**缺陷码**推导，与重量数据无关。
    # 【注意】**priority=15 ⇒ 排在 ``filling_first``(10) 之后** ⇒
    #    **有重量数据时仍走 ``filling_first``**（按重量比例解算行程），
    #    本条只在「拿不到重量口径」时接管 ⇒ 两个场景互不覆盖。
    # 【注意】**规则原料 U-07「先胶量端」** ⇒ 白名单顺序 = 调整次序：
    #    胶量端（熔胶终止位置 / VP 切换位置）→ 保压组 → 熔体侧 → 料筒温度组。
    #    **料筒温度组排末位**（熔体黏度的间接影响，打足阶段不是主旋钮）。
    # 【注意】白名单**含 ``inj_t``**：它虽受 G3 让位规则约束（改注射时间要让位给
    #    注射速度，而注射速度是基线项不可调），但**不在白名单会让位理由被
    #    「本场景不允许」掩盖** ⇒ 反而看不出 G3 规则在工作。
    ScenarioStrategy(
        scenario_code='filling_stage_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'in_any', 'value': ('SHORTSHOT',)},
            {'field': 'current_stage', 'operator': 'exact', 'value': 'filling'},
        ),
        allowed_params=(
            # --- 胶量端（充填量端，主旋钮）---
            'met_end_pos',        # 熔胶终止位置（MEL）
            'vps_pos',            # VP 切换位置（VPTL）
            # --- 注射时间（受 G3 让位规则约束，保留在白名单内）---
            'inj_t',
            # 【注意】**注射压力**：规则库实测短射类会产出 ``inj_pres_1`` / ``inj_pres_2``
            #    ⇒ 不放进白名单会有「本场景无输出」风险
            #    （白名单写窄 ⇒ 候选全部让位 ⇒ 这一轮什么都不落地）。
            # 【注意】但**不进优先集** ⇒ 排在优先集之后 ⇒ 胶量端/保压/熔体侧
            #    都不可调时才轮得到它（注射速度才是基线项，注射压力不是）。
            'inj_pres_1', 'inj_pres_2',
            # --- 保压组 ---
            'hold_pres_1',        # 一段保压压力
            'hold_spd_1',         # 一段保压速度
            'hold_t_1',           # 一段保压时间
            # --- 熔体侧 ---
            'met_back_pres_1',    # 一段背压
            'met_rot_spd_1',      # 一段螺杆转速
            'pst_met_decomp_dist',  # 熔胶后松退距离
            # --- 料筒温度组（末位：熔体黏度的间接影响）---
            'brl_temp_1', 'brl_temp_2', 'brl_temp_3', 'brl_temp_4', 'brl_temp_5',
            'brl_temp_6', 'brl_temp_7', 'brl_temp_8', 'brl_temp_9',
            'noz_temp',
        ),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        # 【注意】优先集与白名单同序 ⇒ **白名单成员的先后即调整次序**
        #    （`resolve_priority` 的排序键：场景优先集 → 字段级优先级 → 原序）。
        preferred_params=(
            'met_end_pos', 'vps_pos',
            'inj_t',
            'hold_pres_1', 'hold_spd_1', 'hold_t_1',
            'met_back_pres_1', 'met_rot_spd_1', 'pst_met_decomp_dist',
            'brl_temp_1', 'brl_temp_2', 'brl_temp_3', 'brl_temp_4', 'brl_temp_5',
            'brl_temp_6', 'brl_temp_7', 'brl_temp_8', 'brl_temp_9',
            'noz_temp',
        ),
        max_items=1,             # 一轮只调一个量（与其它场景一致）
        # 【注意】**不声明口径**（默认按规则增量）：拿不到重量口径 ⇒ 不能按比例解算行程。
        reason='打足阶段（短射）⇒ 充填量优先：胶量端 → 保压 → 熔体侧 → 料筒温度',
        priority=15,
    ),
    # --- S2 补缩：缩水类 ⇒ 只动保压组 ---
    # 【注意】**规则原料 SK-01 / SK-02** ⇒ 白名单 = 二段压力 + 二段时间；
    #    二段时间的定量锚点是**浇口封冻时间**（【待补】尚缺判据 ⇒ 目标值待校准）。
    ScenarioStrategy(
        scenario_code='shrinking_first',
        conditions=(
            {
                'field': 'defect_codes',
                'operator': 'in_any',
                'value': ('SHRINKAGE', 'UNDERSIZE', 'OVERSIZE', 'WARPING'),
            },
        ),
        allowed_params=('hold_pres_1', 'hold_t_1'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('hold_pres_1',),
        max_items=1,
        reason='充填已足 ⇒ 只动保压：二段压力与二段时间（二段时间锚点是浇口封冻）',
        priority=20,
    ),
    # --- S3 外观：飞边 ⇒ 降压或减胶量 ---
    # 【注意】**规则原料 FL-01**（降二段压力）/ **FL-02**（减胶量，充填比例 ≤ 98%）
    #    ⇒ 白名单只留这两个主旋钮；目标值待校准（FL-02 的 98% 上限）。
    # 【注意】优先项取 ``met_end_pos``（减胶量）—— 飞边是型腔压力过高，
    #    胶量端是充填量第一旋钮。
    # 【注意】飞边**可能是模具问题而不是工艺问题**（规则原料 FL-06：
    #    不带二段的充填件本身就飞边 ⇒ 判为模具问题，**不属工艺**）。
    #    ⇒ 本场景的前提应是「已排除模具问题」，但**该判据目前系统里没有信号**
    #    （【待补】需「不带二段的充填件」测试结果）⇒ 只能写进 ``reason``（进留痕），
    #    **不写成条件**（写了就等于该场景永不命中）。
    ScenarioStrategy(
        scenario_code='flash_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'in_any', 'value': ('FLASH',)},
        ),
        allowed_params=('hold_pres_1', 'met_end_pos'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_end_pos',),
        max_items=1,
        reason=(
            '飞边 ⇒ 型腔压力过高 ⇒ 减胶量或降二段压力'
            '（【注意】若不带二段的充填件本身就飞边 ⇒ 属模具问题，应先修模）'
        ),
        priority=30,
    ),
    # --- S3 外观：烧焦 ⇒ 熔体侧（背压 / 松退 / 螺杆转速）---
    # 【注意】**规则原料 BN-01** 要求「先提示修模/清模，不要先给参数建议」——
    #    **提示通道尚未具备**（【待补】需 4M 归因字段）⇒ 本条只给参数侧。
    # 【注意】**规则原料 BN-02**（降一段充填速度）落在**基线项**（注射速度）⇒ 不可用，
    #    故白名单只留熔体侧三项 + 保压压力。
    # 【注意】烧焦**首要根因是模具排气不良**（规则原料 BN-01），
    #    调参 = 绕过根因 ⇒ 「已排气处理」本应是前提，但**没有信号**
    #    （【待补】）⇒ 只能写进 ``reason``（进留痕）。
    ScenarioStrategy(
        scenario_code='burn_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'in_any', 'value': ('BURN',)},
        ),
        allowed_params=(
            'met_back_pres_1',
            'pst_met_decomp_dist',
            'met_rot_spd_1',
            'hold_pres_1',
        ),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_back_pres_1',),
        max_items=1,
        reason=(
            '烧焦 ⇒ 熔体侧排查：背压 / 熔胶后松退 / 螺杆转速'
            '（【注意】首要根因是排气不良 ⇒ 应先修模/清模，不要先给参数建议）'
        ),
        priority=40,
    ),
    # --- S3 外观：气纹 ⇒ 查背压 ---
    # 【注意】拍板 G：气纹形态 = 「查背压」⇒ 优先项取 ``met_back_pres_1``。
    #    规则库实测：气纹类规则里背压（``MBP0``）是主要输出参数之一。
    # 【注意】白名单比拍板 G 宽（背压 + 保压压力 + 保压时间）—— 只留背压一个时，
    #    若本轮规则只推了其它旋钮，会出现“本场景无输出”。
    ScenarioStrategy(
        scenario_code='gasveins_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'in_any', 'value': ('GASVEINS',)},
        ),
        allowed_params=('met_back_pres_1', 'hold_pres_1', 'hold_t_1'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_back_pres_1',),
        max_items=1,
        reason='气纹 ⇒ 查背压（塑料含气 / 背压不足）',
        priority=50,
    ),
    # --- 兜底：缺省一轮只调一个量 ---
    # 【注意】``conditions=()`` ⇒ **恒命中**（空条件 = 无条件成立）⇒ 没命中任何
    #    具体场景时的缺省行为；``priority`` 排最后 ⇒ 具体场景永远优先。
    # 【注意】兜底恒命中 ⇒ **场景永不为 None** ⇒ 留痕里永远有「这一轮按什么场景裁决」。
    # 【注意】**白名单留空**（不限制）⇒ 兜底不窄化；基线项由禁入清单挡住。
    ScenarioStrategy(
        scenario_code='default_one_adjust',
        conditions=(),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        max_items=1,
        reason='缺省一轮只调一个量',
        priority=100,
    ),
)


def sorted_scenario_strategies() -> Tuple[ScenarioStrategy, ...]:
    """返回场景清单（按 ``priority`` 升序 ⇒ 命中判定从靠前的开始）。"""
    return tuple(
        sorted(SCENARIO_STRATEGIES, key=lambda item: (item.priority, item.scenario_code))
    )


# ===========================================================================
# 第2层的入口：原料 + 算法建议 ⇒ 调整方案
# ===========================================================================
#
# 「做一道菜」拆成四个依次完成的步骤：
#
# 1. **挑料**：从原料里取出本层要用的事实（缺陷码 / 实测重量 / 制品总重 /
#    上一轮评价 / 上一轮落地参数）；
# 2. **派生**：为场景条件补出两个中间量（充填缺口、当前阶段）；
# 3. **匹配**：按条件命中第一条场景；
# 4. **裁决**：合候选 → 定保留 / 让位 / 暂缓 / 次序 → 带出目标值与口径，
#    并把裁决状态回填到每条建议。
#
# 【注意】**原料只做搬运** —— 本层要什么自己挑、取到什么算什么；
# 取不到的键**根本不存在**（条件引用不到 ⇒ 不命中，不臆造）。
#
# 【注意】**本层不碰参数** —— 「改成多少」是第3层的事（它手上有旧值）。
#
# 【注意】**重量与第3层同源** —— 两个重量都从底座
# :func:`anchors.read_weights` 取（第2层拿它派生充填缺口、第3层拿它解算行程
# 目标）⇒ 不会出现「两边算的不是一个数」。


def _derive_selected_defect(feedback: Mapping[str, Any]) -> Optional[str]:
    """派生**本轮选中的缺陷码**（事实表 ``defect_codes`` 的来源）。

    取值优先级：
    1. ``defect_selection['selected']['keyword_name']`` —— 缺陷选取的**一手出口**
       （留痕含 level / position / index，见 :mod:`process.services.optimize_chain.defect_selection`）；
    2. ``defects[0]['keyword_name']`` —— **回落**：反馈未经 ``select_defect`` 收敛时用，
       **只看第一条**（列表顺序语义）。

    Args:
        feedback: 缺陷反馈（已收敛或未收敛均可）。

    Returns:
        Optional[str]: 缺陷码；没选出缺陷时返回 None（条件不命中，不臆造）。
    """
    selection = feedback.get('defect_selection') or {}
    selected = selection.get('selected') or {}
    code = selected.get('keyword_name')
    if code:
        return str(code)
    defects = feedback.get('defects') or ()
    selected = defects[0] if defects else {}
    if not isinstance(selected, Mapping):
        return None
    code = selected.get('keyword_name')
    return str(code) if code else None


def collect_facts(
    feedback: Optional[Mapping[str, Any]] = None,
    mold_info: Optional[Mapping[str, Any]] = None,
    last_advised_params: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """挑料 + 派生：原料 ⇒ 本层判定要用的**事实**。

    **只放取到的值** —— 取不到的键根本不存在（条件引用不到 ⇒ 不命中，不臆造）。

    Args:
        feedback: 缺陷反馈（``defect_selection`` / ``defects[]`` / ``observations[]`` /
            ``tuning_result``）。
        mold_info: 模具上下文（取 ``total_product_weight``）。
        last_advised_params: 上一轮**实际落地**的参数（业务字段名）—— 由调用方
            从上一轮的建议记录取出。

    Returns:
        Dict[str, Any]: 事实字典；键名 = 场景条件可引用的字段名。
    """
    feedback = feedback or {}
    mold_info = mold_info or {}

    facts: Dict[str, Any] = {}

    # 取缺陷码只认一处 —— 由缺陷选取的一手出口派生
    # （service 预处理层的 ``select_defect`` 已把缺陷收敛成一条）
    # ⇒ 不再从 ``defects`` 列表另取一遍。
    selected = _derive_selected_defect(feedback)
    if selected:
        facts['defect_codes'] = (selected,)

    target_weight, actual_weight = read_weights(feedback, mold_info)
    if actual_weight is not None:
        facts['actual_weight'] = actual_weight
    if target_weight is not None:
        facts['target_weight'] = target_weight

    # 充填缺口 = 总重 − 实测重（**正数 = 缺料**）—— 供条件判定「重量不足」
    if actual_weight is not None and target_weight is not None:
        facts['fill_gap'] = target_weight - actual_weight

    tuning_result = feedback.get('tuning_result') or None
    if tuning_result:
        facts['last_tuning_result'] = tuning_result

    if last_advised_params:
        facts['last_advised_params'] = tuple(last_advised_params)

    # 当前阶段（由缺陷码推导）—— 供条件判定「还在打足阶段」
    stage_progress = derive_stage_progress(facts.get('defect_codes', ()))
    facts['current_stage'] = stage_progress.current
    _logger.info('[optimize] 阶段进度: %s', stage_progress.to_trace())

    return facts


def _apply_decision_status(
    recommendations: List[Dict[str, Any]],
    decision: StrategyDecision,
) -> None:
    """把裁决状态就地回填到每条建议。

    【注意】状态三取值：adopted（保留执行）/ yielded（让位）/ deferred（暂缓）；
        不在候选集里的建议不打标 ⇒ 历史轮次没有状态字段时照常显示，不会被误当成「未采用」。
    """
    for rec in recommendations:
        status, reason = decision.status_of(rec.get('param') or '')
        if status is None:
            continue
        rec['decision_status'] = status
        if reason:
            rec['decision_reason'] = reason


def build_adjustment_scheme(
    recommendations: List[Dict[str, Any]],
    *,
    feedback: Optional[Mapping[str, Any]] = None,
    mold_info: Optional[Mapping[str, Any]] = None,
    last_advised_params: Optional[Sequence[str]] = None,
) -> AdjustmentScheme:
    """原料 + 算法建议 ⇒ **调整方案**。

    步骤：**挑料** → **匹配场景** → **裁决** → **回填裁决状态**。

    Args:
        recommendations: 算法给的平级建议（``param`` + ``recommended_value``），
            裁决状态就地回填在它们身上。
        feedback: 缺陷反馈（原料）。
        mold_info: 模具上下文（原料）。
        last_advised_params: 上一轮**实际落地**的参数（原料）。

    Returns:
        AdjustmentScheme: 调整方案 —— 调哪几个、谁让位、谁暂缓、按什么口径调。
    """
    facts = collect_facts(feedback, mold_info, last_advised_params)

    strategies = sorted_scenario_strategies()
    scenario = select_strategy(strategies, facts) if strategies else None

    candidates = collect_candidates(recommendations)
    scheme = resolve_scheme(
        candidates.names,
        candidates.targets,
        facts=facts,
        strategy=scenario,
        table=scenario.priority_table if scenario else None,
    )

    # 记决策留痕，有让位或暂缓时才落日志，正常路径不产噪声
    if scheme.selection.yielded or scheme.selection.deferred:
        _logger.info('infer scheme: %s', scheme.selection.to_trace())

    # 回填裁决状态，让前端和落库看到的是同一份
    _apply_decision_status(recommendations, scheme.selection)

    return scheme


__all__ = [
    # 条件求值
    'INEFFECTIVE_TUNING_RESULTS',
    'match_conditions',
    'select_strategy',
    # 策略数据
    'PriorityEntry',
    'PriorityTable',
    'ScenarioStrategy',
    'StrategyDecision',
    'resolve_priority',
    'priority_table_from_mapping',
    # 候选与方案
    'Candidates',
    'collect_candidates',
    'AdjustmentScheme',
    'resolve_scheme',
    # 业务规则：阶段模型与场景清单
    'BASELINE_BLOCKED_PARAMS',
    'DEFECT_STAGE_MAP',
    'SCENARIO_STRATEGIES',
    'STAGE_ORDER',
    'StageProgress',
    'UNKNOWN_STAGE',
    'derive_stage_progress',
    'rank_of_stage',
    'sort_defects_by_stage',
    'sorted_scenario_strategies',
    'stage_of_defect',
    # 第2层入口
    'build_adjustment_scheme',
    'collect_facts',
]
