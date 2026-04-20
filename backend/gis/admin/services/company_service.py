"""
公司服务
"""
from webbrowser import get
from gis.common.django_ext.models import paginate
from gis.common.exceptions import BizException

from hsmolding.exceptions import ERROR_DATA_EXIST, ERROR_DATA_NOT_EXIST

from gis.admin.models import User, Company, Group
from gis.admin.services import admin_service, group_service
from django.db import transaction


group_description = []

# 构建公司默认组织对象
def construct_company_default(
    company_id: int = None, 
    company_name: str = None,
    admin_user: str = None,
    admin_passwd: str = None
):
    with transaction.atomic():
        if not company_id:
            return

        root_dict = {
            "company_id": company_id,
            "name": company_name,
            "parent_id": None,
            "sort_index": 0,
            "created_at": None,
            "updated_at": None,
            "deleted": 0
        }    
        root = group_service._add_company_group(root_dict)
        
        # 组织--系统管理
        xtgl_dict = {
            "company_id": company_id,
            "name": "系统管理",
            "parent_id": root.id,
            "sort_index": 0,
            "created_at": None,
            "updated_at": None,
            "deleted": 0
        }
        xtgl_group = group_service._add_company_group(xtgl_dict)

        # 角色--管理员
        admin_permissions = [

            "review_mold",
            "add_mold",
            "delete_mold",
            "update_mold",

            "process_list",
            # "process_optimize",
            # "process_rule",
            "process_entry",
            "process_transplant",

            "review_machine",
            "add_machine",
            "delete_machine",
            "update_machine",

            "review_polymer",
            "add_polymer",
            "delete_polymer",
            "update_polymer",

            "machine_performance_trial",

            "review_department",
            "add_department",
            "delete_department",
            "update_department",

            "review_role",
            "add_role",
            "delete_role",
            "update_role",

            "review_user",
            "add_user",
            "delete_user",
            "update_user"
        ]
        admin_permission_ids = admin_service.get_permissions_by_codes(admin_permissions)
        admin_role = {
            "name": company_name+"管理员",
            "description": "负责"+company_name+"维护与管理",
            "permissions": admin_permission_ids,
            "company_id": company_id,
        }
        admin_role_dict: dict = admin_service.add_role(**admin_role)

        params = {
            "company_id": company_id,
            "enable": 1,
            "is_super": 0,
            "name": admin_user,
            "engineer": company_name,
            "password": admin_passwd,
            "role_ids": [ admin_role_dict.get("id") ],
            "group_id": xtgl_group.id,
            "group_ids": [ xtgl_group.id ]
        }
        user_dict: dict = admin_service.add_user(**params)
        update_company(company_id, { "admin_id": user_dict.get("id") })


# 新增企业信息 返回obj
def _add_company(params: dict):
    # 增加公司的时候，先用name查询，如果存在，返回已经存在提示
    companies = Company.objects.filter(name=params.get("name")).all()
    if len(companies) == 0:
        company = Company()
    else:
        if companies.first().deleted == 0:
            raise BizException(ERROR_DATA_EXIST, "该企业信息已存在, 请勿重复添加!")
        elif companies.first().deleted == 1:
            raise BizException(ERROR_DATA_EXIST, "该企业信息已存在, 但为禁用状态, 请联系!")

    for name in params:
        if hasattr(Company, name):
            setattr(company, name, params[name])
    company.save()

    # 构建企业初始信息
    construct_company_default(
        company.id, 
        company.name, 
        params.get("admin_user"), 
        params.get("admin_passwd")
    )

    return company


# 新增企业信息 返回dict
def add_company(params):
    company = _add_company(params)
    return company.to_dict()


# 获取企业信息 返回obj
def _get_company(company_id):
    if company_id:
        company = Company.objects.filter(pk=company_id).first()
        if not company:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该企业不存在")
        return company


