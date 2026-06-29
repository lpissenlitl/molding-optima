from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    ListField,
    DecimalField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
)


# 工艺参数记录表--process_setting_item setting_items inject_para table_data item
class InjectParaTableDataItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    unit = StringField(null=True)
    sections = ListField(null=True)
    max = StringField(null=True)


# 工艺参数记录表--process_setting_item setting_items inject_para
class SettingItemsInjectParaDoc(EmbeddedDocument):
    injection_stage = IntField(null=True)
    max_injection_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(InjectParaTableDataItemDoc)
    injection_time = DecimalField(null=True)
    injection_delay_time = DecimalField(null=True)
    cooling_time = DecimalField(null=True)


# 工艺参数记录表--process_setting_item setting_items holding_para table_data item
class HoldingParaTableDataItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    unit = StringField(null=True)
    sections = ListField(null=True)
    max = StringField(null=True)


# 工艺参数记录表--process_setting_item setting_items holding_para
class SettingItemsHoldingParaDoc(EmbeddedDocument):
    holding_stage = IntField(null=True)
    max_holding_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(HoldingParaTableDataItemDoc)


# 工艺参数记录表--process_setting_item setting_items VP_switch
class SettingItemsVPSwitchDoc(EmbeddedDocument):
    VP_switch_mode = StringField(null=True)
    VP_switch_position = DecimalField(null=True)
    VP_switch_time = DecimalField(null=True)
    VP_switch_pressure = DecimalField(null=True)
    VP_switch_velocity = DecimalField(null=True)


# 工艺参数记录表--process_setting_item setting_items metering_para table_data item
class MeteringParaTableDataItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    unit = StringField(null=True)
    sections = ListField(null=True)
    max = StringField(null=True)


# 工艺参数记录表--process_setting_item setting_items metering_para decompressure_paras item
class MeteringParaDecompressureParasItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    pressure = DecimalField(null=True)
    velocity = DecimalField(null=True)
    time = DecimalField(null=True)
    distance = DecimalField(null=True)
    maxpre = StringField(null=True)
    maxvel = StringField(null=True)


# 工艺参数记录表--process_setting_item setting_items metering_para
class SettingItemsMeteringParaDoc(EmbeddedDocument):
    metering_stage = IntField(null=True)
    max_metering_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(MeteringParaTableDataItemDoc)
    decompressure_mode_before_metering = StringField(null=True)
    decompressure_mode_after_metering = StringField(null=True)
    decompressure_paras = EmbeddedDocumentListField(MeteringParaDecompressureParasItemDoc)
    metering_delay_time = DecimalField(null=True)
    metering_ending_position = DecimalField(null=True)


# 工艺参数记录表--process_setting_item setting_items temp_para table_data item
class TempParaTableDataItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    unit = StringField(null=True)
    sections = ListField(null=True)


# 工艺参数记录表--process_setting_item setting_items temp_para
class SettingItemsTempParaDoc(EmbeddedDocument):
    barrel_temperature_stage = IntField(null=True)
    max_barrel_temperature_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(TempParaTableDataItemDoc)


# 工艺参数记录表--table_data item
class TableDataItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    unit = StringField(null=True)
    sections = ListField(null=True)
    max = StringField(null=True)


# 工艺参数记录表--顶针前进
class ThimbleForwardParaDoc(EmbeddedDocument):
    ejector_forward_stage = IntField(null=True)
    max_ejector_forward_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(TableDataItemDoc)


# 工艺参数记录表--顶针后退
class ThimbleBackParaDoc(EmbeddedDocument):
    ejector_backward_stage = IntField(null=True)
    max_ejector_backward_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(TableDataItemDoc)


