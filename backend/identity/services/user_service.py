from django.http import HttpRequest
from identity.models import User, Role, Token, RedirectToken, Company, Organization
from datetime import timedelta, datetime
from extensions.encrypt.pwdutils import check_pwd_strength, hash_pwd, check_pwd
from extensions.exceptions import BizException
from utils.sercurity import generate_random_password
from utils.db import parse_ordering, paginate_queryset, build_filters
from utils.validation import validate_required, validate_pk, validate_id_list, validate_code
from identity.exceptions import (
    ERROR_USER_TOKEN_NOT_EXISTS,
    ERROR_USER_USERNAME_EMPTY,
    ERROR_USER_USERNAME_EXISTS,
    ERROR_USER_USERNAME_NOT_EXISTS,
    ERROR_USER_PASSWORD_EMPTY,
    ERROR_USER_PASSWORD_STRENGTH,
    ERROR_USER_NOT_FOUND,
    ERROR_USER_PASSWORD_WRONG,
    ERROR_USER_AUTH_FAILED,
    ERROR_USER_NOT_ACTIVE,
    ERROR_USER_PERMISSION_DENIED,
    ERROR_COMPANY_NOT_ACCESSIBLE,
    ERROR_ORGANIZATION_NOT_FOUND,
    ERROR_ROLE_NOT_FOUND
)
from extensions.exceptions import (
    ERROR_SYSTEM_EXCEPTION,
    ERROR_ILLEGAL_ARGUMENT
)
from django.db import transaction
import logging
import hashlib
from identity.services.role_service import (
    get_system_guest_role,
    get_company_default_role
)


DEFAULT_TOKEN_EXPIRY_HOURS = 6  # 默认token过期时间


def authenticate_user(username: str, password: str):
    """认证用户登录"""
    try:
        user = User.objects.select_related(
            "company", "organization"
        ).prefetch_related(
            "roles", "extra_accessible_orgs"
        ).get(username=username)
    except User.DoesNotExist:
        raise BizException(ERROR_USER_NOT_FOUND)
    except User.MultipleObjectsReturned:
        logging.error(f"数据异常：用户名 '{username}' 对应多个用户记录", exc_info=True)
        raise BizException(ERROR_SYSTEM_EXCEPTION)
    
    # 普通用户判断权限
    if not user.is_accessible():
        raise BizException(ERROR_USER_PERMISSION_DENIED)
    
    # 单点登录会传内部 hashed_password
    if password.startswith("$") and password == user.password:
        return user
        
    # 正常登录
    if not check_pwd(password, user.password):
        raise BizException(ERROR_USER_PASSWORD_WRONG)
    
    return user


def create_token(
    request: HttpRequest, 
    user: User,
    expire_hours: int = DEFAULT_TOKEN_EXPIRY_HOURS,
    allow_multi_login: bool = True
):
    """创建Token"""
    # 限制用户多端登录
    if not allow_multi_login:
        Token.objects.filter(
            user=user,
            is_revoked=False,
            expires_at__gt=datetime.now()
        ).update(
            is_revoked=True,
            revoked_at=datetime.now()
        )
    
    raw_token, hash_token = Token.create(user, request, expire_hours)
    return raw_token


def get_user_by_token(raw_token: str):
    """根据 Token 获取用户信息"""

    # 验证 token 格式
    if not raw_token or not isinstance(raw_token, str):
        logging.warning(f"Token 格式错误：{raw_token}")
        return None

    raw_token = raw_token.strip()
    if len(raw_token) > 255 or len(raw_token) < 32:
        logging.warning(f"Token 值长度异常：{raw_token}")
        return None
        
    try:
        hash_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    except Exception:
        logging.warning(f"Token 值格式异常：{raw_token}")
        return None
    
    # 验证 login token
    token = Token.objects.filter(
        token=hash_token,
        expires_at__gt=datetime.now(),
        is_revoked=False,
        user__is_active=True,
        user__is_deleted=False
    ).select_related(
        "user",
        "user__company",
        "user__organization"
    ).first()
    
    if token:
        token.flush_token()
        return token.user
    
    # 验证 redirect token
    token = RedirectToken.objects.filter(
        token=hash_token,
        expires_at__gt=datetime.now(),
        is_used=False,
        user__is_active=True,
        user__is_deleted=False
    ).select_related(
        "user",
        "user__company",
        "user__organization"
    ).first()
    
    if token:
        return token.user
    
    return None


