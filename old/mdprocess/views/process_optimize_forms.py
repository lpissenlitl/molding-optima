from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema
from mdprocess.views.standard_process_forms import ProcessSettingItemSettingItemsSchema
from mdprocess.views.rule_forms import RuleMethodSchema


# 工艺参数优化记录 前置条件--process_optimization precondition
class ProcessOptimizationPreconditionSchema(BaseSchema):

    mold_id = fields.Integer(required=False, allow_none=True)
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

    data_sources = fields.String(required=False, allow_none=True)  # 数据来源
    mold_trials_no = fields.String(required=False, allow_none=True)  # 试模次数

    runner_type = fields.String(required=False, allow_none=True)
    hot_runner_num = fields.Integer(required=False, allow_none=True)
    valve_num = fields.Integer(required=False, allow_none=True)
    meta = {"strict": False}


# 辅机（热流道）设定值--auxiliary_setting hot_runner
class AuxiliarySettingHotRunnerSchema(BaseSchema):
    valve_num = fields.Integer(required=False, allow_none=True)
    sequential_ctrl_time = fields.List(fields.Float(required=False, allow_none=True))


# 辅机（模温机）设定值--auxiliary_setting mold_temp
class AuxiliarySettingMoldTempSchema(BaseSchema):
    mold_temp_num = fields.Integer(required=False, allow_none=True)
    setting_temp = fields.Float(required=False, allow_none=True)
    mold_temp_list = fields.List(fields.Float(required=False, allow_none=True))
    meta = {"strict": False}


# 辅机设定值--auxiliary_setting
class AuxiliarySettingDetailSchema(BaseSchema):
    hot_runner = fields.Nested(AuxiliarySettingHotRunnerSchema)
    mold_temp = fields.Nested(AuxiliarySettingMoldTempSchema)
    hot_runner_temperatures = fields.List(fields.Float(required=False, allow_none=True))


# 工艺参数优化记录--process_optimization record defect_info item
class RecordDefectInfoItemSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)  # 缺陷的中文名称
    desc = fields.String(required=False, allow_none=True)  # 缺陷的大写字母
    level = fields.String(required=False, allow_none=True)
    position = fields.String(required=False, allow_none=True)
    feedback = fields.String(required=False, allow_none=True)
    count = fields.Integer(required=False, allow_none=True)
    remark = fields.String(required=False, allow_none=True)


# 工艺参数优化记录--process_optimization record defect_info
# class RecordDefectInfoSchema(BaseSchema):    
#     short_shot = fields.Nested(RecordDefectInfoItemSchema)
#     flash = fields.Nested(RecordDefectInfoItemSchema)
#     shrinkage = fields.Nested(RecordDefectInfoItemSchema)
#     weld_line = fields.Nested(RecordDefectInfoItemSchema)
#     aberration = fields.Nested(RecordDefectInfoItemSchema)
#     air_trap = fields.Nested(RecordDefectInfoItemSchema)
#     gas_veins = fields.Nested(RecordDefectInfoItemSchema)
#     material_flower = fields.Nested(RecordDefectInfoItemSchema)
#     hard_demolding = fields.Nested(RecordDefectInfoItemSchema)
#     burn = fields.Nested(RecordDefectInfoItemSchema)
#     water_ripple = fields.Nested(RecordDefectInfoItemSchema)
#     top_white = fields.Nested(RecordDefectInfoItemSchema)
#     warping = fields.Nested(RecordDefectInfoItemSchema)
#     oversize = fields.Nested(RecordDefectInfoItemSchema)
#     undersize = fields.Nested(RecordDefectInfoItemSchema)
#     gatemark = fields.Nested(RecordDefectInfoItemSchema)
#     shading = fields.Nested(RecordDefectInfoItemSchema)


# 规则调用记录--process_optimization record rules_selected
class RecordRulesParaSchema(BaseSchema):
    rule_id = fields.Integer(required=False, allow_none=True)
    rule_description = fields.String(required=False, allow_none=True)
    rule_activation = fields.Float(required=False, allow_none=True)
    rule_result_key = fields.String(required=False, allow_none=True)
    rule_result_value = fields.Float(required=False, allow_none=True)


# 特殊规则调用记录--process_optimization record adjust_rules
class RecordRulesWordSchema(BaseSchema):
    rule_id = fields.Integer(required=False, allow_none=True)
    rule_description = fields.String(required=False, allow_none=True)
    rule_defect = fields.String(required=False, allow_none=True)
    rule_output = fields.String(required=False, allow_none=True)


