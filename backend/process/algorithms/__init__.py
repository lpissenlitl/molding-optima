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


================================================================================
调参链的 4 层（用户口径，2026-11-12）
================================================================================

本目录里的**四个平级模块**就是调参链的 4 层，每层只回答一个问题，
依赖**单向**（``anchors ← decide_direction ← integrate_params ← check_params``）：

==============  ==============================  ==============================
层              模块                            回答什么
==============  ==============================  ==============================
第1层           各算法包（fuzzy/llm/empirical） 算法给出调整方向（平级建议）
第2层           ``decide_direction.py``         结合实际情况，确定**明确的**调整方向
第3层           ``integrate_params.py``         整合参数（物理上自洽）
第4层           ``check_params.py``             校验参数合理性（**只读**，不改值）
底座            ``anchors.py``                  字段口径 + 锚点关系（只定义一次）
==============  ==============================  ==============================

**service 层把它们串成直线**（每层一次调用）：

.. code-block:: python

    # 第2层：结合实际情况，确定明确的调整方向
    #   from process.algorithms.decide_direction import resolve_direction
    direction = resolve_direction(candidates, targets, baseline, ...)

    # 第3层：整合参数（写入方向 + 锚点传导自洽）
    #   from process.algorithms.integrate_params import apply_direction
    integrated = apply_direction(baseline, direction, previous=baseline)

    # 第4层：校验参数合理性（只报不阻断）
    #   from process.algorithms.check_params import validate
    validation = validate(integrated.values)

⚠️ **红线**：业务判断（场景是什么 / 调哪些 / 按什么次序 / 留几个）必须是**数据**
（策略清单文件 ``strategies.py``），代码只负责读 + 匹配 + 裁决；
物理算式（充填量→行程、MEL 目标→计量位置）落代码，因为那是**逻辑**。

**根目录其它文件**（不属于 4 层链路）：

=============================  ==============================================
文件                           职责
=============================  ==============================================
``base.py``                    算法包基类 + 注册中心（``AlgorithmRegistry``）
``field_contract.py``          算法入参契约机制（字段字典 ⊥ 校验机制分离）
``material_physics.py``        材料物理常量 + 派生公式（专家/模糊共用）
``defect_selection.py``        缺陷选取（一次只解决一个缺陷，**L1 侧**）
``strategies.py``              策略清单（文件版）：第2层的规则来源
=============================  ==============================================
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
