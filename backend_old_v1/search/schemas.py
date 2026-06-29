from marshmallow import fields
from extensions.schemas import BaseSchema


class SearchConditionSchema(BaseSchema):
    """查询条件"""
    table = fields.String(required=True, allow_none=True)
    column = fields.String(required=True, allow_none=True)
    input = fields.String(required=True, allow_none=True)
    with_id = fields.Boolean(load_default=False, allow_none=True)
    limit = fields.Integer(load_default=100, allow_none=True)
    filter_columns = fields.Dict(required=False, allow_none=True)
    sub_column = fields.String(required=False, allow_none=True)
