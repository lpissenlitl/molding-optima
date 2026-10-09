"""
经验推理算法模块

algorithm_type='optimization'，由 condition service 编排 chain（兜底）。
基于工程师经验编码的硬编码工艺知识。
（数据来源：原 process.services.optimization_advice.DEFECT_OPTIMIZATION_HINTS，已迁至 algorithms/empirical/hints.py）
"""

from .empirical_algorithm import EmpiricalReasoning
from .hints import EMPIRICAL_HINTS

__all__ = ["EmpiricalReasoning", "EMPIRICAL_HINTS"]
