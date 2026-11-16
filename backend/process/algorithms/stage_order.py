"""调机阶段（**业务数据**）—— 「这一轮处在调机的第几步」。

阶段 = **缺陷族**（要解决的问题），不是「工艺组」（注射 / 保压 / 计量…）。
划分依据（2026-11-12 拍板）：阶段的进入/达成信号必须是**可观测量**
（缺陷码 + 重量缺口），而"保压参数"不可观测 ⇒ 阶段按缺陷族划分。

三个阶段（用户口径：「先把产品打到差不多 → 再补缩 → 最后针对性处理外观缺陷」）：

===================  ==================  ==================================
阶段码                目标                归属缺陷码
===================  ==================  ==================================
``filling``           充填到位            ``SHORTSHOT``
``shrinking``         尺寸与形状达标      ``SHRINKAGE`` ``UNDERSIZE``
                                           ``OVERSIZE`` ``WARPING``
``appearance``        表面质量达标        其余 12 类（外观类）
===================  ==================  ==================================

⚠️ **阶段状态不落库** —— 阶段由**本轮反馈的缺陷构成**推导（纯函数）：
换模 / 轮次失败 / 反馈缺失都自动自愈，不会出现"状态卡在某一步"。
将来若要「人工锁定阶段」，再引入可空的 ``stage_override``（当前不建）。

⚠️ **本文件是业务知识（数据），不是逻辑** —— 缺陷码归属与阶段顺序都摆在这里。
:mod:`process.algorithms.defect_selection`（选哪个缺陷）与
:mod:`process.algorithms.strategies`（调什么）**共读同一份**，
才不会选出 A 阶段的缺陷却命中 B 阶段的策略。

⚠️ **未知缺陷码不臆造归属** —— 归到 :data:`UNKNOWN_STAGE`（排末位），
既不塞进已知阶段，也不丢。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

#: 阶段优先级（**升序 = 推进顺序**）：打足 → 补缩 → 外观。
STAGE_ORDER: Tuple[str, ...] = ('filling', 'shrinking', 'appearance')

#: 未知缺陷码的兜底阶段（排在所有已知阶段之后）。
UNKNOWN_STAGE: str = 'unknown'

#: 缺陷码 → 阶段（**17 类全覆盖**）。
DEFECT_STAGE: Mapping[str, str] = {
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


def stage_of(defect_code: Optional[str]) -> str:
    """缺陷码 → 阶段码；未知或空 ⇒ :data:`UNKNOWN_STAGE`（不臆造归属）。"""
    if not defect_code:
        return UNKNOWN_STAGE
    return DEFECT_STAGE.get(str(defect_code), UNKNOWN_STAGE)


def stage_rank(stage: str) -> int:
    """阶段码 → 推进次序；未知阶段排**末位**（不早于任何已知阶段）。"""
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return len(STAGE_ORDER)


def order_defects(
    defects: Sequence[Any],
) -> List[Tuple[int, Any]]:
    """按阶段优先级给缺陷列表排序，返回 ``[(原始下标, 缺陷项), ...]``。

    - 阶段顺序见 :data:`STAGE_ORDER`；
    - **同阶段内保持原始顺序**（稳定排序 —— 同阶段缺陷的先后是用户的判断，不改）；
    - 无 ``keyword_name`` 的项与未知缺陷码归末位（**不丢**，交给选取环节跳过）。

    ⚠️ 返回**原始下标**是刻意的：留痕里的 ``index`` 要能指回用户提交的那一项，
    重排后的下标会指错位置。
    """
    decorated: List[Tuple[int, int, Any]] = []
    for index, item in enumerate(defects or ()):
        code = item.get('keyword_name') if isinstance(item, Mapping) else None
        decorated.append((stage_rank(stage_of(code)), index, item))
    decorated.sort(key=lambda row: (row[0], row[1]))
    return [(index, item) for _, index, item in decorated]


@dataclass(frozen=True)
class StageProgress:
    """阶段进度（**每轮从反馈纯推导**，不落库）。

    Attributes:
        defect_codes: 本轮反馈涉及的缺陷码（去重，保持出现顺序）。
        achieved: **本轮未复现**的阶段（本轮反馈里没有该阶段的任何缺陷码）。
        pending: 本轮仍有缺陷的阶段（**明确未达成**）。
        current: 当前应推进的阶段 = 第一个 ``pending``
            （``None`` = 本轮无已知阶段的缺陷）。
    """

    defect_codes: Tuple[str, ...] = ()
    achieved: Tuple[str, ...] = ()
    pending: Tuple[str, ...] = ()
    current: Optional[str] = None

    def to_trace(self) -> Dict[str, Any]:
        """留痕载荷（阶段进度进第2层留痕）。"""
        return {
            'defect_codes': list(self.defect_codes),
            'achieved': list(self.achieved),
            'pending': list(self.pending),
            'current': self.current,
        }


def derive_stage_progress(defect_codes: Sequence[str]) -> StageProgress:
    """由本轮缺陷码 ⇒ **阶段进度**（纯函数，不落库、不查库）。

    口径（**阶段达成信号**，见 ``docs/l2-stage-strategy-design.md`` §3.2）：

    - **达成**：该阶段的**所有**缺陷码在本轮反馈里**都不出现**
      （「这一类缺陷不见了」= 可观测的达成信号）；
    - **未达成（pending）**：本轮反馈里还有该阶段的缺陷码；
    - **当前阶段（current）**：第一个未达成的阶段（按 :data:`STAGE_ORDER` 推进顺序）。

    ⚠️ **不区分「已解决」与「从未报过」** —— 阶段状态不落库 ⇒ 没有历史可比
    ⇒ 「本轮没报该阶段缺陷」一律记为达成。反馈稀疏时**可能高估达成度**。

    ⚠️ **本函数只做推导，不做裁决** —— 裁决由**策略清单**做
    （:func:`process.algorithms.strategies.STRATEGIES`）：
    ``current`` 经 ``services/policies.py`` 注入 ``ScenarioContext.extra``
    ⇒ 场景条件**可引用**它（如 ``filling_stage_first`` 用
    ``current_stage == 'filling'`` 判定「还在打足阶段」）。
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
        by_stage.setdefault(stage_of(code), []).append(code)

    pending = tuple(stage for stage in STAGE_ORDER if by_stage.get(stage))
    achieved = tuple(stage for stage in STAGE_ORDER if not by_stage.get(stage))
    return StageProgress(
        defect_codes=tuple(codes),
        achieved=achieved,
        pending=pending,
        current=pending[0] if pending else None,
    )


__all__ = [
    'DEFECT_STAGE',
    'STAGE_ORDER',
    'StageProgress',
    'UNKNOWN_STAGE',
    'derive_stage_progress',
    'order_defects',
    'stage_of',
    'stage_rank',
]