from extensions.models import AbstractBaseModel, BusinessBaseModel
from django.db import models


class Mold(BusinessBaseModel):
    """模具信息"""
    # --- 元状态信息 ---
    project = models.ForeignKey(
        "masterdata.Project",
        null=True,
        on_delete=models.SET_NULL,
        related_name="molds",
        verbose_name="项目信息"
    )
    status = models.CharField(null=True, max_length=20, verbose_name="模具状态")
    
    # --- 基本信息 ---
    mold_no = models.CharField(max_length=50, verbose_name="模具编号")
    mold_name = models.CharField(null=True, max_length=256, verbose_name="模具名称")
    mold_type = models.CharField(null=True, max_length=50, verbose_name="工艺类别：注塑、冲压等")
    category = models.CharField(null=True, max_length=50, verbose_name="应用场景：汽车、医疗等")
    structure = models.CharField(null=True, max_length=50, verbose_name="开合结构：两板模、三板模等")
    shot_count = models.IntegerField(null=True, verbose_name="注射次数（多色成型）1=单次注射，2=两次注射")
    cavity_layout = models.CharField(null=True, max_length=50, verbose_name="模腔布局", help_text="如：1x1,2x2，1+1， A+B+C等")
    cavity_count = models.SmallIntegerField(null=True, verbose_name="型腔数量", help_text="用于快速筛选和统计")
    target_cycle_time = models.FloatField(null=True, verbose_name="目标成型周期 [s]", help_text="模具设计或工艺规划阶段设定的理想周期时间")
    recommended_tonnage = models.PositiveIntegerField(null=True, verbose_name="推荐注塑机吨位 [Ton]", help_text="单位：吨（T），指推荐使用的注塑机锁模力")
    total_injection_weight = models.FloatField(null=True, verbose_name="总注射重量 [g]", help_text="单位：克（g），指总注射重量")
    
    # --- 辅助装置 ---
    mechanism = models.CharField(null=True, max_length=50, verbose_name="动作机构：转盘、侧抽等")
    special_processes = models.JSONField(null=True, verbose_name="特殊加工：如：加压、压延、压延等", help_text="例如：[ '加压', '氮气注射' ]")
    
    # --- 产品分类 ---
    product_category = models.CharField(null=True, max_length=50, verbose_name="产品大类（空调、洗衣机）")
    product_subcategory = models.CharField(null=True, max_length=50, verbose_name="产品中类（柜机、挂机）")
    product_model = models.CharField(null=True, max_length=50, verbose_name="产品小类（具体型号）")
    product_description = models.TextField(null=True, verbose_name="产品描述")
    
    # --- 模具外形尺寸&重量 ---
    mold_length = models.FloatField(
        null=True, 
        verbose_name="模具长度 [mm]",
        help_text="垂直于开合模方向，对于卧式注塑机，通常为左右尺寸，对应拉杆水平排布方向，坐标系中为 X 轴"
    )
    mold_width = models.FloatField(
        null=True, 
        verbose_name="模具宽度 [mm]",
        help_text="垂直于开合模方向，对于卧式注塑机，通常为上下尺寸，对应拉杆垂直排布方向，坐标系中为 Y 轴"
    )
    mold_thickness = models.FloatField(
        null=True, 
        verbose_name="模具厚度 [mm]",
        help_text="垂直于开合模方向，对于卧式注塑机，通常为上下尺寸，对应拉杆轴线延伸方向，坐标系中为 Z 轴"
    )
    mold_weight = models.FloatField(null=True, verbose_name="模具重量 [kg]")
    
    # --- 浇注系统（外键关联）---
    # 通过 CastingSystem.mold 关联，反向使用 Mold.gating_systems 获取
    
    # --- 冷却系统（外键关联）---
        
    # --- 顶出系统（外键关联）---
    
    # --- 吊装结构 ---
    handling_type = models.CharField(null=True, max_length=20, verbose_name="吊装类型")
    handling_thread_size = models.CharField(null=True, max_length=20, default="M16", verbose_name="吊装螺纹规格")
    handling_thread_depth = models.FloatField(null=True, verbose_name="吊装螺孔深度 [mm]", help_text="建议 ≥1.5倍螺纹直径")
    handling_point_count = models.PositiveSmallIntegerField(null=True, verbose_name="吊装点数量")
    handling_position = models.CharField(null=True, max_length=50, verbose_name="吊装点位置", help_text="如：四角、X方向中点")

    # --- 定位圈 ---
    locating_ring_outer_dia = models.FloatField(null=True, verbose_name="定位圈外径 [mm]")
    locating_ring_inner_dia = models.FloatField(null=True, verbose_name="定位圈内径 [mm]")
    locating_ring_height = models.FloatField(null=True, verbose_name="定位圈高度 [mm]")
    locating_ring_material = models.CharField(null=True, max_length=50, verbose_name="定位圈材质")
    locating_ring_standard = models.CharField(null=True, max_length=50, verbose_name="定位圈标准")
    mov_half_locating_ring_outer_dia = models.FloatField(null=True, verbose_name="动模定位圈外径 [mm]")
    mov_half_locating_ring_inner_dia = models.FloatField(null=True, verbose_name="动模定位圈内径 [mm]")
    mov_half_locating_ring_height = models.FloatField(null=True, verbose_name="动模定位圈高度 [mm]")
    
    # --- 导向与定位结构 ---
    guide_pin_diameter = models.FloatField(null=True, verbose_name="导柱直径 [mm]", help_text="如 φ25, φ30")
    guide_pin_count = models.PositiveSmallIntegerField(null=True, verbose_name="导柱数量", help_text="通常4根，大型模6~8根")
    has_precision_locator = models.BooleanField(null=True, default=False, verbose_name="是否有精定位", help_text="用于高精度或大型模具")
    locator_type = models.CharField(null=True, max_length=20, verbose_name="精定位类型")
    locator_position = models.CharField(null=True, max_length=50, verbose_name="精定位位置", help_text="如：四角、长边中点")
    
    # --- 开模与锁模 ---
    part_removal_action = models.CharField(null=True, max_length=50, verbose_name="取件方式")
    runner_separation_distance = models.FloatField(null=True, verbose_name="流道分离距离 [mm]", help_text="流道与定模分离所需的开模距离")
    recommended_opening_stroke = models.FloatField(null=True, verbose_name="所需开模行程 [mm]", help_text="产品脱模所需最小开距")
    min_clamping_force = models.FloatField(
        null=True,
        verbose_name="最小锁模力 [ton]", 
        help_text="""
        防止涨模所需的最小锁模力
        F = A × P

        F：锁模力 [ton]
        A：产品在分型面上的投影面积 [cm²]
        P：型腔压力 [kgf/cm²]，通常取 300~500 kgf/cm²（30~50 MPa）
        """
    )
    wbs = models.CharField(null=True, max_length=50, verbose_name="WBS")
    
    class Meta:
        verbose_name = "模具信息"
        verbose_name_plural = "模具信息"
        ordering = ['-created_at']


