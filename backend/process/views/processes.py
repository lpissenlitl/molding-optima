"""
molding-optima 工艺参数视图（对齐 molding-expert）
"""
from django.utils.decorators import method_decorator
from django.db import transaction

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView, PaginationResponse
from extensions.schemas import PaginationBaseSchema, BatchIdsSchema

from process.schemas import (
    ProcessParameterSchema,
    ProcessParameterListSchema,
    BatchDeleteProcessParameterSchema,
    ProcessInitializationFromSourceConditionSchema,
    ProcessInitializationFromMasterdataSchema,
    ProcessInferSchema,
    InferRequestSchema,
)
from process.services import (
    main_service,
    transplant_service,
    expert_service,
    optimize_service,
    rule_service,
    initialization_service,
    statistics_service,
    OptimizationInferService,
)


# ==================== 工艺参数 ====================

class ProcessParameterListView(BaseView):
    """工艺参数列表"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        total, results = main_service.get_process_parameter_list(
            company_id=request.user.company_id,
            **cleaned_data,
        )
        return PaginationResponse(total=total, items=results)


class ProcessParameterCreateView(BaseView):
    """工艺参数前端创建（对齐 molding-expert /parameter/frontend/）"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def post(self, request, cleaned_data):
        return main_service.create_process_parameter(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **cleaned_data,
        )


class ProcessParameterDetailView(BaseView):
    """工艺参数详情/更新/删除（对齐 molding-expert /parameter/<condition_id>/）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return main_service.get_process_parameter(condition_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def put(self, request, condition_id, cleaned_data):
        return main_service.update_process_parameter(condition_id, **cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, condition_id):
        main_service.delete_process_parameter(condition_id)


class ProcessParameterFlatView(BaseView):
    """工艺参数扁平视图（对齐 molding-expert /parameter/<id>/flat/）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return main_service.get_process_parameter_flat(condition_id)


class ProcessParameterFrontendView(BaseView):
    """工艺参数前端视图（对齐 molding-expert /parameter/<id>/frontend/）"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return main_service.get_process_parameter_frontend(condition_id)


class ProcessParameterBatchDeleteView(BaseView):
    """工艺参数批量删除"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchIdsSchema))
    def post(self, request, cleaned_data):
        return main_service.batch_delete_process_parameter(cleaned_data["ids"])


# ==================== 工艺移植 ====================

class ProcessTransplantView(BaseView):
    """工艺参数移植（对齐 molding-expert /parameter/transplant/）"""

    @method_decorator(require_login)
    def post(self, request):
        return transplant_service.transplant_process_parameter(
            source_parameter_id=request.DATA.get("source_parameter_id"),
            target_machine_spec=request.DATA.get("target_machine_spec"),
        )


# ==================== 工艺参数初始化（基于规则推理）====================

class ProcessInitializationFromSourceConditionView(BaseView):
    """【Mode C】工艺参数初始化接口（基于源 condition_id 复制初始工艺，不调推理）

    POST /api/processes/initialization/from-source-condition/

    业务场景：
      工艺记录中已有“合格工艺”（condition + 其下的 ProcessParameter），
      复用该工艺作为新工艺的起点。service 层会重新检索当前 masterdata
      以保证数据不过时。

    请求体：
    {
        "source_condition_id": 100,   # 必填
        "process_set": {...}           # 可选
    }

    后端行为：创建新 Condition（origin_type=legacy_import）+ ProcessParameter（参数拷贝）
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializationFromSourceConditionSchema))
    def post(self, request, cleaned_data):
        return initialization_service.infer_from_source_condition(
            source_condition_id=cleaned_data["source_condition_id"],
            process_set=cleaned_data.get("process_set"),
        )


class ProcessInitializationFromMasterdataView(BaseView):
    """【Mode B】工艺参数初始化接口（基于 masterdata ID）

    POST /api/processes/initialization/from-masterdata/

    4 步逻辑：
      Step 1: 入口适配 —— 3 个 masterdata ID
      Step 2: 数据前处理 —— ORM + process_context → 4 维 dict
      Step 3: 推理算法 —— 内部调用 infer_initial_params
      Step 4: 输出后处理 —— 落库（创建 Condition + ProcessParameter）

    请求体：
    {
        "mold_id": 100,                                            # 必填
        "polymer_id": 5,                                           # 必填
        "injection_machine_id": 10,                                # 必填
        "process_context": {...},                                   # 可选
        "process_set": {...},                                       # 可选
        "condition_no": "..."                                       # 可选，不传自动生成
    }

    后端行为：创建新 Condition + ProcessParameter
    status / origin_type 由后端固定为 draft / ai_recommendation
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializationFromMasterdataSchema))
    def post(self, request, cleaned_data):
        return initialization_service.infer_from_masterdata(
            mold_id=cleaned_data["mold_id"],
            injection_machine_id=cleaned_data["injection_machine_id"],
            polymer_id=cleaned_data["polymer_id"],
            shot_index=cleaned_data.get("shot_index", 0),
            injection_index=cleaned_data.get("injection_index", 0),
            process_set=cleaned_data.get("process_set"),
        )


