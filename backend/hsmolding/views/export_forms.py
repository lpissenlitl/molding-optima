from marshmallow import fields

from gis.common.django_ext.forms import (
    BaseSchema,
)


# 导出测试详情--export_testing_form
class ExportTestingReportSchema(BaseSchema):
    testing_id = fields.Integer()
    production_department = fields.String(required=False, allow_none=True)
    report_template = fields.Integer(required=False, allow_none=True)
    company_id = fields.Integer(required=False, allow_none=True)
    