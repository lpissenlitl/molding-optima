"""
公司服务
"""
from gis.common.exceptions import BizException

from gis.admin.exceptions import ERROR_GROUP_NOT_EXISTS

from gis.admin.models import Company, Group


group_description = []


# 新增公司组织对象
def _add_company_group(params: dict):
    if params.get("company_id"):
        company_id = params.get("company_id")
        company = Company.objects.get(id=company_id)
        group = Group()
        for key in params:
            if hasattr(Group, key):
                setattr(group, key, params[key])
        group.company = company
        group.save()
        return group


# 新增公司组织
def add_company_group(params: dict):
    group: Group = _add_company_group(params)
    return group.to_dict()


# 获取公司组织对象
def _get_company_group(company_group_id: int):
    if company_group_id:
        try:
            group = Group.objects.filter(id=company_group_id).first()
            if not group:
                raise BizException(ERROR_GROUP_NOT_EXISTS)
        except Exception as e:
            raise BizException(ERROR_GROUP_NOT_EXISTS) from e


# 获取公司组织
def get_company_group(company_group_id: int):
    trees = construct_group_trees(company_group_id)
    return trees


def construct_group_trees(parent_id: int = 0):
    data = _get_company_group(parent_id)
    if data:
        group_data = data.to_dict()
        dept_data = Group.objects.filter(parent_id=parent_id, deleted=0)

        # 构建企业树
        children = []
        for group in dept_data:
            children.append(construct_group_trees(group.id))
        if children:
            group_data["children"] = children

        return group_data


# 更新公司组织
def udpate_company_group(company_group_id: int, params: dict):
    group: Group = _get_company_group(company_group_id)
    if group and params:
        for key in params:
            if hasattr(Group, key):
                setattr(group, key, params[key])
        group.save()
        return group.to_dict()


# 删除公司组织
def delete_company_group(company_group_id: int):
    if company_group_id:
        group: Group = _get_company_group(company_group_id)
        if group:
            group.delete()


# 获取公司组织列表
def get_list_of_group(
    company_id: int = None
):
    query = Group.objects.all()
    if company_id:
        query = Group.objects.filter(company_id=company_id)
    total = query.count()
    return total, [ e.to_dict() for e in query ]
