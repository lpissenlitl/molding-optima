"""
molding-optima process URL 路由

API 路径说明（对齐 molding-expert 风格）：
- /api/processes/parameter/                        → 工艺参数列表（GET）/创建（POST）
- /api/processes/parameter/frontend/               → 工艺参数前端创建（POST，molding-expert 风格）
- /api/processes/parameter/<int:condition_id>/     → 工艺参数详情（GET/PUT/DELETE）
- /api/processes/parameter/<int:condition_id>/flat/ → 工艺参数扁平视图（molding-expert 风格）
- /api/processes/parameter/<int:condition_id>/frontend/ → 工艺参数前端视图（molding-expert 风格）
- /api/processes/parameter/batch_delete/           → 工艺参数批量删除
- /api/processes/parameter/transplant/             → 工艺参数移植
- /api/processes/initialization/from-source-condition/ → 工艺参数初始化（基于源 condition 复制）
- /api/processes/initialization/from-masterdata/      → 工艺参数初始化（基于 masterdata ID）
- /api/processes/initialization/infer/                → 工艺参数纯推理（不查库不落库）

molding-optima 独有功能：
- /api/processes/optimization/infer/                → 工艺优化 infer（调用链路编排）
- /api/processes/optimization/<id>/                → 工艺优化
- /api/processes/optimization/<id>/history/       → 工艺优化历史
- /api/processes/expert/suggestion/                → 专家调优建议
- /api/processes/expert/defect-template/           → 缺陷模板
- /api/processes/expert/create/                    → 专家调优创建
- /api/processes/rules/keywords/                   → 规则关键词
- /api/processes/rules/keywords/<id>/              → 规则关键词详情
- /api/processes/rules/methods/                    → 规则方法
- /api/processes/rules/methods/<id>/               → 规则方法详情
- /api/processes/rules/by-defect/                  → 按缺陷查询规则
"""
from django.urls import path

from .views.processes import (
    ProcessParameterCreateView,
    ProcessParameterListView,
    ProcessParameterDetailView,
    ProcessParameterFlatView,
    ProcessParameterFrontendView,
    ProcessParameterBatchDeleteView,
    ProcessTransplantView,
    ProcessInitializationFromSourceConditionView,
    ProcessInitializationFromMasterdataView,
    ProcessInitializationInferView,
    ProcessOptimizationView,
    ProcessOptimizationHistoryView,
    ProcessExpertSuggestionView,
    ProcessExpertDefectTemplateView,
    ProcessExpertCreateView,
    ProcessOptimizationInferView,
    RuleKeywordListView,
    RuleKeywordDetailView,
    RuleMethodListView,
    RuleMethodDetailView,
    RuleByDefectView,
    DashboardStatisticsView,
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
    # ========== 工艺记录（对齐 molding-expert 4-16）==========
    path("processes/parameter/", ProcessParameterListView.as_view()),
    path("processes/parameter/frontend/", ProcessParameterCreateView.as_view()),
    path("processes/parameter/<int:condition_id>/", ProcessParameterDetailView.as_view()),
    path("processes/parameter/<int:condition_id>/flat/", ProcessParameterFlatView.as_view()),
    path("processes/parameter/<int:condition_id>/frontend/", ProcessParameterFrontendView.as_view()),
    path("processes/parameter/batch_delete/", ProcessParameterBatchDeleteView.as_view()),

    # ========== 工艺移植（对齐 molding-expert）==========
    path("processes/parameter/transplant/", ProcessTransplantView.as_view()),

    # ========== 工艺参数初始化（molding-optima 独有，基于规则推理）==========
    # /initialization/from-source-condition/ → Mode C：基于源 condition 复制初始工艺（不调推理）
    # /initialization/from-masterdata/       → Mode B：基于 masterdata ID（创建 Condition + 落库）
    # /initialization/infer/                 → 纯推理（不查库不落库）：前端传完整数据
    path("processes/initialization/from-source-condition/", ProcessInitializationFromSourceConditionView.as_view()),
    path("processes/initialization/from-masterdata/", ProcessInitializationFromMasterdataView.as_view()),
    path("processes/initialization/infer/", ProcessInitializationInferView.as_view()),

    # ========== 规则管理（molding-optima 独有）==========
    path("processes/rules/keywords/", RuleKeywordListView.as_view()),
    path("processes/rules/keywords/<int:rule_keyword_id>/", RuleKeywordDetailView.as_view()),
    path("processes/rules/methods/", RuleMethodListView.as_view()),
    path("processes/rules/methods/<int:rule_method_id>/", RuleMethodDetailView.as_view()),
    path("processes/rules/by-defect/", RuleByDefectView.as_view()),

    # ========== 工艺优化（molding-optima 独有）==========
    path("processes/optimization/<int:condition_id>/", ProcessOptimizationView.as_view()),
    path("processes/optimization/<int:condition_id>/history/", ProcessOptimizationHistoryView.as_view()),
    # /optimization/infer/ —— infer 调用链路编排（2026-09-23 轮 5）
    path("processes/optimization/infer/", ProcessOptimizationInferView.as_view()),

    # ========== 专家调优（molding-optima 独有）==========
    path("processes/expert/suggestion/", ProcessExpertSuggestionView.as_view()),
    path("processes/expert/defect-template/", ProcessExpertDefectTemplateView.as_view()),
    path("processes/expert/create/", ProcessExpertCreateView.as_view()),

    # ========== 仪表板统计 ==========
    # /statistics/dashboard/ —— 一次返回 trend + origin 聚合（供前端 ECharts 使用）
    path("processes/statistics/dashboard/", DashboardStatisticsView.as_view()),

    # ========== 规则中心（v2：2026-09-14 重构，拆为规则库 + 规则方法 + 专家规则）==========
    # 规则库（Section 1 卡片视图）
    path("processes/rule-libraries/", RuleLibraryListView.as_view()),
    path("processes/rule-libraries/<int:rule_library_id>/", RuleLibraryDetailView.as_view()),
    # 库下规则方法（详情页 Tab 1）
    path("processes/rule-libraries/<int:rule_library_id>/methods/", RuleMethodListByLibraryView.as_view()),
    # 规则方法详情（独立 URL，便于更新/删除）
    path("processes/rule-methods/<int:rule_method_id>/", RuleMethodDetailView.as_view()),
    # 库下专家规则（详情页 Tab 2）
    path("processes/rule-libraries/<int:rule_library_id>/expert-rules/", ExpertRuleListByLibraryView.as_view()),
    # 专家规则详情（独立 URL，避免与库路径冲突）
    path("processes/expert-rules/<int:expert_rule_id>/", ExpertRuleDetailView.as_view()),
]