"""缺陷选取 —— 收敛 ``feedback['defects']``，定出**本轮处理哪个缺陷**。

【注意】**调用约束** —— 选取**只在 service 预处理层做一次**；结果交给调用方，
**本模块不改入参**；引擎与 L2 **只读结果**，不重选、不重排。

**口径 = 阶段序**（:class:`StagePriorityDefectStrategy`）。

零 ORM、零 Django（本模块只认裸 dict）。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .tuning_strategy import sort_defects_by_stage


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
        """返回决策级留痕载荷（选了谁 / 跳过了谁 / 按什么规则）。"""
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

    def to_defect_item(self) -> Dict[str, Any]:
        """返回选中项的**算法契约形状**。

        字段与 ``feedback['defects']`` 里其它项**同名同形**
        ⇒ 收敛前后无需改名。

        【注意】**调用限制** —— 只在已选出缺陷时调用（``keyword_name`` 非空）。
        """
        return {
            'keyword_name': self.keyword_name,
            'level': self.level,
            'position': self.position,
        }


def _collect_candidates(defects: Sequence[Any]) -> List[str]:
    """返回全部候选缺陷码（用户提交了什么）。"""
    out: List[str] = []
    for defect in defects or []:
        if isinstance(defect, dict) and defect.get('keyword_name'):
            out.append(defect['keyword_name'])
    return out


class StagePriorityDefectStrategy:
    """按调机阶段重排后取第一个有效缺陷的选取规则。

    阶段表见 :mod:`process.algorithms.tuning_strategy`（含缺陷码→阶段映射与
    阶段推进顺序）。

    【注意】**业务口径（用户拍板）**：多缺陷反馈**不按列表第一项**，
    而按**调机阶段**取：
    - 「短射 + 缩水 ⇒ 先解决短射」（充填没打足就先打足）；
    - 「缩水 + 飞边 ⇒ 先做缩水」—— 飞边**可能是模具问题而不是工艺问题**，
      不该靠调机解决（对应规则原料 `FL-06` / `BN-01`）。

    【注意】``index`` 记的是**用户提交列表里的原始下标**（不是重排后的位置）。

    【注意】**``skipped`` 记的是「全部」无效项**（原始顺序）—— 语义是
    「用户提交了但没被采用的项」，要**完整审计**。
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

        for original_index, defect in sort_defects_by_stage(items):
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


#: 本模块的选取规则（**阶段序**）—— 阶段推进顺序见
#: :data:`process.algorithms.tuning_strategy.STAGE_ORDER`。
DEFAULT_STRATEGY = StagePriorityDefectStrategy()


def select_defect(
    feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """收敛缺陷反馈 —— 定出**本轮处理哪个缺陷**（唯一入口）。

    选取口径固定 = **阶段序**（见 :data:`DEFAULT_STRATEGY`），无入参可选。

    Args:
        feedback: 缺陷反馈（``defects`` 列表 + 观察记录）。

    Returns:
        **收敛后的 feedback**（新 dict，**入参不改**）：

        - ``defects`` —— 只剩本轮处理的那一条（未选出可用缺陷时为空列表）；
        - ``defect_selection`` —— 选取留痕。
    """
    source = feedback or {}
    selection = DEFAULT_STRATEGY.select(source.get('defects') or [])
    return {
        **source,
        'defects': [] if selection.is_empty() else [selection.to_defect_item()],
        'defect_selection': selection.to_trace(),
    }


__all__ = [
    'DEFAULT_STRATEGY',
    'DefectSelection',
    'StagePriorityDefectStrategy',
    'select_defect',
]
