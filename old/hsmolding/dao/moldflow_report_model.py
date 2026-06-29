from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    DecimalField,
    ListField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
)


# 填充+保压
class FillPressurizeDoc(EmbeddedDocument):
    surface_temperature = DecimalField(null=True)
    melt_temperature = DecimalField(null=True)
    fill_control = StringField(null=True)
    inject_time = DecimalField(null=True)
    flow_rate = DecimalField(null=True)
    control_options = StringField(null=True)
    reference = StringField(null=True)
    nominal_injection_time = DecimalField(null=True)
    nominal_rate = DecimalField(null=True)
    injection_volume = StringField(null=True)
    screw_diameter = DecimalField(null=True)
    start_screw_diameter = DecimalField(null=True)
    packing_warning_limit = DecimalField(null=True)
    starting_screw_position = DecimalField(null=True)
    speed_switching = StringField(null=True)
    fill_volume = DecimalField(null=True)
    screw_position = DecimalField(null=True)
    injection_pressure = DecimalField(null=True)
    hydraulic_pressure = DecimalField(null=True)
    clamping_force = DecimalField(null=True)
    injection_time = DecimalField(null=True)
    node = StringField(null=True)
    pressure = DecimalField(null=True)
    pressure_holding_control = StringField(null=True)
    cooling_time = StringField(null=True)
    cool_time = DecimalField(null=True)


# 填充
class FillDoc(EmbeddedDocument):
    surface_temperature = DecimalField(null=True)
    melt_temperature = DecimalField(null=True)
    fill_control = StringField(null=True)
    inject_time = DecimalField(null=True)
    flow_rate = DecimalField(null=True)
    control_options = StringField(null=True)
    reference = StringField(null=True)
    nominal_injection_time = DecimalField(null=True)
    nominal_rate = DecimalField(null=True)
    injection_volume = StringField(null=True)
    screw_diameter = DecimalField(null=True)
    start_screw_diameter = DecimalField(null=True)
    packing_warning_limit = DecimalField(null=True)
    starting_screw_position = DecimalField(null=True)
    speed_switching = StringField(null=True)
    fill_volume = DecimalField(null=True)
    screw_position = DecimalField(null=True)
    injection_pressure = DecimalField(null=True)
    hydraulic_pressure = DecimalField(null=True)
    clamping_force = DecimalField(null=True)
    injection_time = DecimalField(null=True)
    node = StringField(null=True)
    pressure = DecimalField(null=True)
    pressure_holding_control = StringField(null=True)


# 冷却
class CoolingDoc(EmbeddedDocument):
    melt_temperature = DecimalField(null=True)
    mold_open_time = DecimalField(null=True)
    injection_holding_cooling_time = StringField(null=True)
    injection_holding_cool_time = DecimalField(null=True)


# 填充+保压+翘曲
class FillPressurizeWarpingDoc(EmbeddedDocument):
    surface_temperature = DecimalField(null=True)
    melt_temperature = DecimalField(null=True)
    fill_control = StringField(null=True)
    inject_time = DecimalField(null=True)
    flow_rate = DecimalField(null=True)
    control_options = StringField(null=True)
    reference = StringField(null=True)
    nominal_injection_time = DecimalField(null=True)
    nominal_rate = DecimalField(null=True)
    injection_volume = StringField(null=True)
    screw_diameter = DecimalField(null=True)
    start_screw_diameter = DecimalField(null=True)
    packing_warning_limit = DecimalField(null=True)
    starting_screw_position = DecimalField(null=True)
    speed_switching = StringField(null=True)
    fill_volume = DecimalField(null=True)
    screw_position = DecimalField(null=True)
    injection_pressure = DecimalField(null=True)
    hydraulic_pressure = DecimalField(null=True)
    clamping_force = DecimalField(null=True)
    injection_time = DecimalField(null=True)
    node = StringField(null=True)
    pressure = DecimalField(null=True)
    pressure_holding_control = StringField(null=True)
    cooling_time = StringField(null=True)
    cool_time = DecimalField(null=True)

    warping_analysis_type = StringField(null=True)
    parallel_thread = StringField(null=True)
    amg_select = StringField(null=True)
    thread_count = IntField()


