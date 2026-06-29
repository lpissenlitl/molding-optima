import logging
from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse

from mdprocess.views.rule_forms import (
    RuleKeywordSchema, 
    GetRuleKeywordListSchema, 
    RuleMethodSchema, 
    GetRuleMethodListSchema,
    RuleFlowSchema,
    NewDefectSchema
)
from mdprocess.services import rule_service


# 规则关键字列表
class RuleKeywordListView(BaseView):
    
    # 新增规则关键字
    @method_decorator(require_login)
    @method_decorator(validate_parameters(RuleKeywordSchema))
    def post(self, request, cleaned_data):
        return rule_service.add_rule_keyword(cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(GetRuleKeywordListSchema))
    def get(self, request, cleaned_data):
        total, rule_keywords = rule_service.get_list_of_rule_keyword(**cleaned_data)
        return PaginationResponse(total, rule_keywords)

    # 新增缺陷
    @method_decorator(require_login)
    @method_decorator(validate_parameters(NewDefectSchema))
    def put(self, request, cleaned_data):
        return rule_service.add_defect(cleaned_data)


# 规则关键字
class RuleKeywordDetailView(BaseView):

    @method_decorator(require_login)
    def get(self, request, rule_keyword_id):
        rule_keyword = rule_service.get_rule_keyword(rule_keyword_id)
        return rule_keyword

    @method_decorator(require_login)
    @method_decorator(validate_parameters(RuleKeywordSchema))
    def put(self, request, rule_keyword_id, cleaned_data):
        rule_service.update_rule_keyword(rule_keyword_id, cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, rule_keyword_id):
        rule_service.delete_rule_keyword(rule_keyword_id)


# 规则方法列表
class RuleMethodListView(BaseView):
    
    # 新增规则方法
    @method_decorator(require_login)
    @method_decorator(validate_parameters(RuleMethodSchema))
    def post(self, request, cleaned_data):
        return rule_service.add_rule_method(cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(GetRuleMethodListSchema))
    def get(self, request, cleaned_data):
        total, rules = rule_service.get_list_of_rule_method(**cleaned_data)
        return PaginationResponse(total, rules)
        
    @method_decorator(require_login)
    def delete(self, request, subrule_no):
        rule_service.delete_rule_method_by_no(subrule_no)


# 规则方法
class RuleMethodDetailView(BaseView):

    @method_decorator(require_login)
    def get(self, request, rule_id):
        rule = rule_service.get_rule_method(rule_id)
        return rule

    @method_decorator(require_login)
    @method_decorator(validate_parameters(RuleMethodSchema))
    def put(self, request, rule_id, cleaned_data):
        rule_service.update_rule_method(rule_id, cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, rule_id):
        rule_service.delete_rule_method(rule_id)


# 规则流程图
class RuleFlowView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(RuleFlowSchema))
    def get(self, request, cleaned_data):
        rule = rule_service.get_rule_flow(**cleaned_data)
        return rule

    @method_decorator(require_login)
    @method_decorator(validate_parameters(RuleFlowSchema))
    def post(self, request, cleaned_data):
        rule = rule_service.add_rule_flow(cleaned_data)
        return rule


class ImportRuleView(BaseView):

    @method_decorator(require_login)
    def post(self, request):
        return rule_service.import_rule(request)
