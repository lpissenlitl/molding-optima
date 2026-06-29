from django.urls import path
from identity import views

urlpatterns = [
    # 用户注册、登录、登出
    path("register/", views.RegisterView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("sso-login/", views.SSOLoginView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    # 普通用户管理用户信息、密码修改、注销
    path("profile/", views.UserProfileView.as_view()),
    path("profile/deactivate/", views.UserDeactivationView.as_view()),
    path("profile/reset-password/", views.UserResetPasswordView.as_view()),
    # 管理员管理用户信息
    path("users/", views.AdminUserListView.as_view()),
    path("users/actions/batch-delete/", views.AdminUserListView.as_view()),
    path("users/<int:user_id>/", views.AdminUserDetailView.as_view()),
    path("users/<int:user_id>/reset-password/", views.AdminResetUserPasswordView.as_view()),
    path("users/<int:user_id>/enable/", views.AdminUserEnableView.as_view()),
    path("users/<int:user_id>/disable/", views.AdminUserDisableView.as_view()),
    # 管理员管理角色信息
    path("roles/", views.AdminRoleListView.as_view()),
    path("roles/actions/batch-delete/", views.AdminRoleListView.as_view()),
    path("roles/<int:role_id>/", views.AdminRoleDetailView.as_view()),
    path("roles/<int:role_id>/enable/", views.AdminRoleEnableView.as_view()),
    path("roles/<int:role_id>/disable/", views.AdminRoleDisableView.as_view()),
    path("roles/permissions/tree/", views.AdminRolePermissionTreeView.as_view()),
    # 管理员管理公司信息
    path("companies/", views.AdminCompanyListView.as_view()),
    path("companies/<int:company_id>/", views.AdminCompanyDetailView.as_view()),
    path("companies/actions/batch-delete/", views.AdminCompanyListView.as_view()),
    path("companies/<int:company_id>/enable/", views.AdminCompanyEnableView.as_view()),
    path("companies/<int:company_id>/disable/", views.AdminCompanyDisableView.as_view()),
    path("companies/<int:company_id>/assume/", views.AdminAssumeCompanyView.as_view()),
    path("companies/<int:company_id>/release/", views.AdminReleaseCompanyView.as_view()),
    # 管理员管理组织信息
    path("organizations/", views.AdminOrganizationListView.as_view()),
    path("organizations/<int:organization_id>/", views.AdminOrganizationDetailView.as_view()),
    path("organizations/actions/batch-update/", views.AdminOrganizationListView.as_view()),
    path("organizations/actions/batch-delete/", views.AdminOrganizationListView.as_view()),
]