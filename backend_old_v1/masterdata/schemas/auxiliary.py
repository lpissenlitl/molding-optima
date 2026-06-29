from extensions.schemas import BaseSchema, PaginationBaseSchema
from marshmallow import fields


class AuxiliaryEquipmentSchema(BaseSchema):
    """辅助装置"""
    equipment_name = fields.String(required=True, metadata={"description": "名称"})
    equipment_type = fields.String(required=True, metadata={"description": "类型"})
    specification = fields.String(allow_none=True, metadata={"description": "规格"})
    total_count = fields.Integer(allow_none=True, metadata={"description": "数量"})
    avaliable_count = fields.Integer(allow_none=True, metadata={"description": "可用数量"})
    remarks = fields.String(allow_none=True, metadata={"description": "备注"})


class AuxiliaryEquipmentListSchema(PaginationBaseSchema):
    """辅助装置列表"""
    equipment_name = fields.String(allow_none=True, metadata={"description": "名称"})
    equipment_type = fields.String(allow_none=True, metadata={"description": "名称"})