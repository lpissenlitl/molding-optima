from identity.models import Role, User, Permission
from extensions.exceptions import BizException
from utils.validation import validate_required, validate_pk, validate_code
from utils.validation import validate_id_list
from identity.exceptions import(
    ERROR_ROLE_NOT_FOUND,
    ERROR_ROLE_CODE_EXISTS,
    ERROR_USER_PERMISSION_DENIED,
    ERROR_COMPANY_NOT_FOUND
)
from utils.db import build_filters, parse_ordering, paginate_queryset
from identity.permissions import RolePermission
from datetime import datetime
from django.db import transaction
from django.db.models import Max


ALL_PERMISSION_CACHE = None
ADMIN_PERMISSION_CODES = [
    # 权限管理根菜单
    "permission_manage",

    # 部门管理
    "department_manage",
    "review_department",
    "add_department",
    "delete_department",
    "update_department",

    # 角色管理
    "role_manage",
    "review_role",
    "add_role",
    "delete_role",
    "update_role",

    # 用户管理
    "user_manage",
    "review_user",
    "add_user",
    "delete_user",
    "update_user",
]

def get_system_guest_role():
    """
    获取系统级访客角色（如 'guest'）
    用于游客注册、平台公共权限等
    """
    try:
        return Role.objects.get(company_id__isnull=True, code="guest")
    except Role.DoesNotExist:
        raise RuntimeError(
            "系统未初始化：缺少系统级默认角色 'guest' 。"
            "请联系管理员初始化系统。"
        )
    except Role.MultipleObjectsReturned:
        raise RuntimeError(
            "数据异常：存在多个系统级默认角色 'guest' 。"
            "请联系管理员清理数据库。"
        )


def get_company_default_role(company_id: int):
    """
    获取公司级默认角色（如 'member'）
    用于该公司新成员的默认权限分配
    """    
    company_id = validate_pk(company_id, "company_id")
    try:
        return Role.objects.get(company_id__exact=company_id, code="member")
    except Role.DoesNotExist:
        raise RuntimeError(
            "公司未初始化：缺少公司级默认角色 'member' 。"
            "请联系管理员初始化系统。"
        )
    except Role.MultipleObjectsReturned:
        raise RuntimeError(
            "数据异常：存在多个公司级默认角色 'member' 。"
            "请联系管理员清理数据库。"
        )


def validate_role_info(
    company_id: int,
    name: str,
    code: str,
    exclude_id: int = None
):
    """
    角色信息参数校验
    params:
        company_id: int 公司ID，为 None 时，表示创建全局角色
        name: str 角色名称，必填项
        code: str 角色编码，必填项，需要校验格式
        exclude_id: int 角色ID，为 None 时，表示创建角色，否则为更新角色
    """
    # 角色名称不能为空，角色编码符合规范
    name = validate_required(name, "角色名称")
    code = validate_code(code, "角色编码")

    # 检验角色名称唯一性
    if company_id is None:
        qs = Role.objects.filter(company_id__isnull=True, name=name)
    else:
        qs = Role.objects.filter(company_id=company_id, name=name)
    
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise BizException(ERROR_ROLE_CODE_EXISTS)
        
    return name, code


def create_role(
    user: User,
    name: str,
    code: str,
    is_active: bool = True,
    description: str = None,
    permission_codes: list = None,
    company_id: int = None,
):
    """创建角色"""
    if not company_id:
        company_id = user.company_id
    name, code = validate_role_info(company_id, name, code)
    RolePermission(user).check_can_create_role(company_id)
    with transaction.atomic():
        role = Role.objects.create(
            company_id=company_id,
            name=name,
            code=code,
            is_active=is_active,
            description=description,
        )
        basic_permission_codes = [
            # 系统权限
            "system_permission",
            
            # 权限管理（部门、角色、用户）
            "permission_manage",  # 前端导航栏目录-用户管理(权限管理)
            "review_department",  # 获取组织id
            "review_role",        # 获取角色id
            "user_manage"         # 用户管理界面
        ]
        all_permission_codes = list(set(basic_permission_codes + permission_codes))
        role.set_permissions(permission_codes=all_permission_codes)
        return role.to_dict()
    

def get_permission_index_map_cache():
    global ALL_PERMISSION_CACHE
    if ALL_PERMISSION_CACHE:
        return ALL_PERMISSION_CACHE
    permissions = Permission.objects.filter(is_active=True).all()
    ALL_PERMISSION_CACHE = [p.to_dict() for p in permissions]
    return ALL_PERMISSION_CACHE


