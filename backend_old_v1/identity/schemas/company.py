from marshmallow import fields, Schema, EXCLUDE
from extensions.schemas import BaseSchema, PaginationBaseSchema


class CompanySchema(BaseSchema):
    """公司信息"""
    class CompanyAdminSchema(Schema):
        username = fields.String(allow_none=True, metadata={"description": "用户名"})
        email = fields.String(allow_none=True, metadata={"description": "邮箱"})
        password = fields.String(allow_none=True, metadata={"description": "密码"})
        confirm_password = fields.String(allow_none=True, metadata={"description": "确认密码"})
        
    id = fields.Integer(dump_only=True, metadata={"description": "公司ID"})
    name = fields.String(allow_none=True,required=True, metadata={"description": "公司名称"})
    code = fields.String(allow_none=True,required=True, metadata={"description": "公司编码"})
    is_active = fields.Boolean(allow_none=True,required=True, metadata={"description": "是否激活"})
    industry = fields.String(allow_none=True, metadata={"description": "所属行业"})
    description = fields.String(allow_none=True, metadata={"description": "公司描述"})
    expires_at = fields.DateTime(allow_none=True, metadata={"description": "公司有效期"})
    tier_level = fields.Integer(allow_none=True, metadata={"description": "公司层级"})
    
    # --- 公司管理员信息 ---
    admin_user = fields.Nested(CompanyAdminSchema, allow_none=True, unknown=EXCLUDE, metadata={"description": "公司管理员信息"})
    

class CompanyListSchema(PaginationBaseSchema):
    """公司列表信息"""
    name = fields.String(allow_none=True, metadata={"description": "公司名称"})
    industry = fields.String(allow_none=True, metadata={"description": "所属行业"})
    is_active = fields.Boolean(allow_none=True, metadata={"description": "是否激活"})


class OrganizationSchema(BaseSchema):
    """组织信息"""
    id = fields.Integer(dump_only=True, metadata={"description": "组织ID"})
    name = fields.String(required=True, metadata={"description": "组织名称"})
    code = fields.String(allow_none=True, metadata={"description": "组织编码"})
    manager_id = fields.Integer(allow_none=True, metadata={"description": "组织负责人ID"})
    parent_id = fields.Integer(allow_none=True, metadata={"description": "父级组织ID"})
    org_type = fields.String(required=True, metadata={"description": "组织类型"})
    description = fields.String(allow_none=True, metadata={"description": "组织描述"})
    level = fields.Integer(allow_none=True, metadata={"description": "组织层级"})
    path = fields.String(allow_none=True, metadata={"description": "组织路径"})
    sort_order = fields.Integer(allow_none=True, metadata={"description": "排序"})
    is_active = fields.Boolean(allow_none=True, metadata={"description": "是否激活"})


class OrganizationBatchUpdateSchema(BaseSchema):
    """批量更新组织信息"""
    class UpdateDetail(Schema):
        id = fields.Integer(required=True, metadata={"description": "组织ID"})
        parent_id = fields.Integer(allow_none=True, metadata={"description": "父级组织ID"})
        sort_order = fields.Integer(allow_none=True, metadata={"description": "排序"})
        path = fields.String(allow_none=True, metadata={"description": "组织路径"})
    
    org_list = fields.Nested(UpdateDetail, many=True, metadata={"description": "组织信息列表"})


class OrganizationListSchema(PaginationBaseSchema):
    """组织列表信息"""
    company_id = fields.Integer(allow_none=True, metadata={"description": "公司ID"})
    name = fields.String(allow_none=True, metadata={"description": "组织名称"})
    org_type = fields.String(allow_none=True, metadata={"description": "组织类型"})
    code = fields.String(allow_none=True, metadata={"description": "组织编码"})
    level = fields.Integer(allow_none=True, metadata={"description": "组织层级"})


class OrganizationTreeSchema(Schema):
    """组织树信息"""
    id = fields.Integer(metadata={"description": "组织ID"})
    company_id = fields.Integer(metadata={"description": "公司ID"})