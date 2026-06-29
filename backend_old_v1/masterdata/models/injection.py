from extensions.models import AbstractBaseModel, BusinessBaseModel
from django.db import models


class InjectionMoldingMachine(BusinessBaseModel):
    """注塑机"""
    # --- 状态信息 ---
    STATUS_CHOICES = [
        ('idle', '空闲'),
        ('running', '运行中'),
        ('maintenance', '维护中'),
        ('offline', '离线'),
        ('fault', '故障'),
    ]
    status = models.CharField(max_length=50, null=True, verbose_name="状态")
    # --- 基本信息 ---
    brand = models.CharField(max_length=50, null=True, verbose_name="品牌")
    model = models.CharField(max_length=50, null=True, verbose_name="设备型号")
    manufacturer = models.CharField(max_length=50, null=True, verbose_name="制造商")
    location = models.CharField(
        max_length=50, 
        null=True,
        verbose_name="位置",
        help_text="如：xx工厂-一车间-注塑区"
    )
    device_no = models.CharField(
        max_length=50, 
        null=True,
        verbose_name="设备编号",
        help_text="如：SN1234567890"
    )
    asset_no = models.CharField(
        max_length=50, 
        null=True,
        verbose_name="资产编号",
        help_text="如：A01"
    )
    machine_type = models.CharField(max_length=50, null=True, verbose_name="设备类型")
    drive_system = models.CharField(max_length=50, null=True, verbose_name="驱动系统")
    unit_count = models.PositiveSmallIntegerField(
        default=1,
        null=True,
        verbose_name="射台数量",
        help_text="如：1=单射台、2=双射台、3=三射台"
    )
    
    # --- 控制器信息 ---
    controller_model = models.CharField(
        max_length=50, 
        null=True,
        verbose_name="控制器型号",
        help_text="如：Fanuc ROBOshot, Engle CC300, SEIKI S-TECH"
    )
    controller_version = models.CharField(
        max_length=50, 
        null=True,
        verbose_name="控制器版本",
        help_text="如：V3.2.1"
    )
    
    # --- 通讯能力 ---
    is_comm_enabled = models.BooleanField(
        default=False,
        null=True,
        verbose_name="是否支持通讯"
    )
    communication_protocol = models.CharField(
        max_length=50,
        null=True,
        choices=[
            ('fanuc_focas', 'FANUC FOCAS'),
            ('opc_ua', 'OPC UA'),
            ('modbus_tcp', 'Modbus TCP'),
            ('profinet', 'Profinet'),
            ('ethercat', 'EtherCAT'),
            ('rs232', 'RS232'),
            ('custom', '厂商私有协议'),
            ('none', '无通讯能力'),
        ],
        verbose_name="通讯协议"
    )
    communication_ip = models.GenericIPAddressField(
        null=True,
        verbose_name="通讯IP",
        help_text="如：192.168.1.100"
    )
    last_comm_time = models.DateTimeField(
        null=True,
        verbose_name="上次通讯时间"
    )
    
    # --- 默认单位系统（由控制器统一设定） ---
    pressure_unit = models.CharField(
        max_length=10,
        null=True,
        default='bar',
        verbose_name="压力单位"
    )
    speed_unit = models.CharField(
        max_length=10,
        null=True,
        default='mm/s',
        verbose_name="速度单位"
    )
    position_unit = models.CharField(
        max_length=10,
        null=True,
        default='mm',
        verbose_name="位置单位"
    )
    time_unit = models.CharField(
        max_length=10,
        null=True,
        default='s',
        verbose_name="时间单位"
    )
    back_pressure_unit = models.CharField(
        max_length=10,
        null=True,
        default='bar',
        verbose_name="背压单位"
    )
    screw_rotation_unit = models.CharField(
        max_length=10,
        null=True,
        default='rpm',
        verbose_name="螺杆转速单位"
    )
    temperature_unit = models.CharField(
        max_length=10,
        null=True,
        default='℃',
        verbose_name="温度单位"
    )
    clamping_force_unit = models.CharField(
        max_length=10,
        null=True,
        default='ton',
        verbose_name="锁模力单位"
    )
    
    # --- 注射单元（外键关联） ---
    # 通过 InjectionUnit.machine 关联，反向使用 InjectionMoldingMachine.injection_units 获取
    
    # --- 模板参数---
    # 定模板
    fixed_platen_width = models.FloatField(null=True, verbose_name="定模板宽度 [mm]")
    fixed_platen_height = models.FloatField(null=True, verbose_name="定模板高度 [mm]")
    fixed_platen_thickness = models.FloatField(null=True, verbose_name="定模板厚度 [mm]")
    locating_hole_diameter = models.FloatField(null=True, verbose_name="定位孔直径 [mm]")
    
    # 动模板
    moving_platen_width = models.FloatField(null=True, verbose_name="动模板宽度 [mm]")
    moving_platen_height = models.FloatField(null=True, verbose_name="动模板高度 [mm]")
    moving_platen_thickness = models.FloatField(null=True, verbose_name="动模板厚度 [mm]")
    
    # --- 拉杆（哥林柱）---
    tie_bar_spacing_width = models.FloatField(null=True, verbose_name="拉杆（格林柱）水平间距 [mm]")
    tie_bar_spacing_height = models.FloatField(null=True, verbose_name="拉杆（格林柱）垂直间距 [mm]")
    tie_bar_diameter = models.FloatField(null=True, verbose_name="拉杆（格林柱）直径 [mm]")
    tie_bar_count = models.IntegerField(
        default=4,
        null=True,
        verbose_name="拉杆（格林柱）数量"
    )
    
    # --- 模板间距（物理极限）---
    min_platen_spacing = models.FloatField(null=True, verbose_name="最小模板间距 [mm]")
    max_platen_spacing = models.FloatField(null=True, verbose_name="最大模板间距 [mm]")
    
    # --- 容模参数（工程推荐） ---
    min_mold_length = models.FloatField(null=True, verbose_name="最小容模水平尺寸 [mm]")
    max_mold_length = models.FloatField(null=True, verbose_name="最大容模水平尺寸 [mm]")
    min_mold_width = models.FloatField(null=True, verbose_name="最小容模垂直尺寸 [mm]")
    max_mold_width = models.FloatField(null=True, verbose_name="最大容模垂直尺寸 [mm]")
    min_mold_thickness = models.FloatField(null=True, verbose_name="最小容模厚度 [mm]")
    max_mold_thickness = models.FloatField(null=True, verbose_name="最大容模厚度 [mm]")
    max_opening_stroke = models.FloatField(null=True, verbose_name="最大开模行程 [mm]")
    
    # --- 锁模性能 ---
    clamping_type = models.CharField(
        max_length=50,
        null=True,
        choices=[
            ('spring', '弹簧锁模'),
            ('hydraulic', '液压锁模'),
            ('servo', '伺服锁模'),
        ],
        verbose_name="锁模类型",
        help_text="锁模机构类型"
    )
    max_clamping_force = models.FloatField(null=True, verbose_name="最大锁模力 [ton]")
    
    # --- 顶出系统---
    ejection_type = models.CharField(
        max_length=50,
        null=True,
        choices=[
            ('hydraulic_rear', '后置液压'),
            ('hydraulic_front', '前置液压'),
            ('mechanical', '机械顶出'),
            ('servo', '伺服顶出'),
        ],
        verbose_name="顶出类型",
        help_text="机器顶出机构类型"
    )
    ejection_mode = models.CharField(
        max_length=50,
        null=True,
        choices=[
            ('single_center', '单中心顶出'),
            ('four_corner_symmetric', '四角对称顶出'),
            ('none', '无自动顶出'),
        ],
        verbose_name="顶出模式",
        help_text="机器顶出机构的工作方式，用于匹配模具顶棍孔分布"
    )
    ejection_stroke = models.FloatField(null=True, verbose_name="顶出行程 [mm]")
    ejection_force = models.FloatField(null=True, verbose_name="顶出力 [kN]")
    
    # --- 尺寸与功率 ---
    size_length = models.FloatField(null=True, verbose_name="机台外形尺寸长 [mm]")
    size_width = models.FloatField(null=True, verbose_name="机台外形尺寸宽 [mm]")
    size_height = models.FloatField(null=True, verbose_name="机台外形尺寸高[mm]")
    machine_weight = models.FloatField(null=True, verbose_name="机台重量 [kg]")
    motor_power = models.FloatField(null=True, verbose_name="电机功率 [kW]")
    heater_power = models.FloatField(null=True, verbose_name="电热功率 [kW]")
    rated_power = models.FloatField(null=True, verbose_name="额定功率 [kW]")
    
    # --- 日期 ---
    manufacture_date = models.DateField(null=True, verbose_name="制造日期")
    commissioning_date = models.DateField(null=True, verbose_name="投产日期")
    
    # --- 其它信息 ---
    class Meta:
        verbose_name = "注塑机信息"
        verbose_name_plural = "注塑机信息"
   