# 优化记录--process_optimization record optimize_info
class RecordOptimizeInfoSchema(BaseSchema):
    defect_num = fields.Integer(required=False, allow_none=True)
    defect_feedback = fields.String(required=False, allow_none=True)
    defect_name = fields.String(required=False, allow_none=True)
    defect_position = fields.String(required=False, allow_none=True)
    defect_level = fields.String(required=False, allow_none=True)
    adjust_name = fields.String(required=False, allow_none=True)
    adjust_direction = fields.Float(required=False, allow_none=True)
    adjust_value = fields.Float(required=False, allow_none=True)
    rule_in_use = fields.String(required=False, allow_none=True)
    rule_valid = fields.Integer(required=False, allow_none=True)
    rule_library_in_use = fields.String(required=False, allow_none=True)
    subrule_no = fields.String(required=False, allow_none=True)

    candidate_rules = fields.Nested(RecordRulesParaSchema, many=True)
    adjust_rules = fields.Nested(RecordRulesWordSchema, many=True)
    chosen_rules = fields.Nested(RuleMethodSchema, many=True)  # 用户选择执行的子规则


# 反馈信息--process_optimization detail
class RcordFeedbackDetailSchema(BaseSchema):
    actual_product_weight = fields.Float(required=False, allow_none=True)  # 实际制品重量,与缺陷反馈同时录入
    defect_info = fields.Nested(RecordDefectInfoItemSchema, many=True)
    optimize_export = fields.Nested(RecordOptimizeInfoSchema)


# 工艺参数记录表--process_setting_item
class ProcessOptimizationProcessDetailSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    
    process_detail = fields.Nested(ProcessSettingItemSettingItemsSchema)
    auxiliary_detail = fields.Nested(AuxiliarySettingDetailSchema)
    feedback_detail = fields.Nested(RcordFeedbackDetailSchema)


# 工艺参数优化记录
class ProcessOptimizationSchema(BaseSchema):
    process_index_id = fields.Integer(required=False, allow_none=True)
    precondition = fields.Nested(ProcessOptimizationPreconditionSchema)
    optimize_list = fields.Nested(ProcessOptimizationProcessDetailSchema, many=True)
    flaw_picture_url = fields.String(required=False, allow_none=True)


# 优化时缺陷信息--defect_info item
class OptimizeDefectInfoItemSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)  # 缺陷的中文名称
    desc = fields.String(required=False, allow_none=True)  # 缺陷的大写字母
    level = fields.String(required=False, allow_none=True)
    position = fields.String(required=False, allow_none=True)
    feedback = fields.String(required=False, allow_none=True)
    count = fields.Integer(required=False, allow_none=True)
    remark = fields.String(required=False, allow_none=True)


