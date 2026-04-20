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


class PropertyDoc(EmbeddedDocument):
    rule_name = StringField(null=True)
    action = StringField(null=True)


class NodeDoc(EmbeddedDocument):
    id = StringField(null=True)
    type = StringField(null=True)
    x = IntField(null=True)
    y = IntField(null=True)
    text = StringField(null=True)
    properties = EmbeddedDocumentField(PropertyDoc)


class PostionDoc(EmbeddedDocument):
    x = IntField(null=True)
    y = IntField(null=True)


class EdgeDoc(EmbeddedDocument):
    sourceNodeId = StringField(null=True)
    targetNodeId = StringField(null=True)
    type = StringField(null=True)
    text = StringField(null=True)
    pointsList = EmbeddedDocumentListField(PostionDoc)


class GraphDataDoc(EmbeddedDocument):
    nodes = EmbeddedDocumentListField(NodeDoc)
    edges = EmbeddedDocumentListField(EdgeDoc)


class SolutionsDoc(EmbeddedDocument):
    conditiontype = StringField(null=True)  # "结论"
    keyword = StringField(null=True)  # "储料量"
    describe = StringField(null=True)  # "MEL"
    action = StringField(null=True)  # "增大"
    action_key = StringField(null=True)  # "add"


class PreconditionsDoc(EmbeddedDocument):
    conditiontype = StringField(null=True)  # "检查VP切换位置"
    keyword = StringField(null=True)  # "储料量"
    describe = StringField(null=True)  # "MEL"
    status = StringField(null=True)  # "不足"
    solutions = EmbeddedDocumentListField(SolutionsDoc)


class RuleMethodDoc(EmbeddedDocument):
    total_pre_num = IntField(null=True)
    preconditions = EmbeddedDocumentListField(PreconditionsDoc)
    total_solution_num = IntField(null=True)
    sub_solution_num_list = ListField(null=True)
    solution_ways = ListField(null=True)
    

class DefectDataDoc(EmbeddedDocument):
    defect_name = StringField(null=True)  # 如短射
    defect_desc = StringField(null=True)  # 如SHORTSHOT
    graph_data = EmbeddedDocumentField(GraphDataDoc)
    rule_method = EmbeddedDocumentField(RuleMethodDoc)


class RuleFlowDoc(BaseDoc):
    rule_library = StringField(null=True)  # 基础库, 或 R20220609163348
    rule_type = StringField(null=True)  # 基础库, 或 子规则库
    product_small_type = StringField(null=True)  # 制品
    polymer_abbreviation = StringField(null=True)  # 塑料
    defect_data = EmbeddedDocumentListField(DefectDataDoc)
    enable = BooleanField(default=True)
