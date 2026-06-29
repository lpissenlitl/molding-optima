from identity.models import Company, Organization, User, Permission
from identity.exceptions import(
    ERROR_COMPANY_NAME_EMPTY,
    ERROR_COMPANY_NAME_EXISTS,
    ERROR_COMPANY_CODE_EXISTS,
    ERROR_COMPANY_CODE_FORMAT,
    ERROR_COMPANY_NOT_FOUND,
    ERROR_ORGANIZATION_NAME_EXISTS,
    ERROR_ORGANIZATION_CODE_EXISTS,
    ERROR_ORGANIZATION_PARENT_NOT_EXISTS,
    ERROR_ORGANIZATION_NOT_FOUND,
    ERROR_ORGANIZATION_LIST,
    ERROR_ORGANIZATION_TREE,
    ERROR_USER_NOT_FOUND,
    ERROR_USER_PERMISSION_DENIED,
    ERROR_USER_USERNAME_EMPTY,
    ERROR_USER_PASSWORD_EMPTY
)
from identity.services.user_service import register_user
from identity.services.role_service import create_role
from extensions.exceptions import BizException
from utils.validation import validate_required, validate_pk, validate_id_list, validate_code
from utils.db import build_filters, paginate_queryset, parse_ordering
from datetime import datetime
from django.db import transaction
from collections import defaultdict
from utils.object_utils import safe_get
from identity.permissions import CompanyPermission, OrganizationPermission


def validate_company_info(
    name: str,
    code: str,
    exclude_id: int = None
):
    """
    公司信息参数校验
    params:
        name: str 公司名称，必填项
        code: str 公司编码，必填项，需要校验格式
        exclude_id: int 公司ID，为 None 时，表示创建公司，否则为更新公司
    """
    name = validate_required(name, "公司名称")
    code = validate_code(code, "公司编码")
    
    # 检验唯一性（公司名称）
    qs = Company.objects.filter(name=name)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise BizException(ERROR_COMPANY_NAME_EXISTS, f"公司名称 '{name}' 已存在")
    
    # 检验唯一性（公司编码）
    qs = Company.objects.filter(code=code)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise BizException(ERROR_COMPANY_CODE_EXISTS, f"公司编码 '{code}' 已存在")
    
    return name, code


def create_company(
    user: User,
    name: str = None,
    code: str = None,
    industry: str = None,
    description: str = None,
    expires_at: datetime = None,
    tier_level: int = 1,
    is_active: bool = True,
    admin_user: dict = None,
):
    """创建公司"""
    # --- 参数校验 ---
    name, code = validate_company_info(name, code)
    CompanyPermission(user).check_can_create_company()
    
    if not admin_user:
        raise BizException(ERROR_USER_NOT_FOUND)
    
    username = admin_user.get("username")
    password = admin_user.get("password") 
    if not username:
        raise BizException(ERROR_USER_USERNAME_EMPTY)
    if not password:
        raise BizException(ERROR_USER_PASSWORD_EMPTY)
    
    with transaction.atomic():
        # --- 创建公司 ---
        company = Company.objects.create(
            name=name,
            code=code,
            industry=industry,
            description=description,
            is_active=is_active,
            tier_level=tier_level,
            expires_at=expires_at,
        )
        # --- 创建公司组织树根部 ---
        organization = create_organization(
            user=user,
            name=company.name+"总部",
            code=company.code+"_HQ",
            company_id=company.id,
            org_type="group",
            path="/"+company.code+"_HQ",
            sort_order=0,
            is_active=True,
        )
        permission_codes = list(Permission.objects.filter(is_active=True,tier_level__lte=tier_level).values_list("code", flat=True))
        # --- 创建公司管理员角色 ---
        role = create_role(
            user=user,
            name="公司管理员",
            code=company.code+"_admin",
            is_active=True,
            description="公司管理员角色",
            company_id=company.id,
            # TODO: 初始化公司管理员权限
            permission_codes=permission_codes
        )
        # ---创建公司管理员用户 ---
        register_user(
            user=user,
            username=username,
            password=password,
            company_id=company.id,
            organization_id=organization.get("id",None),
            is_active=True,
            is_tenant_admin=True,
            is_superuser=False,
            expires_at=expires_at,
            roles=[role.get('id')],
        )
        
        # TODO: 初始化创建公司 默认组织、角色、权限、管理员用户
    
    return company.to_dict()