# 冷却+填充+保压+翘曲
class CoolingFillPressurizeWarpingDoc(EmbeddedDocument):
    melt_temperature = DecimalField(null=True)
    mold_open_time = DecimalField(null=True)
    injection_holding_cooling_time = StringField(null=True)
    injection_holding_cool_time = DecimalField(null=True)

    fill_control = StringField(null=True)
    inject_time = DecimalField(null=True)
    flow_rate = DecimalField(null=True)
    control_options = StringField(null=True)
    reference = StringField(null=True)
    nominal_injection_time = DecimalField(null=True)
    nominal_rate = DecimalField(null=True)
    injection_volume = StringField(null=True)
    screw_diameter = DecimalField(null=True)
    start_screw_diameter = DecimalField(null=True)
    packing_warning_limit = DecimalField(null=True)
    starting_screw_position = DecimalField(null=True)
    speed_switching = StringField(null=True)
    fill_volume = DecimalField(null=True)
    screw_position = DecimalField(null=True)
    injection_pressure = DecimalField(null=True)
    hydraulic_pressure = DecimalField(null=True)
    clamping_force = DecimalField(null=True)
    injection_time = DecimalField(null=True)
    node = StringField(null=True)
    pressure = DecimalField(null=True)
    pressure_holding_control = StringField(null=True)

    warping_analysis_type = StringField(null=True)
    parallel_thread = StringField(null=True)
    amg_select = StringField(null=True)
    thread_count = IntField()


# 冷却FEM
class CoolingFemDoc(EmbeddedDocument):
    melt_temperature = DecimalField(null=True)
    mold_open_time = DecimalField(null=True)
    mold_close_time = DecimalField(null=True)
    injection_holding_cooling_time = StringField(null=True)
    injection_holding_cool_time = DecimalField(null=True)
    mold_temperature = StringField(null=True)


# 冷却FEM+填充+保压+翘曲
class CoolingFemFillPressurizeWarpingDoc(EmbeddedDocument):
    melt_temperature = DecimalField(null=True)
    mold_open_time = DecimalField(null=True)
    mold_close_time = DecimalField(null=True)
    injection_holding_cooling_time = StringField(null=True)
    injection_holding_cool_time = DecimalField(null=True)
    mold_temperature = StringField(null=True)

    fill_control = StringField(null=True)
    inject_time = DecimalField(null=True)
    flow_rate = DecimalField(null=True)
    control_options = StringField(null=True)
    reference = StringField(null=True)
    nominal_injection_time = DecimalField(null=True)
    nominal_rate = DecimalField(null=True)
    injection_volume = StringField(null=True)
    screw_diameter = DecimalField(null=True)
    start_screw_diameter = DecimalField(null=True)
    packing_warning_limit = DecimalField(null=True)
    starting_screw_position = DecimalField(null=True)
    speed_switching = StringField(null=True)
    fill_volume = DecimalField(null=True)
    screw_position = DecimalField(null=True)
    injection_pressure = DecimalField(null=True)
    hydraulic_pressure = DecimalField(null=True)
    clamping_force = DecimalField(null=True)
    injection_time = DecimalField(null=True)
    node = StringField(null=True)
    pressure = DecimalField(null=True)
    pressure_holding_control = StringField(null=True)

    warping_analysis_type = StringField(null=True)
    parallel_thread = StringField(null=True)
    amg_select = StringField(null=True)
    thread_count = IntField()


class TableDataItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    unit = StringField(null=True)
    sections = ListField(null=True)
    max = StringField(null=True)

    
