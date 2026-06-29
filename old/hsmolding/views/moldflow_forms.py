from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema


class TableDataSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))

    
class ProcessMonitorSchema(BaseSchema):
    injection_time = fields.Float(required=False, allow_none=True)
    cooling_time = fields.Float(required=False, allow_none=True)  # 冷却时间
    holding_time = fields.Float(required=False, allow_none=True)
    mold_opening_time = fields.Float(required=False, allow_none=True)
    mold_clamping_time = fields.Float(required=False, allow_none=True)
    # open_close_time = fields.Float(required=False, allow_none=True)

    # mold_open_clamp_time = fields.Float(required=False, allow_none=True)  # 开合模时间
    cycle_time = fields.Float(required=False, allow_none=True)  #周期时间
    product_projected_area = fields.Float(required=False, allow_none=True)
    single_volume = fields.Float(required=False, allow_none=True)

    melt_temp = fields.Float(required=False, allow_none=True)
    cavity_temp = fields.Float(required=False, allow_none=True)
    core_temp = fields.Float(required=False, allow_none=True)

    injection_pressure = fields.Float(required=False, allow_none=True)
    max_clamping_force = fields.Float(required=False, allow_none=True)

    polymer_trademark = fields.String(required=False, allow_none=True)  # 材料牌号
    thickness = fields.Float(required=False, allow_none=True)  # 壁厚
    product_weight = fields.Float(required=False, allow_none=True)  # 克重
    gate_temperature = fields.Float(required=False, allow_none=True)  # 浇口温度
    pentroof_temperature = fields.Float(required=False, allow_none=True)  # 斜顶温度
    slug_temperature = fields.Float(required=False, allow_none=True)  # 弹块滑块温度
    lifters_temperature = fields.Float(required=False, allow_none=True)  # 内抽温度

    injection = fields.Float(required=False, allow_none=True)  # 注塑机压力
    hot_runner_pressure = fields.Float(required=False, allow_none=True)  # 热流道压力
    gate_pressure = fields.Float(required=False, allow_none=True)  # 浇口压力

    inject_para = fields.Nested(TableDataSchema, many=True)
    holding_para = fields.Nested(TableDataSchema, many=True)
    

class MoldFlowSchema(BaseSchema):
    project_id = fields.Integer()  # 模号ID
    mold_no = fields.String()  # 模号
    doc_link = fields.String(required=False, allow_none=True)  # txt文件
    pdf_link = fields.String(required=False, allow_none=True)  # pdf文件
    ppt_link = fields.String(required=False, allow_none=True)  # ppt文件
    monitor_item = fields.Nested(ProcessMonitorSchema)
