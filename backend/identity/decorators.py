from functools import wraps
from django.http import HttpRequest
from extensions.exceptions import BizException
from identity.exceptions import ERROR_USER_TOKEN_NOT_EXISTS, ERROR_USER_PERMISSION_DENIED
from identity.services.user_service import get_user_by_token


def _authenticate_request(request: HttpRequest):
    """从 request 中解析 token 并设置 request.user，返回 User 对象"""
    if not isinstance(request, HttpRequest):
        raise Exception(
            "the first parameter must be request, "
            "you must use @method_decorator(require_login/require_admin) if you use the class-based View."
        )
    
    token = request.META.get("HTTP_X_AUTH_TOKEN")
    if not token:
        token = request.GET.get("token")
    if not token:
        raise BizException(ERROR_USER_TOKEN_NOT_EXISTS, "Authorization token is missing.")
    
    user = get_user_by_token(request, token)
    if not user:
        raise BizException(ERROR_USER_TOKEN_NOT_EXISTS, "Authorization token is invalid.")
    
    request.user = user
    request.user_id = user.id
    request.token = token
    return user


def require_login(func):
    """登录校验装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        _authenticate_request(args[0])
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """管理员权限校验装饰器（包含登录校验）

    允许以下用户通过：
    1. is_superuser=True（超级管理员，可接管任意公司）
    2. is_tenant_admin=True（租户管理员，由超级管理员接管后设置）
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = _authenticate_request(args[0])
        if not (user.is_superuser or user.is_tenant_admin):
            raise BizException(ERROR_USER_PERMISSION_DENIED, "需要管理员权限")
        return func(*args, **kwargs)
    return wrapper


def require_superuser(func):
    """超级管理员权限校验装饰器（包含登录校验）

    只允许 is_superuser=True 通过：
    - 超级管理员未接管时（company_id=None）：可看平台级内部数据（如系统演示公司的专家规则）
    - 超级管理员接管某公司后（company_id=<被接管公司>）：仍可看（全局视角）
    - 租户管理员 / 普通用户：拒绝（专家规则属于平台级内部规则，不向租户展示）

    使用场景：
    - 专家规则（ExpertRule）：工艺参数初始化系数，是平台级内部规则
    - 系统演示数据管理：只允许平台超管操作
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = _authenticate_request(args[0])
        if not user.is_superuser:
            raise BizException(ERROR_USER_PERMISSION_DENIED, "需要超级管理员权限")
        return func(*args, **kwargs)
    return wrapper