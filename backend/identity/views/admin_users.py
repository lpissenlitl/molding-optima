from django.utils.decorators import method_decorator
from extensions.views import BaseView, PaginationResponse
from extensions.decorators import validate_parameters
from extensions.schemas import BatchIdsSchema
from identity.services import user_service
from identity.decorators import require_login, require_admin
from identity.schemas import (
    UserSchema,
    UserListSchema,
    ResetUserPasswordSchema
)


class AdminUserDetailView(BaseView):
    
    @method_decorator(require_admin)
    def get(self, request, user_id):
        """管理员获取用户详情"""
        return user_service.get_user_info(user_id=user_id)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(UserSchema))
    def put(self, request, user_id, cleaned_data):
        """管理员更新用户信息"""
        return user_service.update_user_info(
            operator=request.user,
            user_id=user_id,
            **cleaned_data
        )
    
    @method_decorator(require_admin)
    def delete(self, request, user_id):
        """管理员删除用户"""
        return user_service.delete_user(
            operator=request.user,
            user_id=user_id
        )


class AdminUserListView(BaseView):
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(UserListSchema))
    def get(self, request, cleaned_data):
        """管理员获取用户列表"""
        total, items = user_service.get_user_list(
            company_id=request.user.company_id,
            **cleaned_data
        )
        return PaginationResponse(total, items)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(UserSchema))
    def post(self, request, cleaned_data):
        """管理员创建用户"""
        return user_service.create_user(
            operator=request.user,
            **cleaned_data
        )
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(BatchIdsSchema))   
    def delete(self, request, cleaned_data):
        """管理员批量删除用户"""
        return user_service.batch_delete_user(
            operator=request.user,
            **cleaned_data
        )


class AdminUserEnableView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, user_id):
        """管理员启用用户"""
        return user_service.enable_user(
            operator=request.user,
            user_id=user_id
        )


class AdminUserDisableView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, user_id):
        """管理员禁用用户"""
        return user_service.disable_user(
            operator=request.user,
            user_id=user_id
        )


class AdminResetUserPasswordView(BaseView):
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(ResetUserPasswordSchema))
    def put(self, request, user_id, cleaned_data):
        """管理员重置用户密码"""
        return user_service.reset_password(
            operator=request.user,
            user_id=user_id,
            **cleaned_data
        )
