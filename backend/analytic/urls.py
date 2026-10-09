"""
molding-optima analytic URL 路由

聚合分析接口（实时查询）：
- /api/analytic/process-statistics/        → 工艺统计聚合（trend + origin）

与 reporting app 区别：
- reporting：离线文档生成（Excel/PDF/DOCX）
- analytic：实时聚合查询（dashboard / KPI / chart）
"""
from django.urls import path

from .views import ProcessStatisticsView


urlpatterns = [
    path("analytic/process-statistics/", ProcessStatisticsView.as_view(), name="analytic-process-statistics"),
]