# 工艺参数优化传递参数
class OptimizeProcessSchema(BaseSchema):

    # 注射
    injection_stage = fields.Integer(required=False, allow_none=True)

    IP0 = fields.Float(required=False, allow_none=True)
    IV0 = fields.Float(required=False, allow_none=True)
    IL0 = fields.Float(required=False, allow_none=True)
    IP1 = fields.Float(required=False, allow_none=True)
    IV1 = fields.Float(required=False, allow_none=True)
    IL1 = fields.Float(required=False, allow_none=True)
    IP2 = fields.Float(required=False, allow_none=True)
    IV2 = fields.Float(required=False, allow_none=True)
    IL2 = fields.Float(required=False, allow_none=True)
    IP3 = fields.Float(required=False, allow_none=True)
    IV3 = fields.Float(required=False, allow_none=True)
    IL3 = fields.Float(required=False, allow_none=True)
    IP4 = fields.Float(required=False, allow_none=True)
    IV4 = fields.Float(required=False, allow_none=True)
    IL4 = fields.Float(required=False, allow_none=True)
    IP5 = fields.Float(required=False, allow_none=True)
    IV5 = fields.Float(required=False, allow_none=True)
    IL5 = fields.Float(required=False, allow_none=True)

    IT = fields.Float(required=False, allow_none=True)
    ID = fields.Float(required=False, allow_none=True)
    CT = fields.Float(required=False, allow_none=True)

    # 保压
    holding_stage = fields.Integer(required=False, allow_none=True)

    INIT_PP = fields.Float(required=False, allow_none=True)
    INIT_PV = fields.Float(required=False, allow_none=True)
    INIT_PT = fields.Float(required=False, allow_none=True)

    PP0 = fields.Float(required=False, allow_none=True)
    PV0 = fields.Float(required=False, allow_none=True)
    PT0 = fields.Float(required=False, allow_none=True)
    PP1 = fields.Float(required=False, allow_none=True)
    PV1 = fields.Float(required=False, allow_none=True)
    PT1 = fields.Float(required=False, allow_none=True)
    PP2 = fields.Float(required=False, allow_none=True)
    PV2 = fields.Float(required=False, allow_none=True)
    PT2 = fields.Float(required=False, allow_none=True)
    PP3 = fields.Float(required=False, allow_none=True)
    PV3 = fields.Float(required=False, allow_none=True)
    PT3 = fields.Float(required=False, allow_none=True)
    PP4 = fields.Float(required=False, allow_none=True)
    PV4 = fields.Float(required=False, allow_none=True)
    PT4 = fields.Float(required=False, allow_none=True)

    # VP切换
    VPTM = fields.String(required=False, allow_none=True)
    VPTT = fields.Float(required=False, allow_none=True)
    VPTL = fields.Float(required=False, allow_none=True)
    VPTP = fields.Float(required=False, allow_none=True)
    VPTV = fields.Float(required=False, allow_none=True)

    # 计量
    metering_stage = fields.Integer(required=False, allow_none=True)

    MP0 = fields.Float(required=False, allow_none=True)
    MSR0 = fields.Float(required=False, allow_none=True)
    MBP0 = fields.Float(required=False, allow_none=True)
    ML0 = fields.Float(required=False, allow_none=True) 
    MP1 = fields.Float(required=False, allow_none=True)
    MSR1 = fields.Float(required=False, allow_none=True)
    MBP1 = fields.Float(required=False, allow_none=True)
    ML1 = fields.Float(required=False, allow_none=True)
    MP2 = fields.Float(required=False, allow_none=True)
    MSR2 = fields.Float(required=False, allow_none=True)
    MBP2 = fields.Float(required=False, allow_none=True)
    ML2 = fields.Float(required=False, allow_none=True)
    MP3 = fields.Float(required=False, allow_none=True)
    MSR3 = fields.Float(required=False, allow_none=True)
    MBP3 = fields.Float(required=False, allow_none=True)
    ML3 = fields.Float(required=False, allow_none=True)

    DMBM = fields.String(required=False, allow_none=True)
    DMAM = fields.String(required=False, allow_none=True)

    DPBM = fields.Float(required=False, allow_none=True)
    DVBM = fields.Float(required=False, allow_none=True)
    DDBM = fields.Float(required=False, allow_none=True)
    DTBM = fields.Float(required=False, allow_none=True)

    DPAM = fields.Float(required=False, allow_none=True)
    DVAM = fields.Float(required=False, allow_none=True)
    DDAM = fields.Float(required=False, allow_none=True)
    DTAM = fields.Float(required=False, allow_none=True)

    MD = fields.Float(required=False, allow_none=True)
    MEL = fields.Float(required=False, allow_none=True)

    # 料筒温度
    barrel_temperature_stage = fields.Integer(required=False, allow_none=True)

    NT = fields.Float(required=False, allow_none=True)
    BT1 = fields.Float(required=False, allow_none=True)
    BT2 = fields.Float(required=False, allow_none=True)
    BT3 = fields.Float(required=False, allow_none=True)
    BT4 = fields.Float(required=False, allow_none=True)
    BT5 = fields.Float(required=False, allow_none=True)
    BT6 = fields.Float(required=False, allow_none=True)
    BT7 = fields.Float(required=False, allow_none=True)
    BT8 = fields.Float(required=False, allow_none=True)
    BT9 = fields.Float(required=False, allow_none=True)

    # 热流道时序控制时间
    SCVN = fields.Integer(required=False, allow_none=True)
    SCT0 = fields.Float(required=False, allow_none=True)
    SCT1 = fields.Float(required=False, allow_none=True)
    SCT2 = fields.Float(required=False, allow_none=True)
    SCT3 = fields.Float(required=False, allow_none=True)
    SCT4 = fields.Float(required=False, allow_none=True)
    SCT5 = fields.Float(required=False, allow_none=True)
    SCT6 = fields.Float(required=False, allow_none=True)
    SCT7 = fields.Float(required=False, allow_none=True)
    SCT8 = fields.Float(required=False, allow_none=True)
    SCT9 = fields.Float(required=False, allow_none=True)

    # 模温设定值
    MT = fields.Float(required=False, allow_none=True)
    MTN = fields.Integer(required=False, allow_none=True)
    MT0 = fields.Float(required=False, allow_none=True)
    MT1 = fields.Float(required=False, allow_none=True)
    MT2 = fields.Float(required=False, allow_none=True)
    MT3 = fields.Float(required=False, allow_none=True)
    MT4 = fields.Float(required=False, allow_none=True)
    MT5 = fields.Float(required=False, allow_none=True)
    MT6 = fields.Float(required=False, allow_none=True)
    MT7 = fields.Float(required=False, allow_none=True)
    MT8 = fields.Float(required=False, allow_none=True)
    MT9 = fields.Float(required=False, allow_none=True)
    MT10 = fields.Float(required=False, allow_none=True)
    MT11 = fields.Float(required=False, allow_none=True)
    MT12 = fields.Float(required=False, allow_none=True)
    MT13 = fields.Float(required=False, allow_none=True)
    MT14 = fields.Float(required=False, allow_none=True)
    MT15 = fields.Float(required=False, allow_none=True)
    MT16 = fields.Float(required=False, allow_none=True)
    MT17 = fields.Float(required=False, allow_none=True)
    MT18 = fields.Float(required=False, allow_none=True)
    MT19 = fields.Float(required=False, allow_none=True)

    # 热流道温度
    HRN = fields.Integer(required=False, allow_none=True)  # 热流道段数
    HRT0 = fields.Float(required=False, allow_none=True)
    HRT1 = fields.Float(required=False, allow_none=True)
    HRT2 = fields.Float(required=False, allow_none=True)
    HRT3 = fields.Float(required=False, allow_none=True)
    HRT4 = fields.Float(required=False, allow_none=True)
    HRT5 = fields.Float(required=False, allow_none=True)
    HRT6 = fields.Float(required=False, allow_none=True)
    HRT7 = fields.Float(required=False, allow_none=True)
    HRT8 = fields.Float(required=False, allow_none=True)
    HRT9 = fields.Float(required=False, allow_none=True)
    HRT10 = fields.Float(required=False, allow_none=True)
    HRT11 = fields.Float(required=False, allow_none=True)
    HRT12 = fields.Float(required=False, allow_none=True)
    HRT13 = fields.Float(required=False, allow_none=True)
    HRT14 = fields.Float(required=False, allow_none=True)
    HRT15 = fields.Float(required=False, allow_none=True)
    HRT16 = fields.Float(required=False, allow_none=True)
    HRT17 = fields.Float(required=False, allow_none=True)
    HRT18 = fields.Float(required=False, allow_none=True)
    HRT19 = fields.Float(required=False, allow_none=True)
    HRT20 = fields.Float(required=False, allow_none=True)
    HRT21 = fields.Float(required=False, allow_none=True)
    HRT22 = fields.Float(required=False, allow_none=True)
    HRT23 = fields.Float(required=False, allow_none=True)
    HRT24 = fields.Float(required=False, allow_none=True)
    HRT25 = fields.Float(required=False, allow_none=True)
    HRT26 = fields.Float(required=False, allow_none=True)
    HRT27 = fields.Float(required=False, allow_none=True)
    HRT28 = fields.Float(required=False, allow_none=True)
    HRT29 = fields.Float(required=False, allow_none=True)
    HRT30 = fields.Float(required=False, allow_none=True)
    HRT31 = fields.Float(required=False, allow_none=True)
    HRT32 = fields.Float(required=False, allow_none=True)
    HRT33 = fields.Float(required=False, allow_none=True)
    HRT34 = fields.Float(required=False, allow_none=True)
    HRT35 = fields.Float(required=False, allow_none=True)
    HRT36 = fields.Float(required=False, allow_none=True)
    HRT37 = fields.Float(required=False, allow_none=True)
    HRT38 = fields.Float(required=False, allow_none=True)
    HRT39 = fields.Float(required=False, allow_none=True)
    HRT40 = fields.Float(required=False, allow_none=True)
    HRT41 = fields.Float(required=False, allow_none=True)
    HRT42 = fields.Float(required=False, allow_none=True)
    HRT43 = fields.Float(required=False, allow_none=True)
    HRT44 = fields.Float(required=False, allow_none=True)
    HRT45 = fields.Float(required=False, allow_none=True)
    HRT46 = fields.Float(required=False, allow_none=True)
    HRT47 = fields.Float(required=False, allow_none=True)
    HRT48 = fields.Float(required=False, allow_none=True)
    HRT49 = fields.Float(required=False, allow_none=True)

    actual_product_weight = fields.Float(required=False, allow_none=True)
    defect_info = fields.Nested(OptimizeDefectInfoItemSchema, many=True)
    optimize_export = fields.Nested(RecordOptimizeInfoSchema)

    process_index_id = fields.Integer(required=False, allow_none=True)
    machine_id = fields.Integer(required=False, allow_none=True)
    product_weight = fields.Float(required=False, allow_none=True)
    opt_nums = fields.Integer(required=False, allow_none=True)

    polymer_abbreviation = fields.String(required=False, allow_none=True)
    product_small_type = fields.String(required=False, allow_none=True)

    subrule_no = fields.String(required=False, allow_none=True)
    general = fields.Boolean(required=False, allow_none=True)  # 调用的通用规则库

    precondition = fields.Nested(ProcessOptimizationPreconditionSchema)
