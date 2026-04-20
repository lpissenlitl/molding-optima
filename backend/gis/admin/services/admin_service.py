import copy
import logging
import random
import string
import uuid
import json
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from gis.admin.dto import UserListCriteria, RoleListCriteria, RecordListCriteria
from gis.admin.exceptions import (
    ERROR_USER_NOT_EXISTS,
    ERROR_USER_PASSWORD_INCORRECT,
    ERROR_USER_DISABLED,
    ERROR_ROLE_NAME_EXISTS,
    ERROR_ROLE_BIND_ONLY_LEAF_PERMISSION,
    ERROR_ROLE_NOT_ALLOW_SET_PERMISSION_ATTR,
    ERROR_ROLE_NOT_EXISTS,
    ERROR_GROUP_NOT_EXISTS,
    ERROR_PERMISSION_NOT_EXISTS,
    ERROR_USER_TOKEN_ERROR,
    ERROR_USER_NAME_DUPLICATE,
    ERROR_USER_ROLES_NOT_EXISTS,
    ERROR_PERMISSION_EXISTS,
    ERROR_COMPANY_NOT_PERMISSION,
    ERROR_DEPARTMENT_NOT_PERMISSION,
    ERROR_ROLE_NOT_PERMISSION,
    ERROR_USER_NOT_PERMISSION
)
from gis.admin.models import (
    Company,
    Group,
    Department,
    User,
    Role,
    RolePermissionRel,
    Permission,
    Record,
    Token
)
from gis.common.django_ext.models import paginate
from gis.common.encrypt import pwdutil
from gis.common.exceptions import BizException, ERROR_ILLEGAL_PARAMETER
from gis.common.django_ext.outer_request import request_post, request_get
from django.conf import settings
from gis.common.django_ext.json import JsonEncoder


##################################################################################
# 用户操作
##################################################################################

def _check_password(password):
    errors = []
    # if not any(x.isupper() for x in password):
    #     errors.append("必需含有大写字母\n")
    # if not any(x.islower() for x in password):
    #     errors.append("必需含有小写字母\n")
    # if not any(x.isdigit() for x in password):
    #     errors.append("必需含有数字\n")
    if not len(password) >= 6:
        errors.append("长度必需大于等于6\n")
    if errors:
        raise BizException(ERROR_ILLEGAL_PARAMETER, "密码格式：" + "".join(errors))


def _check_user_name_duplicate(name):
    if User.objects.filter(name=name, deleted=0).exists():
        raise BizException(ERROR_USER_NAME_DUPLICATE)


def _check_user_valid(user, check_deleted, check_enable):
    if not user:
        raise BizException(ERROR_USER_NOT_EXISTS)
    if check_deleted and user.deleted:
        raise BizException(ERROR_USER_NOT_EXISTS)
    if check_enable and not user.enable:
        raise BizException(ERROR_USER_DISABLED)


def add_user(
    name,
    password,
    company_id=None,
    group_id=None,
    department_id=None,
    engineer=None,
    email=None,
    phone=None,
    group_ids=None,
    role_ids=None,
    enable=False,
    is_super=False
):
    """
    新增用户
    """
    assert name
    assert password
    if role_ids:
        assert isinstance(role_ids, list)
    pwd_valid, pwd_fail_reason = pwdutil.check_pwd_strength(password)
    if not pwd_valid:
        raise BizException(ERROR_ILLEGAL_PARAMETER, pwd_fail_reason)
    _check_user_name_duplicate(name)

    with transaction.atomic():
        user = User.objects.create(
            name=name,
            password=pwdutil.hash_pwd(password),
            company_id=company_id,
            group_id=group_id,
            department_id=department_id,
            engineer=engineer,
            email=email,
            phone=phone,
            enable=enable,
            is_super=is_super,
        )
        user.save()
        _bind_user_to_roles(user, role_ids)
        _bind_user_to_groups(user, group_ids)

    return user.to_dict(exclude=["password", "deleted"])


