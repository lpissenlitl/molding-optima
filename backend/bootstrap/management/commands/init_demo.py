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


# ============================================================================
# Demo 业务数据（基础数据模块演示）
# 设计：每个模块 3-5 条样本，便于 demo_admin 登录后查看列表
# 编号统一前缀 _demo_ 或 DEMO- 便于识别
# 关联关系：mold.project_id → project.id（先创建 project 再创建 mold）
# 简化原则：只填关键业务字段（必填 + 代表性字段），不全量覆盖
# ============================================================================

# ----------------------------------------------------------------------------
# 辅助装置（auxiliary）—— 6 模块中最简单的一个，作为样板
# ----------------------------------------------------------------------------
DEMO_AUXILIARIES = [
    {
        "equipment_name": "模温机_A1",
        "equipment_type": "模温机",
        "specification": "TM-120",
        "total_count": 3,
        "available_count": 2,
        "remarks": "主要用于模具加热，温度范围 40-120℃",
    },
    {
        "equipment_name": "干燥机_B1",
        "equipment_type": "干燥机",
        "specification": "DH-50",
        "total_count": 2,
        "available_count": 1,
        "remarks": "料斗式干燥机，适用于 PP/ABS 等材料",
    },
    {
        "equipment_name": "色母机_C1",
        "equipment_type": "色母机",
        "specification": "MC-03",
        "total_count": 1,
        "available_count": 1,
        "remarks": "体积式色母添加",
    },
    {
        "equipment_name": "机械手_D1",
        "equipment_type": "取出机械手",
        "specification": "ROBO-100",
        "total_count": 2,
        "available_count": 0,
        "remarks": "三轴伺服机械手，目前全部占用",
    },
]


# ----------------------------------------------------------------------------
# 项目（project）—— mold 依赖项，先创建
# ----------------------------------------------------------------------------
DEMO_PROJECTS = [
    {
        "project_code": "PRJ-DEMO-001",
        "project_name": "汽车仪表盘外壳注塑项目",
        "initiator": "华域汽车系统股份有限公司",
        "initiation_reference": "ORDER-2026-08-A45",
        "application_industry": "汽车内饰件",
        "manufacturing_location": "上海",
        "manufacturing_method": "自制",
        "is_premium": True,
        "importance_level": "高",
        "project_manager": "Demo PM",
        "sales_manager": "Demo Sales",
        "project_engineer": "Demo 工程师",
        "technical_manager": "Demo 技术经理",
        "status": "active",
        "review_status": "approved",
        "standard_trial_count": 3,
        "target_new_cycle_days": 45,
        "target_rework_cycle_days": 15,
        "remarks": "高端项目、生命周期 3 年",
    },
    {
        "project_code": "PRJ-DEMO-002",
        "project_name": "家电外壳注塑项目",
        "initiator": "美的集团股份有限公司",
        "initiation_reference": "ORDER-2026-09-B12",
        "application_industry": "家电",
        "manufacturing_location": "佛山",
        "manufacturing_method": "自制",
        "is_premium": False,
        "importance_level": "中",
        "project_manager": "Demo PM",
        "project_engineer": "Demo 工程师",
        "process_engineer": "Demo 工艺",
        "status": "trial",
        "review_status": "approved",
        "standard_trial_count": 2,
        "target_new_cycle_days": 30,
        "target_rework_cycle_days": 10,
        "remarks": "中批量、年供货 50 万件",
    },
    {
        "project_code": "PRJ-DEMO-003",
        "project_name": "薄壁包装盒注塑项目",
        "initiator": "某包装制品有限公司",
        "initiation_reference": "ORDER-2026-09-C07",
        "application_industry": "包装",
        "manufacturing_location": "义乌",
        "manufacturing_method": "自制",
        "is_premium": False,
        "importance_level": "低",
        "project_manager": "Demo PM",
        "project_engineer": "Demo 工程师",
        "status": "draft",
        "review_status": "pending",
        "standard_trial_count": 2,
        "target_new_cycle_days": 20,
        "target_rework_cycle_days": 7,
        "remarks": "薄壁包装、成型周期 < 5s",
    },
]