class ProcessInitializationInferView(BaseView):
    """【/infer/】工艺参数纯推理接口（前端传完整数据，不查库不落库）

    POST /api/processes/initialization/infer/

    只跑 Step 3（跳过 Step 1/2/4）：
      - service 不查 DB（数据库里没数据）
      - service 不落库（无关联可挂）
      - 前端直接传 4 维 dict

    请求体（4 个独立维度，职责清晰）：
    {
        "mold_info": {...},        # 模具信息（模具级 + 产品/浇口/壁厚派生）
        "machine_info": {...},     # 设备信息（机台本身 + 注射单元）
        "polymer_info": {...},     # 材料信息
        "process_set": {...}       # 工艺设置（与设备/模具/材料无关的"工艺元数据"）
    }
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInferSchema))
    def post(self, request, cleaned_data):
        return initialization_service.infer_from_dict(
            mold_info=cleaned_data["mold_info"],
            machine_info=cleaned_data["machine_info"],
            polymer_info=cleaned_data["polymer_info"],
            process_set=cleaned_data.get("process_set"),
        )


# ==================== 规则管理 ====================

class RuleKeywordListView(BaseView):
    """规则关键字列表"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        # 默认按当前用户公司过滤；平台超管未接管时可看全部
        result = rule_service.get_list_of_rule_keyword(
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
            **cleaned_data,
        )
        return PaginationResponse(total=result["total"], items=result["items"])

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


class ProcessOptimizationInferView(BaseView):
    """工艺优化 infer 接口（调用链路编排）

    POST /api/processes/optimization/infer/

    业务语义：
      “基于上一轮工艺与缺陷反馈，调算法生成新工艺，并同步落库”

    适用场景（统一调用逻辑，仅 feedback 不同）：
      - 场景 1（基本调参）：feedback.defect 包含 1+ 缺陷
      - 场景 2（自动回撤）：feedback.tuning_result='ineffective'
      - 场景 3（手动修改）：parameter 包含用户手动调整

    请求体（InferRequestSchema）：
    {
        "condition_id": int,             # 必填
        "parent_seq_idx": int,           # 必填（业务编号）
        "parameter": dict | None,        # 可选，手动修改覆盖
        "feedback": {
            "defect": [...],             # 可选，缺陷反馈列表
            "observations": [...],       # 可选，实测观察
            "tuning_result": str | null, # 可选，增量反馈
        }
    }

    响应：
    {
        "new_parameter": {...},          # 新工艺参数（含 parameter_id / seq_idx）
        "suggestion": {
            "source_type": str,
            "recommendation_id": int,
            "groups": [
                {"category": str, "icon": str, "items": [...]}
            ]
        }
    }
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(InferRequestSchema))
    def post(self, request, cleaned_data):
        service = OptimizationInferService()
        return service.infer(
            condition_id=cleaned_data["condition_id"],
            parent_seq_idx=cleaned_data["parent_seq_idx"],
            parameter=cleaned_data.get("parameter"),
            feedback=cleaned_data.get("feedback"),
        )



class RuleByDefectView(BaseView):
    """根据缺陷名获取规则（query: defect_name）"""

    @method_decorator(require_login)
    def get(self, request):
        defect_name = request.GET.get("defect_name")
        if not defect_name:
            return []
        return rule_service.get_rules_by_defect(defect_name)


# ==================== 仪表板统计 ====================

class DashboardStatisticsView(BaseView):
    """仪表板统计聚合（近 30 天趋势 + 起源类型分布）

    GET /api/processes/statistics/dashboard/

    业务说明：
    - 一次返回 dashboard 全部图表所需数据，避免前端 N+1 查询
    - 多租户隔离：按当前用户 company_id 过滤
    """

    @method_decorator(require_login)
    def get(self, request):
        return statistics_service.get_dashboard_statistics(
            company_id=request.user.company_id,
            days=30,
        )