"""
经验推理引擎 - 基于工程师经验编码的硬编码工艺知识

数据来源：
- engines/empirical/hints.py 的 EMPIRICAL_HINTS 字典
- 原 process.services.optimization_advice.DEFECT_OPTIMIZATION_HINTS（已迁移到 algorithms/empirical/hints.py）

定位：
- 作为工艺参数优化 chain 的最后兜底
- fuzzy / llm 引擎均未返回推荐时启用
- 与 fuzzy 模型驱动的不同：本引擎是"规则-结论"硬编码，不依赖运行时数据

设计理念：
- "Empirical" 在工程领域特指"经验方法"——虽然没有严格数学推导但工程上有效
- 不是临时 demo，是"工程师多年试错经验的形式化沉淀"
- 与 fuzzy 的"模型驱动"形成对比：fuzzy 动态推断，本引擎静态查表

与其他引擎对比：
| 引擎        | 类型     | 数据来源     | 计算成本 | 可解释性 |
|-------------|----------|--------------|----------|----------|
| fuzzy       | 模型驱动 | 模糊规则库   | 中       | 高       |
| llm         | 模型驱动 | 大模型推理   | 高       | 中       |
| empirical   | 经验查表 | 工程师硬编码 | 低       | 高       |
"""

import json
import logging
from typing import List, Optional

from process.algorithms.base import AlgorithmBase, AlgorithmRecommendation, AlgorithmRegistry
from process.algorithms.defect_selection import (
    DefectSelection,
    FirstOnlyDefectStrategy,
    select_defect,
)
from process.algorithms.empirical.hints import EMPIRICAL_HINTS

logger = logging.getLogger(__name__)

#: 本引擎的缺陷选取策略 = **只看列表第一个**（历史行为，保持不变）。
#:
#: 与 fuzzy 的「取第一个有效项」**刻意不同** —— 两个引擎历史语义本就不同，
#: 强行统一会让经验推理在「首项无效、次项有效」时凭空多出推荐。
#: 两者都从同一个真相源取（`process/algorithms/defect_selection.py`），
#: 差别只在**策略**，不在实现。
_FIRST_ONLY = FirstOnlyDefectStrategy()


def _log_selection(selection: DefectSelection) -> None:
    """缺陷选取留痕（结构化日志）。

    本引擎没有 per-request 诊断容器（那是 fuzzy 的机制，见
    `process/algorithms/fuzzy/diagnostics.py`），故用标准日志出口。

    ⚠️ **只在有项被跳过时才打** —— 正常路径（首项有效）不产生任何日志噪音；
    有跳过才说明「为什么放弃了后面的缺陷」，那才是需要被看见的情况。
    """
    if not selection.skipped:
        return
    logger.info('[EmpiricalReasoning] 缺陷选取 %s',
                json.dumps(selection.to_trace(), ensure_ascii=False, default=str))


class EmpiricalReasoning(AlgorithmBase):
    """
    经验推理引擎 - 工程师硬编码的工艺知识

    输入：
        context.feedback.defect: 缺陷列表（取第一个的 keyword_name）

    输出：
        AlgorithmRecommendation 列表（increase / decrease 方向）
    """

    algorithm_name = "经验推理"
    algorithm_type = "optimization"
    algorithm_subtype = "empirical"

    def __init__(self, hints: Optional[dict] = None):
        """
        Args:
            hints: 自定义经验字典（默认用 EMPIRICAL_HINTS，便于测试注入）
        """
        self.hints = hints if hints is not None else EMPIRICAL_HINTS

    def recommend(self, context: dict) -> List[AlgorithmRecommendation]:
        """
        根据缺陷返回硬编码的工艺调整方向

        Args:
            context: {
                'feedback': {
                    'defect': [{'keyword_name': 'SHORTSHOT', 'level': 'high'}, ...]
                },
                'process_parameter': {...}   # 可选，用于填充 current_value
            }

        Returns:
            AlgorithmRecommendation 列表
        """
        defects = (context.get('feedback') or {}).get('defect') or []
        if not defects:
            return []

        # 缺陷选取 —— **唯一真相源**（`process/algorithms/defect_selection.py`），
        # 本引擎用「只看第一个」策略（与历史行为逐字一致）。
        # 反馈传的是 keyword_name（SHORTSHOT / SHRINKAGE / ...），
        # 与 RuleMethod.defect_code、RuleKeyword.keyword_name 对齐。
        # 历史实现读的是中文 defect_name / defect_name_zh，
        # 与 hints 表的英文 key 永远对不上 → 经验引擎恒返回空。
        selection = select_defect(context, strategy=_FIRST_ONLY)
        _log_selection(selection)

        defect_name = selection.keyword_name
        if not defect_name:
            return []

        hint = self.hints.get(defect_name)
        if not hint:
            return []

        process_parameter = context.get('process_parameter') or {}
        recommendations: List[AlgorithmRecommendation] = []

        # increase 方向
        for param_code in hint.get('increase', []):
            current = process_parameter.get(param_code)
            recommendations.append(AlgorithmRecommendation(
                param_name=param_code,
                current_value=float(current) if current is not None else 0.0,
                recommended_value=None,  # 经验不给出具体数值
                confidence=None,        # 经验无置信度
                reason=f"经验推理：缺陷 {defect_name} 建议调高 {param_code}",
                source='empirical',
                direction='increase',
            ))

        # decrease 方向
        for param_code in hint.get('decrease', []):
            current = process_parameter.get(param_code)
            recommendations.append(AlgorithmRecommendation(
                param_name=param_code,
                current_value=float(current) if current is not None else 0.0,
                recommended_value=None,
                confidence=None,
                reason=f"经验推理：缺陷 {defect_name} 建议调低 {param_code}",
                source='empirical',
                direction='decrease',
            ))

        return recommendations

    def is_available(self, context: dict) -> bool:
        """
        经验推理总是可用（只要有 defect 信息且在 hints 表中）

        注：此方法仅判断"是否能调用"，是否真返回推荐由 recommend() 决定
        """
        defects = (context.get('feedback') or {}).get('defect') or []
        if not defects:
            return False
        # 缺陷码取 keyword_name（英文码，与 hints 表 key 对齐）
        # ⚠️ 不留痕：`is_available` 会被 chain 调度频繁调用，每次都打日志是噪音。
        #    留痕只发生在 `recommend()`（真正做决策的地方）。
        defect_name = select_defect(context, strategy=_FIRST_ONLY).keyword_name
        if not defect_name:
            return False
        return defect_name in self.hints

    def run(self, context: dict) -> List[AlgorithmRecommendation]:
        """统一入口：包装 recommend()。

        algorithm_type='optimization'，返回 List[AlgorithmRecommendation]。
        """
        return self.recommend(context)


AlgorithmRegistry.register('empirical', EmpiricalReasoning())