def _make_hot_runner_gating(
    shot_no: int,
    total_product_weight: float,
    cavity_count_per_shot: int,
    product_name: str,
    estimated_weight_per_cavity: float,
    max_flow_length: float,
    ave_wall_thickness: float,
    gate_type: str,
    gate_shape: str,
    gate_count: int,
    location: str,
    diameter: float = 1.0,
) -> dict:
    """生成一条热流道浇注系统数据(包含 1 个 cavity + 1 个 gate)。
    Gate 关键尺寸采用圆点形状(diameter)。
    """
    return {
        "runner_type": "热流道",
        "total_product_weight": total_product_weight,
        "hot_runner_supplier": "圣万提",
        "hot_runner_system_type": "针阀式",
        "hot_runner_manifold_zones": 4,
        "hot_runner_nozzle_count": cavity_count_per_shot,
        "has_sequencing_control": False,
        "cavities": [
            {
                # === Cavity 字段（对应 backend/masterdata/models/mold.py::Cavity）===
                "cavity_count_per_shot": cavity_count_per_shot,
                "product_name": product_name,
                "product_code": f"{product_name}-{shot_no:02d}",
                "max_flow_length": max_flow_length,
                "ave_wall_thickness": ave_wall_thickness,
                "min_wall_thickness": ave_wall_thickness * 0.85,
                "max_wall_thickness": ave_wall_thickness * 1.2,
                "estimated_weight_per_cavity": estimated_weight_per_cavity,
                "gates": [
                    {
                        # === Gate 字段（对应 backend/masterdata/models/mold.py::Gate）===
                        "gate_type": gate_type,
                        "gate_shape": gate_shape,
                        "gate_count": gate_count,
                        "location_description": location,
                        "diameter": diameter,  # 圆点形状使用直径
                    }
                ],
            }
        ],
    }


def _make_cold_runner_gating(
    shot_no: int,
    total_product_weight: float,
    runner_weight: float,
    runner_length: float,
    cavity_count_per_shot: int,
    product_name: str,
    estimated_weight_per_cavity: float,
    max_flow_length: float,
    ave_wall_thickness: float,
    gate_type: str,
    gate_shape: str,
    gate_count: int,
    location: str,
    diameter: float = 1.0,
) -> dict:
    """生成一条冷流道浇注系统数据(包含 1 个 cavity + 1 个 gate)。
    Gate 关键尺寸采用圆点形状(diameter)。
    """
    return {
        "runner_type": "冷流道",
        "total_product_weight": total_product_weight,
        "runner_weight": runner_weight,
        "runner_length": runner_length,
        "sprue_bushing_outer_dia": 30.0,
        "sprue_bushing_bore_dia": 6.0,
        "sprue_bushing_radius": 15.0,
        "cavities": [
            {
                # === Cavity 字段（对应 backend/masterdata/models/mold.py::Cavity）===
                "cavity_count_per_shot": cavity_count_per_shot,
                "product_name": product_name,
                "product_code": f"{product_name}-{shot_no:02d}",
                "max_flow_length": max_flow_length,
                "ave_wall_thickness": ave_wall_thickness,
                "min_wall_thickness": ave_wall_thickness * 0.85,
                "max_wall_thickness": ave_wall_thickness * 1.2,
                "estimated_weight_per_cavity": estimated_weight_per_cavity,
                "gates": [
                    {
                        # === Gate 字段（对应 backend/masterdata/models/mold.py::Gate）===
                        "gate_type": gate_type,
                        "gate_shape": gate_shape,
                        "gate_count": gate_count,
                        "location_description": location,
                        "diameter": diameter,  # 圆点形状使用直径
                    }
                ],
            }
        ],
    }