def add_company_manager(params: dict):
    '''
    根据组织id创建组织管理员
    1. 创建默认部门
    2. 创建默认角色，并分配权限
    3. 创建用户
    '''
    return # 已弃用


def get_or_create_user(
    name,
    password=None,
    role_ids=None,
    enable=True,
    is_super=False,
    company_id=None,
):
    """
    查找或新增用户
    """
    assert name
    if role_ids:
        assert isinstance(role_ids, list)
    if password:
        pwd_valid, pwd_fail_reason = pwdutil.check_pwd_strength(password)
        if not pwd_valid:
            raise BizException(ERROR_ILLEGAL_PARAMETER, pwd_fail_reason)

    with transaction.atomic():
        user, _ = User.objects.get_or_create(
            name=name,
            defaults=dict(
                password=pwdutil.hash_pwd(password) if password else None,
                enable=enable,
                is_super=is_super,
                company_id=company_id,
            ),
        )
        _bind_user_to_roles(user, role_ids)
    user_dict: dict = user.to_dict(exclude=["password", "deleted"])
    if user_dict.get("roles"):
        user_dict.update({ role_ids: [ item.get("id") for item in user_dict.get("roles") ] })
    else:
        user_dict.update({ role_ids: [] })
    return user_dict


def _get_user_by_id(user_id, check_deleted=True, check_enable=True):
    user = User.objects.filter(pk=user_id, deleted=0).first()
    # _check_user_valid(user, check_deleted, check_enable)
    return user


def _get_user_by_name(name, check_deleted=True, check_enable=True):
    user = User.objects.filter(name=name, deleted=0).first()
    # _check_user_valid(user, check_deleted, check_enable)
    return user


def get_user_by_id(user_id, check_enable=True, with_roles=False, with_groups=True, check_deleted=True):
    user = _get_user_by_id(user_id, check_enable=check_enable, check_deleted=check_deleted)

    if not user:
        raise BizException(ERROR_USER_NOT_EXISTS)
    result = user.to_dict(exclude=["password", "deleted"])

    company: Company = Company.objects.filter(id=result["company_id"]).first()
    group: Group = Group.objects.filter(id=result["group_id"]).first()
    # department = Department.objects.get(id=user["department_id"])

    if company:
        result["company"] = company.name

    if group:
        result["group"] = group.name

    if with_roles:
        result["roles"] = [e.to_dict(fields=["id", "name"]) for e in user.roles.all()]
        result["role_ids"] = [item.get("id") for item in result["roles"]]

    if with_groups:
        result["groups"] = [e.to_dict(fields=["id", "name"]) for e in user.groups.all()]
        result['group_ids'] = [item.get("id") for item in result["groups"]]

    result["permissions"] = list(get_user_all_permission_codes(user.id))

    return result


def get_user_by_engineer(company_id, engineer):
    ret = dict()
    info_list = User.objects.filter(company_id=company_id, deleted=0).filter(engineer=engineer).values_list("engineer", "department", "name", "email")
    for info in info_list:
        ret.update({info[0]: [info[1], info[2], info[3]]})
    return ret


# 通过角色查找员工
def get_user_by_role(role_list=None, company_id=None):
    user_check = UserListCriteria()
    user_check.company_id = company_id
    total, users = list_users(user_check)
    emails = set()
    message = ""
    if users:
        for role in role_list:
            role_count, roles = list_roles(RoleListCriteria(name=role))
            if role_count == 0:
                message = "此角色:"+str(role)+"下没有用户。<br>"
                break
            for user in users:
                if user.get("roles_desc") and role in user.get("roles_desc"):
                    if user.get("email"):
                        emails.add(user.get("email"))
                    else:
                        message = "收件人"+str(user.get("engineer"))+"邮箱为空,"

    return {"emails":emails, 
    "message":message, 
    }


