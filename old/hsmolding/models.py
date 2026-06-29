from django.db import models
from gis.common.django_ext.models import ExtraBaseModel
from gis.admin.models import Company


# 工程--project
class Project(ExtraBaseModel):
    '''
    注塑模具信息表
    '''

    # 标记
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    deleted = models.IntegerField(default=0)

    status = models.IntegerField(default=1) # 模具当前状态
    mold_no = models.CharField(max_length=45)  # 模具编号
    mold_type = models.CharField(max_length=45, null=True)  # 模具类型
    mold_name = models.CharField(max_length=45, null=True)  # 模具名称
    cavity_num = models.CharField(max_length=45, null=True)  # 型腔数量

    product_no = models.CharField(max_length=45, null=True)  # 制品编号
    product_name = models.CharField(max_length=45, null=True)  # 制品名称
    product_type = models.CharField(max_length=45, null=True)  # 制品类别
    product_category = models.CharField(max_length=45, null=True)  # 制品品类
    product_small_type = models.CharField(max_length=45, null=True) 
    # product_ave_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 平均壁厚
    # product_max_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 最大壁厚
    # product_min_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 最小壁厚
    # product_max_length = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 制品流长
    # product_single_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 单件体积
    # product_single_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 单件重量
    product_total_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 总重量
    product_projected_area = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 总投射面积

    locate_ring_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 定位圈直径
    # sprue_hole_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 射嘴孔直径
    # sprue_sphere_radius = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 射嘴球径
    # runner_type = models.CharField(max_length=45, null=True)  # 流道类型
    # valve_num = models.IntegerField(null=True)  # 热流道控制阀数量
    # runner_length = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 流道长度
    # runner_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 流道重量
    # hot_runner_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 热流道总体积
    # gate_type = models.CharField(max_length=45, null=True)  # 浇口类别
    # gate_num = models.IntegerField(null=True)  # 浇口数量
    # gate_shape = models.CharField(max_length=45, null=True)  # 浇口形状
    # gate_area = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口横截面积
    # gate_radius = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口半径(圆)
    # gate_length = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口长(矩形)
    # gate_width = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口宽(矩形)

    cavity_cooling_water_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 前模冷却水直径
    cavity_cooling_circuit_number = models.IntegerField(null=True)  # 前模冷却回路组数
    cavity_water_nozzle_specification = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 前模水嘴安装规格
    core_cooling_water_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 后模冷却水直径
    core_cooling_circuit_number = models.IntegerField(null=True)  # 后模冷却回路组数
    core_water_nozzle_specification = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 后模水嘴安装规格
    circuit_picture_url = models.CharField(max_length=1024, null=True)  # 冷却回路附件
   
    ejector_stroke = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 顶出行程
    ejector_rod_hole_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 顶棍孔直径
    # ejector_rod_hole_distribute = models.CharField(max_length=45, null=True)  # 顶棍孔分布
    ejector_rod_hole_spacing = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 顶棍孔间距
    ejector_rod_number = models.IntegerField(null=True)  # 顶棍数量
    ejector_force = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 顶出力
    ejector_times = models.IntegerField(null=True)  # 顶出次数
    reset_method = models.CharField(max_length=45, null=True)  # 复位方式
    ejection_method = models.CharField(max_length=45, null=True)  # 顶出方式
    ejector_position_length = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 顶出孔位置
    ejector_position_width = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 顶出孔位置

    mold_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 模具重量
    hanging_mold_hole_specification = models.CharField(max_length=45, null=True)  # 吊模孔规格

    size_horizon = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 模具尺寸（横）
    size_vertical = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 模板尺寸（竖）
    size_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 模具厚度
    mold_opening_stroke = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 开模行程
    min_clamping_force = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 最小锁模力
    drain_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 取流道距离
    inject_cycle_require = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 注塑周期要求
    subrule_no = models.CharField(max_length=256, null=True)  # 模具绑定的子规则库

    assisting_equipments = models.CharField(max_length=256, null=True)  # 辅助装置

    customer = models.CharField(max_length=45, null=True)  # 客户
    project_engineer = models.CharField(max_length=45, null=True)  # 项目工程师
    design_engineer = models.CharField(max_length=45, null=True)  # 设计工程师
    production_engineer = models.CharField(max_length=45, null=True)  # 制作工程师
    mold_engineer = models.CharField(max_length=45, null=True)  # 模具工程师
    product_engineer = models.CharField(max_length=45, null=True)  # 产品工程师
    junior_product_engineer = models.CharField(max_length=45, null=True)  # 初级产品工程师
    injection_engineer = models.CharField(max_length=45, null=True)  # 注塑工程师
    senior_injection_engineer = models.CharField(max_length=45, null=True)  # 高级注塑工程师
    order_date = models.DateField(null=True)  # 订单日期
    entry_date = models.DateField(null=True)  # 信息录入日期

    class Meta:
        db_table = "project"