# ----------------------------------------------------------------------------
# 模具（mold）—— 关联 project_id
# 依赖项目：创建 mold 时需传入 project_id（从 DEMO_PROJECTS 查询获取）
# ----------------------------------------------------------------------------
DEMO_MOLDS = [
    {
        # 单射模具演示（仪表盘主体外壳、单色）
        "mold_no": "MOLD-DEMO-001",
        "mold_name": "仪表盘外壳模具",
        "mold_type": "二板式",
        "category": "大型模具",
        "structure": "热流道",
        "cavity_layout": "1+1",
        "cavity_count": 2,
        "shot_count": 1,
        "target_cycle_time": 45.0,
        "recommended_tonnage": 800,
        "product_category": "汽车内饰件",
        "product_subcategory": "仪表盘",
        "product_description": "汽车仪表盘主体外壳，PC+ABS 材料",
        "mold_length": 1200,
        "mold_width": 900,
        "mold_thickness": 850,
        "mold_weight": 4500,
        "min_clamping_force": 800,
        "project_code_ref": "PRJ-DEMO-001",
        "gating_systems": [
            _make_hot_runner_gating(
                shot_no=1,
                total_product_weight=560.0,
                cavity_count_per_shot=2,
                product_name="仪表盘主体外壳-A",
                estimated_weight_per_cavity=280.0,
                max_flow_length=620.0,
                ave_wall_thickness=3.5,
                gate_type="针阀式热浇口",
                gate_shape="圆点",
                gate_count=2,
                location="主板中央",
                diameter=1.2,
            ),
        ],
    },
    {
        # 多射模具演示（双腔/多色/多材料场景，切换射次查看不同浇注系统）
        "mold_no": "MOLD-DEMO-002",
        "mold_name": "家电外壳模具",
        "mold_type": "三板式",
        "category": "中型模具",
        "structure": "冷流道",
        "cavity_layout": "2+2",
        "cavity_count": 4,
        "shot_count": 2,
        "target_cycle_time": 25.0,
        "recommended_tonnage": 280,
        "product_category": "家电",
        "product_subcategory": "洗衣机面板",
        "product_description": "洗衣机控制面板，ABS 材料",
        "mold_length": 700,
        "mold_width": 500,
        "mold_thickness": 450,
        "mold_weight": 1800,
        "min_clamping_force": 280,
        "project_code_ref": "PRJ-DEMO-002",
        "gating_systems": [
            _make_cold_runner_gating(
                shot_no=1,
                total_product_weight=320.0,
                runner_weight=35.0,
                runner_length=120.0,
                cavity_count_per_shot=4,
                product_name="洗衣机面板-A面",
                estimated_weight_per_cavity=80.0,
                max_flow_length=180.0,
                ave_wall_thickness=2.5,
                gate_type="点浇口",
                gate_shape="圆点",
                gate_count=4,
                location="顶面中心",
                diameter=0.8,
            ),
            _make_cold_runner_gating(
                shot_no=2,
                total_product_weight=320.0,
                runner_weight=35.0,
                runner_length=120.0,
                cavity_count_per_shot=4,
                product_name="洗衣机面板-B面",
                estimated_weight_per_cavity=80.0,
                max_flow_length=180.0,
                ave_wall_thickness=2.5,
                gate_type="点浇口",
                gate_shape="圆点",
                gate_count=4,
                location="顶面中心",
                diameter=0.8,
            ),
        ],
    },
    {
        # 单射模具演示（薄壁包装）
        "mold_no": "MOLD-DEMO-003",
        "mold_name": "薄壁包装盒模具",
        "mold_type": "三板式",
        "category": "小型模具",
        "structure": "热流道",
        "cavity_layout": "8+8",
        "cavity_count": 16,
        "shot_count": 1,
        "target_cycle_time": 4.5,
        "recommended_tonnage": 160,
        "product_category": "包装",
        "product_subcategory": "一次性饭盒",
        "product_description": "薄壁饭盒盖，PP 材料，壁厚 0.4mm",
        "mold_length": 450,
        "mold_width": 350,
        "mold_thickness": 280,
        "mold_weight": 800,
        "min_clamping_force": 160,
        "project_code_ref": "PRJ-DEMO-003",
        "gating_systems": [
            _make_hot_runner_gating(
                shot_no=1,
                total_product_weight=128.0,
                cavity_count_per_shot=16,
                product_name="薄壁饭盒盖",
                estimated_weight_per_cavity=8.0,
                max_flow_length=80.0,
                ave_wall_thickness=0.4,
                gate_type="热针点浇口",
                gate_shape="圆点",
                gate_count=16,
                location="顶面中心",
                diameter=0.5,
            ),
        ],
    },
]


