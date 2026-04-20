from django.urls import path

from mdprocess.views import (
    process_index_views,
    process_record_views,
    process_optimize_views,
    process_expert_views,
    machine_com_views,
    rule_views,
    inovance_views
)

urlpatterns = [

    path("process_index/", process_index_views.ProcessIndexListView.as_view()),
    path("process_index/<int:process_index_id>/", process_index_views.ProcessIndexDetailView.as_view()),

    path("record_process/", process_record_views.ProcessRecordDetailView.as_view()),
    path("record_process/<int:process_index_id>/", process_record_views.ProcessRecordDetailView.as_view()),
    path("optimize_process/", process_optimize_views.ProcessOptimizeDetailView.as_view()),
    path("optimize_process/<int:process_index_id>/", process_optimize_views.ProcessOptimizeDetailView.as_view()),
    path("expert_process/", process_expert_views.ProcessExpertDetailView.as_view()),
    path("expert_process/<int:process_index_id>/", process_expert_views.ProcessExpertDetailView.as_view()),

    path("algorithm/initial/", process_optimize_views.ProcessInitialAlgorithmView.as_view()),
    path("algorithm/optimize/", process_optimize_views.ProcessOptimizeAlgorithmView.as_view()),

    path("rule_keyword/", rule_views.RuleKeywordListView.as_view()),
    path("rule_keyword/<int:rule_keyword_id>/", rule_views.RuleKeywordDetailView.as_view()),
    path("rule_method/", rule_views.RuleMethodListView.as_view()),
    path("rule_method_delete/<str:subrule_no>/", rule_views.RuleMethodListView.as_view()),
    path("rule_method/<int:rule_id>/", rule_views.RuleMethodDetailView.as_view()),
    path("rule_flow/", rule_views.RuleFlowView.as_view()),
    path("mes_process/", machine_com_views.MachineMesView.as_view()),
    
    # --- Inovance ---
    path("inovance/molds/", inovance_views.ProjectDetailView.as_view()),
    path("inovance/molds/<int:project_id>/", inovance_views.ProjectDetailView.as_view()),
    path("inovance/polymers/", inovance_views.PolymerDetailView.as_view()),
    path("inovance/polymers/<int:polymer_id>/", inovance_views.PolymerDetailView.as_view()),
    path("inovance/initialize-process/", inovance_views.ProcessInitialAlgorithmView.as_view()),
    path("inovance/optimize-process/", inovance_views.ProcessOptimizeAlgorithmView.as_view()),
]
