from marshmallow import fields

from gis.common.django_ext.forms import (
    BaseSchema,
    CNDatetimeField,
    PaginationBaseSchema,
)


# 载荷敏感度测试--测试表格
class LoadSensitivityTableItemSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True) 
    inj_time_nomal = fields.Float(required=False, allow_none=True)
    inj_time_empty = fields.Float(required=False, allow_none=True)
    peak_pres_nomal = fields.Float(required=False, allow_none=True)
    peak_pres_empty = fields.Float(required=False, allow_none=True)
    result = fields.Float(required=False, allow_none=True)


# 载荷敏感度测试
class LoadSensitivityTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer()

    mold_no = fields.String(required=False, allow_none=True) 
    product_name = fields.String(required=False, allow_none=True) 
    machine_trademark = fields.String(required=False, allow_none=True) 
    polymer_abbreviation = fields.String(required=False, allow_none=True) 
    cycle = fields.String(required=False, allow_none=True) 
    cavity_num = fields.String(required=False, allow_none=True)
    trial_name = fields.String(required=False, allow_none=True) 
    mold_trial_date = fields.Date(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    pressure_unit = fields.String(required=False, allow_none=True)

    table_data = fields.Nested(LoadSensitivityTableItemSchema, many=True)


# 动态止逆环重复性测试--测试表格
class CheckRingDynamicTableItemSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))


# 动态止逆环重复性测试
class CheckRingDynamicTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer()

    mold_no = fields.String(required=False, allow_none=True) 
    product_name = fields.String(required=False, allow_none=True) 
    machine_trademark = fields.String(required=False, allow_none=True) 
    polymer_abbreviation = fields.String(required=False, allow_none=True) 
    cycle = fields.String(required=False, allow_none=True) 
    cavity_num = fields.String(required=False, allow_none=True)
    trial_name = fields.String(required=False, allow_none=True) 
    mold_trial_date = fields.Date(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)

    product_weight = fields.Float(required=False, allow_none=True)

    table_data = fields.Nested(CheckRingDynamicTableItemSchema, many=True)

    total_weight = fields.Float(required=False, allow_none=True)
    avg_product_weight = fields.Float(required=False, allow_none=True)
    max_product_weight = fields.Float(required=False, allow_none=True)
    min_product_weight = fields.Float(required=False, allow_none=True)
    product_weight_diff = fields.Float(required=False, allow_none=True)
    deviation_ratio = fields.Float(required=False, allow_none=True)


# 静态止逆环重复性测试--测试表格
class CheckRingStaticTableItemSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))


# 静态止逆环重复性测试
class CheckRingStaticTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer()

    mold_no = fields.String(required=False, allow_none=True) 
    product_name = fields.String(required=False, allow_none=True) 
    machine_trademark = fields.String(required=False, allow_none=True) 
    polymer_abbreviation = fields.String(required=False, allow_none=True) 
    cycle = fields.String(required=False, allow_none=True) 
    cavity_num = fields.String(required=False, allow_none=True)
    trial_name = fields.String(required=False, allow_none=True) 
    mold_trial_date = fields.Date(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)

    table_data = fields.Nested(CheckRingStaticTableItemSchema, many=True)

    screw_diameter = fields.Float(required=False, allow_none=True)
    max_cushion = fields.Float(required=False, allow_none=True)
    min_cushion = fields.Float(required=False, allow_none=True)
    cushion_diff = fields.Float(required=False, allow_none=True)
    deviation_ratio = fields.Float(required=False, allow_none=True)


# 注射速度线性度测试--测试表格
class InjectVelocityLinearityTableItemSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    setting_inject_velo = fields.Float(required=False, allow_none=True)
    theory_fill_time = fields.Float(required=False, allow_none=True)
    actual_fill_time = fields.Float(required=False, allow_none=True)
    actual_inject_velo = fields.Float(required=False, allow_none=True)
    deviation_ratio = fields.Float(required=False, allow_none=True)


# 注射速度线性度测试
class InjectVelocityLinearityTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer()

    mold_no = fields.String(required=False, allow_none=True) 
    product_name = fields.String(required=False, allow_none=True) 
    machine_trademark = fields.String(required=False, allow_none=True) 
    polymer_abbreviation = fields.String(required=False, allow_none=True) 
    cycle = fields.String(required=False, allow_none=True) 
    cavity_num = fields.String(required=False, allow_none=True)
    trial_name = fields.String(required=False, allow_none=True) 
    mold_trial_date = fields.Date(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)

    metering_ending_position = fields.Float(required=False, allow_none=True)
    decompressure_distance_after_metering = fields.Float(required=False, allow_none=True)
    vp_switch_position = fields.Float(required=False, allow_none=True)
    injection_distance = fields.Float(required=False, allow_none=True)

    table_data = fields.Nested(InjectVelocityLinearityTableItemSchema, many=True)

    ave_deviation_ratio = fields.Float(required=False, allow_none=True)
    act_linear_range = fields.String(required=False, allow_none=True)
    screw_max_stroke = fields.Float(required=False, allow_none=True)
    screw_used_ratio = fields.Float(required=False, allow_none=True)


