from django.urls import path
from process import views

urlpatterns = [
    # 工艺记录
    path('processes/parameter/<int:condition_id>/', views.ProcessParameterDetailView.as_view()),
    path('processes/parameter/', views.ProcessParameterListView.as_view()),
    path('processes/parameter/batch_delete/', views.ProcessParameterListView.as_view()),
]