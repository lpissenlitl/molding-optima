"""molding-optima 工艺条件 Schema 定义

字段命名严格匹配 process/models/condition.py。

对应 Model：ProcessCondition
"""
from typing import Optional

from pydantic import Field

from extensions.schemas import BaseSchema


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


class ProcessConditionAndParameterSchema(BaseSchema):
    """工艺条件及参数（一次性创建）"""

    # 用 forward reference 避免 condition.py ↔ parameter.py 循环 import
    condition: "ProcessConditionSchema" = Field(...)
    parameter: "ProcessParameterSchema" = Field(...)