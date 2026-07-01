"""
molding-optima 工艺参数视图（对齐 molding-expert）
"""
from django.utils.decorators import method_decorator
from django.db import transaction

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView

from process.schemas import (
    ProcessParameterSchema,
    ProcessParameterListSchema,
    BatchDeleteProcessParameterSchema,
    ProcessInitializationSchema,
    InitializationFromIdsSchema,
)
from process.services import condition_service


# ==================== 工艺参数（对齐 molding-expert 4-16）====================

class ProcessParameterListView(BaseView):
    """工艺参数列表"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        return condition_service.get_process_parameter_list(**cleaned_data)


class ProcessParameterCreateView(BaseView):
    """工艺参数前端创建（对齐 molding-expert /parameter/frontend/）"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def post(self, request, cleaned_data):
        return condition_service.create_process_parameter(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **cleaned_data,
        )


class ProcessParameterDetailView(BaseView):
    """工艺参数详情/更新/删除（对齐 molding-expert /parameter/<condition_id>/）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition_service.get_process_parameter(condition_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def put(self, request, condition_id, cleaned_data):
        return condition_service.update_process_parameter(condition_id, **cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, condition_id):
        condition_service.delete_process_parameter(condition_id)


class ProcessParameterFlatView(BaseView):
    """工艺参数扁平视图（对齐 molding-expert /parameter/<id>/flat/）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition_service.get_process_parameter_flat(condition_id)


class ProcessParameterFrontendView(BaseView):
    """工艺参数前端视图（对齐 molding-expert /parameter/<id>/frontend/）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition_service.get_process_parameter_frontend(condition_id)


class ProcessParameterBatchDeleteView(BaseView):
    """工艺参数批量删除"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteProcessParameterSchema))
    def post(self, request, cleaned_data):
        return condition_service.batch_delete_process_parameter(cleaned_data["ids"])


# ==================== 工艺移植 ====================

from process.services import (
    record_service,
    transplant_service,
    expert_service,
    optimize_service,
    rule_service,
    initialization_service,
)
from extensions.schemas import (
    PaginationBaseSchema,
    BatchIdsSchema,
)


class ProcessTransplantView(BaseView):
    """工艺参数移植（对齐 molding-expert /parameter/transplant/）"""

    @method_decorator(require_login)
    def post(self, request):
        return transplant_service.transplant_process_parameter(
            source_parameter_id=request.DATA.get("source_parameter_id"),
            target_machine_spec=request.DATA.get("target_machine_spec"),
        )


class ProcessOptimizationView(BaseView):
    """工艺优化（基于规则匹配）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return optimize_service.get_process_optimization(condition_id)

    @method_decorator(require_login)
    def post(self, request):
        """
        请求体：
        {
            "condition_id": int,
            "target_defect": "短射"  # 可选
        }
        """
        return optimize_service.add_process_optimization(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            condition_id=request.DATA.get("condition_id"),
            target_defect=request.DATA.get("target_defect"),
        )

    @method_decorator(require_login)
    def put(self, request, condition_id):
        return optimize_service.update_process_optimization(
            condition_id, **request.DATA,
        )


class ProcessOptimizationHistoryView(BaseView):
    """工艺优化历史"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return optimize_service.get_optimization_history(condition_id)


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
        return expert_service.suggest_expert_adjustment(
            condition_id=request.DATA.get("condition_id"),
            defect_feedback=request.DATA.get("defect_feedback"),
        )


class ProcessExpertDefectTemplateView(BaseView):
    """缺陷类型模板"""

    @method_decorator(require_login)
    def get(self, request):
        return expert_service.get_defect_template()


