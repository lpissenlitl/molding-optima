"""molding-optima 工艺参数 Schema 集中导出

约定：
- 每个 schema 按业务对象拆到独立文件（condition.py / parameter.py / record.py / tuning.py / ...）
- 本文件统一 re-export，外部统一 `from process.schemas import XxxSchema`
- 跨文件依赖单向: record.py → condition.py (records 写入强验证 condition 字段)
"""
# ===== 工艺条件 =====
from .condition import (
    ProcessConditionSchema,
    ProcessConditionListSchema,
    BatchDeleteConditionSchema,
)

# ===== 工艺参数（独立 parameter service 契约）=====
#   FLAT (算法 / 移植) + NEST (前端 UI) 两种格式都独立导出
from .parameter import (
    ProcessParameterSchema,
    ProcessParameterListSchema,
    ProcessParameterTreeSchema,
    SettingProcessSchema,
    ProcessParameterNestSchema,
    ProcessParameterUpdateSchema,
)

# ===== 初始化 / 推理 =====
from .initialization import (
    MachineInfoSchema,
    PolymerInfoSchema,
    MoldInfoSchema,
    ProcessSetSchema,
    ProcessInitializeFromMasterdataSchema,
    ProcessInitializeFromConditionSchema,
    ProcessInitializeFromProvidedSchema,
)

# ===== 工艺参数调优（optimize）=====
from .optimization import (
    DefectFeedbackDataSchema,
    CycleObservationSchema,
    FeedbackSchema,
    # 三维上下文（调优精度旋钮）
    OptimizeMoldInfoSchema,
    OptimizeMachineInfoSchema,
    OptimizePolymerInfoSchema,
    # 两个入口
    ProcessOptimizeFromConditionSchema,
    ProcessOptimizeFromProvidedSchema,
    SuggestionItemSchema,
    SuggestionGroupSchema,
    SuggestionSchema,
)

# ===== 工艺记录（独立 records service 契约）=====
from .record import (
    ProcessRecordListSchema,
    ProcessConditionAndParameterSchema,
    ProcessConditionWriteSchema,
    ProcessRecordBatchDeleteSchema,
)

# ===== 调机动作 (人工调机反馈 + 批量删除) =====
from .tuning import (
    TuningRecordRequestSchema,
    TuningBatchDeleteSchema,
)

# ===== 工艺参数移植 =====
from .transplant import (
    TransplantRequestSchema,
)


__all__ = [
    # 工艺条件
    "ProcessConditionSchema",
    "ProcessConditionListSchema",
    "BatchDeleteConditionSchema",
    # 工艺参数（独立 parameter service 契约）
    "ProcessParameterSchema",
    "ProcessParameterListSchema",
    "ProcessParameterTreeSchema",
    "SettingProcessSchema",
    "ProcessParameterNestSchema",
    "ProcessParameterUpdateSchema",
    # 初始化 / 推理
    "MachineInfoSchema",
    "PolymerInfoSchema",
    "MoldInfoSchema",
    "ProcessSetSchema",
    "ProcessInitializeFromMasterdataSchema",
    "ProcessInitializeFromConditionSchema",
    "ProcessInitializeFromProvidedSchema",
    # 工艺参数调优（optimize）
    "DefectFeedbackDataSchema",
    "CycleObservationSchema",
    "FeedbackSchema",
    "OptimizeMoldInfoSchema",
    "OptimizeMachineInfoSchema",
    "OptimizePolymerInfoSchema",
    "ProcessOptimizeFromConditionSchema",
    "ProcessOptimizeFromProvidedSchema",
    "SuggestionItemSchema",
    "SuggestionGroupSchema",
    "SuggestionSchema",
    # 工艺记录（独立 records service 契约）
    "ProcessRecordListSchema",
    "ProcessConditionAndParameterSchema",
    "ProcessConditionWriteSchema",
    "ProcessRecordBatchDeleteSchema",
    # 调机动作 (人工调机反馈 + 批量删除)
    "TuningRecordRequestSchema",
    "TuningBatchDeleteSchema",
    # 工艺参数移植
    "TransplantRequestSchema",
]
