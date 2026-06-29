from extensions.models import TracedModel, BusinessBaseModel, AbstractBaseModel
from django.db import models


class Polymer(BusinessBaseModel):
    """塑料材料主数据"""
    # --- 基本信息 ---
    abbreviation = models.CharField(null=True, max_length=50, verbose_name="缩写", help_text="如：ABS、PP")
    grade = models.CharField(null=True, max_length=100, verbose_name="牌号", help_text="聚丙烯 Grade PP-H040")
    manufacturer = models.CharField(null=True, max_length=100, verbose_name="制造商")
    category = models.CharField(null=True, max_length=50, verbose_name="类别", help_text="如：结晶型、无定形")
    series = models.CharField(null=True, max_length=50, verbose_name="系列", help_text="如：高抗冲")
    data_source = models.CharField(null=True, max_length=50, verbose_name="数据来源", help_text="如：客户、供应商、内部")
    data_status = models.CharField(null=True, max_length=50, verbose_name="数据状态", help_text="如：正常、测试、归档")
    internal_id = models.CharField(null=True, max_length=50, verbose_name="内部编号", help_text="如：PP-H040")
    level_code = models.CharField(null=True, max_length=50, verbose_name="等级代码")
    vendor_code = models.CharField(null=True, max_length=50, verbose_name="供应商代码")
    
    # --- 工艺信息 ---
    melt_density = models.FloatField(null=True, verbose_name="熔体密度 [g/cm³]")
    solid_density = models.FloatField(null=True, verbose_name="固体密度 [g/cm³]")

    min_melt_temp = models.FloatField(null=True, verbose_name="最小熔体温度 [℃]")
    max_melt_temp = models.FloatField(null=True, verbose_name="最大熔体温度 [℃]")
    recommended_melt_temp = models.FloatField(null=True, verbose_name="推荐熔体温度 [℃]")
    
    min_mold_temp = models.FloatField(null=True, verbose_name="最小模具温度 [℃]")
    max_mold_temp = models.FloatField(null=True, verbose_name="最大模具温度 [℃]")
    recommended_mold_temp = models.FloatField(null=True, verbose_name="推荐模具温度 [℃]")
    
    min_shear_line_speed = models.FloatField(null=True, verbose_name="最小剪切线速度 [mm/s]")
    max_shear_line_speed = models.FloatField(null=True, verbose_name="最大剪切线速度 [mm/s]")
    recommended_shear_line_speed = models.FloatField(null=True, verbose_name="推荐剪切线速度 [mm/s]")
    
    degradation_temp = models.FloatField(null=True, verbose_name="降解温度 [℃]")
    ejection_temp = models.FloatField(null=True, verbose_name="顶出温度 [℃]")
    barrel_residence_time = models.FloatField(null=True, verbose_name="料筒滞留时间 [min]")
    max_shear_rate = models.FloatField(null=True, verbose_name="最大剪切速率 [1/s]")
    max_shear_stress = models.FloatField(null=True, verbose_name="最大剪切应力 [MPa]")
    
    recommend_injection_rate = models.FloatField(null=True, verbose_name="推荐注塑速率 [cm³/s]")
    recommend_back_pressure = models.FloatField(null=True, verbose_name="推荐背压 [MPa]")

    drying_method = models.CharField(null=True, max_length=50, verbose_name="干燥方式", help_text="如：热风干燥、真空干燥")
    drying_temp_min = models.FloatField(null=True, verbose_name="干燥温度下限 [℃]")
    drying_temp_max = models.FloatField(null=True, verbose_name="干燥温度上限 [℃]")
    drying_time_min = models.FloatField(null=True, verbose_name="干燥时间下限 [min]")
    drying_time_max = models.FloatField(null=True, verbose_name="干燥时间上限 [min]")
    
    # --- 填充物组成 ---
    polymer_filler_composition = models.JSONField(null=True, verbose_name="填充物组成")
    
    class Meta:
        verbose_name = "常用材料信息"
        verbose_name_plural = "常用材料信息"


