"""专家规则（ExpertRule）视图层

API 路径：
- GET    /api/processes/rule-libraries/<lib_id>/expert-rules/    库下专家规则列表
- POST   /api/processes/rule-libraries/<lib_id>/expert-rules/    新建专家规则
- GET    /api/processes/expert-rules/<id>/                       专家规则详情
- PATCH  /api/processes/expert-rules/<id>/                       更新专家规则
- DELETE /api/processes/expert-rules/<id>/                       删除专家规则

权限说明：
- 专家规则属于平台级内部规则（工艺参数初始化系数），不向租户暴露
- 仅 superuser 可访问
"""
from django.utils.decorators import method_decorator

from extensions.decorators import validate_parameters
from extensions.schemas import PaginationBaseSchema
from extensions.views import BaseView, PaginationResponse
from identity.decorators import require_login, require_superuser

from process.services import rule_service


@method_decorator(require_superuser, name="dispatch")
class ExpertRuleListByLibraryView(BaseView):
    """专家规则列表（按库过滤）"""

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, rule_library_id, cleaned_data):
        result = rule_service.get_list_of_expert_rule(
            rule_library_id=rule_library_id,
            **cleaned_data,
        )
        return PaginationResponse(total=result["total"], items=result["items"])

    @method_decorator(require_superuser)
    def post(self, request, rule_library_id):
        return rule_service.add_expert_rule(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            rule_library_id=rule_library_id,
            **request.DATA,
        )


@method_decorator(require_superuser, name="dispatch")
class ExpertRuleDetailView(BaseView):
    """专家规则详情"""

    def get(self, request, expert_rule_id):
        return rule_service.get_expert_rule(expert_rule_id)

    def patch(self, request, expert_rule_id):
        return rule_service.update_expert_rule(
            expert_rule_id,
            company_id=request.user.company_id,
            **request.DATA,
        )

    def delete(self, request, expert_rule_id):
        rule_service.delete_expert_rule(
            expert_rule_id,
            company_id=request.user.company_id,
        )