def update_user(user_id, **kwargs):
    """
    参数列表
    user_id,
    company_id=None,
    group_id=None,
    department_id=None,
    engineer=None,
    email=None,
    phone=None,
    group_ids=None,
    role_ids=None,
    enable=None,
    is_super=None,
    修改用户信息，包括重新分配角色
    """
    if "role_ids" in kwargs:
        assert isinstance(kwargs["role_ids"], list)
    if "group_ids" in kwargs:
        assert isinstance(kwargs["group_ids"], list)

    with transaction.atomic():
        user: User = _get_user_by_id(user_id, check_enable=False)
        if user:
            user.roles.clear()
            user.groups.clear()
            for key in kwargs:
                if key == "password":
                    setattr(user, key, pwdutil.hash_pwd(kwargs[key]))
                else:
                    setattr(user, key, kwargs[key])
            user.save()

            if "role_ids" in kwargs:
                _bind_user_to_roles(user, kwargs["role_ids"])
            if "group_ids" in kwargs:
                _bind_user_to_groups(user, kwargs["group_ids"])
        else:
            raise BizException(ERROR_USER_NOT_EXISTS)

def set_app_id(user_id, app_id = None):
    user: User = _get_user_by_id(user_id, check_enable=False)
    user.app_id = app_id
    user.save()


def disable_user(user_id):
    """
    禁用用户
    """
    user = _get_user_by_id(user_id)
    user.enable = False
    user.save()


def enable_user(user_id):
    """
    启用用户
    """
    user = _get_user_by_id(user_id, check_enable=False)
    user.enable = True
    user.save()


def delete_user(user_id):
    """
    删除用户
    """
    assert isinstance(user_id, int)

    with transaction.atomic():
        user = _get_user_by_id(user_id, check_enable=False)
        if user:
            user.delete()
            # user.deleted = True
            # user.enable = False
            # user.save()
        else:
            raise BizException(ERROR_USER_NOT_EXISTS)

def delete_multiple_user(user_id_list):
    for user_id in user_id_list:
        delete_user(user_id)


def list_users(criteria: UserListCriteria):
    if criteria.company_name:
        company_info_list = Company.objects.filter(name__contains=criteria.company_name, deleted=0).all().values("id", "name")
    else:
        company_info_list = Company.objects.filter(deleted=0).all().values("id", "name")
    company_id_list = [ item.get("id") for item in company_info_list ]
    company_id_name_map: dict = { item.get("id"): item.get("name") for item in company_info_list }

    if criteria.group_name:
        group_info_list = Group.objects.filter(name__contains=criteria.group_name, company_id__in=company_id_list, deleted=0).all().values("id", "name")
    else:
        group_info_list = Group.objects.filter(company_id__in=company_id_list, deleted=0).all().values("id", "name")
    group_id_list = [ item.get("id") for item in group_info_list ]
    group_id_name_map: dict = { item.get("id"): item.get("name") for item in group_info_list }

    # if criteria.department_name:
    #     department_info_list = Department.objects.filter(name__contains=criteria.department_name, company_id__in=company_id_list, deleted=0).all().values("id", "name")
    # else:
    #     department_info_list = Department.objects.filter(company_id__in=company_id_list, deleted=0).all().values("id", "name")
    # department_id_list = [ item.get("id") for item in department_info_list ]
    # department_id_name_map: dict = { item.get("id"): item.get("name") for item in department_info_list }

    # query = User.objects.filter(company_id__in=company_id_list, department_id__in=department_id_list, deleted=False).all().order_by("company_id").order_by("company_id", "department_id")
    query = User.objects.filter(company_id__in=company_id_list, deleted=False).all().order_by("company_id")
    # query = User.objects.filter(group_id__in=group_id_list, deleted=False).all().order_by("group_id")

    if criteria.name:
        query = query.filter(name=criteria.name)
    if criteria.enable is not None:
        query = query.filter(enable=criteria.enable)
    if criteria.role_id:
        query = query.filter(roles__exact=criteria.role_id)
    if criteria.engineer:
        query = query.filter(engineer__icontains=criteria.engineer)
    if criteria.email:
        query = query.filter(email__icontains=criteria.email)
    if criteria.phone:
        query = query.filter(phone__icontains=criteria.phone)
    if criteria.company_id:
        query = query.filter(company_id=criteria.company_id)
    # if criteria.department_id:
    #     query = query.filter(department_id=criteria.department_id)
    if criteria.page_no and criteria.page_size:
        query = paginate(query, criteria.page_no, criteria.page_size)

    total_count = query.count()
    user_dict_list = [ e.to_dict(exclude=["password"], return_many_to_many=True) for e in query ]

    for user_dict in user_dict_list:
        user_dict.update({ "company_name": company_id_name_map.get(user_dict.get("company_id")) })
        user_dict.update({ "group_name": group_id_name_map.get(user_dict.get("group_id")) })
        # user_dict.update({ "department_name": department_id_name_map.get(user_dict.get("department_id")) })
        if user_dict.get("roles"):
            user_dict.update({ "roles_desc": ', '.join([ item.get("name") for item in user_dict.get("roles") ]) })
        if user_dict.get("groups"):
            user_dict.update({ "groups_desc": ', '.join([ item.get("name") for item in user_dict.get("groups") ]) })

    return total_count, user_dict_list


