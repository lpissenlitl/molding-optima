from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema


# 工艺参数记录表--process_setting_item setting_items inject_para table_data item
class InjectParaTableDataSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))
    max = fields.String(required=False, allow_none=True)


# 工艺参数记录表--process_setting_item setting_items inject_para
class SettingItemsInjectParaSchema(BaseSchema):
    injection_stage = fields.Integer(required=False, allow_none=True)
    max_injection_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(InjectParaTableDataSchema, many=True)
    injection_time = fields.Float(required=False, allow_none=True)
    injection_delay_time = fields.Float(required=False, allow_none=True)
    cooling_time = fields.Float(required=False, allow_none=True)


# 工艺参数记录表--process_setting_item setting_items holding_para table_data item
class HoldingParaTableDataSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))
    max = fields.String(required=False, allow_none=True)


# 工艺参数记录表--process_setting_item setting_items holding_para
class SettingItemsHoldingParaSchema(BaseSchema):
    holding_stage = fields.Integer(required=False, allow_none=True)
    max_holding_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(HoldingParaTableDataSchema, many=True)


# 工艺参数记录表--process_setting_item setting_items VP_switch
class SettingItemsVPSwitchSchema(BaseSchema):
    VP_switch_mode = fields.String(required=False, allow_none=True)
    VP_switch_position = fields.Float(required=False, allow_none=True)
    VP_switch_time = fields.Float(required=False, allow_none=True)
    VP_switch_pressure = fields.Float(required=False, allow_none=True)
    VP_switch_velocity = fields.Float(required=False, allow_none=True)


# 工艺参数记录表--process_setting_item setting_items metering_para table_data item
class MeteringParaTableDataItemSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))
    max = fields.String(required=False, allow_none=True)


# 工艺参数记录表--process_setting_item setting_items metering_para decompressure_paras item
class MeteringParaDecompressureParasItemSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    pressure = fields.Float(required=False, allow_none=True)
    velocity = fields.Float(required=False, allow_none=True)
    time = fields.Float(required=False, allow_none=True)
    distance = fields.Float(required=False, allow_none=True)
    maxpre = fields.String(required=False, allow_none=True)
    maxvel = fields.String(required=False, allow_none=True)


# 工艺参数记录表--process_setting_item setting_items metering_para
class SettingItemsMeteringParaSchema(BaseSchema):
    metering_stage = fields.Integer(required=False, allow_none=True)
    max_metering_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(MeteringParaTableDataItemSchema, many=True)
    decompressure_mode_before_metering = fields.String(required=False, allow_none=True)
    decompressure_mode_after_metering = fields.String(required=False, allow_none=True)
    decompressure_paras = fields.Nested(MeteringParaDecompressureParasItemSchema, many=True)
    metering_delay_time = fields.Float(required=False, allow_none=True)
    metering_ending_position = fields.Float(required=False, allow_none=True)


# 工艺参数记录表--process_setting_item setting_items temp_para table_data item
class TempParaTableDataItemSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))


# 工艺参数记录表--process_setting_item setting_items temp_para
class SettingItemsTempParaSchema(BaseSchema):
    barrel_temperature_stage = fields.Integer(required=False, allow_none=True)
    max_barrel_temperature_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(TempParaTableDataItemSchema, many=True)


# 工艺参数记录表--table_data item
class TableDataItemSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))
    max = fields.String(required=False, allow_none=True)


# 工艺参数记录表--顶针前进
class ThimbleForwardParaSchema(BaseSchema):
    ejector_forward_stage = fields.Integer(required=False, allow_none=True)
    max_ejector_forward_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(TableDataItemSchema, many=True)


# 工艺参数记录表--顶针后退
class ThimbleBackParaSchema(BaseSchema):
    ejector_backward_stage = fields.Integer(required=False, allow_none=True)
    max_ejector_backward_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(TableDataItemSchema, many=True)


