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
    
    @method_decorator(require_login)
    def get(self, request):
        """获取用户信息接口"""
        return user_service.get_profile(request.user)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UserSchema))
    def put(self, request, cleaned_data):
        """更新用户信息接口"""
        return user_service.update_profile(request.user, **cleaned_data)


class UserDeactivationView(BaseView):
    
    @method_decorator(require_login)
    def put(self, request):
        """用户注销接口"""
        return user_service.deactivate(request.user)


class UserResetPasswordView(BaseView):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(UpdateUserPasswordSchema))
    def put(self, request, cleaned_data):
        """用户重置密码接口"""
        return user_service.reset_password_after_verify_old_password(request.user, **cleaned_data)

