
from django.db import models, transaction
from extensions.models import BaseModel
from datetime import datetime
from django.core.validators import RegexValidator
from utils.tenant import generate_tenant_slug
from utils.identifier import auto_code_from_name, COMPANY_SUFFIXES, ORGANIZATION_SUFFIXES


class Company(BaseModel):
    """公司表"""
    name = models.CharField(max_length=255, verbose_name="公司名称")
    code = models.CharField(
        null=True, blank=True, max_length=30,
        unique=True,
        help_text="业务代号（默认基于名称自动生成，可手动调整）",
        verbose_name="公司代号",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    industry = models.CharField(max_length=255, null=True, verbose_name="所属行业")
    description = models.CharField(max_length=512, null=True, verbose_name="公司描述")
    expires_at = models.DateTimeField(null=True, verbose_name="公司有效期")
    tier_level = models.IntegerField(default=1, verbose_name="公司层级")
    tenant_slug = models.CharField(
        max_length=32,
        unique=True,
        default=generate_tenant_slug,
        help_text="租户唯一标识，用于文件存储隔离和外部引用"
    )

    def is_accessible(self) -> bool:
        """判断公司是否处于可访问状态"""
        return self.is_active \
            and (self.expires_at is None or self.expires_at > datetime.now())

    def save(self, *args, **kwargs):
        """保存前自动生成 code（如果未提供）"""
        if not self.code and self.name:
            self.code = auto_code_from_name(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "公司"
        verbose_name_plural = "公司"


class Organization(BaseModel):
    """组织表"""
    name = models.CharField(max_length=255, verbose_name="组织名称")
    code = models.CharField(
        null=True, blank=True, max_length=30,
        help_text="业务代号（默认基于名称自动生成，可手动调整）",
        verbose_name="组织代号",
    )
    company = models.ForeignKey(
        "identity.Company", 
        on_delete=models.CASCADE,
        verbose_name="所属公司",
        related_name="subordinate_orgs"
    )
    manager = models.ForeignKey(
        "identity.User", 
        on_delete=models.SET_NULL,
        null=True, 
        verbose_name="组织负责人",
        related_name="managed_orgs"
    )
    parent = models.ForeignKey(
        "self", 
        on_delete=models.CASCADE,
        null=True, 
        related_name="children"
    )
    org_type = models.CharField(
        null=True, 
        max_length=50,
        choices=[
            ('group', '集团'),
            ('subsidiary', '子公司'),
            ('division', '事业部'),
            ('department', '部门'),
            ('workshop', '车间'),
            ('section', '工段'),
            ('team', '班组'),
        ],
        verbose_name="组织类型"
    )
    description = models.TextField(null=True, verbose_name="组织描述")
    level = models.IntegerField(null=True, verbose_name="组织层级")
    path = models.CharField(null=True, max_length=255, verbose_name="组织路径")
    sort_order = models.IntegerField(null=True, default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    
    def get_ancestors(self):
        """获取所有上级组织"""
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors[::-1]
    
    def get_descendants(self):
        """获取所有下级组织"""
        return Organization.objects.filter(path__startswith=f"{self.path}/", company=self.company)

    @classmethod
    def get_manager_name_map(cls, org_names: list):
        """
        批量获取组织负责人姓名映射
        
        Args:
            org_names: 组织名称列表
            
        Returns:
            dict: {组织名称: 负责人姓名}，负责人为空时返回 None
        """
        if not org_names:
            return {}
        orgs = cls.objects.filter(name__in=org_names).select_related('manager')
        return {org.name: (org.manager.engineer_name if org.manager else None) for org in orgs}

    def save(self, *args, **kwargs):
        """保存前自动生成 code（如果未提供）

        Organization 使用公司级 + 组织级后缀剥离，提取核心名称
        """
        if not self.code and self.name:
            self.code = auto_code_from_name(
                self.name,
                suffixes=COMPANY_SUFFIXES + ORGANIZATION_SUFFIXES,
            )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "组织"
        verbose_name_plural = "组织"
        unique_together = [('company', 'code')]


class AccessibleOrganization(BaseModel):
    """可访问组织表"""
    user = models.ForeignKey(
        "identity.User", 
        on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        "identity.Organization", 
        on_delete=models.CASCADE
    )
    granted_by = models.ForeignKey(
        "identity.User", 
        on_delete=models.SET_NULL,
        null=True,
        related_name="grants_made"
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True)
    
    class Meta:
        verbose_name = "可访问组织"
        verbose_name_plural = "可访问组织"
        unique_together = [("user", "organization")]