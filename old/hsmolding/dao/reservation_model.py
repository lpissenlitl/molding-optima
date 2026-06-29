from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    EmbeddedDocumentListField,
    ListField,
)


class DataItemDoc(EmbeddedDocument):
    mold_desc = StringField(null=True)
    mold_info = StringField(null=True)
    desc = StringField(null=True)
    values = ListField(null=True)


class MachineAdaptionDoc(BaseDoc):
    p_id = IntField(null=True)  # 对应模具project_id或者工艺process_index_id
    adaption_type = StringField(null=True)  # 模具或者工艺
    adaption_no = StringField(null=True)
    machine_id_list = ListField(null=True)
    table_data = EmbeddedDocumentListField(DataItemDoc, many=True)
    color_data = EmbeddedDocumentListField(DataItemDoc, many=True)
    machine_num = IntField(null=True)
    deleted = IntField(null=True)
