"""molding-optima 工艺条件 Schema 定义

字段命名严格匹配 process/models/condition.py。

对应 Model：ProcessCondition
"""
from datetime import date
from typing import Optional

from pydantic import Field

from extensions.schemas import BaseSchema, PaginationBaseSchema


class ProcessConditionSchema(BaseSchema):
    """工艺条件"""

    condition_no: Optional[str] = Field(None, description="工艺条件编号")
    status: Optional[str] = Field(None, description="状态")
    origin_type: Optional[str] = Field(None, description="工艺起源类型")
    process_context: Optional[dict] = Field(None, description="工艺上下文（前端输入，业务覆盖值）")
    process_context_snapshot: Optional[dict] = Field(None, description="工艺条件快照（后端自动生成）")
    mold_id: Optional[int] = Field(None, description="模具 ID")
    shot_index: Optional[int] = Field(None, description="注射次数")
    injection_machine_id: Optional[int] = Field(None, description="注塑机 ID")
    injection_index: Optional[int] = Field(None, description="注射单元")
    polymer_id: Optional[int] = Field(None, description="材料 ID")


class ProcessConditionListSchema(PaginationBaseSchema):
    """工艺条件列表查询条件（按 condition 字段过滤, 取最新 parameter）"""

    status: Optional[str] = Field(None, description="状态")
    origin_type: Optional[str] = Field(None, description="工艺起源类型")
    mold_id: Optional[int] = Field(None, description="模具 ID")
    injection_machine_id: Optional[int] = Field(None, description="注塑机 ID")
    polymer_id: Optional[int] = Field(None, description="材料 ID")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class BatchDeleteConditionSchema(BaseSchema):
    """批量删除工艺条件

    业务语义: 传入 condition_id 列表, 级联软删其下所有 parameter。
    实际 view 现阶段使用通用的 BatchIdsSchema, 本 schema 作为业务契约预留。
    """

    ids: list[int] = Field(..., min_length=1, description="工艺条件 ID 列表")
