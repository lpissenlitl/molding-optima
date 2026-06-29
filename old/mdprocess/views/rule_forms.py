from marshmallow import fields
from gis.common.django_ext.forms import BaseSchema, PaginationBaseSchema, CNDatetimeField


class RuleKeywordSchema(BaseSchema):
    id = fields.Integer(blank=True, null=True, allow_none=True)
    name = fields.String(max_length=20, null=True, allow_none=True)  # 关键字的名字
    level = fields.Integer(blank=True, default=0, allow_none=True)  # 模糊级别：3或5
    all_range_min = fields.Integer(blank=True, null=True, allow_none=True)  # 参数取值范围最小值
    all_range_max = fields.Integer(blank=True, null=True, allow_none=True)  # 参数取值范围最大值
    action_range_min = fields.Integer(blank=True, null=True, allow_none=True)  # 参数调整区间最小值
    action_range_max = fields.Integer(blank=True, null=True, allow_none=True)  # 参数调整区间最大值
    action_max_val = fields.Integer(blank=True, null=True, allow_none=True)  # 参数调整最大值
    keyword_type = fields.String(max_length=20, null=True, allow_none=True)  # 关键词类型
    comment = fields.String(max_length=20, null=True, allow_none=True)  # 注释

    subrule_no = fields.String(max_length=45, null=True, allow_none=True)
    product_small_type = fields.String(max_length=45, null=True, allow_none=True)
    polymer_abbreviation = fields.String(max_length=45, null=True, allow_none=True)
    rule_type = fields.String(max_length=45, null=True, allow_none=True)
    show_on_page = fields.Boolean(null=True, allow_none=True)

    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer(required=False, allow_none=True)


class GetRuleKeywordListSchema(PaginationBaseSchema):
    name = fields.String(max_length=20, null=True)  # 关键字的名字
    keyword_type = fields.String(max_length=20, null=True)  # 类型
    page_no = fields.Integer(blank=True, default=1) 
    page_size = fields.Integer(blank=True, default=30) 
    rule_type = fields.String(max_length=45, null=True, allow_none=True)
    subrule_no = fields.String(max_length=45, null=True, allow_none=True)
    polymer_abbreviation = fields.String(max_length=45, null=True, allow_none=True)
    product_small_type = fields.String(max_length=45, null=True, allow_none=True)
    show_on_page = fields.Boolean(null=True, allow_none=True)

    
class RuleMethodSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    polymer_abbreviation = fields.String(max_length=45, null=True, allow_none=True)
    product_small_type = fields.String(max_length=45, null=True, allow_none=True)
    rule_description = fields.String(max_length=500, null=True, allow_none=True)
    rule_explanation = fields.String(max_length=500, null=True, allow_none=True)

    is_auto = fields.Integer(required=False, allow_none=True)
    enable = enable = fields.Integer(required=False, allow_none=True)

    defect_name = fields.String(max_length=45, null=True, allow_none=True)
    defect_desc = fields.String(max_length=45, null=True, allow_none=True)
    rule_type = fields.String(max_length=45, null=True, allow_none=True)
    subrule_no = fields.String(max_length=45, null=True, allow_none=True)
    
    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer(required=False, allow_none=True)

    priority = fields.Float(required=False, allow_none=True)


class GetRuleMethodListSchema(PaginationBaseSchema):
    polymer_abbreviation = fields.String(max_length=45, null=True, allow_none=True)
    product_small_type = fields.String(max_length=45, null=True, allow_none=True)
    is_auto = fields.Integer(null=True)  # 自动规则
    enable = fields.Integer(null=True)  # 启用
    page_no = fields.Integer(blank=True, default=1) 
    page_size = fields.Integer(blank=True, default=30)
    defect_name = fields.String(max_length=45, null=True, allow_none=True)
    defect_desc = fields.String(max_length=45, null=True, allow_none=True)
    rule_type = fields.String(max_length=45, null=True, allow_none=True)
    subrule_no = fields.String(max_length=45, null=True, allow_none=True)
    rule_description = fields.String(max_length=45, null=True, allow_none=True)
    rule_explanation = fields.String(max_length=45, null=True, allow_none=True)