def verify_password(name, password):
    """
    验证密码正确性
    """
    user = _get_user_by_name(name)
    if not user:
        raise BizException(ERROR_USER_NOT_EXISTS)
    if not pwdutil.check_pwd(password, user.password):
        raise BizException(ERROR_USER_PASSWORD_INCORRECT)
    return user.to_dict(exclude=["password", "deleted"], return_many_to_many=True)


def create_token(user_id, ua=None):
    new_token = str(uuid.uuid4())
    Token.objects.create(user_id=user_id, token=new_token, ua=ua)
    return new_token


def update_user_login_count(user_id):
    User.objects.filter(pk=user_id).update(login_count=F("login_count") + 1)


def update_user_last_login_time(user_id):
    User.objects.filter(pk=user_id).update(last_login_at=timezone.now())


def get_department_id_map():
    ret = dict()
    info_list = Department.objects.values_list("id", "name")
    for info in info_list:
        ret.update({info[0]: info[1]})
    return ret


def login(name, password, ua=None):
    '''
    登录需要验证：密码、企业、角色、用户
    '''
    user = verify_password(name, password)
    company: Company = Company.objects.filter(id=user["company_id"]).first()
    group: Group = Group.objects.filter(id=user["group_id"]).first()

    if user["is_super"]:
        if company:
            user.update({ "company_name": company.name })

        if group:
            user.update({ "group_name": group.name })
        pass
    else:
        if company and company.deleted == 1:
            raise BizException(ERROR_COMPANY_NOT_PERMISSION)
        else:
            user.update({ "company_name": company.name })

        if group and group.deleted == 1:
            pass
        elif group:
            user.update({ "group_name": group.name })

        # if department and department.deleted == 1:
        #     raise BizException(ERROR_DEPARTMENT_NOT_PERMISSION)

        if user["groups"] and len(user["groups"]) > 0:
            pass

        if user["roles"] and len(user["roles"]) > 0:
            allow_role_count = 0
            for role in user["roles"]:
                if role["deleted"] == 0:
                    allow_role_count += 1
            if allow_role_count == 0:
                raise BizException(ERROR_ROLE_NOT_PERMISSION)
        else:
            raise BizException(ERROR_USER_ROLES_NOT_EXISTS)

        if not user["enable"]:
            raise BizException(ERROR_USER_NOT_PERMISSION)

    # user.update(dict(department=get_department_id_map().get(user["department_id"])))
    token = create_token(user["id"], ua)
    user.update(dict(token=token))
    update_user_login_count(user["id"])
    update_user_last_login_time(user["id"])

    return user


def auth_login(name):
    user = _get_user_by_name(name).to_dict(return_many_to_many=True)
    token = create_token(user["id"])
    user.update(dict(token=token))
    update_user_login_count(user["id"])
    update_user_last_login_time(user["id"])
    return user