class PolymerRheology(AbstractBaseModel):
    """流变属性"""
    polymer = models.OneToOneField(
        "masterdata.Polymer", 
        related_name="rheology",
        on_delete=models.CASCADE
    )
    
    VISCOSITY_MODELS = [
        ('cross_wlf', 'Cross-WLF'),
    ]
    model_type = models.CharField(
        verbose_name="粘度模型", 
        null=True, 
        max_length=50, 
        choices=VISCOSITY_MODELS, 
        default="cross_wlf"
    )
    
    # Cross-WLF 模型参数
    cross_wlf_n = models.FloatField(null=True, verbose_name="Cross-WLF n")
    cross_wlf_tau = models.FloatField(null=True, verbose_name="Cross-WLF tau [Pa]")
    cross_wlf_d1 = models.FloatField(null=True, verbose_name="Cross-WLF D1 [Pa·s]")
    cross_wlf_d2 = models.FloatField(null=True, verbose_name="Cross-WLF D2 [K]")
    cross_wlf_d3 = models.FloatField(null=True, verbose_name="Cross-WLF D3 [K/Pa]")
    cross_wlf_a1 = models.FloatField(null=True, verbose_name="Cross-WLF A1")
    cross_wlf_a2 = models.FloatField(null=True, verbose_name="Cross-WLF A2 [K]")
    
    c1 = models.FloatField(null=True, verbose_name="接合点损失法c1 [Pa^(1-c2)]")
    c2 = models.FloatField(null=True, verbose_name="接合点损失法c2")
    
    transition_temp = models.FloatField(null=True, verbose_name="转换温度 [℃]")
    viscosity_index = models.CharField(
        max_length=45, null=True, blank=True, 
        verbose_name="粘度指数", 
        help_text="如：高、中、低"
    )
    
    mfr_temp = models.FloatField(null=True, verbose_name="MFR测试温度 [℃]")
    mfr_load = models.FloatField(null=True, verbose_name="MFR载荷 [kg]")
    mfr_value = models.FloatField(null=True, verbose_name="MFR值 [g/10min]")
    
    class Meta:
        verbose_name = "流变属性"
        verbose_name_plural = "流变属性"


class PolymerPVT(AbstractBaseModel):
    """PVT 属性"""
    polymer = models.OneToOneField(
        "masterdata.Polymer", 
        related_name="pvt",
        on_delete=models.CASCADE
    )
    
    tait_b5 = models.FloatField(null=True, verbose_name="Tait b5 [K]")
    tait_b6 = models.FloatField(null=True, verbose_name="Tait b6 [K/Pa]")
    tait_b1m = models.FloatField(null=True, verbose_name="Tait b1m [m³/kg]")
    tait_b2m = models.FloatField(null=True, verbose_name="Tait b2m [m³/kg·K]")
    tait_b3m = models.FloatField(null=True, verbose_name="Tait b3m [Pa]")
    tait_b4m = models.FloatField(null=True, verbose_name="Tait b4m [1/k]")
    tait_b1s = models.FloatField(null=True, verbose_name="Tait b1s [m³/kg]")
    tait_b2s = models.FloatField(null=True, verbose_name="Tait b2s [m³/kg·K]")
    tait_b3s = models.FloatField(null=True, verbose_name="Tait b3s [Pa]")
    tait_b4s = models.FloatField(null=True, verbose_name="Tait b4s [1/K]")
    tait_b7 = models.FloatField(null=True, verbose_name="Tait b7 [m³/kg]")
    tait_b8 = models.FloatField(null=True, verbose_name="Tait b8 [1/K]")
    tait_b9 = models.FloatField(null=True, verbose_name="Tait b9 [1/Pa]")
    
    class Meta:
        verbose_name = "PVT 属性"
        verbose_name_plural = "PVT 属性"
        

class PolymerMechanical(AbstractBaseModel):
    """机械属性"""
    polymer = models.OneToOneField(
        "masterdata.Polymer", 
        related_name="mechanical",
        on_delete=models.CASCADE
    )
    
    elastic_modulus_1 = models.FloatField(null=True, verbose_name="弹性模量E1 [MPa]")
    elastic_modulus_2 = models.FloatField(null=True, verbose_name="弹性模量E2 [MPa]")
    poisson_v12 = models.FloatField(null=True, verbose_name="泊松比v12 [1/K]", help_text="横向变形系数")
    poisson_v23 = models.FloatField(null=True, verbose_name="泊松比v23 [1/K]", help_text="厚度方向变形系数")
    shear_modulus_g12 = models.FloatField(null=True, verbose_name="剪切模量G12 [MPa]")
    thermal_expansion_1 = models.FloatField(null=True, verbose_name="热膨胀系数α1 [1/K]")
    thermal_expansion_2 = models.FloatField(null=True, verbose_name="热膨胀系数α2 [1/K]")
    
    class Meta:
        verbose_name = "机械属性"
        verbose_name_plural = "机械属性"


class PolymerShrinkage(AbstractBaseModel):
    """收缩属性"""
    polymer = models.OneToOneField(
        "masterdata.Polymer", 
        related_name="shrinkage",
        on_delete=models.CASCADE
    )
    
    ave_h_shrink = models.FloatField(null=True, verbose_name="平均水平收缩率 [%]")
    ave_v_shrink = models.FloatField(null=True, verbose_name="平均垂直收缩率 [%]")
    min_h_shrink = models.FloatField(null=True, verbose_name="最小水平收缩率 [%]")
    max_h_shrink = models.FloatField(null=True, verbose_name="最大水平收缩率 [%]")
    min_v_shrink = models.FloatField(null=True, verbose_name="最小垂直收缩率 [%]")
    max_v_shrink = models.FloatField(null=True, verbose_name="最大垂直收缩率 [%]")
    
    class Meta:
        verbose_name = "收缩属性"
        verbose_name_plural = "收缩属性"


