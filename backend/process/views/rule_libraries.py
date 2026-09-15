"""规则库（RuleLibrary）视图层

API 路径：
- GET    /api/processes/rule-libraries/                 规则库列表（带规则数量统计）
- POST   /api/processes/rule-libraries/                 新建规则库
- GET    /api/processes/rule-libraries/<id>/            规则库详情
- PATCH  /api/processes/rule-libraries/<id>/            更新规则库
- DELETE /api/processes/rule-libraries/<id>/            删除规则库（级联软删除）

隔离规则：
- 列表默认按当前用户的 company_id 过滤
- 系统库（owner_type=system）不可更新/删除
"""
from django.utils.decorators import method_decorator

from extensions.decorators import validate_parameters
from extensions.schemas import PaginationBaseSchema
from extensions.views import BaseView, PaginationResponse
from identity.decorators import require_login

from process.services import rule_service


@method_decorator(require_login, name="dispatch")
class RuleLibraryListView(BaseView):
    """规则库列表（卡片视图数据源）"""

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        # 默认按当前用户公司过滤；平台超管未接管时可看全部（已接管则跟租户走）
        result = rule_service.get_list_of_rule_library(
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
            **cleaned_data,
        )
        return PaginationResponse(total=result["total"], items=result["items"])

    @method_decorator(require_login)
    def post(self, request):
        return rule_service.add_rule_library(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


@method_decorator(require_login, name="dispatch")
class RuleLibraryDetailView(BaseView):
    """规则库详情"""

    def get(self, request, rule_library_id):
        return rule_service.get_rule_library(rule_library_id)

    def patch(self, request, rule_library_id):
        return rule_service.update_rule_library(
            rule_library_id,
            company_id=request.user.company_id,
            **request.DATA,
        )

    def delete(self, request, rule_library_id):
        rule_service.delete_rule_library(
            rule_library_id,
            company_id=request.user.company_id,
        )
