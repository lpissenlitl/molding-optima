"""
模具相关 Schema 定义 - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

from extensions.schemas import AbstractBaseSchema, BaseSchema, PaginationBaseSchema


# ==================== 嵌套 Schema ====================

class GateSchema(AbstractBaseSchema):
    """浇口"""
    
    id: Optional[int] = Field(None, description="浇口ID")
    # --- 浇口信息 ---
    gate_shape: Optional[str] = Field(None, description="浇口形状")
    gate_type: Optional[str] = Field(None, description="浇口类型")
    gate_count: Optional[int] = Field(None, description="浇口数量")
    location_description: Optional[str] = Field(None, description="浇口位置描述")
    # --- 关键尺寸（分别定义） ---
    # 矩形类
    length: Optional[float] = Field(None, description="长度 [mm]")
    width: Optional[float] = Field(None, description="宽度 [mm]")
    # 圆形类
    diameter: Optional[float] = Field(None, description="直径 [mm]")
    # 梯形类
    top_length: Optional[float] = Field(None, description="顶边长度 [mm]")
    bottom_length: Optional[float] = Field(None, description="底边长度 [mm]")
    height: Optional[float] = Field(None, description="高度 [mm]")
    # 环形类
    outer_diameter: Optional[float] = Field(None, description="外径 [mm]")
    inner_diameter: Optional[float] = Field(None, description="内径 [mm]")
    gap: Optional[float] = Field(None, description="间隔 [mm]")


class CavitySchema(AbstractBaseSchema):
    """型腔"""
    
    id: Optional[int] = Field(None, description="型腔ID")
    # --- 数量：这类型腔的数量 ---
    cavity_count_per_shot: Optional[int] = Field(None, description="型腔数量")
    # --- 制品名称 ---
    product_name: Optional[str] = Field(None, description="制品名称")
    product_code: Optional[str] = Field(None, description="制品编号")
    # --- 制品关键工艺参数 ---
    max_flow_length: Optional[float] = Field(None, description="最大流动长度 [mm]")
    ave_wall_thickness: Optional[float] = Field(None, description="平均壁厚 [mm]")
    min_wall_thickness: Optional[float] = Field(None, description="最小壁厚 [mm]")
    max_wall_thickness: Optional[float] = Field(None, description="最大壁厚 [mm]")
    projected_area_per_cavity: Optional[float] = Field(None, description="单腔投影面积 [mm²]")
    estimated_weight_per_cavity: Optional[float] = Field(None, description="单腔制品预估重量 [g]")
    # --- 可计算特征 ---
    flow_ratio: Optional[float] = Field(None, description="流动长度 / 平均壁厚")
    thickness_variation: Optional[float] = Field(None, description="壁厚变化率")
    # --- 浇口 ---
    gates: Optional[List[GateSchema]] = Field(None, description="浇口")


class GatingSystemSchema(AbstractBaseSchema):
    """浇注系统"""
    
    id: Optional[int] = Field(None, description="浇注系统ID")
    # --- 流道类型 ---
    runner_type: Optional[str] = Field(None, description="流道类型")
    total_product_weight: Optional[float] = Field(None, description="总产品重量")
    # --- 热流道系统（热流道 & 热转冷） ---
    hot_runner_supplier: Optional[str] = Field(None, description="热流道供应商")
    hot_runner_system_type: Optional[str] = Field(None, description="热流道类型")
    hot_runner_manifold_zones: Optional[int] = Field(None, description="分流板温控区数")
    hot_runner_nozzle_count: Optional[int] = Field(None, description="热喷嘴数量")
    has_sequencing_control: Optional[bool] = Field(None, description="是否有序流控制")
    sequencing_control_method: Optional[str] = Field(None, description="时序控制方式")
    valve_actuation_type: Optional[str] = Field(None, description="针阀驱动方式")
    # --- 主流道衬套（冷流道 & 热转冷） ---
    runner_weight: Optional[float] = Field(None, description="主流道重量 [g]")
    runner_length: Optional[float] = Field(None, description="主流道长度 [mm]")
    sprue_bushing_outer_dia: Optional[float] = Field(None, description="衬套外径 D1 [mm]")
    sprue_bushing_bore_dia: Optional[float] = Field(None, description="衬套孔径 D2 [mm]")
    sprue_bushing_radius: Optional[float] = Field(None, description="球面半径 R [mm]")
    sprue_bushing_angle: Optional[float] = Field(None, description="密封锥角 θ [°]")
    sprue_bushing_material: Optional[str] = Field(None, description="主流道衬套材质")
    sprue_bushing_standard: Optional[str] = Field(None, description="主流道衬套标准")
    # --- 工艺相关参数 ---
    estimated_shot_weight: Optional[float] = Field(None, description="注射重量 [g]")
    estimated_runner_weight: Optional[float] = Field(None, description="流道重量 [g]")
    projected_area: Optional[float] = Field(None, description="投影面积 [cm²]")
    # --- 型腔参数 ---
    cavities: Optional[List[CavitySchema]] = Field(None, description="型腔")


class CoolingSystemSchema(AbstractBaseSchema):
    """冷却系统"""
    
    id: Optional[int] = Field(None, description="冷却系统ID")
    cooling_cavity_type: Optional[str] = Field(None, description="型腔冷却类型")
    cooling_cavity_circuit_count: Optional[int] = Field(None, description="型腔冷却回路数量")
    cooling_cavity_layout: Optional[str] = Field(None, description="型腔冷却布局")
    cooling_cavity_pipe_diameter: Optional[float] = Field(None, description="型腔冷却管径 [mm]")
    cooling_cavity_fitting_type: Optional[str] = Field(None, description="型腔冷却管连接器类型")
    cooling_cavity_fitting_count: Optional[int] = Field(None, description="型腔冷却管连接器数量")
    cooling_cavity_fitting_labels: Optional[str] = Field(None, description="型腔冷却管连接器标签")
    cooling_cavity_fitting_seal_method: Optional[str] = Field(None, description="型腔水嘴密封方式")
    cooling_core_type: Optional[str] = Field(None, description="型芯冷却类型")
    cooling_core_circuit_count: Optional[int] = Field(None, description="型芯冷却回路数量")
    cooling_core_layout: Optional[str] = Field(None, description="型芯冷却布局")
    cooling_core_pipe_diameter: Optional[float] = Field(None, description="型芯冷却管径 [mm]")
    cooling_core_fitting_type: Optional[str] = Field(None, description="型芯冷却管连接器类型")
    cooling_core_fitting_count: Optional[int] = Field(None, description="型芯冷却管连接器数量")
    cooling_core_fitting_labels: Optional[str] = Field(None, description="型芯冷却管连接器标签")
    cooling_core_fitting_seal_method: Optional[str] = Field(None, description="型芯水嘴密封方式")


class EjectionSystemSchema(AbstractBaseSchema):
    """顶出系统"""
    
    id: Optional[int] = Field(None, description="顶出系统ID")
    ejection_type: Optional[str] = Field(None, description="顶出类型")
    reset_method: Optional[str] = Field(None, description="复位方式")
    ejector_rod_hole_type: Optional[str] = Field(None, description="顶棍孔类型")
    ejector_rod_hole_diameter: Optional[float] = Field(None, description="顶棍孔直径 [mm]")
    ejector_rod_hole_depth: Optional[float] = Field(None, description="顶棍孔深度 [mm]")
    ejector_rod_hole_spacing_x: Optional[float] = Field(None, description="顶棍孔x向间隔 [mm]")
    ejector_rod_hole_spacing_y: Optional[float] = Field(None, description="顶棍孔y向间隔 [mm]")
    ejection_stroke: Optional[float] = Field(None, description="顶出行程 [mm]")
    has_pre_ejection: Optional[bool] = Field(None, description="是否有预顶出")
    pre_ejection_stroke: Optional[float] = Field(None, description="预顶出行程 [mm]")
    estimated_ejection_force: Optional[float] = Field(None, description="预估顶出力 [kgf]")


# ==================== 模具主 Schema ====================

class MoldSchema(BaseSchema):
    """模具表单"""
    
    id: Optional[int] = Field(None, description="模具ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    # --- 状态信息 ---
    status: Optional[str] = Field(None, description="模具状态")
    # --- 基本信息 ---
    mold_no: str = Field(..., description="模具编号")
    mold_name: Optional[str] = Field(None, description="模具名称")
    mold_type: Optional[str] = Field(None, description="模具类型")
    category: Optional[str] = Field(None, description="模具类别")
    structure: Optional[str] = Field(None, description="模具结构")
    shot_count: Optional[int] = Field(None, description="注射阶段总数")
    cavity_layout: Optional[str] = Field(None, description="模腔布局")
    cavity_count: Optional[int] = Field(None, description="型腔数")
    target_cycle_time: Optional[float] = Field(None, description="目标成型周期 [s]")
    recommended_tonnage: Optional[float] = Field(None, description="推荐成型吨位")
    total_injection_weight: Optional[float] = Field(None, description="总注射重量")
    material_handle_weight: Optional[float] = Field(None, description="料把重量")
    # --- 辅助装置 ---
    mechanism: Optional[str] = Field(None, description="辅助装置")
    special_processes: Optional[List[str]] = Field(None, description="特殊工艺")
    # --- 产品分类 ---
    product_category: Optional[str] = Field(None, description="产品大类")
    product_subcategory: Optional[str] = Field(None, description="产品中类")
    product_model: Optional[str] = Field(None, description="产品小类")
    product_description: Optional[str] = Field(None, description="产品描述")
    # --- 浇注系统 ---
    gating_systems: Optional[List[GatingSystemSchema]] = Field(None, description="浇注系统")
    # --- 冷却系统 ---
    cooling_system: Optional[CoolingSystemSchema] = Field(None, description="冷却系统")
    # --- 顶出系统 ---
    ejection_system: Optional[EjectionSystemSchema] = Field(None, description="顶出系统")
    # --- 模具外形尺寸&重量 ---
    mold_length: Optional[float] = Field(None, description="水平尺寸 [mm]")
    mold_width: Optional[float] = Field(None, description="垂直尺寸 [mm]")
    mold_thickness: Optional[float] = Field(None, description="闭合尺寸 [mm]")
    mold_weight: Optional[float] = Field(None, description="重量 [kg]")
    # --- 开模与锁模 ---
    part_removal_action: Optional[str] = Field(None, description="取件方式")
    runner_separation_distance: Optional[float] = Field(None, description="流道分离距离 [mm]")
    recommended_opening_stroke: Optional[float] = Field(None, description="所需开模行程 [mm]")
    min_clamping_force: Optional[float] = Field(None, description="最小锁模力 [Ton]")
    # --- 吊装结构 ---
    handling_type: Optional[str] = Field(None, description="吊装类型")
    handling_thread_size: Optional[str] = Field(None, description="吊装螺纹尺寸")
    handling_thread_depth: Optional[float] = Field(None, description="吊装螺纹深度 [mm]")
    handling_point_count: Optional[int] = Field(None, description="吊装点数量")
    handling_position: Optional[str] = Field(None, description="吊装点位置")
    # --- 定位圈 ---
    locating_ring_outer_dia: Optional[float] = Field(None, description="定位圈外径 [mm]")
    locating_ring_inner_dia: Optional[float] = Field(None, description="定位圈内径 [mm]")
    locating_ring_height: Optional[float] = Field(None, description="定位圈高度 [mm]")
    locating_ring_material: Optional[str] = Field(None, description="定位圈材质")
    locating_ring_standard: Optional[str] = Field(None, description="定位圈标准")
    mov_half_locating_ring_outer_dia: Optional[float] = Field(None, description="动模定位圈外径 [mm]")
    mov_half_locating_ring_inner_dia: Optional[float] = Field(None, description="动模定位圈内径 [mm]")
    mov_half_locating_ring_height: Optional[float] = Field(None, description="动模定位圈高度 [mm]")
    # --- 导向与定位结构 ---
    guide_pin_diameter: Optional[float] = Field(None, description="导柱直径 [mm]")
    guide_pin_count: Optional[int] = Field(None, description="导柱数量")
    has_precision_locator: Optional[bool] = Field(None, description="是否有精定位")
    locator_type: Optional[str] = Field(None, description="精定位类型")
    locator_position: Optional[str] = Field(None, description="精定位位置")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )


class MoldListSchema(PaginationBaseSchema):
    """获取模具列表"""
    
    id: Optional[int] = Field(None, description="模具ID")
    status: Optional[str] = Field(None, description="模具状态")
    mold_no: Optional[str] = Field(None, description="模具代码")
    mold_name: Optional[str] = Field(None, description="模具名称")
    category: Optional[str] = Field(None, description="模具类别")
    structure: Optional[str] = Field(None, description="模具结构")
    cavity_layout: Optional[str] = Field(None, description="模腔布局")
    manufacturing_method: Optional[str] = Field(None, description="制作方式")
    is_duplicate_check: Optional[bool] = Field(None, description="是否为检查重复项")