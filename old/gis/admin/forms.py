from marshmallow import fields

from gis.admin.dto import UserListCriteria, RoleListCriteria, RecordListCriteria
from gis.common.django_ext.forms import (
    BaseSchema,
    PaginationSchema,
    PaginationBaseSchema,
    OptionField,
    ExportSchema,
    StripStrField,
    CNDatetimeField
)


# 新增公司信息
class AddCompanySchema(BaseSchema):
    name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    admin_id = fields.Integer(required=False, allow_none=True)
    admin_user = fields.String(required=False, allow_none=True)
    admin_passwd = fields.String(required=False, allow_none=True)
    level = fields.Integer(required=False, allow_none=True)
    parent_id = fields.Integer(required=False, allow_none=True)  # 父节点名称
    order_num = fields.Integer(required=False, allow_none=True)  # 显示顺序


# 更新公司信息
class UpdateCompanySchema(AddCompanySchema):
    id = fields.Integer()
    deleted = fields.Integer(required=False, allow_none=True)
    

# 删除公司信息 (多选)
class DelMultipleCompanySchema(BaseSchema):
    company_id_list = fields.List(fields.Integer(required=False, allow_none=True))


# 获取公司列表信息
class CompanyListSchema(PaginationBaseSchema):
    name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    deleted = fields.Integer(required=False, allow_none=True)


# 新增部门信息
class AddDepartmentSchema(BaseSchema):
    company_id = fields.Integer()
    name = fields.String()
    abbreviation = fields.String(required=False, allow_none=True)
    serial_number = fields.String(required=False, allow_none=True)
    header = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    attribute = fields.String(required=False, allow_none=True)
    parent_id = fields.Integer(required=False, allow_none=True)  # 父部门名称
    order_num = fields.Integer(required=False, allow_none=True)  # 显示顺序


# 更新部门信息
class UpdateDepartmentSchema(AddDepartmentSchema):
    id = fields.Integer()
    deleted = fields.Integer(required=False, allow_none=True)


# 删除部门信息 (多选)
class DelMultipleDepartmentSchema(BaseSchema):
    department_id_list = fields.List(fields.Integer(required=False, allow_none=True))


# 获取部门列表信息
class DepartmentListSchema(PaginationBaseSchema):
    company_name = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    abbreviation = fields.String(required=False, allow_none=True)
    company_id = fields.Integer(required=False, allow_none=True)


