"""
AI 推理类算法库

本目录（process/algorithms/）是 process app 下所有 AI 推理类算法的统一实现库。
物理位置统一（平铺），通过 algorithm_type 字段区分业务场景。

子模块按 algorithm_type 分类：
- 'optimization' 类型（通过 AlgorithmRegistry 编排 chain）：
    - fuzzy/         algorithm_subtype='fuzzy'
    - llm/           algorithm_subtype='llm'
    - empirical/     algorithm_subtype='empirical'
- 'initialization' 类型（service 直调，不走 Registry）：
    - expert/        algorithm_subtype='expert'
- 'mining' 类型（未来由独立 service 编排）：
    - mining/        含 rule_miner.py（algorithm_subtype='rule_miner'）

注意：
- 子模块在 __init__ 中显式 import 是为了触发 AlgorithmRegistry.register
- 仅 optimization 类型会注册到 AlgorithmRegistry
- initialization / mining 类型各只有一个实现，service 直调即可
- 如需新增算法：建子包 + 子模块的 __init__.py + 本文件显式 import
- 如需新增 algorithm_type：在 algorithms/base.AlgorithmBase.algorithm_type 标注
"""

from .base import AlgorithmBase, AlgorithmRegistry, Recommendation

# 显式 import 子模块以触发 AlgorithmRegistry.register
# optimization 类型（进入工艺参数优化 chain）
from .fuzzy import fuzzy_algorithm  # noqa: F401
from .llm import llm_algorithm  # noqa: F401
from .empirical import empirical_algorithm  # noqa: F401

# initialization 类型（不走 Registry，process.services.parameter_initialize 直调）
# from .expert import ...  # 不在此 import，避免循环依赖

# mining 类型（不走 Registry，未来由独立 service 编排）
# from .mining import rule_miner  # noqa: F401  （algorithm_subtype='rule_miner'）

__all__ = [
    "AlgorithmBase",
    "AlgorithmRegistry",
    "Recommendation",
]
