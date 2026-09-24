"""molding-optima 工艺优化（infer）Schema 定义

对应接口：
- POST /api/processes/optimization/infer/

调用链路（详见 docs/optimization-infer-design-status-2026-09-22.md）：
  Step 1: 入口适配  —— condition_id + parent_seq_idx（业务编号）反查 parent_param
  Step 2: 数据准备  —— parent_param.parameters 作为基线，可选 parameter 覆盖
  Step 3: 推理算法  —— recommendation_service.get_recommendations()（接口契约）
  Step 4: 落库       —— ProcessParameter + TuningRecord + Recommendation 原子事务

术语规范：
- parameter：用户手动修改覆盖（可选）
- feedback：嵌套结构（defect / observations / tuning_result）
- new_parameter：算法推理后的新工艺参数（含 parameter_id）
- suggestion：算法建议展示对象（含 source_type / recommendation_id / groups）
"""
from typing import Optional, List, Dict, Any

from pydantic import Field

from extensions.schemas import BaseSchema


# ============================================================================
# 入参 Schema（Feedback 子结构）
# ============================================================================

class DefectFeedbackDataSchema(BaseSchema):
    """缺陷反馈数据（与前端 DefectFeedbackData 对齐）

    数据约束：
    - keyword_id / keyword_name：可空（用户未选时为 null；后端匹配走 keyword_name）
    - level：当 keyword_name='DEFECTFREE' 时为 null；其他情况按 fuzzy_level 选词
    - position：缺陷位置（产品区域描述，如 "DL飞边3"）
    - position_3d：可选的 3D 模型点选坐标
    """

    keyword_id: Optional[int] = Field(None, description="缺陷关键词 ID（关联 RuleKeyword.id，可空）")
    keyword_name: Optional[str] = Field(None, description="缺陷关键词名称（冗余存，可空）")
    level: Optional[str] = Field(None, description="缺陷档位（low/medium/high/...）")
    position: Optional[str] = Field("", description="缺陷位置")
    position_3d: Optional[Dict[str, float]] = Field(
        None, description="3D 模型点选坐标（可选）",
    )


class CycleObservationSchema(BaseSchema):
    """实测观察项

    对齐前端 CycleObservation：
    - param_key：4 种参数类型之一（actual_product_weight / peak_pressure / ...）
    - value：单值字段，可为 null（未观测）
    """

    param_key: str = Field(
        ...,
        description="实测参数键：actual_product_weight / peak_pressure / injection_time / cycle_time",
    )
    value: Optional[float] = Field(None, description="实测值（未观测时为 null）")


class FeedbackSchema(BaseSchema):
    """反馈信息（嵌套在 InferRequest 内）

    3 类反馈合一：
    - defect[]：缺陷反馈列表（多个，算法识别优先级）
    - observations[]：实测观察（按需传）
    - tuning_result：增量反馈（effective / ineffective / null）
    """

    defect: List[DefectFeedbackDataSchema] = Field(
        default_factory=list, description="缺陷反馈列表（可空，可多个）",
    )
    observations: List[CycleObservationSchema] = Field(
        default_factory=list, description="实测观察列表（按需传）",
    )
    tuning_result: Optional[str] = Field(
        None, description="调机效果评价：effective / ineffective / null",
    )


class InferRequestSchema(BaseSchema):
    """工艺优化 infer 请求 Schema

    业务语义：
    - condition_id：工艺条件 ID（必填，后端反查 mold/machine/polymer 上下文）
    - parent_seq_idx：基准业务编号（必填，与 condition_id 联合定位父节点）
    - parameter：手动修改覆盖（可选，结构化 dict）
    - feedback：反馈信息（嵌套结构）

    主动不传的字段（从 condition_id 反查）：
    - ❌ machine_id / polymer_id / mold_id / process_set
    - ❌ subrule_no（后端算法自动识别）
    - ❌ 上一轮 suggestion（后端实时推理）
    """

    condition_id: int = Field(..., description="工艺条件 ID（必填）")
    parent_seq_idx: int = Field(
        ..., description="基准业务编号 seq_idx（必填，与 condition_id 联合定位父节点）",
    )
    parameter: Optional[Dict[str, Any]] = Field(
        None, description="手动修改覆盖（结构化 dict，与前端 settingProcessForm 对齐）",
    )
    feedback: FeedbackSchema = Field(
        default_factory=FeedbackSchema, description="反馈信息",
    )


# ============================================================================
# 出参 Schema（Suggestion 子结构）
# ============================================================================

class SuggestionItemSchema(BaseSchema):
    """单条建议项

    对齐前端 Suggestion：
    - description：建议文本
    - direction：调整方向（increase / decrease / hold / check）
    - rule_refs：关联规则 ID 列表
    """

    description: str = Field(..., description="建议文本")
    direction: Optional[str] = Field(
        None, description="调整方向：increase / decrease / hold / check",
    )
    rule_refs: Optional[List[str]] = Field(
        default_factory=list, description="关联规则 ID 列表",
    )


class SuggestionGroupSchema(BaseSchema):
    """同一类别的多个建议

    与后端 Recommendation.recommendations 对齐（按 category 分组）：
    - category：类别名（如 '注射参数' / '保压参数'）
    - icon：类别图标（mdi iconify 名）
    - items：该类下的多条建议
    """

    category: str = Field(..., description="类别名")
    icon: Optional[str] = Field(None, description="类别图标（mdi iconify 名）")
    items: List[SuggestionItemSchema] = Field(
        default_factory=list, description="该类下的多条建议",
    )


class SuggestionSchema(BaseSchema):
    """算法建议（infer 返回的核心对象）

    设计要点：
    - source_type：算法来源（fuzzy_rule / rule_miner / llm ...）
    - recommendation_id：落库后产生（关联后端 Recommendation 表）
    - groups：按类别分组的建议项
    """

    source_type: str = Field(..., description="算法来源类型")
    recommendation_id: Optional[int] = Field(
        None, description="推荐记录 ID（落库后产生）",
    )
    groups: List[SuggestionGroupSchema] = Field(
        default_factory=list, description="按类别分组的建议项",
    )


__all__ = [
    "DefectFeedbackDataSchema",
    "CycleObservationSchema",
    "FeedbackSchema",
    "InferRequestSchema",
    "SuggestionItemSchema",
    "SuggestionGroupSchema",
    "SuggestionSchema",
]