def get_user_by_app_id(app_id):
    user = User.objects.filter(app_id=app_id, deleted=0).first()
    if not user:
        raise BizException(ERROR_USER_NOT_EXISTS)
    
    return user.to_dict(exclude=["password"])


def get_user_by_token(token):
    try:
        token_user = Token.objects.filter(
            token=token,
            created_at__gt=timezone.now() - timedelta(hours=6),
            user__enable=True,
        ).first()
        if not token_user:
            raise BizException(ERROR_USER_TOKEN_ERROR)

        return token_user.user.to_dict(exclude=["password"])
    except Exception as e:
        print(e)


def delete_token(user_id, token):
    Token.objects.filter(user_id=user_id, token=token).delete()
    

def logout(user_id, token):
    Token.objects.filter(user_id=user_id, token=token).delete()


def reset_password_after_verify_old_success(user_id, old_password, new_password):
    """
    更新密码, 需先检验旧密码
    """
    user = _get_user_by_id(user_id)
    if not pwdutil.check_pwd(old_password, user.password):
        raise BizException(ERROR_USER_PASSWORD_INCORRECT)
    reset_password(user_id, new_password)


def reset_password(user_id, password):
    """
    重置密码
    """
    password = password if password else random_password()
    _check_password(password)
    user = _get_user_by_id(user_id)
    pwd_valid, pwd_fail_reason = pwdutil.check_pwd_strength(password)
    if not pwd_valid:
        raise BizException(ERROR_ILLEGAL_PARAMETER, pwd_fail_reason)
    user.password = pwdutil.hash_pwd(password)
    user.save()
    Token.objects.filter(user_id=user_id).delete()
    return password


def random_password():
    """
    随机生成13位的包含字母大小写+数字+特俗字符的密码
    """
    src_digits = string.digits
    src_uppercase = string.ascii_uppercase
    src_lowercase = string.ascii_lowercase
    password = random.sample(src_digits, 4) + random.sample(src_uppercase, 4) + random.sample(src_lowercase, 4)

    random.shuffle(password)
    new_password = "".join(password) + "#"
    return new_password



##################################################
##################################################


def add_role(name, description=None, permissions=None, company_id=None):
    """
    添加角色，并绑定权限
    """
    _check_role_permission_rel(permissions)
    _check_role_name_duplicate(name, company_id)

    with transaction.atomic():
        role = Role.objects.create(name=name, description=description, company_id=company_id)
        _bind_role_and_permissions(role, permissions)

    return role.to_dict()


def _check_role_name_duplicate(name, company_id):
    if Role.objects.filter(name=name).filter(company_id=company_id).exists():
        raise BizException(ERROR_ROLE_NAME_EXISTS)


def update_role(role_id, name=None, company_id=None, description=None, permissions=None, deleted=None):
    """
    更新角色，包括更新权限信息
    """
    _check_role_permission_rel(permissions)
    role = _get_role(role_id)
    with transaction.atomic():
        if company_id:
            role.company_id = company_id
        if name:
            role.name = name
        if description:
            role.description = description
        if deleted or deleted == 0:
            role.deleted = deleted
        role.save()
        # 重新设置权限，目前用的暴力删除全部旧的再重新设置。
        # 可以优化：分成新增，修改，删除三个集合事件，分别处理
        if permissions:
            role.permissions.clear()
            _bind_role_and_permissions(role, permissions)


def delete_role(role_id):
    """
    删除角色，会删除该角色绑定的权限关系
    """
    role = _get_role(role_id)
    role.deleted = 1
    role.save()
    # deleted_count, _ = role.delete()
    # return deleted_count > 0


# 获取 list 值：｛ label: name, value: id ｝
def get_role_option(company_id=None):
    # query = Role.objects.all()
    # if company_id:
    #     query = query.filter(company_id=company_id).values("id", "name")
    #     return [ { "label": item.get("name"), "value": item.get("id") } for item in query ]
    # return [ { "label": item.get("name"), "value": item.get("id") } for item in query.values("id", "name") ]
    try:
        query = Role.objects.values('id', 'name')  # 明确指定需要的字段
        
        options = [
            {"label": item.get("name"), "value": item.get("id")}
            for item in query if item.get("name") and item.get("id")
        ]
        
        return options
    
    except Exception as e:
        print(e)


