"""molding-optima 工艺相关视图 (processes)。

按业务领域分段 (以业务定位划分, 不以 method/path 数量划分):

| 段 | 业务对象 | 业务定位 |
|---|---|---|
| records       | 工艺记录 (condition + 最新 parameter) | 业务级入口 |
| conditions    | 纯 condition                  | 数据级访问 |
| parameters    | ProcessParameter               | 数据级 CRUD |
| tunings       | 人工调机反馈                    | parameter 子资源 |
| algorithms    | 算法触发                       | 独立触发器 |

各段的设计原则与段间关系见对应段级块注释。
rules / mining 段在 views/rules.py、views/mining.py。
URL 路由见 process/urls.py。
"""
from django.utils.decorators import method_decorator
from django.db import transaction

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView, PaginationResponse
from extensions.schemas import PaginationBaseSchema, BatchIdsSchema
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ACCESS_DENIED

from process.models import ProcessParameter
from process.schemas import (
    ProcessConditionAndParameterSchema,
    ProcessConditionWriteSchema,
    ProcessParameterListSchema,
    ProcessParameterTreeSchema,
    ProcessParameterUpdateSchema,
    ProcessRecordListSchema,
    ProcessRecordBatchDeleteSchema,
    ProcessInitializeFromMasterdataSchema,
    ProcessInitializeFromConditionSchema,
    ProcessInitializeFromProvidedSchema,
    ProcessOptimizeFromConditionSchema,
    TuningRecordRequestSchema,
    TransplantRequestSchema,
)
from process.services import (
    condition,
    parameter as parameter_service,
    parameter_optimize,
    parameter_transplant,
    rule,
    ParameterInitializeService,
    TuningService,
)
from process.services.tuning import is_round_sealed


# ============================================================
# 0. records 段 -- 业务对象 = 工艺记录 (condition + 最新 parameter 整体)
# ============================================================
#
# 业务定位:
# - 不接受"独立 parameter"业务
# - 与 conditions 段的分工见 conditions 段块注释
# - 完整视图 (parameter-list / parameter-tree / history) 挂在本段下, 是 records 业务的子视图
#
# 路由见 process/urls.py
# ============================================================


class ProcessRecordListView(BaseView):
    """工艺记录端点 —— 列表与录入。

    GET  -- 列表 (按 view_type 区分), 入参见 ProcessRecordListSchema
    POST -- 录入 (condition 必填, parameter 可选), 入参见 ProcessConditionAndParameterSchema

    POST payload 场景:
    - { condition }           : 骨架 (后续 PUT 补全)
    - { condition, parameter }: 完整 (condition + first parameter 原子)
    - { parameter } / {}      : 拒绝 (condition 必填)
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordListSchema))
    def get(self, request, cleaned_data):
        view_type = cleaned_data.pop("view_type", "parameter")
        total, results = condition.get_condition_list(
            view_type=view_type,
            company_id=request.user.company_id,
            **cleaned_data,
        )
        return PaginationResponse(total=total, items=results)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionAndParameterSchema))
    def post(self, request, cleaned_data):
        return condition.create_condition(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            **cleaned_data,
        )

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordBatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除工艺记录（按 condition_id, 级联软删其下 parameter）。

        入参字段语义见 ProcessRecordBatchDeleteSchema。
        """
        return condition.batch_delete_condition(
            cleaned_data["ids"], company_id=request.user.company_id
        )


class ProcessRecordDetailView(BaseView):
    """工艺记录端点 —— 详情、修改与软删。

    GET    -- 详情 (condition + 最新 parameter)
    PUT    -- 修改 (condition [+ 最新 parameter], 业务身份锁)
    DELETE -- 软删 condition (级联 parameter)

    业务:
    - condition_id = 业务聚合根; latest parameter 由 service 内部识别
    - GET 返回 {condition, parameter: {setting_process}} 嵌套结构
      (语义 = "前端可填表结构")
    - PUT 业务身份锁:
      - condition 字段: 见 ProcessConditionWriteSchema
      - parameter 字段 (Optional, NEST 格式):
        * 不传 → 仅改 condition
        * 传 setting_process → 改 condition 下的"最新 parameter"
          (latest parameter_id 由 service 按 created_at desc 选第一条)
    """

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition_frontend(condition_id, company_id=request.user.company_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionAndParameterSchema))
    def put(self, request, condition_id, cleaned_data):
        """修改工艺记录 (condition [+ 最新 parameter], 业务身份锁)。

        condition 字段的业务身份锁见 ProcessConditionWriteSchema;
        parameter 不传 → 仅改 condition, 传 setting_process → 改 condition 下的最新 parameter。
        """
        condition_data = cleaned_data.get("condition") or {}
        parameter_data = cleaned_data.get("parameter")

        # 业务身份锁字段静默忽略 + condition/parameter 双写
        return condition.update_record(
            condition_id,
            condition_data=condition_data,
            parameter_data=parameter_data,
            company_id=request.user.company_id,
        )

    @method_decorator(require_login)
    def delete(self, request, condition_id):
        condition.delete_condition(condition_id, company_id=request.user.company_id)


