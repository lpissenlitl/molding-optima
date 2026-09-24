"""molding-optima 工艺参数 Schema 集中导出

约定：
- 每个 schema 按业务对象拆到独立文件（condition.py / parameter.py / initialization.py）
- 本文件统一 re-export，外部统一 `from process.schemas import XxxSchema`
- 跨文件依赖：condition.py 引用 parameter.py（ProcessConditionAndParameterSchema 嵌套 parameter）
"""
# ===== 工艺条件 =====
from .condition import (
    ProcessConditionSchema,
    ProcessConditionAndParameterSchema,
)

# ===== 工艺参数 =====
from .parameter import (
    ProcessParameterSchema,
    ProcessParameterListSchema,
    BatchDeleteProcessParameterSchema,
)

# ===== 初始化 / 推理 =====
from .initialization import (
    MachineInfoSchema,
    PolymerInfoSchema,
    MoldInfoSchema,
    ProcessSetSchema,
    ProcessInferSchema,
    ProcessInitializationFromSourceConditionSchema,
    ProcessInitializationFromMasterdataSchema,
)

# ===== 工艺优化（infer）=====
from .optimization_infer import (
    DefectFeedbackDataSchema,
    CycleObservationSchema,
    FeedbackSchema,
    InferRequestSchema,
    SuggestionItemSchema,
    SuggestionGroupSchema,
    SuggestionSchema,
)

# ===== 仪表板统计 =====
from .statistics import (
    DashboardTrendSchema,
    DashboardOriginItemSchema,
    DashboardStatisticsSchema,
)


__all__ = [
    # 工艺条件
    "ProcessConditionSchema",
    "ProcessConditionAndParameterSchema",
    # 工艺参数
    "ProcessParameterSchema",
    "ProcessParameterListSchema",
    "BatchDeleteProcessParameterSchema",
    # 初始化 / 推理
    "MachineInfoSchema",
    "PolymerInfoSchema",
    "MoldInfoSchema",
    "ProcessSetSchema",
    "ProcessInferSchema",
    "ProcessInitializationFromSourceConditionSchema",
    "ProcessInitializationFromMasterdataSchema",
    # 工艺优化（infer）
    "DefectFeedbackDataSchema",
    "CycleObservationSchema",
    "FeedbackSchema",
    "InferRequestSchema",
    "SuggestionItemSchema",
    "SuggestionGroupSchema",
    "SuggestionSchema",
    # 仪表板统计
    "DashboardTrendSchema",
    "DashboardOriginItemSchema",
    "DashboardStatisticsSchema",
]

# 重建 ProcessConditionAndParameterSchema（其字段是 forward reference，需要在所有类加载完后解析）
ProcessConditionAndParameterSchema.model_rebuild()