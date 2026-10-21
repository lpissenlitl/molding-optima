"""molding-optima 工艺相关视图 (processes)

按"业务领域"分 5 段 (以业务定位划分, 不以 method/path 数量划分):

| 段 | 业务对象 | 业务定位 | URL |
|---|---|---|---|
| records       | 工艺记录 (condition + 最新 parameter) | 业务级入口 | /records/... |
| conditions    | 纯 condition                  | 数据级访问 | /conditions/... |
| parameters    | ProcessParameter                 | 数据级 CRUD | /parameters/... |
| tunings       | 人工调机反馈                    | parameter 子资源 | /parameters/<pid>/tuning-feedback/ |
| algorithms    | 算法触发                       | 独立触发器 | /algorithms/... |
| rules         | 规则主数据                      | 主数据 | /rules/... |

设计原则 (2026-10-13):
- 业务对象 = 工艺记录 (records), 业务级 CRUD 走 records 段
- conditions 段 = 数据级访问 (list + 独立创建 + 详情 + 业务身份锁修改)
  - 与 records 段并存: 业务级 vs 数据级, 两条入口各自适用不同场景
- parameters 段 = 数据级 CRUD (URL 单段化, 独立对象)
  - 2026-10-12 拆除双段嵌套: 旧 /conditions/<id>/parameters/... 改为 /parameters/...
  - condition_id 退化为可选 query 过滤条件, 不在 URL 重复表达 belongs_to
  - service 函数不带 _in_condition 后缀, 仅凭 parameter_id 定位 + 可选过滤
  - tuning-feedback / parameter-tree: view + service 保留, 路由暂不挂出, 需要时再加回
- frontend/history/batch_delete 已移除: 都是冗余或低频
- algorithms 段保持多个独立触发器 (initialize / optimize / transplant), 智能调机 optimize 不合并入 tunings

业务区分:
- records/<id>/parameter-list/  = 工艺记录完整视图平铺 ({condition, parameters[]})   - 2026-10-12 新增
- records/<id>/parameter-tree/  = 工艺记录完整视图树形 ({condition, parameter_tree[]}) - 2026-10-12 新增
- 智能调机触发 = algorithms/optimize/  (algorithms 段, 独立算法触发)
- 人工调机反馈 = parameters/<pid>/tuning-feedback/  (parameter 子资源, 反映真实归属, 2026-10-12 拆除双段)

新增 records 段 (2026-10-12):
- 业务对象 = 工艺记录 (condition + first parameter 整体), 区别于纯 condition 段
- 仅 POST 录入端点, 其余接口服务待讨论
- 与 POST /processes/conditions/ 区别:
  - POST /processes/conditions/ : 纯 condition CRUD
  - POST /processes/records/    : 工艺记录业务 (condition + first parameter 整体)

URL 路由见 process/urls.py (以上表格仅为起点汇总, 不维护详细路径)。
"""
from django.utils.decorators import method_decorator

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
    parameter as parameter_service,  # 按 parameter_id 操作 (单条 + 版本树)
    parameter_transplant,
    rule,
    ParameterInitializeService,
    ParameterOptimizeService,
    TuningService,
)


# ============================================================
# 0. records 段 -- 业务对象 = 工艺记录 (condition + 最新 parameter 整体)
# ============================================================
#
# 业务定位 (2026-10-12 新增):
# - 业务对象 = 工艺记录, 不接受"独立 parameter"业务
# - 与 conditions 段并存: 业务级入口 vs 数据级访问, 两条入口各自适用不同场景
# - 列表 view_type (GET): 'parameter' / 'optimization'
# - 3 种 POST payload: {condition} / {condition, parameter} / 拒绝 {parameter} 或 {}
#
# URL 路由 (会变, 以 process/urls.py 为准):
# - list/create/batch_delete: /api/processes/records/
# - detail (get/put/delete):    /api/processes/records/<id>/
# - 完整视图 (parameter-list / parameter-tree) 挂在本段下, 是 records 业务的子视图
# ============================================================


