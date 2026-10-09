"""
大模型推理算法模块

algorithm_type='optimization'，由 optimization_advice service 编排 chain（占位）。
"""

from .llm_algorithm import LLMEngine

__all__ = ["LLMEngine"]
