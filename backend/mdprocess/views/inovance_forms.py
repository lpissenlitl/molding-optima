from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema, PaginationBaseSchema, CNDatetimeField



# 产品(form)--product_schema
class ProductSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    project_id = fields.Integer(required=False, allow_none=True)

    mold_type = fields.String(required=False, allow_none=True)
    inject_part = fields.String(required=True, allow_none=False)

    ave_thickness = fields.Float(required=False, allow_none=True)
    max_thickness = fields.Float(required=True, allow_none=False)
    min_thickness = fields.Float(required=False, allow_none=True)
    flow_length = fields.Float(required=True, allow_none=False)
    single_volume = fields.Float(required=False, allow_none=True)
    single_weight = fields.Float(required=False, allow_none=True)

    locate_ring_diameter = fields.Float(required=False, allow_none=True)  # 定位圈直径
    sprue_hole_diameter = fields.Float(required=False, allow_none=True)  # 喷嘴孔直径
    sprue_sphere_radius = fields.Float(required=False, allow_none=True)  # 喷嘴球半径
    runner_type = fields.Integer(required=True, allow_none=False)  # 流道类型
    hot_runner_num = fields.Integer(required=False, allow_none=True)
    valve_num = fields.Integer(required=False, allow_none=True)  # 热流道控制阀数量
    runner_length = fields.Float(required=True, allow_none=False)  # 流道长度
    runner_weight = fields.Float(required=True, allow_none=False)  # 流道重量
    gate_type = fields.Integer(required=True, allow_none=False)  # 浇口类别
    gate_num = fields.Integer(required=True, allow_none=False)  # 浇口数量
    gate_shape = fields.Integer(required=True, allow_none=False)  # 浇口形状
    gate_area = fields.Float(required=False, allow_none=True)  # 浇口横截面积
    gate_radius = fields.Float(required=False, allow_none=True)  # 浇口半径(圆)
    gate_length = fields.Float(required=False, allow_none=True)  # 浇口长(矩形)
    gate_width = fields.Float(required=False, allow_none=True)  # 浇口宽(矩形)
    