class ProcessRecordListView(BaseView):
    """工艺记录列表 (GET) / 录入 (POST) - 业务对象 = 工艺记录 (condition [+ first parameter])

    GET  /api/processes/records/    -- 列表 (按 view_type 区分)
    POST /api/processes/records/    -- 录入 (condition 必填, parameter 可选)

    业务 (2026-10-12):
    - 业务名 = 工艺记录 (records)
    - 业务对象 = 工艺记录, 不接受"独立 parameter" 业务
    - 3 种 payload 场景 (POST):
      - { condition }           : 骨架 (后续 PUT 补全)
      - { condition, parameter }: 完整 (condition + first parameter 原子)
      - { parameter }           : 拒绝 (parameter 必须有 condition 归属)
      - {}                      : 拒绝 (condition 必填)
    - 列表 view_type (GET):
      - 'parameter'    : condition + latest parameter (工艺录入视图, 默认)
      - 'optimization' : condition + parameters_count (工艺优化视图)

    参考 ProjectListView / ConditionListView 风格, 1 个 view class 处理 list + create
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
        """批量删除工艺记录（按 condition_id, 级联软删其下 parameter）

        参考 ProjectListView 风格: list 端点同时处理 batch_delete
        URL: DELETE /api/processes/records/actions/batch-delete/  (与 BaseRequest 通用规则对齐, 2026-10-13)
        body: {"ids": [condition_id1, condition_id2, ...]}
        """
        return condition.batch_delete_condition(cleaned_data["ids"])


class ProcessRecordDetailView(BaseView):
    """工艺记录详情 (GET) / 修改 (PUT) / 软删 (DELETE)

    GET    /api/processes/records/<int:condition_id>/   -- 详情 (condition + 最新 parameter)
    PUT    /api/processes/records/<int:condition_id>/   -- 修改 (condition [+ 最新 parameter], 业务身份锁)
    DELETE /api/processes/records/<int:condition_id>/   -- 软删 condition (级联 parameter)

    参考 ProjectDetailView / ConditionDetailView 风格, 1 view class 处理 3 方法

    业务 (2026-10-12):
    - 业务名 = 工艺记录 (records)
    - 业务对象 = 工艺记录 (condition + 最新 parameter 整体)
    - <int:condition_id> = condition_id (业务聚合根, latest parameter 由 service 内部识别)
    - GET 返回 {condition, parameter: {setting_process}} 嵌套结构
      (语义 = "前端可填表结构", 与 get_condition_frontend 对齐)
    - PUT 业务身份锁:
      - condition 字段: 与 ProcessConditionWriteSchema 一致
        (允许 status, process_context; 锁定主关联 + 身份字段)
      - parameter 字段 (Optional, NEST 格式):
        * 不传 → 仅改 condition
        * 传 setting_process → 改 condition 下的"最新 parameter"
          (latest parameter_id 由 service 按 created_at desc 选第一条)
    - DELETE: 软删 condition (级联软删其下所有 parameter, 已有 service)
    """

    @method_decorator(require_login)
    def get(self, request, condition_id):
        """详情: 返回 condition + 最新 parameter (前端嵌套结构)

        复用 condition.get_condition_frontend (已有 service)
        返回结构: {condition: {...}, parameter: {setting_process: {...}}}
        """
        return condition.get_condition_frontend(condition_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionAndParameterSchema))
    def put(self, request, condition_id, cleaned_data):
        """修改工艺记录 (condition [+ 最新 parameter], 业务身份锁)

        body:
          - condition: 必填 (强验证, 10 字段, 业务身份锁字段会被 service 拦截)
          - parameter: 可选 (NEST: {setting_process: {...}})
            - 不传 → 仅改 condition
            - 传    → 改 condition + condition 下"最新 parameter"

        TODO: 待 service 层实现 update_record (业务身份锁 + 路由 condition/parameter 双写)
              或在 view 层组合调用 condition.update_condition + parameter_service.update_parameter_in_condition
        """
        condition_data = cleaned_data.get("condition") or {}
        parameter_data = cleaned_data.get("parameter")

        # 路由到 service.update_record (业务身份锁拦截 + condition/parameter 双写)
        return condition.update_record(
            condition_id,
            condition_data=condition_data,
            parameter_data=parameter_data,
        )

    @method_decorator(require_login)
    def delete(self, request, condition_id):
        """软删工艺记录 (级联软删其下所有 parameter)

        复用 condition.delete_condition (已有 service)
        """
        condition.delete_condition(condition_id)


class ProcessRecordParameterListView(BaseView):
    """工艺记录完整视图 (平铺) - GET

    GET /api/processes/records/<int:condition_id>/parameter-list/   -- 返回 {condition, parameters[]}
                                                    业务: 一次拿全部parameter (调机完整流水)

    2026-10-12 新增: 一体化业务视图 (与 records/<id>/ 同样以 records 业务为接口入口)
    - records/<id>/             -> 摘要视图 (condition + 最新 1 条 parameter)
    - records/<id>/parameter-list/ -> 完整视图 (condition + 全部 parameter, 平铺)
    """
    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition_with_parameter_list(condition_id)


class ProcessRecordParameterTreeView(BaseView):
    """工艺记录完整视图 (树形) - GET

    GET /api/processes/records/<int:condition_id>/parameter-tree/   -- 返回 {condition, parameter_tree[]}
                                                    业务: 拿参数迭代树 (parameter 父子关系)

    2026-10-12 新增: 一体化业务视图 (树形视图, 与 parameter-list 平级对称)
    - conditions/<id>/parameter-tree/  -> 仅 parameter 树 (数据级视图)
    - records/<id>/parameter-tree/     -> condition + parameter 树 (业务级视图)
    """
    @method_decorator(require_login)
    def get(self, request, condition_id):
        return condition.get_condition_with_parameter_tree(condition_id)


# ============================================================
# 1. conditions 段 -- 业务粒度 = 纯 condition (数据级访问)
# ============================================================
#
# 业务定位 (2026-10-13 反转, 恢复独立 CRUD 入口):
# - records 段    = 业务级入口 (condition + first parameter 整体, 创建/列表/软删/批量软删)
# - conditions 段 = 数据级访问 (list + 独立创建 + 详情 + 业务身份锁修改)
# - 软删入口走 records 段, 不在本段提供 (避免双口)
#
# 与 records 段区别 (POST):
# - /records/      业务级 (condition + first parameter 一起创建)
# - /conditions/   数据级 (仅 condition; 如需 first parameter 请走 records 段)
#
# URL 路由 (会变, 以 process/urls.py 为准):
# - list/create:          /api/processes/conditions/
# - detail (get/put):     /api/processes/conditions/<id>/
# ============================================================


class ConditionListView(BaseView):
    """工艺条件列表 (GET) / 独立创建 (POST) - 数据级访问 (2026-10-13 反转)

    GET  /api/processes/conditions/   -- 条件列表 (按 view_type 区分, 与 records 段共享 schema)
    POST /api/processes/conditions/   -- 独立创建 (仅 condition, parameter 字段被忽略)

    业务 (2026-10-13):
    - 与 records 段 ListView 共享 schema 和 service, 业务区别:
      - records 段: 业务级 (condition + first parameter 整体)
      - conditions 段: 数据级 (仅 condition, 不携带 parameter)
    - view_type 默认 'all' (纯 condition, 不带 latest parameter 详情)
      - 传 'parameter' / 'optimization' 也可, 复用 records 段业务视图
    - POST 接收 ProcessConditionAndParameterSchema, 但仅使用 condition 字段
      (如需 condition + first parameter 一起建, 请走 records 段)

    设计原则:
    - 不破坏 records 段"业务级"语义, 仅为纯数据级 CRUD 提供独立入口
    - service 层无新函数, 复用 condition.get_condition_list / condition.create_condition
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordListSchema))
    def get(self, request, cleaned_data):
        # conditions 段默认 view_type='all' (纯 condition, 不带 parameter 详情)
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
        # data-level 入口: 仅使用 condition, parameter 字段被忽略
        # 如需 condition + first parameter 一起建, 请走 records 段
        return condition.create_condition(
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
            condition=cleaned_data["condition"],
        )


