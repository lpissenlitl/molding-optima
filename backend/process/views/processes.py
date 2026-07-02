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
    ProcessInferSchema,
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
    """工艺参数初始化接口（统一入口，都是落库接口）

    POST /api/processes/initialization/

    Mode A：基于已有 condition_id
    请求体：
    {
        "condition_id": 123,
        // 可选覆盖字段
        "product_weight": 80,
        "gate_type": "点浇口",
        // 工艺设置（段数与模式）
        "process_set": {
            "inj_stg": 1, "hold_stg": 1, "met_stg": 1,
            "vps_mode": 0, ...
        }
    }
    后端行为：从 condition 查询 mold/machine/polymer，创建新的 Parameter 记录

    Mode B：基于 masterdata ID 组装
    请求体：
    {
        "mold_id": 100,
        "polymer_id": 5,
        "injection_machine_id": 10,
        "shot_index": 1, "injection_index": 1,
        "status": "draft",
        "origin_type": "ai_recommendation",
        // 可选覆盖字段
        "product_weight": 80,
        "gate_type": "点浇口",
        // 工艺设置（段数与模式）
        "process_set": {
            "inj_stg": 1, "hold_stg": 1, "met_stg": 1,
            ...
        }
    }
    后端行为：从 masterdata 查询并组装，创建新 Condition + Parameter

    其他场景：
    - /initialization/infer/：纯推理，前端传完整数据（扁平化结构），不查库不落库

    响应：
    Mode A:
    {
        "condition_id": 123,         # 原 condition ID
        "parameter_id": 456,         # 新建 Parameter
        "matched_rules": [...],
        "process": {...}, "mold_temp": {...}, "hot_runner": {...},
        "summary": {...}
    }
    Mode B:
    {
        "condition_id": 789,         # 新建
        "parameter_id": 790,         # 新建
        ...
    }
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializationSchema))
    def post(self, request, cleaned_data):
        condition_id = cleaned_data.get("condition_id")

        # Mode A：基于已有 condition_id 推理，不需 mold/machine/polymer 查询（infer_initial_params 内部会查）
        if condition_id is not None:
            return initialization_service.infer_initial_params(
                condition_id=condition_id,
            )

        # Mode B：基于 masterdata ID 组装并创建工艺记录
        mold_id = cleaned_data.get("mold_id")
        polymer_id = cleaned_data.get("polymer_id")
        injection_machine_id = cleaned_data.get("injection_machine_id")
        if not (mold_id and polymer_id and injection_machine_id):
            raise ValueError(
                "必须提供 condition_id（Mode A）或者同时提供 mold_id + polymer_id + injection_machine_id（Mode B）"
            )

        # 提取可选覆盖字段（用户覆盖 masterdata 默认值）
        overrides = {
            k: cleaned_data[k] for k in (
                'product_weight', 'runner_weight', 'gate_type',
                'ave_thickness', 'max_thickness', 'max_length',
                'gate_radius', 'gate_length', 'gate_width',
            ) if cleaned_data.get(k) is not None
        }
        # 提取 process_set 字段中的段数与模式设置
        process_set = cleaned_data.get("process_set") or {}
        return initialization_service.create_and_infer_initial_params(
            mold_id=mold_id,
            polymer_id=polymer_id,
            injection_machine_id=injection_machine_id,
            shot_index=cleaned_data.get("shot_index", 1),
            injection_index=cleaned_data.get("injection_index", 1),
            status=cleaned_data.get("status", "draft"),
            origin_type=cleaned_data.get("origin_type", "ai_recommendation"),
            condition_code=cleaned_data.get("condition_code"),
            overrides=overrides or None,
            inj_stg=process_set.get("inj_stg", 1),
            hold_stg=process_set.get("hold_stg", 1),
            met_stg=process_set.get("met_stg", 1),
            barrel_temperature_stage=process_set.get("barrel_temperature_stage", 5),
            vps_mode=process_set.get("vps_mode"),
            pre_met_decomp_mode=process_set.get("pre_met_decomp_mode"),
            pst_met_decomp_mode=process_set.get("pst_met_decomp_mode"),
            save=True,
        )


class ProcessInitializationInferView(BaseView):
    """工艺参数纯推理接口（前端传完整数据，不查库不落库）

    POST /api/processes/initialization/infer/

    请求体：
    {
        "machine_info": {...},     // 注塑机本身信息
        "injection_unit": {...},   // 注射单元参数
        "polymer_info": {...},     // 材料信息
        "mold_info": {...},        // 模具信息
        "product_info": {...},     // 产品信息
        "process_set": {...}       // 工艺设置
    }

    适用场景：
    - 第三方集成：调用方没有我们的 masterdata
    - 算法试算：仅做参数推荐，不保存记录

    不落库原因：数据库中没有关联数据，落库是数据丢失。

    响应：与 /initialization/ 一致，但 condition_id 和 parameter_id 始终为 null
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInferSchema))
    def post(self, request, cleaned_data):
        # 合并扁平化字段为算法引擎期望的格式
        machine_info = {
            **cleaned_data["machine_info"],
            **cleaned_data["injection_unit"],
        }
        polymer_info = cleaned_data["polymer_info"]
        # 把 mold_info + process_set 合并到 product_info
        product_info = {
            **cleaned_data["mold_info"],
            **cleaned_data["product_info"],
            **cleaned_data["process_set"],
        }
        return initialization_service.infer_initial_params(
            machine_info=machine_info,
            polymer_info=polymer_info,
            product_info=product_info,
        )


class RuleByDefectView(BaseView):
    """根据缺陷名获取规则（query: defect_name）"""

    @method_decorator(require_login)
    def get(self, request):
        defect_name = request.GET.get("defect_name")
        if not defect_name:
            return []
        return rule_service.get_rules_by_defect(defect_name)