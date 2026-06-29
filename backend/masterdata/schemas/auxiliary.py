"""
辅助设备相关 Schema 定义 - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from pydantic import Field

from extensions.schemas import BaseSchema, PaginationBaseSchema


class AuxiliaryEquipmentSchema(BaseSchema):
    """辅助装置"""
    
    equipment_name: str = Field(..., description="名称")
    equipment_type: str = Field(..., description="类型")
    specification: str = Field(None, description="规格")
    total_count: int = Field(None, description="数量")
    avaliable_count: int = Field(None, description="可用数量")
    remarks: str = Field(None, description="备注")


class AuxiliaryEquipmentListSchema(PaginationBaseSchema):
    """辅助装置列表"""
    
    equipment_name: str = Field(None, description="名称")
    equipment_type: str = Field(None, description="名称")