class ConditionDetailView(BaseView):
    """工艺条件详情 (GET) / 修改 (PUT) - 纯 condition 数据级访问

    GET    /api/processes/conditions/<condition_id>/  -- 纯 condition 详情 (不带 latest parameter)
    PUT    /api/processes/conditions/<condition_id>/  -- 业务身份锁修改 (仅 condition 字段)

    业务 (2026-10-13 反转后保留):
    - 删除入口: 走 records 段 (DELETE /records/<id>/), 软删 + 级联 parameter
    - 列表/创建入口: 走本段 ConditionListView (2026-10-13 新增)
    - PUT 业务身份锁: 锁定主关联 (mold/machine/polymer/shot/injection_index) + 身份字段 (origin_type/condition_no)
      允许: status / process_context
    - parameter 更新走独立子端点: PUT /parameters/<parameter_id>/ (ParameterDetailView)
    """

    @method_decorator(require_login)
    def get(self, request, condition_id):
        """详情: 纯 condition (数据级, 不带 latest parameter)

        复用 condition.get_condition (已有 service)
        与 records/<id>/ 的区别: records GET 返回 condition + 最新 parameter
        """
        return condition.get_condition(condition_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionWriteSchema))
    def put(self, request, condition_id, cleaned_data):
        """业务身份锁修改 (仅 condition 字段)

        允许: status / process_context
        锁定: condition_no / origin_type / process_context_snapshot / mold_id / injection_machine_id / polymer_id / shot_index / injection_index
        """
        return condition.update_condition(condition_id, **cleaned_data)


