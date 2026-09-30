"""
调参记录 Schema

对应接口：
- POST /api/processes/tuning/record/

业务语义（与前端 processTuningRecord 对齐）：
- 用户在 OptimizationCreate 页填写完反馈 + 实测结果后点"保存当前工艺"
- 不创建新 ProcessParameter（不调算法），仅保存/更新 TuningRecord

入参字段来源：
- parameter_id：必填（前端从 activeRound.parameter_id 取）
- defect_feedbacks：缺陷反馈列表（结构对齐 DefectFeedbackDataSchema）
- observations：实测观察（过程观测数据；本接口不存储，仅 schema 校验透传）
- tuning_result：调机效果评价（前端枚举 effective/ineffective/qualified/unqualified/pending）
- result_detail：结果详情文本（≤ 500 字，与模型 result_detail 对齐）
"""
from typing import Optional, List, Dict, Any

from pydantic import Field

from extensions.schemas import BaseSchema


class TuningRecordRequestSchema(BaseSchema):
    """保存当前试模结果请求 Schema

    与前端 api/index.ts 进程的 processTuningRecord 参数对齐。
    """

    parameter_id: int = Field(..., description="工艺参数 ID（必填）")

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


__all__ = ["TuningRecordRequestSchema"]