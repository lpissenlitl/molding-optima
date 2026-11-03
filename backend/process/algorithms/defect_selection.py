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
2. **可插拔策略** —— 默认策略 = 取第一个有效缺陷；业务优先级规则将来作为
   新策略接入，**不改调用点**；
3. **留痕** —— 返回对象自带选取依据（选了谁 / 跳过了谁 / 依据什么），
   由调用方写进自己的诊断出口。

⚠️ 本轮**不实现**业务优先级规则 —— 口径是「一次只解决一个缺陷，
优先级机制**功能预留**」⇒ 策略接口先立起来，规则等业务输入。

零 ORM、零 Django（本模块只认 context 里的裸 dict）。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable


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

    ⚠️ 与默认策略的差异是**刻意保留**的：两个引擎历史语义不同，
    强行统一会让经验推理在「首项无效、次项有效」时凭空多出推荐。
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


#: 默认策略（未显式指定时用）—— 等价于 fuzzy 的历史行为。
DEFAULT_STRATEGY = FirstValidDefectStrategy()


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


__all__ = [
    'DEFAULT_STRATEGY',
    'DefectSelection',
    'DefectSelectionStrategy',
    'FirstOnlyDefectStrategy',
    'FirstValidDefectStrategy',
    'select_defect',
]
