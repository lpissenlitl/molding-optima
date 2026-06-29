"""
公司组织相关 Schema - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Optional, List
from datetime import datetime
from pydantic import Field, ConfigDict

from extensions.schemas import BaseSchema, PaginationBaseSchema, AbstractBaseSchema


class CompanyAdminSchema(AbstractBaseSchema):
    """公司管理员信息"""
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, description="密码")
    confirm_password: Optional[str] = Field(None, description="确认密码")


class CompanySchema(BaseSchema):
    """公司信息"""
    id: Optional[int] = Field(None, description="公司ID")
    name: str = Field(..., description="公司名称")
    code: str = Field(..., description="公司编码")
    is_active: bool = Field(..., description="是否激活")
    industry: Optional[str] = Field(None, description="所属行业")
    description: Optional[str] = Field(None, description="公司描述")
    expires_at: Optional[datetime] = Field(None, description="公司有效期")
    tier_level: Optional[int] = Field(None, description="公司层级")
    
    # --- 公司管理员信息 ---
    admin_user: Optional[CompanyAdminSchema] = Field(None, description="公司管理员信息")

    model_config = ConfigDict(extra="ignore")


class CompanyListSchema(PaginationBaseSchema):
    """公司列表信息"""
    name: Optional[str] = Field(None, description="公司名称")
    industry: Optional[str] = Field(None, description="所属行业")
    is_active: Optional[bool] = Field(None, description="是否激活")


class OrganizationSchema(BaseSchema):
    """组织信息"""
    id: Optional[int] = Field(None, description="组织ID")
    name: str = Field(..., description="组织名称")
    code: Optional[str] = Field(None, description="组织编码")
    manager_id: Optional[int] = Field(None, description="组织负责人ID")
    parent_id: Optional[int] = Field(None, description="父级组织ID")
    org_type: str = Field(..., description="组织类型")
    description: Optional[str] = Field(None, description="组织描述")
    level: Optional[int] = Field(None, description="组织层级")
    path: Optional[str] = Field(None, description="组织路径")
    sort_order: Optional[int] = Field(None, description="排序")
    is_active: Optional[bool] = Field(None, description="是否激活")


class OrganizationBatchUpdateSchema(BaseSchema):
    """批量更新组织信息"""
    
    class UpdateDetailSchema(AbstractBaseSchema):
        """更新详情"""
        id: int = Field(..., description="组织ID")
        parent_id: Optional[int] = Field(None, description="父级组织ID")
        sort_order: Optional[int] = Field(None, description="排序")
        path: Optional[str] = Field(None, description="组织路径")
    
    org_list: List[UpdateDetailSchema] = Field(..., description="组织信息列表")


class OrganizationListSchema(PaginationBaseSchema):
    """组织列表信息"""
    name: Optional[str] = Field(None, description="组织名称")
    org_type: Optional[str] = Field(None, description="组织类型")
    code: Optional[str] = Field(None, description="组织编码")
    level: Optional[int] = Field(None, description="组织层级")


class OrganizationTreeSchema(AbstractBaseSchema):
    """组织树信息"""
    id: int = Field(..., description="组织ID")