from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    DecimalField,
    ListField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    DateTimeField
)
from mdprocess.dao.standard_process_model import ProcessSettingItemDoc


# 工艺参数优化记录 前置条件--process_optimization precondition
class ProcessOptimizationPreconditionDoc(EmbeddedDocument):
    mold_id = IntField(null=True)
    mold_no = StringField(null=True)
    cavity_num = StringField(null=True)
    inject_cycle_require = DecimalField(null=True)
    subrule_no = StringField(null=True)  # 模具绑定的子规则库
    runner_length = DecimalField(null=True)
    runner_weight = DecimalField(null=True)
    gate_type = StringField(null=True)
    gate_num = IntField(null=True)
    gate_shape = StringField(null=True)
    gate_area = DecimalField(null=True)
    gate_radius = DecimalField(null=True)
    gate_length = DecimalField(null=True)
    gate_width = DecimalField(null=True)

    inject_part = StringField(null=True)
    product_type = StringField(null=True)
    product_total_weight = DecimalField(null=True)

    product_no = StringField(null=True)
    product_name = StringField(null=True)
    product_ave_thickness = DecimalField(null=True)
    product_max_thickness = DecimalField(null=True)
    product_max_length = DecimalField(null=True)

    machine_id = IntField(null=True)
    machine_data_source = StringField(null=True)
    machine_trademark = StringField(null=True)
    machine_serial_no = StringField(null=True)

    polymer_id = IntField(null=True)
    polymer_abbreviation = StringField(null=True)
    polymer_trademark = StringField(null=True)
    recommend_melt_temperature = DecimalField(null=True)

    data_sources = StringField(null=True)
    mold_trials_no = StringField(null=True)

    injection_stage = IntField(null=True)  # 注射段数
    holding_stage = IntField(null=True)  # 计量段数
    VP_switch_mode = StringField(null=True)  # VP切换模式
    metering_stage = IntField(null=True)  # 计量段数
    decompressure_mode_before_metering = StringField(null=True)  # 储前松退模式
    decompressure_mode_after_metering = StringField(null=True)  # 储后松退模式
    barrel_temperature_stage = IntField(null=True)  # 料筒温度段数
    
    runner_type = StringField(null=True)
    hot_runner_num = IntField(null=True)

    valve_num = IntField(null=True)


# 辅机（热流道）设定值--auxiliary_setting hot_runner
class AuxiliarySettingHotRunnerDoc(EmbeddedDocument):
    valve_num = IntField(null=True)
    sequential_ctrl_time = ListField(null=True)


# 辅机（模温机）设定值--auxiliary_setting mold_temp
class AuxiliarySettingMoldTempDoc(EmbeddedDocument):
    setting_temp = DecimalField(null=True)
    mold_temp_num = IntField(null=True)
    mold_temp_list = ListField(null=True)


# 辅机设定值--auxiliary_setting
class AuxiliarySettingDetailDoc(EmbeddedDocument):
    hot_runner = EmbeddedDocumentField(AuxiliarySettingHotRunnerDoc)
    mold_temp = EmbeddedDocumentField(AuxiliarySettingMoldTempDoc)
    hot_runner_temperatures = ListField()  # 热流道温度


# 缺陷反馈--process_optimization record defect_info item
class RecordDefectInfoItemDoc(EmbeddedDocument):
    label = StringField(null=True)  # 缺陷的中文名称
    desc = StringField(null=True)  # 缺陷的大写字母
    level = StringField(null=True)
    position = StringField(null=True)
    feedback = StringField(null=True)
    count = IntField(null=True)
    remark = StringField(null=True)


# 缺陷反馈--process_optimization record defect_info
# class RecordDefectInfoDoc(EmbeddedDocument):
#     short_shot = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     flash = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     shrinkage = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     weld_line = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     aberration = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     air_trap = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     gas_veins = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     material_flower = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     hard_demolding = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     burn = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     water_ripple = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     top_white = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     warping = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     oversize = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     undersize = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     gatemark = EmbeddedDocumentField(RecordDefectInfoItemDoc)
#     shading = EmbeddedDocumentField(RecordDefectInfoItemDoc)


# 优化记录--process_optimization record rules_para
class RecordRulesParaDoc(EmbeddedDocument):
    rule_id = IntField(null=True)
    rule_description = StringField(null=True)
    rule_activation = DecimalField(null=True)
    rule_result_key = StringField(null=True)
    rule_result_value = DecimalField(null=True)


# 特殊规则记录--process_optimization record rules_para
class RecordRulesWordDoc(EmbeddedDocument):
    rule_id = IntField(null=True)
    rule_description = StringField(null=True)
    rule_defect = StringField(null=True)
    rule_output = StringField(null=True)


class RuleMethodDoc(EmbeddedDocument):
    id = IntField(null=True)
    
    polymer_abbreviation = StringField(null=True)  # 材料类别
    product_small_type = StringField(null=True)  # 制品类别
    rule_description = StringField(null=True)  # 规则描述
    rule_explanation = StringField(null=True)  # 规则解释

    is_auto = IntField(null=True)
    enable = IntField(null=True)

    defect_name = StringField(null=True)
    defect_desc = StringField(null=True)
    subrule_no = StringField(null=True)
    rule_type = StringField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    deleted =  IntField(null=True)


# 优化记录--process_optimization record optimize_info
class RecordOptimizeInfoDoc(EmbeddedDocument):
    defect_num = IntField(null=True)  # 记录上一模缺陷在缺陷列表中的序号,0表示短射
    defect_feedback = StringField(null=True)  # 记录上一模缺陷反馈
    defect_name = StringField(null=True)  # 上一模缺陷的大写
    defect_position = StringField(null=True)  #  上一模缺陷的位置
    defect_level = StringField(null=True)  # 上一模缺陷的程度
    adjust_name = StringField(null=True)
    adjust_direction = DecimalField(null=True)
    adjust_value = DecimalField(null=True)
    rule_in_use = StringField(null=True)
    rule_valid = IntField(null=True)
    rule_library_in_use = StringField(null=True)

    candidate_rules = EmbeddedDocumentListField(RecordRulesParaDoc)
    adjust_rules = EmbeddedDocumentListField(RecordRulesWordDoc)
    chosen_rules = EmbeddedDocumentListField(RuleMethodDoc)  # 用户选择执行的子规则


# 反馈信息--process_optimization detail
class RecordFeedbackDetailDoc(EmbeddedDocument):
    actual_product_weight = DecimalField(null=True)
    defect_info = EmbeddedDocumentListField(RecordDefectInfoItemDoc)
    optimize_export = EmbeddedDocumentField(RecordOptimizeInfoDoc)


# 工艺参数记录表--process_parameter_record optimize_list
class ProcessOptimizeOptimizeDetailDoc(EmbeddedDocument):
    title = StringField(null=True)
    name = StringField(null=True)
    
    process_detail = EmbeddedDocumentField(ProcessSettingItemDoc)
    auxiliary_detail = EmbeddedDocumentField(AuxiliarySettingDetailDoc)
    feedback_detail = EmbeddedDocumentField(RecordFeedbackDetailDoc)


# 工艺参数优化记录
class ProcessOptimizationDoc(BaseDoc):
    process_index_id = IntField(null=True)
    precondition = EmbeddedDocumentField(ProcessOptimizationPreconditionDoc)
    optimize_list = EmbeddedDocumentListField(ProcessOptimizeOptimizeDetailDoc)
    flaw_picture_url = StringField(null=True)
