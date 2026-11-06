"""工艺模块 - 服务层

服务按领域分组（扁平结构，不拆子目录）：
- condition 域（核心实体）:
    condition         — 工艺条件全生命周期 CRUD + frontend 转换 + optimization 预览
- parameter 子领域（condition 的子资源动作）:
    parameter_initialize  — 工艺参数初始化推理
    parameter_optimize    — 工艺优化 infer（落库）
    parameter_transplant  — 工艺参数移植
- 其他独立域:
    rule             — 规则 CRUD
    tuning           — 调参记录

业务模型：
- ProcessCondition（工艺条件）是一等公民，所有 CRUD 都通过 condition
- ProcessParameter（工艺参数 / 调机轮次）是 condition 的子资源，必须依附 condition
- view_type 区分应用场景：parameter / optimization / all
- condition 一旦创建不轻易变更，变更 = 新建 condition
- condition 内容允许重复（同样 mold+polymer+machine 可有多个 condition）

类命名规范：<领域><动作>Service（Django app 路径本身已是命名空间，不加 Process 前缀）。
"""
from .tuning import TuningService
from .parameter_initialize import ParameterInitializeService
from .parameter_optimize import ParameterOptimizeService

__all__ = [
    "TuningService",
    "ParameterInitializeService",
    "ParameterOptimizeService",
]