# ============================================================
# 2. parameters 段 -- 业务对象 = ProcessParameter (数据级 CRUD)
# ============================================================
#
# 设计原则 (2026-10-12 拆除双段嵌套):
# - parameter 是独立业务对象 (自带 ID, 自带 process_condition_id 外键)
# - URL 单段化 (不嵌套 condition_id), 避免与数据库 FK 重复表达
# - condition_id 退化为可选 query 过滤条件, 不在 URL 重复表达 belongs_to
# - service 函数不带 _in_condition 后缀, 仅凭 parameter_id 定位 + 可选过滤
# - 写操作 (PUT/DELETE) 在 service 层校验归属 (parameter 自带 process_condition_id)
# - 基于 parameter 的视图 (frontend/history/tree) 挂本段下, 避免 "Condition*" 命名误导
#
# URL 路由 (会变, 以 process/urls.py 为准):
# - list/tree:        /api/processes/parameters/   (单段, 独立对象)
# - detail (单条):    /api/processes/parameters/<parameter_id>/
# ============================================================


class ParameterListView(BaseView):
    """parameter 列表 (GET) - 2026-10-12 URL 拆除双段嵌套

    GET /api/processes/parameters/?condition_id=<id>&...    -- 列出 parameter (可选 condition_id 过滤)

    与 tree 区别:
    - tree 返回树形结构 (用于调机树展示)
    - 本端点返回平铺列表 (用于参数详情页列出全部版本)

    支持过滤 (2026-10-12, 与 records list 风格一致):
    - condition_id:   过滤该 condition 下的 parameter (可选)
    - param_source:   参数来源 (manual / algorithm_init / system_inferred / ...)
    - seq_idx:        序列序号
    - parent_seq_idx: 父参数业务编号
    - param_code:     参数编号 (icontains)
    - created_after/before: 创建时间区间

    分页: page_no / page_size / sort (继承 PaginationBaseSchema)
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        total, items = parameter_service.list_parameters(**cleaned_data)
        return PaginationResponse(total=total, items=items)


class ParameterDetailView(BaseView):
    """parameter 单条 (GET) / 更新 (PUT) / 删除 (DELETE) - 2026-10-12 URL 拆除双段嵌套

    URL 单段端点 (仅凭 parameter_id 定位):
    - GET    /api/processes/parameters/<parameter_id>/   -- 参数详情
    - PUT    /api/processes/parameters/<parameter_id>/   -- 更新参数
    - DELETE /api/processes/parameters/<parameter_id>/   -- 软删参数

    设计依据 (2026-10-12):
    - parameter 是独立业务对象 (自带 ID, 自带 process_condition_id 外键)
    - URL 不再嵌套 condition_id, 避免与数据库 FK 重复表达
    - service 仅凭 parameter_id 定位, belongs_to 由 parameter 自带字段表达
    """

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


class ParameterTreeView(BaseView):
    """工艺参数版本树 - 2026-10-12 URL 拆除双段嵌套

    GET /api/processes/parameter-tree/?condition_id=<id>   -- 参数版本树 (parent_param_id 递归属关系)

    2026-10-12 URL 改造:
    - 旧: /conditions/<id>/parameters/tree/ (双段)
    - 新: /parameters/tree/ 独立段 (导出视图, condition_id 走 query)
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
# 与 algorithms/optimize 的关系 (2026-10-12 决定):
# - algorithms/optimize  智能调机 (独立算法触发器, 不合并入本段)
# - tunings/feedback     人工调机 (本段, 人工记录试模结果)
#
# 设计原则 (2026-10-12 拆除双段嵌套):
# - tuning 实际归属 parameter, 不挂 condition (避免李鬼归属)
# - URL 单段化: 参数挂 parameter, 不嵌套 condition_id
# - service 层校验 parameter.process_condition_id 等业务字段 (parameter 自带)
#
# URL 路由 (会变, 以 process/urls.py 为准):
# - feedback (post): /api/processes/parameters/<parameter_id>/tuning-feedback/
# ============================================================


