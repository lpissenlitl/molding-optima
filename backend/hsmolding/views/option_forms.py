from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema, CNDatetimeField


class OptionSchema(BaseSchema):
    company_id = fields.Integer()

    db_table = fields.String(required=False, allow_none=True)
    form_input = fields.String(required=False, allow_none=True)  # 某些字段的推荐

    abbreviation = fields.String(required=False, allow_none=True)  # 材料缩写
    data_source = fields.String(required=False, allow_none=True)  # 注塑机数据来源
    trademark = fields.String(required=False, allow_none=True) # 牌号
    manufacturer = fields.String(required=False, allow_none=True) # 生产厂商
    serial_no = fields.String(required=False, allow_none=True) # 设备编码
    asset_no = fields.String(required=False, allow_none=True) # 资产编号

    interface_view = fields.String(required=False, allow_none=True)  # 自定义下拉
    interface_select = fields.String(required=False, allow_none=True)  # 自定义下拉

    label = fields.String(required=False, allow_none=True)
    value = fields.String(required=False, allow_none=True)
    key = fields.Integer(required=False, allow_none=True)
    view_desc = fields.String(required=False, allow_none=True)
    select_desc = fields.String(required=False, allow_none=True)

    parent_id = fields.Integer(required=False, allow_none=True)
    project_id = fields.Integer(required=False, allow_none=True)

    machine_id_list = fields.List(fields.Integer(required=False, allow_none=True))
    process_id = fields.Integer(required=False, allow_none=True)
    machine_type = fields.String(required=False, allow_none=True)
    power_method = fields.String(required=False, allow_none=True)
    propulsion_axis = fields.String(required=False, allow_none=True)

    product_small_type = fields.String(required=False, allow_none=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    

class OptionsSchema(BaseSchema):
    options = fields.Nested(OptionSchema, many=True)
