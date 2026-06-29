from django.db import models, transaction
from django.db.models import Exists, OuterRef
from django.http import HttpRequest
from extensions.models import AbstractBaseModel, TracedModel, BaseModel
from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT
from utils.validation import validate_permission_codes
from utils.request_utils import get_client_ip
from extensions.encrypt.pwdutils import hash_pwd
from datetime import datetime, timedelta
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)


class User(BaseModel):
    """用户表"""
    company = models.ForeignKey(
        "identity.Company", 
        on_delete=models.CASCADE, 
        null=True, 
        verbose_name="所属公司"
    )
    
    organization = models.ForeignKey(
        "identity.Organization", 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="members",
        verbose_name="所属组织"
    )
    
    username = models.CharField(max_length=50, verbose_name="用户名")
    password = models.CharField(max_length=128, verbose_name="密码")
    engineer_name = models.CharField(null=True, max_length=50, verbose_name="工程师姓名")
    email = models.EmailField(null=True, verbose_name="邮箱")
    phone = models.CharField(null=True, max_length=11, verbose_name="手机")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    is_staff = models.BooleanField(default=True, verbose_name="是否员工")
    is_tenant_admin = models.BooleanField(default=False, verbose_name="是否租户管理员")
    is_superuser = models.BooleanField(default=False, verbose_name="是否超级管理员")
    login_count = models.IntegerField(default=0, verbose_name="登录次数")
    last_login_at = models.DateTimeField(null=True, verbose_name="上次登录时间")
    expires_at = models.DateTimeField(null=True, verbose_name="用户有效期")

    roles = models.ManyToManyField(
        "identity.Role", 
        related_name="belong_users",
        verbose_name="角色"
    )
    
    extra_accessible_orgs = models.ManyToManyField(
        "identity.Organization", 
        through="identity.AccessibleOrganization",
        through_fields=("user", "organization"),
        related_name="extra_authorized_users",
        verbose_name="额外授权的可访问组织信息"
    )
    
    feishu_id =  models.CharField(null=True, max_length=50, verbose_name="飞书用户ID")
    
    def is_accessible(self):
        """判断用户是否可访问"""

        if self.is_superuser:
            return True # 超级管理员用户，拥有所有权限

        if self.company is None:
            return False # 未关联公司，无访问权限
            
        if not self.company.is_accessible():
            return False # 公司不可访问，则用户无权限
        
        if not self.is_active:
            return False # 未激活用户，无访问权限
        
        if self.is_deleted:
            return False # 已删除用户，无访问权限

        if self.expires_at and self.expires_at < datetime.now():
            return False # 已过期用户，无访问权限

        return True
    
    def record_login(self):
        self.login_count += 1
        self.last_login_at = datetime.now()
        self.save(update_fields=["login_count", "last_login_at", "updated_at"])
  
    def get_permissions(self):
        """获取用户权限,用户后端鉴权,能否操作"""
        if self.is_tenant_admin:
            company_tier = getattr(self.company, 'tier_level', None)
            if company_tier is None:
                return []
            return list(Permission.objects.filter(is_active=True,tier_level__lte=self.company.tier_level).values_list("code", flat=True))
        else:
            permissions = set()
            for role in self.roles.all():
                if role.is_active:  
                    permissions.update(role.get_permissions())
            return list(permissions)
    
    def get_accessible_organizations(self):
        """获取用户可访问组织"""
        if self.is_tenant_admin:
            from identity.models import Organization
            return Organization.objects.filter(company_id=self.company_id)
        else:
            root_orgs = self.extra_accessible_orgs.all()
            all_acc_orgs = []
            for root_org in root_orgs:
                all_acc_orgs.append(root_org)
                all_acc_orgs.extend(root_org.get_descendants())
            return all_acc_orgs
    
    def has_permission(self, permission_code: str):
        """判断用户是否拥有指定权限"""
        return permission_code in self.get_permissions()
    
    def deactivate(self):
        """用户注销"""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])
    
    def construct_user_info(self) -> dict:
        """构造用户信息"""
        # 构建脱敏用户信息
        user_info = {
            **self.to_dict(
                exclude=["password", "is_deleted"], 
                include_m2m=True, include_rvs=True
            ),
            "permissions": self.get_permissions()
        }
        
        # 补充公司名称，游客用户显示为"游客"
        company_name = self.company.name if self.company else "游客"
        user_info.update({"company_name": company_name})
        
        # 补充组织名称，游客用户显示为"游客"
        organization_name = self.organization.name if self.organization else "游客"
        user_info.update({"organization_name": organization_name})
    
        return user_info
    
    @classmethod
    def create_superuser(cls, username: str, password: str):
        """创建超级管理员用户"""
        # print(password, hash_pwd(password))
        user = cls.objects.create(
            username=username,
            password=hash_pwd(password),
            engineer_name="超级管理员",
            is_superuser=True,
            is_staff=False,
            is_active=True,
            is_tenant_admin=False,
        )
        return user


    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"