class ProcessRecordParameterListView(BaseView):
    """工艺记录完整视图 (平铺) —— 一次取全部调机轮次。

    返回 {condition, parameters[]}
    """
    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition_with_parameter_list(
            condition_id, company_id=request.user.company_id
        )


class ProcessRecordParameterTreeView(BaseView):
    """工艺记录完整视图 (树形) —— 参数迭代树。

    返回 {condition, parameter_tree[]}
    """
    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition_with_parameter_tree(
            condition_id, company_id=request.user.company_id
        )


class ProcessRecordHistoryView(BaseView):
    """调机历史 —— 某个 condition 下的全部调机轮次 (时间线)。

    调机记录弹窗数据源, 返回 {condition, count, history[]}
    (每条 parameter = 一轮调机, 按 created_at 倒序)
    """

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition_history(
            condition_id, company_id=request.user.company_id
        )


# ============================================================
# 1. conditions 段 -- 业务粒度 = 纯 condition (数据级访问)
# ============================================================
#
# 业务定位:
# - records 段    = 业务级入口 (condition + first parameter 整体, 创建/列表/软删/批量软删)
# - conditions 段 = 数据级访问 (list + 独立创建 + 详情 + 业务身份锁修改)
# - 软删入口走 records 段, 不在本段提供 (避免双口)
# - POST 区别: records 段 condition + first parameter 一起创建; conditions 段仅 condition
#
# 路由见 process/urls.py
# ============================================================


class ConditionListView(BaseView):
    """工艺条件端点 —— 列表与独立创建 (数据级访问)。

    GET  -- 条件列表 (按 view_type 区分)
    POST -- 独立创建 (仅 condition, parameter 字段被忽略)

    业务:
    - view_type 默认 'all' (纯 condition, 不带 latest parameter 详情)
    - POST 接收 ProcessConditionAndParameterSchema, 但仅使用 condition 字段
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordListSchema))
    def get(self, request, cleaned_data):
        view_type = cleaned_data.pop("view_type", "all")
        total, results = condition.get_condition_list(
            view_type=view_type,
            company_id=request.user.company_id,
            **cleaned_data,
        )
        return PaginationResponse(total=total, items=results)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionAndParameterSchema))
    def post(self, request, cleaned_data):
        return condition.create_condition(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            condition=cleaned_data["condition"],
        )


class ConditionDetailView(BaseView):
    """工艺条件端点 —— 详情与修改 (纯 condition 数据级访问)。

    GET -- 纯 condition 详情 (不带 latest parameter)
    PUT -- 业务身份锁修改 (仅 condition 字段)

    业务:
    - PUT 的允许 / 锁定字段清单见 services/condition.py::CONDITION_LOCKED_FIELDS
    """

    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition(condition_id, company_id=request.user.company_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionWriteSchema))
    def put(self, request, condition_id, cleaned_data):
        """业务身份锁修改 (仅 condition 字段)。

        允许 / 锁定字段清单见 services/condition.py::CONDITION_LOCKED_FIELDS。
        """
        return condition.update_condition(
            condition_id, company_id=request.user.company_id, **cleaned_data
        )


# ============================================================
# 2. parameters 段 -- 业务对象 = ProcessParameter (数据级 CRUD)
# ============================================================
#
# 设计原则:
# - parameter 是独立业务对象 (自带 ID, 自带 process_condition_id 外键)
# - URL 单段化 (不嵌套 condition_id), 避免与数据库 FK 重复表达
# - condition_id 退化为可选 query 过滤条件, 不在 URL 重复表达 belongs_to
# - service 函数不带 _in_condition 后缀, 仅凭 parameter_id 定位 + 可选过滤
# - 写操作 (PUT/DELETE) 在 service 层校验归属 (parameter 自带 process_condition_id)
#
# 路由见 process/urls.py
# ============================================================


class ParameterListView(BaseView):
    """parameter 列表 —— 平铺列出全部版本 (用于参数详情页)。

    过滤字段与分页参数见 ProcessParameterListSchema。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        total, items = parameter_service.list_parameters(**cleaned_data)
        return PaginationResponse(total=total, items=items)


