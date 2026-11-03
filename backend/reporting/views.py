"""
molding-optima reporting 视图（精简）
仅保留工艺相关的导出与报告生成入口，以及列表导出/下载入口。
"""
import os

from django.http import FileResponse
from django.utils.decorators import method_decorator

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView

from reporting.schemas import ExportListSchema, ProcessExportSchema, ProcessReportGenerateSchema
from reporting.services import process_export_service
from reporting.services import list_export_service
from reporting.utils import resolve_export_list_file


# Excel 文件 MIME 类型
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ProcessExportView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessExportSchema))
    def post(self, request, cleaned_data):
        """工艺参数导出（Excel）"""
        return process_export_service.export_process_parameters(
            company_id=request.user.company_id,
            tenant_slug=request.user.company.tenant_slug,
            **cleaned_data,
        )


class ProcessReportGenerateView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessReportGenerateSchema))
    def post(self, request, cleaned_data):
        """工艺报告生成（PDF/DOCX）"""
        return process_export_service.generate_process_report(
            company_id=request.user.company_id,
            tenant_slug=request.user.company.tenant_slug,
            **cleaned_data,
        )


class ExportListView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ExportListSchema))
    def post(self, request, cleaned_data):
        """列表数据导出（Excel），返回下载地址"""
        return list_export_service.export_list(
            company_id=request.user.company_id,
            tenant_slug=request.user.company.tenant_slug,
            **cleaned_data,
        )


class ReportDownloadView(BaseView):
    @method_decorator(require_login)
    def get(self, request, path):
        """导出文件下载（Excel）"""
        file_path = resolve_export_list_file(
            tenant_slug=request.user.company.tenant_slug,
            relative_path=path,
        )
        return FileResponse(
            open(file_path, "rb"),
            content_type=XLSX_CONTENT_TYPE,
            as_attachment=True,
            filename=os.path.basename(file_path),
        )