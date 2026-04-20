from django.urls import path, include

urlpatterns = [
    path("admin/", include("gis.admin.urls")),
    path("molding/", include("hsmolding.urls")),
    path("molding/", include("mdprocess.urls")),
]