def register_user(
    company_id: int = None,
    organization_id: int = None,
    username: str = None,
    password: str = None,
    engineer_name: str = None,
    email: str = None,
    phone: str = None,
    is_active: bool = True,
    is_staff: bool = False,
    is_tenant_admin: bool = False,
    is_superuser: bool = False,
    roles: list = None,
    extra_accessible_orgs: list = None,
    expires_at: datetime = None
):
    """注册用户"""
    if not username:
        raise BizException(ERROR_USER_USERNAME_EMPTY)
    if not password:
        raise BizException(ERROR_USER_PASSWORD_EMPTY)    
    
    pwd_valid, pwd_msg = check_pwd_strength(password)
    if not pwd_valid:
        raise BizException(ERROR_USER_PASSWORD_STRENGTH, pwd_msg)
    
    if User.objects.filter(username=username).exists():
        raise BizException(ERROR_USER_USERNAME_EXISTS)
    
    with transaction.atomic():
        user = User.objects.create(
            company_id=company_id,
            organization_id=organization_id,
            username=username,
            password=hash_pwd(password),
            engineer_name=engineer_name,
            email=email,
            phone=phone,
            is_active=is_active,
            is_staff=is_staff,
            is_tenant_admin=is_tenant_admin,
            is_superuser=is_superuser,
            expires_at=expires_at,
            feishu_id=username
        )
        
        if company_id is None:
            # 场景1：游客注册 -> 分配默认角色
            default_role = get_system_guest_role()
            user.roles.add(default_role)
        else:
            # 场景2：组织内注册 -> 使用指定角色 或 分配默认角色
            if roles:
                # 由邀请方指定角色
                _bind_user_to_roles(user, roles)
            else:
                # 无指定角色，分配默认角色
                default_role = get_company_default_role(company_id)
                user.roles.add(default_role)

        if extra_accessible_orgs:
            _bind_user_to_organizations(user, extra_accessible_orgs)     
            
        return user.to_dict(exclude=["password", "is_deleted"])


def login(request: HttpRequest, username: str, password: str, **kwargs):
    """用户登录：认证 + 权限校验 + 用户信息组装"""
    user = authenticate_user(username, password)
    
    # 构建脱敏用户信息
    user_dict = user.construct_user_info()
    
    # 创建Token
    token = create_token(request, user)
    user_dict.update({"token": token})
    
    # --- 记录登录信息 ---
    user.record_login()
    
    return user_dict


def sso_login(request: HttpRequest):
    """SSO登录"""
    if not hasattr(request, "user") or not request.user:
        raise BizException(ERROR_USER_NOT_FOUND)
    user: User = request.user
    return login(request, user.username, user.password)


def logout(user: User, token: str):
    """用户登出"""
    Token.objects.filter(user=user, token=token).update(is_revoked=True, revoked_at=datetime.now())


def _get_user_by_id(user_id: int) -> User:
    """根据用户 ID 获取用户"""
    user_id = validate_pk(user_id, "user_id")

    # 预加载用户企业、组织、角色、访问信息
    user = User.objects.filter(
        id=user_id
    ).select_related(
        "company", "organization"
    ).prefetch_related(
        "roles", "extra_accessible_orgs"
    ).first()
    
    if not user:
        raise BizException(ERROR_USER_NOT_FOUND)

    return user


def get_user_info(user_id: int) -> dict:
    """
    根据用户 ID 获取用户信息（排除 password 字段），包含外键和多对多关系数据
    """
    target = _get_user_by_id(user_id)

    user_dict = { 
        **target.to_dict(
            exclude=["password", "is_deleted"], 
            include_m2m=True, include_rvs=True
        ),
        "permissions": target.get_permissions(),
        "company_name": target.company.name if target.company else None,
        "company_code": target.company.code if target.company else None,
    }
    return user_dict


@transaction.atomic
def update_user_info(operator: User, user_id: int, **kwargs):
    """更新用户信息（支持部分字段更新）"""
    target = _get_user_by_id(user_id)
    kwargs.pop("password") if "password" in kwargs else None
    target.update_info(**kwargs)
    
    if "roles" in kwargs:
        ori_roles = list(target.roles.all().values_list("id", flat=True))
        if sorted(ori_roles) != sorted(kwargs.get("roles", [])):
            _bind_user_to_roles(target, kwargs["roles"])
    
    if "extra_accessible_orgs" in kwargs:
        ori_acc_orgs = list(target.extra_accessible_orgs.all().values_list("id", flat=True))
        if sorted(ori_acc_orgs) != sorted(kwargs.get("extra_accessible_orgs", [])):
            _bind_user_to_organizations(target, kwargs["extra_accessible_orgs"])


def delete_user(operator: User, user_id: int):
    """管理员删除用户（软删除）"""
    target = _get_user_by_id(user_id)
    target.soft_delete()