# 删除多个角色信息--软删除
def del_multiple_role(role_id_list):
    if role_id_list:
        roles = Role.objects.filter(id__in=role_id_list).all()
        if len(roles) > 0:
            for index in range(0, len(roles)):
                roles[index].delete()


def get_role(role_id, with_permissions=False):
    """
    返回角色信息, 如果 with_permissions 为True时，返回数据包含权限列表
    :return {'permission': list<RolePermissionBO>}
    """
    role = _get_role(role_id)
    result = role.to_dict()
    if with_permissions:
        permissions = RolePermissionRel.objects.filter(role=role)
        result["permissions"] = [e.to_dict(fields=["permission", "include_fields"]) for e in permissions]
    return result


def list_roles(criteria: RoleListCriteria):
    if criteria.company_name:
        company_info_list = Company.objects.filter(name__contains=criteria.company_name, deleted=0).all().values("id", "name")
    else:
        company_info_list = Company.objects.filter(deleted=0).all().values("id", "name")
    company_id_list = [ item.get("id") for item in company_info_list ]
    company_id_name_map: dict = { item.get("id"): item.get("name") for item in company_info_list }

    query = Role.objects.filter(company_id__in=company_id_list).all().order_by("company_id")
    if criteria.name:
        query = query.filter(name__contains=criteria.name)
    if criteria.company_id:
        query = query.filter(company_id=criteria.company_id)
    total_count = query.count()
    if criteria.page_no and criteria.page_size:
        query = paginate(query, criteria.page_no, criteria.page_size)
    
    role_dict_list = [e.to_dict() for e in query]
    for role_dict in role_dict_list:
        role_dict.update({ "company_name": company_id_name_map.get(role_dict.get("company_id")) })

    return total_count, role_dict_list


def _bind_role_and_permissions(role, permissions):
    if not permissions:
        return
    for each in permissions:
        permission_id = each.get("permission_id")
        include_fields = each.get("include_fields")
        permission = _get_permission(permission_id)
        if not permission.is_leaf:
            raise BizException(ERROR_ROLE_BIND_ONLY_LEAF_PERMISSION, permission_id)
        if not permission.fields and include_fields:
            raise BizException(ERROR_ROLE_NOT_ALLOW_SET_PERMISSION_ATTR, permission_id)
        RolePermissionRel.objects.create(role=role, permission=permission, include_fields=include_fields)


def _check_role_permission_rel(permissions):
    if permissions:
        assert isinstance(permissions, list)


def _get_role(role_id):
    role = Role.objects.filter(pk=role_id).first()
    if not role:
        raise BizException(ERROR_ROLE_NOT_EXISTS, role_id)
    return role

def _get_group(group_id):
    group = Group.objects.filter(pk=group_id).first()
    if not group:
        raise BizException(ERROR_GROUP_NOT_EXISTS, group_id)
    return group


##################################################
##################################################


def get_user_permission_include_fields(user_id, permission_code):
    """
    返回某个用户对特定某个权限的可见字段集合
    :param user_id:
    :param permission_code:
    :return: {field1, field2, ...}
    """
    user = _get_user_by_id(user_id)
    result = set()
    if user.is_super:
        permission = Permission.objects.get(code=permission_code)
        if permission.fields:
            result = set(permission.fields)
    else:
        rels = RolePermissionRel.objects.filter(role__user__id=user_id, permission__code=permission_code)
        for each in rels:
            if each.include_fields:
                result.update(set(each.include_fields))
    return result


