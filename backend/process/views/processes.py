"""
molding-optima 工艺参数视图
"""
from django.utils.decorators import method_decorator
from django.db import transaction

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView

from process.schemas import (
    ProcessConditionSchema,
    ProcessParameterSchema,
    ProcessConditionAndParameterSchema,
    ProcessParameterListSchema,
    BatchDeleteProcessParameterSchema,
)
from process.services import process_service


# ==================== 工艺条件与参数 ====================

class ProcessConditionListView(BaseView):
    """工艺条件列表"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        return process_service.get_process_condition_list(**cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionSchema))
    def post(self, request, cleaned_data):
        return process_service._create_process_condition(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **cleaned_data,
        )


class ProcessConditionDetailView(BaseView):
    """工艺条件详情"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return process_service.get_process_parameter(condition_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionSchema))
    def put(self, request, condition_id, cleaned_data):
        return process_service.update_process_condition(condition_id, **cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, condition_id):
        process_service.soft_delete_process_condition(condition_id)


class ProcessParameterCreateView(BaseView):
    """工艺参数创建"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def post(self, request, cleaned_data):
        return process_service.create_process_parameter(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **cleaned_data,
        )


class ProcessParameterListView(BaseView):
    """工艺参数列表"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        return process_service.get_process_parameter_list(**cleaned_data)


class ProcessParameterDetailView(BaseView):
    """工艺参数详情/更新/删除"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def put(self, request, parameter_id, cleaned_data):
        return process_service.update_process_parameter(parameter_id, **cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, parameter_id):
        process_service.delete_process_parameter(parameter_id)


class ProcessParameterBatchDeleteView(BaseView):
    """工艺参数批量删除"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteProcessParameterSchema))
    def post(self, request, cleaned_data):
        return process_service.batch_delete_process_parameter(cleaned_data["ids"])


class ProcessConditionAndParameterCreateView(BaseView):
    """一次性创建工艺条件及参数"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionAndParameterSchema))
    def post(self, request, cleaned_data):
        condition_data = cleaned_data["condition"]
        parameter_data = cleaned_data["parameter"]

        with transaction.atomic():
            condition = process_service._create_process_condition(
                company_id=request.user.company_id,
                organization_id=request.user.organization_id,
                **condition_data,
            )
            parameter_data["process_condition_id"] = condition.id
            parameter = process_service.create_process_parameter(
                company_id=request.user.company_id,
                organization_id=request.user.organization_id,
                **parameter_data,
            )

        return {
            "condition": condition.to_dict(),
            "parameter": parameter.to_dict(),
        }


# ==================== 工艺优化 / 调优 / 移植 ====================
# 注：ProcessIndex 已合并到 ProcessCondition（所有非关键文本字段存到 process_context_snapshot JSON）

from process.services import (
    process_record_service,
    process_transplant_service,
    process_expert_service,
    process_optimize_service,
    rule_service,
)
from extensions.schemas import (
    PaginationBaseSchema,
    BatchIdsSchema,
)


class ProcessTransplantView(BaseView):
    """工艺参数移植"""

    @method_decorator(require_login)
    def post(self, request):
        return process_transplant_service.transplant_process_parameter(
            source_parameter_id=request.DATA.get("source_parameter_id"),
            target_machine_spec=request.DATA.get("target_machine_spec"),
        )


class ProcessOptimizationView(BaseView):
    """工艺优化（基于规则匹配）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return process_optimize_service.get_process_optimization(condition_id)

    @method_decorator(require_login)
    def post(self, request):
        """
        请求体：
        {
            "condition_id": int,
            "target_defect": "短射"  # 可选
        }
        """
        return process_optimize_service.add_process_optimization(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            condition_id=request.DATA.get("condition_id"),
            target_defect=request.DATA.get("target_defect"),
        )

    @method_decorator(require_login)
    def put(self, request, condition_id):
        return process_optimize_service.update_process_optimization(
            condition_id, **request.DATA,
        )


class ProcessOptimizationHistoryView(BaseView):
    """工艺优化历史"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return process_optimize_service.get_optimization_history(condition_id)


# ==================== 专家调优 ====================

class ProcessExpertSuggestionView(BaseView):
    """专家调优建议（基于缺陷反馈 + 规则匹配）"""

    @method_decorator(require_login)
    def post(self, request):
        """
        请求体：
        {
            "condition_id": int,
            "defect_feedback": { "B000": "level", "B001": "position", "B002": "feedback", ... }
        }
        """
        return process_expert_service.suggest_expert_adjustment(
            condition_id=request.DATA.get("condition_id"),
            defect_feedback=request.DATA.get("defect_feedback"),
        )


class ProcessExpertDefectTemplateView(BaseView):
    """缺陷类型模板"""

    @method_decorator(require_login)
    def get(self, request):
        return process_expert_service.get_defect_template()


class ProcessExpertCreateView(BaseView):
    """创建专家调优记录"""

    @method_decorator(require_login)
    def post(self, request):
        return process_expert_service.create_expert_optimization(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


# ==================== 规则管理 ====================

class RuleKeywordListView(BaseView):
    """规则关键字列表"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        return rule_service.get_list_of_rule_keyword(**cleaned_data)

    @method_decorator(require_login)
    def post(self, request):
        return rule_service.add_rule_keyword(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


class RuleKeywordDetailView(BaseView):
    """规则关键字详情"""

    @method_decorator(require_login)
    def get(self, request, rule_keyword_id):
        return rule_service.get_rule_keyword(rule_keyword_id)

    @method_decorator(require_login)
    def put(self, request, rule_keyword_id):
        return rule_service.update_rule_keyword(rule_keyword_id, **request.DATA)

    @method_decorator(require_login)
    def delete(self, request, rule_keyword_id):
        rule_service.delete_rule_keyword(rule_keyword_id)


class RuleMethodListView(BaseView):
    """规则方法列表"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        return rule_service.get_list_of_rule_method(**cleaned_data)

    @method_decorator(require_login)
    def post(self, request):
        return rule_service.add_rule_method(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


class RuleMethodDetailView(BaseView):
    """规则方法详情"""

    @method_decorator(require_login)
    def get(self, request, rule_method_id):
        return rule_service.get_rule_method(rule_method_id)

    @method_decorator(require_login)
    def put(self, request, rule_method_id):
        return rule_service.update_rule_method(rule_method_id, **request.DATA)

    @method_decorator(require_login)
    def delete(self, request, rule_method_id):
        rule_service.delete_rule_method(rule_method_id)


class RuleByDefectView(BaseView):
    """根据缺陷名获取规则（query: defect_name）"""

    @method_decorator(require_login)
    def get(self, request):
        defect_name = request.GET.get("defect_name")
        if not defect_name:
            return []
        return rule_service.get_rules_by_defect(defect_name)