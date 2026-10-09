"""
molding-optima 工艺相关视图 (processes)

2026-10-09 重构: 按"业务粒度=condition"重新设计工艺记录
  - 段名: processes/record/ (业务名"工艺记录")
  - 变量: condition_id (业务粒度=condition)
  - 录入是组合动作: condition + parameter 一起创建
  - 列表返回每条 condition + latest parameter
  - frontend 嵌套视图按 condition_id 查

按业务场景分块:
  1. 工艺记录 (record 业务粒度) -- 6 个 method 接口
  2. 工艺条件 (condition 维度) -- 历史视图 (暂保留)
  3. 调机反馈 (Tuning)
  4. 工艺移植 (基于 condition)
  5. 工艺初始化 (基于 condition)
  6. 工艺优化 (基于 condition)
  7. 规则管理

URL 路由见 process/urls.py。
"""
from django.utils.decorators import method_decorator

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView, PaginationResponse
from extensions.schemas import PaginationBaseSchema, BatchIdsSchema
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ACCESS_DENIED

from process.models import ProcessParameter
from process.schemas import (
    ProcessParameterSchema,
    ProcessParameterListSchema,
    ProcessInitializationFromMasterdataSchema,
    InferRequestSchema,
    TuningRecordRequestSchema,
)
from process.services import (
    condition,
    parameter as parameter_service,  # 按 parameter_id 操作 (单条 + 版本树)
    parameter_transplant,
    rule,
    parameter_initialize,
    ParameterOptimizeService,
    TuningService,
)


# ============================================================
# 1. 工艺记录 (record 业务粒度) - 6 个 method 接口
# ============================================================
# 设计说明:
# - 段名: processes/record/ (业务名"工艺记录")
# - 变量: condition_id (业务粒度=condition)
# - 录入是组合动作: condition + parameter 一起创建
# - 列表返回每条 condition + latest parameter
# - 业务粒度=condition (段名=业务名, 变量=查询粒度)
# ============================================================


class ParameterRecordListView(BaseView):
    """工艺记录列表 (GET) / 录入 (POST)

    GET  /api/processes/record/   -- 工艺记录列表
    POST /api/processes/record/   -- 录入工艺记录 (创建 condition + parameter)

    业务说明:
    - 录入是组合动作: condition + parameter 一起创建 (业务上录入工艺是一个动作)
    - 列表返回每条 condition + latest parameter
    - 段名=record (业务名), 变量=condition_id (查询粒度)
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        total, results = condition.get_condition_list(
            view_type="parameter",
            company_id=request.user.company_id,
            **cleaned_data,
        )
        return PaginationResponse(total=total, items=results)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def post(self, request, cleaned_data):
        return condition.create_condition(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **cleaned_data,
        )


class ParameterRecordDetailView(BaseView):
    """工艺记录详情 / 修改 / 删除 (按 condition_id)

    GET    /api/processes/record/<int:condition_id>/   -- 详情
    PUT    /api/processes/record/<int:condition_id>/   -- 修改
    DELETE /api/processes/record/<int:condition_id>/   -- 删除

    说明: 业务粒度改为 condition (URL 段名=record, 变量=condition_id)
    """

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition(condition_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def put(self, request, condition_id, cleaned_data):
        return condition.update_condition(condition_id, **cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, condition_id):
        condition.delete_condition(condition_id)


# ============================================================
# 2. 工艺条件 (condition 维度) - 历史视图 (本轮暂保留, 后续清理)
# ============================================================


class ConditionListView(BaseView):
    """工艺条件列表 (GET) -- 历史接口, 后续由 ParameterRecordListView 取代"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        total, results = condition.get_condition_list(
            company_id=request.user.company_id,
            **cleaned_data,
        )
        return PaginationResponse(total=total, items=results)


class ConditionCreateView(BaseView):
    """工艺条件创建 (POST) -- 历史接口, 后续由 ParameterRecordListView 取代"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def post(self, request, cleaned_data):
        return condition.create_condition(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **cleaned_data,
        )


class ConditionDetailView(BaseView):
    """工艺条件详情 / 更新 / 删除 -- 历史接口, 后续由 ParameterDetailView 取代"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition(condition_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterSchema))
    def put(self, request, condition_id, cleaned_data):
        return condition.update_condition(condition_id, **cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, condition_id):
        condition.delete_condition(condition_id)


class OptimizationListView(BaseView):
    """工艺优化列表 (GET)

    2026-10-09 新增: optimization 业务粒度 (本轮先列 URL, view 占位)
    GET /api/processes/optimization/   -- 列表

    【占位】业务逻辑待实现
    """
    pass


class OptimizationDetailView(BaseView):
    """工艺优化详情 (GET) (按 condition_id)

    2026-10-09 新增: optimization 业务粒度 (本轮先列 URL, view 占位)
    GET /api/processes/optimization/<int:condition_id>/   -- 详情

    【占位】业务逻辑待实现
    """
    pass


class ParameterTreeView(BaseView):
    """工艺参数版本树 (GET)"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return parameter_service.get_parameter_tree(condition_id)


class ConditionBatchDeleteView(BaseView):
    """工艺条件批量删除 (POST)"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchIdsSchema))
    def post(self, request, cleaned_data):
        return condition.batch_delete_condition(cleaned_data["ids"])


# ============================================================
# 4. 调机反馈 (Tuning)
# ============================================================


