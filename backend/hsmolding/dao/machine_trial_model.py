from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    ListField,
    DecimalField,
    EmbeddedDocumentListField,
    DateField,
)


# 载荷敏感度测试--测试表格
class LoadSensitivityTableItemDoc(EmbeddedDocument):
    title = StringField(max_length=45, default="")
    inj_time_nomal = DecimalField(null=True,precision=3)
    inj_time_empty = DecimalField(null=True,precision=3)
    peak_pres_nomal = DecimalField(null=True,precision=3)
    peak_pres_empty = DecimalField(null=True,precision=3)
    # injection_time_ratio = DecimalField(null=True,precision=3)
    # injection_pressure_ratio = DecimalField(null=True,precision=3)
    result = DecimalField(null=True,precision=3)


# 载荷敏感度测试
class LoadSensitivityTrialDoc(BaseDoc):
    machine_trial_id = IntField(null=True)

    mold_no = StringField(max_length=45, default="") 
    product_name = StringField(max_length=45, default="") 
    machine_trademark = StringField(max_length=45, default="") 
    polymer_abbreviation = StringField(max_length=45, default="")
    polymer_trademark = StringField(max_length=45, default="")
    cycle = StringField(max_length=45, default="") 
    cavity_num = StringField(max_length=45, default="") 
    trial_name = StringField(max_length=45, default="") 
    mold_trial_date = DateField()
    asset_no = StringField(max_length=45, default="") 
    machine_data_source = StringField(max_length=45, default="") 
    pressure_unit = StringField(max_length=45, default="") 

    table_data = EmbeddedDocumentListField(LoadSensitivityTableItemDoc)



# 动态止逆环重复性测试--测试表格
class CheckRingDynamicTableItemDoc(EmbeddedDocument):
    title = StringField(max_length=45, default="") 
    sections = ListField(null=True)


# 动态止逆环重复性测试
class CheckRingDynamicTrialDoc(BaseDoc):
    machine_trial_id = IntField(null=True)

    mold_no = StringField(max_length=45, default="") 
    product_name = StringField(max_length=45, default="") 
    machine_trademark = StringField(max_length=45, default="") 
    polymer_abbreviation = StringField(max_length=45, default="")
    polymer_trademark = StringField(max_length=45, default="")
    cycle = StringField(max_length=45, default="") 
    cavity_num = StringField(max_length=45, default="") 
    trial_name = StringField(max_length=45, default="") 
    mold_trial_date = DateField()
    asset_no = StringField(max_length=45, default="") 
    machine_data_source = StringField(max_length=45, default="") 

    product_weight = DecimalField(null=True,precision=3)
    
    table_data = EmbeddedDocumentListField(CheckRingDynamicTableItemDoc)

    total_weight = DecimalField(null=True,precision=3)
    avg_product_weight = DecimalField(null=True,precision=3)
    max_product_weight = DecimalField(null=True,precision=3)
    min_product_weight = DecimalField(null=True,precision=3)
    product_weight_diff = DecimalField(null=True,precision=3)
    deviation_ratio = DecimalField(null=True,precision=3)


# 静态止逆环重复性测试--测试表格
class CheckRingStaticTableItemDoc(EmbeddedDocument):
    title = StringField(max_length=45, default="") 
    sections = ListField(null=True)


# 静态止逆环重复性测试
class CheckRingStaticTrialDoc(BaseDoc):
    machine_trial_id = IntField(null=True)

    mold_no = StringField(max_length=45, default="") 
    product_name = StringField(max_length=45, default="") 
    machine_trademark = StringField(max_length=45, default="") 
    polymer_abbreviation = StringField(max_length=45, default="") 
    polymer_trademark = StringField(max_length=45, default="")
    cycle = StringField(max_length=45, default="") 
    cavity_num = StringField(max_length=45, default="") 
    trial_name = StringField(max_length=45, default="") 
    mold_trial_date = DateField()
    asset_no = StringField(max_length=45, default="") 
    machine_data_source = StringField(max_length=45, default="") 

    table_data = EmbeddedDocumentListField(CheckRingStaticTableItemDoc)

    screw_diameter = DecimalField(null=True,precision=3)
    max_cushion = DecimalField(null=True,precision=3)
    min_cushion = DecimalField(null=True,precision=3)
    cushion_diff = DecimalField(null=True,precision=3)
    deviation_ratio = DecimalField(null=True,precision=3)


# 注射速度线性度测试--测试表格
class InjectVelocityLinearityTableItemDoc(EmbeddedDocument):
    title = StringField(max_length=45, default="") 
    setting_inject_velo = DecimalField(null=True,precision=3)
    theory_fill_time = DecimalField(null=True,precision=3)
    actual_fill_time = DecimalField(null=True,precision=3)
    actual_inject_velo = DecimalField(null=True,precision=3)
    deviation_ratio = DecimalField(null=True,precision=3)


