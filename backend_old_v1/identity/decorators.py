from functools import wraps
from django.http import HttpRequest
from extensions.exceptions import BizException
from identity.exceptions import ERROR_USER_TOKEN_NOT_EXISTS
from identity.services.user_service import get_user_by_token

def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        request = args[0]
        if not isinstance(request, HttpRequest):
            raise Exception(
                "the first parameter must be request, "
                "you must use @method_decorator(require_login) if you use the class-based View."
            )
        
        token = request.META.get("HTTP_X_AUTH_TOKEN")

        if not token:
            token = request.GET.get("token")

        if not token:
            raise BizException(ERROR_USER_TOKEN_NOT_EXISTS, "Authorization token is missing.")
        
        user = get_user_by_token(token)
        if not user:
            raise BizException(ERROR_USER_TOKEN_NOT_EXISTS, "Authorization token is invalid.")
        
        request.user = user
        request.user_id = user.id if user else None
        request.token = token
        
        return func(*args, **kwargs)

    return wrapper