#  工艺参数
class ProcessDataDoc(EmbeddedDocument):
    inject_stage = IntField(null=True)
    holding_stage = IntField(null=True)
    max_inject_stage_option = IntField(null=True)
    max_holding_stage_option = IntField(null=True)
    inject_para = EmbeddedDocumentListField(TableDataItemDoc)
    holding_para = EmbeddedDocumentListField(TableDataItemDoc)


# 分析结果二级目录
class ChildrenDoc(EmbeddedDocument):
    id = IntField()
    desc = StringField(null=True)
    animation_url = StringField(null=True)
    max_value = DecimalField(null=True)
    name = StringField(null=True)
    unit = StringField(null=True)
    

# 分析结果
class ResultDoc(EmbeddedDocument):
    name = StringField(null=True)
    children = EmbeddedDocumentListField(ChildrenDoc)


# 工艺
class TechnologyDoc(EmbeddedDocument):
    analytical_sequence = StringField(null=True)
    fill_holding = EmbeddedDocumentField(FillPressurizeDoc)
    fill = EmbeddedDocumentField(FillDoc)
    cooling = EmbeddedDocumentField(CoolingDoc)
    fill_holding_warping = EmbeddedDocumentField(FillPressurizeWarpingDoc)
    cooling_fill_holding_warping = EmbeddedDocumentField(CoolingFillPressurizeWarpingDoc)
    cooling_fem = EmbeddedDocumentField(CoolingFemDoc)
    cooling_fem_fill_holding_warping = EmbeddedDocumentField(CoolingFemFillPressurizeWarpingDoc)
    process_data = EmbeddedDocumentField(ProcessDataDoc)


# 材料
class PolymerDoc(EmbeddedDocument):
    id = IntField()
    poly_trademark = StringField(null=True)
    max_melt_temperature = DecimalField(null=True)
    min_melt_temperature = DecimalField(null=True)
    recommend_melt_temperature = DecimalField(null=True)
    max_mold_temperature = DecimalField(null=True)
    min_mold_temperature = DecimalField(null=True)
    recommend_mold_temperature = DecimalField(null=True)
    max_shear_linear_speed = DecimalField(null=True)
    min_shear_linear_speed = DecimalField(null=True)
    recommend_shear_linear_speed = DecimalField(null=True)
    recommend_injection_rate = DecimalField(null=True)
    degradation_temperature = DecimalField(null=True)
    ejection_temperature = DecimalField(null=True)
    max_sheer_rate = DecimalField(null=True)
    max_sheer_stress = DecimalField(null=True)
    recommend_back_pressure = DecimalField(null=True)
    barrel_residence_time = DecimalField(null=True)


# 机器
class MachineDoc(EmbeddedDocument):
    id = IntField()
    trademark = StringField(null=True)
    data_source = StringField(null=True)
    manufacturer = StringField(null=True)
    machine_type = StringField(null=True)
    

# 分析数据
class AnalyzeDataDoc(EmbeddedDocument):
    filling_time = DecimalField(null=True)
    vp_switch = DecimalField(null=True)
    clamping_force = DecimalField(null=True)
    injection_pressure = DecimalField(null=True)
    pressure = DecimalField(null=True)
    cavity_weight = DecimalField(null=True)
    filling_end_pressure = DecimalField(null=True)
    

# 模流数据
class MoldFlowReportDoc(BaseDoc):
    project_id = IntField()  # 模号ID
    mold_flow_no = StringField(null=True)
    deleted = IntField()
    mold_no = StringField(null=True)
    doc_link = StringField(null=True)
    ppt_link = StringField(null=True)
    machine = EmbeddedDocumentField(MachineDoc)
    polymer = EmbeddedDocumentField(PolymerDoc)
    technology = EmbeddedDocumentField(TechnologyDoc)
    result = EmbeddedDocumentListField(ResultDoc)
    analyze_data = EmbeddedDocumentField(AnalyzeDataDoc)
    test_list = ListField()