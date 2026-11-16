"""缺陷选取 —— 本轮处理哪个缺陷（**唯一真相源**）。

背景：`process/schemas/optimization.py::FeedbackSchema.defect` 是**列表**，
字段说明写着「多个，算法识别优先级」⇒ 契约层**早已声明**优先级语义，
但算法侧一直只取第一个，而且**各算法各取各的**：

- fuzzy：遍历取第一个**有 keyword_name** 的（跳过无效项）
- empirical：只看 `defects[0]`，首项无效就整个放弃

⇒ 同一份反馈在不同算法下可能选中**不同的缺陷**，且**选取依据没有任何记录**
（事后无法回答「为什么选了短射、没选缩水」）。

本模块职责（**只做选取，不做推理**）：

1. **唯一实现** —— fuzzy 与 empirical 都从这里取「本轮处理哪个缺陷」；
2. **可插拔策略** —— 默认策略 = 取第一个有效缺陷；业务优先级规则作为
   新策略接入，**不改调用点**；
3. **留痕** —— 返回对象自带选取依据（选了谁 / 跳过了谁 / 依据什么），
   由调用方写进自己的诊断出口。

⚠️ **「这一轮该处理哪个缺陷」的实现属本模块，调用时机属 service 的预处理层**
（2026-11-16 用户界定）—— 用户原话：「feedback 预处理是分层架构里的一层，
输入和输出都明确」「这个工作在后续理论上都不需要再重复做了，否则会有歧义」。
⇒ **service 层调一次**（``services/parameter_optimize.py::_prepare_defect_selection``），
   结果随 context 的 ``selected_defect`` 下传；**引擎不再各自选**（只读结果），
   **L2 也不重选、不重排**（只拿确定的缺陷信息去匹配策略、裁决方向）。

本模块提供三种口径：

- :class:`FirstValidDefectStrategy` —— **默认（当前生效）**，取第一个有效缺陷；
- :class:`FirstOnlyDefectStrategy` —— 「只认首项，首项无效就整体放弃」
  —— ⚠️ **引擎侧已不再单独选取**（预处理层已把列表收敛成一条有效项）⇒ 仅作历史语义参照；
- :class:`StagePriorityDefectStrategy` —— **候选规则（未接线）**：先按**调机阶段**
  （打足 → 补缩 → 外观）重排，再取第一个有效缺陷（阶段表见
  :mod:`process.algorithms.stage_order`）。
  ⚠️ 当前生效规则是「只选第一条」—— 更优的匹配规则尚未确定（用户口径：
  「结合入参进行分析」，例：短射+缩水⇒先短射；缩水+飞边⇒先缩水）。

零 ORM、零 Django（本模块只认 context 里的裸 dict）。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable

from .stage_order import order_defects


@dataclass
class DefectSelection:
    """本轮选中的缺陷 + 选取依据（留痕载荷）。

    Attributes:
        keyword_name: 选中的缺陷英文码（SHORTSHOT / SHRINKAGE / …）。
        level: 严重程度（low / medium / high），与规则前件的档位词一致。
        position: 缺陷位置（`DL` + 缺陷名 + 段号）。
        strategy: 产出本结果的策略名（留痕用）。
        index: 选中项在原始列表里的下标。
        candidates: 全部候选缺陷码（留痕用 —— 反映用户提交了什么）。
        skipped: 被跳过的项 + 原因（留痕用）。
    """

    keyword_name: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    strategy: str = ''
    index: Optional[int] = None
    candidates: List[str] = field(default_factory=list)
    skipped: List[Dict[str, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        """没选出可用缺陷。"""
        return not self.keyword_name

    def to_trace(self) -> Dict[str, Any]:
        """留痕载荷（写进调用方的诊断出口）。

        刻意**不**放进 `field_reports` / `diagnostics` 那两个清单 ——
        它们是「规则级诊断」，本项是「决策级留痕」，性质不同，分开更清楚。
        """
        return {
            'strategy': self.strategy,
            'selected': (
                {
                    'keyword_name': self.keyword_name,
                    'level': self.level,
                    'position': self.position,
                    'index': self.index,
                }
                if self.keyword_name else None
            ),
            'candidates': list(self.candidates),
            'skipped': list(self.skipped),
        }

    def to_context(self) -> Dict[str, Any]:
        """→ **随 context 下传**的载荷（引擎读的形状）。

        字段名与算法侧契约一致（``defect_name`` / ``level`` / ``position``）——
        与 ``fuzzy/engine.py::_extract_defect_context`` 的返回形状**相同**
        ⇒ 引擎改读它时零适配成本。

        ``trace`` 携带完整留痕（选了谁 / 跳过了谁 / 依据什么）⇒ 引擎的
        ``Diagnostic.selections`` 记的就是它（结构与 ``to_trace()`` 一致）。

        ⚠️ ``defect_name`` 为 None = **本轮没选出可用缺陷**（前端提交了但缺
        ``keyword_name``）⇒ 由消费方按「无缺陷可处理」处理。
        """
        return {
            'defect_name': self.keyword_name,
            'level': self.level,
            'position': self.position,
            'strategy': self.strategy,
            'index': self.index,
            'trace': self.to_trace(),
        }


@runtime_checkable
class DefectSelectionStrategy(Protocol):
    """缺陷选取策略接口（**可替换点**）。

    实现方只需给出 `name` 与 `select()`。
    业务优先级规则将来作为新策略接入，**调用点不变**。
    """

    name: str

    def select(self, defects: Sequence[Any]) -> DefectSelection:
        """从缺陷列表里选出本轮处理的那一个。"""
        ...


def _collect_candidates(defects: Sequence[Any]) -> List[str]:
    """全部候选缺陷码（用户提交了什么）—— 各策略共用。"""
    out: List[str] = []
    for defect in defects or []:
        if isinstance(defect, dict) and defect.get('keyword_name'):
            out.append(defect['keyword_name'])
    return out


class FirstValidDefectStrategy:
    """默认策略：按列表顺序取第一个**有效**缺陷。

    「有效」= 是 dict 且有非空 `keyword_name`；无效项跳过，继续往后找。

    —— 与 FuzzyEngine 现行行为**逐字一致**（切换到本模块不改变任何结果）。

    ⚠️ 这**不是**业务优先级规则（业务优先级待定，见模块 docstring）。
    """

    name = 'first_valid'

    def select(self, defects: Sequence[Any]) -> DefectSelection:
        items = list(defects or [])
        candidates = _collect_candidates(items)
        skipped: List[Dict[str, Any]] = []

        for index, defect in enumerate(items):
            if not isinstance(defect, dict):
                skipped.append({'index': index, 'keyword_name': None,
                                'reason': 'not_a_dict'})
                continue
            keyword_name = defect.get('keyword_name')
            if not keyword_name:
                skipped.append({'index': index, 'keyword_name': None,
                                'reason': 'no_keyword_name'})
                continue
            return DefectSelection(
                keyword_name=keyword_name,
                level=defect.get('level'),
                position=defect.get('position'),
                strategy=self.name,
                index=index,
                candidates=candidates,
                skipped=skipped,
            )

        return DefectSelection(strategy=self.name, candidates=candidates, skipped=skipped)


class FirstOnlyDefectStrategy:
    """只看列表第一个（EmpiricalReasoning 的现行行为）。

    首项无效就**整体放弃**（不往后找）—— 保留该引擎的历史行为，
    切换到本模块不改变任何结果。

    ⚠️ 与默认策略的差异来自两个引擎的**历史语义**不同（经验推理历史上
    「首项无效即整体放弃」）。

    ⚠️ **引擎侧已不再单独选取**（2026-11-16）：缺陷选取上移到 service 预处理层
    且**只做一次**，预处理层已把缺陷列表收敛成**一条有效项**
    ⇒ 引擎读到它时不会遇到「首项无效」⇒ 本策略在生产路径上**不再被调用**，
    仅作历史语义参照保留。
    """

    name = 'first_only'

    def select(self, defects: Sequence[Any]) -> DefectSelection:
        items = list(defects or [])
        candidates = _collect_candidates(items)
        if not items:
            return DefectSelection(strategy=self.name, candidates=candidates)

        first = items[0]
        if not isinstance(first, dict):
            return DefectSelection(
                strategy=self.name, candidates=candidates,
                skipped=[{'index': 0, 'keyword_name': None, 'reason': 'not_a_dict'}],
            )
        keyword_name = first.get('keyword_name')
        if not keyword_name:
            return DefectSelection(
                strategy=self.name, candidates=candidates,
                skipped=[{'index': 0, 'keyword_name': None, 'reason': 'no_keyword_name'}],
            )
        return DefectSelection(
            keyword_name=keyword_name,
            level=first.get('level'),
            position=first.get('position'),
            strategy=self.name,
            index=0,
            candidates=candidates,
            skipped=[],
        )


class StagePriorityDefectStrategy:
    """**业务优先级策略** —— 按**调机阶段**选取本轮缺陷。

    解决的问题（模块 docstring 里的现状问题）：fuzzy 与 empirical **各选各的**，
    同一份反馈在不同引擎下可能选中**不同的缺陷**，且选取依据没有记录。
    ⇒ 各引擎**各选各的**会让同一份反馈推理出不同缺陷的方案。
    ⚠️ **口径（2026-11-13 用户界定）**：缺陷选取属 **L1 侧** ——
    **L2 的输入是「规则」+「已确定的缺陷信息」，L2 不重选**。
    本策略是**收敛 L1 侧各引擎的选取口径**（把「各选各的」变成一致的阶段优先级），
    不是 L2 的裁决。

    口径：**先按阶段优先级重排**（打足 → 补缩 → 外观；阶段表见
    :mod:`process.algorithms.stage_order`），**再取第一个有效缺陷**。

    ⚠️ **业务口径（2026-11-13 用户拍板）**：多缺陷反馈**不按列表第一项**，
    而按**调机阶段**取：
    - 「短射 + 缩水 ⇒ 先解决短射」（充填没打足就先打足）；
    - 「缩水 + 飞边 ⇒ 先做缩水」—— 飞边**可能是模具问题而不是工艺问题**，
      不该靠调机解决（对应规则原料 `FL-06` / `BN-01`）。

    ⚠️ **接线状态（2026-11-16）**：**未接线** —— 当前生效的是「只选第一条」
    （`DEFAULT_STRATEGY`）。本策略保留为**候选实现**，等确定更优的匹配规则
    （用户口径：「结合入参进行分析」）后由预处理层选用，**调用点不变**。

    ⚠️ **与 :class:`FirstValidDefectStrategy` 的差别只有一条**（多了阶段重排）：
    有效性判定完全一致 —— 无效项跳过；
    ``index`` 记的是**用户提交列表里的原始下标**（不是重排后的位置）。

    ⚠️ **``skipped`` 记的是「全部」无效项**（原始顺序），比父策略多记了
    「排在有效项之后」的那几个：阶段重排会把无效项挪到末位，
    而选取是**遇到第一个有效项就停** ⇒ 不预扫一遍就会漏记它们
    （父策略因为按原顺序遍历，天然不会漏）。
    ⇒ ``skipped`` 的语义是「用户提交了但没被采用的项」，要**完整审计**。
    """

    name = 'stage_priority'

    def select(self, defects: Sequence[Any]) -> DefectSelection:
        items = list(defects or [])
        candidates = _collect_candidates(items)
        skipped: List[Dict[str, Any]] = []

        # 先扫一遍**全部**项，把无效项都记下来（阶段重排会把它们挪到末位，
        # 选取时走不到 ⇒ 不预扫就会漏记）。
        for index, defect in enumerate(items):
            if not isinstance(defect, dict):
                skipped.append({'index': index, 'keyword_name': None,
                                'reason': 'not_a_dict'})
                continue
            if not defect.get('keyword_name'):
                skipped.append({'index': index, 'keyword_name': None,
                                'reason': 'no_keyword_name'})

        for original_index, defect in order_defects(items):
            if not isinstance(defect, dict):
                continue
            keyword_name = defect.get('keyword_name')
            if not keyword_name:
                continue
            return DefectSelection(
                keyword_name=keyword_name,
                level=defect.get('level'),
                position=defect.get('position'),
                strategy=self.name,
                index=original_index,
                candidates=candidates,
                skipped=skipped,
            )

        return DefectSelection(strategy=self.name, candidates=candidates, skipped=skipped)


#: 默认策略（未显式指定时用）—— 等价于 fuzzy 的历史行为。
DEFAULT_STRATEGY = FirstValidDefectStrategy()

#: 业务优先级策略 —— 按调机阶段重排后取第一个有效缺陷。
#: ⚠️ **候选规则、未接线**（2026-11-16）：当前生效的是「只选第一条」
#:    （`DEFAULT_STRATEGY`）—— 更优的匹配规则待定（用户口径：
#:    「结合入参进行分析」，例：短射+缩水⇒先短射；缩水+飞边⇒先缩水）。
STAGE_PRIORITY_STRATEGY = StagePriorityDefectStrategy()


def select_defect(
    context: dict,
    strategy: Optional[DefectSelectionStrategy] = None,
) -> DefectSelection:
    """从推理上下文里选出**本轮处理哪个缺陷**（唯一入口）。

    Args:
        context: 推理上下文（只读 `context['feedback']['defect']`）。
        strategy: 选取策略（None = 默认策略「取第一个有效缺陷」）。

    Returns:
        `DefectSelection` —— 选中项 + 留痕依据（选了什么 / 跳过了什么）。
    """
    defects = ((context or {}).get('feedback') or {}).get('defect') or []
    return (strategy or DEFAULT_STRATEGY).select(defects)


def ensure_selected_defect(
    context: dict,
    strategy: Optional[DefectSelectionStrategy] = None,
) -> dict:
    """确保 context 里有 ``selected_defect``（**幂等**，**就地补**）。

    给**绕过 service 预处理层**的调用方用（condition chain / 离线 runner /
    黄金快照脚本）—— 它们各自构造 context，没有 service 那层兜底。

    ⚠ **等价性**：本函数只是把原先**藏在引擎内部**的 ``select_defect`` 调用
       提到调用方 ⇒ 对同一 context、同一策略，结果逐字不变。

    ⚠ **幂等**：已有 ``selected_defect`` 则原样返回（**不重算**）⇒
       service 层整理过的 context 不会被二次加工 ⇒ 两个来源不可能打架。

    ⚠ 默认策略 = 「只选第一条有效项」（当前生效口径）；与 ``select_defect``
       默认一致。
    """
    if not isinstance(context, dict):
        return context
    if context.get('selected_defect'):
        return context
    context['selected_defect'] = select_defect(context, strategy=strategy).to_context()
    return context


__all__ = [
    'DEFAULT_STRATEGY',
    'STAGE_PRIORITY_STRATEGY',
    'DefectSelection',
    'DefectSelectionStrategy',
    'FirstOnlyDefectStrategy',
    'FirstValidDefectStrategy',
    'StagePriorityDefectStrategy',
    'ensure_selected_defect',
    'select_defect',
]
