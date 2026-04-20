from ast import alias
from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    DecimalField,
    EmbeddedDocumentField,
)
from mdprocess.dao.standard_process_model import ProcessSettingItemDoc


# 工艺参数优化记录 前置条件--process_optimization precondition
class ProcessRecordPreconditionDoc(EmbeddedDocument):
    mold_id = IntField(null=True)
    data_sources = StringField(null=True)
    mold_trials_no = StringField(null=True)
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


# 工艺参数记录
class ProcessParameterRecordDoc(BaseDoc):
    process_index_id = IntField(null=True)
    precondition = EmbeddedDocumentField(ProcessRecordPreconditionDoc)
    process_detail = EmbeddedDocumentField(ProcessSettingItemDoc)