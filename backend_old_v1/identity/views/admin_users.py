from extensions.views import BaseView, PaginationResponse
from extensions.decorators import validate_parameters
from extensions.schemas import (
    BatchIdsSchema
)
from django.utils.decorators import method_decorator
from identity.services import user_service
from identity.decorators import require_login
from identity.schemas import (
    UserSchema,
    UserListSchema,
    ResetUserPasswordSchema
)


class AdminUserDetailView(BaseView):
    """管理员操作用户"""
    
    @method_decorator(require_login)
    def get(self, request, user_id):
        return user_service.get_user_info(request.user, user_id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UserSchema))
    def put(self, request, user_id, cleaned_data):
        user_service.update_user_info(request.user, user_id, **cleaned_data)
    
    @method_decorator(require_login)
    def delete(self, request, user_id):
        user_service.delete_user(request.user, user_id)


class AdminUserListView(BaseView):
    """管理员获取用户列表"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UserListSchema))
    def get(self, request, cleaned_data):
        print(cleaned_data)
        total, items = user_service.get_user_list(request.user, **cleaned_data)
        return PaginationResponse(total, items)
    """管理员创建用户"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UserSchema))
    def post(self, request, cleaned_data):
        user_service.create_user(request.user, **cleaned_data)
    """管理员批量删除用户"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchIdsSchema))   
    def delete(self, request, cleaned_data):
        user_service.batch_delete_user(request.user, **cleaned_data)



class AdminUserEnableView(BaseView):
    """管理员启用用户"""
    
    @method_decorator(require_login)
    def put(self, request, user_id):
        user_service.enable_user(request.user, user_id)


class AdminResetUserPasswordView(BaseView):
    """管理员重置用户密码"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ResetUserPasswordSchema))
    def put(self, request, user_id, cleaned_data):
        user_service.reset_password(request.user, user_id, **cleaned_data)


class AdminUserDisableView(BaseView):
    """管理员禁用用户"""
    
    @method_decorator(require_login)
    def put(self, request, user_id):
        user_service.disable_user(request.user, user_id)
