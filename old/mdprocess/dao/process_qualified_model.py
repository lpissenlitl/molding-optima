from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    ListField,
    DecimalField,
    DateTimeField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
)
from mdprocess.dao.standard_process_model import ProcessSettingItemDoc


class AuxiliaryDoc(EmbeddedDocument):
    id = IntField(null=True)
    company_id = IntField(null=True)
    machine_id = IntField(null=True)
    auxiliary_type = StringField(null=True)
    auxiliary_trademark = StringField(null=True)
    manufacture = StringField(null=True)
    serial_num = StringField(null=True)

    machine_data_source = StringField(null=True)
    machine_trademark = StringField(null=True)
    communication_interface = IntField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    deleted = IntField(null=True)


# 工艺参数优化记录 前置条件--process_optimization precondition
class ProcessQualifiedPreconditionDoc(EmbeddedDocument):
    mold_id = IntField(null=True)
    mold_no = StringField(null=True)
    cavity_num = StringField(null=True)
    runner_length = DecimalField(null=True)
    runner_weight = DecimalField(null=True)
    gate_type = StringField(null=True)
    gate_num = IntField(null=True)
    gate_shape = StringField(null=True)
    gate_area = DecimalField(null=True)
    gate_radius = DecimalField(null=True)
    gate_length = DecimalField(null=True)
    gate_width = DecimalField(null=True)

    product_no = StringField(null=True)
    product_type = StringField(null=True)
    product_name = StringField(null=True)
    product_total_weight = DecimalField(null=True)
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

    auxiliary_list = EmbeddedDocumentListField(AuxiliaryDoc)


class DrierDoc(EmbeddedDocument):
    # 干燥机
    id = IntField(null=True)
    auxiliary_type = StringField(null=True)
    auxiliary_trademark = StringField(null=True)
    manufacture = StringField(null=True)
    serial_num = StringField(null=True)
    regeneration_temperature = StringField(null=True)
    dry_temperature = StringField(null=True)
    dew_point_temperature = StringField(null=True)
    set_temperature = StringField(null=True)
    running_mark = StringField(null=True)


class ColorMatchDoc(EmbeddedDocument):
    # 色母机
    id = IntField(null=True)
    auxiliary_type = StringField(null=True)
    auxiliary_trademark = StringField(null=True)
    manufacture = StringField(null=True)
    serial_num = StringField(null=True)
    machine_each_total_control = StringField(null=True)
    one_percent = StringField(null=True)
    two_percent = StringField(null=True)
    running_mark = StringField(null=True)


class MoldTempDoc(EmbeddedDocument):
    # 模温机
    id = IntField(null=True)
    auxiliary_type = StringField(null=True)
    auxiliary_trademark = StringField(null=True)
    manufacture = StringField(null=True)
    serial_num = StringField(null=True)
    gas_outlet_temperature = StringField(null=True)
    gas_back_temperature = StringField(null=True)
    set_temperature = StringField(null=True)
    running_mark = StringField(null=True)


class HotRunnerItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    actual_temperature = StringField(null=True)
    setting_temperature = StringField(null=True)
    output_current = StringField(null=True)
    run_switch = StringField(null=True)
    running_mark = StringField(null=True)


class HotRunnerDoc(EmbeddedDocument):
    # 热流道 
    id = IntField(null=True)
    auxiliary_type = StringField(null=True)
    auxiliary_trademark = StringField(null=True)
    manufacture = StringField(null=True)
    serial_num = StringField(null=True)
    valve_needle_num = IntField(null=True)
    valve_needle_options = ListField(null=True)
    table_data = EmbeddedDocumentListField(HotRunnerItemDoc)


class AuxiliaryDetailDoc(EmbeddedDocument):
    drier = EmbeddedDocumentListField(DrierDoc)
    color_match = EmbeddedDocumentListField(ColorMatchDoc)
    mold_temp = EmbeddedDocumentListField(MoldTempDoc)
    hot_runner_timing_ctrl = EmbeddedDocumentListField(HotRunnerDoc)


# 工艺参数记录
class ProcessParameterQualifiedDoc(BaseDoc):
    process_index_id = IntField(null=True)
    precondition = EmbeddedDocumentField(ProcessQualifiedPreconditionDoc)
    process_detail = EmbeddedDocumentField(ProcessSettingItemDoc)
    auxiliary_detail = EmbeddedDocumentField(AuxiliaryDetailDoc)
