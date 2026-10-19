"""规则中心 v2 视图层

URL 段 (4 类资源对称, 全部为 list + detail):
- rules/keywords/        规则关键词 (基础字典)
- rule-libraries/        规则库
- rule-methods/          规则方法 (缺陷→参数调整, query 过滤 library)
- expert-rules/          专家规则 (初始化系数, superuser, query 过滤 library)
- rules/by-defect/       按缺陷查规则 (业务功能)

权限:
- keyword / library / method: require_login
- expert_rule: require_superuser
"""
from django.utils.decorators import method_decorator

from extensions.decorators import validate_parameters
from extensions.schemas import PaginationBaseSchema
from extensions.views import BaseView, PaginationResponse
from identity.decorators import require_login, require_superuser

from process.services import rule


# ----- 规则关键词 (rules/keywords) -----

@method_decorator(require_login, name="dispatch")
class RuleKeywordListView(BaseView):
    """规则关键字列表 / 创建"""

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        result = rule.get_list_of_rule_keyword(
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
            **cleaned_data,
        )
        return PaginationResponse(total=result["total"], items=result["items"])

    @method_decorator(require_login)
    def post(self, request):
        return rule.add_rule_keyword(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


@method_decorator(require_login, name="dispatch")
class RuleKeywordDetailView(BaseView):
    """规则关键字详情 / 更新 / 删除"""

    def get(self, request, rule_keyword_id):
        return rule.get_rule_keyword(rule_keyword_id)

    def put(self, request, rule_keyword_id):
        return rule.update_rule_keyword(rule_keyword_id, **request.DATA)

    def delete(self, request, rule_keyword_id):
        rule.delete_rule_keyword(rule_keyword_id)


# ----- 规则库 (rule-libraries) -----

@method_decorator(require_login, name="dispatch")
class RuleLibraryListView(BaseView):
    """规则库列表 / 创建"""

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        # 默认按当前用户公司过滤；平台超管未接管时可看全部（已接管则跟租户走）
        result = rule.get_list_of_rule_library(
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
            **cleaned_data,
        )
        return PaginationResponse(total=result["total"], items=result["items"])

    @method_decorator(require_login)
    def post(self, request):
        return rule.add_rule_library(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


@method_decorator(require_login, name="dispatch")
class RuleLibraryDetailView(BaseView):
    """规则库详情"""

    def get(self, request, rule_library_id):
        return rule.get_rule_library(rule_library_id)

    def patch(self, request, rule_library_id):
        return rule.update_rule_library(
            rule_library_id,
            company_id=request.user.company_id,
            **request.DATA,
        )

    def delete(self, request, rule_library_id):
        rule.delete_rule_library(
            rule_library_id,
            company_id=request.user.company_id,
        )


# ----- 规则方法 (rule-methods, 独立资源, 不嵌套) -----
# GET 可选 query: rule_library_id  按库过滤
# POST 必填 body: rule_library_id    (service 层校验)

@method_decorator(require_login, name="dispatch")
class RuleMethodListView(BaseView):
    """规则方法列表 / 创建

    GET 可选 query:
    - defect_code  按缺陷查询所有启用的规则 (业务功能, 不分页)
    - rule_library_id  按库过滤
    - 其余分页参数 page_no / page_size / sort
    """

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        defect_code = request.GET.get("defect_code")
        if defect_code:
            # 业务功能: 按缺陷查所有启用的规则, 不分页
            cleaned_data["defect_code"] = defect_code
            cleaned_data["is_active"] = True
            cleaned_data["page_size"] = 9999
        rule_library_id = request.GET.get("rule_library_id")
        if rule_library_id:
            cleaned_data["rule_library_id"] = int(rule_library_id)
        result = rule.get_list_of_rule_method(**cleaned_data)
        return PaginationResponse(total=result["total"], items=result["items"])

    @method_decorator(require_login)
    def post(self, request):
        return rule.add_rule_method(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


@method_decorator(require_login, name="dispatch")
class RuleMethodDetailView(BaseView):
    """规则方法详情"""

    def get(self, request, rule_method_id):
        return rule.get_rule_method(rule_method_id)

    def patch(self, request, rule_method_id):
        return rule.update_rule_method(rule_method_id, **request.DATA)

    def delete(self, request, rule_method_id):
        rule.delete_rule_method(rule_method_id)


# ----- 专家规则 (expert-rules, 独立资源, superuser) -----
# GET 可选 query: rule_library_id  按库过滤
# POST 必填 body: rule_library_id    (service 层校验)

@method_decorator(require_superuser, name="dispatch")
class ExpertRuleListView(BaseView):
    """专家规则列表 / 创建"""

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        rule_library_id = request.GET.get("rule_library_id")
        if rule_library_id:
            cleaned_data["rule_library_id"] = int(rule_library_id)
        result = rule.get_list_of_expert_rule(**cleaned_data)
        return PaginationResponse(total=result["total"], items=result["items"])

    @method_decorator(require_superuser)
    def post(self, request):
        return rule.add_expert_rule(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


@method_decorator(require_superuser, name="dispatch")
class ExpertRuleDetailView(BaseView):
    """专家规则详情"""

    def get(self, request, expert_rule_id):
        return rule.get_expert_rule(expert_rule_id)

    def patch(self, request, expert_rule_id):
        return rule.update_expert_rule(
            expert_rule_id,
            company_id=request.user.company_id,
            **request.DATA,
        )

    def delete(self, request, expert_rule_id):
        rule.delete_expert_rule(
            expert_rule_id,
            company_id=request.user.company_id,
        )
