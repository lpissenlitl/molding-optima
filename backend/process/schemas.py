"""
molding-optima 工艺参数相关 Schema 定义（Pydantic 版本）

字段命名严格匹配 process/models.py（参考 molding-expert 设计）：
- 工艺参数：param_code, param_source, parent_param_id, seq_idx
- 注射参数：inj_stg, inj_spd_1..6, inj_pres_1..6, inj_pos_1..6, inj_t, inj_dly_t
- VP 切换：vps_mode, vps_pos, vps_t, vps_pres, vps_spd
- 保压参数：hold_stg, hold_pres_1..5, hold_spd_1..5, hold_t_1..5
- 冷却参数：cool_t
- 熔胶参数：met_stg, met_pres_1..4, met_rot_spd_1..4, met_back_pres_1..4, met_pos_1..4
- 松退参数：pre_met_decomp_*, pst_met_decomp_*, met_lim_t, met_end_pos
- 料筒温度：brl_temp_stg, noz_temp, brl_temp_1..9
"""
from typing import Optional, Any
from datetime import date
from pydantic import Field

from extensions.schemas import BaseSchema, PaginationBaseSchema


class ProcessConditionSchema(BaseSchema):
    """工艺条件"""

    condition_code: Optional[str] = Field(None, description="工艺条件编号")
    status: Optional[str] = Field(None, description="状态")
    origin_type: Optional[str] = Field(None, description="工艺起源类型")
    process_context_snapshot: Optional[dict] = Field(None, description="工艺条件快照")
    mold_id: Optional[int] = Field(None, description="模具 ID")
    shot_index: Optional[int] = Field(None, description="注射次数")
    injection_machine_id: Optional[int] = Field(None, description="注塑机 ID")
    injection_index: Optional[int] = Field(None, description="注射单元")
    polymer_id: Optional[int] = Field(None, description="材料 ID")


class ProcessParameterSchema(BaseSchema):
    """工艺参数记录"""

    process_condition_id: Optional[int] = Field(None, description="所属工艺条件 ID")

    # --- 基本信息 ---
    param_code: Optional[str] = Field(None, description="工艺参数编号")
    param_source: Optional[str] = Field(None, description="参数来源")
    parent_param_id: Optional[int] = Field(None, description="父参数 ID")
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


class ProcessConditionAndParameterSchema(BaseSchema):
    """工艺条件及参数（一次性创建）"""

    condition: ProcessConditionSchema = Field(...)
    parameter: ProcessParameterSchema = Field(...)


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


# ========== 工艺参数初始化（基于规则推理） ==========

class MachineInfoSchema(BaseSchema):
    """注塑机本身信息（推理输入）

    仅描述机器级别的元数据，注射相关参数在 InjectionUnitSchema 中。
    """

    power_method: Optional[str] = Field(
        None,
        description="动力方式：液压机/电动机",
    )


class InjectionUnitSchema(BaseSchema):
    """注射单元参数（推理输入）

    描述一个注射单元的物理能力，喷嘴安装在注射单元上。
    """

    screw_diameter: Optional[float] = Field(None, description="螺杆直径 (mm)")
    max_set_injection_pressure: Optional[float] = Field(None, description="最大设定注射压力")
    max_set_injection_velocity: Optional[float] = Field(None, description="最大设定注射速度")
    max_set_holding_pressure: Optional[float] = Field(None, description="最大设定保压压力")
    max_set_holding_velocity: Optional[float] = Field(None, description="最大设定保压速度")
    max_set_screw_rotation_speed: Optional[float] = Field(None, description="最大设定螺杆转速")
    max_set_metering_pressure: Optional[float] = Field(None, description="最大设定计量压力")
    nozzle_type: Optional[str] = Field(None, description="喷嘴类型：直通型/锁定型")


class PolymerInfoSchema(BaseSchema):
    """材料信息（推理输入）"""

    abbreviation: Optional[str] = Field(None, description="材料简称（ABS/PC/PC+ABS...）")
    recommend_melt_temperature: Optional[float] = Field(None, description="推荐熔体温度")
    recommend_shear_linear_speed: Optional[float] = Field(None, description="推荐剪切线速度")
    recommend_back_pressure: Optional[float] = Field(None, description="推荐背压")
    recommend_mold_temperature: Optional[float] = Field(None, description="推荐模温")
    melt_density: Optional[float] = Field(None, description="熔体密度")


