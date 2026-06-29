from extensions.schemas import PaginationBaseSchema, TracedSchema, BaseSchema, AbstractBaseSchema
from marshmallow import fields, EXCLUDE


class PolymerRheologySchema(AbstractBaseSchema):
    """流变属性"""
    id = fields.Integer(allow_none=True, metadata={"description": "流变属性ID"})

    # Cross-WLF 模型参数
    model_type = fields.String(allow_none=True, load_default="cross_wlf", metadata={"description": "粘度模型"})
    cross_wlf_n = fields.Float(allow_none=True, metadata={"description": "Cross-WLF n"})
    cross_wlf_tau = fields.Float(allow_none=True, metadata={"description": "Cross-WLF tau [Pa]"})
    cross_wlf_d1 = fields.Float(allow_none=True, metadata={"description": "Cross-WLF D1 [Pa·s]"})
    cross_wlf_d2 = fields.Float(allow_none=True, metadata={"description": "Cross-WLF D2 [K]"})
    cross_wlf_d3 = fields.Float(allow_none=True, metadata={"description": "Cross-WLF D3 [K/Pa]"})
    cross_wlf_a1 = fields.Float(allow_none=True, metadata={"description": "Cross-WLF A1"})
    cross_wlf_a2 = fields.Float(allow_none=True, metadata={"description": "Cross-WLF A2 [K]"})
    
    c1 = fields.Float(allow_none=True, metadata={"description": "接合点损失法c1 [Pa^(1-c2)]"})
    c2 = fields.Float(allow_none=True, metadata={"description": "接合点损失法c2"})
    
    transition_temp = fields.Float(allow_none=True, metadata={"description": "转换温度 [℃]"})
    viscosity_index = fields.String(
        allow_none=True,
        metadata={"description": "粘度指数"}, 
    )
    
    mfr_temp = fields.Float(allow_none=True, metadata={"description": "MFR测试温度 [℃]"})
    mfr_load = fields.Float(allow_none=True, metadata={"description": "MFR载荷 [kg]"})
    mfr_value = fields.Float(allow_none=True, metadata={"description": "MFR值 [g/10min]"})


class PolymerPVTSchema(AbstractBaseSchema):
    """PVT 属性"""
    id = fields.Integer(allow_none=True, metadata={"description": "PVT 属性ID"})
    
    tait_b5 = fields.Float(allow_none=True, metadata={"description": "Tait b5 [K]"})
    tait_b6 = fields.Float(allow_none=True, metadata={"description": "Tait b6 [K/Pa]"})
    tait_b1m = fields.Float(allow_none=True, metadata={"description": "Tait b1m [m³/kg]"})
    tait_b2m = fields.Float(allow_none=True, metadata={"description": "Tait b2m [m³/kg·K]"})
    tait_b3m = fields.Float(allow_none=True, metadata={"description": "Tait b3m [Pa]"})
    tait_b4m = fields.Float(allow_none=True, metadata={"description": "Tait b4m [1/k]"})
    tait_b1s = fields.Float(allow_none=True, metadata={"description": "Tait b1s [m³/kg]"})
    tait_b2s = fields.Float(allow_none=True, metadata={"description": "Tait b2s [m³/kg·K]"})
    tait_b3s = fields.Float(allow_none=True, metadata={"description": "Tait b3s [Pa]"})
    tait_b4s = fields.Float(allow_none=True, metadata={"description": "Tait b4s [1/K]"})
    tait_b7 = fields.Float(allow_none=True, metadata={"description": "Tait b7 [m³/kg]"})
    tait_b8 = fields.Float(allow_none=True, metadata={"description": "Tait b8 [1/K]"})
    tait_b9 = fields.Float(allow_none=True, metadata={"description": "Tait b9 [1/Pa]"})
        

