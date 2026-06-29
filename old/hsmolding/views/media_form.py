from marshmallow import fields

from gis.common.django_ext.forms import (
    BaseSchema,
    PaginationBaseSchema,
    CNDatetimeField,
)


class ListMediaUrlSchema(BaseSchema):
    search_id = fields.Integer(required=False, allow_none=True)
    search_type = fields.String(required=False, allow_none=True)
    file_url = fields.String(required=False, allow_none=True)
    