# 工程(form)--project_index_schema
class ProjectIndexSchema(BaseSchema):
    '''
    注塑模具信息表单
    '''

    id = fields.Integer(required=False, allow_none=True)
    company_id = fields.Integer(required=True, allow_none=False)
    created_at = CNDatetimeField(required=False, allow_none=True)
    updated_at = CNDatetimeField(required=False, allow_none=True)
    deleted = fields.Integer(required=False, allow_none=True)

    status = fields.Integer(required=False, allow_none=True)  # 模具当前状态
    mold_no = fields.String(required=True, allow_none=False)  # 模具编号
    mold_name = fields.String(required=False, allow_none=True)  # 模具名称
    mold_type = fields.String(required=False, allow_none=True)  # 模具类别
    cavity_num = fields.String(required=True, allow_none=False)  # 型腔数量

    product_no = fields.String(required=False, allow_none=True)  # 制品编号
    product_name = fields.String(required=True, allow_none=False)  # 制品名称
    product_type = fields.String(required=False, allow_none=True)  # 制品类别
    product_category = fields.String(required=False, allow_none=True)  # 制品品类
    product_small_type = fields.String(required=True, allow_none=False)
    product_total_weight = fields.Float(required=True, allow_none=False)  # 总重量
    product_projected_area = fields.Float(required=False, allow_none=True)  # 总投射面积

    product_infos = fields.Nested(ProductSchema, many=True)

    locate_ring_diameter = fields.Float(required=False, allow_none=True)  # 定位圈直径

    cavity_cooling_water_diameter = fields.Float(required=False, allow_none=True)  # 前模冷却水直径
    cavity_cooling_circuit_number = fields.Integer(required=False, allow_none=True)  # 前模冷却回路组数
    cavity_water_nozzle_specification = fields.Float(required=False, allow_none=True)  # 前模水嘴安装规格
    core_cooling_water_diameter = fields.Float(required=False, allow_none=True)  # 后模冷却水直径
    core_cooling_circuit_number = fields.Integer(required=False, allow_none=True)  # 后模冷却回路组数
    core_water_nozzle_specification = fields.Float(required=False, allow_none=True)  # 后模水嘴安装规格
    circuit_picture_url = fields.String(required=False, allow_none=True)  # 冷却回路附件
    
    ejector_stroke = fields.Float(required=False, allow_none=True)  # 顶出行程
    ejector_rod_hole_diameter = fields.Float(required=False, allow_none=True)  # 顶棍孔直径
    # ejector_rod_hole_distribute = fields.String(required=False, allow_none=True)  # 顶棍孔分布
    ejector_rod_hole_spacing = fields.Float(required=False, allow_none=True)  # 顶棍孔间距
    ejector_rod_number = fields.Integer(required=False, allow_none=True)  # 顶棍数量
    ejector_force = fields.Float(required=False, allow_none=True)  # 顶出力
    ejector_times = fields.Integer(required=False, allow_none=True)  # 顶出次数
    reset_method = fields.String(required=False, allow_none=True)  # 复位方式
    ejection_method = fields.String(required=False, allow_none=True)  # 顶出方式
    ejector_position_length = fields.Float(required=False, allow_none=True)  # 顶出孔位置
    ejector_position_width = fields.Float(required=False, allow_none=True)  # 顶出孔位置

    mold_weight = fields.Float(required=False, allow_none=True)  # 模具重量
    hanging_mold_hole_specification = fields.String(required=False, allow_none=True)  # 吊模孔规格

    size_horizon = fields.Float(required=False, allow_none=True)  # 模具尺寸（横）
    size_vertical = fields.Float(required=False, allow_none=True)  # 模板尺寸（竖）
    size_thickness = fields.Float(required=False, allow_none=True)  # 模具厚度
    min_clamping_force = fields.Float(required=False, allow_none=True)  # 最小锁模力
    drain_distance = fields.Float(required=False, allow_none=True)  # 取流道距离
    mold_opening_stroke = fields.Float(required=False, allow_none=True)  # 开模行程
    inject_cycle_require = fields.Float(required=False, allow_none=True)  # 注塑周期要求
    subrule_no = fields.String(required=False, allow_none=True)  # 模具绑定的子规则库
    
    assisting_equipments = fields.String(required=False, allow_none=True)  # 辅助装置信息

    customer = fields.String(required=False, allow_none=True)  # 客户
    project_engineer = fields.String(required=False, allow_none=True)  # 项目工程师
    design_engineer = fields.String(required=False, allow_none=True)  # 设计工程师
    production_engineer = fields.String(required=False, allow_none=True)  # 制作工程师
    mold_engineer = fields.String(required=False, allow_none=True)  # 模具工程师
    product_engineer = fields.String(required=False, allow_none=True)  # 产品工程师
    junior_product_engineer = fields.String(required=False, allow_none=True)  # 初级产品工程师
    injection_engineer = fields.String(required=False, allow_none=True)  # 注塑工程师
    senior_injection_engineer = fields.String(required=False, allow_none=True)  # 高级注塑工程师
    order_date = fields.Date(required=False, allow_none=True)  # 订单日期
    entry_date = fields.Date(required=False, allow_none=True)  # 信息录入日期


# 工程信息(from)--project_schema
class ProjectSchema(BaseSchema):
    mold_info = fields.Nested(ProjectIndexSchema)