# 工艺参数记录表--顶针
class EjectorSettingSchema(BaseSchema):
    ejector_backward = fields.Nested(ThimbleBackParaSchema)
    ejector_forward = fields.Nested(ThimbleForwardParaSchema)

    ejector_mode = fields.String(required=False, allow_none=True)  # 顶针模式
    ejector_start_point = fields.Float(required=False, allow_none=True)  # 开始位置
    ejector_times = fields.Integer(required=False, allow_none=True)  # 顶出次数
    ejector_stroke = fields.Float(required=False, allow_none=True)  # 顶出行程
    ejector_on_opening = fields.String(required=False, allow_none=True)  # 开模中推顶
    ejector_delay = fields.Float(required=False, allow_none=True)  # 顶进延时
    ejector_keep = fields.Float(required=False, allow_none=True)  # 保持时间
    ejector_pause = fields.Float(required=False, allow_none=True)  # 中间时间
    ejector_blow_time = fields.Float(required=False, allow_none=True)  # 吹气时间
    ejector_force = fields.Float(required=False, allow_none=True)  # 推顶力
    set_torque = fields.Float(required=False, allow_none=True)  # 监视扭矩(设定值)


# 工艺参数记录表--开模
class MoldOpeningSchema(BaseSchema):
    mold_opening_stage = fields.Integer(required=False, allow_none=True)
    max_mold_opening_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(TableDataItemSchema, many=True)


# 工艺参数记录表--合模
class MoldClampingSchema(BaseSchema):
    mold_clamping_stage = fields.Integer(required=False, allow_none=True)
    max_mold_clamping_stage_option = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(TableDataItemSchema, many=True)


# 工艺参数记录表--开合模
class OpeningAndClampingMoldSettingSchema(BaseSchema):
    mold_opening = fields.Nested(MoldOpeningSchema)
    mold_clamping = fields.Nested(MoldClampingSchema)

    set_mold_clamping_force = fields.Integer(required=False, allow_none=True)  # 设定锁模力
    using_robot = fields.String(required=False, allow_none=True)  # 机械手使用状态 是/否
    using_tool = fields.String(required=False, allow_none=True)  # 夹具使用状态 是/否
    reset_method = fields.String(required=False, allow_none=True)  # 复位方式
    set_mold_protect_time = fields.Float(required=False, allow_none=True)  # 设定模保时间
    set_mold_protect_velocity = fields.Float(required=False, allow_none=True)  # 设定模保速度
    set_mold_protect_pressure = fields.Float(required=False, allow_none=True)  # 设定模保压力
    set_mold_protect_distance = fields.Float(required=False, allow_none=True)  # 设定模保位置
    opening_position_deviation = fields.Float(required=False, allow_none=True)  # 开模终止位置允许偏差
    turnable_method = fields.String(required=False, allow_none=True)  # 转盘方式
    turnable_velocity = fields.Float(required=False, allow_none=True)  # 转盘速度


# 工艺参数记录表--抽芯每一项
class CoreTableDataItemSchema(BaseSchema):
    core_switch_selection = fields.String(required=False, allow_none=True)  # 开关选择
    core_mold_clamping_method = fields.String(required=False, allow_none=True)  # 锁模入芯方式
    core_mold_opening_method = fields.String(required=False, allow_none=True)  # 开模出芯方式
    set_core_in_time = fields.Float(required=False, allow_none=True)  # 入芯时间设定值
    set_core_out_time = fields.Float(required=False, allow_none=True)  # 出芯时间设定值
    core_in_position = fields.Float(required=False, allow_none=True)  # 入芯位置
    core_out_position = fields.Float(required=False, allow_none=True)  # 出芯位置
    

# 工艺参数记录表--抽芯
class LooseCoreSchema(BaseSchema):
    core_movement_method = fields.String(required=False, allow_none=True)  # 运作状态:手动,连动
    table_data = fields.Nested(CoreTableDataItemSchema, many=True)


# 工艺参数记录表--process_setting_item setting_items
class ProcessSettingItemSettingItemsSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    inject_para = fields.Nested(SettingItemsInjectParaSchema)
    holding_para = fields.Nested(SettingItemsHoldingParaSchema)
    VP_switch = fields.Nested(SettingItemsVPSwitchSchema)
    metering_para = fields.Nested(SettingItemsMeteringParaSchema)
    temp_para = fields.Nested(SettingItemsTempParaSchema)
    ejector_setting = fields.Nested(EjectorSettingSchema)
    opening_and_clamping_mold_setting = fields.Nested(OpeningAndClampingMoldSettingSchema)
    loose_core = fields.Nested(LooseCoreSchema)


# 工艺参数记录表--process_setting_item
class ProcessSettingItemSchema(BaseSchema):
    active_trial_index = fields.String(required=False, allow_none=True)
    setting_items = fields.Nested(ProcessSettingItemSettingItemsSchema, many=True)
    