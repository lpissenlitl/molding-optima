"""molding-optima 工艺参数 Schema 定义

字段命名严格匹配 process/models/parameter.py。

对应 Model：ProcessParameter

包含：注射参数（6 段）、VP 切换、保压参数（5 段）、冷却参数、熔胶参数（4 段）、
      松退参数、料筒温度参数（10 段）。
"""
from typing import Optional
from datetime import date

from pydantic import Field

from extensions.schemas import BaseSchema, PaginationBaseSchema


class ProcessParameterSchema(BaseSchema):
    """工艺参数记录"""

    process_condition_id: Optional[int] = Field(None, description="所属工艺条件 ID")

    # --- 基本信息 ---
    param_code: Optional[str] = Field(None, description="工艺参数编号")
    param_source: Optional[str] = Field(None, description="参数来源")
    # 业务编号：前端可见，用于确定调机树中的基准节点
    # 与 process_condition_id 联合定位父节点（反查 parent_param.id）
    # 注意：这是业务编号（condition 内全局递增），不是数据库 ID
    parent_seq_idx: Optional[int] = Field(None, description="父参数业务编号（seq_idx）")
    seq_idx: Optional[int] = Field(None, description="序列序号")

    # --- 注射参数 (6段) ---
    inj_stg: Optional[int] = Field(None, description="注射段数 1-6")

    inj_spd_1: Optional[float] = Field(None, description="一段注射速度")
    inj_spd_2: Optional[float] = Field(None, description="二段注射速度")
    inj_spd_3: Optional[float] = Field(None, description="三段注射速度")
    inj_spd_4: Optional[float] = Field(None, description="四段注射速度")
    inj_spd_5: Optional[float] = Field(None, description="五段注射速度")
    inj_spd_6: Optional[float] = Field(None, description="六段注射速度")

    inj_pres_1: Optional[float] = Field(None, description="一段注射压力")
    inj_pres_2: Optional[float] = Field(None, description="二段注射压力")
    inj_pres_3: Optional[float] = Field(None, description="三段注射压力")
    inj_pres_4: Optional[float] = Field(None, description="四段注射压力")
    inj_pres_5: Optional[float] = Field(None, description="五段注射压力")
    inj_pres_6: Optional[float] = Field(None, description="六段注射压力")

    inj_pos_1: Optional[float] = Field(None, description="一段注射位置")
    inj_pos_2: Optional[float] = Field(None, description="二段注射位置")
    inj_pos_3: Optional[float] = Field(None, description="三段注射位置")
    inj_pos_4: Optional[float] = Field(None, description="四段注射位置")
    inj_pos_5: Optional[float] = Field(None, description="五段注射位置")
    inj_pos_6: Optional[float] = Field(None, description="六段注射位置")

    inj_t: Optional[float] = Field(None, description="注射时间")
    inj_dly_t: Optional[float] = Field(None, description="注射延时")

    # --- VP 切换参数 ---
    vps_mode: Optional[int] = Field(None, description="VP切换模式")
    vps_pos: Optional[float] = Field(None, description="VP切换位置")
    vps_t: Optional[float] = Field(None, description="VP切换时间")
    vps_pres: Optional[float] = Field(None, description="VP切换压力")
    vps_spd: Optional[float] = Field(None, description="VP切换速度")

    # --- 保压参数 (5段) ---
    hold_stg: Optional[int] = Field(None, description="保压段数 1-5")

    hold_pres_1: Optional[float] = Field(None, description="一段保压压力")
    hold_pres_2: Optional[float] = Field(None, description="二段保压压力")
    hold_pres_3: Optional[float] = Field(None, description="三段保压压力")
    hold_pres_4: Optional[float] = Field(None, description="四段保压压力")
    hold_pres_5: Optional[float] = Field(None, description="五段保压压力")

    hold_spd_1: Optional[float] = Field(None, description="一段保压速度")
    hold_spd_2: Optional[float] = Field(None, description="二段保压速度")
    hold_spd_3: Optional[float] = Field(None, description="三段保压速度")
    hold_spd_4: Optional[float] = Field(None, description="四段保压速度")
    hold_spd_5: Optional[float] = Field(None, description="五段保压速度")

    hold_t_1: Optional[float] = Field(None, description="一段保压时间")
    hold_t_2: Optional[float] = Field(None, description="二段保压时间")
    hold_t_3: Optional[float] = Field(None, description="三段保压时间")
    hold_t_4: Optional[float] = Field(None, description="四段保压时间")
    hold_t_5: Optional[float] = Field(None, description="五段保压时间")

    # --- 冷却参数 ---
    cool_t: Optional[float] = Field(None, description="冷却时间")

    # --- 熔胶参数 (4段) ---
    met_stg: Optional[int] = Field(None, description="熔胶段数 1-4")

    met_pres_1: Optional[float] = Field(None, description="一段熔胶压力")
    met_pres_2: Optional[float] = Field(None, description="二段熔胶压力")
    met_pres_3: Optional[float] = Field(None, description="三段熔胶压力")
    met_pres_4: Optional[float] = Field(None, description="四段熔胶压力")

    met_rot_spd_1: Optional[float] = Field(None, description="一段螺杆转速")
    met_rot_spd_2: Optional[float] = Field(None, description="二段螺杆转速")
    met_rot_spd_3: Optional[float] = Field(None, description="三段螺杆转速")
    met_rot_spd_4: Optional[float] = Field(None, description="四段螺杆转速")

    met_back_pres_1: Optional[float] = Field(None, description="一段背压")
    met_back_pres_2: Optional[float] = Field(None, description="二段背压")
    met_back_pres_3: Optional[float] = Field(None, description="三段背压")
    met_back_pres_4: Optional[float] = Field(None, description="四段背压")

    met_pos_1: Optional[float] = Field(None, description="一段熔胶位置")
    met_pos_2: Optional[float] = Field(None, description="二段熔胶位置")
    met_pos_3: Optional[float] = Field(None, description="三段熔胶位置")
    met_pos_4: Optional[float] = Field(None, description="四段熔胶位置")

    # --- 松退参数 ---
    pre_met_decomp_mode: Optional[int] = Field(None, description="熔胶前松退模式")
    pre_met_decomp_pres: Optional[float] = Field(None, description="熔胶前松退压力")
    pre_met_decomp_spd: Optional[float] = Field(None, description="熔胶前松退速度")
    pre_met_decomp_t: Optional[float] = Field(None, description="熔胶前松退时间")
    pre_met_decomp_dist: Optional[float] = Field(None, description="熔胶前松退距离")

    pst_met_decomp_mode: Optional[int] = Field(None, description="熔胶后松退模式")
    pst_met_decomp_pres: Optional[float] = Field(None, description="熔胶后松退压力")
    pst_met_decomp_spd: Optional[float] = Field(None, description="熔胶后松退速度")
    pst_met_decomp_t: Optional[float] = Field(None, description="熔胶后松退时间")
    pst_met_decomp_dist: Optional[float] = Field(None, description="熔胶后松退距离")

    met_lim_t: Optional[float] = Field(None, description="熔胶延时")
    met_end_pos: Optional[float] = Field(None, description="熔胶终止位置")

    # --- 料筒温度参数 (10段) ---
    brl_temp_stg: Optional[int] = Field(None, description="料筒温度段数 1-10")
    noz_temp: Optional[float] = Field(None, description="喷嘴温度")
    brl_temp_1: Optional[float] = Field(None, description="一段料筒温度")
    brl_temp_2: Optional[float] = Field(None, description="二段料筒温度")
    brl_temp_3: Optional[float] = Field(None, description="三段料筒温度")
    brl_temp_4: Optional[float] = Field(None, description="四段料筒温度")
    brl_temp_5: Optional[float] = Field(None, description="五段料筒温度")
    brl_temp_6: Optional[float] = Field(None, description="六段料筒温度")
    brl_temp_7: Optional[float] = Field(None, description="七段料筒温度")
    brl_temp_8: Optional[float] = Field(None, description="八段料筒温度")
    brl_temp_9: Optional[float] = Field(None, description="九段料筒温度")


class ProcessParameterListSchema(PaginationBaseSchema):
    """工艺参数列表查询条件"""

    status: Optional[str] = Field(None, description="状态")
    origin_type: Optional[str] = Field(None, description="工艺起源类型")
    mold_id: Optional[int] = Field(None, description="模具 ID")
    injection_machine_id: Optional[int] = Field(None, description="注塑机 ID")
    polymer_id: Optional[int] = Field(None, description="材料 ID")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class BatchDeleteProcessParameterSchema(BaseSchema):
    """批量删除工艺参数"""

    ids: list[int] = Field(..., min_length=1, description="工艺参数 ID 列表")