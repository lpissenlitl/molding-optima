"""
材料相关 Schema 定义 - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Optional, Dict, Any
from pydantic import Field

from extensions.schemas import AbstractBaseSchema, BaseSchema, PaginationBaseSchema


class PolymerRheologySchema(AbstractBaseSchema):
    """流变属性"""
    
    id: Optional[int] = Field(None, description="流变属性ID")
    # Cross-WLF 模型参数
    model_type: str = Field(default="cross_wlf", description="粘度模型")
    cross_wlf_n: Optional[float] = Field(None, description="Cross-WLF n")
    cross_wlf_tau: Optional[float] = Field(None, description="Cross-WLF tau [Pa]")
    cross_wlf_d1: Optional[float] = Field(None, description="Cross-WLF D1 [Pa·s]")
    cross_wlf_d2: Optional[float] = Field(None, description="Cross-WLF D2 [K]")
    cross_wlf_d3: Optional[float] = Field(None, description="Cross-WLF D3 [K/Pa]")
    cross_wlf_a1: Optional[float] = Field(None, description="Cross-WLF A1")
    cross_wlf_a2: Optional[float] = Field(None, description="Cross-WLF A2 [K]")
    c1: Optional[float] = Field(None, description="接合点损失法c1 [Pa^(1-c2)]")
    c2: Optional[float] = Field(None, description="接合点损失法c2")
    transition_temp: Optional[float] = Field(None, description="转换温度 [℃]")
    viscosity_index: Optional[str] = Field(None, description="粘度指数")
    mfr_temp: Optional[float] = Field(None, description="MFR测试温度 [℃]")
    mfr_load: Optional[float] = Field(None, description="MFR载荷 [kg]")
    mfr_value: Optional[float] = Field(None, description="MFR值 [g/10min]")


class PolymerPVTSchema(AbstractBaseSchema):
    """PVT 属性"""
    
    id: Optional[int] = Field(None, description="PVT 属性ID")
    tait_b5: Optional[float] = Field(None, description="Tait b5 [K]")
    tait_b6: Optional[float] = Field(None, description="Tait b6 [K/Pa]")
    tait_b1m: Optional[float] = Field(None, description="Tait b1m [m³/kg]")
    tait_b2m: Optional[float] = Field(None, description="Tait b2m [m³/kg·K]")
    tait_b3m: Optional[float] = Field(None, description="Tait b3m [Pa]")
    tait_b4m: Optional[float] = Field(None, description="Tait b4m [1/k]")
    tait_b1s: Optional[float] = Field(None, description="Tait b1s [m³/kg]")
    tait_b2s: Optional[float] = Field(None, description="Tait b2s [m³/kg·K]")
    tait_b3s: Optional[float] = Field(None, description="Tait b3s [Pa]")
    tait_b4s: Optional[float] = Field(None, description="Tait b4s [1/K]")
    tait_b7: Optional[float] = Field(None, description="Tait b7 [m³/kg]")
    tait_b8: Optional[float] = Field(None, description="Tait b8 [1/K]")
    tait_b9: Optional[float] = Field(None, description="Tait b9 [1/Pa]")


class PolymerMechanicalSchema(AbstractBaseSchema):
    """机械属性"""
    
    id: Optional[int] = Field(None, description="机械属性ID")
    elastic_modulus_1: Optional[float] = Field(None, description="弹性模量E1 [MPa]")
    elastic_modulus_2: Optional[float] = Field(None, description="弹性模量E2 [MPa]")
    poisson_v12: Optional[float] = Field(None, description="泊松比v12 [1/K]")
    poisson_v23: Optional[float] = Field(None, description="泊松比v23 [1/K]")
    shear_modulus_g12: Optional[float] = Field(None, description="剪切模量G12 [MPa]")
    thermal_expansion_1: Optional[float] = Field(None, description="热膨胀系数α1 [1/K]")
    thermal_expansion_2: Optional[float] = Field(None, description="热膨胀系数α2 [1/K]")


class PolymerShrinkageSchema(AbstractBaseSchema):
    """收缩属性"""
    
    id: Optional[int] = Field(None, description="ID")
    ave_h_shrink: Optional[float] = Field(None, description="平均水平收缩率 [%]")
    ave_v_shrink: Optional[float] = Field(None, description="平均垂直收缩率 [%]")
    min_h_shrink: Optional[float] = Field(None, description="最小水平收缩率 [%]")
    max_h_shrink: Optional[float] = Field(None, description="最大水平收缩率 [%]")
    min_v_shrink: Optional[float] = Field(None, description="最小垂直收缩率 [%]")
    max_v_shrink: Optional[float] = Field(None, description="最大垂直收缩率 [%]")


class FillerSchema(BaseSchema):
    """填充物属性"""
    
    name: Optional[str] = Field(None, description="名称")
    abbreviation: Optional[str] = Field(None, description="缩写")
    # --- 关键分类与形态 ---
    category: Optional[str] = Field(None, description="类别")
    shape: Optional[str] = Field(None, description="形状")
    # --- 关键工艺相关参数 ---
    particle_size_d50: Optional[float] = Field(None, description="中位粒径 D50 [μm]")
    aspect_ratio: Optional[float] = Field(None, description="长径比")
    moisture_content: Optional[float] = Field(None, description="含水率 [%]")
    surface_treatment: Optional[str] = Field(None, description="表面处理")
    # --- 关键物理性能（用于质量控制） ---
    density: Optional[float] = Field(None, description="密度 [g/cm³]")
    thermal_stability_temp: Optional[float] = Field(None, description="热稳定温度 [℃]")
    color: Optional[str] = Field(None, description="颜色")


class PolymerSchema(BaseSchema):
    """塑料材料主数据"""
    
    # --- 基本信息 ---
    abbreviation: Optional[str] = Field(None, description="缩写，如：ABS、PP")
    grade: Optional[str] = Field(None, description="牌号，聚丙烯 Grade PP-H040")
    manufacturer: Optional[str] = Field(None, description="制造商")
    category: Optional[str] = Field(None, description="类别，如：结晶型、无定形")
    series: Optional[str] = Field(None, description="系列，如：高抗冲")
    data_source: Optional[str] = Field(None, description="数据来源，如：客户、供应商、内部")
    data_status: Optional[str] = Field(None, description="数据状态，如：正常、测试、归档")
    internal_id: Optional[str] = Field(None, description="内部编号，如：PP-H040")
    level_code: Optional[str] = Field(None, description="等级代码")
    vendor_code: Optional[str] = Field(None, description="供应商代码")
    # --- 工艺信息 ---
    melt_density: Optional[float] = Field(None, description="熔体密度 [g/cm³]")
    solid_density: Optional[float] = Field(None, description="固体密度 [g/cm³]")
    min_melt_temp: Optional[float] = Field(None, description="最小熔体温度 [℃]")
    max_melt_temp: Optional[float] = Field(None, description="最大熔体温度 [℃]")
    recommended_melt_temp: Optional[float] = Field(None, description="推荐熔体温度 [℃]")
    min_mold_temp: Optional[float] = Field(None, description="最小模具温度 [℃]")
    max_mold_temp: Optional[float] = Field(None, description="最大模具温度 [℃]")
    recommended_mold_temp: Optional[float] = Field(None, description="推荐模具温度 [℃]")
    min_shear_line_speed: Optional[float] = Field(None, description="最小剪切线速度 [mm/s]")
    max_shear_line_speed: Optional[float] = Field(None, description="最大剪切线速度 [mm/s]")
    recommended_shear_line_speed: Optional[float] = Field(None, description="推荐剪切线速度 [mm/s]")
    degradation_temp: Optional[float] = Field(None, description="降级温度 [℃]")
    ejection_temp: Optional[float] = Field(None, description="顶出温度 [℃]")
    barrel_residence_time: Optional[float] = Field(None, description="料筒滞留时间 [min]")
    max_shear_rate: Optional[float] = Field(None, description="最大剪切速率 [1/s]")
    max_shear_stress: Optional[float] = Field(None, description="最大剪切应力 [MPa]")
    recommend_injection_rate: Optional[float] = Field(None, description="推荐注塑速率 [cm³/s]")
    recommend_back_pressure: Optional[float] = Field(None, description="推荐背压 [MPa]")
    drying_method: Optional[str] = Field(None, description="干燥方式")
    drying_temp_min: Optional[float] = Field(None, description="干燥温度下限 [℃]")
    drying_temp_max: Optional[float] = Field(None, description="干燥温度上限 [℃]")
    drying_time_min: Optional[float] = Field(None, description="干燥时间下限 [min]")
    drying_time_max: Optional[float] = Field(None, description="干燥时间上限 [min]")
    # --- 填充物组成 ---
    polymer_filler_compositions: Optional[Dict[str, Any]] = Field(None, description="填充物组成")
    # --- 嵌套属性 ---
    rheology: Optional[PolymerRheologySchema] = Field(None, description="流变属性")
    pvt: Optional[PolymerPVTSchema] = Field(None, description="PVT 属性")
    mechanical: Optional[PolymerMechanicalSchema] = Field(None, description="机械属性")
    shrinkage: Optional[PolymerShrinkageSchema] = Field(None, description="收缩属性")


class FillerListSchema(PaginationBaseSchema):
    """填充物列表"""
    
    name: Optional[str] = Field(None, description="名称")
    category: Optional[str] = Field(None, description="类别")
    shape: Optional[str] = Field(None, description="形状")
    color: Optional[str] = Field(None, description="颜色")
    abbreviation: Optional[str] = Field(None, description="缩写")


class PolymerListSchema(PaginationBaseSchema):
    """塑料列表"""
    
    abbreviation: Optional[str] = Field(None, description="缩写")
    grade: Optional[str] = Field(None, description="牌号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    category: Optional[str] = Field(None, description="类别")
    data_source: Optional[str] = Field(None, description="数据来源")
    level_code: Optional[str] = Field(None, description="等级代码")
    vendor_code: Optional[str] = Field(None, description="供应商代码")