class MoldInfoSchema(BaseSchema):
    """模具信息（推理输入）

    描述模具级别的元数据（如射数），产品/浇口/壁厚等详细信息在 ProductInfoSchema 中。
    """

    shot_count: Optional[int] = Field(None, description="模具射数")


class ProductInfoSchema(BaseSchema):
    """产品信息（推理输入）

    描述产品的物理特征，从 mold 的 cavity/gate 提取：
    - 产品本身特征：product_weight, runner_weight
    - 产品尺寸（来自 Cavity）：ave_thickness, max_thickness, max_length
    - 浇口特征（来自 Gate）：gate_type, gate_radius, gate_length, gate_width
    """

    # 产品本身特征
    product_weight: float = Field(..., description="产品重量 (g)")
    runner_weight: Optional[float] = Field(0, description="流道重量 (g)，0 表示热流道")

    # 产品尺寸（来自 Cavity）
    ave_thickness: float = Field(..., description="平均壁厚 (mm)")
    max_thickness: float = Field(..., description="最大壁厚 (mm)")
    max_length: Optional[float] = Field(100, description="最大流长 (mm)")

    # 浇口特征（来自 Gate）
    gate_type: str = Field(
        ..., description="浇口类型：直浇口/侧浇口/点浇口/护耳式浇口/...",
    )
    gate_radius: Optional[float] = Field(None, description="浇口半径 (mm)，侧浇口使用")
    gate_length: Optional[float] = Field(None, description="浇口长度 (mm)，侧浇口使用")
    gate_width: Optional[float] = Field(None, description="浇口宽度 (mm)，侧浇口使用")

    # 热流道
    valve_num: Optional[int] = Field(0, description="热流道阀针数量")

    # 周期要求（可由模具设计决定）
    inject_cycle_require: Optional[float] = Field(None, description="注塑周期要求 (s)")


class ProcessSetSchema(BaseSchema):
    """工艺设置（推理输入）

    描述工艺段数与模式设置，与产品/模具无关，是独立设置项。
    """

    # 段数设置
    inj_stg: Optional[int] = Field(1, ge=1, le=6, description="注射段数（1-6）")
    hold_stg: Optional[int] = Field(1, ge=1, le=5, description="保压段数（1-5）")
    met_stg: Optional[int] = Field(1, ge=1, le=4, description="计量段数（1-4）")
    barrel_temperature_stage: Optional[int] = Field(
        5, ge=1, le=10, description="料筒温度段数（1-10）",
    )

    # 模式设置
    VP_switch_mode: Optional[str] = Field("位置", description="VP 切换模式：位置/时间/...")
    vps_mode: Optional[int] = Field(None, ge=0, le=2, description="VP切换模式：0=位置 / 1=时间 / 2=其他")
    pre_met_decomp_mode: Optional[int] = Field(None, ge=0, le=2, description="熔胶前松退模式")
    pst_met_decomp_mode: Optional[int] = Field(None, ge=0, le=2, description="熔胶后松退模式")


class ProcessInferSchema(BaseSchema):
    """工艺参数纯推理请求（前端传完整数据，不查库不落库）

    适用场景：
    - 第三方系统集成：调用方没有我们的 masterdata，只能传完整数据
    - 算法试算：仅做参数推荐，不需要保存记录

    数据完整性要求：
    - 必须按信息归属层级提供完整的输入上下文
    - 与 /initialization/ 接口的区别：完全由调用方提供数据，后端不查库

    响应：
    {
        "param_source": "algorithm_init",
        "condition_id": null,                 # 纯推理不创建 Condition
        "matched_rules": [...],
        "process": {...}, "mold_temp": {...}, "hot_runner": {...},
        "summary": {...}
    }
    """

    # 机器层面
    machine_info: MachineInfoSchema = Field(
        ..., description="注塑机本身信息（动力方式）",
    )
    injection_unit: InjectionUnitSchema = Field(
        ..., description="注射单元参数（螺杆、最大压力等）",
    )

    # 材料层面
    polymer_info: PolymerInfoSchema = Field(
        ..., description="材料信息",
    )

    # 模具/产品层面
    mold_info: MoldInfoSchema = Field(
        ..., description="模具信息（模具级）",
    )
    product_info: ProductInfoSchema = Field(
        ..., description="产品信息（产品级）",
    )

    # 工艺设置
    process_set: ProcessSetSchema = Field(
        ..., description="工艺设置（段数与模式）",
    )


