"""
工艺模块 - 服务层（对应文件：原 process/services/）

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

业务模型（2026-10-09 统一）：
- ProcessCondition（工艺条件）是一等公民，所有 CRUD 都通过 condition
- ProcessParameter（工艺参数 / 调机轮次）是 condition 的子资源，必须依附 condition
- view_type 区分应用场景：parameter / optimization / all
- condition 一旦创建不轻易变更，变更 = 新建 condition
- condition 内容允许重复（同样 mold+polymer+machine 可有多个 condition）

合并历史：
- 2026-10-08：engines/ 目录重命名为 algorithms/
- 2026-10-08：删除 expert.py（孤儿代码）、statistics.py（迁至 analytic app）
- 2026-10-09：record.py + parameter.py + parameter_transformer.py + optimization_advice.py
              合并为 condition.py
- 2026-10-09：parameter_init.py → parameter_initialize.py
- 2026-10-09：optimization_infer.py → parameter_optimize.py
- 2026-10-09：transplant.py → parameter_transplant.py

类命名规范：<领域><动作>Service。
Process 前缀已去掉（Django app 路径本身已是命名空间，Process 前缀冗余）。
"""
from .tuning import TuningService
from .parameter_initialize import ParameterInitializeService
from .parameter_optimize import ParameterOptimizeService

__all__ = [
    "TuningService",
    "ParameterInitializeService",
    "ParameterOptimizeService",
]