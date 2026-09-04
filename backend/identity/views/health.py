"""
服务健康检查接口

设计要点：
- 无需鉴权（@login_not_required）：让前端在登录前就能探测后端可用性
- 不查数据库：不依赖任何业务数据，纯响应式返回
- 极轻量：仅返回 { status, service }，用于登录页 status 指示器
- 失败语义：接口本身只返回"服务在线"。数据库挂了不影响此接口 200 响应。
  真实业务可用性由各业务接口自己保证（出现 5xx 时前端感知）。
"""
from extensions.views import BaseView


class HealthView(BaseView):
    """GET /api/health/ — 服务健康检查（公开接口）"""

    def get(self, request):
        return {
            "status": "ok",
            "service": "molding-optima",
        }
