from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    StringField,
    IntField,
    DecimalField,
    ListField,
    BooleanField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField
)
from mdprocess.dao.standard_process_model import ProcessSettingItemDoc
from mdprocess.dao.process_qualified_model import AuxiliaryDetailDoc, AuxiliaryDoc


# 调机工艺导航记录 前置条件--process_guide precondition
class ProcessGuidePreconditionDoc(EmbeddedDocument):
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


# 调机工艺导航记录 注塑准备--process_guide prepare check_item
class ProcessGuidePrepareCheckItemDoc(EmbeddedDocument):
    desc = StringField(null=True)
    result = IntField(default=0)
    remark = ListField(null=True)


# 调机工艺导航记录 每模工艺--process_guide process
class ProcessGuideProcess(EmbeddedDocument):
    title = StringField(null=True)
    name = StringField(null=True)
    is_show = BooleanField(null=True)
    process_detail = EmbeddedDocumentField(ProcessSettingItemDoc)
    auxiliary_detail = EmbeddedDocumentField(AuxiliaryDetailDoc)


# 调机工艺导航记录--process_guide
class ProcessGuideDoc(BaseDoc):
    process_index_id = IntField(null=True)
    precondition = EmbeddedDocumentField(ProcessGuidePreconditionDoc)
    prepare_state = EmbeddedDocumentListField(ProcessGuidePrepareCheckItemDoc)
    process_list = EmbeddedDocumentListField(ProcessGuideProcess)