def get_user_all_permission_codes(user_id):
    """
    返回用户权限列表
    如果用户拥有一个 1/2/3/ 这样的三级结点权限，则会1，2，3级结点权限编码都会返回
    如果用户拥有多个角色，权限为所有角色的并集

    :param user_id:
    :return: {permission_code, ...}
    """
    result = set()
    user = _get_user_by_id(user_id)
    if user.is_super:
        result = {e.code for e in Permission.objects.all()}
    else:
        roles = user.roles.all()
        for role in roles:
            permissions = role.permissions.all()
            for permission in permissions:
                for each in _get_ancestor_include_current_permission(permission):
                    result.add(each["code"])

    return result


def get_total_permission_tree(is_super=None, company_id=None):
    """
    返回整个权限树结构视图
    """
    try:
        result = []
        index_map = copy.deepcopy(get_permission_index_map_cache())
        company = Company.objects.get(pk=company_id)
        for pk, each in index_map.items():
            if is_super or (company.level >= each.get("level") and each.get("code") != "super_user" and each.get("deleted") == 0):
                if each["parent_id"]:
                    parent = index_map[each["parent_id"]]
                    if "children" in parent:
                        parent["children"].append(index_map[pk])
                    else:
                        parent["children"] = [index_map[pk]]
                else:
                    result.append(index_map[pk])
        return result
    except Exception as e:
        print(e)


ALL_PERMISSION_CACHE = None

def get_permission_index_map_cache():
    global ALL_PERMISSION_CACHE
    if ALL_PERMISSION_CACHE:
        return ALL_PERMISSION_CACHE
    all_permissions = list(Permission.objects.all())
    ALL_PERMISSION_CACHE = {e.pk: e.to_dict(fields=["id", "parent", "name", "code", "fields", "level", "deleted"]) for e in all_permissions}
    return ALL_PERMISSION_CACHE


def get_permission_by_code(code, raise_none=True):
    assert code
    permission = Permission.objects.filter(code=code).first()
    if not permission:
        if raise_none:
            raise BizException(ERROR_PERMISSION_NOT_EXISTS, code)
        else:
            return None
    return permission.to_dict()


def get_permissions_by_codes(codes: list):
    permissions = Permission.objects.filter(code__in=codes).all().values("id")
    return [ { "permission_id": item.get("id") } for item in permissions ]


def get_company_manager_permissions():
    permissions = Permission.objects.filter(is_leaf=1, deleted=0, level__lt=9999).all().values("id")
    return [ { "permission_id": item.get("id") } for item in permissions ]


def _get_permission(permission_id):
    permission = Permission.objects.filter(pk=permission_id).first()
    if not permission:
        raise BizException(ERROR_PERMISSION_NOT_EXISTS, permission_id)
    return permission


def add_permission(params):
    parent_permission = None
    if params.get("parent_id"):
        parent_permission = _get_permission(params.get("parent_id"))

    if get_permission_by_code(params.get("code"), raise_none=False):
        # 更新
        permission = Permission.objects.filter(code=params.get("code")).first()
        for item in params:
            setattr(permission, item, params[item])
        permission.save()
        raise BizException(ERROR_PERMISSION_EXISTS)

    permission = Permission()
    for item in params:
        setattr(permission, item, params[item])
    permission.save()

    if parent_permission:
        if parent_permission.full_path.endswith("/"):
            permission.full_path = "{}{}/".format(parent_permission.full_path, permission.id)
        else:
            permission.full_path = "{}/{}/".format(parent_permission.full_path, permission.id)
    else:
        permission.full_path = "%s/" % permission.id

    permission.save()
    return permission.to_dict()


def _get_ancestor_include_current_permission(permission):
    ancestor_ids = [int(e) for e in permission.full_path.split("/") if e]
    return [get_permission_index_map_cache()[e] for e in ancestor_ids]


def insert_record(resource, resource_id, action, content, operator, ip, user_agent):
    record = Record.objects.create(
        resource=resource,
        resource_id=resource_id,
        action=action,
        content=content,
        operator=operator,
        ip=ip,
        user_agent=user_agent,
    )
    return record.to_dict()


