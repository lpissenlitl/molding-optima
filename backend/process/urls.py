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

molding-optima 独有功能：
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
    # ========== 工艺记录（对齐 molding-expert 4-16）==========
    path("processes/parameter/", ProcessParameterListView.as_view()),
    path("processes/parameter/frontend/", ProcessParameterCreateView.as_view()),
    path("processes/parameter/<int:condition_id>/", ProcessParameterDetailView.as_view()),
    path("processes/parameter/<int:condition_id>/flat/", ProcessParameterFlatView.as_view()),
    path("processes/parameter/<int:condition_id>/frontend/", ProcessParameterFrontendView.as_view()),
    path("processes/parameter/batch_delete/", ProcessParameterBatchDeleteView.as_view()),

    # ========== 工艺移植（对齐 molding-expert）==========
    path("processes/parameter/transplant/", ProcessTransplantView.as_view()),

    # ========== 规则管理（molding-optima 独有）==========
    path("processes/rules/keywords/", RuleKeywordListView.as_view()),
    path("processes/rules/keywords/<int:rule_keyword_id>/", RuleKeywordDetailView.as_view()),
    path("processes/rules/methods/", RuleMethodListView.as_view()),
    path("processes/rules/methods/<int:rule_method_id>/", RuleMethodDetailView.as_view()),
    path("processes/rules/by-defect/", RuleByDefectView.as_view()),

    # ========== 工艺优化（molding-optima 独有）==========
    path("processes/optimization/<int:condition_id>/", ProcessOptimizationView.as_view()),
    path("processes/optimization/<int:condition_id>/history/", ProcessOptimizationHistoryView.as_view()),

    # ========== 专家调优（molding-optima 独有）==========
    path("processes/expert/suggestion/", ProcessExpertSuggestionView.as_view()),
    path("processes/expert/defect-template/", ProcessExpertDefectTemplateView.as_view()),
    path("processes/expert/create/", ProcessExpertCreateView.as_view()),
]