"""
molding-optima analytic 视图（聚合分析）

聚合分析接口（实时查询，按业务域拆分，便于后续扩展）：
- /api/analytic/process-statistics/        → 工艺统计聚合（trend + origin）
- /api/analytic/machine-statistics/        → 机器利用率（待扩展）
- /api/analytic/alarm-statistics/          → 报警趋势（待扩展）
- /api/analytic/quality-statistics/        → 缺陷分布（待扩展）

迁移记录：
- 2026-10-08 从 process app 迁出
  原 URL：/api/processes/statistics/dashboard/
  原归属：process.views.processes.DashboardStatisticsView
  中间站：dashboard.app（保留 1 小时，后改为 analytic）
  现 URL：/api/analytic/process-statistics/
  原因：analytic 是跨模块聚合分析，不属于工艺 CRUD 范畴；
        无 -s 后缀符合项目命名习惯
"""
from django.utils.decorators import method_decorator

from identity.decorators import require_login
from extensions.views import BaseView

from analytic.services import statistics


class ProcessStatisticsView(BaseView):
    """工艺统计聚合（近 30 天趋势 + 起源类型分布）

    GET /api/analytic/process-statistics/

    业务说明：
    - 一次返回 dashboard 全部图表所需数据，避免前端 N+1 查询
    - 多租户隔离：按当前用户 company_id 过滤
    - 数据来源：ProcessCondition（trend / origin_type）
    """

    @method_decorator(require_login)
    def get(self, request):
        return statistics.get_process_statistics(
            company_id=request.user.company_id,
            days=30,
        )