def _get_company_by_id(company_id: int) -> Company:
    """根据公司 ID 获取公司对象"""
    company_id = validate_pk(company_id, "company_id")
    company = Company.objects.filter(id=company_id).first()
    if not company:
        raise BizException(ERROR_COMPANY_NOT_FOUND)
    return company


def get_company_info(user: User, company_id: int) -> dict:
    """根据公司 ID 获取公司信息"""
    company = _get_company_by_id(company_id)
    CompanyPermission(user).check_can_manage_company(company)
    return company.to_dict()


def update_company_info(user: User, company_id: int, **kwargs):
    """更新公司信息"""
    company = _get_company_by_id(company_id)
    CompanyPermission(user).check_can_manage_company(company)
    name = kwargs.get("name")
    code = kwargs.get("code")
    name, code = validate_company_info(
        name=name,
        code=code,
        exclude_id=company.id
    )
    company.update_info(**kwargs)


def delete_company(user: User, company_id: int, ):
    """删除公司（软删除）"""
    company = _get_company_by_id(company_id)
    CompanyPermission(user).check_can_manage_company(company)
    company.soft_delete()
    

def get_list_of_company(
    user: User,
    name: str = None,
    code: str = None,
    is_active: bool = None,
    industry: str = None, 
    page_no: int = None,
    page_size: int = None,
    sort: str = None
):
    """获取公司列表"""
    
    if not user.is_superuser:
        return 0,[]
    
    # 构建查询参数
    filter_map = {
        "name": {"input": name, "column": "name", "lookup": "icontains"},
        "code": {"input": code, "column": "code", "lookup": "icontains"},
        "industry": {"input": industry, "column": "industry", "lookup": "icontains"},
        "is_active": {"input": is_active, "column": "is_active", "lookup": "exact"},
    }
    filters = build_filters(filter_map)
    qs = Company.objects.filter(**filters)
    
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict() for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, results


def batch_delete_company(user: User, ids: list):
    """批量删除公司"""
    ids = validate_id_list(ids, "公司 ID 列表")
    return Company.objects.filter(id__in=ids).update(is_deleted=True, deleted_at=datetime.now())


def validate_organization_info(
    company_id: int,
    name: str,
    code: str,
    exclude_id: int = None,
):
    """
    组织机构信息参数校验
    params:
        company_id: int 公司ID，为 None 时，表示创建全局角色
        name: str 组织机构名称，必填项
        code: str 组织机构编码，必填项，需要校验格式
        exclude_id: int 组织机构ID，为 None 时，表示创建角色，否则为更新角色
    """
    company_id = validate_pk(company_id, "公司ID")  # 公司ID不能为 None
    name = validate_required(name, "组织机构名称")  # 组织机构名称不能为空
    code = validate_code(code, "组织机构编码")  # 组织机构编码不能为空，且需要符合规范

    # 必须要有公司信息
    company = Company.objects.filter(id=company_id).first()
    if company is None:
        raise BizException(ERROR_COMPANY_NOT_FOUND)

    # 检验组织名称唯一性
    qs = Organization.objects.filter(company_id=company_id, name=name)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise BizException(ERROR_ORGANIZATION_NAME_EXISTS)
    
    # 校验组织编码唯一性
    qs = Organization.objects.filter(company_id=company_id, code=code)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise BizException(ERROR_ORGANIZATION_CODE_EXISTS)
    
    return name, code


def enable_company(user: User, company_id: int):
    """启用公司"""
    if not user.is_superuser:
        raise BizException(ERROR_USER_PERMISSION_DENIED)
    company = _get_company_by_id(company_id)
    
    company.is_active = True
    company.save()


def disable_company(user: User, company_id: int):
    """禁用公司"""
    if not user.is_superuser:
        raise BizException(ERROR_USER_PERMISSION_DENIED)
    company = _get_company_by_id(company_id)
    
    company.is_active = False
    company.save()
    

def assume_company(user: User, company_id: int):
    """接管公司"""
    if not user.is_superuser:
        raise BizException(ERROR_USER_PERMISSION_DENIED)
    company = _get_company_by_id(company_id)

    user.company_id = company.id
    user.is_tenant_admin = True
    user.save()