class PolymerMechanicalSchema(AbstractBaseSchema):
    """机械属性"""
    id = fields.Integer(allow_none=True, metadata={"description": "机械属性ID"})
    
    elastic_modulus_1 = fields.Float(allow_none=True, metadata={"description": "弹性模量E1 [MPa]"})
    elastic_modulus_2 = fields.Float(allow_none=True, metadata={"description": "弹性模量E2 [MPa]"})
    poisson_v12 = fields.Float(allow_none=True, metadata={"description": "泊松比v12 [1/K]"})
    poisson_v23 = fields.Float(allow_none=True, metadata={"description": "泊松比v23 [1/K]"})
    shear_modulus_g12 = fields.Float(allow_none=True, metadata={"description": "剪切模量G12 [MPa]"})
    thermal_expansion_1 = fields.Float(allow_none=True, metadata={"description": "热膨胀系数α1 [1/K]"})
    thermal_expansion_2 = fields.Float(allow_none=True, metadata={"description": "热膨胀系数α2 [1/K]"})


class PolymerShrinkageSchema(AbstractBaseSchema):
    """收缩属性"""
    id = fields.Integer(allow_none=True, metadata={"description": "ID"})

    ave_h_shrink = fields.Float(allow_none=True, metadata={"description": "平均水平收缩率 [%]"})
    ave_v_shrink = fields.Float(allow_none=True, metadata={"description": "平均垂直收缩率 [%]"})
    min_h_shrink = fields.Float(allow_none=True, metadata={"description": "最小水平收缩率 [%]"})
    max_h_shrink = fields.Float(allow_none=True, metadata={"description": "最大水平收缩率 [%]"})
    min_v_shrink = fields.Float(allow_none=True, metadata={"description": "最小垂直收缩率 [%]"})
    max_v_shrink = fields.Float(allow_none=True, metadata={"description": "最大垂直收缩率 [%]"})


class FillerSchema(BaseSchema):
    """
    填充物属性
    如：玻璃纤维、滑石粉、碳酸钙等
    """
    name = fields.String(allow_none=True, metadata={"description": "名称"})
    abbreviation = fields.String(allow_none=True, metadata={"description": "缩写"})
    
    # --- 关键分类与形态 ---
    category = fields.String(allow_none=True, metadata={"description": "类别"})
    shape = fields.String(allow_none=True, metadata={"description": "形状"})
    
    # --- 关键工艺相关参数 ---
    particle_size_d50 = fields.Float(allow_none=True, metadata={"description": "中位粒径 D50 [μm]"})
    aspect_ratio = fields.Float(allow_none=True, metadata={"description": "长径比"})
    moisture_content = fields.Float(allow_none=True, metadata={"description": "含水率 [%]"})
    surface_treatment = fields.String(allow_none=True, metadata={"description": "表面处理"})

    # --- 关键物理性能（用于质量控制） ---
    density = fields.Float(allow_none=True, metadata={"description": "密度 [g/cm³]"})
    thermal_stability_temp = fields.Float(allow_none=True, metadata={"description": "热稳定温度 [℃]"})
    color = fields.String(allow_none=True, metadata={"description": "颜色"})
    

