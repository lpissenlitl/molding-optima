"""
molding-optima 系统初始化命令

用法：
    python manage.py init_data

功能：
    1. 创建默认公司（Default Company）
    2. 创建默认组织（游客）
    3. 创建超级管理员账号（admin / admin123）
    4. 创建基础角色和权限（如未存在）
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from extensions.encrypt.pwdutils import hash_pwd


class Command(BaseCommand):
    help = "molding-optima 系统初始化（公司、组织、管理员、基础角色）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-username",
            default="admin",
            help="超级管理员用户名（默认：admin）",
        )
        parser.add_argument(
            "--admin-password",
            default="admin123",
            help="超级管理员密码（默认：admin123）",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin_username = options["admin_username"]
        admin_password = options["admin_password"]

        self.stdout.write("🚀 开始初始化 molding-optima 系统...")

        company = self._init_company()
        organization = self._init_organization(company)
        self._init_roles()
        self._init_superuser(company, organization, admin_username, admin_password)

        self.stdout.write(self.style.SUCCESS("✅ 系统初始化完成"))
        self.stdout.write(f"   公司: {company.name}")
        self.stdout.write(f"   组织: {organization.name}")
        self.stdout.write(f"   管理员账号: {admin_username} / {admin_password}")
        self.stdout.write(self.style.WARNING("⚠️  生产环境请修改默认密码"))

    def _init_company(self):
        from identity.models.company import Company

        company, created = Company.objects.get_or_create(
            name="Default Company",
            defaults={"is_active": True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ 创建公司: {company.name}"))
        else:
            self.stdout.write(f"  - 公司已存在: {company.name}")
        return company

    def _init_organization(self, company):
        from identity.models.company import Organization

        org, created = Organization.objects.get_or_create(
            name="游客",
            company=company,
            defaults={"is_active": True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ 创建组织: {org.name}"))
        else:
            self.stdout.write(f"  - 组织已存在: {org.name}")
        return org

    def _init_roles(self):
        from identity.models.user import Role

        default_roles = [
            {"code": "super_admin", "name": "超级管理员", "description": "系统超级管理员"},
            {"code": "tenant_admin", "name": "租户管理员", "description": "公司租户管理员"},
            {"code": "engineer", "name": "工艺工程师", "description": "工艺管理"},
            {"code": "viewer", "name": "只读用户", "description": "只读权限"},
        ]
        for role_data in default_roles:
            Role.objects.get_or_create(
                code=role_data["code"],
                defaults={
                    "name": role_data["name"],
                    "description": role_data["description"],
                },
            )
        self.stdout.write(self.style.SUCCESS(f"  ✓ 初始化 {len(default_roles)} 个基础角色"))

    def _init_superuser(self, company, organization, username, password):
        from identity.models.user import User

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"  - 管理员已存在: {username}")
            return

        user = User.objects.create(
            username=username,
            password=hash_pwd(password),
            email=f"{username}@example.com",
            company=company,
            organization=organization,
            is_active=True,
            is_staff=True,
            is_tenant_admin=True,
        )
        self.stdout.write(self.style.SUCCESS(f"  ✓ 创建超级管理员: {user.username}"))