class PolymerSchema(BaseSchema):
    # 增加材料
    company_id = fields.Integer(required=False, allow_none=True)
    series = fields.String(required=False, allow_none=True)
    manufacturer = fields.String(required=False, allow_none=True)
    trademark = fields.String(required=True, allow_none=False)
    abbreviation = fields.String(required=True, allow_none=False)
    category = fields.String(required=False, allow_none=True)  # 材料类型:结晶性,无定形
    data_source = fields.String(required=False, allow_none=True)
    data_status = fields.String(required=False, allow_none=True)
    internal_id = fields.String(required=False, allow_none=True)
    level_code = fields.String(required=False, allow_none=True)
    vendor_code = fields.String(required=False, allow_none=True)

    # 推荐工艺
    max_melt_temperature = fields.Float(required=False, allow_none=True)
    min_melt_temperature = fields.Float(required=False, allow_none=True)
    recommend_melt_temperature = fields.Float(required=True, allow_none=False)
    max_mold_temperature = fields.Float(required=False, allow_none=True)
    min_mold_temperature = fields.Float(required=False, allow_none=True)
    recommend_mold_temperature = fields.Float(required=True, allow_none=False)
    max_shear_linear_speed = fields.Float(required=False, allow_none=True)
    min_shear_linear_speed = fields.Float(required=False, allow_none=True)
    recommend_shear_linear_speed = fields.Float(required=True, allow_none=False)
    recommend_injection_rate = fields.Float(required=False, allow_none=True)
    recommend_back_pressure = fields.Float(required=True, allow_none=False)
    degradation_temperature = fields.Float(required=False, allow_none=True)
    ejection_temperature = fields.Float(required=False, allow_none=True)
    barrel_residence_time = fields.Float(required=False, allow_none=True)
    max_sheer_rate = fields.Float(required=False, allow_none=True)
    max_sheer_stress = fields.Float(required=False, allow_none=True)
    dry_temperature = fields.String(required=False, allow_none=True)
    dry_time = fields.String(required=False, allow_none=True)
    dry_method = fields.String(required=False, allow_none=True)

    # 流变属性
    viscosity_model = fields.String(required=False, allow_none=True)  # 粘度模型:cross_WLF
    cross_WLF_n = fields.String(required=False, allow_none=True)
    cross_WLF_Tau = fields.String(required=False, allow_none=True)  # Pa
    cross_WLF_D1 = fields.String(required=False, allow_none=True)  # Pa-s
    cross_WLF_D2 = fields.String(required=False, allow_none=True)  # k
    cross_WLF_D3 = fields.String(required=False, allow_none=True)  # k/Pa
    cross_WLF_A1 = fields.String(required=False, allow_none=True)
    cross_WLF_A2 = fields.String(required=False, allow_none=True)  # k
    c1 = fields.String(required=False, allow_none=True)  # 接合点损失法系数(Pa^(1-c2))
    c2 = fields.String(required=False, allow_none=True)  # 接合点损失法系数
    switch_temp = fields.String(required=False, allow_none=True)  # 转换温度(℃)
    viscosity_index = fields.String(required=False, allow_none=True)  # 粘度指数
    MFR_temp = fields.String(required=False, allow_none=True)  # 温度（℃）
    MFR_load = fields.String(required=False, allow_none=True)  # 载入（Kg）
    MFR_measure = fields.String(required=False, allow_none=True)  # 测量的MFR（g/10min）

    # pvT属性
    melt_density = fields.Float(required=True, allow_none=False)
    solid_density = fields.Float(required=True, allow_none=False)
    Tait_pvT_b5 = fields.String(required=False, allow_none=True)
    Tait_pvT_b6 = fields.String(required=False, allow_none=True)
    Tait_pvT_b1m = fields.String(required=False, allow_none=True)
    Tait_pvT_b2m = fields.String(required=False, allow_none=True)
    Tait_pvT_b3m = fields.String(required=False, allow_none=True)
    Tait_pvT_b4m = fields.String(required=False, allow_none=True)
    Tait_pvT_b1s = fields.String(required=False, allow_none=True)
    Tait_pvT_b2s = fields.String(required=False, allow_none=True)
    Tait_pvT_b3s = fields.String(required=False, allow_none=True)
    Tait_pvT_b4s = fields.String(required=False, allow_none=True)
    Tait_pvT_b7 = fields.String(required=False, allow_none=True)
    Tait_pvT_b8 = fields.String(required=False, allow_none=True)
    Tait_pvT_b9 = fields.String(required=False, allow_none=True)

    # 机械属性
    E1 = fields.Float(required=False, allow_none=True)
    E2 = fields.Float(required=False, allow_none=True)
    v12 = fields.Float(required=False, allow_none=True)
    v23 = fields.Float(required=False, allow_none=True)
    G12 = fields.Float(required=False, allow_none=True)
    Alpha1 = fields.Float(required=False, allow_none=True)
    Alpha2 = fields.Float(required=False, allow_none=True)

    # 收缩属性
    average_horizontal_shrinkage = fields.Float(required=False, allow_none=True)
    average_vertical_shrinkage = fields.Float(required=False, allow_none=True)
    min_horizontal_shrinkage = fields.Float(required=False, allow_none=True)
    max_horizontal_shrinkage = fields.Float(required=False, allow_none=True)
    min_vertical_shrinkage = fields.Float(required=False, allow_none=True)
    max_vertical_shrinkage = fields.Float(required=False, allow_none=True)

    # 填充物属性
    filler = fields.String(required=False, allow_none=True)
    filler_type = fields.String(required=False, allow_none=True)
    filler_shape = fields.String(required=False, allow_none=True)
    filler_percentage = fields.Float(required=False, allow_none=True)
    filler_density = fields.Float(required=False, allow_none=True)
    filler_specific_heat = fields.Float(required=False, allow_none=True)
    filler_specific_thermal_conductivity = fields.Float(required=False, allow_none=True)
    filler_E1 = fields.Float(required=False, allow_none=True)
    filler_E2 = fields.Float(required=False, allow_none=True)
    filler_v12 = fields.Float(required=False, allow_none=True)
    filler_v23 = fields.Float(required=False, allow_none=True)
    filler_G12 = fields.Float(required=False, allow_none=True)
    filler_Alpha1 = fields.Float(required=False, allow_none=True)
    filler_Alpha2 = fields.Float(required=False, allow_none=True)
    filler_horizontal_tensile_strength = fields.Float(required=False, allow_none=True)
    filler_vertical_tensile_strength = fields.Float(required=False, allow_none=True)
    filler_aspect_ratio = fields.Float(required=False, allow_none=True)
    
    # 修改时要用到的字段
    id = fields.Integer(required=False, allow_none=True)
    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer(default=0)


