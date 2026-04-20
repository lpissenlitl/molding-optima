from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema


# 填充+保压
class FillPressurizeSchema(BaseSchema):
    surface_temperature = fields.Float(required=False, allow_none=True)
    melt_temperature = fields.Float(required=False, allow_none=True)
    fill_control = fields.String(required=False, allow_none=True)
    inject_time = fields.Float(required=False, allow_none=True)
    flow_rate = fields.Float(required=False, allow_none=True)
    control_options = fields.String(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    nominal_injection_time = fields.Float(required=False, allow_none=True)
    nominal_rate = fields.Float(required=False, allow_none=True)
    injection_volume = fields.String(required=False, allow_none=True)
    screw_diameter = fields.Float(required=False, allow_none=True)
    start_screw_diameter = fields.Float(required=False, allow_none=True)
    packing_warning_limit = fields.Float(required=False, allow_none=True)
    starting_screw_position = fields.Float(required=False, allow_none=True)
    speed_switching = fields.String(required=False, allow_none=True)
    fill_volume = fields.Float(required=False, allow_none=True)
    screw_position = fields.Float(required=False, allow_none=True)
    injection_pressure = fields.Float(required=False, allow_none=True)
    hydraulic_pressure = fields.Float(required=False, allow_none=True)
    clamping_force = fields.Float(required=False, allow_none=True)
    injection_time = fields.Float(required=False, allow_none=True)
    node = fields.String(required=False, allow_none=True)
    pressure = fields.Float(required=False, allow_none=True)
    pressure_holding_control = fields.String(required=False, allow_none=True)
    cooling_time = fields.String(required=False, allow_none=True)
    cool_time = fields.Float(required=False, allow_none=True)


# 填充
class FillSchema(BaseSchema):
    surface_temperature = fields.Float(required=False, allow_none=True)
    melt_temperature = fields.Float(required=False, allow_none=True)
    fill_control = fields.String(required=False, allow_none=True)
    inject_time = fields.Float(required=False, allow_none=True)
    flow_rate = fields.Float(required=False, allow_none=True)
    control_options = fields.String(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    nominal_injection_time = fields.Float(required=False, allow_none=True)
    nominal_rate = fields.Float(required=False, allow_none=True)
    injection_volume = fields.String(required=False, allow_none=True)
    screw_diameter = fields.Float(required=False, allow_none=True)
    start_screw_diameter = fields.Float(required=False, allow_none=True)
    packing_warning_limit = fields.Float(required=False, allow_none=True)
    starting_screw_position = fields.Float(required=False, allow_none=True)
    speed_switching = fields.String(required=False, allow_none=True)
    fill_volume = fields.Float(required=False, allow_none=True)
    screw_position = fields.Float(required=False, allow_none=True)
    injection_pressure = fields.Float(required=False, allow_none=True)
    hydraulic_pressure = fields.Float(required=False, allow_none=True)
    clamping_force = fields.Float(required=False, allow_none=True)
    injection_time = fields.Float(required=False, allow_none=True)
    node = fields.String(required=False, allow_none=True)
    pressure = fields.Float(required=False, allow_none=True)
    pressure_holding_control = fields.String(required=False, allow_none=True)


# 冷却
class CoolingSchema(BaseSchema):
    melt_temperature = fields.Float(required=False, allow_none=True)
    mold_open_time = fields.Float(required=False, allow_none=True)
    injection_holding_cooling_time = fields.String(required=False, allow_none=True)
    injection_holding_cool_time = fields.Float(required=False, allow_none=True)


# 填充+保压+翘曲
class FillPressurizeWarpingSchema(BaseSchema):
    surface_temperature = fields.Float(required=False, allow_none=True)
    melt_temperature = fields.Float(required=False, allow_none=True)
    fill_control = fields.String(required=False, allow_none=True)
    inject_time = fields.Float(required=False, allow_none=True)
    flow_rate = fields.Float(required=False, allow_none=True)
    control_options = fields.String(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    nominal_injection_time = fields.Float(required=False, allow_none=True)
    nominal_rate = fields.Float(required=False, allow_none=True)
    injection_volume = fields.String(required=False, allow_none=True)
    screw_diameter = fields.Float(required=False, allow_none=True)
    start_screw_diameter = fields.Float(required=False, allow_none=True)
    packing_warning_limit = fields.Float(required=False, allow_none=True)
    starting_screw_position = fields.Float(required=False, allow_none=True)
    speed_switching = fields.String(required=False, allow_none=True)
    fill_volume = fields.Float(required=False, allow_none=True)
    screw_position = fields.Float(required=False, allow_none=True)
    injection_pressure = fields.Float(required=False, allow_none=True)
    hydraulic_pressure = fields.Float(required=False, allow_none=True)
    clamping_force = fields.Float(required=False, allow_none=True)
    injection_time = fields.Float(required=False, allow_none=True)
    node = fields.String(required=False, allow_none=True)
    pressure = fields.Float(required=False, allow_none=True)
    pressure_holding_control = fields.String(required=False, allow_none=True)
    cooling_time = fields.String(required=False, allow_none=True)
    cool_time = fields.Float(required=False, allow_none=True)

    warping_analysis_type = fields.String(required=False, allow_none=True)
    parallel_thread = fields.String(required=False, allow_none=True)
    amg_select = fields.String(required=False, allow_none=True)
    thread_count = fields.Integer(required=False, allow_none=True)


# 冷却+填充+保压+翘曲
class CoolingFillPressurizeWarpingSchema(BaseSchema):
    melt_temperature = fields.Float(required=False, allow_none=True)
    mold_open_time = fields.Float(required=False, allow_none=True)
    injection_holding_cooling_time = fields.String(required=False, allow_none=True)
    injection_holding_cool_time = fields.Float(required=False, allow_none=True)

    fill_control = fields.String(required=False, allow_none=True)
    inject_time = fields.Float(required=False, allow_none=True)
    flow_rate = fields.Float(required=False, allow_none=True)
    control_options = fields.String(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    nominal_injection_time = fields.Float(required=False, allow_none=True)
    nominal_rate = fields.Float(required=False, allow_none=True)
    injection_volume = fields.String(required=False, allow_none=True)
    screw_diameter = fields.Float(required=False, allow_none=True)
    start_screw_diameter = fields.Float(required=False, allow_none=True)
    packing_warning_limit = fields.Float(required=False, allow_none=True)
    starting_screw_position = fields.Float(required=False, allow_none=True)
    speed_switching = fields.String(required=False, allow_none=True)
    fill_volume = fields.Float(required=False, allow_none=True)
    screw_position = fields.Float(required=False, allow_none=True)
    injection_pressure = fields.Float(required=False, allow_none=True)
    hydraulic_pressure = fields.Float(required=False, allow_none=True)
    clamping_force = fields.Float(required=False, allow_none=True)
    injection_time = fields.Float(required=False, allow_none=True)
    node = fields.String(required=False, allow_none=True)
    pressure = fields.Float(required=False, allow_none=True)
    pressure_holding_control = fields.String(required=False, allow_none=True)

    warping_analysis_type = fields.String(required=False, allow_none=True)
    parallel_thread = fields.String(required=False, allow_none=True)
    amg_select = fields.String(required=False, allow_none=True)
    thread_count = fields.Integer(required=False, allow_none=True)


# 冷却FEM
class CoolingFemSchema(BaseSchema):
    melt_temperature = fields.Float(required=False, allow_none=True)
    mold_open_time = fields.Float(required=False, allow_none=True)
    mold_close_time = fields.Float(required=False, allow_none=True)
    injection_holding_cooling_time = fields.String(required=False, allow_none=True)
    injection_holding_cool_time = fields.Float(required=False, allow_none=True)
    mold_temperature = fields.String(required=False, allow_none=True)


# 冷却FEM+填充+保压+翘曲
class CoolingFemFillPressurizeWarpingSchema(BaseSchema):
    melt_temperature = fields.Float(required=False, allow_none=True)
    mold_open_time = fields.Float(required=False, allow_none=True)
    mold_close_time = fields.Float(required=False, allow_none=True)
    injection_holding_cooling_time = fields.String(required=False, allow_none=True)
    injection_holding_cool_time = fields.Float(required=False, allow_none=True)
    mold_temperature = fields.String(required=False, allow_none=True)

    fill_control = fields.String(required=False, allow_none=True)
    inject_time = fields.Float(required=False, allow_none=True)
    flow_rate = fields.Float(required=False, allow_none=True)
    control_options = fields.String(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    nominal_injection_time = fields.Float(required=False, allow_none=True)
    nominal_rate = fields.Float(required=False, allow_none=True)
    injection_volume = fields.String(required=False, allow_none=True)
    screw_diameter = fields.Float(required=False, allow_none=True)
    start_screw_diameter = fields.Float(required=False, allow_none=True)
    packing_warning_limit = fields.Float(required=False, allow_none=True)
    starting_screw_position = fields.Float(required=False, allow_none=True)
    speed_switching = fields.String(required=False, allow_none=True)
    fill_volume = fields.Float(required=False, allow_none=True)
    screw_position = fields.Float(required=False, allow_none=True)
    injection_pressure = fields.Float(required=False, allow_none=True)
    hydraulic_pressure = fields.Float(required=False, allow_none=True)
    clamping_force = fields.Float(required=False, allow_none=True)
    injection_time = fields.Float(required=False, allow_none=True)
    node = fields.String(required=False, allow_none=True)
    pressure = fields.Float(required=False, allow_none=True)
    pressure_holding_control = fields.String(required=False, allow_none=True)

    warping_analysis_type = fields.String(required=False, allow_none=True)
    parallel_thread = fields.String(required=False, allow_none=True)
    amg_select = fields.String(required=False, allow_none=True)
    thread_count = fields.Integer(required=False, allow_none=True)


class TableDataSchema(BaseSchema):
    label = fields.String(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))
    max = fields.String(required=False, allow_none=True)

    
#  工艺参数
class ProcessDataSchema(BaseSchema):
    inject_stage = fields.Integer(required=False, allow_none=True)
    holding_stage = fields.Integer(required=False, allow_none=True)
    max_inject_stage_option = fields.Integer(required=False, allow_none=True)
    max_holding_stage_option = fields.Integer(required=False, allow_none=True)
    inject_para = fields.Nested(TableDataSchema, many=True)
    holding_para = fields.Nested(TableDataSchema, many=True)


# 分析结果二级目录
class ChildrenSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    desc = fields.String(required=False, allow_none=True)
    animation_url = fields.String(required=False, allow_none=True)
    max_value = fields.Float(required=False, allow_none=True)
    unit = fields.String(required=False, allow_none=True)


# 分析结果
class ResultSchema(BaseSchema):
    name = fields.String(required=False, allow_none=True)
    children = fields.Nested(ChildrenSchema, many=True)


# 工艺
class TechnologySchema(BaseSchema):
    analytical_sequence = fields.String(required=False, allow_none=True)
    fill_holding = fields.Nested(FillPressurizeSchema)
    fill = fields.Nested(FillSchema)
    cooling = fields.Nested(CoolingSchema)
    fill_holding_warping = fields.Nested(FillPressurizeWarpingSchema)
    cooling_fill_holding_warping = fields.Nested(CoolingFillPressurizeWarpingSchema)
    cooling_fem = fields.Nested(CoolingFemSchema)
    cooling_fem_fill_holding_warping = fields.Nested(CoolingFemFillPressurizeWarpingSchema)
    process_data = fields.Nested(ProcessDataSchema)


# 材料
class PolymerSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    poly_trademark = fields.String(required=False, allow_none=True)
    max_melt_temperature = fields.Float(required=False, allow_none=True)
    min_melt_temperature = fields.Float(required=False, allow_none=True)
    recommend_melt_temperature = fields.Float(required=False, allow_none=True)
    max_mold_temperature = fields.Float(required=False, allow_none=True)
    min_mold_temperature = fields.Float(required=False, allow_none=True)
    recommend_mold_temperature = fields.Float(required=False, allow_none=True)
    max_shear_linear_speed = fields.Float(required=False, allow_none=True)
    min_shear_linear_speed = fields.Float(required=False, allow_none=True)
    recommend_shear_linear_speed = fields.Float(required=False, allow_none=True)
    recommend_injection_rate = fields.Float(required=False, allow_none=True)
    degradation_temperature = fields.Float(required=False, allow_none=True)
    ejection_temperature = fields.Float(required=False, allow_none=True)
    max_sheer_rate = fields.Float(required=False, allow_none=True)
    max_sheer_stress = fields.Float(required=False, allow_none=True)
    recommend_back_pressure = fields.Float(required=False, allow_none=True)
    barrel_residence_time = fields.Float(required=False, allow_none=True)


# 机器
class MachineSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    trademark = fields.String(required=False, allow_none=True)
    data_source = fields.String(required=False, allow_none=True)
    manufacturer = fields.String(required=False, allow_none=True)
    machine_type = fields.String(required=False, allow_none=True)
    

# 分析数据
class AnalyzeDatSchema(BaseSchema):
    filling_time = fields.Float(required=False, allow_none=True)
    vp_switch = fields.Float(required=False, allow_none=True)
    clamping_force = fields.Float(required=False, allow_none=True)
    injection_pressure = fields.Float(required=False, allow_none=True)
    pressure = fields.Float(required=False, allow_none=True)
    cavity_weight = fields.Float(required=False, allow_none=True)
    filling_end_pressure = fields.Float(required=False, allow_none=True)
    
# 模流数据
class MoldFlowReportSchema(BaseSchema):
    project_id = fields.Integer()  # 模号ID
    mold_flow_no = fields.String(required=False, allow_none=True)
    deleted = fields.Integer()
    mold_no = fields.String(required=False, allow_none=True)
    doc_link = fields.String(required=False, allow_none=True)
    ppt_link = fields.String(required=False, allow_none=True)
    machine = fields.Nested(MachineSchema)
    polymer = fields.Nested(PolymerSchema)
    technology = fields.Nested(TechnologySchema)
    result = fields.Nested(ResultSchema, many=True)
    analyze_data = fields.Nested(AnalyzeDatSchema)
    test_list = fields.List(fields.Integer())


# 按条件搜索
class MoldFlowReportQuerySchema(BaseSchema):
    project_id = fields.Integer()  # 模号ID
    mold_flow_no = fields.String(required=False, allow_none=True)
    analytical_sequence = fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    poly_trademark = fields.String(required=False, allow_none=True)
    created_at = fields.Date(required=False, allow_none=True)