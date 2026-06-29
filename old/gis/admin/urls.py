from django.urls import path
from gis.admin import views

urlpatterns = [
    # 注册，登录，登出
    path("register/", views.RegisterView.as_view()),
    path("login/", views.AuthLoginView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("user_info/", views.UserInfoView.as_view()),
    path("reset_password/", views.UserUpdatePasswordView.as_view()),
    path("reset_password/<int:user_id>/", views.UserResetPasswordView.as_view()),

    # 用户管理
    path("users/", views.UserListView.as_view()),
    path("users/<int:user_id>/", views.UserDetailView.as_view()),
    path("users/<int:user_id>/enable/", views.UserEnableView.as_view()),
    path("users/<int:user_id>/disable/", views.UserDisableView.as_view()),
    path("users/<int:user_id>/npauth/", views.UserNoPasswordAuthView.as_view()),

    # 组织管理员用户
    path("managers/", views.CompanyManagerView.as_view()),

    # 公司
    path("company/", views.CompanyListView.as_view()),
    path("company/<int:company_id>/", views.CompanyDetailView.as_view()),

    # 组织
    path("group/", views.GroupListView.as_view()),
    path("group/<int:group_id>/", views.GroupDetailView.as_view()),

    # 部门
    path("department/", views.DepartmentListView.as_view()),
    path("department/<int:department_id>/", views.DepartmentDetailView.as_view()),

    # 角色管理
    path("roles/", views.RoleListView.as_view()),
    path("roles/<int:role_id>/", views.RoleDetailView.as_view()),

    # 权限管理
    path("permissions/", views.PermissionListView.as_view()),

    # 操作记录
    path("record/", views.RecordListView.as_view()),

    # 访问MES的登录api,验证token_em的有效性
    path("login_em/", views.AuthLoginEmView.as_view()),
    path("login_uuid/", views.AuthLoginUuidView.as_view()),
]
