from extensions.views import BaseView
from extensions.decorators import validate_parameters
from django.utils.decorators import method_decorator
from identity.decorators import require_login
from identity.services import user_service
from identity.schemas import (
    UserSchema,
    UpdateUserPasswordSchema
)


class UserProfileView(BaseView):
    """用户信息接口"""
    
    @method_decorator(require_login)
    def get(self, request):
        return user_service.get_user_info(request.user, request.user.id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UserSchema))
    def put(self, request, cleaned_data):
        user_service.update_user_info(request.user, request.user.id, **cleaned_data)


class UserResetPasswordView(BaseView):
    """用户重置密码接口"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UpdateUserPasswordSchema))
    def post(self, request, cleaned_data):
        user_service.reset_password_after_verify_old_password(request.user, **cleaned_data)


class UserDeactivationView(BaseView):
    """用户注销接口"""
    
    @method_decorator(require_login)
    def post(self, request):
        user_service.deactivate_user(request.user, request.user.id)