class GatingSystem(AbstractBaseModel):
    """模具浇注系统信息"""
    mold = models.ForeignKey(
        "masterdata.Mold",
        on_delete=models.CASCADE,
        related_name="gating_systems",
        verbose_name="所属模具"
    )
    
    # --- 流道类型 ---
    runner_type = models.CharField(null=True, max_length=50, verbose_name="流道类型")
    total_product_weight = models.FloatField(null=True, verbose_name="产品总重量 [g]")
    
    # --- 热流道系统（热流道 & 热转冷） ---
    hot_runner_supplier = models.CharField(null=True, max_length=50, verbose_name="热流道供应商")
    hot_runner_system_type = models.CharField(null=True, max_length=100, verbose_name="热流道类型")
    hot_runner_manifold_zones = models.IntegerField(null=True, verbose_name="分流板温控区数")
    hot_runner_nozzle_count = models.IntegerField(null=True, verbose_name="热喷嘴数量")

    has_sequencing_control = models.BooleanField(null=True, verbose_name="是否有序流控制")
    sequencing_control_method = models.CharField(null=True, max_length=50, verbose_name="时序控制方式")
    valve_actuation_type = models.CharField(null=True, max_length=150, verbose_name="针阀驱动方式")
    
    # --- 主流道衬套（冷流道 & 热转冷） ---
    runner_weight = models.FloatField(null=True, verbose_name="主流道重量 [g]")
    runner_length = models.FloatField(null=True, verbose_name="主流道长度 [mm]")
    sprue_bushing_outer_dia = models.FloatField(null=True, verbose_name="衬套外径 D1 [mm]")
    sprue_bushing_bore_dia = models.FloatField(null=True, verbose_name="衬套孔径 D2 [mm]")
    sprue_bushing_radius = models.FloatField(null=True, verbose_name="球面半径 R [mm]")
    sprue_bushing_angle = models.FloatField(null=True, verbose_name="密封锥角 θ [°]")
    sprue_bushing_material = models.CharField(null=True, max_length=50, verbose_name="主流道衬套材质")
    sprue_bushing_standard = models.CharField(null=True, max_length=50, verbose_name="主流道衬套标准")
    
    # --- 工艺相关参数 ---
    estimated_shot_weight = models.FloatField(null=True, verbose_name="注射重量 [g]")
    estimated_runner_weight = models.FloatField(null=True, verbose_name="流道重量 [g]")
    projected_area = models.FloatField(null=True, verbose_name="投影面积 [cm²]")

    class Meta:
        verbose_name = "浇注系统"
        verbose_name_plural = "浇注系统"