# 稳定性评估测试--测试表格
class StabilityAssessmentTableItemSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    cycle_time = fields.Float(required=False, allow_none=True)
    injection_time = fields.Float(required=False, allow_none=True)
    measure_time = fields.Float(required=False, allow_none=True)
    residual_posi = fields.Float(required=False, allow_none=True)
    metering_ending_position = fields.Float(required=False, allow_none=True)
    injection_pres = fields.Float(required=False, allow_none=True)
    packing_pres = fields.Float(required=False, allow_none=True)
    backing_pres = fields.Float(required=False, allow_none=True)


# 稳定性评估测试
class StabilityAssessmentTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer()

    mold_no = fields.String(required=False, allow_none=True) 
    product_name = fields.String(required=False, allow_none=True) 
    machine_trademark = fields.String(required=False, allow_none=True) 
    polymer_abbreviation = fields.String(required=False, allow_none=True) 
    cycle = fields.String(required=False, allow_none=True) 
    cavity_num = fields.String(required=False, allow_none=True)
    trial_name = fields.String(required=False, allow_none=True) 
    mold_trial_date = fields.Date(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    pressure_unit = fields.String(required=False, allow_none=True)

    trial_no = fields.Integer(required=False, allow_none=True)
    table_data = fields.Nested(StabilityAssessmentTableItemSchema, many=True)


# 模版变形测试--测试表格
class MouldBoardDeflectionTableItemSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))


# 模版变形测试
class MouldBoardDeflectionTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer()

    mold_no = fields.String(required=False, allow_none=True) 
    product_name = fields.String(required=False, allow_none=True) 
    machine_trademark = fields.String(required=False, allow_none=True) 
    polymer_abbreviation = fields.String(required=False, allow_none=True) 
    cycle = fields.String(required=False, allow_none=True) 
    cavity_num = fields.String(required=False, allow_none=True)
    trial_name = fields.String(required=False, allow_none=True) 
    mold_trial_date = fields.Date(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)

    table_data = fields.Nested(MouldBoardDeflectionTableItemSchema, many=True)

    total_deflection = fields.Float(required=False, allow_none=True)
    average_deflection = fields.Float(required=False, allow_none=True)


# 机器测试
class MachineTrialSchema(BaseSchema):
    id = fields.Float()
    company_id = fields.Integer()

    machine_trial_type = fields.String(required=False, allow_none=True)
    mold_id = fields.Integer(required=False, allow_none=True)
    mold_no = fields.String(required=False, allow_none=True)
    product_name = fields.String(required=False, allow_none=True)
    product_type = fields.String(required=False, allow_none=True)
    machine_id = fields.Integer(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    polymer_id = fields.Integer(required=False, allow_none=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)

    doc_link = fields.String(required=False, allow_none=True)
    report_export_at = CNDatetimeField()

    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer()


# 机器测试记录
class GetMachineTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer(required=False, allow_none=True)


# 机器测试记录列表
class GetMachineTrialListSchema(PaginationBaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    machine_trial_type = fields.String(required=False, allow_none=True)
    trial_start_date = fields.Date(required=False, allow_none=True)
    trial_end_date = fields.Date(required=False, allow_none=True)
    

# 多条记录处理
class HandleMultipleTrialSchema(BaseSchema):
    machine_trial_id_list = fields.List(fields.Integer(required=False, allow_none=True))


class ExportMachineTrialSchema(BaseSchema):
    machine_trial_id = fields.Integer(required=False, allow_none=True)


class ScrewWearItemSchema(BaseSchema):
    title = fields.String(required=False, allow_none=True)
    sections = fields.List(fields.Float(required=False, allow_none=True))


class Injector(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    machine_id = fields.Integer(required=False, allow_none=True)
    screw_diameter = fields.Float(required=False, allow_none=True)
    max_injection_stroke = fields.Float(required=False, allow_none=True)


class ScrewWearSchema(BaseSchema):
    machine_trial_id = fields.Integer(required=False, allow_none=True)
    mold_no = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    asset_no = fields.String(required=False, allow_none=True)
    injectors = fields.Nested(Injector, many=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    cycle = fields.String(required=False, allow_none=True)
    product_name = fields.String(required=False, allow_none=True)
    cavity_num = fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    trial_name = fields.String(required=False, allow_none=True)
    mold_trial_date = CNDatetimeField(required=False, allow_none=True)

    inject_part = fields.String(required=False, allow_none=True)
    max_injection_stroke = fields.Float(required=False, allow_none=True)
    injection_starting_position = fields.Float(required=False, allow_none=True)
    interval = fields.Float(required=False, allow_none=True)

    melt_density = fields.Float(required=False, allow_none=True)
    table_data = fields.Nested(ScrewWearItemSchema, many=True)

    slope = fields.Float(required=False, allow_none=True)
    intercept = fields.Float(required=False, allow_none=True)
