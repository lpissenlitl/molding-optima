from django.urls import path

from hsmolding.views import (
    machine_views,
    auxiliary_views,
    polymer_views,
    project_views,
    option_views,
    media_views,
    export_views,
    machine_trial_views,
    moldflow_views,
)
from mdprocess.views import process_record_views, rule_views


urlpatterns = [
    # 工程相关--模具信息
    path("projects/", project_views.ProjectListView.as_view()),
    path("projects/<int:project_id>/", project_views.ProjectDetailView.as_view()),

    # 界面下拉选项相关--给一些selection专门提供API
    path("options/", option_views.SelectOptionView.as_view()),
    path("options/<str:option_name>/", option_views.SelectOptionView.as_view()),

    # 机器相关
    path("machines/", machine_views.MachineListView.as_view()),
    path("machines/<int:machine_id>/", machine_views.MachineDetailView.as_view()),

    # 辅机相关
    path("auxiliaries/", auxiliary_views.AuxiliaryListView.as_view()),
    path("auxiliaries/<int:auxiliary_id>/", auxiliary_views.AuxiliaryDetailView.as_view()),

    # 材料相关
    path("polymers/", polymer_views.PolymerListView.as_view()),
    path("polymers/<int:polymer_id>/", polymer_views.PolymerDetailView.as_view()),

    # 机器性能测试
    path("machine_trials/", machine_trial_views.MachineTrialListView.as_view()),
    path("machine_trials/<int:machine_trial_id>/", machine_trial_views.MachineTrialListView.as_view()),
    path("machine_trials/<str:machine_trial_type>/", machine_trial_views.MachineTrialDetailView.as_view()),

    # 上传 视频、照片、报告
    path("upload_file/", media_views.FileServiceView.as_view()),
    path("upload_file/<int:file_id>/", media_views.FileServiceView.as_view()),

    # 从excel导入 模具、机器、胶料、工艺
    path("upload/mold/", project_views.ProjectDetailView.as_view()),
    path("upload/machine/", machine_views.MachineDetailView.as_view()),
    path("upload/polymer/", polymer_views.PolymerDetailView.as_view()),
    path("upload/process/", process_record_views.ProcessRecordView.as_view()),
    path("upload/rule/", rule_views.ImportRuleView.as_view()),

    # 导出相关
    path("export/mold/<int:project_id>/", export_views.MoldInfoExportView.as_view()),  # 根据模具id导出excel文件
    path("export/mold/", export_views.MoldInfoExportView.as_view()),  # 根据模具信息导出excel文件
    path("export/machine/<int:machine_id>/", export_views.MachineExportView.as_view()),  # 根据机器id导出excel文件
    path("export/machine/", export_views.MachineExportView.as_view()),  # 根据机器信息导出excel文件
    path("export/polymer/<int:polymer_id>/", export_views.PolymerExportView.as_view()),  # 根据胶料id导出excel文件
    path("export/polymer/", export_views.PolymerExportView.as_view()),  # 根据胶料信息导出excel文件
    path("export/process/<int:process_id>/", export_views.ProcessExportView.as_view()),  # 根据工艺id导出excel文件
    path("export/process/", export_views.ProcessExportView.as_view()),  # 根据工艺信息导出excel文件
    path("export/rule/", export_views.RuleView.as_view()),  # 根据subrule_no导出excel文件

    # 模流相关
    path("moldflow/", moldflow_views.MoldflowView.as_view()),  # 读取vbs txt
    path("moldflow/<str:mold_no>/<int:project_id>/", moldflow_views.ImportMoldflowView.as_view()),  # 上传vbs txt
    path("moldflow_list/", moldflow_views.MoldflowListView.as_view()),  # 读取一个模具的多个模流文件
]