class PropertySchema(BaseSchema):
    rule_name = fields.String(max_length=45, null=True, allow_none=True)
    action = fields.String(max_length=45, null=True, allow_none=True)


class NodeSchema(BaseSchema):
    id = fields.String(max_length=45, null=True, allow_none=True)
    type = fields.String(max_length=45, null=True, allow_none=True)
    x = fields.Integer(required=False, allow_none=True)
    y = fields.Integer(required=False, allow_none=True)
    text = fields.String(max_length=45, null=True, allow_none=True)
    properties = fields.Nested(PropertySchema)


class PostionSchema(BaseSchema):
    x = fields.Integer(required=False, allow_none=True)
    y = fields.Integer(required=False, allow_none=True)


class EdgeSchema(BaseSchema):
    sourceNodeId = fields.String(max_length=45, null=True, allow_none=True)
    targetNodeId = fields.String(max_length=45, null=True, allow_none=True)
    type = fields.String(max_length=45, null=True, allow_none=True)
    text = fields.String(max_length=45, null=True, allow_none=True)
    pointsList = fields.Nested(PostionSchema, many=True)


class GraphDataSchema(BaseSchema):
    nodes = fields.Nested(NodeSchema, many=True)
    edges = fields.Nested(EdgeSchema, many=True)


class SolutionsSchema(BaseSchema):
    conditiontype = fields.String(max_length=45, null=True, allow_none=True)  # "结论"
    keyword = fields.String(max_length=45, null=True, allow_none=True)  # "储料量"
    describe = fields.String(max_length=45, null=True, allow_none=True)  # "MEL"
    action = fields.String(max_length=45, null=True, allow_none=True)  # "增大"
    action_key = fields.String(max_length=45, null=True, allow_none=True)  # "add"


class PreconditionsSchema(BaseSchema):
    conditiontype = fields.String(max_length=45, null=True, allow_none=True)  # "检查VP切换位置"
    keyword = fields.String(max_length=45, null=True, allow_none=True)  # "储料量"
    describe = fields.String(max_length=45, null=True, allow_none=True)  # "MEL"
    status = fields.String(max_length=45, null=True, allow_none=True)  # "不足"
    solutions = fields.Nested(SolutionsSchema, many=True)


class RuleMethodDetailSchema(BaseSchema):
    total_pre_num = fields.Integer(null=True, allow_none=True)
    preconditions = fields.Nested(PreconditionsSchema, many=True)
    total_solution_num = fields.Integer(null=True, allow_none=True)
    sub_solution_num_list = fields.List(fields.Integer(null=True, allow_none=True))
    solution_ways = fields.List(fields.List(fields.Integer(null=True, allow_none=True)))


class DefectDataSchema(BaseSchema):
    defect_name = fields.String(max_length=45, null=True, allow_none=True)  # 如短射
    defect_desc = fields.String(max_length=45, null=True, allow_none=True)  # 如SHORTSHOT
    graph_data = fields.Nested(GraphDataSchema)
    rule_method = fields.Nested(RuleMethodDetailSchema)


class RuleFlowSchema(BaseSchema):
    rule_library = fields.String(max_length=45, null=True, allow_none=True)  # 基础库, 或 R20220609163348
    rule_type = fields.String(max_length=45, null=True, allow_none=True)  # 基础库, 或 子规则库
    product_small_type = fields.String(max_length=45, null=True, allow_none=True)  # 制品
    polymer_abbreviation = fields.String(max_length=45, null=True, allow_none=True)  # 塑料
    defect_data = fields.Nested(DefectDataSchema, many=True)
    enable = fields.Boolean(null=True, allow_none=True)


class GetRuleSchema(BaseSchema):
    flag = fields.String()
    subrule_no = fields.String()


class NewDefectSchema(BaseSchema):
    rule_keyword = fields.Nested(RuleKeywordSchema)
    refer_defect = fields.String(max_length=45, null=True, allow_none=True)
    previous_length = fields.Integer(null=True, allow_none=True)
