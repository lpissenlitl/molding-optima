"""
用户相关 Schema - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Optional, List
from datetime import datetime
from pydantic import Field, ConfigDict

from extensions.schemas import BaseSchema, PaginationBaseSchema


class RegisterSchema(BaseSchema):
    """用户注册信息"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginSchema(BaseSchema):
    """用户登录信息"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    ua: str = Field(..., description="用户代理")


class UpdateUserPasswordSchema(BaseSchema):
    """修改用户密码信息"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")


class ResetUserPasswordSchema(BaseSchema):
    """重置用户密码信息"""
    username: Optional[str] = Field(None, description="用户名")
    password: str = Field(..., description="密码")
    code: Optional[str] = Field(None, description="验证码")


class UserSchema(BaseSchema):
    """用户信息"""
    # company_id = fields.Integer(allow_none=True, metadata={"description": "所属公司ID"})
    organization_id: Optional[int] = Field(None, description="所属组织ID")
    id: Optional[int] = Field(None, description="用户ID")
    username: str = Field(..., description="用户名")
    password: Optional[str] = Field(None, description="密码")
    engineer_name: Optional[str] = Field(None, description="工程师姓名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_staff: Optional[bool] = Field(None, description="是否员工")
    is_tenant_admin: Optional[bool] = Field(None, description="是否租户管理员")
    # is_superuser = fields.Boolean(allow_none=True, metadata={"description": "是否超级管理员"})
    login_count: Optional[int] = Field(None, description="登录次数")
    last_login_at: Optional[datetime] = Field(None, description="上次登录时间")
    expires_at: Optional[datetime] = Field(None, description="用户有效期")
    roles: Optional[List[int]] = Field(None, description="角色ID列表")
    extra_accessible_orgs: Optional[List[int]] = Field(None, description="被授权可访问的组织ID列表")

    model_config = ConfigDict(extra="ignore")


class UserListSchema(PaginationBaseSchema):
    """用户列表信息"""
    organization_id: Optional[int] = Field(None, description="组织ID")
    username: Optional[str] = Field(None, description="用户名")
    engineer_name: Optional[str] = Field(None, description="工程师姓名")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_staff: Optional[bool] = Field(None, description="是否员工")
    is_tenant_admin: Optional[bool] = Field(None, description="是否租户管理员")
    is_superuser: Optional[bool] = Field(None, description="是否超级管理员")
    roles__name: Optional[str] = Field(None, description="角色名称")


class RoleSchema(BaseSchema):
    """角色信息"""
    id: Optional[int] = Field(None, description="角色ID")
    name: Optional[str] = Field(None, description="角色名称")
    code: Optional[str] = Field(None, description="角色代码")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    permission_codes: Optional[List[str]] = Field(None, description="权限编码列表")


class RoleListSchema(PaginationBaseSchema):
    """角色列表信息"""
    name: Optional[str] = Field(None, description="角色名称")