def release_company(user: User, company_id: int):
    """放弃接管公司"""
    if not user.is_superuser:
        raise BizException(ERROR_USER_PERMISSION_DENIED)
    company = _get_company_by_id(company_id)
    
    user.company_id = None
    user.is_tenant_admin = False
    user.save()
    

def create_organization(
    user: User,
    name: str,
    code: str,
    company_id: int = None,
    manager_id: int = None,
    parent_id: int = None,
    org_type: str = None,
    description: str = None,
    path: str = None,
    sort_order: int = None,
    is_active: bool = True
):
    """创建组织"""
    if not company_id:
        if parent_id is not None:
            company_id = Organization.objects.filter(id=parent_id).first().company_id
        else:
            raise BizException(ERROR_COMPANY_NOT_FOUND)
    name, code = validate_organization_info(company_id, name, code)
    OrganizationPermission(user).check_can_create_organization(company_id)
    # 无 parent_id 时为根节点，否则为子组织节点
    if parent_id is None:
        level = 0
        path = f'/{code}'
        sort_order = 1
    else:
        parent = Organization.objects.filter(id=parent_id).first()
        if not parent:
            raise BizException(ERROR_ORGANIZATION_PARENT_NOT_EXISTS)
        OrganizationPermission(user)._check(OrganizationPermission(user)._can_operate_organization(parent, "update_department"), "用户无此组织管理权限，无法在该组织下创建新组织")
        if parent.level is not None:
            level = parent.level + 1
        else:
            raise BizException(ERROR_ORGANIZATION_LIST)
        if parent.path:
            path = f'{parent.path}/{code}'
    with transaction.atomic():
        # 处理该组织排序的问题
        if sort_order is None:
            exist_count = Organization.objects.filter(parent_id=parent_id).select_for_update().count()
            sort_order = exist_count + 1
        
        organization = Organization.objects.create(
            company_id=company_id,
            name=name,
            code=code,
            description=description,
            level=level,
            path=path,
            sort_order=sort_order,
            org_type=org_type,
            manager_id=manager_id,
            parent_id=parent_id,
            is_active=is_active
        )
    
    return organization.to_dict()
        

def get_list_of_organization(
    user: User,
    company_id=None,
    sort=None,
    page_no=None,
    page_size=None,
):
    if user==None:
        raise BizException(ERROR_USER_NOT_FOUND)
    
    query = Organization.objects.all().order_by("id").select_related("manager")
    all_company_ids = list(Organization.objects.values_list('company_id', flat=True).distinct())
    permission_company_ids = []
    for cmpid in all_company_ids:
        if OrganizationPermission(user)._can_get_organizaiton_tree(cmpid):
            permission_company_ids.append(cmpid)
    query = query.filter(company_id__in=permission_company_ids)
    
    
    # if user:
    #     if user.is_superuser: # 如果是超级管理员,不过滤
    #         pass
    #     elif user.company_id != None: # 非超级管理员只能查看自己公司的组织
    #         company_id = user.company_id
    #         query = query.filter(company_id=company_id)
    #         if not OrganizationPermission(user).check_can_get_organizaiton_tree(company_id):
    #             query = query.none()
    #     else: # 非超级管理员如果没有公司信息(游客？)则根据其权限查看组织信息
    #         all_company_ids = company_ids = list(Organization.objects.values_list('company_id', flat=True).distinct())
    #         permission_company_ids = []
    #         for cmpid in all_company_ids:
    #             if OrganizationPermission(user).check_can_get_organizaiton_tree(cmpid):
    #                 permission_company_ids.append(cmpid)
    #         query = query.filter(company_id__in=permission_company_ids)
    
    total = query.count()
    return total, [ 
        {
            **e.to_dict(), 
            "manager_name": safe_get(e, "manager.engineer_name", None)
        }
        for e in query 
    ]


def _get_organization_by_id(organization_id: int):
    """根据组织 ID 获取组织对象"""
    organization_id = validate_pk(organization_id, "组织ID")
    organization = Organization.objects.filter(id=organization_id).first()
    if organization is None:
        raise BizException(ERROR_ORGANIZATION_NOT_FOUND)
    return organization