class TuningFeedbackView(BaseView):
    """人工调机反馈 (POST) - 2026-10-12 URL 拆除双段嵌套

    POST /api/processes/parameters/<parameter_id>/tuning-feedback/
    body: {defect_feedbacks?, tuning_result?, result_detail?}

    2026-10-12 URL 调整历史:
    - v1: /conditions/<id>/tunings/feedback/ (tuning 实际属于 parameter, 挂 condition 是李鬼归属)
    - v2: /conditions/<id>/parameters/<pid>/tuning-feedback/ (tuning 在 parameter 下面, 反映真实归属)
    - v3: /parameters/<pid>/tuning-feedback/ (URL 单段化, parameter 是独立业务对象)

    业务区分:
    - 智能调机触发 = algorithms/optimize/  (algorithms 段, 独立算法)
    - 人工调机反馈 = parameters/<pid>/tuning-feedback/  (parameter 子资源, 人工记录)

    安全: service 层仍校验 parameter.process_condition_id 等业务字段 (parameter 自带)
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
# 4. algorithms 段 -- 3 method (3 path, 纯 POST 触发)
# ============================================================
# 段名: processes/algorithms/  无 URL 变量 (参数在 body)
# 业务: 智能算法的触发 (initialize / optimize / transplant)
#
# - algorithms/initialize  从 masterdata 启动算法, 推导首条 parameter
# - algorithms/optimize    智能调机 (条件内算法推理, 2026-10-12 决定不合并入 tunings 段)
# - algorithms/transplant  跨机器工艺参数移植
# ============================================================


class AlgorithmsInitializeView(BaseView):
    """算法初始化 (POST)

    POST /api/processes/algorithms/initialize/   -- 工艺参数初始化算法
    body: {mold_id, injection_machine_id, polymer_id, shot_index?, injection_index?, process_set?}

    业务: 从 masterdata ID 启动算法, 推导第一条工艺参数
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializeFromMasterdataSchema))
    def post(self, request, cleaned_data):
        return ParameterInitializeService.infer(
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
    """算法初始化-从源 condition 复制（POST）

    POST /api/processes/algorithms/initialize-from-condition/
    body: {source_condition_id, process_set?}

    业务: 复用历史合格工艺作为新工艺起点，不调推理算法。
    为保证数据不过时，service 层会用最新 masterdata 重建快照。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializeFromConditionSchema))
    def post(self, request, cleaned_data):
        return ParameterInitializeService.infer_from_condition(
            source_condition_id=cleaned_data["source_condition_id"],
            process_set=cleaned_data.get("process_set"),
            company_id=request.user.company_id,
            organization_id=request.user.organization_id,
        )


class AlgorithmsInitializeFromProvidedView(BaseView):
    """算法初始化-纯推理（POST）

    POST /api/processes/algorithms/initialize-from-provided/
    body: {mold_info, machine_info, polymer_info, process_set}

    业务: 调用方提供完整数据，后端纯推理，不查库不落库。
    适用场景：第三方系统集成（无 masterdata）、算法试算。
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessInitializeFromProvidedSchema))
    def post(self, request, cleaned_data):
        return ParameterInitializeService.infer_from_provided(
            mold_info=cleaned_data["mold_info"],
            machine_info=cleaned_data["machine_info"],
            polymer_info=cleaned_data["polymer_info"],
            process_set=cleaned_data.get("process_set"),
        )


class AlgorithmsOptimizeView(BaseView):
    """算法优化 (智能推理) (POST)

    POST /api/processes/algorithms/optimize/   -- 工艺参数优化算法 (调机推理)
    body: {condition_id, parent_seq_idx, parameter?, feedback?}

    业务: 智能优化算法触发 (vs 人工反馈 = tunings/feedback/<condition_id>/)
    命名: optimize (优化) 而非 tuning (调机) -- 业内术语"工艺参数优化算法"。

    2026-10-12 决定: 本端点保持独立, 不合并入 tunings 段 (独立算法触发器价值更高)
    """
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessOptimizeFromConditionSchema))
    def post(self, request, cleaned_data):
        service = ParameterOptimizeService()
        return service.infer(
            condition_id=cleaned_data["condition_id"],
            parent_seq_idx=cleaned_data["parent_seq_idx"],
            parameter=cleaned_data.get("parameter"),
            feedback=cleaned_data.get("feedback"),
        )


class AlgorithmsTransplantView(BaseView):
    """算法移植 (POST)

    POST /api/processes/algorithms/transplant/   -- 工艺参数移植算法
    body: {source_parameter_id, target_machine_spec}

    业务: 把某个 parameter 移植到目标机器 (算法适配)
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(TransplantRequestSchema))
    def post(self, request, cleaned_data):
        return parameter_transplant.transplant_process_parameter(
            source_parameter_id=cleaned_data["source_parameter_id"],
            target_machine_spec=cleaned_data["target_machine_spec"],
        )
