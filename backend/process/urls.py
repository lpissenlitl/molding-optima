"""molding-optima process URL 路由

URL 段架构 (2026-10-13):
- records/                   业务级入口 (condition + parameter 整体)
- conditions/                数据级访问 (纯 condition 字段级, 含 list + 独立创建)
- parameters/                数据级访问 (独立对象, 单段 URL)
- algorithms/                算法触发器 (initialize / optimize / transplant)
- rules/{keywords,methods,rule-libraries,expert-rules}/   规则主数据

设计原则:
- 业务级 CRUD 走 records 段, 纯数据级 CRUD 走 conditions / parameters 段
- parameter 是独立业务对象, URL 单段化, condition_id 退化为可选 query 过滤
- parameter-tree / tuning-feedback: view + service 保留, 路由暂不挂出, 需要时再加回
"""
from django.urls import path

from .views.processes import (
    ProcessRecordListView,
    ProcessRecordDetailView,
    ProcessRecordParameterListView,
    ProcessRecordParameterTreeView,
    ConditionListView,
    ConditionDetailView,
    ParameterListView,
    ParameterDetailView,
    ParameterTreeView,
    TuningFeedbackView,
    AlgorithmsInitializeView,
    AlgorithmsInitializeFromConditionView,
    AlgorithmsInitializeFromProvidedView,
    AlgorithmsOptimizeView,
    AlgorithmsTransplantView,
)
from .views.rules import (
    RuleKeywordListView,
    RuleKeywordDetailView,
    RuleMethodListView,
    RuleMethodDetailView,
    RuleLibraryListView,
    RuleLibraryDetailView,
    ExpertRuleListView,
    ExpertRuleDetailView,
)


urlpatterns = [
    # records 业务段
    path("processes/records/", ProcessRecordListView.as_view()),
    path("processes/records/actions/batch-delete/", ProcessRecordListView.as_view()),
    path("processes/records/<int:condition_id>/", ProcessRecordDetailView.as_view()),
    path("processes/records/<int:condition_id>/parameter-list/", ProcessRecordParameterListView.as_view()),
    path("processes/records/<int:condition_id>/parameter-tree/", ProcessRecordParameterTreeView.as_view()),

    # conditions 数据级 (独立创建/查询, 2026-10-13 接入)
    path("processes/conditions/", ConditionListView.as_view()),
    path("processes/conditions/<int:condition_id>/", ConditionDetailView.as_view()),

    # parameters 数据级 (URL 单段化, condition_id 走 query 可选)
    path("processes/parameters/", ParameterListView.as_view()),
    path("processes/parameters/<int:parameter_id>/", ParameterDetailView.as_view()),
    # 人工调机反馈: tuning 业务上属于 parameter, 挂 parameter 段下 (2026-10-12 URL 单段化)
    path("processes/parameters/<int:parameter_id>/tuning-feedback/", TuningFeedbackView.as_view()),
    # 参数版本树: view + service 保留, 路由暂不挂出, 需要时再加回

    # algorithms 段
    path("processes/algorithms/initialize/", AlgorithmsInitializeView.as_view()),
    path("processes/algorithms/initialize-from-condition/", AlgorithmsInitializeFromConditionView.as_view()),
    path("processes/algorithms/initialize-from-provided/", AlgorithmsInitializeFromProvidedView.as_view()),

    path("processes/algorithms/optimize/", AlgorithmsOptimizeView.as_view()),
    
    path("processes/algorithms/transplant/", AlgorithmsTransplantView.as_view()),

    # rules 段
    path("processes/rules/keywords/", RuleKeywordListView.as_view()),
    path("processes/rules/keywords/<int:rule_keyword_id>/", RuleKeywordDetailView.as_view()),
    path("processes/rules/methods/", RuleMethodListView.as_view()),
    path("processes/rules/methods/<int:rule_method_id>/", RuleMethodDetailView.as_view()),
    path("processes/expert-rules/", ExpertRuleListView.as_view()),
    path("processes/expert-rules/<int:expert_rule_id>/", ExpertRuleDetailView.as_view()),
    path("processes/rule-libraries/", RuleLibraryListView.as_view()),
    path("processes/rule-libraries/<int:rule_library_id>/", RuleLibraryDetailView.as_view()),
]