# 注射速度线性度测试
class InjectVelocityLinearityTrialDoc(BaseDoc):
    machine_trial_id = IntField(null=True)

    mold_no = StringField(max_length=45, default="") 
    product_name = StringField(max_length=45, default="") 
    machine_trademark = StringField(max_length=45, default="") 
    polymer_abbreviation = StringField(max_length=45, default="") 
    polymer_trademark = StringField(max_length=45, default="")
    cycle = StringField(max_length=45, default="") 
    cavity_num = StringField(max_length=45, default="") 
    trial_name = StringField(max_length=45, default="") 
    mold_trial_date = DateField()
    asset_no = StringField(max_length=45, default="") 
    machine_data_source = StringField(max_length=45, default="") 

    metering_ending_position = DecimalField(null=True,precision=3)
    decompressure_distance_after_metering = DecimalField(null=True,precision=3)
    vp_switch_position = DecimalField(null=True,precision=3)
    injection_distance = DecimalField(null=True,precision=3)

    table_data = EmbeddedDocumentListField(InjectVelocityLinearityTableItemDoc)

    ave_deviation_ratio = DecimalField(null=True,precision=3)
    act_linear_range = StringField(max_length=45, default="") 
    screw_max_stroke = DecimalField(null=True,precision=3)
    screw_used_ratio = DecimalField(null=True,precision=3)


# 稳定性评估测试--测试表格
class StabilityAssessmentTableItemDoc(EmbeddedDocument):
    title = StringField(max_length=45, default="")
    cycle_time = DecimalField(null=True,precision=3)
    injection_time = DecimalField(null=True,precision=3)
    measure_time = DecimalField(null=True,precision=3)
    residual_posi = DecimalField(null=True,precision=3)
    metering_ending_position = DecimalField(null=True,precision=3)
    injection_pres = DecimalField(null=True,precision=3)
    packing_pres = DecimalField(null=True,precision=3)
    backing_pres = DecimalField(null=True,precision=3)


# 稳定性评估测试
class StabilityAssessmentTrialDoc(BaseDoc):
    machine_trial_id = IntField(null=True)

    mold_no = StringField(max_length=45, default="") 
    product_name = StringField(max_length=45, default="") 
    machine_trademark = StringField(max_length=45, default="") 
    polymer_abbreviation = StringField(max_length=45, default="") 
    polymer_trademark = StringField(max_length=45, default="")
    cycle = StringField(max_length=45, default="") 
    cavity_num = StringField(max_length=45, default="") 
    trial_name = StringField(max_length=45, default="") 
    mold_trial_date = DateField()
    asset_no = StringField(max_length=45, default="") 
    machine_data_source = StringField(max_length=45, default="") 
    pressure_unit = StringField(max_length=45, default="") 

    trial_no = IntField(null=True)
    table_data = EmbeddedDocumentListField(StabilityAssessmentTableItemDoc)


# 模版变形测试--测试表格
class MouldBoardDeflectionTableItemDoc(EmbeddedDocument):
    title = StringField(max_length=45, default="") 
    sections = ListField(null=True)


# 模版变形测试
class MouldBoardDeflectionTrialDoc(BaseDoc):
    machine_trial_id = IntField(null=True)

    mold_no = StringField(max_length=45, default="") 
    product_name = StringField(max_length=45, default="") 
    machine_trademark = StringField(max_length=45, default="") 
    polymer_abbreviation = StringField(max_length=45, default="") 
    polymer_trademark = StringField(max_length=45, default="")
    cycle = StringField(max_length=45, default="") 
    cavity_num = StringField(max_length=45, default="") 
    trial_name = StringField(max_length=45, default="") 
    mold_trial_date = DateField()
    asset_no = StringField(max_length=45, default="") 
    machine_data_source = StringField(max_length=45, default="") 

    table_data = EmbeddedDocumentListField(MouldBoardDeflectionTableItemDoc)

    total_deflection = DecimalField(null=True,precision=3)
    average_deflection = DecimalField(null=True,precision=3)


class ScrewWearItemDoc(EmbeddedDocument):
    title = StringField(max_length=45, default="") 
    sections = ListField()


class Injector(EmbeddedDocument):
    id = IntField(null=True)
    machine_id = IntField(null=True)
    screw_diameter = DecimalField(null=True)
    max_injection_stroke = DecimalField(null=True)


class ScrewWearDoc(BaseDoc):
    machine_trial_id = IntField(null=True)
    mold_no = StringField(max_length=45, default="") 
    machine_data_source = StringField(max_length=45, default="") 
    asset_no = StringField(max_length=45, default="") 
    injectors = EmbeddedDocumentListField(Injector, many=True)
    polymer_abbreviation = StringField(max_length=45, default="") 
    polymer_trademark = StringField(max_length=45, default="") 
    cycle = StringField(max_length=45, default="")
    product_name = StringField(max_length=45, default="")
    cavity_num = StringField(max_length=45, default="")
    machine_trademark = StringField(max_length=45, default="")
    trial_name = StringField(max_length=45, default="") 
    mold_trial_date = DateField()

    inject_part = StringField(max_length=45, default="") 
    max_injection_stroke = DecimalField(null=True)
    injection_starting_position = DecimalField(null=True)
    interval = DecimalField(null=True)

    melt_density = DecimalField(null=True)
    table_data = EmbeddedDocumentListField(ScrewWearItemDoc)

    slope = DecimalField(null=True)
    intercept = DecimalField(null=True)
