"""
大模型推理引擎（占位实现）

定位：作为工艺参数优化 engine 池的一员，补充 fuzzy 的不足场景（如冷门缺陷 / 小众材料）。
- algorithm_type = "optimization"，进入优化 chain
- 当前为占位实现：is_available() 始终返回 False，chain 会自动跳过

未来实现计划：
- 基于 RAG 检索历史调参案例
- 使用 LLM 推理生成参数调整推荐
- recommend() 返回 Recommendation 列表与 fuzzy 同 schema
"""

from typing import List

from process.algorithms.base import AlgorithmBase, Recommendation, AlgorithmRegistry


class LLMEngine(AlgorithmBase):
    """
    大模型推理算法（占位）

    algorithm_type='optimization'，由 optimization_advice service 编排 chain。
    使用大语言模型进行工艺参数推荐。is_available() 始终返回 False，
    chain 调用时会跳过本算法。
    """

    algorithm_name = "大模型推理"
    algorithm_type = "optimization"
    algorithm_subtype = "llm"

    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        # TODO: 后续初始化 LLM 客户端

    def recommend(self, context: dict) -> List[Recommendation]:
        """
        根据上下文返回推荐

        Args:
            context: {
                'defect_feedbacks': [...],
                'process_parameter': {...},
                'tuning_history': [...],
                'similar_cases': [...],
            }

        Returns:
            推荐列表
        """
        # TODO: 后续实现 RAG + LLM 推理
        return []

    def is_available(self, context: dict) -> bool:
        """
        判断是否可用

        需要配置 LLM API
        """
        # TODO: 后续检查配置
        return False

    def run(self, context: dict) -> List[Recommendation]:
        """统一入口：包装 recommend()。

        algorithm_type='optimization'，返回 List[Recommendation]。
        """
        return self.recommend(context)

    def _retrieve_similar_cases(self, context: dict) -> List[dict]:
        """向量检索相似历史案例"""
        # TODO: 后续实现向量检索
        return []

    def _build_prompt(self, context: dict, similar_cases: List[dict]) -> str:
        """构建 LLM prompt"""
        # TODO: 后续实现
        return ""

    def _parse_llm_response(self, response: str) -> List[Recommendation]:
        """解析 LLM 输出"""
        # TODO: 后续实现
        return []


# 注册引擎
AlgorithmRegistry.register('llm', LLMEngine())
