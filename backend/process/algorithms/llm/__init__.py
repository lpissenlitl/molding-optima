"""
大模型推理算法模块

algorithm_type='optimization'，由 condition service 通过 AlgorithmRegistry 编排 chain（占位）。
"""

from .llm_algorithm import LLMEngine

__all__ = ["LLMEngine"]