class ParameterDetailView(BaseView):
    """parameter 单条端点 —— 详情、更新与删除。"""

    @method_decorator(require_login)
    def get(self, request, parameter_id):
        return parameter_service.get_parameter(parameter_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterUpdateSchema))
    def put(self, request, parameter_id, cleaned_data):
        return parameter_service.update_parameter(
            parameter_id, parameter=cleaned_data["parameter"]
        )

    @method_decorator(require_login)
    def delete(self, request, parameter_id):
        parameter_service.delete_parameter(parameter_id)


class ProcessParameterCloneRoundView(BaseView):
    """以某一轮为基线新建一轮。

    已落库评价的轮次已归档、参数不可改写；但用户可以「回到某一轮重来」——
    以源轮参数为起点，在同一 condition 下新建第 N+1 轮（parent 指向源轮），
    **源轮不被改写**。新轮未评价 ⇒ 参数可继续编辑。
    """

    @method_decorator(require_login)
    def post(self, request, parameter_id):
        return parameter_service.clone_round_from_parameter(
            parameter_id,
            company_id=request.user.company_id,
        )


class ParameterTreeView(BaseView):
    """工艺参数版本树。

    parent_param_id 递归属关系; 【注意】路由未挂出 (见 process/urls.py)
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterTreeSchema))
    def get(self, request, cleaned_data):
        condition_id = cleaned_data.get("condition_id")
        return parameter_service.get_parameter_tree(condition_id=condition_id)


# ============================================================
# 3. tunings 段 -- 业务 = 人工调机反馈 (动作 = feedback)
# ============================================================
#
# 与 algorithms 段的关系:
# - /api/processes/algorithms/optimize/ 独立算法触发器, 不合并入本段
# - 本段 /api/processes/parameters/<int:parameter_id>/tuning-feedback/ 人工记录试模结果
#
# 设计原则:
# - tuning 实际归属 parameter, 不挂 condition (避免李鬼归属)
# - tuning 写入在 service 层校验 parameter 归属 (parameter 自带 process_condition_id)
#
# 路由见 process/urls.py
# ============================================================


class TuningFeedbackView(BaseView):
    """人工调机反馈。

    「保存当前工艺」语义:
    - 参数与评价**一起落库**（同一事务）：「我用了这组参数，试模结果是 X」
    - parameter 省略时退化为「只写评价」（向后兼容）
    入参字段语义见 TuningRecordRequestSchema。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(TuningRecordRequestSchema))
    def post(self, request, parameter_id, cleaned_data):
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

        # 参数与评价必须同生共死，否则会出现「参数存了、评价没存」的错配
        # （评价属于「该轮参数自身的试模结果」，参数变了评价就对不上了）。
        parameter_payload = cleaned_data.get("parameter")
        parameter_locked = False
        with transaction.atomic():
            # 【注意】用真值判断而非 `is not None`：空 dict 传进来会让 update_parameter
            #    报「parameter 不能为空」，而它的语义就是「没改参数，只写评价」
            if parameter_payload:
                if is_round_sealed(parameter):
                    # 归档轮次：参数是「当时实际用的工艺」这一历史事实，不允许改写。
                    # 这里**不抛错而是忽略参数** —— 本端点的语义是「参数+评价一起落库」，
                    # 直接抛错会连带评价也存不进去，与「参数锁死、评价可改」的口径矛盾。
                    parameter_locked = True
                else:
                    # 部分更新：只写传了的字段（validate_parameters 已 exclude_none，
                    # 未传的字段保持原值）；parent_param / seq_idx 等版本关系字段受锁保护
                    parameter_service.update_parameter(
                        parameter_id,
                        parameter=parameter_payload,
                    )

            record, created = TuningService.upsert_tuning_record(
                parameter=parameter,
                defect_feedbacks=cleaned_data.get("defect_feedbacks"),
                observations=cleaned_data.get("observations"),
                tuning_result=cleaned_data.get("tuning_result"),
                result_detail=cleaned_data.get("result_detail"),
            )

        return {
            "tuning_record_id": record.id,
            "parameter_id": parameter.id,
            "created": created,
            # 参数被忽略的标记（前端据此提示「参数已锁定，仅保存评价」）
            "parameter_locked": parameter_locked,
            "updated_at": record.updated_at,
        }


