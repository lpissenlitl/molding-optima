"""molding-optima 工艺参数初始化 Schema 定义

包含：
- 4 个推理输入：MachineInfoSchema / PolymerInfoSchema / MoldInfoSchema / ProcessSetSchema
- 3 个推理/初始化请求：
    ProcessInferSchema                              （/infer/ 纯推理，不查库不落库）
    ProcessInitializationFromSourceConditionSchema  （Mode C：从历史合格工艺复制）
    ProcessInitializationFromMasterdataSchema       （Mode B：基于 masterdata ID 调推理）
"""
from typing import Optional

from pydantic import Field

from extensions.schemas import BaseSchema


class MachineInfoSchema(BaseSchema):
    """设备信息（推理输入）

    单射设计：工艺推理时一台机台只取一个 InjectionUnit（按 injection_index 选取），
    因此 injection_unit 的字段被扁平化到 machine_info 同一层，避免 view 层做二次融合。

    包含：
    - 机器本身：power_method（动力方式）
    - 注射单元：screw_diameter / max_set_* / nozzle_type
    """

    # === 机器本身 ===
    power_method: Optional[str] = Field(
        None,
        description="动力方式：液压机/电动机",
    )

    # === 注射单元（扁平化，原 InjectionUnitSchema 内容）===
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

    单射设计：工艺推理时一个 mold 只取第一个 cavity / gate，
    因此 product / cavity / gate 的字段被扁平化到 mold_info 同一层。

    包含：
    - 模具级：shot_count
    - 产品（来自 GatingSystem）：product_weight / runner_weight
    - 产品尺寸（来自 Cavity）：ave_thickness / max_thickness / max_length
    - 浇口（来自 Gate）：gate_type / gate_radius / gate_length / gate_width
    - 热流道：valve_num
    - 周期：inject_cycle_require
    """

    # === 模具级 ===
    shot_count: Optional[int] = Field(None, description="模具射数")

    # === 产品本身（来自 GatingSystem）===
    product_weight: Optional[float] = Field(None, description="产品重量 (g)")
    runner_weight: Optional[float] = Field(0, description="流道重量 (g)，0 表示热流道")

    # === 产品尺寸（来自 Cavity）===
    ave_thickness: Optional[float] = Field(None, description="平均壁厚 (mm)")
    max_thickness: Optional[float] = Field(None, description="最大壁厚 (mm)")
    max_length: Optional[float] = Field(100, description="最大流长 (mm)")

    # === 浇口（来自 Gate）===
    gate_type: Optional[str] = Field(None, description="浇口类型：直浇口/侧浇口/点浇口/护耳式浇口/...")
    gate_radius: Optional[float] = Field(None, description="浇口半径 (mm)，侧浇口使用")
    gate_length: Optional[float] = Field(None, description="浇口长度 (mm)，侧浇口使用")
    gate_width: Optional[float] = Field(None, description="浇口宽度 (mm)，侧浇口使用")

    # === 热流道 ===
    valve_num: Optional[int] = Field(0, description="热流道阀针数量")

    # === 周期要求 ===
    inject_cycle_require: Optional[float] = Field(None, description="注塑周期要求 (s)")


class ProcessSetSchema(BaseSchema):
    """工艺设置（推理输入）

    独立维度：与机器/模具/材料无关，是推理时需要的"工艺元数据"。
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

    请求体（4 个独立维度，职责清晰）：
    {
        "mold_info": {...},        // 模具信息（模具级 + 产品/浇口/壁厚派生合一）
        "machine_info": {...},     // 设备信息（机台本身 + 注射单元合一）
        "polymer_info": {...},     // 材料信息
        "process_set": {...}       // 工艺设置（与设备/模具/材料无关的"工艺元数据"）
    }

    响应：
    {
        "param_source": "algorithm_init",
        "condition_id": null,                 # 纯推理不创建 Condition
        "matched_rules": [...],
        "process": {...}, "mold_temp": {...}, "hot_runner": {...},
        "summary": {...}
    }
    """

    # 4 个独立维度（扁平化、职责清晰），顺序统一为：模具 → 设备 → 材料 → 工艺设定
    # - 模具信息（模具级 + 产品/浇口/壁厚派生合一）
    # - 设备信息（机台本身 + 注射单元合一）
    # - 材料信息
    # - 工艺设置（与设备/模具/材料无关的"工艺元数据"）
    mold_info: MoldInfoSchema = Field(
        ..., description="模具信息（模具级 + 产品/浇口/壁厚派生）",
    )
    machine_info: MachineInfoSchema = Field(
        ..., description="设备信息（机器本身 + 注射单元）",
    )
    polymer_info: PolymerInfoSchema = Field(
        ..., description="材料信息",
    )
    process_set: ProcessSetSchema = Field(
        ..., description="工艺设置（段数与模式）",
    )


class ProcessInitializationFromSourceConditionSchema(BaseSchema):
    """【Mode C】基于源 condition_id 复制初始工艺参数请求

    POST /api/processes/initialization/from-source-condition/

    业务场景：
      工艺记录中已有“合格工艺”（condition + 其下的 ProcessParameter），
      复用该工艺作为新工艺的起点，不调用推理算法。
      为保证数据不过时，service 层会重新检索当前 masterdata 重构快照。

    请求体：
    {
        "source_condition_id": 100,   # 源工艺条件 ID（必填）
        "process_set": {...}           # 可选：工艺设置覆盖
    }

    status / origin_type 由后端固定为 draft / legacy_import。
    process_context 由后端自动写入（调用入参快照）。
    """

    source_condition_id: int = Field(
        ..., description="源工艺条件 ID（历史合格工艺，必填）",
    )
    process_set: Optional[ProcessSetSchema] = Field(
        None, description="工艺设置（段数与模式），不传则用 schema 默认值",
    )


class ProcessInitializationFromMasterdataSchema(BaseSchema):
    """【Mode B】基于 masterdata ID 的工艺初始化请求

    POST /api/processes/initialization/from-masterdata/

    业务语义：
      "基于 masterdata ID 创建一个新的工艺条件（ProcessCondition），
       并基于该条件生成初始工艺参数（ProcessParameter）"

    Step 1 入口适配：3 个 masterdata ID + shot_index + injection_index
    Step 2 数据前处理：service 层从 ORM 构建完整快照 (process_context_snapshot)
    Step 3+4 推理算法 + 落库：创建 Condition（存完整快照）+ ProcessParameter

    shot_index / injection_index 的角色：
      - shot_index       = 模具的"第几射"（多射模具：0=第一射, 1=第二射, ...）
      - injection_index  = 注塑机的"第几个射台"（多射台机：0=第一射台, 1=第二射台, ...）
      - 两个索引一旦确定，本次工艺条件对应的"哪台机哪个射台打哪个产品"也就确定
      - service 层会用它们从 mold.gating_systems[shot_index] 与 machine.injection_units[injection_index]
        精确选取子项，构建完整快照

    status / origin_type / condition_no 由后端自动生成。
    """

    mold_id: int = Field(..., description="模具 ID（必填）")
    polymer_id: int = Field(..., description="材料 ID（必填）")
    injection_machine_id: int = Field(..., description="注塑机 ID（必填）")

    # 索引字段（把旧版藏在 process_context 里的关联 ID 提升为显式入参）
    shot_index: int = Field(
        0, ge=0,
        description="模具的第几射（0-based，默认 0）。多射模具按此索引从 gating_systems 选取具体浇注系统。",
    )
    injection_index: int = Field(
        0, ge=0,
        description="注塑机的第几个射台（0-based，默认 0）。多射台注塑机按此索引从 injection_units 选取具体射台。",
    )

    process_set: Optional[ProcessSetSchema] = Field(
        None, description="工艺设置（段数与模式），不传则用 schema 默认值",
    )