# 产品信息（模具）--product
class Product(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    # project = models.ForeignKey(Project, on_delete=models.CASCADE)
    project_id = models.IntegerField(null=True)

    mold_type = models.CharField(max_length=45, null=True)  # 模具类别
    inject_part = models.CharField(max_length=45, null=True)  # 所在射台

    ave_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 平均壁厚
    max_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 最大壁厚
    min_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 最小壁厚
    flow_length = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 制品流长
    single_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 单件体积
    single_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 单件重量

    # locate_ring_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 定位圈直径
    sprue_hole_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 射嘴孔直径
    sprue_sphere_radius = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 射嘴球径
    runner_type = models.CharField(max_length=45, null=True)  # 流道类型
    hot_runner_num = models.IntegerField(null=True)  # 流道类型
    valve_num = models.IntegerField(null=True)  # 热流道控制阀数量
    runner_length = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 流道长度
    runner_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 流道重量
    # hot_runner_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 热流道总体积
    gate_type = models.CharField(max_length=45, null=True)  # 浇口类别
    gate_num = models.IntegerField(null=True)  # 浇口数量
    gate_shape = models.CharField(max_length=45, null=True)  # 浇口形状
    gate_area = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口横截面积
    gate_radius = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口半径(圆)
    gate_length = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口长(矩形)
    gate_width = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 浇口宽(矩形)
    
    class Meta:
        db_table = "product"


# 机器数据库--machine
class Machine(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    manufacturer = models.CharField(max_length=45, null=True, help_text="注塑机品牌")
    trademark = models.CharField(max_length=45, help_text="注塑机型号(品牌+锁模力)")
    machine_type = models.CharField(max_length=45, null=True, help_text="注塑机类别")
    manufacturing_date = models.DateField(null=True, help_text="制造日期")
    data_source = models.CharField(max_length=45, null=True, help_text="注塑机数据来源")
    asset_no = models.CharField(max_length=45, null=True, help_text="资产编号")
    serial_no = models.CharField(max_length=45, null=True, help_text="设备编码")
    internal_id = models.IntegerField(null=True, help_text="注塑机ID")
    communication_interface = models.IntegerField(default=0, help_text="通讯接口")
    agreement = models.CharField(max_length=45, null=True, help_text="协议")

    pressure_unit = models.CharField(max_length=45, default="MPa", null=True, help_text="压力单位")
    backpressure_unit = models.CharField(max_length=45, default="MPa", null=True, help_text="背压单位")
    oc_pressure_unit = models.CharField(max_length=45, default="MPa", null=True, help_text="压力单位")
    velocity_unit = models.CharField(max_length=45, default="mm/s", null=True, help_text="速度单位")
    oc_velocity_unit = models.CharField(max_length=45, default="mm/s", null=True, help_text="速度单位")
    temperature_unit = models.CharField(max_length=45, default="℃", null=True, help_text="温度单位")
    time_unit = models.CharField(max_length=45, default="s", null=True, help_text="时间单位")
    position_unit = models.CharField(max_length=45, default="mm", null=True, help_text="位置单位")
    clamping_force_unit = models.CharField(max_length=45, default="KN", null=True, help_text="锁模力单位")
    screw_rotation_unit = models.CharField(max_length=45, default="rpm", null=True, help_text="螺杆转速单位")
    power_unit = models.CharField(max_length=45, default="KW", null=True, help_text="功率单位")
    ejection_amount_unit = models.CharField(max_length=45, default="KW", null=True, help_text="最大注射重量单位")

    platen_size_horizon = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="模板尺寸（横）")
    platen_size_vertical = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="模板尺寸（竖）")
    min_mold_size_horizon = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最小容模尺寸（横）")
    min_mold_size_vertical = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最小容模尺寸（竖）")
    max_mold_size_horizon = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最大容模尺寸（横）")
    max_mold_size_vertical = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最大容模尺寸（竖）")
    min_mold_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最小容模厚度")
    max_mold_thickness = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最大容模厚度")
    min_platen_opening = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最小模板开距")
    max_platen_opening = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最大模板开距")
    locate_ring_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="定位圈直径")

    pull_rod_size = models.CharField(max_length=100, null=True , help_text="拉杆连接头,M开头的字符串")
    pull_rod_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="拉杆直径")
    pull_rod_distance_horizon = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="拉杆间距(横)")
    pull_rod_distance_vertical = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="拉杆间距(竖)")

    clamping_method = models.CharField(max_length=45, null=True, help_text="锁模方式")
    max_clamping_force = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="最大锁模力") 
    max_opening_force = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大开模力")
    max_mold_open_stroke = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最大开模行程")
    max_clamping_velocity = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="最大合模速度")
    max_opening_velocity = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="最大开模速度")

    max_ejection_force = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="顶出力")
    max_ejection_stroke = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="顶出行程")
    ejection_hole_num = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="顶出孔数量")
    max_thimble_forward_speed = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="顶针最大顶进速度")
    max_thimble_back_speed = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="顶针最大顶退速度")

    hydraulic_system_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="最大系统压力")
    motor_power = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="电机功率")
    heater_power = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="电热功率")
    temp_control_zone_num = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="温度控制区数")
    main_power = models.DecimalField(max_digits=10, decimal_places=0, null=True , help_text="工作电压")
    power_method = models.CharField(max_length=45, null=True, help_text="动力方式")
    propulsion_axis = models.CharField(max_length=45, null=True, help_text="推进轴线")

    machine_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="机器重量")
    size_length = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="机台外形尺寸（长）")
    size_width = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="机台外形尺寸（宽）")
    size_height = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="机台外形尺寸（高）")
    hopper_capacity = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="料斗容积 (Kg)")
    needle_core =  models.CharField(max_length=45, null=True , help_text="抽芯")
    core_pulling = models.CharField(max_length=45, null=True , help_text="抽芯（组）")
    response_time = models.DecimalField(max_digits=10, decimal_places=2, null=True , help_text="响应时间")
    enhancement_ratio = models.CharField(max_length=45, null=True , help_text="增强比")
    manufacture_date = models.DateField(default="2000-01-01", null=True , help_text="出厂日期")
    manufacture_no = models.CharField(max_length=100, null=True , help_text="出厂编码")
    remark = models.CharField(max_length=100, null=True , help_text="备注")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        db_table = "machine"


