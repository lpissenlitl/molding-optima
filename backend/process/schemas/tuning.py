"""
调机反馈 Schema

对应 URL 段: processes/parameters/<pid>/tuning-feedback/  业务对象 ID: parameter_id

tuning-feedback 子资源:
- 归属: parameters/<pid>/tuning-feedback/ (parameter 是 tuning 的真正父资源)

业务语义:
- parameter_id 从 URL 限定, 不从 body 传入 (一意唯一)
- 调机反馈隶属于某个具体 parameter (多轮迭代场景)
- 缺陷反馈/调整记录随 parameter 归属

独立 tuning service 契约:
- TuningRecordRequestSchema    人工调机反馈 (写 TuningRecord)
- TuningBatchDeleteSchema      批量删除 (仍按 condition_id, 与 records/batch-delete 职责重复, 保留备用)
"""
from typing import List, Dict, Any, Optional

from pydantic import Field

from extensions.schemas import BaseSchema
from .parameter import ProcessParameterSchema


class TuningRecordRequestSchema(BaseSchema):
    """人工调机反馈 (写 TuningRecord)

    业务语义:
    - parameter_id 从 URL 限定 (POST /conditions/<id>/parameters/<pid>/tuning-feedback/)
    - 反馈字段: defect_feedbacks / observations / tuning_result / result_detail

    tuning_result：首轮 qualified/unqualified，第 2 轮起 qualified + effective/unchanged/ineffective

    合格态（qualified）语义：
    - 产品没有缺陷 ⇒ 缺陷信息一律丢弃（即使传了也不入库）
    - 仍照常落库（result=qualified），提交通道保持可用
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
            "试模效果评价（对【该轮工艺参数】的整体评价，即该参数的试模标签）。"
            "前端枚举：qualified（合格）/ unqualified（不合格）/ effective（改善）/ "
            "unchanged（无变化）/ ineffective（变差）/ null（未评价）；"
            "首轮只提供 qualified/unqualified；第 2 轮起提供 qualified + 后三档"
            "后端 service 层会做映射：effective → improved / unchanged → unchanged / "
            "ineffective → worse / qualified → qualified / unqualified → unqualified"
        ),
    )

    result_detail: Optional[str] = Field(
        None,
        max_length=500,
        description="结果详情文本（最多 500 字）",
    )

    parameter: Optional[ProcessParameterSchema] = Field(
        None,
        description=(
            "本轮实际使用的工艺参数（flat，字段对齐 ProcessParameterSchema；"
            "前端嵌套 form → flat 的翻译由 parameterToFlat 负责）。"
            "「保存当前工艺」时一并提交：后端把它写回 URL 指定的 parameter 行。"
            "部分更新——只写传了的字段（未传保持原值）；"
            "parent_param / seq_idx 等版本关系字段受锁保护，不会被改动。"
            "不传则只写评价、不动参数。"
        ),
    )


class TuningBatchDeleteSchema(BaseSchema):
    """批量删除调机记录（按 condition_id, 级联软删其下 parameter）"""

    ids: list[int] = Field(..., min_length=1, description="工艺条件 ID 列表")


__all__ = [
    "TuningRecordRequestSchema",
    "TuningBatchDeleteSchema",
]