class Role(BaseModel):
    """角色表"""
    company = models.ForeignKey(
        "identity.Company", 
        on_delete=models.CASCADE,
        null=True,
        related_name="roles",
        verbose_name="所属公司"
    )
    name = models.CharField(max_length=50, verbose_name="角色名称")
    code = models.CharField(null=True, max_length=100, verbose_name="角色编码，用于程序识别")
    description = models.CharField(null=True, max_length=255, verbose_name="角色描述")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")

    @transaction.atomic
    def set_permissions(self, permission_codes: list):
        """设置角色权限"""
        # permission_codes 为None或空列表，清空权限
        if permission_codes is None:
            raise BizException(ERROR_ILLEGAL_ARGUMENT, message="权限编码列表不能为空")
        if isinstance(permission_codes, list) and len(permission_codes) == 0:
            if self.permissions.all():
                return self.permissions.clear()
        
        # 获取当前权限 code
        current_codes = set()
        if self.permissions.all():
            current_codes = set(self.permissions.values_list('permission_code', flat=True))

        # 提取并清洗 code
        cleaned_codes = set(validate_permission_codes(permission_codes, "权限编码"))

        # 识别差异
        added_codes = cleaned_codes - current_codes
        removed_codes = current_codes - cleaned_codes
        
        # 先删后增
        if removed_codes: 
            self.permissions.filter(permission_code__in=removed_codes).delete()

        if added_codes: 
            RolePermission.objects.bulk_create([
                RolePermission(role=self, permission_code=code) 
                for code in added_codes
            ])        
        
    def get_permissions(self):
        """返回角色权限 code 列表"""
        valid_permission = Permission.objects.filter(
            code=OuterRef('permission_code'),  # 子查询引用外层RolePermission的permission_code
            is_active=True  # 只找Permission表中启用的权限
        )
        # 2. 用Exists过滤外层的RolePermission，只保留有对应有效Permission的记录
        valid_role_perms = self.permissions.filter(Exists(valid_permission))
        # 3. 提取过滤后的有效权限编码，返回列表
        return [e.permission_code for e in valid_role_perms]
    
    
    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"


class RolePermission(TracedModel):
    """角色权限关系表"""
    role = models.ForeignKey(
        "identity.Role", 
        on_delete=models.CASCADE,
        related_name="permissions",
        verbose_name="角色"
    )
    permission_code = models.CharField(max_length=100, db_index=True, verbose_name="权限代码")

    class Meta:
        verbose_name = "角色权限关系"
        verbose_name_plural = "角色权限关系"
        unique_together = [('role', 'permission_code')]


class Permission(TracedModel):
    """权限表"""

    name = models.CharField(max_length=50, verbose_name="权限名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="权限代码")
    parent_code = models.CharField(null=True, max_length=50, verbose_name="父级权限代码")

    PERMISSION_TYPE_CHOICES = [
        ('menu', '菜单权限'),
        ('button', '按钮/操作权限'),
    ]
    type = models.CharField(default="menu", max_length=20, verbose_name="权限类型")
    module = models.CharField(null=True, max_length=50, verbose_name="关联模块")
    sort_order = models.IntegerField(null=True, default=0, verbose_name="排序")
    tier_level = models.PositiveSmallIntegerField(default=1, verbose_name="权限等级（不同应用等级）")
    description = models.CharField(null=True, max_length=100, verbose_name="权限描述")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    @classmethod
    def sync_permissions(cls):
        
        from identity.const import PERMISSIONS
        
        for perm in PERMISSIONS:
            obj, created = Permission.objects.update_or_create(
                code=perm["code"],
                defaults=perm
            )
            status = "✅ 创建" if created else "🔄 更新"
            logger.info(f'{status}: {perm["name"]} ({perm["code"]})')

    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限" 
        ordering = [ "sort_order" ]


class Token(AbstractBaseModel):
    """用户Token"""
    user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="tokens", verbose_name="用户")
    token = models.CharField(max_length=255, db_index=True, verbose_name="哈希Token")
    ua = models.CharField(max_length=512, default="", verbose_name="用户代理")
    is_revoked = models.BooleanField(default=False, verbose_name="是否撤销")
    ip_address = models.CharField(max_length=45, default="", verbose_name="IP地址")
    expires_at = models.DateTimeField(null=True, verbose_name="过期时间")
    revoked_at = models.DateTimeField(null=True, verbose_name="撤销时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    @classmethod
    def create(cls, user: User, request: HttpRequest, expire_hours=6):
        """生成一个6小时内有效的Token"""
        raw_token = secrets.token_urlsafe(48)
        hash_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now() + timedelta(hours=expire_hours)
        ua = request.META.get("HTTP_USER_AGENT", "")
        ip = get_client_ip(request)
        
        login_token = cls.objects.create(
            user=user,
            token=hash_token,
            ua=ua,
            ip_address=ip,
            expires_at=expires_at,
        )
        
        return raw_token, login_token
        
    
    def flush_token(self):
        if self.expires_at < datetime.now() + timedelta(hours=3):
            self.expires_at = datetime.now() + timedelta(hours=3)
            self.save(update_fields=["expires_at"])


class RedirectToken(TracedModel):
    """跳转令牌"""
    token = models.CharField(max_length=255, unique=True, db_index=True, verbose_name="跳转令牌")
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE, verbose_name="用户")
    target_url = models.TextField(verbose_name="目标地址")
    is_used = models.BooleanField(default=False, verbose_name="是否已使用")
    expires_at = models.DateTimeField(verbose_name="过期时间")

    @classmethod
    def create(cls, user: User, target_url: str, expire_hours=72):
        """生成一个72小时内有效的跳转token"""
        raw_token = secrets.token_urlsafe(48)  # 长度足够安全
        hash_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now() + timedelta(hours=expire_hours)

        redirect_token =  cls.objects.create(
            token=hash_token,
            user=user,
            target_url=target_url,
            expires_at=expires_at
        )

        return raw_token, redirect_token

    def is_valid(self):
        """验证该跳转令牌是否有效"""
        now = datetime.now()
        return not self.is_used and now < self.expires_at
    
    def consume(self):
        """使用并作废该 Token"""
        if self.is_valid():
            self.is_used = True
            self.save()
            return True
        return False