# 机器数据库--machine injector
class MachineInjector(ExtraBaseModel):
    # 注塑机
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

    title = models.CharField(max_length=45, null=True, help_text="射台")
    name = models.CharField(max_length=45, null=True, help_text="编号")
    serial_no = models.CharField(max_length=45, null=True, help_text="射台编码")
    
    nozzle_type = models.CharField(max_length=45, null=True, help_text="喷嘴类别")
    nozzle_protrusion = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="喷嘴伸出量")
    nozzle_hole_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="喷嘴孔直径")
    nozzle_sphere_diameter = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="喷嘴球半径")
    nozzle_force = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="喷嘴接触力")

    screw_type = models.CharField(max_length=45, null=True, help_text="螺杆规格类别")
    screw_diameter = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="螺杆规格直径")
    screw_length = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="螺杆规格长度")
    screw_length_diameter_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="螺杆长径比L/D")
    screw_compression_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="螺杆压缩比")
    plasticizing_capacity = models.DecimalField(max_digits=10, decimal_places=0,  null=True, help_text="塑化能力")
    barrel_heating_sections = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="料筒加热段数")
    barrel_heating_power = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="料筒加热功率")
    max_injection_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="cm³理论射胶量")
    max_injection_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="g理论射胶量")
    max_injection_stroke = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="最大注射行程")

    # 油缸和活塞
    cylinder_numer = models.IntegerField(null=True, help_text="油缸数")
    cylinder_diameter = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="油缸直径")
    piston_rod_diameter = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="活塞杆直径")
    use_small_size = models.IntegerField(null=True, help_text="活塞杆位于注射侧")  # 活塞杆位于注射侧
    cylinder_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="油缸面积")
    intensification_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Intensification Ratio = Injection Pressure / Hydraulic Pressure

    max_injection_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大射出压力")
    max_injection_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大注射速度")
    max_holding_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大保压压力")
    max_holding_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大保压速度")
    max_metering_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大计量压力")
    max_screw_rotation_speed = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大螺杆转速")
    max_metering_back_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大计量背压")
    max_decompression_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大松退压力")
    max_decompression_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大松退速度")

    max_injection_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大注射速率")  # 默认单位cm³/s
    max_holding_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大保压速率")  # 默认单位cm³/s
    max_decompression_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大松退速率")  # 默认单位cm³/s
    max_screw_linear_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大螺杆转速线速度")  # 默认单位cm/s
    screw_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="螺杆面积")
    screw_circumference = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="螺杆周长")
    max_ejector_forward_velocity = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="最大顶进速度")
    max_ejector_backward_velocity = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="最大顶退速度")
    max_mold_opening_velocity = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="最大开模速度")
    max_mold_clamping_velocity = models.DecimalField(max_digits=10, decimal_places=0, null=True, help_text="最大合模速度")

    # 工艺参数设置限定值
    max_set_injection_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定注射压力")
    max_set_injection_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定注射速度")
    max_set_holding_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定保压压力")
    max_set_holding_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定保压速度")
    max_set_metering_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定计量压力")
    max_set_screw_rotation_speed = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定螺杆转速")
    max_set_metering_back_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定计量背压")
    max_set_decompression_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定射退压力")
    max_set_decompression_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定松退速度")
    max_set_ejector_forward_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定顶进速度")
    max_set_ejector_backward_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定顶退速度")
    max_set_mold_opening_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定开模速度")
    max_set_mold_clamping_velocity = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大可设定合模速度")

    max_injection_stage = models.IntegerField(default=6)
    max_holding_stage = models.IntegerField(default=5)
    max_metering_stage = models.IntegerField(default=4)
    max_temperature_stage = models.IntegerField(default=10)
    max_opening_and_clamping_stage = models.IntegerField(default=10)
    max_ejector_stage = models.IntegerField(default=10)
    
    class Meta:
        db_table = "machine_injector"


