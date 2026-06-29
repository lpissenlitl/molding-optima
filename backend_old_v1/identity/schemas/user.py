from marshmallow import fields, Schema
from extensions.schemas import StripStrField, BaseSchema, PaginationBaseSchema


class RegisterSchema(Schema):
    """用户注册信息"""
    username = StripStrField(required=True, metadata={"description": "用户名"})
    password = fields.String(required=True, metadata={"description": "密码"})


class LoginSchema(Schema):
    """用户登录信息"""
    username = fields.String(required=True, metadata={"description": "用户名"})
    password = fields.String(required=True, metadata={"description": "密码"})
    ua = fields.String(required=True, metadata={"description": "用户代理"})
    

class UpdateUserPasswordSchema(Schema):
    """修改用户密码信息"""
    old_password = fields.String(required=True, metadata={"description": "旧密码"})
    new_password = fields.String(required=True, metadata={"description": "新密码"})
    

class ResetUserPasswordSchema(Schema):
    """重置用户密码信息"""
    username = fields.String(allow_none=True, metadata={"description": "用户名"})
    password = fields.String(required=True, metadata={"description": "密码"})
    code = fields.String(allow_none=True, metadata={"description": "验证码"})


class UserSchema(BaseSchema):
    """用户信息"""
    # company_id = fields.Integer(allow_none=True, metadata={"description": "所属公司ID"})
    organization_id = fields.Integer(allow_none=True, metadata={"description": "所属组织ID"})
    id = fields.Integer(dump_only=True, metadata={"description": "用户ID"})
    username = fields.String(required=True, metadata={"description": "用户名"})
    password = fields.String(allow_none=True, metadata={"description": "密码"})
    engineer_name = fields.String(allow_none=True, metadata={"description": "工程师姓名"})
    email = fields.String(allow_none=True, metadata={"description": "邮箱"})
    phone = fields.String(allow_none=True, metadata={"description": "手机号"})
    is_active = fields.Boolean(allow_none=True, metadata={"description": "是否激活"})
    is_staff = fields.Boolean(allow_none=True, metadata={"description": "是否员工"})
    # is_tenant_admin = fields.Boolean(allow_none=True, metadata={"description": "是否租户管理员"})
    # is_superuser = fields.Boolean(allow_none=True, metadata={"description": "是否超级管理员"})
    login_count = fields.Integer(allow_none=True, metadata={"description": "登录次数"})
    last_login_at = fields.DateTime(dump_only=True, metadata={"description": "上次登录时间"})
    expires_at = fields.DateTime(allow_none=True, metadata={"description": "用户有效期"})
    roles = fields.List(fields.Integer(), allow_none=True, metadata={"description": "角色ID列表"})
    extra_accessible_orgs = fields.List(fields.Integer(), allow_none=True, metadata={"description": "被授权可访问的组织ID列表"})


class UserListSchema(PaginationBaseSchema):
    """用户列表信息"""
    company_id = fields.Integer(allow_none=True, metadata={"description": "公司ID"})
    organization_id = fields.Integer(allow_none=True, metadata={"description": "组织ID"})
    username = fields.String(allow_none=True, metadata={"description": "用户名"})
    engineer_name = fields.String(allow_none=True, metadata={"description": "工程师姓名"})
    is_active = fields.Boolean(allow_none=True, metadata={"description": "是否激活"})
    is_staff = fields.Boolean(allow_none=True, metadata={"description": "是否员工"})
    is_tenant_admin = fields.Boolean(allow_none=True, metadata={"description": "是否租户管理员"})
    is_superuser = fields.Boolean(allow_none=True, metadata={"description": "是否超级管理员"})
    roles__name = fields.String(allow_none=True, metadata={"description": "角色名称"})


class RoleSchema(BaseSchema):
    """角色信息"""
    id = fields.Integer(dump_only=True, metadata={"description": "角色ID"})
    company_id = fields.Integer(allow_none=True, metadata={"description": "所属公司ID"})
    name = fields.String(allow_none=True, metadata={"description": "角色名称"})
    code = fields.String(allow_none=True, metadata={"description": "角色代码"})
    description = fields.String(allow_none=True, metadata={"description": "角色描述"})
    is_active = fields.Boolean(allow_none=True, metadata={"description": "是否激活"})
    permission_codes = fields.List(fields.String(), allow_none=True, metadata={"description": "权限编码列表"})


class RoleListSchema(PaginationBaseSchema):
    """角色列表信息"""
    name = fields.String(allow_none=True, metadata={"description": "角色名称"})