def get_record_list(criteria: RecordListCriteria):
    query = Record.objects.all()
    if criteria.operator:
        query = query.filter(operator=criteria.operator)
    if criteria.resources:
        query = query.filter(resource__in=criteria.resources)
    if criteria.action:
        query = query.filter(action=criteria.action)
    if criteria.ip:
        query = query.filter(ip=criteria.ip)
    if criteria.created_at_begin:
        query = query.filter(created_at__gte=criteria.created_at_begin)
    if criteria.created_at_end:
        query = query.filter(created_at__lte=criteria.created_at_end)
    return (
        query.count(),
        [e.to_dict() for e in paginate(query.order_by("-updated_at"), criteria.page_no, criteria.page_size)],
    )


def _bind_user_to_roles(user: User, role_ids: list):
    if not role_ids:
        return
    for role_id in role_ids:
        role = _get_role(role_id)
        user.roles.add(role)

def _bind_user_to_groups(user: User, group_ids: list):
    if not group_ids:
        return
    for group_id in group_ids:
        group = _get_group(group_id)
        user.groups.add(group)


def list_user_name_phone(company_id=None):
    query = (
        User.objects.filter(deleted=False, company_id=company_id)
        .exclude(engineer__contains="管理员")
        .values_list("engineer", "phone", "department_id")
    )
    return list(query)


# 通过用户确认数据访问的范围,可以对应多个组织
def get_user_group(user_id):
    return []


def login_by_token(token):
    token_object = Token.objects.filter(
        token=token,
        created_at__gt=timezone.now() - timedelta(hours=6),
        user__enable=True,
    ).first()
    if not token_object:
        return "failure"
    user_object = token_object.user
    user = token_object.user.to_dict(exclude=["password"])
    user["roles"] = [e.to_dict(fields=["id", "name"]) for e in user_object.roles.all()]
    if not user["is_super"] and not user["roles"]:
        raise BizException(ERROR_USER_ROLES_NOT_EXISTS)

    token = token_object.token
    user.update(dict(token=token))
    update_user_login_count(user["id"])
    update_user_last_login_time(user["id"])
    user.update(dict(department=get_department_id_map().get(user["department_id"])))

    return user


def login_by_token_em(token):
    url = settings.MES + "/api/web/auth/verifyToken"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    ret = json.loads(request_post(url, json.dumps({"token":token},            ensure_ascii=False,
                    cls=JsonEncoder,), headers, flag=0))
    # ret = json.loads('{"name":"王园","result":true,"usernums":"boss"}')
    # 反馈正常：{"name":"王园","result":true,"usernums":"boss"}
    # 记录token,查询admin_user记录user_id
    if ret and ret.get("code")==200 and ret.get("data").get("valid")==True:
        user = _get_user_by_name(ret.get("data").get("username"))
        if user:
            # user_id = 222
            token_login = Token()
            token_login.user = user
            token_login.token = token
            token_login.save()
            # Token.objects.create(user_id=user_id, token=token_em)
            user = login_by_token(token)
            ret["user"] = user
    # 过期或异常：{"result":false,"message":"登陆已过期，请重新登陆"}
    return ret


def login_by_token_uuid(token):
    url = settings.MES + "/api/custom/open/sso/getUserinfoByUuid?uuid="+token
    # url = "https://iiot2.yizumi.com/api/custom/open/sso/getUserinfoByUuid?uuid="+token
    ret = json.loads(request_get(url))
    # {
    #  code:200, 
    #  msg:'success',
        # data: {
        # username:'lisi',
        # customerCode: 'test'
        # }
    # }
    #  {'code': 40101004, 'msg': '验证码失效', 'data': None}
    if ret and ret.get("data"):
        username = ret.get("data").get("username")
        if ret and ret.get("code")==200 and ret.get("msg")=="success" and username:
            user = _get_user_by_name(username)
            # 如果用户存在,那么使用id,如果不存在,那么返回用户不存在
            if user:
                token = create_token(user.id)

                user = login_by_token(token)
                ret["user"] = user
            else:
                ret["error_message"] = "用户不存在"
    # elif ret and ret.get("code") == "40101004":
    #     ret["error_message"] = "验证码已失效"
    return ret
