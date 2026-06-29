from django.urls import path
from masterdata import views

urlpatterns = [
    # --- 项目管理 ---
    path("projects/<int:project_id>/", views.ProjectDetailView.as_view()),
    path("projects/", views.ProjectListView.as_view()),
    path("projects/actions/batch-delete/", views.ProjectListView.as_view()),
    # --- 模具管理 ---
    path("molds/<int:mold_id>/", views.MoldDetailView.as_view()),
    path("molds/", views.MoldListView.as_view()),
    path("molds/actions/batch-delete/", views.MoldListView.as_view()),
    # --- 材料管理 ---
    path("polymers/<int:polymer_id>/", views.PolymerDetailView.as_view()),
    path("polymers/", views.PolymerListView.as_view()),
    path("polymers/actions/batch-delete/", views.PolymerListView.as_view()),
    # --- 填充物管理 ---
    path("fillers/<int:filler_id>/", views.FillerDetailView.as_view()),
    path("fillers/", views.FillerListView.as_view()),
    path("fillers/actions/batch-delete/", views.FillerListView.as_view()),
    # --- 注塑机管理 ---
    path("injection-machines/<int:injection_machine_id>/", views.InjectionMachineDetailView.as_view()),
    path("injection-machines/", views.InjectionMachineListView.as_view()),
    path("injection-machines/actions/batch-delete/", views.InjectionMachineListView.as_view()),
    # --- 辅助设备管理 ---
    path("auxiliary-equipments/<int:auxiliary_equipment_id>/", views.AuxiliaryEquipmentDetailView.as_view()),
    path("auxiliary-equipments/", views.AuxiliaryEquipmentListView.as_view()),
    path("auxiliary-equipments/actions/batch-delete/", views.AuxiliaryEquipmentListView.as_view()),
]