# 新增组织关系
class AddGroupSchema(BaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    parent_id = fields.Integer(required=False, allow_none=True)
    sort_index = fields.Integer(required=False, allow_none=True)
    created_at = CNDatetimeField(required=False, allow_none=True)
    updated_at = CNDatetimeField(required=False, allow_none=True)
    deleted = fields.Integer(required=False, allow_none=True)


# 编辑组织关系
class EditGroupSchema(BaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    parent_id = fields.Integer(required=False, allow_none=True)
    sort_index = fields.Integer(required=False, allow_none=True)
    created_at = CNDatetimeField(required=False, allow_none=True)
    updated_at = CNDatetimeField(required=False, allow_none=True)
    deleted = fields.Integer(required=False, allow_none=True)


# 获取组织列表
class GroupListSchema(BaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)


# 角色权限信息
class RolePermissionRelSchema(BaseSchema):
    permission_id = fields.Integer(required=True)
    include_fields = fields.List(fields.String(required=False))


# 新增角色信息
class AddRoleSchema(BaseSchema):
    name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    company_id = fields.Integer()
    permissions = fields.List(fields.Nested(RolePermissionRelSchema))


# 更新角色&权限信息
class UpdateRoleSchema(AddRoleSchema):
    id = fields.Integer()
    deleted = fields.Integer(required=False, allow_none=True)


# 删除角色信息 (多选)
class DelMultipleRoleSchema(BaseSchema):
    role_id_list = fields.List(fields.Integer(required=False, allow_none=True))


# 角色列表信息
class RoleListSchema(PaginationSchema):
    company_id = fields.Integer()
    company_name = fields.String()
    name = fields.String()

    def make_criteria(self, data) -> RoleListCriteria:
        return RoleListCriteria(
            company_id=data.get("company_id"),
            company_name=data.get("company_name"),
            name=data.get("name")
        )


# 用户注册信息
class RegisterSchema(BaseSchema):
    name = StripStrField(required=True)
    password = fields.String(required=True)


# 新增用户信息
class AddUserSchema(BaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    group_id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=True)
    password = fields.String(required=True)
    engineer = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True)
    enable = fields.Boolean(missing=False)
    is_super = fields.Boolean(missing=False)
    group_ids = fields.List(fields.Integer(required=False, allow_none=True))
    role_ids = fields.List(fields.Integer(required=False, allow_none=True))
    department_id = fields.Integer(required=False, allow_none=True)


# 获取用户信息
class GetUserSchema(PaginationSchema):
    name = fields.String()
    enable = fields.Boolean()
    role_id = fields.Integer()
    engineer = fields.String()
    email = fields.String()
    phone = fields.String(max_length=11)
    department_id = fields.Integer()
    department_name = fields.String()
    group_id = fields.Integer()
    group_name = fields.String()
    company_id = fields.Integer()
    company_name = fields.String()
    order_by = OptionField(["last_login_at", "-last_login_at", "id", "-id"], required=False, missing="-id")

    def make_criteria(self, data) -> UserListCriteria:
        return UserListCriteria(
            name=data.get("name"),
            enable=data.get("enable"),
            role_id=data.get("role_id"),
            engineer=data.get("engineer"),
            email=data.get("email"),
            phone=data.get("phone"),
            group_id=data.get("group_id"),
            group_name=data.get("group_name"),
            department_id=data.get("department_id"),
            department_name=data.get("department_name"),
            company_id=data.get("company_id"),
            company_name=data.get("company_name"),
            order_by=data.get("order_by"),
        )


# 更新用户信息
class UpdateUserSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    company_id = fields.Integer(required=False, allow_none=True)
    group_id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    password = fields.String(required=False, allow_none=True)
    engineer = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True)
    app_id = fields.String(required=False, allow_none=True)
    enable = fields.Boolean(missing=False)
    is_super = fields.Boolean(missing=False)
    group_ids = fields.List(fields.Integer(required=False, allow_none=True))
    role_ids = fields.List(fields.Integer(required=False, allow_none=True))
    department_id = fields.Integer(required=False, allow_none=True)


# 删除用户信息 (多选)
class DelMultipleUserSchema(BaseSchema):
    user_id_list = fields.List(fields.Integer())


# 用户登陆验证
class AuthLoginSchema(BaseSchema):
    name = fields.String(required=True)
    password = fields.String(required=True)
    ua = fields.String()  # 记录用户浏览器信息


# 更新用户密码
class UpdateUserPasswordSchema(BaseSchema):
    old_password = fields.String(required=True)
    new_password = fields.String(required=True)


# 重置用户密码
class ResetUserPasswordSchema(BaseSchema):
    new_password = fields.String()


# 操作记录
class RecordListSchema(ExportSchema):
    resources = fields.String(allow_none=True)
    operator = fields.Integer()
    action = fields.Integer()
    ip = fields.String()
    company_id = fields.Integer()
    created_at_begin = fields.DateTime()
    created_at_end = fields.DateTime()

    def make_criteria(self, data, **kwargs) -> RecordListCriteria:
        return RecordListCriteria(
            resources=data["resources"].split(",") if data.get("resources") else [],
            operator=data.get("operator"),
            action=data.get("action"),
            ip=data.get("ip"),
            created_at_begin=data.get("created_at_begin"),
            created_at_end=data.get("created_at_end"),
            company_id=data.get("company_id"),
        )



# 用户可以查看的公司列表
class UserGroupSchema(BaseSchema):
    user_id = fields.Integer()
    group_id = fields.Integer()


class UserGroupListSchema(BaseSchema):
    user_group_list = fields.List(fields.Nested(UserGroupSchema))


class AuthLoginByTokenSchema(BaseSchema):
    token = fields.String(required=True)


class AuthLoginByTokenEmSchema(BaseSchema):
    token_em = fields.String(required=True)

class AuthLoginByTokenUuidSchema(BaseSchema):
    token = fields.String(required=True)
