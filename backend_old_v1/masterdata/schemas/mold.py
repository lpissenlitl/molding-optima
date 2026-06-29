from extensions.schemas import AbstractBaseSchema, BaseSchema, PaginationBaseSchema
from marshmallow import fields, EXCLUDE


class MoldSchema(BaseSchema):
    """模具表单"""
    id = fields.Integer(allow_none=True, metadata={"description": "模具ID"})
    project_id = fields.Integer(allow_none=True, metadata={"description": "项目ID"})
    # --- 状态信息 ---
    status = fields.String(allow_none=True, metadata={"description": "模具状态"})
    
    # --- 基本信息 ---
    mold_no = fields.String(required=True, metadata={"description": "模具编号"})
    mold_name = fields.String(allow_none=True, metadata={"description": "模具名称"})
    mold_type = fields.String(allow_none=True, metadata={"description": "模具类型"})
    category = fields.String(allow_none=True, metadata={"description": "模具类别"})
    structure = fields.String(allow_none=True, metadata={"description": "模具结构"})
    shot_count = fields.Integer(allow_none=True, metadata={"description": "注射阶段总数"})
    cavity_layout = fields.String(allow_none=True, metadata={"description": "模腔布局"})
    cavity_count = fields.Integer(allow_none=True, metadata={"description": "型腔数"})
    target_cycle_time = fields.Float(allow_none=True, metadata={"description": "目标成型周期 [s]"})
    recommended_tonnage = fields.Float(allow_none=True, metadata={"description": "推荐成型吨位"})
    total_injection_weight = fields.Float(allow_none=True, metadata={"description": "总注射重量"})
    material_handle_weight = fields.Float(allow_none=True, metadata={"description": "料把重量"})
    
    # --- 辅助装置 ---
    mechanism = fields.String(allow_none=True, metadata={"description": "辅助装置"})
    special_processes = fields.List(fields.String(), allow_none=True, metadata={"description": "特殊工艺"})
    
    # --- 产品分类 ---
    product_category = fields.String(allow_none=True, metadata={"description": "产品大类"})
    product_subcategory = fields.String(allow_none=True, metadata={"description": "产品中类"})
    product_model = fields.String(allow_none=True, metadata={"description": "产品小类"})
    product_description = fields.String(allow_none=True, metadata={"description": "产品描述"})
    
    # --- 浇注系统 ---
    gating_systems = fields.Nested("GatingSystemSchema", many=True, unknown=EXCLUDE)
    
    # --- 冷却系统 ---
    cooling_system = fields.Nested("CoolingSystemSchema", unknown=EXCLUDE)

    # --- 顶出系统 ---
    ejection_system = fields.Nested("EjectionSystemSchema", unknown=EXCLUDE)
    
    # --- 模具外形尺寸&重量 ---
    mold_length = fields.Float(allow_none=True, metadata={"description": "水平尺寸 [mm]"})
    mold_width = fields.Float(allow_none=True, metadata={"description": "垂直尺寸 [mm]"})
    mold_thickness = fields.Float(allow_none=True, metadata={"description": "闭合尺寸 [mm]"})
    mold_weight = fields.Float(allow_none=True, metadata={"description": "重量 [kg]"})
    
    # --- 开模与锁模 ---
    part_removal_action = fields.String(allow_none=True, metadata={"description": "取件方式"})
    runner_separation_distance = fields.Float(allow_none=True, metadata={"description": "流道分离距离 [mm]"})
    recommended_opening_stroke = fields.Float(allow_none=True, metadata={"description": "所需开模行程 [mm]"})
    min_clamping_force = fields.Float(allow_none=True, metadata={"description": "最小锁模力 [Ton]"})

    # --- 吊装结构 ---
    handling_type = fields.String(allow_none=True, metadata={"description": "吊装类型"})
    handling_thread_size = fields.String(allow_none=True, metadata={"description": "吊装螺纹尺寸"})
    handling_thread_depth = fields.Float(allow_none=True, metadata={"description": "吊装螺纹深度 [mm]"})
    handling_point_count = fields.Integer(allow_none=True, metadata={"description": "吊装点数量"})
    handling_position = fields.String(allow_none=True, metadata={"description": "吊装点位置"})
    
    # --- 定位圈 ---
    locating_ring_outer_dia = fields.Float(allow_none=True, metadata={"description": "定位圈外径 [mm]"})
    locating_ring_inner_dia = fields.Float(allow_none=True, metadata={"description": "定位圈内径 [mm]"})
    locating_ring_height = fields.Float(allow_none=True, metadata={"description": "定位圈高度 [mm]"})
    locating_ring_material = fields.String(allow_none=True, metadata={"description": "定位圈材质"})
    locating_ring_standard = fields.String(allow_none=True, metadata={"description": "定位圈标准"})
    mov_half_locating_ring_outer_dia = fields.Float(allow_none=True, metadata={"description": "动模定位圈外径 [mm]"})
    mov_half_locating_ring_inner_dia = fields.Float(allow_none=True, metadata={"description": "动模定位圈内径 [mm]"})
    mov_half_locating_ring_height = fields.Float(allow_none=True, metadata={"description": "动模定位圈高度 [mm]"})
    
    # --- 导向与定位结构 ---
    guide_pin_diameter = fields.Float(allow_none=True, metadata={"description": "导柱直径 [mm]"})
    guide_pin_count = fields.Integer(allow_none=True, metadata={"description": "导柱数量"})
    has_precision_locator = fields.Boolean(allow_none=True, metadata={"description": "是否有精定位"})
    locator_type = fields.String(allow_none=True, metadata={"description": "精定位类型"})
    locator_position = fields.String(allow_none=True, metadata={"description": "精定位位置"})


