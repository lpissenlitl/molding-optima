"""
molding-optima 平台级数据初始化命令

用法：
    python manage.py init_platform

功能：
    1. 同步 const.PERMISSIONS → Permission 表（200+ 条权限）
    2. 创建 system_demo 公司（演示/试用专用，所有游客共享）
    3. 创建游客角色（属于 system_demo，绑定查看类权限）
    4. 创建超级管理员用户（is_superuser=True，平台级用户）

设计原则：
    - 平台级数据 = 系统自带、与租户无关的基础数据
    - 业务角色（tenant_admin / engineer / viewer 等）由租户按需创建
    - is_superuser 是用户属性，不是角色（见 User.get_permissions）
    - demo 公司是多租户的特殊单元，超级管理员可通过接管操作其数据
    - 游客角色 = system_demo 的标准成员角色，仅看不能改
    - 超级管理员不需要 company（平台级用户），需要时可接管任意租户

幂等性：
    - Permission：update_or_create（更新已有 / 创建新增）
    - Company：get_or_create by code（已存在则跳过）
    - Role：get_or_create by (company, code)（已存在则跳过）
    - RolePermission：双向同步（差异计算 + 应用变更）
    - User：已存在则跳过（不覆盖运维已修改的密码）
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from identity.const import SYSTEM_DEMO_COMPANY_CODE, SYSTEM_DEMO_COMPANY_NAME


class Command(BaseCommand):
    help = "molding-optima 平台级数据初始化（权限 + demo 公司 + 游客角色 + 超级管理员）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-demo-company",
            action="store_true",
            help="跳过 system_demo 公司创建（仅同步权限）",
        )
        parser.add_argument(
            "--skip-superuser",
            action="store_true",
            help="跳过超级管理员用户创建",
        )
        parser.add_argument(
            "--superuser-username",
            default="admin",
            help="超级管理员用户名（默认：admin）",
        )
        parser.add_argument(
            "--superuser-password",
            default="admin123",
            help="超级管理员密码（默认：admin123，生产环境必须修改）",
        )
        parser.add_argument(
            "--reset-superuser",
            action="store_true",
            help="强制重置超级管理员密码（覆盖已有密码，用于密码找回场景）",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("=== molding-optima 平台级初始化 ===\n")

        # 1. 同步权限清单
        self._sync_permissions()

        # 2. 创建系统演示公司（可选跳过）
        company = None
        if options["skip_demo_company"]:
            self.stdout.write(self.style.WARNING("\n[跳过] system_demo 公司未创建（--skip-demo-company）"))
        else:
            company = self._create_demo_company()

        # 3. 创建游客角色（需要 company 存在）
        if company is not None:
            self._create_guest_role(company)
        else:
            self.stdout.write(self.style.WARNING("\n[跳过] 游客角色未创建（system_demo 不存在）"))

        # 4. 创建超级管理员用户（可选跳过）
        if options["skip_superuser"]:
            self.stdout.write(self.style.WARNING("\n[跳过] 超级管理员未创建（--skip-superuser）"))
        else:
            self._create_superuser(
                username=options["superuser_username"],
                password=options["superuser_password"],
                reset=options["reset_superuser"],
            )

        self.stdout.write(self.style.SUCCESS("\n[完成] 平台级初始化完成"))

    def _sync_permissions(self):
        """同步 const.PERMISSIONS → Permission 表"""
        from identity.models.user import Permission

        self.stdout.write("[1/2] 同步权限清单...")
        before = Permission.objects.count()
        Permission.sync_permissions()
        after = Permission.objects.count()
        self.stdout.write(self.style.SUCCESS(f"  权限总数: {after}（新增 {after - before} / 更新 {before}）"))

    def _create_demo_company(self):
        """创建 system_demo 公司（游客共享）+ 根组织（公司级属性）

        设计原则：
        - 公司创建 = 同时初始化组织容器（根组织）
        - 根组织是 company 的属性，与 company.name 同步命名
        - init_demo 创建的 children 业务组织挂载到此根组织下
        """
        from identity.models.company import Company, Organization

        self.stdout.write("\n[2/3] 创建系统演示公司 + 根组织...")
        company, created = Company.objects.get_or_create(
            code=SYSTEM_DEMO_COMPANY_CODE,
            defaults={
                "name": SYSTEM_DEMO_COMPANY_NAME,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  [OK] 创建公司: {company.name} (code={company.code})"))
        else:
            self.stdout.write(f"  - 公司已存在: {company.name} (code={company.code})")

        self.stdout.write(self.style.WARNING(
            "  [提示] system_demo 是特殊公司：\n"
            "     - 游客/试用账号归属此公司\n"
            "     - 超级管理员可通过「接管」操作其数据\n"
            "     - 前端应在公司选择列表中过滤掉此公司"
        ))

        # 创建公司根组织（组织容器）
        # 设计原则：公司创建 = 同时初始化根组织（公司级属性，非业务数据）
        # 根组织 name == company.name（保持语义对齐：通过 org_type="group"
        # 表明这是集团/容器，不依赖 name 后缀区分）
        root_org_code = f"{SYSTEM_DEMO_COMPANY_CODE}_HQ"
        root, root_created = Organization.objects.get_or_create(
            company=company,
            code=root_org_code,
            defaults={
                "name": SYSTEM_DEMO_COMPANY_NAME,
                "org_type": "group",
                "level": 0,
                "path": f"/{root_org_code}",
                "sort_order": 0,
                "is_active": True,
            },
        )
        if root_created:
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] 创建根组织: {root.name} ({root.code})"
            ))
        else:
            # 同步 name == company.name（保持公司/根组织语义对齐）
            if root.name != company.name:
                root.name = company.name
                root.save(update_fields=["name", "updated_at"])
                self.stdout.write(
                    self.style.WARNING(
                        f"  [同步] 根组织 name → {root.name}（保持与 company.name 一致）"
                    )
                )
            else:
                self.stdout.write(f"  - 根组织已存在: {root.name} ({root.code})")

        return company

    def _create_guest_role(self, company):
        """创建游客角色（属于 system_demo，绑定查看类权限）

        权限范围：
        - 所有 type='menu' 的权限（业务模块）→ 游客能看见菜单入口
        - 所有 code 以 'review_' 开头的权限 → 游客能查看数据列表
        - 排除 module='admin'（权限/部门/角色/用户管理仅租户管理员和超管可访问）
        - 不绑定 button 类权限（add_/update_/delete_/approve_ 等）→ 不能修改数据
        """
        from django.db.models import Q
        from identity.models.user import Role, RolePermission, Permission

        self.stdout.write("\n[3/3] 创建游客角色（属于 system_demo）...")

        role, created = Role.objects.get_or_create(
            company=company,
            code="guest",
            defaults={
                "name": "游客",
                "description": "系统演示公司标准成员（仅查看权限）",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  [OK] 创建角色: {role.name} (code={role.code})"))
        else:
            self.stdout.write(f"  - 角色已存在: {role.name} (code={role.code})")

        # 双向同步游客角色权限：
        # - 新增：const 中存在但游客角色未绑定的权限
        # - 删除：游客角色已绑定但 const 中不再属于游客范围的权限
        # 这样 init_platform 可以幂等地响应 const.PERMISSIONS 的变更
        target_perms = Permission.objects.filter(
            Q(type="menu") | Q(code__startswith="review_"),
            is_active=True,
        ).exclude(module="admin")
        target_codes = set(target_perms.values_list("code", flat=True))

        existing_codes = set(
            RolePermission.objects.filter(role=role).values_list("permission_code", flat=True)
        )

        to_add = target_codes - existing_codes
        to_remove = existing_codes - target_codes

        if to_add:
            RolePermission.objects.bulk_create([
                RolePermission(role=role, permission_code=code)
                for code in to_add
            ])
        if to_remove:
            RolePermission.objects.filter(
                role=role, permission_code__in=to_remove
            ).delete()

        total = len(target_codes)
        self.stdout.write(
            f"  [OK] 权限同步: 总 {total} 条, 新增 {len(to_add)} 条, 删除 {len(to_remove)} 条"
        )
        self.stdout.write(self.style.WARNING(
            "  [提示] 游客权限范围：所有业务菜单 + review_类权限\n"
            "     - 可查看业务数据（mold / reservation / process 等）\n"
            "     - 不可增删改（无 button 权限）\n"
            "     - 不可访问 admin 模块（仅租户管理员和超管可见）"
        ))

    def _create_superuser(self, username: str, password: str, reset: bool = False):
        """创建/重置超级管理员用户（平台级用户）

        设计要点：
        - is_superuser=True：自动拥有所有权限（User.get_permissions 第一行）
        - company=None：平台级用户不属于任何租户
        - is_tenant_admin=False：默认未接管任何租户
        - 不绑定角色：超管不需要角色分配权限

        幂等性：
        - 用户不存在：创建
        - 用户存在 + reset=False：跳过（保护运维可能修改过的密码）
        - 用户存在 + reset=True：仅重置密码，其他字段保持不变
          （接管状态、邮箱等不受影响）
        """
        from extensions.encrypt.pwdutils import hash_pwd
        from identity.models.user import User

        self.stdout.write("\n[4/4] 创建超级管理员用户...")

        existing = User.objects.filter(username=username).first()
        if existing is not None:
            if reset:
                existing.password = hash_pwd(password)
                existing.save(update_fields=["password", "updated_at"])
                self.stdout.write(self.style.SUCCESS(f"  [OK] 重置超级管理员密码: {username}"))
                self.stdout.write(self.style.WARNING(
                    f"  [提示] 新密码: {password}\n"
                    f"     [警告] 所有现有 session 将失效，需要重新登录"
                ))
            else:
                self.stdout.write(f"  - 超级管理员已存在: {username}（如需重置密码加 --reset-superuser）")
            return

        user = User.objects.create(
            username=username,
            password=hash_pwd(password),
            email=f"{username}@example.com",
            company=None,            # 平台级用户不属于任何公司
            organization=None,
            is_active=True,
            is_staff=True,
            is_tenant_admin=False,   # 默认未接管任何租户
            is_superuser=True,       # 自动全权限
        )

        self.stdout.write(self.style.SUCCESS(f"  [OK] 创建超级管理员: {user.username}"))
        self.stdout.write(self.style.WARNING(
            f"  [提示] 账号: {username} / {password}\n"
            f"     [警告] 生产环境请立即修改默认密码！\n"
            f"     可在 admin 后台或通过 User 模型的 set_password() 修改"
        ))