class EjectorSettingDoc(EmbeddedDocument):
    ejector_forward = EmbeddedDocumentField(ThimbleForwardParaDoc)
    ejector_backward = EmbeddedDocumentField(ThimbleBackParaDoc)

    ejector_mode = StringField(null=True)  # 顶针模式
    ejector_start_point = DecimalField(null=True)  # 开始位置
    ejector_times = IntField(null=True)  # 顶出次数
    ejector_stroke = DecimalField(null=True)  # 顶出行程
    ejector_on_opening = StringField(null=True)  # 开模中推顶
    ejector_delay = DecimalField(null=True)  # 顶进延时
    ejector_keep = DecimalField(null=True)  # 保持时间
    ejector_pause = DecimalField(null=True)  # 中间时间
    ejector_blow_time = DecimalField(null=True)  # 吹气时间
    ejector_force = DecimalField(null=True)  # 推顶力
    set_torque = DecimalField(null=True)  # 监视扭矩(设定值)


# 工艺参数记录表--开模
class MoldOpeningDoc(EmbeddedDocument):
    mold_opening_stage = IntField(null=True)
    max_mold_opening_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(TableDataItemDoc)


# 工艺参数记录表--合模
class MoldClampingDoc(EmbeddedDocument):
    mold_clamping_stage = IntField(null=True)
    max_mold_clamping_stage_option = IntField(null=True)
    table_data = EmbeddedDocumentListField(TableDataItemDoc)


# 工艺参数记录表--开合模
class OpeningAndClampingMoldSettingDoc(EmbeddedDocument):
    mold_opening = EmbeddedDocumentField(MoldOpeningDoc)
    mold_clamping = EmbeddedDocumentField(MoldClampingDoc)

    set_mold_clamping_force = IntField(null=True)  # 设定锁模力
    using_robot = StringField(null=True)  # 机械手使用状态
    using_tool = StringField(null=True)  # 夹具使用状态
    reset_method = StringField(null=True)  # 复位方式
    set_mold_protect_time = DecimalField(null=True)  # 设定模保时间
    set_mold_protect_velocity = DecimalField(null=True)  # 设定模保速度
    set_mold_protect_pressure = DecimalField(null=True)  # 设定模保压力
    set_mold_protect_distance = DecimalField(null=True)  # 设定模保位置
    opening_position_deviation = DecimalField(null=True)  # 开模终止位置允许偏差

    turnable_method = StringField(null=True)  # 转盘方式
    turnable_velocity = DecimalField(null=True)  # 转盘速度


# 工艺参数记录表--抽芯每一项
class CoreItemDoc(EmbeddedDocument):
    core_switch_selection = StringField(null=True)  # 开关选择
    core_mold_clamping_method = StringField(null=True)  # 锁模入芯方式
    core_mold_opening_method = StringField(null=True)  # 开模出芯方式
    set_core_in_time = DecimalField(null=True)  # 入芯时间设定值
    set_core_out_time = DecimalField(null=True)  # 出芯时间设定值
    core_in_position = DecimalField(null=True)  # 入芯位置
    core_out_position = DecimalField(null=True)  # 出芯位置
    

# 工艺参数记录表--抽芯
class LooseCoreDoc(EmbeddedDocument):
    core_movement_method = StringField(null=True)  # 运作状态:手动,连动
    table_data = EmbeddedDocumentListField(CoreItemDoc)


# 工艺参数记录表--process_setting_item setting_items
class ProcessSettingItemDoc(EmbeddedDocument):
    title = StringField(null=True)
    name = StringField(null=True)
    inject_para = EmbeddedDocumentField(SettingItemsInjectParaDoc)
    holding_para = EmbeddedDocumentField(SettingItemsHoldingParaDoc)
    VP_switch = EmbeddedDocumentField(SettingItemsVPSwitchDoc)
    metering_para = EmbeddedDocumentField(SettingItemsMeteringParaDoc)
    temp_para = EmbeddedDocumentField(SettingItemsTempParaDoc)
    ejector_setting = EmbeddedDocumentField(EjectorSettingDoc)
    opening_and_clamping_mold_setting = EmbeddedDocumentField(OpeningAndClampingMoldSettingDoc)
    loose_core = EmbeddedDocumentField(LooseCoreDoc)
    

# 工艺参数记录表--process_setting_item 计划多射台情况
class ProcessSettingDoc(EmbeddedDocument):
    active_trial_index = StringField(null=True)
    setting_items = EmbeddedDocumentListField(ProcessSettingItemDoc)
