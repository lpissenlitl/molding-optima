from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema

class YizumiMesTransfer(BaseSchema):
    machine_id = fields.Integer(required=False, allow_none=True)
    