class ProcessExpertCreateView(BaseView):
    """创建专家调优记录"""

    @method_decorator(require_login)
    def post(self, request):
        return expert_service.create_expert_optimization(
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


# ==================== 工艺参数初始化（基于规则推理）====================

class ProcessInitializationView(BaseView):
    """工艺参数初始化接口（纯推理，不落库）

    POST /api/processes/initialization/
    请求体（两种互斥模式）：
    - Mode A: {"condition_id": 123}
    - Mode B: {
        "machine_info": {...},
        "polymer_info": {...},
        "product_info": {...}
      }

    响应：
    {
        "param_source": "algorithm_init",
        "condition_id": 123 | null,
        "matched_rules": ["DEFAULT", "MATERIAL_GENERAL", "GATE_DIRECT"],
        "process": {...},   # 注塑机工艺参数（扁平）
        "mold_temp": {...},
        "hot_runner": {...},
        "summary": {...}    # 关键参数摘要
    }
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializationSchema))
    def post(self, request, cleaned_data):
        return initialization_service.infer_initial_params(
            condition_id=cleaned_data.get("condition_id"),
            machine_info=cleaned_data.get("machine_info"),
            polymer_info=cleaned_data.get("polymer_info"),
            product_info=cleaned_data.get("product_info"),
        )


class ProcessInitializationFromIdsView(BaseView):
    """工艺参数初始化接口（第三方用户场景：ID → 可选落库）

    POST /api/processes/initialization/from-ids/

    与 /initialization/ 的区别：
    - 输入：masterdata 的 ID（mold_id / polymer_id / injection_machine_id）
    - 行为：save=True 时创建 ProcessCondition + ProcessParameter；save=False 时纯推理不落库
    - 适用：第三方集成一次性创建完整工艺记录，或只做纯推理试算

    请求体（InitializationFromIdsSchema）：
    {
        "save": true,                    // 是否落库，默认 true
        "mold_id": 100,
        "polymer_id": 5,
        "injection_machine_id": 10,
        "shot_index": 1,
        "injection_index": 1,
        "status": "draft",
        "origin_type": "ai_recommendation",
        "condition_code": null,           // 不传则自动生成（save=True 时生效）
        "inj_stg": 1, "hold_stg": 1, "met_stg": 1,
        "barrel_temperature_stage": 5,
        "vps_mode": 0, "pre_met_decomp_mode": 0, "pst_met_decomp_mode": 0,
        // 可选覆盖字段（masterdata 字段不准确时手动覆盖）
        "product_weight": 80, "runner_weight": 0, "gate_type": "点浇口",
        "ave_thickness": 2.5, "max_thickness": 3.0, "max_length": 150,
        "gate_radius": 1.5, "gate_length": null, "gate_width": null
    }

    响应：
    save=True:
    {
        "condition_id": 123,           // 新建 ProcessCondition.id
        "parameter_id": 456,           // 新建 ProcessParameter.id (param_source=algorithm_init)
        ...
    }
    save=False:
    {
        "condition_id": null,          // 不创建
        "parameter_id": null,          // 不创建
        ...
    }
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(InitializationFromIdsSchema))
    def post(self, request, cleaned_data):
        # 提取可选覆盖字段（用户覆盖 masterdata 默认值）
        overrides = {
            k: cleaned_data[k] for k in (
                'product_weight', 'runner_weight', 'gate_type',
                'ave_thickness', 'max_thickness', 'max_length',
                'gate_radius', 'gate_length', 'gate_width',
            ) if cleaned_data.get(k) is not None
        }
        return initialization_service.create_and_infer_initial_params(
            mold_id=cleaned_data["mold_id"],
            polymer_id=cleaned_data["polymer_id"],
            injection_machine_id=cleaned_data["injection_machine_id"],
            shot_index=cleaned_data.get("shot_index", 1),
            injection_index=cleaned_data.get("injection_index", 1),
            status=cleaned_data.get("status", "draft"),
            origin_type=cleaned_data.get("origin_type", "ai_recommendation"),
            condition_code=cleaned_data.get("condition_code"),
            overrides=overrides or None,
            inj_stg=cleaned_data.get("inj_stg", 1),
            hold_stg=cleaned_data.get("hold_stg", 1),
            met_stg=cleaned_data.get("met_stg", 1),
            barrel_temperature_stage=cleaned_data.get("barrel_temperature_stage", 5),
            vps_mode=cleaned_data.get("vps_mode"),
            pre_met_decomp_mode=cleaned_data.get("pre_met_decomp_mode"),
            pst_met_decomp_mode=cleaned_data.get("pst_met_decomp_mode"),
            save=cleaned_data.get("save", True),
        )


class RuleByDefectView(BaseView):
    """根据缺陷名获取规则（query: defect_name）"""

    @method_decorator(require_login)
    def get(self, request):
        defect_name = request.GET.get("defect_name")
        if not defect_name:
            return []
        return rule_service.get_rules_by_defect(defect_name)