def get_organization_info(user: User, organization_id: int):
    """根据组织 ID 获取组织信息"""
    organization = _get_organization_by_id(organization_id)
    OrganizationPermission(user).check_can_manage_organization(organization)
    return organization.to_dict()


def update_organization_info(user: User, organization_id: int, **kwargs):
    """更新组织信息"""
    organization = _get_organization_by_id(organization_id)
    OrganizationPermission(user).check_can_manage_organization(organization)
    name = kwargs.get("name")
    code = kwargs.get("code")
    name, code = validate_organization_info(
        company_id=organization.company_id,
        name=name,
        code=code,
        exclude_id=organization.id
    )
    organization.update_info(**kwargs)


def batch_update_organization_structure(user: User, org_list: list):
    """批量更新组织结构"""
    resort_organizations(org_list, user)


def resort_organizations(org_list: list, user: User):
    """
    重新排序组织（批量更新）
    params:
        org_list: list 组织列表，格式为 [{id: 1, sort_order: 1, ...}, {id: 2, sort_order: 2, ...}]
    """
    
    if not org_list:
        return
    
    if not isinstance(org_list, list):
        raise BizException(ERROR_ORGANIZATION_LIST, "参数必须是一个列表")
    
    # 所有待更新的 org_id，构建 map：org_id -> org
    org_ids = { item["id"] for item in org_list }
    
    # 获取涉及到的 parent_id，构建 map：parent_id -> parent
    parent_ids = { item["parent_id"] for item in org_list if item["parent_id"] }

    # 合并要查询的对象，获取查询对象
    all_ids = org_ids | parent_ids
    all_orgs = Organization.objects.filter(id__in=all_ids).all()
    org_map = { org.id: org for org in all_orgs }

    # 构建要更新的组织信息
    organizations = []
    for item in org_list:

        if not isinstance(item, dict):
            raise BizException(ERROR_ORGANIZATION_LIST, "列表中的每个元素必须是字典")

        org_id = item.get("id")
        organization = org_map.get(org_id)
        OrganizationPermission(user).check_can_manage_organization(organization)
        
        parent_id = item.get("parent_id")
        parent = org_map.get(parent_id)
        
        if not organization or not parent:
            raise BizException(ERROR_ORGANIZATION_NOT_FOUND)
        
        # 更新组织信息        
        organization.parent_id = parent.id
        organization.sort_order = item.get("sort_order")
        organization.path = f'{parent.path}/{organization.code}'

        organizations.append(organization)
    
    Organization.objects.bulk_update(organizations, ["parent_id", "sort_order", "path"])

    
def delete_organization(user: User, organization_id: int):
    """删除组织（软删除）"""
    organization = _get_organization_by_id(organization_id)
    OrganizationPermission(user).check_can_delete_organization(organization)
    organization.soft_delete()


def construct_organization_tree(root_org: Organization):
    """递归构造组织树"""
    all_orgs = root_org.get_descendants()
    
    children_map = defaultdict(list)
    org_map = {}
    org_map[root_org.id] = root_org
    for org in all_orgs:
        org_map[org.id] = org
        if org.parent_id:
            children_map[org.parent_id].append(org)
    
    def _build_tree(org: Organization):
        node = org.to_dict()
        children = children_map.get(org.id, [])
        if children:
            node["children"] = [ _build_tree(child) for child in children]
        else:
            node["children"] = []
        return node
    
    return _build_tree(root_org)


def get_organization_tree(user: User):
    """获取组织树"""
    company_id = user.company_id
    company_id = validate_pk(company_id, "公司ID")
    OrganizationPermission(user).check_can_get_organizaiton_tree(company_id)
    root_org = Organization.objects.get(
        company_id=company_id, 
        parent_id__isnull=True
    )
    if not root_org:
        raise BizException(ERROR_ORGANIZATION_TREE, "公司下没有组织信息")

    return construct_organization_tree(root_org)  


def batch_delete_organization(user: User, ids: list):
    """批量删除组织"""
    ids = validate_id_list(ids, "组织 ID 列表")
    return Organization.objects.filter(id__in=ids).update(is_deleted=True, deleted_at=datetime.now())