class Cavity(AbstractBaseModel):
    """型腔信息"""
    gating_system = models.ForeignKey(
        "masterdata.GatingSystem",
        on_delete=models.CASCADE,
        related_name="cavities",
        verbose_name="所属浇注系统"
    )
    
    # --- 数量：这类型腔的数量 ---
    cavity_count_per_shot = models.IntegerField(
        null=True,
        default=1, 
        verbose_name="型腔数量",
        help_text="本次注射时，该类型产品的型腔数量"
    )

    # --- 制品名称 ---
    product_name = models.CharField(null=True, max_length=150, verbose_name="制品名称")
    product_code = models.CharField(null=True, max_length=150, verbose_name="制品编号")

    # --- 制品关键工艺参数 ---
    max_flow_length = models.FloatField(null=True, verbose_name="最大流动长度 [mm]")
    ave_wall_thickness = models.FloatField(null=True, verbose_name="平均壁厚 [mm]")
    min_wall_thickness = models.FloatField(null=True, verbose_name="最小壁厚 [mm]")
    max_wall_thickness = models.FloatField(null=True, verbose_name="最大壁厚 [mm]")
    projected_area_per_cavity = models.FloatField(null=True, verbose_name="单腔投影面积 [mm²]")
    estimated_weight_per_cavity = models.FloatField(null=True, verbose_name="单腔制品预估重量 [g]")

    # --- 可计算特征 ---
    flow_ratio = models.FloatField(null=True, verbose_name="L/t 比", help_text="流动长度 / 平均壁厚")
    thickness_variation = models.FloatField(null=True, verbose_name="壁厚变化率", help_text="(最大 - 最小) / 平均")

    class Meta:
        verbose_name = "型腔信息"
        verbose_name_plural = "型腔信息"


class Gate(AbstractBaseModel):
    """浇口特征定义，直接关联到具体型腔"""
    cavity = models.ForeignKey(
        "masterdata.Cavity",
        on_delete=models.CASCADE,
        related_name="gates",
        verbose_name="所属型腔"
    )
    
    gate_shape = models.CharField(null=True, max_length=20, verbose_name="浇口形状")
    gate_type = models.CharField(null=True, max_length=100, verbose_name="浇口类型")
    gate_count = models.IntegerField(
        null=True,
        default=1, 
        verbose_name="浇口数量",
        help_text="该型腔使用此类型浇口的数量"
    )
    
    location_description = models.CharField(
        null=True, 
        max_length=100, 
        verbose_name="浇口位置描述",
        help_text="如：顶面中心、侧面距边缘10mm处、底面边缘20mm处"
    )
    # --- 关键尺寸（分别定义） ---
    # 矩形类
    length = models.FloatField(null=True, verbose_name="长度 [mm]")
    width = models.FloatField(null=True, verbose_name="宽度 [mm]")
    # 圆形类
    diameter = models.FloatField(null=True, verbose_name="直径 [mm]")
    # 梯形类
    top_length = models.FloatField(null=True, verbose_name="顶边长度 [mm]")
    bottom_length = models.FloatField(null=True, verbose_name="底边长度 [mm]")
    height = models.FloatField(null=True, verbose_name="高度 [mm]")
    # 环形类
    outer_diameter = models.FloatField(null=True, verbose_name="外径 [mm]")
    inner_diameter = models.FloatField(null=True, verbose_name="内径 [mm]")
    gap = models.FloatField(null=True, verbose_name="间隔 [mm]")
    
    class Meta:
        verbose_name = "浇口信息"
        verbose_name_plural = "浇口信息"


