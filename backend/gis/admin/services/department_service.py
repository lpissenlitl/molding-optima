"""
部门服务
"""
from gis.common.django_ext.models import paginate
from gis.common.exceptions import BizException

from hsmolding.exceptions import ERROR_DATA_EXIST, ERROR_DATA_NOT_EXIST

from gis.admin.models import Company, User, Department
from gis.admin.services.admin_service import update_user, list_users
from gis.admin.dto import UserListCriteria
import logging


# 新增部门信息 返回obj
def _add_department(params: dict):
    # 增加部门的时候，先用name查询，如果存在，返回已经存在提示
    departments = Department.objects.filter(name=params.get("name"), company_id=params.get("company_id"),parent_id=params.get("parent_id")).all()
    if len(departments) == 0:
        department = Department()
    else:
        if departments.first().deleted == 0:
            raise BizException(ERROR_DATA_EXIST, "该部门信息已存在, 请勿重复添加!")
        elif departments.first().deleted == 1:
            raise BizException(ERROR_DATA_EXIST, "该部门信息已存在, 但为禁用状态, 请联系管理员!")
    for name in params:
        if hasattr(Department, name):
            setattr(department, name, params[name])
    department.save()
    return department


# 新增部门信息 返回dict
def add_department(params):
    department = _add_department(params)
    return department.to_dict()


# 获取部门信息 返回obj
def _get_department(department_id):
    if department_id:
        department = Department.objects.filter(pk=department_id).first()
        if not department:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该部门不存在")
        return department


# 获取部门信息 返回dict
def get_department(department_id):
    if department_id:
        department = _get_department(department_id)
        if department:
            return department.to_dict()


# 更新部门信息
def update_department(department_id, param_dict):
    department = _get_department(department_id)
    for key, value in param_dict.items():
        setattr(department, key, value)
    department.save()


# 删除部门信息
def delete_department(department_id):
    # # 删除部门之前，先去检查该部门下是否有用户。如果有，提醒用户先移出用户。
    # total_count, users = list_users(UserListCriteria({"department_id":department_id}))
    # if total_count > 0:
    #     return {"message":"该部门下有用户，请先到用户管理移出用户。"}
    # else:
    department = _get_department(department_id)
    if department:
        department.deleted = 1
        department.save()


# 获取 list 值：｛ label: name, value: id ｝
def get_department_option(company_id=None):
    query = Department.objects.all()
    if company_id:
        query = query.filter(company_id=company_id).values("id", "name")
        return [ { "label": item.get("name"), "value": item.get("id") } for item in query ]
    return [ { "label": item.get("name"), "value": item.get("id") } for item in query.values("id", "name") ]


# 获取 list 值：{ name: abbreviation }
def get_department_abbre_map():
    ret = dict()
    info_list = Department.objects.values_list("name", "abbreviation")
    for info in info_list:
        ret.update({info[0]: info[1]})
    return ret


# 获取 list 值: department
def list_departments(page_no=None, page_size=None, company_name=None, name=None, abbreviation=None, company_id=None):
    if company_name:
        company_info_list = Company.objects.filter(name__contains=company_name, deleted=0).all().values("id", "name")
    else:
        company_info_list = Company.objects.filter(deleted=0).all().values("id", "name")
    company_id_list = [ item.get("id") for item in company_info_list ]
    company_id_name_map: dict = { item.get("id"): item.get("name") for item in company_info_list }

    query = Department.objects.filter(company_id__in=company_id_list).all().order_by("company_id")
    if name:
        query = query.filter(name__icontains=name)
    if abbreviation:
        query = query.filter(abbreviation__icontains=abbreviation)
    if company_id:
        query = query.filter(company_id=company_id)
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    department_dict_list = [e.to_dict() for e in query]
    for department_dict in department_dict_list:
        department_dict.update({ "company_name": company_id_name_map.get(department_dict.get("company_id")) })

    return total_count, department_dict_list


# 删除多个组织信息--软删除
def del_multiple_department(department_id_list):
    if department_id_list:
        departments = Department.objects.filter(id__in=department_id_list).all()
        if len(departments) > 0:
            for index in range(0, len(departments)):
                departments[index].deleted = 1
                departments[index].save()


# 批量修改部门下的员工
def move_user_to_another_department(params):
    user_id_list = params.get("user_id_list")
    department_id = params.get("department_id")
    if user_id_list:
        for user_id in user_id_list:
            update_user(user_id=user_id, department_id=department_id)


# 通过部门名称获取部门id
def get_department_id_by_name(company_id=None):
    ret = dict()
    info_list = Department.objects.filter(company_id=company_id).values_list("name", "id")
    for info in info_list:
        ret.update({info[0]: info[1]})
    return ret


def get_department_tree(parent_id=0, name=None):
    if name:
        # 部门名不为空，直接根据条件查询数据
        try:
            model = Department.objects.filter(name__contains=name, deleted=0)
        except Exception as e:
            print(e)
    else:
        # 部门为空，获取全部部门
        department_tree = construct_department_trees(parent_id)  # 获取菜单树
        return {"department_tree":department_tree}


def construct_department_trees(parentId=0):
    '''
    通过递归实现根据父ID查找子部门
    1.根据父ID获取该部门下的子部门
    2.遍历子部门，继续向下获取，直到最小部门
    3.如果没有遍历到，返回空的数组，有返回权限列表
    :param parentId:
    :return:dict
    '''
    dept_data = Department.objects.filter(parent_id=parentId,deleted=0).order_by('order_num').all()
    dept_dict = [e.to_dict() for e in dept_data]
    if len(dept_dict) > 0:
        data = []
        for dept in dept_dict:
            dept['children'] = construct_department_trees(dept['id'])
            data.append(dept)
        return data
    return []