# ----------------------------------------------------------------------------
# 聚合物（polymer）—— 简化版（不展开嵌套 rheology/pvt/mechanical/shrinkage）
# ----------------------------------------------------------------------------
DEMO_POLYMERS = [
    {
        "abbreviation": "PP",
        "grade": "PP-H040",
        "manufacturer": "中石化",
        "category": "结晶型",
        "series": "均聚聚丙烯",
        "data_source": "供应商",
        "data_status": "正常",
        "internal_id": "PP-H040-CN",
        "level_code": "食品级",
        "vendor_code": "ZSH-PP-001",
        # 密度
        "melt_density": 0.74,
        "solid_density": 0.91,
        # 熔体温度
        "min_melt_temp": 200,
        "max_melt_temp": 280,
        "recommended_melt_temp": 230,
        # 模具温度
        "min_mold_temp": 20,
        "max_mold_temp": 80,
        "recommended_mold_temp": 40,
        # 剪切线速度
        "min_shear_line_speed": 50.0,
        "max_shear_line_speed": 200.0,
        "recommended_shear_line_speed": 100.0,
        # 临界参数
        "degradation_temp": 320,
        "ejection_temp": 110,
        "barrel_residence_time": 10.0,
        "max_shear_rate": 10000.0,
        "max_shear_stress": 0.3,
        # 推荐参数
        "recommend_injection_rate": 30.0,
        "recommend_back_pressure": 5.0,
        # 干燥工艺
        "drying_method": "热风干燥",
        "drying_temp_min": 80,
        "drying_temp_max": 100,
        "drying_time_min": 60,
        "drying_time_max": 120,
    },
    {
        "abbreviation": "ABS",
        "grade": "ABS-0215",
        "manufacturer": "中石油",
        "category": "无定形",
        "series": "高光泽",
        "data_source": "客户",
        "data_status": "正常",
        "internal_id": "ABS-0215-CN",
        "level_code": "通用级",
        "vendor_code": "ZSY-ABS-002",
        "melt_density": 0.95,
        "solid_density": 1.04,
        "min_melt_temp": 210,
        "max_melt_temp": 270,
        "recommended_melt_temp": 240,
        "min_mold_temp": 40,
        "max_mold_temp": 80,
        "recommended_mold_temp": 60,
        "min_shear_line_speed": 40.0,
        "max_shear_line_speed": 160.0,
        "recommended_shear_line_speed": 80.0,
        "degradation_temp": 290,
        "ejection_temp": 95,
        "barrel_residence_time": 8.0,
        "max_shear_rate": 8000.0,
        "max_shear_stress": 0.25,
        "recommend_injection_rate": 25.0,
        "recommend_back_pressure": 4.0,
        "drying_method": "热风干燥",
        "drying_temp_min": 80,
        "drying_temp_max": 90,
        "drying_time_min": 120,
        "drying_time_max": 240,
    },
    {
        "abbreviation": "PA6",
        "grade": "PA6-GF30",
        "manufacturer": "杜邦",
        "category": "结晶型",
        "series": "玻纤增强",
        "data_source": "供应商",
        "data_status": "正常",
        "internal_id": "PA6-GF30-DUP",
        "level_code": "工程级",
        "vendor_code": "DUP-PA6-003",
        "melt_density": 1.15,
        "solid_density": 1.36,
        "min_melt_temp": 250,
        "max_melt_temp": 290,
        "recommended_melt_temp": 270,
        "min_mold_temp": 70,
        "max_mold_temp": 120,
        "recommended_mold_temp": 90,
        "min_shear_line_speed": 30.0,
        "max_shear_line_speed": 120.0,
        "recommended_shear_line_speed": 60.0,
        "degradation_temp": 310,
        "ejection_temp": 180,
        "barrel_residence_time": 6.0,
        "max_shear_rate": 6000.0,
        "max_shear_stress": 0.4,
        "recommend_injection_rate": 20.0,
        "recommend_back_pressure": 6.0,
        "drying_method": "真空干燥",
        "drying_temp_min": 100,
        "drying_temp_max": 120,
        "drying_time_min": 240,
        "drying_time_max": 480,
    },
]


# ----------------------------------------------------------------------------
# 填充物（filler）
# ----------------------------------------------------------------------------
DEMO_FILLERS = [
    {
        "name": "玻璃纤维",
        "abbreviation": "GF",
        "category": "无机填充",
        "shape": "fibrous",
        "particle_size_d50": 10.0,
        "aspect_ratio": 200.0,
        "moisture_content": 0.05,
        "surface_treatment": "硅烷偶联剂处理",
        "density": 2.55,
        "thermal_stability_temp": 300,
        "color": "白色",
    },
    {
        "name": "滑石粉",
        "abbreviation": "TALC",
        "category": "无机填充",
        "shape": "platelet",
        "particle_size_d50": 5.0,
        "aspect_ratio": 1.0,
        "moisture_content": 0.3,
        "surface_treatment": "硬脂酸处理",
        "density": 2.78,
        "thermal_stability_temp": 400,
        "color": "白色",
    },
    {
        "name": "碳酸钙",
        "abbreviation": "CaCO3",
        "category": "无机填充",
        "shape": "irregular",
        "particle_size_d50": 3.0,
        "aspect_ratio": 1.0,
        "moisture_content": 0.1,
        "surface_treatment": "钛酸酯偶联剂处理",
        "density": 2.7,
        "thermal_stability_temp": 600,
        "color": "白色",
    },
]


