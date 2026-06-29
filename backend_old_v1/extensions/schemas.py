import re
from marshmallow import fields, Schema, validates, ValidationError, EXCLUDE
from marshmallow.validate import Length, Range, And



class AbstractBaseSchema(Schema):
    """替代marshmallow.Schema基类"""
    pass


class TracedSchema(AbstractBaseSchema):
    """跟踪字段Schema基类"""
    created_at = fields.DateTime(dump_only=True, metadata={"description": "创建时间"})
    updated_at = fields.DateTime(dump_only=True, metadata={"description": "更新时间"})
    

class BaseSchema(TracedSchema):
    """通用Schema基类"""
    is_deleted = fields.Boolean(dump_only=True, metadata={"description": "是否删除"})
    deleted_at = fields.DateTime(dump_only=True, metadata={"description": "删除时间"})

    class Meta:
        unknown = EXCLUDE


class PaginationBaseSchema(Schema):
    """分页接口参数基类检查器"""
    page_no = fields.Integer(
        load_default=1,
        validate=And(
            Range(min=1, error="页码必须大于0")
        ),
        metadata={"description": "页码"}
    )
    page_size = fields.Integer(
        load_default=30,
        validate=And(
            Range(min=1, max=1000, error="每页数量必须在 1-1000 之间")
        ),
        metadata={"description": "每页数量"}
    )
    sort = fields.String(
        allow_none=True, 
        metadata={
            "排序规则。格式：'+字段' 升序，'-字段' 降序。"
            "多字段用逗号分隔，如 '+username,-age'。"
            "传 null 或空字符串表示不排序。"
            "不传此参数则默认按 id 倒序。"
        }
    )

    @validates("sort")
    def validate_sort(self, value, **kwargs):
        """验证排序参数，支持 null/空字符串（不排序）和格式化字符串"""
        if value is None or value == "":
            return
        
        if not isinstance(value, str):  # 验证格式
            raise ValidationError("排序参数必须是字符串或 null")
        
        pattern = r'^[+-]?[\w]+(,\s*[+-]?[\w]+)*$'
        if not re.match(pattern, value.strip()):  # 验证格式
            raise ValidationError(
                "排序参数格式无效。示例：'+username' 或 '+username,-age'。"
                "字段名仅含字母、数字、下划线，不可用逗号结尾或开头。"
            )


class BatchIdsSchema(Schema):
    """通用批量操作Schema：仅包含ID列表"""
    ids = fields.List(
        fields.Integer(), 
        required=True, 
        validate=Length(min=1, max=1000),
        metadata={"description": "ID列表"}
    )


class BatchDeleteSchema(BatchIdsSchema):
    """通用批量删除Schema：仅包含ID列表"""
    pass


class StripStrField(fields.String):
    """去除字符串首尾空字符"""
    def _deserialize(self, value, attr, data, **kwargs):
        stripped_str = super()._deserialize(value, attr, data, **kwargs).strip()
        if self.required and stripped_str == "":
            raise ValidationError("不能为空字符串")
        return stripped_str
    