"""
molding-optima demo 数据初始化命令

用法：
    python manage.py init_demo
    python manage.py init_demo --reset   # 先软删除现有 demo 数据再重建

前置：
    必须先执行 init_platform 创建 system_demo 公司。

功能（基于 system_demo 公司，创建根组织 + 业务数据）：
    1. 创建 system_demo 根组织（system_demo_HQ）+ demo 业务组织
       （覆盖 department/workshop/team，根组织为 group 类型）
    2. 创建 demo 角色并分配对应的业务权限
    3. 创建 demo 用户（每个角色配一个测试账号）

幂等性：
    - Organization：get_or_create by (company, code)
    - Role：get_or_create by (company, code)
    - RolePermission：双向同步（差异计算 + 应用变更）
    - User：已存在则跳过

设计原则：
    - 所有 demo 数据归属于 system_demo 公司（通过公司上下文隔离，不依赖前缀）
    - 不创建独立根节点，复用 init_platform 创建的根组织（system_demo_HQ）
    - 命名采用业务化命名（"注塑车间"、"班组长"），不加 demo 前缀
    - 用户名加 demo_ 前缀（用户名全局唯一性要求，避免与真实用户冲突）
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from identity.const import SYSTEM_DEMO_COMPANY_CODE, SYSTEM_DEMO_COMPANY_NAME

# 根组织 code（"system_demo_HQ"）和 name（与 company.name 一致）
# 主路径：由 init_platform 创建（公司创建时同步创建根组织）
# 兌底逻辑：init_demo 也保留 get_or_create（防御性，兼容历史数据）
# 设计原则：根组织 name == company.name（语义对齐）
SYSTEM_DEMO_ROOT_ORG_CODE = f"{SYSTEM_DEMO_COMPANY_CODE}_HQ"
SYSTEM_DEMO_ROOT_ORG_NAME = SYSTEM_DEMO_COMPANY_NAME


# ============================================================================
# Demo 组织结构
# 设计：直接挂在 init_platform 创建的根组织（system_demo_HQ）下
#      覆盖 department / workshop / team 等业务 org_type（group 由根组织承载）
# ============================================================================

DEMO_ORG_TREE = [
    {
        "name": "研发中心",
        "code": "rd_center",
        "org_type": "department",
        "children": [
            {"name": "工艺组", "code": "process_team", "org_type": "team"},
        ],
    },
    {
        "name": "生产中心",
        "code": "production_center",
        "org_type": "department",
        "children": [
            {
                "name": "注塑车间",
                "code": "injection_workshop",
                "org_type": "workshop",
                "children": [
                    {"name": "A班", "code": "shift_a", "org_type": "team"},
                    {"name": "B班", "code": "shift_b", "org_type": "team"},
                ],
            },
            {
                "name": "装配车间",
                "code": "assembly_workshop",
                "org_type": "workshop",
            },
        ],
    },
    {
        "name": "品质中心",
        "code": "quality_center",
        "org_type": "department",
        "children": [
            {"name": "质检组", "code": "qc_team", "org_type": "team"},
        ],
    },
    {"name": "销售中心", "code": "sales_center", "org_type": "department"},
    {"name": "采购中心", "code": "purchase_center", "org_type": "department"},
    {"name": "行政中心", "code": "admin_center", "org_type": "department"},
]


# ============================================================================
# Demo 角色
# 设计：覆盖主要业务场景，每个角色对应一类员工
# ============================================================================

DEMO_ROLES = [
    {
        "name": "租户管理员",
        "code": "tenant_admin",
        "description": "完整权限（用于测试所有功能）",
        # 特殊标记：解析为所有 is_active=True 且 tier_level <= 5 的权限
        "permission_strategy": "all_active",
    },
    {
        "name": "工程师",
        "code": "engineer",
        "description": "模具 / 工艺 / 试模相关权限",
        "permission_codes": [
            # 模具管理
            "mold_manage", "mold_list",
            "review_mold", "add_mold", "update_mold", "delete_mold",
            "review_moldflow", "review_trial_resume", "review_problem_resume",
            "project_list", "review_project", "add_project", "update_project",
            # 工艺管理
            "process_manage", "process_list", "process_entry", "process_transplant",
            # 机器 / 材料查看
            "machine_manage", "review_machine", "review_auxiliary",
            "polymer_manage", "review_polymer",
            # 试模查看
            "trial_manage", "trial_dashboard", "trial_list", "operate_record",
            # 库存查看
            "inventory_manage", "review_material", "review_inventory",
            # 排程查看
            "reservation_manage", "reservation_list",
            "review_reservation", "review_schedule",
        ],
    },
    {
        "name": "班组长",
        "code": "team_leader",
        "description": "车间管理 / 排程 / 试模完备审批权限",
        "permission_codes": [
            # 模具查看
            "review_mold", "review_moldflow", "review_trial_resume",
            # 试模管理
            "trial_manage", "trial_dashboard", "trial_plan", "trial_list",
            # 试模完备
            "readiness_list", "readiness_overview",
            "trial_approval", "trial_approval_bz", "trial_approval_xz",
            "mold_inspection", "trial_request",
            "mold_handover", "confirm_readiness_mold",
            # 排程 / 计划
            "reservation_manage", "reservation_list", "reservation_board",
            "review_reservation", "review_schedule",
            "reservation_plan", "confirm_plan", "cancel_plan",
            "submit_assignment", "review_reservation_plan",
            "plan_list", "review_plan",
            # 机器查看
            "review_machine", "review_auxiliary",
        ],
    },
    {
        "name": "质检员",
        "code": "qc",
        "description": "试模报告 / 质检相关权限",
        "permission_codes": [
            # 模具查看
            "review_mold", "review_moldflow", "review_trial_resume",
            # 试模报告
            "trial_manage", "trial_report", "trial_list",
            "check_report", "download_report", "upload_report",
            "trial_approval", "trial_approval_zj",
            # 试模完备
            "readiness_list", "readiness_overview", "confirm_readiness",
            "operate_record",
            # 工艺 / 库存查看
            "process_manage", "process_list",
            "inventory_manage", "review_material", "review_inventory",
        ],
    },
    {
        "name": "销售",
        "code": "sales",
        "description": "销售视角：模具 / 项目 / 约机查看",
        "permission_codes": [
            "mold_manage", "mold_list", "review_mold",
            "project_list", "review_project",
            "reservation_manage", "reservation_board", "reservation_daily",
            "reservation_list", "review_reservation",
            "schedule_list", "review_schedule",
            "trial_manage", "trial_dashboard",
            "inventory_manage", "review_inventory",
        ],
    },
    {
        "name": "采购",
        "code": "purchase",
        "description": "采购视角：物料 / 库存 / 采购管理",
        "permission_codes": [
            "inventory_manage",
            "material_list", "review_material", "add_material", "update_material",
            "inventory_list", "review_inventory", "add_inventory", "update_inventory",
            "matrequisition_list", "review_matrequisition",
            "add_matrequisition", "update_matrequisition",
            "material_purchase", "review_material_purchase", "add_material_purchase",
            "update_material_purchase", "approve_material_purchase",
            "export_material_purchase",
            "confirm_maintained_status", "confirm_received_status",
            "packaging_material_list", "review_packaging_material", "update_packaging_material",
            "polymer_manage", "polymer_list", "review_polymer",
        ],
    },
]


# ============================================================================
# Demo 用户
# 设计：每个角色配一个测试账号，归属到对应业务组织
# 用户名前缀 demo_ 是为了避免与真实用户冲突（用户名全局唯一）
# ============================================================================

DEMO_USERS = [
    {
        "username": "demo_admin",
        "password": "demo123456",
        "engineer_name": "Demo 管理员",
        "email": "demo_admin@example.com",
        "role_code": "tenant_admin",
        "org_code": "hq",
    },
    {
        "username": "demo_engineer",
        "password": "demo123456",
        "engineer_name": "Demo 工程师",
        "email": "demo_engineer@example.com",
        "role_code": "engineer",
        "org_code": "rd_center",
    },
    {
        "username": "demo_leader",
        "password": "demo123456",
        "engineer_name": "Demo 班组长",
        "email": "demo_leader@example.com",
        "role_code": "team_leader",
        "org_code": "injection_workshop",
    },
    {
        "username": "demo_qc",
        "password": "demo123456",
        "engineer_name": "Demo 质检员",
        "email": "demo_qc@example.com",
        "role_code": "qc",
        "org_code": "qc_team",
    },
    {
        "username": "demo_sales",
        "password": "demo123456",
        "engineer_name": "Demo 销售",
        "email": "demo_sales@example.com",
        "role_code": "sales",
        "org_code": "sales_center",
    },
    {
        "username": "demo_purchase",
        "password": "demo123456",
        "engineer_name": "Demo 采购",
        "email": "demo_purchase@example.com",
        "role_code": "purchase",
        "org_code": "purchase_center",
    },
]


class Command(BaseCommand):
    help = "molding-optima demo 数据初始化（基于 system_demo 公司）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="先软删除现有 demo 数据再重建（仅影响 system_demo 公司下的数据）",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("=== molding-optima demo 数据初始化 ===\n")

        company = self._get_demo_company()
        if company is None:
            self.stdout.write(self.style.ERROR(
                f"[错误] 未找到 code={SYSTEM_DEMO_COMPANY_CODE} 的公司，"
                f"请先执行 init_platform 命令初始化平台数据"
            ))
            return

        if options["reset"]:
            self._clean_demo_data(company)

        # 1. 创建组织结构
        org_map = self._create_orgs(company)

        # 2. 创建角色 + 同步权限
        role_map = self._create_roles(company)

        # 3. 创建用户
        self._create_users(company, org_map, role_map)

        self.stdout.write(self.style.SUCCESS("\n[完成] demo 数据初始化完成"))

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _get_demo_company(self):
        """获取 system_demo 公司"""
        from identity.models.company import Company
        try:
            return Company.objects.get(code=SYSTEM_DEMO_COMPANY_CODE)
        except Company.DoesNotExist:
            return None

    def _clean_demo_data(self, company):
        """清理已有的 demo 数据（软删除）

        仅清理 system_demo 公司下的数据，避免影响其他租户：
        - demo_ 开头的用户
        - 除 guest 外的所有 system_demo 角色
        - 除 group 外的所有 system_demo 组织（保留根节点）
        """
        from identity.models.user import User, Role
        from identity.models.company import Organization

        self.stdout.write(self.style.WARNING(
            "\n[清理] 软删除 system_demo 下的现有 demo 数据..."
        ))

        deleted_user_count = User.objects.filter(
            company=company,
            username__startswith="demo_",
            is_deleted=False,
        ).update(is_deleted=True, is_active=False)
        self.stdout.write(f"  - 删除 demo 用户: {deleted_user_count}")

        deleted_role_count = Role.objects.filter(
            company=company,
            is_deleted=False,
        ).exclude(code="guest").update(is_deleted=True)
        self.stdout.write(f"  - 删除 demo 角色: {deleted_role_count}")

        # 仅保留 init_platform 创建的根组织（system_demo_HQ），
        # 历史 init_demo 旧版可能创建的 hq 节点也会被清理
        deleted_org_count = Organization.objects.filter(
            company=company,
            is_deleted=False,
        ).exclude(code=SYSTEM_DEMO_ROOT_ORG_CODE).update(is_deleted=True)
        self.stdout.write(f"  - 删除组织节点: {deleted_org_count}")

    # ------------------------------------------------------------------
    # 组织创建
    # ------------------------------------------------------------------

    def _create_orgs(self, company):
        """创建组织结构（递归），返回 code → Organization 的映射

        init_demo 兌底创建 system_demo 根组织（system_demo_HQ），
        DEMO_ORG_TREE 的所有节点作为子节点挂载到根组织下。
        """
        from identity.models.company import Organization

        self.stdout.write("\n[1/3] 创建 demo 组织结构（含根组织）...")

        # 兌底创建 system_demo 根组织（init_platform 不创建组织，
        # 由 init_demo 负责）
        root, root_created = Organization.objects.get_or_create(
            company=company,
            code=SYSTEM_DEMO_ROOT_ORG_CODE,
            defaults={
                "name": SYSTEM_DEMO_ROOT_ORG_NAME,
                "org_type": "group",
                "level": 0,
                "path": f"/{SYSTEM_DEMO_ROOT_ORG_CODE}",
                "sort_order": 0,
                "is_active": True,
            }
        )
        if root_created:
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] 创建根组织: {root.name} ({root.code})"
            ))
        else:
            self.stdout.write(
                f"  - 根组织已存在: {root.name} ({root.code}, path={root.path})"
            )

        org_map: dict = {root.code: root}

        # DEMO_ORG_TREE 不含根节点，全部作为根组织的子节点（level=1）
        for org_def in DEMO_ORG_TREE:
            self._create_org_recursive(company, root.id, org_def, org_map, level=1)

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] 组织节点（含根）: {len(org_map)} 个"
        ))
        return org_map

    def _create_org_recursive(self, company, parent_id, org_def, org_map, level):
        from identity.models.company import Organization

        # 计算 path（与 create_organization service 保持一致）
        if parent_id is None:
            path = f"/{org_def['code']}"
        else:
            parent = Organization.objects.get(id=parent_id)
            path = f"{parent.path}/{org_def['code']}"

        # 已存在则跳过创建但保留在 org_map 中（支持 --reset 后的重建）
        existing = Organization.objects.filter(
            company=company,
            code=org_def["code"],
            is_deleted=False,
        ).first()

        if existing:
            org = existing
            status = "-"
        else:
            org = Organization.objects.create(
                company=company,
                code=org_def["code"],
                name=org_def["name"],
                org_type=org_def["org_type"],
                description=org_def.get("description", ""),
                parent_id=parent_id,
                level=level,
                path=path,
                sort_order=1,
                is_active=True,
            )
            status = "[OK]"

        self.stdout.write(
            f"  {status} {org.name} ({org.code}, type={org.org_type})"
        )
        org_map[org.code] = org

        # 递归创建子组织
        for child in org_def.get("children", []):
            self._create_org_recursive(
                company, org.id, child, org_map, level=level + 1
            )

    # ------------------------------------------------------------------
    # 角色创建 + 权限同步
    # ------------------------------------------------------------------

    def _create_roles(self, company):
        """创建 demo 角色，同步权限，返回 code → Role 的映射"""
        from identity.models.user import Role

        self.stdout.write("\n[2/3] 创建 demo 角色 + 同步权限...")
        role_map: dict = {}

        for role_def in DEMO_ROLES:
            existing = Role.objects.filter(
                company=company,
                code=role_def["code"],
                is_deleted=False,
            ).first()

            if existing:
                role = existing
                status = "-"
            else:
                role = Role.objects.create(
                    company=company,
                    code=role_def["code"],
                    name=role_def["name"],
                    description=role_def.get("description", ""),
                    is_active=True,
                )
                status = "[OK]"

            self.stdout.write(f"  {status} {role.name} ({role.code})")
            role_map[role.code] = role

            # 同步权限
            target_codes = self._resolve_permission_codes(role_def)
            self._sync_role_permissions(role, target_codes)

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] 角色: {len(role_map)} 个"
        ))
        return role_map

    def _resolve_permission_codes(self, role_def):
        """根据角色定义解析目标权限码集合"""
        from identity.models.user import Permission

        if role_def.get("permission_strategy") == "all_active":
            # 租户管理员：所有 is_active=True 且 tier_level <= 5 的权限
            return set(
                Permission.objects.filter(
                    is_active=True, tier_level__lte=5
                ).values_list("code", flat=True)
            )

        # 指定权限码集合 + 所有角色必须有的基础权限
        codes = set(role_def.get("permission_codes", []))
        codes.add("system_permission")  # 系统根菜单
        return codes

    def _sync_role_permissions(self, role, target_codes):
        """双向同步角色权限（与 init_platform 游客角色同样的同步逻辑）"""
        from identity.models.user import RolePermission

        existing_codes = set(
            RolePermission.objects.filter(role=role).values_list(
                "permission_code", flat=True
            )
        )

        to_add = target_codes - existing_codes
        to_remove = existing_codes - target_codes

        if to_remove:
            RolePermission.objects.filter(
                role=role, permission_code__in=to_remove
            ).delete()
        if to_add:
            RolePermission.objects.bulk_create([
                RolePermission(role=role, permission_code=code)
                for code in to_add
            ])

        self.stdout.write(
            f"    权限: 总 {len(target_codes)}, 新增 {len(to_add)}, 删除 {len(to_remove)}"
        )

    # ------------------------------------------------------------------
    # 用户创建
    # ------------------------------------------------------------------

    def _create_users(self, company, org_map, role_map):
        """创建 demo 用户"""
        from extensions.encrypt.pwdutils import hash_pwd
        from identity.models.user import User

        self.stdout.write("\n[3/3] 创建 demo 用户...")
        created_count = 0
        skipped_count = 0

        for user_def in DEMO_USERS:
            existing = User.objects.filter(
                username=user_def["username"]
            ).first()
            if existing is not None:
                self.stdout.write(f"  - 已存在: {user_def['username']}")
                skipped_count += 1
                continue

            org = org_map.get(user_def["org_code"])
            role = role_map.get(user_def["role_code"])

            user = User.objects.create(
                username=user_def["username"],
                password=hash_pwd(user_def["password"]),
                engineer_name=user_def["engineer_name"],
                email=user_def.get("email"),
                company=company,
                organization=org,
                is_active=True,
                is_staff=True,
                is_tenant_admin=False,
                is_superuser=False,
            )
            if role:
                user.roles.add(role)

            self.stdout.write(self.style.SUCCESS(
                f"  [OK] 创建: {user.username} "
                f"({user.engineer_name}, role={user_def['role_code']}, "
                f"org={user_def['org_code']})"
            ))
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] 用户: 创建 {created_count}, 跳过 {skipped_count}"
        ))

        # 提示测试账号信息
        if created_count > 0:
            self.stdout.write(self.style.WARNING(
                "\n[提示] demo 账号密码统一为: demo123456\n"
                "     登录后通过【切换身份】进入 system_demo 公司即可测试"
            ))