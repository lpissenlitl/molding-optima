from django.utils.decorators import method_decorator
import logging

from gis.admin.decorators import require_login, check_permission
from gis.admin.dto import UserListCriteria, RoleListCriteria, RecordListCriteria
from gis.admin.forms import (
    AddCompanySchema,
    UpdateCompanySchema,
    CompanyListSchema,
    DelMultipleCompanySchema,
    AddDepartmentSchema,
    UpdateDepartmentSchema,
    DepartmentListSchema,
    DelMultipleDepartmentSchema,
    AddRoleSchema,
    UpdateRoleSchema,
    RoleListSchema,
    DelMultipleRoleSchema,
    AddUserSchema,
    UpdateUserSchema,
    GetUserSchema,
    DelMultipleUserSchema,
    RegisterSchema,
    AuthLoginSchema,
    UpdateUserPasswordSchema,
    ResetUserPasswordSchema,
    RecordListSchema,
    AuthLoginByTokenSchema,
    UserGroupListSchema,
    AddGroupSchema,
    EditGroupSchema,
    GroupListSchema,
    AuthLoginByTokenUuidSchema
)
from gis.admin.helper import wrapper_record_info
from gis.admin.services import admin_service, company_service, department_service, group_service
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse
from gis.common.exceptions import BizException, ERROR_ACCESS_LIMIT

_LOGGER = logging.getLogger(__name__)


###################################################################
# 企业管理
###################################################################
class CompanyListView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("company_get"))
    @method_decorator(validate_parameters(CompanyListSchema))
    def get(self, request, cleaned_data):
        total, companies = company_service.list_companies(**cleaned_data)
        return PaginationResponse(total, companies)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_add"))
    @method_decorator(validate_parameters(AddCompanySchema))
    def post(self, request, cleaned_data):
        return company_service.add_company(cleaned_data)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_update"))
    @method_decorator(validate_parameters(DelMultipleCompanySchema))
    def delete(self, request, cleaned_data):
        company_service.del_multiple_company(**cleaned_data)


class CompanyDetailView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("department_get"))
    def get(self, request, company_id):
        return company_service.get_company(company_id)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_update"))
    @method_decorator(validate_parameters(UpdateCompanySchema))
    def put(self, request, company_id, cleaned_data):
        company_service.update_company(company_id, cleaned_data)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_delete"))
    def delete(self, request, company_id):
        return company_service.delete_company(company_id)


###################################################################
# 部门管理
###################################################################
class DepartmentListView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("department_get"))
    @method_decorator(validate_parameters(DepartmentListSchema))
    def get(self, request, cleaned_data):
        total, departments = department_service.list_departments(**cleaned_data)
        return PaginationResponse(total, departments)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_add"))
    @method_decorator(validate_parameters(AddDepartmentSchema))
    def post(self, request, cleaned_data):
        return department_service.add_department(cleaned_data)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_update"))
    @method_decorator(validate_parameters(DelMultipleDepartmentSchema))
    def delete(self, request, cleaned_data):
        department_service.del_multiple_department(**cleaned_data)


class DepartmentDetailView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("department_get"))
    def get(self, request, department_id):
        return department_service.get_department(department_id)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_update"))
    @method_decorator(validate_parameters(UpdateDepartmentSchema))
    def put(self, request, department_id, cleaned_data):
        department_service.update_department(department_id, cleaned_data)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_delete"))
    def delete(self, request, department_id):
        return department_service.delete_department(department_id)


###################################################################
# 组织管理
###################################################################
class GroupListView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(GroupListSchema))
    def get(self, request, cleaned_data):
        total, groups = group_service.get_list_of_group(**cleaned_data)
        return PaginationResponse(total, groups)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(AddGroupSchema))
    def post(self, request, cleaned_data):
        return group_service.add_company_group(cleaned_data)


class GroupDetailView(BaseView):
    @method_decorator(require_login)
    def get(self, request, group_id):
        return group_service.get_company_group(group_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(EditGroupSchema))
    def put(self, request, group_id, cleaned_data):
        group_service.udpate_company_group(group_id, cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, group_id):
        return group_service.delete_company_group(group_id)


###################################################################
# 权限管理
###################################################################
class PermissionListView(BaseView):
    @method_decorator(require_login)
    def get(self, request):
        user = request.user
        tree = admin_service.get_total_permission_tree(user["is_super"], user["company_id"])
        return dict(permissions=tree)


###################################################################
# 角色管理
###################################################################
class RoleListView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_role_get"))
    @method_decorator(validate_parameters(RoleListSchema))
    def get(self, request, cleaned_data: RoleListCriteria):
        total, roles = admin_service.list_roles(cleaned_data)
        return PaginationResponse(total, roles)

    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_role_add"))
    @method_decorator(validate_parameters(AddRoleSchema))
    def post(self, request, cleaned_data):
        return admin_service.add_role(**cleaned_data)

    @method_decorator(require_login)
    # @method_decorator(check_permission("department_update"))
    @method_decorator(validate_parameters(DelMultipleRoleSchema))
    def delete(self, request, cleaned_data):
        admin_service.del_multiple_role(**cleaned_data)