# 胶料数据库--polymer
class Polymer(ExtraBaseModel):
    # 胶料
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    series = models.CharField(max_length=45, null=True, help_text="系列")
    trademark = models.CharField(max_length=200, null=True, help_text="塑料牌号")
    manufacturer = models.CharField(max_length=45, null=True, help_text="塑料制造商")
    abbreviation = models.CharField(max_length=45, null=True, help_text="塑料缩写")
    category = models.CharField(max_length=45, null=True, help_text="塑料类别:结晶性,无定形")
    data_source = models.CharField(max_length=45, null=True, help_text="数据来源")
    
    data_status = models.CharField(max_length=45, null=True, help_text="数据状态")
    internal_id = models.CharField(max_length=45, null=True, help_text="内部ID")
    level_code = models.CharField(max_length=45, null=True, help_text="等级代码")
    vendor_code = models.CharField(max_length=45, null=True, help_text="材料供应商")

    # 推荐工艺
    max_melt_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大成型温度")
    min_melt_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最小成型温度")
    recommend_melt_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="推荐成型温度")
    max_mold_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大模具温度")
    min_mold_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最小模具温度")
    recommend_mold_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="推荐模具温度")
    max_shear_linear_speed = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大剪切线速度")
    min_shear_linear_speed = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最小剪切线速度")
    recommend_shear_linear_speed = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="推荐剪切线速度")
    degradation_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="降解温度")
    ejection_temperature = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="顶出温度")
    recommend_injection_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="推荐注射速率")
    max_sheer_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大许可剪切速率")
    max_sheer_stress = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="最大许可剪切应力")
    recommend_back_pressure = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="推荐背压")
    barrel_residence_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="料筒滞留时间")
    dry_temperature = models.CharField(max_length=64, null=True, help_text="干燥温度")
    dry_time = models.CharField(max_length=64, null=True, help_text="干燥时间")
    dry_method = models.CharField(max_length=255, null=True, help_text="干燥方式")

    # 流变属性
    viscosity_model = models.CharField(max_length=45, null=True)  # 粘度模型:cross_WLF
    cross_WLF_n = models.CharField(max_length=45, null=True)
    cross_WLF_Tau = models.CharField(max_length=45, null=True)  # Pa
    cross_WLF_D1 = models.CharField(max_length=45, null=True)  # Pa-s
    cross_WLF_D2 = models.CharField(max_length=45, null=True)  # k
    cross_WLF_D3 = models.CharField(max_length=45, null=True)  # k/Pa
    cross_WLF_A1 = models.CharField(max_length=45, null=True)
    cross_WLF_A2 = models.CharField(max_length=45, null=True)  # k
    c1 = models.CharField(max_length=45, null=True)  # 接合点损失法系数(Pa^(1-c2))
    c2 = models.CharField(max_length=45, null=True)  # 接合点损失法系数
    switch_temp = models.CharField(max_length=45, null=True)  # 转换温度(℃)
    viscosity_index = models.CharField(max_length=45, null=True)  # 粘度指数
    MFR_temp = models.CharField(max_length=45, null=True)  # 温度（℃）
    MFR_load = models.CharField(max_length=45, null=True)  # 载入（Kg）
    MFR_measure = models.CharField(max_length=45, null=True)  # 测量的MFR（g/10min）

    # pvT属性
    melt_density = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    solid_density = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    Tait_pvT_b5 = models.CharField(max_length=45, null=True)
    Tait_pvT_b6 = models.CharField(max_length=45, null=True)
    Tait_pvT_b1m = models.CharField(max_length=45, null=True)
    Tait_pvT_b2m = models.CharField(max_length=45, null=True)
    Tait_pvT_b3m = models.CharField(max_length=45, null=True)
    Tait_pvT_b4m = models.CharField(max_length=45, null=True)
    Tait_pvT_b1s = models.CharField(max_length=45, null=True)
    Tait_pvT_b2s = models.CharField(max_length=45, null=True)
    Tait_pvT_b3s = models.CharField(max_length=45, null=True)
    Tait_pvT_b4s = models.CharField(max_length=45, null=True)
    Tait_pvT_b7 = models.CharField(max_length=45, null=True)
    Tait_pvT_b8 = models.CharField(max_length=45, null=True)
    Tait_pvT_b9 = models.CharField(max_length=45, null=True)

    # 机械属性
    E1 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    E2 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    v12 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    v23 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    G12 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    Alpha1 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    Alpha2 = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # 收缩属性
    average_horizontal_shrinkage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    average_vertical_shrinkage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    min_horizontal_shrinkage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    max_horizontal_shrinkage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    min_vertical_shrinkage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    max_vertical_shrinkage = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # 填充物属性
    filler = models.CharField(max_length=45, null=True, help_text="填充物或者材料添加剂")
    filler_type = models.CharField(max_length=45, null=True, help_text="填充物类别")
    filler_shape = models.CharField(max_length=45, null=True, help_text="填充物形状")
    filler_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, help_text="填充物含量")
    filler_density = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    filler_specific_heat = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_specific_thermal_conductivity = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_E1 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_E2 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_v12 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_v23 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_G12 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_Alpha1 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_Alpha2 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_horizontal_tensile_strength = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_vertical_tensile_strength = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    filler_aspect_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        db_table = "polymer"