# 工艺初始化简版 form
class InitializeProcessSchema(BaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    optimize_type = fields.Integer(Required=False, allow_none=True, default=0) # 初始化 0: 不考虑保压，1：考虑保压
    status = fields.Integer(required=False, allow_none=True)  # 状态: 优化 1, 工艺存储 2, 优化&存储 3, 专家记录 4
    machine_id = fields.Integer(required=False, allow_none=True)
    mold_id = fields.Integer(required=False, allow_none=True)
    polymer_id = fields.Integer(required=False, allow_none=True)
    injection_stage = fields.Integer(required=False, allow_none=True)  # 注射段数
    holding_stage = fields.Integer(required=False, allow_none=True)  # 计量段数
    VP_switch_mode = fields.Integer(required=False, allow_none=True)  # VP切换模式
    metering_stage = fields.Integer(required=False, allow_none=True)  # 计量段数
    decompressure_mode_before_metering = fields.Integer(required=False, allow_none=True)  # 储前松退模式
    decompressure_mode_after_metering = fields.Integer(required=False, allow_none=True)  # 储后松退模式
    barrel_temperature_stage = fields.Integer(required=False, allow_none=True)  # 料筒温度段数


# 工艺参数优化传递参数
class OptimizeProcessSchema(BaseSchema):

    # 注射
    injection_stage = fields.Integer(required=False, allow_none=True)

    IP0 = fields.Float(required=False, allow_none=True)
    IV0 = fields.Float(required=False, allow_none=True)
    IL0 = fields.Float(required=False, allow_none=True)
    IP1 = fields.Float(required=False, allow_none=True)
    IV1 = fields.Float(required=False, allow_none=True)
    IL1 = fields.Float(required=False, allow_none=True)
    IP2 = fields.Float(required=False, allow_none=True)
    IV2 = fields.Float(required=False, allow_none=True)
    IL2 = fields.Float(required=False, allow_none=True)
    IP3 = fields.Float(required=False, allow_none=True)
    IV3 = fields.Float(required=False, allow_none=True)
    IL3 = fields.Float(required=False, allow_none=True)
    IP4 = fields.Float(required=False, allow_none=True)
    IV4 = fields.Float(required=False, allow_none=True)
    IL4 = fields.Float(required=False, allow_none=True)
    IP5 = fields.Float(required=False, allow_none=True)
    IV5 = fields.Float(required=False, allow_none=True)
    IL5 = fields.Float(required=False, allow_none=True)

    IT = fields.Float(required=False, allow_none=True)
    ID = fields.Float(required=False, allow_none=True)
    CT = fields.Float(required=False, allow_none=True)

    # 保压
    holding_stage = fields.Integer(required=False, allow_none=True)

    INIT_PP = fields.Float(required=False, allow_none=True)
    INIT_PV = fields.Float(required=False, allow_none=True)
    INIT_PT = fields.Float(required=False, allow_none=True)

    PP0 = fields.Float(required=False, allow_none=True)
    PV0 = fields.Float(required=False, allow_none=True)
    PT0 = fields.Float(required=False, allow_none=True)
    PP1 = fields.Float(required=False, allow_none=True)
    PV1 = fields.Float(required=False, allow_none=True)
    PT1 = fields.Float(required=False, allow_none=True)
    PP2 = fields.Float(required=False, allow_none=True)
    PV2 = fields.Float(required=False, allow_none=True)
    PT2 = fields.Float(required=False, allow_none=True)
    PP3 = fields.Float(required=False, allow_none=True)
    PV3 = fields.Float(required=False, allow_none=True)
    PT3 = fields.Float(required=False, allow_none=True)
    PP4 = fields.Float(required=False, allow_none=True)
    PV4 = fields.Float(required=False, allow_none=True)
    PT4 = fields.Float(required=False, allow_none=True)

    # VP切换
    VPTM = fields.Integer(required=False, allow_none=True)
    VPTT = fields.Float(required=False, allow_none=True)
    VPTL = fields.Float(required=False, allow_none=True)
    VPTP = fields.Float(required=False, allow_none=True)
    VPTV = fields.Float(required=False, allow_none=True)

    # 计量
    metering_stage = fields.Integer(required=False, allow_none=True)

    MP0 = fields.Float(required=False, allow_none=True)
    MSR0 = fields.Float(required=False, allow_none=True)
    MBP0 = fields.Float(required=False, allow_none=True)
    ML0 = fields.Float(required=False, allow_none=True) 
    MP1 = fields.Float(required=False, allow_none=True)
    MSR1 = fields.Float(required=False, allow_none=True)
    MBP1 = fields.Float(required=False, allow_none=True)
    ML1 = fields.Float(required=False, allow_none=True)
    MP2 = fields.Float(required=False, allow_none=True)
    MSR2 = fields.Float(required=False, allow_none=True)
    MBP2 = fields.Float(required=False, allow_none=True)
    ML2 = fields.Float(required=False, allow_none=True)
    MP3 = fields.Float(required=False, allow_none=True)
    MSR3 = fields.Float(required=False, allow_none=True)
    MBP3 = fields.Float(required=False, allow_none=True)
    ML3 = fields.Float(required=False, allow_none=True)

    DMBM = fields.Integer(required=False, allow_none=True)
    DMAM = fields.Integer(required=False, allow_none=True)

    DPBM = fields.Float(required=False, allow_none=True)
    DVBM = fields.Float(required=False, allow_none=True)
    DDBM = fields.Float(required=False, allow_none=True)
    DTBM = fields.Float(required=False, allow_none=True)

    DPAM = fields.Float(required=False, allow_none=True)
    DVAM = fields.Float(required=False, allow_none=True)
    DDAM = fields.Float(required=False, allow_none=True)
    DTAM = fields.Float(required=False, allow_none=True)

    MD = fields.Float(required=False, allow_none=True)
    MEL = fields.Float(required=False, allow_none=True)

    # 料筒温度
    barrel_temperature_stage = fields.Integer(required=False, allow_none=True)

    NT = fields.Float(required=False, allow_none=True)
    BT1 = fields.Float(required=False, allow_none=True)
    BT2 = fields.Float(required=False, allow_none=True)
    BT3 = fields.Float(required=False, allow_none=True)
    BT4 = fields.Float(required=False, allow_none=True)
    BT5 = fields.Float(required=False, allow_none=True)
    BT6 = fields.Float(required=False, allow_none=True)
    BT7 = fields.Float(required=False, allow_none=True)
    BT8 = fields.Float(required=False, allow_none=True)
    BT9 = fields.Float(required=False, allow_none=True)

    # 热流道时序控制时间
    SCVN = fields.Integer(required=False, allow_none=True)
    SCT0 = fields.Float(required=False, allow_none=True)
    SCT1 = fields.Float(required=False, allow_none=True)
    SCT2 = fields.Float(required=False, allow_none=True)
    SCT3 = fields.Float(required=False, allow_none=True)
    SCT4 = fields.Float(required=False, allow_none=True)
    SCT5 = fields.Float(required=False, allow_none=True)
    SCT6 = fields.Float(required=False, allow_none=True)
    SCT7 = fields.Float(required=False, allow_none=True)
    SCT8 = fields.Float(required=False, allow_none=True)
    SCT9 = fields.Float(required=False, allow_none=True)

    # 模温设定值
    MT = fields.Float(required=False, allow_none=True)
    MTN = fields.Integer(required=False, allow_none=True)
    MT0 = fields.Float(required=False, allow_none=True)
    MT1 = fields.Float(required=False, allow_none=True)
    MT2 = fields.Float(required=False, allow_none=True)
    MT3 = fields.Float(required=False, allow_none=True)
    MT4 = fields.Float(required=False, allow_none=True)
    MT5 = fields.Float(required=False, allow_none=True)
    MT6 = fields.Float(required=False, allow_none=True)
    MT7 = fields.Float(required=False, allow_none=True)
    MT8 = fields.Float(required=False, allow_none=True)
    MT9 = fields.Float(required=False, allow_none=True)
    MT10 = fields.Float(required=False, allow_none=True)
    MT11 = fields.Float(required=False, allow_none=True)
    MT12 = fields.Float(required=False, allow_none=True)
    MT13 = fields.Float(required=False, allow_none=True)
    MT14 = fields.Float(required=False, allow_none=True)
    MT15 = fields.Float(required=False, allow_none=True)
    MT16 = fields.Float(required=False, allow_none=True)
    MT17 = fields.Float(required=False, allow_none=True)
    MT18 = fields.Float(required=False, allow_none=True)
    MT19 = fields.Float(required=False, allow_none=True)

    actual_product_weight = fields.Float(required=False, allow_none=True)

    process_index_id = fields.Integer(required=False, allow_none=True)
    machine_id = fields.Integer(required=False, allow_none=True)
    product_weight = fields.Float(required=False, allow_none=True)
    opt_nums = fields.Integer(required=False, allow_none=True)

    polymer_abbreviation = fields.String(required=False, allow_none=True)
    product_small_type = fields.String(required=False, allow_none=True)

    subrule_no = fields.String(required=False, allow_none=True)
    general = fields.Boolean(required=False, allow_none=True)  # 调用的通用规则库
    
    B000 = fields.Integer(required=False, allow_none=True)
    B001 = fields.Integer(required=False, allow_none=True)
    B002 = fields.Integer(required=False, allow_none=True)
    B003 = fields.Integer(required=False, allow_none=True)
    B004 = fields.Integer(required=False, allow_none=True)
    B005 = fields.Integer(required=False, allow_none=True)
    B006 = fields.Integer(required=False, allow_none=True)
    B007 = fields.Integer(required=False, allow_none=True)
    B008 = fields.Integer(required=False, allow_none=True)
    B009 = fields.Integer(required=False, allow_none=True)
    B010 = fields.Integer(required=False, allow_none=True)
    B011 = fields.Integer(required=False, allow_none=True)
    B012 = fields.Integer(required=False, allow_none=True)
    B013 = fields.Integer(required=False, allow_none=True)
    B014 = fields.Integer(required=False, allow_none=True)
    B015 = fields.Integer(required=False, allow_none=True)
    B016 = fields.Integer(required=False, allow_none=True)
    B017 = fields.Integer(required=False, allow_none=True)
    B018 = fields.Integer(required=False, allow_none=True)
    B019 = fields.Integer(required=False, allow_none=True)
    B020 = fields.Integer(required=False, allow_none=True)
    B021 = fields.Integer(required=False, allow_none=True)
    B022 = fields.Integer(required=False, allow_none=True)
    B023 = fields.Integer(required=False, allow_none=True)
    B024 = fields.Integer(required=False, allow_none=True)
    B025 = fields.Integer(required=False, allow_none=True)
    B026 = fields.Integer(required=False, allow_none=True)
    B027 = fields.Integer(required=False, allow_none=True)
    B028 = fields.Integer(required=False, allow_none=True)
    B029 = fields.Integer(required=False, allow_none=True)
    B030 = fields.Integer(required=False, allow_none=True)
    B031 = fields.Integer(required=False, allow_none=True)
    B032 = fields.Integer(required=False, allow_none=True)
    B033 = fields.Integer(required=False, allow_none=True)
    B034 = fields.Integer(required=False, allow_none=True)
    B035 = fields.Integer(required=False, allow_none=True)
    B036 = fields.Integer(required=False, allow_none=True)
    B037 = fields.Integer(required=False, allow_none=True)
    B038 = fields.Integer(required=False, allow_none=True)
    B039 = fields.Integer(required=False, allow_none=True)
    B040 = fields.Integer(required=False, allow_none=True)
    B041 = fields.Integer(required=False, allow_none=True)
    B042 = fields.Integer(required=False, allow_none=True)
    B043 = fields.Integer(required=False, allow_none=True)
    B044 = fields.Integer(required=False, allow_none=True)
    B045 = fields.Integer(required=False, allow_none=True)
    B046 = fields.Integer(required=False, allow_none=True)
    B047 = fields.Integer(required=False, allow_none=True)
    B048 = fields.Integer(required=False, allow_none=True)
    B049 = fields.Integer(required=False, allow_none=True)
    B050 = fields.Integer(required=False, allow_none=True)
    
    

