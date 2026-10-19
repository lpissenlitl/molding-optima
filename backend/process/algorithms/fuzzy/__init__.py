"""
模糊推理算法模块

algorithm_type='optimization'，由 condition service 通过 AlgorithmRegistry 编排 chain。

模块组成：
- FuzzyEngine: 模糊推理引擎
- specs: 调优入参契约（字段选择 + 必填等级）+ OptimizeDataValidator
  与 expert 同构：契约定在算法层，所有调用方（service / 第三方 / CLI）自动受约束
"""

from .fuzzy_algorithm import FuzzyEngine
from .specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OPTIMIZE_POLYMER_INFO_FIELDS,
    OPTIMIZE_MOLD_INFO_FIELDS,
    REQUIRED_OPTIMIZE_MACHINE_FIELDS,
    REQUIRED_OPTIMIZE_POLYMER_FIELDS,
    REQUIRED_OPTIMIZE_MOLD_FIELDS,
    OptimizeDataValidator,
)

__all__ = [
    "FuzzyEngine",
    "OPTIMIZE_MACHINE_INFO_FIELDS",
    "OPTIMIZE_POLYMER_INFO_FIELDS",
    "OPTIMIZE_MOLD_INFO_FIELDS",
    "REQUIRED_OPTIMIZE_MACHINE_FIELDS",
    "REQUIRED_OPTIMIZE_POLYMER_FIELDS",
    "REQUIRED_OPTIMIZE_MOLD_FIELDS",
    "OptimizeDataValidator",
]
