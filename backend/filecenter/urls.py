from django.urls import path
from filecenter import views


urlpatterns = [
    # ==================== 用户认证接口（需要登录）====================
    path("files/", views.FileListView.as_view()),
    path("files/<uuid:uuid>/", views.FileDetailView.as_view()),
    path("files/<uuid:uuid>/download/", views.FileDownloadView.as_view()),
    path("files/<uuid:uuid>/preview/", views.FilePreviewView.as_view()),
    
    # ==================== 租户认证接口（无需登录，使用 Token）====================
    path("tenant/files/<uuid:uuid>/download/", views.TenantFileDownloadView.as_view(), name='tenant-file-download'),
    path("tenant/files/<uuid:uuid>/preview/", views.TenantFilePreviewView.as_view(), name='tenant-file-preview'),
]