class CoolingSystem(AbstractBaseModel):
    """模具冷却系统信息"""
    mold = models.OneToOneField(
        "masterdata.Mold",
        on_delete=models.CASCADE,
        related_name="cooling_system"
    )
    
    cooling_cavity_type = models.CharField(null=True, max_length=50, verbose_name="型腔冷却类型")
    cooling_cavity_circuit_count = models.SmallIntegerField(null=True, verbose_name="型腔冷却回路数量")
    cooling_cavity_layout = models.CharField(null=True, max_length=50, verbose_name="型腔冷却布局")
    cooling_cavity_pipe_diameter = models.FloatField(null=True, verbose_name="型腔冷却管径 [mm]")
    cooling_cavity_fitting_type = models.CharField(null=True, max_length=50, verbose_name="型腔冷却管连接器类型")
    cooling_cavity_fitting_count = models.SmallIntegerField(null=True, verbose_name="型腔冷却管连接器数量")
    cooling_cavity_fitting_labels = models.CharField(
        null=True, 
        max_length=50, 
        verbose_name="型腔冷却管连接器标签",
        help_text="例如：C1,C2,C3（用于标识回路）"
    )
    cooling_cavity_fitting_seal_method = models.CharField(null=True, max_length=50, verbose_name="型腔水嘴密封方式")
    
    cooling_core_type = models.CharField(null=True, max_length=50, verbose_name="型芯冷却类型")
    cooling_core_circuit_count = models.SmallIntegerField(null=True, verbose_name="型芯冷却回路数量")
    cooling_core_layout = models.CharField(null=True, max_length=50, verbose_name="型芯冷却布局")
    cooling_core_pipe_diameter = models.FloatField(null=True, verbose_name="型芯冷却管径 [mm]")
    cooling_core_fitting_type = models.CharField(null=True, max_length=50, verbose_name="型芯冷却管连接器类型")
    cooling_core_fitting_count = models.SmallIntegerField(null=True, verbose_name="型芯冷却管连接器数量")
    cooling_core_fitting_labels = models.CharField(
        null=True, 
        max_length=50, 
        verbose_name="型芯冷却管连接器标签",
        help_text="例如：C1,C2,C3（用于标识回路）"
    )
    cooling_core_fitting_seal_method = models.CharField(null=True, max_length=50, verbose_name="型芯水嘴密封方式")

    class Meta:
        verbose_name = "冷却系统信息"
        verbose_name_plural = "冷却系统信息"
    

class EjectionSystem(AbstractBaseModel):
    """模具顶出系统信息"""
    mold = models.OneToOneField(
        "masterdata.Mold",
        on_delete=models.CASCADE,
        related_name="ejection_system"
    )
    
    ejection_type = models.CharField(null=True, max_length=100, verbose_name="顶出类型")
    reset_method = models.CharField(null=True, max_length=100, verbose_name="复位方式")
    ejector_rod_hole_type = models.CharField(null=True, max_length=20, verbose_name="顶棍孔类型")
    ejector_rod_hole_diameter = models.FloatField(
        null=True, 
        verbose_name="顶棍孔直径 [mm]",
        help_text="单个孔的直径，建议比顶棍大0.2~0.5mm"
    )
    ejector_rod_hole_depth = models.FloatField(
        null=True, 
        verbose_name="顶棍孔深度 [mm]",
        help_text="从尾板表面到孔底的距离"
    )
    ejector_rod_hole_spacing_x = models.FloatField(
        null=True, 
        verbose_name="顶棍孔x向间隔 [mm]",
        help_text="四点分布时，左右孔之间的距离"
    )
    ejector_rod_hole_spacing_y = models.FloatField(
        null=True, 
        verbose_name="顶棍孔y向间隔 [mm]",
        help_text="四点分布时，上下孔之间的距离"
    )
    ejection_stroke = models.FloatField(null=True, verbose_name="顶出行程 [mm]")
    has_pre_ejection = models.BooleanField(null=True, verbose_name="是否有预顶出")
    pre_ejection_stroke = models.FloatField(null=True, verbose_name="预顶出行程 [mm]")
    estimated_ejection_force = models.FloatField(
        null=True, 
        verbose_name="预估顶出力 [kgf]",
        help_text="""
        # 包紧力估算（主要来源）
        F = P × A × μ

        F：顶出力 [kgf]
        P：包紧压力 [MPa]，经验取 8~12 MPa（ABS/PC 取 10）
        A：塑件与型芯的侧向投影面积 [cm²]
        μ：摩擦系数，ABS ≈ 0.3~0.4，PP ≈ 0.2

        # 示例：ABS 壳体，投影面积 50 cm²
        F = 10 MPa × 50 cm² × 0.35 = 175 kgf
        """
    )
    
    class Meta:
        verbose_name = "顶出系统信息"
        verbose_name_plural = "顶出系统信息"
