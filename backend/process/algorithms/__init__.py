"""AI 推理类算法库。

本目录（process/algorithms/）是 process app 下所有 AI 推理类算法的统一实现库。
通过 algorithm_type 字段区分业务场景，子模块按 algorithm_type 分类：
- 'optimization' 类型（通过 AlgorithmRegistry 编排 chain）：
    - fuzzy/         algorithm_subtype='fuzzy'
    - llm/           algorithm_subtype='llm'
    - empirical/     algorithm_subtype='empirical'
- 'initialization' 类型（service 直调，不走 Registry）：
    - expert/        algorithm_subtype='expert'
- 'mining' 类型（未来由独立 service 编排）：
    - mining/        含 rule_miner.py（algorithm_subtype='rule_miner'）

**例外**：``common/`` **不是算法子包** —— 它不注册任何 algorithm_type，
是被多条算法线与 service 层共同引用的**跨算法线公共底座**（详见
``common/__init__.py``）；不要把它当成一条算法线。

注意：
- 子模块在 __init__ 中显式 import 是为了触发 AlgorithmRegistry.register
- 仅 optimization 类型会注册到 AlgorithmRegistry
- initialization / mining 类型各只有一个实现，service 直调即可
- 如需新增算法：建子包 + 子模块的 __init__.py + 本文件显式 import
- 如需新增 algorithm_type：在 algorithms/base.AlgorithmBase.algorithm_type 标注


================================================================================
本目录只放「算法」与「跨算法线公共件」
================================================================================

**调参链的 4 层不在本目录** —— L2 裁决 / L3 整合 / L4 校验 + 底座 ``anchors``
+ 两份配套（``tuning_strategy`` / ``defect_selection``）是**优化链路的编排与
领域计算**，不是 AI 推理算法 ⇒ 住在 ``process/services/optimize_chain/``
（见该包的 docstring，含 4 层链路表与红线）。

=============================  ==============================================
文件 / 目录                     职责
=============================  ==============================================
``base.py``                    算法包基类 + 注册中心（``AlgorithmRegistry``）
``common/``                    跨算法线公共底座（**不是算法子包**）：
                               ``field_contract.py`` 算法入参契约机制
                               ``material_physics.py`` 材料物理常量 + 派生公式
``fuzzy/`` 内的算法命名空间：  ``field_names.py`` 字段名映射（业务 ↔ 算法）
                               ``device_limits.py`` 算法族表（区间类型 + 查表 + 跨命名空间翻译）
=============================  ==============================================

【注意】**``common/`` 全目录零外部依赖** —— 每个模块都只 import
同包相对模块或标准库，**不 import 任何算法包 / Django / ORM** ⇒ 依赖方向恒为
「算法包 / service 层 → common」⇒ 公共底座**不反向依赖任何算法线**
⇒ **无循环导入风险**。

【注意】**根目录只留 ``base.py``**：它是 ``algorithm_type`` /
``algorithm_subtype`` 的**标注处**（=「算法是什么」的定义），也是本包的门面
（``__all__`` 导出 3 个符号）⇒ 必须住在根。其余件要么是算法子包，要么归
``common/`` ⇒ **看文件落在哪，就知道它是不是算法**（无歧义）。
"""

from .base import AlgorithmBase, AlgorithmRegistry, AlgorithmRecommendation

# 显式 import 子模块以触发 AlgorithmRegistry.register
# optimization 类型（进入工艺参数优化 chain）
from .fuzzy import engine  # noqa: F401
from .llm import llm_algorithm  # noqa: F401
from .empirical import empirical_algorithm  # noqa: F401

# initialization 类型（不走 Registry，process.services.parameter_initialize 直调）
# from .expert import ...  # 不在此 import，避免循环依赖

# mining 类型（不走 Registry，未来由独立 service 编排）
# from .mining import rule_miner  # noqa: F401  （algorithm_subtype='rule_miner'）

__all__ = [
    "AlgorithmBase",
    "AlgorithmRegistry",
    "AlgorithmRecommendation",
]