class ProcessTuningRecordView(BaseView):
    """保存当前试模结果 (试模反馈 + 缺陷 + 效果评价)

    POST /api/processes/tuning/record/
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(TuningRecordRequestSchema))
    def post(self, request, cleaned_data):
        parameter_id = cleaned_data["parameter_id"]
        try:
            parameter = ProcessParameter.all_objects.get(id=parameter_id)
        except ProcessParameter.DoesNotExist:
            raise BizException(
                ERROR_DATA_NOT_FOUND,
                f"工艺参数不存在: id={parameter_id}",
            )

        user_company_id = getattr(request.user, "company_id", None)
        if (
            parameter.company_id is not None
            and user_company_id is not None
            and parameter.company_id != user_company_id
        ):
            raise BizException(
                ERROR_ACCESS_DENIED,
                f"无权访问其他公司的工艺参数: parameter_id={parameter_id}",
            )

        record, created = TuningService.upsert_tuning_record(
            parameter=parameter,
            defect_feedbacks=cleaned_data.get("defect_feedbacks"),
            tuning_result=cleaned_data.get("tuning_result"),
            result_detail=cleaned_data.get("result_detail"),
        )

        return {
            "tuning_record_id": record.id,
            "parameter_id": parameter.id,
            "created": created,
            "updated_at": record.updated_at,
        }


# ============================================================
# 5. 工艺移植 (基于 condition)
# ============================================================


class ConditionTransplantView(BaseView):
    """工艺移植 (POST)"""

    @method_decorator(require_login)
    def post(self, request):
        return parameter_transplant.transplant_process_parameter(
            source_parameter_id=request.DATA.get("source_parameter_id"),
            target_machine_spec=request.DATA.get("target_machine_spec"),
        )


# ============================================================
# 6. 工艺初始化 (基于 condition)
# ============================================================


class ConditionInitializeView(BaseView):
    """工艺初始化 (基于 masterdata ID + 算法推理 + 落库)

    POST /api/processes/condition/initialize/
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializationFromMasterdataSchema))
    def post(self, request, cleaned_data):
        return parameter_initialize.infer_from_masterdata(
            mold_id=cleaned_data["mold_id"],
            injection_machine_id=cleaned_data["injection_machine_id"],
            polymer_id=cleaned_data["polymer_id"],
            shot_index=cleaned_data.get("shot_index", 0),
            injection_index=cleaned_data.get("injection_index", 0),
            process_set=cleaned_data.get("process_set"),
        )


# ============================================================
# 7. 工艺优化 (基于 condition)
# ============================================================


class OptimizationHistoryView(BaseView):
    """工艺优化历史 (GET)"""

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition_history(condition_id)


class OptimizationInferView(BaseView):
    """工艺优化 infer (调机迭代核心接口)"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(InferRequestSchema))
    def post(self, request, condition_id, cleaned_data):
        service = ParameterOptimizeService()
        return service.infer(
            condition_id=condition_id,
            parent_seq_idx=cleaned_data["parent_seq_idx"],
            parameter=cleaned_data.get("parameter"),
            feedback=cleaned_data.get("feedback"),
        )


# ============================================================
# 8. 规则管理 (保持现状 -- 与 parameter 维度无关)
# ============================================================


class RuleKeywordListView(BaseView):
    """规则关键字列表 / 创建"""

    @method_decorator(require_login)
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


class RuleMethodListView(BaseView):
    """规则方法列表 / 创建"""

    @method_decorator(require_login)
    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        return rule.get_list_of_rule_method(**cleaned_data)

    @method_decorator(require_login)
    def post(self, request):
        return rule.add_rule_method(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **request.DATA,
        )


class RuleByDefectView(BaseView):
    """根据缺陷名获取规则 (query: defect_name)"""

    @method_decorator(require_login)
    def get(self, request):
        defect_name = request.GET.get("defect_name")
        if not defect_name:
            return []
        return rule.get_rules_by_defect(defect_name)


# ============================================================
# 占位 view -- 待单独设计接口
# ============================================================
# “”【2026-10-09 重命名】ParameterDetailView / ParameterFrontendView
# 原逻辑已迁移到 ParameterRecordDetailView / ParameterRecordFrontendView。
# 这两个 view 名保留, 后续会有独立的 URL 设计 (业务场景待定)。
# ============================================================


# ============================================================
# 占位 view -- 待单独设计接口
# ============================================================
# 2026-10-09 重命名: ParameterDetailView / ParameterFrontendView
# 原逻辑已迁移到 ParameterRecordDetailView / ParameterRecordFrontendView。
# 这两个 view 名保留, 后续会有独立的 URL 设计 (业务场景待定)。
# ============================================================


class ParameterDetailView(BaseView):
    """工艺参数详情 / 修改 / 删除 (按 parameter_id)

    2026-10-09 启用: parameter 业务粒度 (5 个 method 接口之一)
    GET    /api/processes/parameter/<int:parameter_id>/   -- 详情
    PUT    /api/processes/parameter/<int:parameter_id>/   -- 修改
    DELETE /api/processes/parameter/<int:parameter_id>/   -- 删除

    【占位】业务逻辑待实现 (本轮先列 URL, view 用占位)
    """
    pass


class ParameterListCreateView(BaseView):
    """工艺参数列表 / 录入 (parameter 业务粒度)

    2026-10-09 新增: parameter 业务粒度 (5 个 method 接口之一)
    GET  /api/processes/parameter/   -- 列表
    POST /api/processes/parameter/   -- 录入

    【占位】业务逻辑待实现 (本轮先列 URL, view 用占位)
    """
    pass


class ParameterFrontendView(BaseView):
    """工艺参数前端视图 -- 待单独设计接口

    2026-10-09 占位: 原逻辑已迁移到 ParameterRecordFrontendView (业务粒度=condition)。
    本 view 保留, 后续根据业务场景单独设计独立 URL。
    """
    pass
