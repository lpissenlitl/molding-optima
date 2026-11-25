"""经验推理引擎 - 基于工程师经验编码的硬编码工艺知识。

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

from process.algorithms.base import (
    AlgorithmBase,
    AlgorithmRecommendation,
    AlgorithmRegistry,
    filter_unchanged,
)
from process.algorithms.empirical.hints import EMPIRICAL_HINTS

logger = logging.getLogger(__name__)


def _log_selection(trace: dict) -> None:
    """缺陷选取留痕（结构化日志）。

    本引擎没有 per-request 诊断容器（那是 fuzzy 的机制，见
    `process/algorithms/fuzzy/diagnostics.py`），故用标准日志出口。

    【注意】**只在有项被跳过时才打** —— 正常路径（选中的缺陷有效）不产生任何日志噪音；
    有跳过才说明「为什么放弃了后面的缺陷」，那才是需要被看见的情况。

    【注意】选取**不在本引擎**（service 预处理层做一次，见
    `services/optimize_chain/defect_selection.py::select_defect`）⇒ 本函数
    只转述预处理层写回 feedback 的 trace。
    """
    trace = trace or {}
    if not (trace.get('skipped') or []):
        return
    logger.info('[EmpiricalReasoning] 缺陷选取 %s',
                json.dumps(trace, ensure_ascii=False, default=str))


class EmpiricalReasoning(AlgorithmBase):
    """经验推理引擎 - 工程师硬编码的工艺知识。

    输入：
        context.feedback: 缺陷反馈（**已收敛** —— defects 只剩本轮处理的那条，
            含 keyword_name / level / position）

    输出：
        AlgorithmRecommendation 列表（increase / decrease 方向）；
        参数名用**业务字段名**（经验库与 context 同一命名空间 ⇒ 出口无需翻译）
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
        """根据缺陷返回硬编码的工艺调整方向。

        Args:
            context: {
                'feedback': {
                    'defects': [{'keyword_name': 'SHORTSHOT', 'level': 'high'}, ...]
                },
                'process_parameter': {...}   # 可选（业务字段名），用于填充 current_value
            }

        Returns:
            AlgorithmRecommendation 列表
        """
        # 缺陷 —— **选取已在 service 预处理层做完**（只做一次）
        # （见 `services/optimize_chain/defect_selection.py::select_defect`）
        # ⇒ 本引擎**不再自己挑缺陷**，只读整理结果。
        # 反馈传的是 keyword_name（SHORTSHOT / SHRINKAGE / ...），
        # 与 RuleMethod.defect_code、RuleKeyword.keyword_name 对齐。
        # 历史实现读的是中文 defect_name / defect_name_zh，
        # 与 hints 表的英文 key 永远对不上 → 经验引擎恒返回空。
        feedback = context.get('feedback') or {}
        defects = feedback.get('defects') or []
        selected = defects[0] if defects else {}
        _log_selection(feedback.get('defect_selection'))

        defect_name = selected.get('keyword_name') if isinstance(selected, dict) else None
        if not defect_name:
            return []

        hint = self.hints.get(defect_name)
        if not hint:
            return []

        process_parameter = context.get('process_parameter') or {}
        recommendations: List[AlgorithmRecommendation] = []

        # increase 方向
        for param_name in hint.get('increase', []):
            # 【注意】经验库用**业务字段名**（与 context 同一命名空间）⇒ 直接查
            current = process_parameter.get(param_name)
            recommendations.append(AlgorithmRecommendation(
                param_name=param_name,
                # 【注意】参数不存在 ⇒ None（**不是 0.0**）：「当前值是 0」
                #   与「压根没这个参数」是两回事 —— 报 0 会被下游当成真实数值
                #   展示（看起来像「该参数被调到 0」），也会参与数值比较。
                current_value=float(current) if current is not None else None,
                recommended_value=None,  # 经验不给出具体数值
                confidence=None,        # 经验无置信度
                reason=f"经验推理：缺陷 {defect_name} 建议调高 {param_name}",
                source='empirical',
                direction='increase',
            ))

        # decrease 方向
        for param_name in hint.get('decrease', []):
            current = process_parameter.get(param_name)
            recommendations.append(AlgorithmRecommendation(
                param_name=param_name,
                # 【注意】参数不存在 ⇒ None（**不是 0.0**）：「当前值是 0」
                #   与「压根没这个参数」是两回事 —— 报 0 会被下游当成真实数值
                #   展示（看起来像「该参数被调到 0」），也会参与数值比较。
                current_value=float(current) if current is not None else None,
                recommended_value=None,
                confidence=None,
                reason=f"经验推理：缺陷 {defect_name} 建议调低 {param_name}",
                source='empirical',
                direction='decrease',
            ))

        return filter_unchanged(recommendations)

    def is_available(self, context: dict) -> bool:
        """
        经验推理总是可用（只要有 defect 信息且在 hints 表中）

        注：此方法仅判断"是否能调用"，是否真返回推荐由 recommend() 决定
        """
        # 缺陷码取 keyword_name（英文码，与 hints 表 key 对齐）
        # 【注意】不留痕：`is_available` 会被 chain 调度频繁调用，每次都打日志是噪音。
        #    留痕只发生在 `recommend()`（真正做决策的地方）。
        defects = (context.get('feedback') or {}).get('defects') or []
        selected = defects[0] if defects else {}
        defect_name = selected.get('keyword_name') if isinstance(selected, dict) else None
        if not defect_name:
            return False
        return defect_name in self.hints

    def run(self, context: dict) -> List[AlgorithmRecommendation]:
        """统一入口：包装 recommend()。

        algorithm_type='optimization'，返回 List[AlgorithmRecommendation]。
        """
        return self.recommend(context)


AlgorithmRegistry.register('empirical', EmpiricalReasoning())
