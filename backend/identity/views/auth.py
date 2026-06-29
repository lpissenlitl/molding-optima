from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from extensions.views import BaseView
from identity.schemas import LoginSchema, RegisterSchema
from identity.services import user_service
from identity.decorators import require_login


class RegisterView(BaseView):
    
    @method_decorator(validate_parameters(RegisterSchema))
    def post(self, request, cleaned_data):
        """用户注册"""
        return user_service.register_user(**cleaned_data)


class LoginView(BaseView):
    
    @method_decorator(validate_parameters(LoginSchema))
    def post(self, request, cleaned_data):
        """用户登录"""
        return user_service.login(request, **cleaned_data)


class SSOLoginView(BaseView):
    
    @method_decorator(require_login)
    def post(self, request):
        """SSO登录"""
        return user_service.sso_login(request)


class LogoutView(BaseView):
    
    @method_decorator(require_login)
    def post(self, request):
        """用户登出"""
        return user_service.logout(request.user, request.token)
    