class GatingSystemSchema(AbstractBaseSchema):
    """浇注系统"""
    id = fields.Integer(allow_none=True, metadata={"description": "浇注系统ID"})
    
    # --- 流道类型 ---
    runner_type = fields.String(allow_none=True, metadata={"description": "流道类型"})
    total_product_weight = fields.Float(allow_none=True, metadata={"description": "总产品重量"})
    
    # --- 热流道系统（热流道 & 热转冷） ---
    hot_runner_supplier = fields.String(allow_none=True, metadata={"description": "热流道供应商"})
    hot_runner_system_type = fields.String(allow_none=True, metadata={"description": "热流道类型"})
    hot_runner_manifold_zones = fields.Integer(allow_none=True, metadata={"description": "分流板温控区数"})
    hot_runner_nozzle_count = fields.Integer(allow_none=True, metadata={"description": "热喷嘴数量"})

    has_sequencing_control = fields.Boolean(allow_none=True, metadata={"description": "是否有序流控制"})
    sequencing_control_method = fields.String(allow_none=True, metadata={"description": "时序控制方式"})
    valve_actuation_type = fields.String(allow_none=True, metadata={"description": "针阀驱动方式"})
    
    # --- 主流道衬套（冷流道 & 热转冷） ---
    runner_weight = fields.Float(allow_none=True, metadata={"description": "主流道重量 [g]"})
    runner_length = fields.Float(allow_none=True, metadata={"description": "主流道长度 [mm]"})
    sprue_bushing_outer_dia = fields.Float(allow_none=True, metadata={"description": "衬套外径 D1 [mm]"})
    sprue_bushing_bore_dia = fields.Float(allow_none=True, metadata={"description": "衬套孔径 D2 [mm]"})
    sprue_bushing_radius = fields.Float(allow_none=True, metadata={"description": "球面半径 R [mm]"})
    sprue_bushing_angle = fields.Float(allow_none=True, metadata={"description": "密封锥角 θ [°]"})
    sprue_bushing_material = fields.String(allow_none=True, metadata={"description": "主流道衬套材质"})
    sprue_bushing_standard = fields.String(allow_none=True, metadata={"description": "主流道衬套标准"})
    
    # --- 工艺相关参数 ---
    estimated_shot_weight = fields.Float(allow_none=True, metadata={"description": "注射重量 [g]"})
    estimated_runner_weight = fields.Float(allow_none=True, metadata={"description": "流道重量 [g]"})
    projected_area = fields.Float(allow_none=True, metadata={"description": "投影面积 [cm²]"})
    
    # --- 型腔参数 ---
    cavities = fields.Nested("CavitySchema", many=True, unknown=EXCLUDE, metadata={"description": "型腔"})


