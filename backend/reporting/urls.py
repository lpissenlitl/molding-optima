"""
molding-optima reporting URL（精简）
仅注册工艺相关的导出接口。
"""
from django.urls import path

from .views import ProcessExportView, ProcessReportGenerateView


urlpatterns = [
    path("process/export/", ProcessExportView.as_view(), name="reporting-process-export"),
    path("process/report/", ProcessReportGenerateView.as_view(), name="reporting-process-report"),
]