class PolymerSchema(BaseSchema):
    """塑料材料主数据"""
    # --- 基本信息 ---
    abbreviation = fields.String(allow_none=True, metadata={"description": "缩写，如：ABS、PP"})
    grade = fields.String(allow_none=True, metadata={"description": "牌号，聚丙烯 Grade PP-H040"})
    manufacturer = fields.String(allow_none=True, metadata={"description": "制造商"})
    category = fields.String(allow_none=True, metadata={"description": "类别，如：结晶型、无定形"})
    series = fields.String(allow_none=True, metadata={"description": "系列，如：高抗冲"})
    data_source = fields.String(allow_none=True, metadata={"description": "数据来源，如：客户、供应商、内部"})
    data_status = fields.String(allow_none=True, metadata={"description": "数据状态，如：正常、测试、归档"})
    internal_id = fields.String(allow_none=True, metadata={"description": "内部编号，如：PP-H040"})
    level_code = fields.String(allow_none=True, metadata={"description": "等级代码"})
    vendor_code = fields.String(allow_none=True, metadata={"description": "供应商代码"})
    
    # --- 工艺信息 ---
    melt_density = fields.Float(allow_none=True, metadata={"description": "熔体密度 [g/cm³]"})
    solid_density = fields.Float(allow_none=True, metadata={"description": "固体密度 [g/cm³]"})
    
    min_melt_temp = fields.Float(allow_none=True, metadata={"description": "最小熔体温度 [℃]"})
    max_melt_temp = fields.Float(allow_none=True, metadata={"description": "最大熔体温度 [℃]"})
    recommended_melt_temp = fields.Float(allow_none=True, metadata={"description": "推荐熔体温度 [℃]"})
    
    min_mold_temp = fields.Float(allow_none=True, metadata={"description": "最小模具温度 [℃]"})
    max_mold_temp = fields.Float(allow_none=True, metadata={"description": "最大模具温度 [℃]"})
    recommended_mold_temp = fields.Float(allow_none=True, metadata={"description": "推荐模具温度 [℃]"})
    
    min_shear_line_speed = fields.Float(allow_none=True, metadata={"description": "最小剪切线速度 [mm/s]"})
    max_shear_line_speed = fields.Float(allow_none=True, metadata={"description": "最大剪切线速度 [mm/s]"})
    recommended_shear_line_speed = fields.Float(allow_none=True, metadata={"description": "推荐剪切线速度 [mm/s]"})
    
    degradation_temp = fields.Float(allow_none=True, metadata={"description": "降级温度 [℃]"})
    ejection_temp = fields.Float(allow_none=True, metadata={"description": "顶出温度 [℃]"})
    barrel_residence_time = fields.Float(allow_none=True, metadata={"description": "料筒滞留时间 [min]"})
    max_shear_rate = fields.Float(allow_none=True, metadata={"description": "最大剪切速率 [1/s]"})
    max_shear_stress = fields.Float(allow_none=True, metadata={"description": "最大剪切应力 [MPa]"})
    
    recommend_injection_rate = fields.Float(allow_none=True, metadata={"description": "推荐注塑速率 [cm³/s]"})
    recommend_back_pressure = fields.Float(allow_none=True, metadata={"description": "推荐背压 [MPa]"})

    drying_method = fields.String(allow_none=True, metadata={"description": "干燥方式"})
    drying_temp_min = fields.Float(allow_none=True, metadata={"description": "干燥温度下限 [℃]"})
    drying_temp_max = fields.Float(allow_none=True, metadata={"description": "干燥温度上限 [℃]"})
    drying_time_min = fields.Float(allow_none=True, metadata={"description": "干燥时间下限 [min]"})
    drying_time_max = fields.Float(allow_none=True, metadata={"description": "干燥时间上限 [min]"})

    # --- 填充物组成 ---
    polymer_filler_compositions = fields.Dict(allow_none=True, metadata={"description": "填充物组成"})
    
    # ---  plastic rheology ---
    rheology = fields.Nested(PolymerRheologySchema, required=False, allow_none=True, unknown=EXCLUDE)
    # ---  plastic pvt ---
    pvt = fields.Nested(PolymerPVTSchema, required=False, allow_none=True, unknown=EXCLUDE)
    # ---  plastic mechanical ---
    mechanical = fields.Nested(PolymerMechanicalSchema, required=False, allow_none=True, unknown=EXCLUDE)
    # ---  plastic shrinkage ---
    shrinkage = fields.Nested(PolymerShrinkageSchema, required=False, allow_none=True, unknown=EXCLUDE)


class FillerListSchema(PaginationBaseSchema):
    """填充物列表"""
    name = fields.String(allow_none=True, metadata={"description": "名称"})
    category = fields.String(allow_none=True, metadata={"description": "类别"})
    shape = fields.String(allow_none=True, metadata={"description": "形状"})
    color = fields.String(allow_none=True, metadata={"description": "颜色"})
    abbreviation = fields.String(allow_none=True, metadata={"description": "缩写"})


class PolymerListSchema(PaginationBaseSchema):
    """塑料列表"""
    abbreviation = fields.String(allow_none=True, metadata={"description": "缩写"})
    grade = fields.String(allow_none=True, metadata={"description": "牌号"})
    manufacturer = fields.String(allow_none=True, metadata={"description": "制造商"})
    category = fields.String(allow_none=True, metadata={"description": "类别"})
    data_source = fields.String(allow_none=True, metadata={"description": "数据来源"})
    level_code = fields.String(allow_none=True, metadata={"description": "等级代码"})
    vendor_code = fields.String(allow_none=True, metadata={"description": "供应商代码"})