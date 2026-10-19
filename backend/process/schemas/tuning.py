"""
调机反馈 Schema

对应 URL 段: processes/conditions/<id>/parameters/<pid>/tuning-feedback/  业务对象 ID: condition_id + parameter_id

tuning-feedback 子资源 (2026-10-12 改造):
- 原归属: tunings/feedback/<condition_id>/ (李鬼归属, tuning 实际属于 parameter)
- 新归属: parameters/<pid>/tuning-feedback/ (parameter 是 tuning 的真正父资源)

业务语义:
- parameter_id 从 URL 限定, 不再从 body 传入 (一意唯一)
- 调机反馈隶属于某个具体 parameter (多轮迭代场景)
- 缺陷反馈/调整记录随 parameter 归属

独立 tuning service 契约:
- TuningRecordRequestSchema    人工调机反馈 (写 TuningRecord)
- TuningBatchDeleteSchema      批量删除 (仍按 condition_id, 与 records/batch-delete 职责重复, 保留备用)
"""
from typing import List, Dict, Any, Optional

from pydantic import Field

from extensions.schemas import BaseSchema


class TuningRecordRequestSchema(BaseSchema):
    """人工调机反馈 (写 TuningRecord)

    业务语义:
    - parameter_id 从 URL 限定 (POST /conditions/<id>/parameters/<pid>/tuning-feedback/)
    - 不再从 body 传 parameter_id (URL 已表达)
    - 反馈字段: defect_feedbacks / observations / tuning_result / result_detail
    """

    defect_feedbacks: Optional[List[Dict[str, Any]]] = Field(
        None,
        description=(
            "缺陷反馈列表（数组，元素结构对齐 DefectFeedbackDataSchema。"
            "空列表表示用户跳过，与'无缺陷'语义不同）"
        ),
    )

    observations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description=(
            "实测观察列表（按需传）。本接口不存储到数据库，"
            "仅作为 schema 校验透传，避免与前端契约冲突。"
        ),
    )

    tuning_result: Optional[str] = Field(
        None,
        description=(
            "调机效果评价。前端枚举："
            "effective / ineffective / qualified / unqualified / pending / null。"
            "后端 service 层会做映射：effective → improved / ineffective → worse，"
            "其他值原样存储（与 TuningRecord.result choices 对齐）"
        ),
    )

    result_detail: Optional[str] = Field(
        None,
        max_length=500,
        description="结果详情文本（最多 500 字）",
    )


class TuningBatchDeleteSchema(BaseSchema):
    """批量删除调机记录（按 condition_id, 级联软删其下 parameter）"""

    ids: list[int] = Field(..., min_length=1, description="工艺条件 ID 列表")


__all__ = [
    "TuningRecordRequestSchema",
    "TuningBatchDeleteSchema",
]