class Filler(BusinessBaseModel):
    """
    填充物属性
    如：玻璃纤维、滑石粉、碳酸钙等
    # TODO: 考虑moldflow 的填充物属性
    """
    name = models.CharField(
        null=True, 
        max_length=50, 
        verbose_name="名称", 
        help_text="如：玻璃纤维、滑石粉、碳酸钙等"
    )
    abbreviation = models.CharField(
        null=True, 
        max_length=50, 
        verbose_name="缩写",
        help_text="如：GF, TALC, CaCO₃"
    )
    
    # --- 关键分类与形态 ---
    category = models.CharField(
        null=True, 
        max_length=50, 
        verbose_name="类别", 
        help_text="如：无机填充、增强纤维"
    )
    shape = models.CharField(
        null=True, 
        max_length=50,
        verbose_name="形状",
        choices=[
            ('spherical', '球形'),
            ('platelet', '片状'),
            ('fibrous', '纤维状'),
            ('irregular', '不规则'),
        ],
        help_text="几何形态"
    )
    
    # --- 关键工艺相关参数 ---
    particle_size_d50 = models.FloatField(
        null=True, blank=True,
        verbose_name="中位粒径 D50 [μm]",
        help_text="影响分散性和表面光洁度"
    )
    aspect_ratio = models.FloatField(
        null=True, blank=True,
        verbose_name="长径比",
        help_text="纤维/片状材料关键参数，影响增强效果"
    )
    moisture_content = models.FloatField(
        null=True, blank=True,
        verbose_name="含水率 [%]",
        help_text="烘干前原始含水率，决定烘干工艺"
    )
    surface_treatment = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="表面处理",
        help_text="如：硅烷偶联剂、硬脂酸处理"
    )

    # --- 关键物理性能（用于质量控制） ---
    density = models.FloatField(
        null=True,
        verbose_name="密度 [g/cm³]",
        help_text="用于配方计算和成本核算"
    )
    thermal_stability_temp = models.FloatField(
        null=True,
        verbose_name="热稳定温度 [℃]",
        help_text="避免加工温度过高导致分解"
    )
    color = models.CharField(
        max_length=30,
        null=True,
        verbose_name="颜色",
        help_text="如：白色、灰色"
    )
    
    class Meta:
        verbose_name = "填充物属性"
        verbose_name_plural = "填充物属性"


# TODO: 色母模型定义完成，待业务需要时启用
# class ColorMasterbatch(BusinessBaseModel):
#     """
#     色母（色母粒）
#     用于塑料着色的高浓度颜料制剂，按推荐比例添加到基体树脂中
#     """
#     # --- 基本信息 ---
#     name = models.CharField(
#         null=True, max_length=100,
#         verbose_name="名称",
#         help_text="如：黑色母 CM-BK-001"
#     )
#     code = models.CharField(
#         null=True, max_length=50,
#         verbose_name="型号",
#         help_text="供应商产品型号"
#     )
#     manufacturer = models.CharField(
#         null=True, max_length=100,
#         verbose_name="供应商"
#     )
#
#     # --- 颜色属性 ---
#     color_name = models.CharField(
#         null=True, max_length=50,
#         verbose_name="颜色名称",
#         help_text="如：钛白、深蓝"
#     )
#     color_type = models.CharField(
#         null=True, max_length=20,
#         verbose_name="着色类型",
#         choices=[
#             ('pigment', '颜料型'),
#             ('dye', '染料型'),
#             ('pearlescent', '珠光型'),
#         ],
#     )
#
#     # --- 工艺参数 ---
#     carrier_resin = models.CharField(
#         null=True, max_length=100,
#         verbose_name="载体树脂",
#         help_text="如：PE、PP、ABS"
#     )
#     recommended_ratio = models.FloatField(
#         null=True,
#         verbose_name="推荐添加比例 [%]",
#         help_text="占基体树脂的质量百分比"
#     )
#     heat_resistance_temp = models.FloatField(
#         null=True,
#         verbose_name="耐热温度 [℃]",
#         help_text="超过会变色/分解"
#     )
#
#     # --- 物理参数 ---
#     density = models.FloatField(
#         null=True,
#         verbose_name="密度 [g/cm³]",
#     )
#     moisture_content = models.FloatField(
#         null=True,
#         verbose_name="含水率 [%]",
#     )
#
#     class Meta:
#         verbose_name = "色母"
#         verbose_name_plural = "色母"