class CavitySchema(AbstractBaseSchema):
    """型腔"""
    id = fields.Integer(allow_none=True, metadata={"description": "型腔ID"})
    
    # --- 数量：这类型腔的数量 ---
    cavity_count_per_shot = fields.Integer(allow_none=True, metadata={"description": "型腔数量"})

    # --- 制品名称 ---
    product_name = fields.String(allow_none=True, metadata={"description": "制品名称"})
    product_code = fields.String(allow_none=True, metadata={"description": "制品编号"})

    # --- 制品关键工艺参数 ---
    max_flow_length = fields.Float(allow_none=True, metadata={"description": "最大流动长度 [mm]"})
    ave_wall_thickness = fields.Float(allow_none=True, metadata={"description": "平均壁厚 [mm]"})
    min_wall_thickness = fields.Float(allow_none=True, metadata={"description": "最小壁厚 [mm]"})
    max_wall_thickness = fields.Float(allow_none=True, metadata={"description": "最大壁厚 [mm]"})
    projected_area_per_cavity = fields.Float(allow_none=True, metadata={"description": "单腔投影面积 [mm²]"})
    estimated_weight_per_cavity = fields.Float(allow_none=True, metadata={"description": "单腔制品预估重量 [g]"})

    # --- 可计算特征 ---
    flow_ratio = fields.Float(allow_none=True, metadata={"description": "流动长度 / 平均壁厚"})
    thickness_variation = fields.Float(allow_none=True, metadata={"description": "壁厚变化率"})
    
    # --- 浇口 ---
    gates = fields.Nested("GateSchema", many=True, unknown=EXCLUDE, metadata={"description": "浇口"})


class GateSchema(AbstractBaseSchema):
    """浇口"""
    id = fields.Integer(allow_none=True, metadata={"description": "浇口ID"})
    
    # --- 浇口信息 ---
    gate_shape = fields.String(allow_none=True, metadata={"description": "浇口形状"})
    gate_type = fields.String(allow_none=True, metadata={"description": "浇口类型"})
    gate_count = fields.Integer(allow_none=True, metadata={"description": "浇口数量"})
    location_description = fields.String(allow_none=True, metadata={"description": "浇口位置描述"})
    # --- 关键尺寸（分别定义） ---
    # 矩形类
    length = fields.Float(allow_none=True, metadata={"description": "长度 [mm]"})
    width = fields.Float(allow_none=True, metadata={"description": "宽度 [mm]"})
    # 圆形类
    diameter = fields.Float(allow_none=True, metadata={"description": "直径 [mm]"})
    # 梯形类
    top_length = fields.Float(allow_none=True, metadata={"description": "顶边长度 [mm]"})
    bottom_length = fields.Float(allow_none=True, metadata={"description": "底边长度 [mm]"})
    height = fields.Float(allow_none=True, metadata={"description": "高度 [mm]"})
    # 环形类
    outer_diameter = fields.Float(allow_none=True, metadata={"description": "外径 [mm]"})
    inner_diameter = fields.Float(allow_none=True, metadata={"description": "内径 [mm]"})
    gap = fields.Float(allow_none=True, metadata={"description": "间隔 [mm]"})


