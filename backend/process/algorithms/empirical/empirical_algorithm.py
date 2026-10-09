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

from typing import List, Optional

from process.algorithms.base import AlgorithmBase, Recommendation, AlgorithmRegistry
from process.algorithms.empirical.hints import EMPIRICAL_HINTS


class EmpiricalReasoning(AlgorithmBase):
    """
    经验推理引擎 - 工程师硬编码的工艺知识

    输入：
        context.feedback.defect: 缺陷列表（取第一个的 defect_name）

    输出：
        Recommendation 列表（increase / decrease 方向）
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

    def recommend(self, context: dict) -> List[Recommendation]:
        """
        根据缺陷返回硬编码的工艺调整方向

        Args:
            context: {
                'feedback': {
                    'defect': [{'defect_name': '短射'}, ...]
                },
                'process_parameter': {...}   # 可选，用于填充 current_value
            }

        Returns:
            Recommendation 列表
        """
        defects = (context.get('feedback') or {}).get('defect') or []
        if not defects:
            return []

        # 取第一个缺陷的 defect_name（与 FuzzyEngine 处理一致）
        first = defects[0]
        if not isinstance(first, dict):
            return []
        # 优先看中文（defect_name_zh），回退到英文（defect_name）
        defect_name = first.get('defect_name_zh') or first.get('defect_name')
        if not defect_name:
            return []

        hint = self.hints.get(defect_name)
        if not hint:
            return []

        process_parameter = context.get('process_parameter') or {}
        recommendations: List[Recommendation] = []

        # increase 方向
        for param_code in hint.get('increase', []):
            current = process_parameter.get(param_code)
            recommendations.append(Recommendation(
                param_name=param_code,
                current_value=float(current) if current is not None else 0.0,
                recommended_value=None,  # 经验不给出具体数值
                confidence=None,        # 经验无置信度
                reason=f"经验推理：缺陷 {defect_name} 建议调高 {param_code}",
                source='empirical',
            ))

        # decrease 方向
        for param_code in hint.get('decrease', []):
            current = process_parameter.get(param_code)
            recommendations.append(Recommendation(
                param_name=param_code,
                current_value=float(current) if current is not None else 0.0,
                recommended_value=None,
                confidence=None,
                reason=f"经验推理：缺陷 {defect_name} 建议调低 {param_code}",
                source='empirical',
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
        first = defects[0]
        if not isinstance(first, dict):
            return False
        # 优先看中文（defect_name_zh），回退到英文（defect_name）
        defect_name = first.get('defect_name_zh') or first.get('defect_name')
        if not defect_name:
            return False
        return defect_name in self.hints

    def run(self, context: dict) -> List[Recommendation]:
        """统一入口：包装 recommend()。

        algorithm_type='optimization'，返回 List[Recommendation]。
        """
        return self.recommend(context)


AlgorithmRegistry.register('empirical', EmpiricalReasoning())
