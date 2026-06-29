from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from extensions.views import BaseView
from identity.schemas import LoginSchema, RegisterSchema
from identity.services import user_service
from identity.decorators import require_login


class RegisterView(BaseView):
    """用户注册"""
    
    @method_decorator(validate_parameters(RegisterSchema))
    def post(self, request, cleaned_data):
        return user_service.register_user(**cleaned_data)


class LoginView(BaseView):
    """用户登录"""
    
    @method_decorator(validate_parameters(LoginSchema))
    def post(self, request, cleaned_data):
        return user_service.login(request, **cleaned_data)


class LogoutView(BaseView):
    """用户登出"""
    
    @method_decorator(require_login)    
    @method_decorator(require_login)
    def post(self, request):
        user_service.logout(request.user, request.token)
    