class CoolingSystemSchema(AbstractBaseSchema):
    """冷却系统"""
    id = fields.Integer(allow_none=True, metadata={"description": "冷却系统ID"})
    
    cooling_cavity_type = fields.String(allow_none=True, metadata={"description": "型腔冷却类型"})
    cooling_cavity_circuit_count = fields.Integer(allow_none=True, metadata={"description": "型腔冷却回路数量"})
    cooling_cavity_layout = fields.String(allow_none=True, metadata={"description": "型腔冷却布局"})
    cooling_cavity_pipe_diameter = fields.Float(allow_none=True, metadata={"description": "型腔冷却管径 [mm]"})
    cooling_cavity_fitting_type = fields.String(allow_none=True, metadata={"description": "型腔冷却管连接器类型"})
    cooling_cavity_fitting_count = fields.Integer(allow_none=True, metadata={"description": "型腔冷却管连接器数量"})
    cooling_cavity_fitting_labels = fields.String(allow_none=True, metadata={"description": "型腔冷却管连接器标签"})
    cooling_cavity_fitting_seal_method = fields.String(allow_none=True, metadata={"description": "型腔水嘴密封方式"})

    cooling_core_type = fields.String(allow_none=True, metadata={"description": "型芯冷却类型"})
    cooling_core_circuit_count = fields.Integer(allow_none=True, metadata={"description": "型芯冷却回路数量"})
    cooling_core_layout = fields.String(allow_none=True, metadata={"description": "型芯冷却布局"})
    cooling_core_pipe_diameter = fields.Float(allow_none=True, metadata={"description": "型芯冷却管径 [mm]"})
    cooling_core_fitting_type = fields.String(allow_none=True, metadata={"description": "型芯冷却管连接器类型"})
    cooling_core_fitting_count = fields.Integer(allow_none=True, metadata={"description": "型芯冷却管连接器数量"})
    cooling_core_fitting_labels = fields.String(allow_none=True, metadata={"description": "型芯冷却管连接器标签"})
    cooling_core_fitting_seal_method = fields.String(allow_none=True, metadata={"description": "型芯水嘴密封方式"})


class EjectionSystemSchema(AbstractBaseSchema):
    """顶出系统"""
    id = fields.Integer(allow_none=True, metadata={"description": "顶出系统ID"})

    ejection_type = fields.String(allow_none=True, metadata={"description": "顶出类型"})
    reset_method = fields.String(allow_none=True, metadata={"description": "复位方式"})
    ejector_rod_hole_type = fields.String(allow_none=True, metadata={"description": "顶棍孔类型"})
    ejector_rod_hole_diameter = fields.Float(allow_none=True, metadata={"description": "顶棍孔直径 [mm]"})
    ejector_rod_hole_depth = fields.Float(allow_none=True, metadata={"description": "顶棍孔深度 [mm]"})
    ejector_rod_hole_spacing_x = fields.Float(allow_none=True, metadata={"description": "顶棍孔x向间隔 [mm]"})
    ejector_rod_hole_spacing_y = fields.Float(allow_none=True, metadata={"description": "顶棍孔y向间隔 [mm]"})
    ejection_stroke = fields.Float(allow_none=True, metadata={"description": "顶出行程 [mm]"})
    has_pre_ejection = fields.Boolean(allow_none=True, metadata={"description": "是否有预顶出"})
    pre_ejection_stroke = fields.Float(allow_none=True, metadata={"description": "预顶出行程 [mm]"})
    estimated_ejection_force = fields.Float(allow_none=True, metadata={"description": "预估顶出力 [kgf]"})
    

class MoldListSchema(PaginationBaseSchema):
    """获取模具列表"""
    status = fields.String(allow_none=True, metadata={"description": "模具状态"})
    mold_no = fields.String(allow_none=True, metadata={"description": "模具代码"})
    mold_name = fields.String(allow_none=True, metadata={"description": "模具名称"})
    category = fields.String(allow_none=True, metadata={"description": "模具类别"})
    structure = fields.String(allow_none=True, metadata={"description": "模具结构"})
    cavity_layout = fields.String(allow_none=True, metadata={"description": "模腔布局"})
    id = fields.Integer(allow_none=True, metadata={"description": "模具ID"})
    is_duplicate_check = fields.Boolean(allow_none=True, metadata={"description": "是否为检查重复项"})
    