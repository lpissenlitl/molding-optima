from marshmallow import fields
from extensions.schemas import BaseSchema, PaginationBaseSchema


class ProjectSchema(BaseSchema):
    """项目信息 Schema —— 与 Project 模型完全对齐"""

    # --- 核心标识 ---
    project_code = fields.String(allow_none=True, metadata={"description": "项目编号"})
    project_name = fields.String(allow_none=True, metadata={"description": "项目名称"})

    # --- 发起方信息 ---
    initiator = fields.String(allow_none=True, metadata={"description": "发起方、客户名称等"})
    initiation_reference = fields.String(allow_none=True, metadata={"description": "发起依据、订单编号等"})
    manufacturing_location = fields.String(allow_none=True, metadata={"description": "量产地"})
    application_industry = fields.String(allow_none=True, metadata={"description": "应用行业"})
    manufacturing_method = fields.String(allow_none=True, metadata={"description": "制作方式：委外、自制"})

    # --- 项目分类与评级 ---
    is_premium = fields.Boolean(allow_none=True, metadata={"description": "是否高端项目"})
    importance_level = fields.String(allow_none=True, metadata={"description": "重要程度"})

    # --- 项目组成员（含执行接口人）---
    project_manager = fields.String(allow_none=True, metadata={"description": "项目经理"})
    sales_manager = fields.String(allow_none=True, metadata={"description": "市场经理"})
    project_engineer = fields.String(allow_none=True, metadata={"description": "项目组长"})
    technical_manager = fields.String(allow_none=True, metadata={"description": "技术经理"})
    design_leader = fields.String(allow_none=True, metadata={"description": "设计师"})
    process_engineer = fields.String(allow_none=True, metadata={"description": "工艺工程师"})
    fitter = fields.String(allow_none=True, metadata={"description": "钳工负责人"})

    # --- 合同与计划节点 ---
    contract_date = fields.Date(allow_none=True, metadata={"description": "合同日期"})
    contract_t1_date = fields.Date(allow_none=True, metadata={"description": "合同T1日期"})
    contract_factory_delivery_date = fields.Date(allow_none=True, metadata={"description": "合同出厂日期"})
    standard_trial_count = fields.Integer(allow_none=True, metadata={"description": "标准试模次数"})
    target_new_cycle_days = fields.Integer(allow_none=True, metadata={"description": "目标新制周期（天）"})
    target_rework_cycle_days = fields.Integer(allow_none=True, metadata={"description": "目标整改周期（天）"})

    # --- 试模相关 ---
    trial_plan_start_date = fields.Date(allow_none=True, metadata={"description": "试模计划开始日期"})
    trial_plan_end_date = fields.Date(allow_none=True, metadata={"description": "试模计划结束日期"})
    # next_trial_stage = fields.Integer(allow_none=True, metadata={"description": "下一试模阶段"})
    # next_trial_iteration = fields.Integer(allow_none=True, metadata={"description": "下一试模迭代"})
    # is_dry_run_completed = fields.Boolean(allow_none=True, metadata={"description": "是否完成空运行"})
    
    # --- 实际发生时间 ---
    project_kickoff_date = fields.Date(allow_none=True, metadata={"description": "项目启动日期"})
    work_start_date = fields.Date(allow_none=True, metadata={"description": "开工日期"})
    financial_settlement_date = fields.Date(allow_none=True, metadata={"description": "财务结算日期"})

    # --- 状态与协作 ---
    status = fields.String(allow_none=True, metadata={"description": "项目状态"})
    review_status = fields.String(allow_none=True, metadata={"description": "评审结果"})
    trial_machine = fields.String(allow_none=True, metadata={"description": "试模设备"})

    # --- 其他 ---
    remarks = fields.String(allow_none=True, metadata={"description": "备注"})

    # --- 系统集成字段 ---
    origin_system = fields.String(allow_none=True, metadata={"description": "来源系统"})
    reference_id = fields.String(allow_none=True, metadata={"description": "参考ID"})
    sync_status = fields.String(allow_none=True, metadata={"description": "同步状态"})
    sync_time = fields.DateTime(allow_none=True, metadata={"description": "同步时间"})


class ProjectListSchema(PaginationBaseSchema):
    """项目列表"""
    # --- 核心标识 & 业务信息 ---
    project_code = fields.String(allow_none=True, metadata={"description": "项目编号（模糊或精确）"})
    project_name = fields.String(allow_none=True, metadata={"description": "项目名称（模糊查询）"})
    mold_no = fields.String(allow_none=True, metadata={"description": "模具编号（模糊查询）"})
    initiator = fields.String(allow_none=True, metadata={"description": "发起方/客户名称（模糊查询）"})
    initiation_reference = fields.String(allow_none=True, metadata={"description": "发起依据/订单号（模糊查询）"})
    application_industry = fields.String(allow_none=True, metadata={"description": "应用行业"})
    manufacturing_location = fields.String(allow_none=True, metadata={"description": "量产地"})

    # --- 状态与分类 ---
    status = fields.String(allow_none=True, metadata={"description": "项目状态"})
    review_status = fields.String(allow_none=True, metadata={"description": "评审结果"})
    is_premium = fields.Boolean(allow_none=True, metadata={"description": "是否高端项目"})
    importance_level = fields.String(allow_none=True, metadata={"description": "重要程度"})

    # --- 人员筛选 ---
    project_manager = fields.String(allow_none=True, metadata={"description": "项目经理（姓名模糊）"})
    sales_manager = fields.String(allow_none=True, metadata={"description": "市场经理"})
    technical_manager = fields.String(allow_none=True, metadata={"description": "技术经理"})
