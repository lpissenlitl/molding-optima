"""
molding-optima reporting 视图（精简）
仅保留工艺相关的导出与报告生成入口。
"""
from django.utils.decorators import method_decorator

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView

from reporting.schemas import ProcessExportSchema, ProcessReportGenerateSchema
from reporting.services import process_export_service


class ProcessExportView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessExportSchema))
    def post(self, request, cleaned_data):
        """工艺参数导出（Excel）"""
        return process_export_service.export_process_parameters(
            tenant_slug=request.user.company.tenant_slug,
            **cleaned_data,
        )


class ProcessReportGenerateView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessReportGenerateSchema))
    def post(self, request, cleaned_data):
        """工艺报告生成（PDF/DOCX）"""
        return process_export_service.generate_process_report(
            tenant_slug=request.user.company.tenant_slug,
            **cleaned_data,
        )