class RoleDetailView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_role_get"))
    def get(self, request, role_id):
        return admin_service.get_role(role_id=role_id, with_permissions=True)

    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_role_update"))
    @method_decorator(validate_parameters(UpdateRoleSchema))
    def put(self, request, role_id, cleaned_data):
        admin_service.update_role(role_id, **cleaned_data)
        return dict(id=role_id)

    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_role_delete"))
    def delete(self, request, role_id):
        admin_service.delete_role(role_id)
        return dict(id=role_id)


###################################################################
# 用户管理
###################################################################
class UserListView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_get"))
    @method_decorator(validate_parameters(GetUserSchema))
    def get(self, request, cleaned_data: UserListCriteria):
        total, users = admin_service.list_users(cleaned_data)
        return PaginationResponse(total, users)

    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_add"))
    @method_decorator(validate_parameters(AddUserSchema))
    def post(self, request, cleaned_data):
        return admin_service.add_user(**cleaned_data)
    
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_add"))
    @method_decorator(validate_parameters(DelMultipleUserSchema))
    def delete(self, request, cleaned_data):
        return admin_service.delete_multiple_user(**cleaned_data)


class UserDetailView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_get"))
    def get(self, request, user_id):
        return admin_service.get_user_by_id(user_id, check_enable=False, with_roles=True, with_groups=True)

    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_update"))
    @method_decorator(validate_parameters(UpdateUserSchema))
    def put(self, request, user_id, cleaned_data):
        if cleaned_data.get("is_super") == 1:
            # 只有超级管理员才能编辑超级管理员权限
            if not (request.user and request.user.get("is_super")):
                raise BizException(ERROR_ACCESS_LIMIT, "需要超级管理员权限")
        admin_service.update_user(user_id, **cleaned_data)
        return dict(id=user_id)

    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_delete"))
    def delete(self, request, user_id):
        admin_service.delete_user(user_id)
        return dict(id=user_id)


class CompanyManagerView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_add"))
    @method_decorator(validate_parameters(AddUserSchema))
    def post(self, request, cleaned_data):
        return admin_service.add_company_manager(cleaned_data)


class UserInfoView(BaseView):
    @method_decorator(require_login)
    def get(self, request):
        return admin_service.get_user_by_id(request.user_id, with_roles=True, with_groups=True)


class UserEnableView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_enable"))
    def put(self, request, user_id):
        admin_service.enable_user(user_id)
        return dict(id=user_id)


class UserDisableView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_disable"))
    def put(self, request, user_id):
        admin_service.disable_user(user_id)
        return dict(id=user_id)


class UserNoPasswordAuthView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UpdateUserSchema))
    def put(self, request, user_id, cleaned_data):
        admin_service.set_app_id(user_id, cleaned_data.get("app_id"))
        return dict(id=user_id)


class RegisterView(BaseView):
    @method_decorator(validate_parameters(RegisterSchema))
    def post(self, request, cleaned_data):
        return admin_service.add_user(**cleaned_data)


class AuthLoginView(BaseView):
    # 通过MES 带token免登录进入
    @method_decorator(validate_parameters(AuthLoginByTokenSchema))
    def get(self, request, cleaned_data):
        user = admin_service.login_by_token(**cleaned_data)
        return user


    # 通过授权中心登录
    @method_decorator(validate_parameters(AuthLoginSchema))
    def post(self, request, cleaned_data):
        return admin_service.login(**cleaned_data)


class LogoutView(BaseView):
    @method_decorator(require_login)
    def post(self, request):
        user = request.user
        admin_service.logout(user["id"], request.token)


class UserUpdatePasswordView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UpdateUserPasswordSchema))
    def put(self, request, cleaned_data):
        admin_service.reset_password_after_verify_old_success(request.user_id, **cleaned_data)
        return dict(id=request.user_id)


class UserResetPasswordView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_reset_user_password"))
    @method_decorator(validate_parameters(ResetUserPasswordSchema))
    def put(self, request, user_id, cleaned_data):
        new_password = admin_service.reset_password(user_id, cleaned_data.get("new_password"))
        return dict(password=new_password)


class RecordListView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("record_get"))
    @method_decorator(validate_parameters(RecordListSchema))
    def get(self, request, cleaned_data: RecordListCriteria):
        # 导出操作记录
        if cleaned_data.export:
            return self.export(request, cleaned_data)
        total, records = admin_service.get_record_list(cleaned_data)
        records = wrapper_record_info(records)
        return PaginationResponse(total, records)

    # @method_decorator(check_permission("record_export"))
    def export(self, request, cleaned_data: RecordListCriteria):
        cleaned_data.export = None


class AuthLoginEmView(BaseView):
    # 调用MES的登录api,验证token_em是否有效
    @method_decorator(validate_parameters(AuthLoginByTokenSchema))
    def get(self, request, cleaned_data):
        result = admin_service.login_by_token_em(**cleaned_data)
        return result

class AuthLoginUuidView(BaseView):
    # 调用MES的登录api,验证uuid是否有效
    @method_decorator(validate_parameters(AuthLoginByTokenUuidSchema))
    def get(self, request, cleaned_data):
        result = admin_service.login_by_token_uuid(**cleaned_data)
        return result