# 辅机
class AuxiliaryMachine(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    company_id = models.IntegerField(null=True)
    machine_id = models.IntegerField(null=True)
    auxiliary_type = models.CharField(max_length=45, null=True)
    auxiliary_trademark = models.CharField(max_length=45, null=True)
    manufacture = models.CharField(max_length=45, null=True)
    serial_num = models.CharField(max_length=45, null=True)

    machine_data_source = models.CharField(max_length=45, null=True)
    machine_trademark = models.CharField(max_length=45, null=True)
    communication_interface = models.IntegerField(null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        db_table = "auxiliary_machine"


# 机器性能测试
class MachineTrial(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    company_id = models.IntegerField(null=True)

    machine_trial_type = models.CharField(max_length=45, null=True)
    mold_id = models.IntegerField(null=True)
    mold_no = models.CharField(max_length=45, null=True)
    product_name = models.CharField(max_length=45, null=True)
    product_type = models.CharField(max_length=45, null=True)
    machine_id = models.IntegerField(null=True)
    machine_data_source = models.CharField(max_length=45, null=True)
    machine_trademark = models.CharField(max_length=45, null=True)
    polymer_id = models.IntegerField(null=True)
    polymer_abbreviation = models.CharField(max_length=45, null=True)
    polymer_trademark = models.CharField(max_length=45, null=True)
    asset_no =  models.CharField(max_length=45, null=True)

    doc_link = models.CharField(max_length=250, null=True)
    report_export_at = models.DateTimeField(auto_now_add=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        db_table = "machine_trial"


# 自定义下拉选项--custom_option
class CustomOption(ExtraBaseModel):
    # 胶料
    id = models.BigAutoField(primary_key=True)
    company_id = models.IntegerField(null=True)
    interface_view = models.CharField(max_length=45, null=True)  # 界面
    interface_select = models.CharField(max_length=45, null=True)  # 组件
    label = models.CharField(max_length=45, null=True)  # option label
    value = models.CharField(max_length=45, null=True)  # option value
    key = models.IntegerField(null=True)
    view_desc = models.CharField(max_length=45, null=True)
    select_desc = models.CharField(max_length=45, null=True)
    
    class Meta:
        db_table = "custom_option"