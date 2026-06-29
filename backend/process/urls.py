"""
molding-optima process URL 路由

API 路径说明：
- /api/process/conditions/  → 工艺条件 CRUD（统一索引表，含工艺身份信息）
- /api/process/parameters/  → 工艺参数 CRUD
- /api/process/transplant/  → 工艺参数移植
- /api/process/optimization/ → 工艺优化
- /api/process/expert/      → 专家调优
- /api/process/rules/       → 规则管理

注：ProcessIndex 已合并到 ProcessCondition。
"""
from django.urls import path

from .views.processes import (
    ProcessConditionListView,
    ProcessConditionDetailView,
    ProcessParameterCreateView,
    ProcessParameterListView,
    ProcessParameterDetailView,
    ProcessParameterBatchDeleteView,
    ProcessConditionAndParameterCreateView,
    ProcessTransplantView,
    ProcessOptimizationView,
    ProcessOptimizationHistoryView,
    ProcessExpertSuggestionView,
    ProcessExpertDefectTemplateView,
    ProcessExpertCreateView,
    RuleKeywordListView,
    RuleKeywordDetailView,
    RuleMethodListView,
    RuleMethodDetailView,
    RuleByDefectView,
)


urlpatterns = [
    # ========== 工艺条件与参数 ==========
    path("conditions/", ProcessConditionListView.as_view()),
    path("conditions/<int:condition_id>/", ProcessConditionDetailView.as_view()),
    path("conditions/with-parameter/", ProcessConditionAndParameterCreateView.as_view()),
    path("parameters/", ProcessParameterListView.as_view()),
    path("parameters/create/", ProcessParameterCreateView.as_view()),
    path("parameters/<int:parameter_id>/", ProcessParameterDetailView.as_view()),
    path("parameters/batch-delete/", ProcessParameterBatchDeleteView.as_view()),

    # ========== 工艺移植 ==========
    path("transplant/", ProcessTransplantView.as_view()),

    # ========== 工艺优化 ==========
    path("optimization/<int:condition_id>/", ProcessOptimizationView.as_view()),
    path("optimization/<int:condition_id>/history/", ProcessOptimizationHistoryView.as_view()),

    # ========== 专家调优 ==========
    path("expert/suggestion/", ProcessExpertSuggestionView.as_view()),
    path("expert/defect-template/", ProcessExpertDefectTemplateView.as_view()),
    path("expert/create/", ProcessExpertCreateView.as_view()),

    # ========== 规则管理 ==========
    path("rules/keywords/", RuleKeywordListView.as_view()),
    path("rules/keywords/<int:rule_keyword_id>/", RuleKeywordDetailView.as_view()),
    path("rules/methods/", RuleMethodListView.as_view()),
    path("rules/methods/<int:rule_method_id>/", RuleMethodDetailView.as_view()),
    path("rules/by-defect/", RuleByDefectView.as_view()),
]