class ProcessInitializationSchema(BaseSchema):
    """工艺参数初始化请求（统一接口，都是落库接口）

    支持两种方式构建 Condition + Parameter：
    - Mode A：基于已有 condition_id —— 后端从数据库查询 mold/machine/polymer，
      创建新的 Parameter 记录（关联到现有 condition）
    - Mode B：基于 masterdata ID（mold_id + polymer_id + injection_machine_id）——
      后端从数据库查询 masterdata 并组装 Context，创建新的 Condition + Parameter

    两种模式互斥，不同时提供。两种模式默认都落库，因为数据库中有完整数据可关联。

    与 infer 接口的区别：
    - /initialization/infer/：完全由调用方提供数据（machine_info/polymer_info/product_info），
      后端不查库，不落库（数据库中没有关联数据，落库也是数据丢失）
    - /initialization/（本接口）：后端从数据库查询上下文，默认落库

    响应：
    Mode A:
    {
        "param_source": "algorithm_init",
        "condition_id": 123,         # 现有 condition ID（保持不变）
        "parameter_id": 456,         # 新创建的 ProcessParameter ID
        "matched_rules": [...],
        "process": {...}, "mold_temp": {...}, "hot_runner": {...},
        "summary": {...}
    }
    Mode B:
    {
        "condition_id": 789,         # 新建
        "parameter_id": 790,         # 新建
        "matched_rules": [...],
        "process": {...}, "mold_temp": {...}, "hot_runner": {...},
        "summary": {...}
    }
    """

    # ====== Mode A：基于已有 condition ======
    condition_id: Optional[int] = Field(
        None,
        description="Mode A：工艺条件 ID（提供时使用该模式，后端从数据库查询上下文，纯推理不落库）",
    )

    # ====== Mode B：基于 masterdata ID 组装 ======
    mold_id: Optional[int] = Field(
        None,
        description="Mode B：模具 ID（与 polymer_id、injection_machine_id 同时提供以使用此模式）",
    )
    polymer_id: Optional[int] = Field(
        None,
        description="Mode B：材料 ID（与 mold_id、injection_machine_id 同时提供以使用此模式）",
    )
    injection_machine_id: Optional[int] = Field(
        None,
        description="Mode B：注塑机 ID（与 mold_id、polymer_id 同时提供以使用此模式）",
    )

    # ====== Mode B 工艺元信息 ======
    shot_index: int = Field(1, description="Mode B：注射次数（多射场景）")
    injection_index: int = Field(1, description="Mode B：注射单元索引")
    status: str = Field("draft", description="Mode B：工艺条件状态：draft/testing/approved/...")
    origin_type: str = Field(
        "ai_recommendation",
        description="Mode B：工艺起源类型：manual_creation/ai_recommendation/template_based/...",
    )
    condition_code: Optional[str] = Field(
        None,
        description="Mode B：工艺条件编号（不传则自动生成，如 C-{mold}-{timestamp}）",
    )

    # ====== 用户覆盖字段（可选）======
    # 用于 masterdata 字段不准确时手动覆盖，仅限产品/工艺相关字段
    product_weight: Optional[float] = Field(None, description="覆盖：产品重量 (g)")
    runner_weight: Optional[float] = Field(None, description="覆盖：流道重量 (g)，0 表示热流道")
    gate_type: Optional[str] = Field(None, description="覆盖：浇口类型")
    ave_thickness: Optional[float] = Field(None, description="覆盖：平均壁厚 (mm)")
    max_thickness: Optional[float] = Field(None, description="覆盖：最大壁厚 (mm)")
    max_length: Optional[float] = Field(None, description="覆盖：最大流长 (mm)")
    gate_radius: Optional[float] = Field(None, description="覆盖：侧浇口半径 (mm)")
    gate_length: Optional[float] = Field(None, description="覆盖：侧浇口长度 (mm)")
    gate_width: Optional[float] = Field(None, description="覆盖：侧浇口宽度 (mm)")

    # ====== 工艺设置（段数与模式） ======
    # 使用嵌套的 process_set 字段，参数结构与 ProcessSetSchema 保持一致
    process_set: Optional[ProcessSetSchema] = Field(
        None,
        description="工艺设置（段数与模式），包含 inj_stg/hold_stg/met_stg/barrel_temperature_stage/vps_mode 等",
    )