# 获取企业信息 返回dict
def get_company(company_id):
    if company_id:
        company = _get_company(company_id)
        if company:
            return company.to_dict()


# 更新企业信息
def update_company(company_id, param_dict):
    company = _get_company(company_id)
    for key, value in param_dict.items():
        setattr(company, key, value)
    company.save()


# 删除企业信息
def delete_company(company_id):
    company = _get_company(company_id)
    if company:
        company.deleted = 1
        company.save()


# 获取 list 值：{ id: name }
def get_company_id_map():
    ret = dict()
    info_list = Company.objects.values_list("id", "name")
    for info in info_list:
        ret.update({ info[0]: info[1] })
    return ret


# 获取 list 值：name
def list_company_name():
    query = Company.objects.values_list("name").order_by("name")
    return [item[0] for item in query]


# 获取 list 值: company
def list_companies(page_no=None, page_size=None, name=None, description=None, deleted=None):
    query = Company.objects.all()
    if name:
        query = query.filter(name__icontains=name)
    if description:
        query = query.filter(description__icontains=description)
    if deleted or deleted == 0:
        query = query.filter(deleted=deleted)
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    return total_count, [e.to_dict() for e in query]


# 删除多个企业信息--软删除
def del_multiple_company(company_id_list):
    if company_id_list:
        companies = Company.objects.filter(id__in=company_id_list).all()
        if len(companies) > 0:
            for index in range(0, len(companies)):
                companies[index].deleted = 1
                companies[index].save()
    

# 获取企业下拉列表
def get_company_option():
    company_id_name_map = Company.objects.all().values("id", "name")
    return [ { "label": item.get("name"), "value": item.get("id") } for item in company_id_name_map ]


global_parent_id = None
global_is_super = None

def get_group_tree(parent_id=0, company_id=None, is_super=None, name=None):
    if name:
        # 企业名不为空，直接根据条件查询数据
        try:
            model = Company.objects.filter(name__contains=name, deleted=0)
        except Exception as e:
            print(e)
    else:
        # 企业为空，获取全部企业
        global global_parent_id
        global global_is_super
        global_parent_id = parent_id
        global_is_super = is_super
        if is_super:
            parent_id = 0
        group_tree = construct_group_trees(parent_id,company_id)  # 获取菜单树
        return {"group_tree":list(group_tree)}


def construct_group_trees(parent_id=0,company_id=None):
    '''
    通过递归实现根据父ID查找子企业
    1.根据父ID获取该企业下的子企业
    2.遍历子企业，继续向下获取，直到最小企业
    3.如果没有遍历到，返回空的数组，有返回企业列表
    :param parentId:
    :return:dict
    '''
    dept_data = Company.objects.filter(parent_id=parent_id,deleted=0).order_by('order_num').all()
    dept_dict = []
    global global_parent_id
    global global_is_super
    for group in list(dept_data):
        # 如果不是从根节点开始,那么需要包括该节点作为根节点[旁支节点不要],以及它的所有子节点.
        if company_id and company_id != 1 and group.id == company_id and group.parent_id == global_parent_id or group.parent_id != global_parent_id or global_is_super:
            dept_dict.append(group.to_dict())
    if len(dept_dict) > 0:
        data = []
        for dept in dept_dict:
            dept['children'] = construct_group_trees(dept['id'], dept['parent_id'])
            data.append(dept)
        return data
    return []


def get_group(company_id):
    global group_description
    group_description = []
    description = get_group_parent(company_id=company_id)
    description.reverse()
    return {"group_route":"_".join(description),"group_description":description}


def get_group_parent(company_id):
    # 通过递归根据parent_id找到所在企业
    global group_description
    dept_data = Company.objects.filter(id=company_id,deleted=0).first()
    if dept_data:
        dept_dict = dept_data.to_dict()
        group_description.append(dept_dict.get("name"))
        get_group_parent(dept_dict['parent_id'])
        return group_description