def _bind_user_to_roles(user: User, role_ids: list):
    """绑定用户到角色"""
    roles = Role.objects.filter(id__in=role_ids)
    if len(roles) != len(role_ids):
        missing = set(role_ids) - set(roles.values_list('id', flat=True))
        raise BizException(ERROR_ROLE_NOT_FOUND, list(missing))
    user.roles.set(roles)  # 直接设置，自动 clear + add


def _bind_user_to_organizations(user: User, org_ids: list):
    """绑定用户到数据访问"""
    organizations = Organization.objects.filter(id__in=org_ids)
    if len(organizations) != len(org_ids):
        missing = set(org_ids) - set(organizations.values_list('id', flat=True))
        raise BizException(ERROR_ORGANIZATION_NOT_FOUND, list(missing))
    user.extra_accessible_orgs.set(organizations)  # 直接设置，自动 clear + add


def create_user(operator: User, **kwargs):
    """创建用户（通常由管理员调用）"""
    organization = Organization.objects.filter(id=kwargs["organization_id"]).first()
    company_id = organization.company_id if organization else operator.company_id

    return register_user(company_id=company_id, **kwargs)


def get_user_list(
    company_id: int,
    organization_id: int = None,
    username: str = None,
    engineer_name: str = None,
    is_active: bool = None,
    is_staff: bool = None,
    is_tenant_admin: bool = None,
    is_superuser: bool = None,
    roles__name: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None
):
    """获取用户列表"""
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "organization_id": {"input": organization_id, "column": "organization_id", "lookup": "exact"},
        "username": {"input": username, "column": "username", "lookup": "icontains"},
        "engineer_name": {"input": engineer_name, "column": "engineer_name", "lookup": "icontains"},
        "is_active": {"input": is_active, "column": "is_active", "lookup": "exact"},
        "is_staff": {"input": is_staff, "column": "is_staff", "lookup": "exact"},
        "is_tenant_admin": {"input": is_tenant_admin, "column": "is_tenant_admin", "lookup": "exact"},
        "is_superuser": {"input": is_superuser, "column": "is_superuser", "lookup": "exact"},
        "roles__name": {"input": roles__name, "column": "roles__name", "lookup": "icontains"},
    }
    filters = build_filters(filter_map)
    qs = User.objects.filter(**filters).prefetch_related('roles', 'extra_accessible_orgs')
    
    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict(exclude=["password"], include_m2m=True, include_rvs=True) for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, results


def batch_delete_user(user: User, ids: list):
    """批量删除用户（软删除）"""
    ids = validate_id_list(ids, "用户 ID 列表")
    return User.objects.filter(
        id__in=ids, 
        is_deleted=False
    ).update(
        is_deleted=True, 
        deleted_at=datetime.now()
    )


def enable_user(operator: User, user_id: int):
    """管理员启用用户"""
    target = _get_user_by_id(user_id)
    update_user_info(operator, user_id, is_active=True)


def disable_user(operator: User, user_id: int):
    """管理员禁用用户"""
    target = _get_user_by_id(user_id)
    update_user_info(operator, user_id, is_active=False)


def _set_password(user: User, password: str):
    """设置用户密码"""
    pwd_valid, pwd_msg = check_pwd_strength(password)
    if not pwd_valid:
        raise BizException(ERROR_USER_PASSWORD_STRENGTH, pwd_msg)
    user.password = hash_pwd(password)
    user.save(update_fields=["password", "updated_at"])
    # 注销所有 Token
    Token.objects.filter(user=user).update(is_revoked=True, revoked_at=datetime.now())
    

def reset_password(operator: User, user_id: int, password: str):
    """管理员重置用户密码"""
    obj_user = _get_user_by_id(user_id)
    password = password or generate_random_password()
    _set_password(obj_user, password)
    return password


def get_profile(user: User) -> dict:
    """获取当前用户信息"""
    return get_user_info(user.id)


def update_profile(user: User, **kwargs):
    """更新当前用户信息（支持部分字段更新）"""
    user = _get_user_by_id(user.id)
    UPDATABLE_FIELDS = [
        "engineer_name", "email", "phone"
    ]
    user.update_info(**{k: v for k, v in kwargs.items() if k in UPDATABLE_FIELDS})


def deactivate(user: User):
    """用户注销"""
    user.deactivate()


def reset_password_after_verify_old_password(
    user: User, 
    old_password: str, 
    new_password: str
):
    """用户更新密码，需先验证旧密码"""
    if not check_pwd(old_password, user.password):
        raise BizException(ERROR_USER_PASSWORD_WRONG, "旧密码错误")
    _set_password(user, new_password)
    return None # 不返回明文密码