# ============================================================
# 4. algorithms 段 -- 业务 = 算法触发
# ============================================================
# URL 前缀: /api/processes/algorithms/  无 URL 变量 (参数在 body)
#
# 路由见 process/urls.py
# ============================================================


class AlgorithmsInitializeView(BaseView):
    """算法初始化端点 —— 由主数据 ID 建档并产出首轮工艺参数。

    以 mold_id / injection_machine_id / polymer_id 建工艺条件，
    跑推理得出该条件的首轮工艺参数并落库。
    入参字段语义见 ProcessInitializeFromMasterdataSchema。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializeFromMasterdataSchema))
    def post(self, request, cleaned_data):
        return ParameterInitializeService.initialize_from_masterdata(
            mold_id=cleaned_data["mold_id"],
            injection_machine_id=cleaned_data["injection_machine_id"],
            polymer_id=cleaned_data["polymer_id"],
            shot_index=cleaned_data.get("shot_index", 0),
            injection_index=cleaned_data.get("injection_index", 0),
            process_set=cleaned_data.get("process_set"),
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
        )


class AlgorithmsInitializeFromConditionView(BaseView):
    """算法初始化端点 —— 复制源工艺条件的合格工艺作为新起点。

    不跑推理，直接复制源 condition 下的工艺参数建新档；
    快照按最新 masterdata 重建，避免沿用已过期的数据。
    入参字段语义见 ProcessInitializeFromConditionSchema。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializeFromConditionSchema))
    def post(self, request, cleaned_data):
        return ParameterInitializeService.initialize_from_condition(
            source_condition_id=cleaned_data["source_condition_id"],
            process_set=cleaned_data.get("process_set"),
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
        )


class AlgorithmsInitializeFromProvidedView(BaseView):
    """算法初始化端点 —— 调用方直传四维数据做纯推理。

    模具 / 设备 / 材料 / 工艺设置四维数据由调用方直传，后端不查库、不落库。
    适用场景：第三方系统集成（库内无 masterdata）、算法试算。
    入参字段语义见 ProcessInitializeFromProvidedSchema。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializeFromProvidedSchema))
    def post(self, request, cleaned_data):
        return ParameterInitializeService.initialize_from_provided(
            mold_info=cleaned_data["mold_info"],
            machine_info=cleaned_data["machine_info"],
            polymer_info=cleaned_data["polymer_info"],
            process_set=cleaned_data.get("process_set"),
        )


class AlgorithmsOptimizeView(BaseView):
    """智能调机端点 —— 以工艺条件下的基准轮次为基线，推理下一轮工艺参数。

    以 condition_id + parent_seq_idx 定位基准轮次，取该轮参数与缺陷反馈作为推理输入，
    产出新一轮工艺参数与对应建议并落库。
    入参字段语义见 ProcessOptimizeFromConditionSchema。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessOptimizeFromConditionSchema))
    def post(self, request, cleaned_data):
        return parameter_optimize.optimize_from_condition(
            condition_id=cleaned_data["condition_id"],
            parent_seq_idx=cleaned_data["parent_seq_idx"],
            parameter=cleaned_data.get("parameter"),
            feedback=cleaned_data.get("feedback"),
        )


class AlgorithmsTransplantView(BaseView):
    """工艺移植端点 —— 把既有工艺参数换算到目标注塑机。

    取源工艺参数的工艺设置与源机能力上限，按目标机器规格换算出一套新参数。
    入参字段语义见 TransplantRequestSchema。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(TransplantRequestSchema))
    def post(self, request, cleaned_data):
        return parameter_transplant.transplant_process_parameter(
            source_parameter_id=cleaned_data["source_parameter_id"],
            target_machine_spec=cleaned_data["target_machine_spec"],
        )
