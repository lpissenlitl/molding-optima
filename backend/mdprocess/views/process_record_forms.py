from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema
from mdprocess.views.standard_process_forms import ProcessSettingItemSettingItemsSchema


# 工艺参数录入 前置条件--process_record precondition
class ProcessRecordPreconditionSchema(BaseSchema):
    mold_id = fields.Integer(required=False, allow_none=True)
    data_sources = fields.String(required=False, allow_none=True)  # 数据来源
    mold_trials_no = fields.String(required=False, allow_none=True)  # 试模次数
    mold_no = fields.String(required=False, allow_none=True)
    cavity_num = fields.String(required=False, allow_none=True)
    inject_cycle_require = fields.Float(required=False, allow_none=True)
    subrule_no = fields.String(required=False, allow_none=True)
    runner_length = fields.Float(required=False, allow_none=True)
    runner_weight = fields.Float(required=False, allow_none=True)
    gate_type = fields.String(required=False, allow_none=True)
    gate_num = fields.Integer(required=False, allow_none=True)
    gate_shape = fields.String(required=False, allow_none=True)  # 浇口形状
    gate_area = fields.Float(required=False, allow_none=True)  # 浇口横截面积
    gate_radius = fields.Float(required=False, allow_none=True)  # 浇口半径(圆)
    gate_length = fields.Float(required=False, allow_none=True)  # 浇口长(矩形)
    gate_width = fields.Float(required=False, allow_none=True)  # 浇口宽(矩形)

    inject_part = fields.String(required=False, allow_none=True)
    product_type = fields.String(required=False, allow_none=True)
    product_total_weight = fields.Float(required=False, allow_none=True)

    product_no = fields.String(required=False, allow_none=True)
    product_name = fields.String(required=False, allow_none=True)
    product_ave_thickness = fields.Float(required=False, allow_none=True)
    product_max_thickness = fields.Float(required=False, allow_none=True)
    product_max_length = fields.Float(required=False, allow_none=True)

    machine_id = fields.Integer(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    machine_serial_no = fields.String(required=False, allow_none=True)

    polymer_id = fields.Integer(required=False, allow_none=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    recommend_melt_temperature = fields.Float(required=False, allow_none=True)

    injection_stage = fields.Integer(required=False, allow_none=True)  # 注射段数
    holding_stage = fields.Integer(required=False, allow_none=True)  # 计量段数
    VP_switch_mode = fields.String(required=False, allow_none=True)  # VP切换模式
    metering_stage = fields.Integer(required=False, allow_none=True)  # 计量段数
    decompressure_mode_before_metering = fields.String(required=False, allow_none=True)  # 储前松退模式
    decompressure_mode_after_metering = fields.String(required=False, allow_none=True)  # 储后松退模式
    barrel_temperature_stage = fields.Integer(required=False, allow_none=True)  # 料筒温度段数

    runner_type = fields.String(required=False, allow_none=True)
    hot_runner_num = fields.Integer(required=False, allow_none=True)

    valve_num = fields.Integer(required=False, allow_none=True)


# 工艺参数记录
class ProcessRecordSchema(BaseSchema):
    process_index_id = fields.Integer(required=False, allow_none=True)
    precondition = fields.Nested(ProcessRecordPreconditionSchema)
    process_detail = fields.Nested(ProcessSettingItemSettingItemsSchema)