def build_permission_tree(
    max_level: int,
    exclude_codes: set[str],
    include_codes: set[str]
) -> list[dict]:
    """
    通用权限树构建器，用于角色创建/编辑页面。
    
    :param max_level: 权限可见的最高等级（level <= max_level）
    :param exclude_codes: 需要排除的权限 code 集合
    :param include_codes: 已选中的权限 code 集合
    """
    all_permissions = get_permission_index_map_cache()
    allowed_perms = [perm for perm in all_permissions if perm["code"] not in exclude_codes and perm["tier_level"] <= max_level and perm["code"] in include_codes ]
    perm_map = { p["code"]: { **p, "children": [] } for p in allowed_perms }
    roots = []
    
    for p in perm_map.values():
        if p["parent_code"] and p["parent_code"] in perm_map:
            perm_map[p["parent_code"]]["children"].append(p)
        else:
            roots.append(p)
    
    # 按 sort_order 排序
    for node in perm_map.values():
        node["children"].sort(key=lambda x : x['sort_order'])
    
    return roots


def get_permission_tree(user: User) -> list[dict]:
    """根据用户权限获取权限树，在创建角色和编辑角色时使用"""
    RolePermission(user).check_can_get_role_permission_tree(user.company_id)
    perm_level = user.company.tier_level or 1
    exclude_codes = set(ADMIN_PERMISSION_CODES)
    include_codes = set(user.get_permissions())

    return build_permission_tree(
        max_level=perm_level,
        exclude_codes=exclude_codes,
        include_codes=include_codes,
    )


def _get_role_by_id(role_id: int) -> Role:
    """根据角色 ID 获取角色"""
    role_id = validate_pk(role_id, "role_id")
    role = Role.objects.filter(id=role_id).prefetch_related('permissions').first()
    if not role:
        raise BizException(ERROR_ROLE_NOT_FOUND)
    return role


def get_role_info(user: User, role_id: int) -> dict:
    """获取角色信息"""
    if user.company_id is None:
        raise BizException(ERROR_COMPANY_NOT_FOUND,'当前用户没有所属公司，无权编辑或创建角色！')

    role = _get_role_by_id(role_id)
    RolePermission(user).check_can_manage_role(role)
    
    ret_dict = {
        **role.to_dict(),
        "permission_codes": role.get_permissions(),
    }
    
    return ret_dict


def update_role_info(user: User, role_id: int, **kwargs):
    """更新角色信息"""
    role = _get_role_by_id(role_id)
    RolePermission(user).check_can_manage_role(role)
    if "name" in kwargs or "code" in kwargs:
        name = kwargs.get("name")
        code = kwargs.get("code")
        name, code = validate_role_info(
            company_id=role.company_id,
            name=name,
            code=code,
            exclude_id=role.id
        )
        role.update_info(**kwargs)
    
    if "permission_codes" in kwargs:
        role.set_permissions(kwargs.get("permission_codes"))


def enable_role(user: User, role_id: int):
    """启用角色"""
    role = _get_role_by_id(role_id)
    RolePermission(user).check_can_enable_role(role)
    role.is_active = True
    role.save()


def disable_role(user: User, role_id: int):
    """禁用角色"""
    role = _get_role_by_id(role_id)
    RolePermission(user).check_can_enable_role(role)
    role.is_active = False
    role.save()


def delete_role(user: User, role_id: int):
    """删除角色"""
    role = _get_role_by_id(role_id)
    RolePermission(user).check_can_delete_role(role)
    role.soft_delete()


def get_role_list(
    user: User, 
    company_id: int=None, 
    name: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None
):
    """获取角色列表"""
    # 构建查询参数
    company_id = user.company_id
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        # "company_id__isnull": {"input": True, "column": "company_id", "lookup": "isnull"},
        "name": {"input": name, "column": "name", "lookup": "icontains"},
    }
    filters = build_filters(filter_map)
    if RolePermission(user)._can_get_role(company_id):
        qs = Role.objects.filter(**filters)
        
        # 排序需求
        sort = sort or "-id"
        ordering = parse_ordering(sort)
        qs = qs.order_by(*ordering)
    else:
        qs = Role.objects.none()
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict() for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, results


def batch_delete_role(user: User, ids: list):
    """批量删除角色"""
    ids = validate_id_list(ids, "角色 ID 列表")
    return Role.objects.filter(
        id__in=ids, 
        is_deleted=False
    ).update(
        is_deleted=True, 
        deleted_at=datetime.now()
    )