class InjectionUnit(AbstractBaseModel):
    """注射单元"""
    machine = models.ForeignKey(
        "InjectionMoldingMachine",
        on_delete=models.CASCADE,
        related_name="injection_units",
        verbose_name="所属机型"
    )
    
    # --- 射台标识 ---
    unit_code = models.CharField(
        max_length=20, 
        verbose_name="射台编号",
        help_text="如：S000123"
    )
    
    # --- 喷嘴参数 ---
    nozzle_type = models.CharField(
        max_length=50,
        null=True,
        verbose_name="喷嘴类型",
        help_text="如：直通式、倒锥式、针阀式、热流道喷嘴"
    )
    nozzle_protrusion = models.FloatField(
        null=True,
        verbose_name="喷嘴伸出量 [mm]",
        help_text="喷嘴前端超出模具定位环的距离"
    )
    nozzle_hole_diameter = models.FloatField(
        null=True,
        verbose_name="喷嘴孔直径 [mm]",
        help_text="影响料流速度和剪切"
    )
    nozzle_sphere_radius = models.FloatField(
        null=True,
        verbose_name="喷嘴球半径 [mm]",
        help_text="与模具主流道衬套球面配合"
    )
    nozzle_contact_force = models.FloatField(
        null=True,
        verbose_name="喷嘴接触力 [kN]",
        help_text="注射时喷嘴与模具的锁紧力"
    )

    # --- 螺杆参数 ---
    screw_type = models.CharField(
        max_length=50,
        null=True,
        verbose_name="螺杆类型",
        help_text="螺杆规格类别，如通用型、屏障型、混炼型"
    )
    screw_diameter = models.FloatField(
        null=True,
        verbose_name="螺杆直径 [mm]",
        help_text="螺杆外径，影响塑化能力和射胶量"
    )
    screw_length_to_diameter_ratio = models.FloatField(
        null=True,
        verbose_name="长径比 L/D",
        help_text="螺杆有效长度与直径之比，影响塑化均匀性"
    )
    screw_cross_sectional_area = models.FloatField(
        null=True,
        verbose_name="螺杆截面积 [mm²]",
        help_text="用于计算射胶量和剪切速率"
    )
    screw_circumference = models.FloatField(
        null=True,
        verbose_name="螺杆周长 [mm]",
        help_text="用于速度与转速换算"
    )
    screw_compression_ratio = models.FloatField(
        null=True,
        verbose_name="压缩比",
        help_text="加料段深度与均化段深度之比"
    )
    screw_enhancement_ratio = models.FloatField(
        null=True,
        verbose_name="增强比",
        help_text="反映螺杆混炼能力"
    )

    # --- 塑化与注射能力 ---
    plasticizing_capacity = models.FloatField(
        null=True,
        verbose_name="塑化能力 [g/h]",
        help_text="单位时间内熔融塑料的能力"
    )
    max_injection_stroke = models.FloatField(
        null=True,
        verbose_name="最大注射行程 [mm]",
        help_text="螺杆向前推进的最大距离"
    )
    max_injection_volume = models.FloatField(
        null=True,
        verbose_name="理论射胶量 [cm³]",
        help_text="基于行程和截面积计算的熔胶体积"
    )
    max_injection_weight = models.FloatField(
        null=True,
        verbose_name="理论射胶量 [g]",
        help_text="基于密度换算的熔胶质量"
    )
    barrel_heating_power = models.FloatField(
        null=True,
        verbose_name="料筒加热功率 [kW]",
        help_text="料筒总加热功率"
    )

    # --- 控制系统能力（最大段数）---
    max_injection_stages = models.PositiveSmallIntegerField(
        null=True,
        default=6,
        verbose_name="最大注射段数"
    )
    max_holding_stages = models.PositiveSmallIntegerField(
        null=True,
        default=5,
        verbose_name="最大保压段数"
    )
    max_metering_stages = models.PositiveSmallIntegerField(
        null=True,
        default=4,
        verbose_name="最大计量段数"
    )
    max_temperature_control_zones = models.PositiveSmallIntegerField(
        null=True,
        default=10,
        verbose_name="最大温控区域"
    )

    # --- 单位设置 ---
    pressure_unit = models.CharField(
        max_length=10,
        default="MPa",
        null=True,
        verbose_name="压力单位"
    )
    speed_unit = models.CharField(
        max_length=10,
        default="mm/s",
        null=True,
        verbose_name="速度单位"
    )
    position_unit = models.CharField(
        max_length=10,
        default="mm",
        null=True,
        verbose_name="位置单位"
    )
    time_unit = models.CharField(
        max_length=10,
        default="s",
        null=True,
        verbose_name="时间单位"
    )
    back_pressure_unit = models.CharField(
        max_length=10,
        default="MPa",
        null=True,
        verbose_name="背压单位"
    )
    screw_rotation_unit = models.CharField(
        max_length=10,
        default="rpm",
        null=True,
        verbose_name="螺杆转速单位"
    )
    temperature_unit = models.CharField(
        max_length=10,
        default="℃",
        null=True,
        verbose_name="温度单位"
    )

    # --- 成型能力（设备极限）---
    max_injection_pressure = models.FloatField(
        null=True,
        verbose_name="最大注射压力 [MPa]",
        help_text="设备可达到的最高注射压力"
    )
    max_injection_speed = models.FloatField(
        null=True,
        verbose_name="最大注射速度 [mm/s]",
        help_text="螺杆前进的最大线速度"
    )
    max_holding_pressure = models.FloatField(
        null=True,
        verbose_name="最大保压压力 [MPa]",
        help_text="保压阶段可维持的最高压力"
    )
    max_holding_speed = models.FloatField(
        null=True,
        verbose_name="最大保压速度 [mm/s]",
        help_text="保压阶段螺杆推进速度上限"
    )
    max_metering_pressure = models.FloatField(
        null=True,
        verbose_name="最大计量压力 [MPa]",
        help_text="塑化时螺杆后退所受的最大反压"
    )
    max_screw_rotation_speed = models.FloatField(
        null=True,
        verbose_name="最大螺杆转速 [rpm]",
        help_text="塑化时螺杆旋转速度上限"
    )
    max_metering_back_pressure = models.FloatField(
        null=True,
        verbose_name="最大计量背压 [MPa]",
        help_text="计量时施加在螺杆上的反向压力"
    )
    max_decompression_pressure = models.FloatField(
        null=True,
        verbose_name="最大松退压力 [MPa]",
        help_text="抽胶（松退）动作的最大驱动力"
    )
    max_decompression_speed = models.FloatField(
        null=True,
        verbose_name="最大松退速度 [mm/s]",
        help_text="抽胶动作的最大速度"
    )

    # --- HMI 可设定范围（界面限制）---
    max_set_injection_pressure = models.FloatField(
        null=True,
        verbose_name="最大可设定注射压力 [MPa]",
        help_text="操作界面允许输入的最大注射压力值"
    )
    max_set_injection_speed = models.FloatField(
        null=True,
        verbose_name="最大可设定注射速度 [mm/s]",
        help_text="操作界面允许输入的最大注射速度值"
    )
    max_set_holding_pressure = models.FloatField(
        null=True,
        verbose_name="最大可设定保压压力 [MPa]",
        help_text="操作界面允许输入的最大保压压力值"
    )
    max_set_holding_speed = models.FloatField(
        null=True,
        verbose_name="最大可设定保压速度 [mm/s]",
        help_text="操作界面允许输入的最大保压速度值"
    )
    max_set_metering_pressure = models.FloatField(
        null=True,
        verbose_name="最大可设定计量压力 [MPa]",
        help_text="操作界面允许输入的最大计量压力值"
    )
    max_set_screw_rotation_speed = models.FloatField(
        null=True,
        verbose_name="最大可设定螺杆转速 [rpm]",
        help_text="操作界面允许输入的最大螺杆转速值"
    )
    max_set_metering_back_pressure = models.FloatField(
        null=True,
        verbose_name="最大可设定计量背压 [MPa]",
        help_text="操作界面允许输入的最大计量背压值"
    )
    max_set_decompression_pressure = models.FloatField(
        null=True,
        verbose_name="最大可设定松退压力 [MPa]",
        help_text="操作界面允许输入的最大松退压力值"
    )
    max_set_decompression_speed = models.FloatField(
        null=True,
        verbose_name="最大可设定松退速度 [mm/s]",
        help_text="操作界面允许输入的最大松退速度值"
    )
    
    class Meta:
        verbose_name = "注射单元"
        verbose_name_plural = "注射单元"