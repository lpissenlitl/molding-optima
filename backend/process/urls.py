"""
molding-optima process URL 路由

设计原则 (2026-10-09 重构):
- 段名 = 业务名 = 查询 type
- 变量 = 实际查询粒度 (condition_id)
- 避免"万能接口", 每个业务场景用独立 URL 段表达

API 路径总览:
- /api/processes/record/                          -- 工艺记录列表 (GET) / 录入 (POST)
- /api/processes/record/<condition_id>/           -- 工艺记录详情/修改/删除

- /api/processes/rules/keywords/
- /api/processes/rules/methods/
- /api/processes/rules/by-defect/
- /api/processes/rule-libraries/
- /api/processes/rule-libraries/<id>/
- /api/processes/rule-libraries/<id>/methods/
- /api/processes/rule-methods/<id>/
- /api/processes/rule-libraries/<id>/expert-rules/
- /api/processes/expert-rules/<id>/

【2026-10-09 暂注的旧 URL】
原 design 混用 condition/parameter/optimization/tuning 多个段名,
业务场景不分, URL 命名错位。
新 design 按"业务粒度=condition"重设计, 仅保留 2 个 path:
- /api/processes/record/                  (GET + POST)
- /api/processes/record/<id>/             (GET + PUT + DELETE)
注: 仪表板统计已迁出 -- 详见 dashboard.urls (/api/dashboard/process-statistics/)
"""
from django.urls import path

from .views.processes import (
    # 工艺记录 (record 业务粒度) - 6 个 method 接口 (本轮新增)
    ParameterRecordListView,
    ParameterRecordDetailView,
    # 工艺参数 (parameter 业务粒度) - 5 个 method 接口 (本轮新增, view 占位)
    ParameterListCreateView,
    ParameterDetailView,
    # condition 维度 (暂未使用, URL 已暂注, 后续清理)
    ConditionListView,
    ConditionCreateView,
    ConditionDetailView,
    ConditionBatchDeleteView,
    ConditionInitializeView,
    ConditionTransplantView,
    ParameterTreeView,
    OptimizationListView,
    OptimizationDetailView,
    OptimizationHistoryView,
    OptimizationInferView,
    ProcessTuningRecordView,
    # 规则管理
    RuleKeywordListView,
    RuleMethodListView,
    RuleByDefectView,
)
from .views.rule_libraries import (
    RuleLibraryListView,
    RuleLibraryDetailView,
)
from .views.rule_methods import (
    RuleMethodListByLibraryView,
    RuleMethodDetailView,
)
from .views.expert_rules import (
    ExpertRuleListByLibraryView,
    ExpertRuleDetailView,
)


urlpatterns = [
    # =============================================================
    # 【 2026-10-09 新增 - 工艺记录 (按 condition 业务粒度)】
    # ---------------------------------------------------------
    # 段名: processes/record/ (业务名"工艺记录")
    # 变量: condition_id (业务粒度=condition)
    # 5 个 method 接口 (2 个 path):
    #
    #   1. POST   /processes/record/                          -- 录入
    #   2. GET    /processes/record/                          -- 列表
    #   3. GET    /processes/record/<condition_id>/           -- 详情
    #   4. PUT    /processes/record/<condition_id>/           -- 修改
    #   5. DELETE /processes/record/<condition_id>/           -- 删除
    # =============================================================
    path("processes/record/", ParameterRecordListView.as_view()),
    path("processes/record/<int:condition_id>/", ParameterRecordDetailView.as_view()),
    # =============================================================
    # 新增结束 - 下面是 parameter 段
    # =============================================================

    # =============================================================
    # 【 2026-10-09 新增 - 工艺参数 (按 parameter 业务粒度)】
    # ---------------------------------------------------------
    # 段名: processes/parameter/ (业务名"工艺参数")
    # 变量: parameter_id (业务粒度=parameter)
    # 5 个 method 接口 (2 个 path):
    #
    #   1. POST   /processes/parameter/                  -- 录入
    #   2. GET    /processes/parameter/                  -- 列表
    #   3. GET    /processes/parameter/<parameter_id>/   -- 详情
    #   4. PUT    /processes/parameter/<parameter_id>/   -- 修改
    #   5. DELETE /processes/parameter/<parameter_id>/   -- 删除
    # =============================================================
    path("processes/parameter/", ParameterListCreateView.as_view()),
    path("processes/parameter/<int:parameter_id>/", ParameterDetailView.as_view()),
    # =============================================================
    # parameter 段新增结束 - 下面是 optimization 段
    # =============================================================

    # =============================================================
    # 【 2026-10-09 新增 - 工艺优化 (optimization 业务)】
    # ---------------------------------------------------------
    # 段名: processes/optimization/ (业务名"工艺优化")
    # 变量: condition_id (业务粒度=condition)
    # 本轮先列 2 个 method 接口 (2 个 path):
    #
    #   1. GET /processes/optimization/                       -- 列表
    #   2. GET /processes/optimization/<condition_id>/        -- 详情
    # 后续再加 POST/PUT/DELETE/infer/history/tree/initialize/transplant/feedback
    # =============================================================
    path("processes/optimization/", OptimizationListView.as_view()),
    path("processes/optimization/<int:condition_id>/", OptimizationDetailView.as_view()),
    # =============================================================
    # optimization 段新增结束 - 下面是 rules 保留段
    # =============================================================

    # ========== 规则管理 (list/create; detail/update/delete 由 v2 rule_libraries 接管) ==========
    path("processes/rules/keywords/", RuleKeywordListView.as_view()),
    path("processes/rules/methods/", RuleMethodListView.as_view()),
    path("processes/rules/by-defect/", RuleByDefectView.as_view()),

    # ========== 规则中心 (v2: 2026-09-14 重构, 拆为规则库 + 规则方法 + 专家规则) ==========
    # 规则库 (Section 1 卡片视图)
    path("processes/rule-libraries/", RuleLibraryListView.as_view()),
    path("processes/rule-libraries/<int:rule_library_id>/", RuleLibraryDetailView.as_view()),
    # 库下规则方法 (详情页 Tab 1)
    path("processes/rule-libraries/<int:rule_library_id>/methods/", RuleMethodListByLibraryView.as_view()),
    # 规则方法详情 (独立 URL, 便于更新/删除)
    path("processes/rule-methods/<int:rule_method_id>/", RuleMethodDetailView.as_view()),
    # 库下专家规则 (详情页 Tab 2)
    path("processes/rule-libraries/<int:rule_library_id>/expert-rules/", ExpertRuleListByLibraryView.as_view()),
    # 专家规则详情 (独立 URL, 避免与库路径冲突)
    path("processes/expert-rules/<int:expert_rule_id>/", ExpertRuleDetailView.as_view()),
]