# ----------------------------------------------------------------------------
# 注塑机（injection_molding_machine）—— 简化版（不展开嵌套 injection_units）
# ----------------------------------------------------------------------------
DEMO_INJECTION_MACHINES = [
    {
        "device_no": "IMM-DEMO-001",
        "asset_no": "A01-IMM-160",
        "brand": "海天",
        "model": "MA1600/540",
        "manufacturer": "宁波海天塑机集团有限公司",
        "location": "注塑车间-A班",
        "status": "idle",
        "machine_type": "液压注塑机",
        "drive_system": "全液压驱动",
        "unit_count": 1,
        # 控制器
        "controller_model": "KEBA",
        "controller_version": "KEBA KeMotion 1175",
        # 通讯能力
        "is_comm_enabled": True,
        "communication_protocol": "custom",  # Euromap 63 不在 enum，用 custom
        "communication_ip": "192.168.10.101",
        # 默认单位（与后端默认值保持一致）
        "pressure_unit": "bar",
        "speed_unit": "mm/s",
        "position_unit": "mm",
        "time_unit": "s",
        "back_pressure_unit": "bar",
        "screw_rotation_unit": "rpm",
        "temperature_unit": "℃",
        "clamping_force_unit": "ton",
        # 定模板/动模板参数
        "fixed_platen_width": 1100.0,
        "fixed_platen_height": 1100.0,
        "fixed_platen_thickness": 250.0,
        "locating_hole_diameter": 100.0,
        "moving_platen_width": 1100.0,
        "moving_platen_height": 1100.0,
        "moving_platen_thickness": 250.0,
        # 拉杆
        "tie_bar_spacing_width": 760.0,
        "tie_bar_spacing_height": 760.0,
        "tie_bar_diameter": 140.0,
        "tie_bar_count": 4,
        # 模板间距
        "min_platen_spacing": 350.0,
        "max_platen_spacing": 1300.0,
        # 容模参数
        "min_mold_length": 450.0,
        "max_mold_length": 1100.0,
        "min_mold_width": 450.0,
        "max_mold_width": 1100.0,
        "min_mold_thickness": 250.0,
        "max_mold_thickness": 800.0,
        "max_opening_stroke": 950.0,
        # 锁模
        "clamping_type": "hydraulic_toggle",  # 海天 MA 系列传统为肘杆式
        "max_clamping_force": 160.0,
        # 顶出
        "ejection_type": "hydraulic_rear",  # enum: hydraulic_rear/hydraulic_front/mechanical/servo
        "ejection_mode": "double_side_symmetric",  # enum: single_center/four_corner_symmetric/none
        "ejection_stroke": 180.0,
        "ejection_force": 80.0,
        # 尺寸与功率
        "size_length": 6500.0,
        "size_width": 1800.0,
        "size_height": 2200.0,
        "machine_weight": 12000.0,
        "motor_power": 75.0,
        "heater_power": 30.0,
        "rated_power": 75.0,
    },
    {
        "device_no": "IMM-DEMO-002",
        "asset_no": "A02-IMM-200",
        "brand": "长飞亚",
        "model": "Zeres 200T",
        "manufacturer": "宁波海天塑机集团有限公司",
        "location": "注塑车间-B班",
        "status": "idle",
        "machine_type": "全电动注塑机",
        "drive_system": "全电动驱动",
        "unit_count": 1,
        "controller_model": "KEBA",
        "controller_version": "KEBA KeMotion 2800",
        "is_comm_enabled": True,
        "communication_protocol": "opc_ua",
        "communication_ip": "192.168.10.102",
        "pressure_unit": "bar",
        "speed_unit": "mm/s",
        "position_unit": "mm",
        "time_unit": "s",
        "back_pressure_unit": "bar",
        "screw_rotation_unit": "rpm",
        "temperature_unit": "℃",
        "clamping_force_unit": "ton",
        "fixed_platen_width": 1200.0,
        "fixed_platen_height": 1200.0,
        "fixed_platen_thickness": 280.0,
        "locating_hole_diameter": 100.0,
        "moving_platen_width": 1200.0,
        "moving_platen_height": 1200.0,
        "moving_platen_thickness": 280.0,
        "tie_bar_spacing_width": 820.0,
        "tie_bar_spacing_height": 820.0,
        "tie_bar_diameter": 150.0,
        "tie_bar_count": 4,
        "min_platen_spacing": 380.0,
        "max_platen_spacing": 1450.0,
        "min_mold_length": 500.0,
        "max_mold_length": 1250.0,
        "min_mold_width": 500.0,
        "max_mold_width": 1250.0,
        "min_mold_thickness": 280.0,
        "max_mold_thickness": 900.0,
        "max_opening_stroke": 1100.0,
        "clamping_type": "servo",  # 全电动 → 伺服锁模
        "max_clamping_force": 200.0,
        "ejection_type": "servo",  # 伺服电动顶出 → enum 是 servo
        "ejection_mode": "four_corner_symmetric",
        "ejection_stroke": 200.0,
        "ejection_force": 100.0,
        "size_length": 7000.0,
        "size_width": 1900.0,
        "size_height": 2300.0,
        "machine_weight": 14000.0,
        "motor_power": 65.0,
        "heater_power": 28.0,
        "rated_power": 65.0,
    },
    {
        "device_no": "IMM-DEMO-003",
        "asset_no": "A03-IMM-200-D",
        "brand": "伊之密",
        "model": "UN200A",
        "manufacturer": "伊之密股份有限公司",
        "location": "注塑车间-A班",
        "status": "idle",
        "machine_type": "液压注塑机",
        "drive_system": "全液压驱动",
        "unit_count": 2,  # 多射台
        "controller_model": "伊之密专用控制器",
        "controller_version": "伊之密 YZM-V3",
        "is_comm_enabled": False,
        "communication_protocol": "none",  # 无通讯
        "pressure_unit": "bar",
        "speed_unit": "mm/s",
        "position_unit": "mm",
        "time_unit": "s",
        "back_pressure_unit": "bar",
        "screw_rotation_unit": "rpm",
        "temperature_unit": "℃",
        "clamping_force_unit": "ton",
        "fixed_platen_width": 1200.0,
        "fixed_platen_height": 1200.0,
        "fixed_platen_thickness": 280.0,
        "locating_hole_diameter": 100.0,
        "moving_platen_width": 1200.0,
        "moving_platen_height": 1200.0,
        "moving_platen_thickness": 280.0,
        "tie_bar_spacing_width": 820.0,
        "tie_bar_spacing_height": 820.0,
        "tie_bar_diameter": 150.0,
        "tie_bar_count": 4,
        "min_platen_spacing": 380.0,
        "max_platen_spacing": 1400.0,
        "min_mold_length": 500.0,
        "max_mold_length": 1200.0,
        "min_mold_width": 500.0,
        "max_mold_width": 1200.0,
        "min_mold_thickness": 280.0,
        "max_mold_thickness": 850.0,
        "max_opening_stroke": 1050.0,
        "clamping_type": "hydraulic_toggle",
        "max_clamping_force": 200.0,
        "ejection_type": "hydraulic_rear",
        "ejection_mode": "double_side_symmetric",
        "ejection_stroke": 200.0,
        "ejection_force": 100.0,
        "size_length": 6800.0,
        "size_width": 1850.0,
        "size_height": 2250.0,
        "machine_weight": 13000.0,
        "motor_power": 80.0,
        "heater_power": 32.0,
        "rated_power": 80.0,
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

        # 4. 创建基础业务数据（项目/模具/材料/机器/辅机）
        self._create_demo_business_data(company)

        self.stdout.write(self.style.SUCCESS("\n[完成] demo 数据初始化完成"))

    # ------------------------------------------------------------------
    # 业务数据创建（基础数据模块演示）
    # 设计原则：
    # - 幂等：依据业务唯一字段（如 equipment_name）查重，重复跳过
    # - 容忍错误：单条创建失败不影响整体
    # - 简化字段：只填必填+代表性字段，不补齐全部 schema
    # ------------------------------------------------------------------

    def _create_demo_business_data(self, company):
        """创建 6 个基础数据模块的 demo 样本数据

        执行顺序：
        - project 最先创建（mold 依赖 project_id）
        - mold 后于 project 创建
        - 其他模块（polymer/filler/injection/auxiliary）独立

        幂等性：依据业务唯一字段查重，已存在跳过。
        """
        from masterdata.models import (
            Project, Mold, Polymer, Filler,
            InjectionMoldingMachine, AuxiliaryEquipment,
        )
        from masterdata.services import (
            project_service, mold_service, polymer_service,
            filler_service, injection_service, auxiliary_service,
        )
        from identity.models.company import Organization
        from identity.models.user import User as IdUser

        self.stdout.write("\n[4/4] 创建基础业务数据（项目/模具/材料/机器/辅机）...")

        # 获取根组织 (system_demo_HQ) 和 demo_admin（mold 创建需要）
        root_org_id = Organization.all_objects.filter(
            company=company,
            code=SYSTEM_DEMO_ROOT_ORG_CODE,
        ).values_list('id', flat=True).first()
        demo_admin = IdUser.all_objects.filter(username='demo_admin').first()

        created_total = 0
        skipped_total = 0

        # ---------- 1. 项目 (project) ----------
        self.stdout.write("\n  [1/6] 项目...")
        project_id_map: dict = {}
        for item in DEMO_PROJECTS:
            try:
                existing = Project.objects.filter(
                    company_id=company.id,
                    project_code=item["project_code"],
                    is_deleted=False,
                ).first()
                if existing:
                    project_id_map[item["project_code"]] = existing.id
                    self.stdout.write(f"    - 已存在: {item['project_code']}")
                    skipped_total += 1
                    continue

                result = project_service.create_project(
                    company_id=company.id,
                    organization_id=root_org_id,
                    **item,
                )
                project_id_map[item["project_code"]] = result["id"]
                self.stdout.write(self.style.SUCCESS(f"    [OK] {item['project_code']}"))
                created_total += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"    ! 失败 {item['project_code']}: {e}"
                ))

        # ---------- 2. 模具 (mold) —— 依赖 project ----------
        self.stdout.write("\n  [2/6] 模具...")
        for item in DEMO_MOLDS:
            try:
                existing = Mold.objects.filter(
                    company_id=company.id,
                    mold_no=item["mold_no"],
                    is_deleted=False,
                ).first()
                if existing:
                    self.stdout.write(f"    - 已存在: {item['mold_no']}")
                    skipped_total += 1
                    continue

                # 关联到对应 project_id（如果存在）
                project_code_ref = item.pop("project_code_ref", None)
                if project_code_ref and project_code_ref in project_id_map:
                    item["project_id"] = project_id_map[project_code_ref]

                # mold_service.create_mold 需要 user 参数
                mold_service.create_mold(
                    user=demo_admin,
                    **item,
                )
                self.stdout.write(self.style.SUCCESS(f"    [OK] {item['mold_no']}"))
                created_total += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"    ! 失败 {item['mold_no']}: {e}"
                ))

        # ---------- 3. 聚合物 (polymer) ----------
        self.stdout.write("\n  [3/6] 聚合物...")
        for item in DEMO_POLYMERS:
            try:
                existing = Polymer.objects.filter(
                    company_id=company.id,
                    abbreviation=item["abbreviation"],
                    grade=item["grade"],
                    is_deleted=False,
                ).first()
                if existing:
                    self.stdout.write(f"    - 已存在: {item['abbreviation']} / {item['grade']}")
                    skipped_total += 1
                    continue

                polymer_service.create_polymer(
                    company_id=company.id,
                    organization_id=root_org_id,
                    **item,
                )
                self.stdout.write(self.style.SUCCESS(f"    [OK] {item['abbreviation']} / {item['grade']}"))
                created_total += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"    ! 失败 {item['abbreviation']} / {item['grade']}: {e}"
                ))

        # ---------- 4. 填充物 (filler) ----------
        self.stdout.write("\n  [4/6] 填充物...")
        for item in DEMO_FILLERS:
            try:
                existing = Filler.objects.filter(
                    company_id=company.id,
                    name=item["name"],
                    is_deleted=False,
                ).first()
                if existing:
                    self.stdout.write(f"    - 已存在: {item['name']}")
                    skipped_total += 1
                    continue

                filler_service.create_filler(
                    company_id=company.id,
                    organization_id=root_org_id,
                    **item,
                )
                self.stdout.write(self.style.SUCCESS(f"    [OK] {item['name']}"))
                created_total += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"    ! 失败 {item['name']}: {e}"
                ))

        # ---------- 5. 注塑机 (injection) ----------
        self.stdout.write("\n  [5/6] 注塑机...")
        for item in DEMO_INJECTION_MACHINES:
            try:
                existing = InjectionMoldingMachine.objects.filter(
                    company_id=company.id,
                    device_no=item["device_no"],
                    is_deleted=False,
                ).first()
                if existing:
                    self.stdout.write(f"    - 已存在: {item['device_no']}")
                    skipped_total += 1
                    continue

                injection_service.create_injection_machine(
                    company_id=company.id,
                    organization_id=root_org_id,
                    **item,
                )
                self.stdout.write(self.style.SUCCESS(f"    [OK] {item['device_no']}"))
                created_total += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"    ! 失败 {item['device_no']}: {e}"
                ))

        # ---------- 6. 辅助装置 (auxiliary) ----------
        self.stdout.write("\n  [6/6] 辅助装置...")
        for item in DEMO_AUXILIARIES:
            try:
                existing = AuxiliaryEquipment.objects.filter(
                    company_id=company.id,
                    equipment_name=item["equipment_name"],
                    is_deleted=False,
                ).first()
                if existing:
                    self.stdout.write(f"    - 已存在: {item['equipment_name']}")
                    skipped_total += 1
                    continue

                auxiliary_service.create_auxiliary_equipment(
                    company_id=company.id,
                    organization_id=root_org_id,
                    **item,
                )
                self.stdout.write(self.style.SUCCESS(f"    [OK] {item['equipment_name']}"))
                created_total += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"    ! 失败 {item['equipment_name']}: {e}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\n  [完成] 基础业务数据: 创建 {created_total}, 跳过 {skipped_total}"
        ))

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
        - 6 个基础数据模块的业务数据（project/mold/polymer/filler/injection/auxiliary）

        清理顺序考虑依赖关系：
        - mold 依赖 project（先清子 mold，后清父 project）
        """
        from identity.models.user import User, Role
        from identity.models.company import Organization
        from masterdata.models import (
            Mold, Project, Polymer, Filler,
            InjectionMoldingMachine, AuxiliaryEquipment,
        )

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

        # ---- 基础业务数据（6 个模块）----
        # 顺序：先清依赖项（mold 依赖 project），其他模块独立
        from datetime import datetime
        now = datetime.now()

        # Mold 先清（避免悬挂引用）
        deleted_mold_count = Mold.objects.filter(
            company_id=company.id,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now, deleted_at=now)
        self.stdout.write(f"  - 删除模具: {deleted_mold_count}")

        deleted_project_count = Project.objects.filter(
            company_id=company.id,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now, deleted_at=now)
        self.stdout.write(f"  - 删除项目: {deleted_project_count}")

        deleted_polymer_count = Polymer.objects.filter(
            company_id=company.id,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now, deleted_at=now)
        self.stdout.write(f"  - 删除聚合物: {deleted_polymer_count}")

        deleted_filler_count = Filler.objects.filter(
            company_id=company.id,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now, deleted_at=now)
        self.stdout.write(f"  - 删除填充物: {deleted_filler_count}")

        deleted_imm_count = InjectionMoldingMachine.objects.filter(
            company_id=company.id,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now, deleted_at=now)
        self.stdout.write(f"  - 删除注塑机: {deleted_imm_count}")

        deleted_aux_count = AuxiliaryEquipment.objects.filter(
            company_id=company.id,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now, deleted_at=now)
        self.stdout.write(f"  - 删除辅助装置: {deleted_aux_count}")

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

        # 清理同名软删除记录（init_demo 自身产生的数据，无审计价值）
        # 避免 --reset 后重建同名组织时触发 DB unique 约束冲突
        deleted_same_code = Organization.all_objects.filter(
            company=company,
            code=org_def["code"],
            is_deleted=True,
        )
        if deleted_same_code.exists():
            count = deleted_same_code.count()
            deleted_same_code.delete()
            self.stdout.write(self.style.WARNING(
                f"    [清理] 删除同名软删除组织: {org_def['code']} ({count} 条)"
            ))

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
            # 清理同名软删除记录（init_demo 自身产生的数据）
            deleted_same_code = Role.all_objects.filter(
                company=company,
                code=role_def["code"],
                is_deleted=True,
            )
            if deleted_same_code.exists():
                count = deleted_same_code.count()
                deleted_same_code.delete()
                self.stdout.write(self.style.WARNING(
                    f"    [清理] 删除同名软删除角色: {role_def['code']} ({count} 条)"
                ))

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
            # 清理同名软删除用户（init_demo 自身产生的数据）
            deleted_same_user = User.all_objects.filter(
                username=user_def["username"],
                is_deleted=True,
            )
            if deleted_same_user.exists():
                count = deleted_same_user.count()
                deleted_same_user.delete()
                self.stdout.write(self.style.WARNING(
                    f"    [清理] 删除同名软删除用户: {user_def['username']} ({count} 条)"
                ))

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