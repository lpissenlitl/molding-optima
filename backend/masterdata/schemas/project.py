"""
项目相关 Schema 定义 - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Optional
from datetime import datetime, date
from pydantic import Field

from extensions.schemas import BaseSchema, PaginationBaseSchema


class ProjectSchema(BaseSchema):
    """项目信息 Schema —— 与 Project 模型完全对齐"""
    
    # --- 核心标识 ---
    project_code: Optional[str] = Field(None, description="项目编号")
    project_name: Optional[str] = Field(None, description="项目名称")
    # --- 发起方信息 ---
    initiator: Optional[str] = Field(None, description="发起方、客户名称等")
    initiation_reference: Optional[str] = Field(None, description="发起依据、订单编号等")
    manufacturing_location: Optional[str] = Field(None, description="量产地")
    application_industry: Optional[str] = Field(None, description="应用行业")
    manufacturing_method: Optional[str] = Field(None, description="制作方式：委外、自制")
    # --- 项目分类与评级 ---
    is_premium: Optional[bool] = Field(None, description="是否高端项目")
    importance_level: Optional[str] = Field(None, description="重要程度")
    # --- 项目组成员（含执行接口人）---
    project_manager: Optional[str] = Field(None, description="项目经理")
    sales_manager: Optional[str] = Field(None, description="市场经理")
    project_engineer: Optional[str] = Field(None, description="项目组长")
    technical_manager: Optional[str] = Field(None, description="技术经理")
    design_leader: Optional[str] = Field(None, description="设计师")
    process_engineer: Optional[str] = Field(None, description="工艺工程师")
    fitter: Optional[str] = Field(None, description="钳工负责人")
    # --- 合同与计划节点 ---
    contract_date: Optional[date] = Field(None, description="合同日期")
    contract_t1_date: Optional[date] = Field(None, description="合同T1日期")
    contract_factory_delivery_date: Optional[date] = Field(None, description="合同出厂日期")
    standard_trial_count: Optional[int] = Field(None, description="标准试模次数")
    target_new_cycle_days: Optional[int] = Field(None, description="目标新制周期（天）")
    target_rework_cycle_days: Optional[int] = Field(None, description="目标整改周期（天）")
    # --- 试模相关 ---
    trial_plan_start_date: Optional[date] = Field(None, description="试模计划开始日期")
    trial_plan_end_date: Optional[date] = Field(None, description="试模计划结束日期")
    # --- 实际发生时间 ---
    project_kickoff_date: Optional[date] = Field(None, description="项目启动日期")
    work_start_date: Optional[date] = Field(None, description="开工日期")
    financial_settlement_date: Optional[date] = Field(None, description="财务结算日期")
    # --- 状态与协作 ---
    status: Optional[str] = Field(None, description="项目状态")
    review_status: Optional[str] = Field(None, description="评审结果")
    trial_machine: Optional[str] = Field(None, description="试模设备")
    # --- 其他 ---
    remarks: Optional[str] = Field(None, description="备注")
    # --- 系统集成字段 ---
    origin_system: Optional[str] = Field(None, description="来源系统")
    reference_id: Optional[str] = Field(None, description="参考ID")
    sync_status: Optional[str] = Field(None, description="同步状态")
    sync_time: Optional[datetime] = Field(None, description="同步时间")


class ProjectListSchema(PaginationBaseSchema):
    """项目列表"""
    # --- 核心标识 & 业务信息 ---
    project_code: Optional[str] = Field(None, description="项目编号（模糊或精确）")
    project_name: Optional[str] = Field(None, description="项目名称（模糊查询）")
    mold_no: Optional[str] = Field(None, description="模具编号（模糊查询）")
    initiator: Optional[str] = Field(None, description="发起方/客户名称（模糊查询）")
    initiation_reference: Optional[str] = Field(None, description="发起依据/订单号（模糊查询）")
    application_industry: Optional[str] = Field(None, description="应用行业")
    manufacturing_location: Optional[str] = Field(None, description="量产地")
    # --- 状态与分类 ---
    status: Optional[str] = Field(None, description="项目状态")
    review_status: Optional[str] = Field(None, description="评审结果")
    is_premium: Optional[bool] = Field(None, description="是否高端项目")
    importance_level: Optional[str] = Field(None, description="重要程度")
    # --- 人员筛选 ---
    project_manager: Optional[str] = Field(None, description="项目经理（姓名模糊）")
    sales_manager: Optional[str] = Field(None, description="市场经理")
    technical_manager: Optional[str] = Field(None, description="技术经理")