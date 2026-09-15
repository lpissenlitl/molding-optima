"""规则方法（RuleMethod）视图层

API 路径：
- GET    /api/processes/rule-libraries/<lib_id>/methods/    库下规则方法列表（按库过滤）
- POST   /api/processes/rule-libraries/<lib_id>/methods/    新建规则方法
- GET    /api/processes/rule-methods/<id>/                  规则方法详情
- PATCH  /api/processes/rule-methods/<id>/                  更新规则方法
- DELETE /api/processes/rule-methods/<id>/                  删除规则方法
"""
from django.utils.decorators import method_decorator

from extensions.decorators import validate_parameters
from extensions.schemas import PaginationBaseSchema
from extensions.views import BaseView, PaginationResponse
from identity.decorators import require_login

from process.services import rule_service


@method_decorator(require_login, name="dispatch")
class RuleMethodListByLibraryView(BaseView):
    """规则方法列表（按库过滤）"""

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, rule_library_id, cleaned_data):
        result = rule_service.get_list_of_rule_method(
            rule_library_id=rule_library_id,
            **cleaned_data,
        )
        return PaginationResponse(total=result["total"], items=result["items"])

    @method_decorator(require_login)
    def post(self, request, rule_library_id):
        # 把 rule_library_id 注入到 params，避免前端忘记传
        params = dict(request.DATA)
        params["rule_library_id"] = rule_library_id
        return rule_service.add_rule_method(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **params,
        )


@method_decorator(require_login, name="dispatch")
class RuleMethodDetailView(BaseView):
    """规则方法详情"""

    def get(self, request, rule_method_id):
        return rule_service.get_rule_method(rule_method_id)

    def patch(self, request, rule_method_id):
        return rule_service.update_rule_method(rule_method_id, **request.DATA)

    def delete(self, request, rule_method_id):
        rule_service.delete_rule_method(rule_method_id)
