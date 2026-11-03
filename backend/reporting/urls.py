"""
molding-optima reporting URL（精简）
注册工艺导出接口、列表导出接口与导出文件下载接口。
"""
from django.urls import path, re_path

from .views import (
    ExportListView,
    ProcessExportView,
    ProcessReportGenerateView,
    ReportDownloadView,
)


urlpatterns = [
    # --- 列表导出（生成 Excel，返回下载地址）---
    path("reports/export-list/", ExportListView.as_view(), name="reporting-export-list"),
    # --- 导出文件下载（路径含斜杠，用 re_path 捕获）---
    re_path(r"^reports/download/(?P<path>.+)/$", ReportDownloadView.as_view(), name="reporting-download"),
    # --- 工艺相关 ---
    path("process/export/", ProcessExportView.as_view(), name="reporting-process-export"),
    path("process/report/", ProcessReportGenerateView.as_view(), name="reporting-process-report"),
]
