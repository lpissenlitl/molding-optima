from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema, PaginationBaseSchema, CNDatetimeField


class AuxiliaryListSchema(PaginationBaseSchema):
    machine_id = fields.Integer()
    auxiliary_type = fields.String()
    manufacture = fields.String()
    serial_num = fields.String()


class AuxiliaryMachineSchema(BaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    machine_id = fields.Integer(required=False, allow_none=True)
    auxiliary_type = fields.String(required=False, allow_none=True)
    auxiliary_trademark = fields.String(required=False, allow_none=True)
    manufacture = fields.String(required=False, allow_none=True)
    serial_num = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    communication_interface = fields.Integer(required=False, allow_none=True)
    # 修改时用到的字段
    id = fields.Integer(required=False, allow_none=True)
    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer(default=0)


class HandleMultipleAuxiliarySchema(BaseSchema):
    auxiliary_id_list = fields.List(fields.Integer())
    flag = fields.String(default="default") # 标记处理方式
