from email.policy import default
from marshmallow import fields

from gis.common.django_ext.forms import (
    BaseSchema,
    CNDatetimeField,
    PaginationBaseSchema,
)

# 查询机器列表
class GetMachineListSchema(PaginationBaseSchema):
    trademark = fields.String()
    manufacturer = fields.String()
    machine_type = fields.String()
    power_method = fields.String()
    propulsion_axis = fields.String()
    data_source = fields.String(required=False, allow_none=True)
    max_clamping_force = fields.String()
    serial_no = fields.String()
    company_id = fields.Integer()

    # 以下需求为对应模具的注塑机适配
    min_mold_size_horizon = fields.Float(required=False, allow_none=True)
    min_mold_size_vertical = fields.Float(required=False, allow_none=True)
    min_mold_thickness = fields.Float(required=False, allow_none=True)
    min_mold_open_stroke = fields.Float(required=False, allow_none=True)
    min_clamping_force = fields.Float(required=False, allow_none=True)


class HandleMultipleMachineSchema(BaseSchema):
    machine_id_list = fields.List(fields.Integer())
    flag = fields.String(default="default") # 标记处理方式


# 注塑机注射部件信息--machine injector
class MachineInjectorSchema(BaseSchema):
    # 修改的時候，需要增加的字段
    id = fields.Integer(required=False, allow_none=True)
    machine_id = fields.Integer(required=False, allow_none=True)

    # 增加注塑机
    title = fields.String(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    serial_no = fields.String(required=False, allow_none=True)
    
    nozzle_type = fields.String(required=True, allow_none=False)  # 喷嘴类型
    nozzle_protrusion = fields.Float(required=False, allow_none=True)  # 喷嘴伸出量
    nozzle_hole_diameter = fields.Float(required=False, allow_none=True)  # 喷嘴孔直径
    nozzle_sphere_diameter = fields.Float(required=False, allow_none=True)  # 喷嘴球半径（SR）
    nozzle_force = fields.Float(required=False, allow_none=True)  # 喷嘴接触力

    screw_type = fields.String(required=False, allow_none=True)  # 螺杆类别
    screw_diameter = fields.Float(required=True, allow_none=False)  # 螺杆直径(mm)
    screw_length = fields.Float(required=False, allow_none=True)  # 螺杆长度(mm)
    screw_length_diameter_ratio = fields.Float(required=False, allow_none=True)  # 螺杆长径比L/D
    screw_compression_ratio = fields.Float(required=False, allow_none=True)  # 螺杆压缩比
    plasticizing_capacity = fields.Float(required=False, allow_none=True)  # 塑化能力
    barrel_heating_sections = fields.Float(required=False, allow_none=True)  # 料筒加热段数
    barrel_heating_power = fields.Float(required=False, allow_none=True)  # 料筒加热功率
    max_injection_volume = fields.Float(required=False, allow_none=True)  # 最大注射容积
    max_injection_weight = fields.Float(required=False, allow_none=True)  # 最大注射重量
    max_injection_stroke = fields.Float(required=True, allow_none=False)  # 最大注射行程
    
    # 油缸和活塞
    cylinder_numer = fields.Integer(required=False, allow_none=True)  # 油缸数
    cylinder_diameter = fields.Float(required=False, allow_none=True)  # 油缸直径
    piston_rod_diameter = fields.Float(required=False, allow_none=True)  # 活塞杆直径
    use_small_size = fields.Integer(required=False, allow_none=True)  # 活塞杆位于注射侧
    cylinder_area = fields.Float(required=False, allow_none=True)  # 油缸面积
    intensification_ratio = fields.Float(required=False, allow_none=True)  # Intensification Ratio = Injection Pressure / Hydraulic Pressure
    
    max_injection_pressure = fields.Float(required=True, allow_none=False)  # 最大注射压力(MPa)
    max_injection_velocity = fields.Float(required=True, allow_none=False)  # 最大注射速度(mm/s)
    max_holding_pressure = fields.Float(required=True, allow_none=False)  # 最大保压压力
    max_holding_velocity = fields.Float(required=True, allow_none=False)  # 最大保压速度(mm/s)
    max_metering_pressure = fields.Float(required=False, allow_none=True)  # 最大计量压力
    max_screw_rotation_speed = fields.Float(required=True, allow_none=False)  # 最大螺杆转速
    max_metering_back_pressure = fields.Float(required=True, allow_none=False)  # 最大计量背压
    max_decompression_pressure = fields.Float(required=False, allow_none=True)  # 最大松退压力
    max_decompression_velocity = fields.Float(required=True, allow_none=False)  # 最大松退速度
    max_injection_rate = fields.Float(required=False, allow_none=True)  # 最大注射速率 默认单位cm³/s
    max_holding_rate = fields.Float(required=False, allow_none=True)  # 最大保压速率 默认单位cm³/s
    max_decompression_rate = fields.Float(required=False, allow_none=True)  # 最大松退速率 默认单位cm³/s
    max_screw_linear_velocity = fields.Float(required=False, allow_none=True)  # 最大螺杆转速线速度 默认单位cm/s
    screw_area = fields.Float(required=False, allow_none=True)  # 螺杆面积
    screw_circumference = fields.Float(required=False, allow_none=True)  # 螺杆周长
    max_ejector_forward_velocity = fields.Float(required=False, allow_none=True)  # 最大顶进速度
    max_ejector_backward_velocity = fields.Float(required=False, allow_none=True)  # 最大顶退速度
    max_mold_opening_velocity = fields.Float(required=False, allow_none=True)  # 最大开模速度
    max_mold_clamping_velocity = fields.Float(required=False, allow_none=True)  # 最大合模速度

    max_set_injection_pressure = fields.Float(required=True, allow_none=False)  # 最大可设定注射压力
    max_set_injection_velocity = fields.Float(required=True, allow_none=False)  # 最大可设定注射速度
    max_set_holding_pressure = fields.Float(required=True, allow_none=False)  # 最大可设定保压压力
    max_set_holding_velocity = fields.Float(required=True, allow_none=False)  # 最大可设定保压速度
    max_set_metering_pressure = fields.Float(required=False, allow_none=True)  # 最大可设定计量压力
    max_set_screw_rotation_speed = fields.Float(required=True, allow_none=False)  # 最大可设定螺杆转速
    max_set_metering_back_pressure = fields.Float(required=True, allow_none=False)  # 最大可设定计量背压
    max_set_decompression_pressure = fields.Float(required=False, allow_none=True)  # 最大可设定松退压力
    max_set_decompression_velocity = fields.Float(required=False, allow_none=True)  # 最大可设定松退速度
    max_set_ejector_forward_velocity = fields.Float(required=False, allow_none=True)  # 最大可设定顶进速度
    max_set_ejector_backward_velocity = fields.Float(required=False, allow_none=True)  # 最大可设定顶退速度
    max_set_mold_opening_velocity = fields.Float(required=False, allow_none=True)  # 最大可设定开模速度
    max_set_mold_clamping_velocity = fields.Float(required=False, allow_none=True)  # 最大可设定合模速度

    max_injection_stage = fields.Integer(required=True, allow_none=False)
    max_holding_stage = fields.Integer(required=True, allow_none=False)
    max_metering_stage = fields.Integer(required=True, allow_none=False)
    max_temperature_stage = fields.Integer(required=True, allow_none=False)
    max_opening_and_clamping_stage = fields.Integer(required=False, allow_none=True)
    max_ejector_stage = fields.Integer(required=False, allow_none=True)


# 注塑机信息--machine info
class MachineInfoSchema(BaseSchema):
    id = fields.Float(required=False, allow_none=True)
    company_id = fields.Integer(required=True, allow_none=False)

    manufacturer = fields.String(required=True, allow_none=False)  # 注塑机品牌
    trademark = fields.String(required=True, allow_none=False)  # 注塑机型号
    machine_type = fields.String(required=False, allow_none=True)  # 注塑机类别
    manufacturing_date = fields.Date(required=False, allow_none=True)  # 制造日期
    data_source = fields.String(required=True, allow_none=False)  # 注塑机数据来源
    asset_no = fields.String(required=False, allow_none=True)  # 资产编号
    serial_no = fields.String(required=True, allow_none=False)  # 设备编码
    internal_id = fields.Integer(required=False, allow_none=True)  # 注塑机ID
    communication_interface = fields.Integer(default=0, required=False, allow_none=True)  # 注塑机ID
    agreement = fields.String(required=False, allow_none=True)  # 协议

    pressure_unit = fields.String(max_length=45, default="MPa", required=True, allow_none=False)
    backpressure_unit = fields.String(max_length=45, default="MPa", required=True, allow_none=False)
    oc_pressure_unit = fields.String(max_length=45, default="MPa", required=False, allow_none=True)
    velocity_unit = fields.String(max_length=45, default="mm/s", required=True, allow_none=False)
    oc_velocity_unit = fields.String(max_length=45, default="mm/s", required=False, allow_none=True)
    temperature_unit = fields.String(max_length=45, default="℃", required=True, allow_none=False)
    time_unit = fields.String(max_length=45, default="s", required=True, allow_none=False)
    position_unit = fields.String(max_length=45, default="mm", required=True, allow_none=False)
    clamping_force_unit = fields.String(max_length=45, default="Ton", required=True, allow_none=False)
    screw_rotation_unit = fields.String(max_length=45, default="rpm", required=True, allow_none=False)
    power_unit = fields.String(max_length=45, default="KW", required=True, allow_none=False)
    ejection_amount_unit = fields.String(max_length=45, default="cm³", required=False, allow_none=True)

    platen_size_horizon = fields.Float(required=False, allow_none=True)  # 模板尺寸（横*竖）（H*V）（mm）
    platen_size_vertical = fields.Float(required=False, allow_none=True)  # 模板尺寸（横*竖）（H*V）（mm）
    min_mold_size_horizon = fields.Float(required=False, allow_none=True)  # 最小容模尺寸（横*竖）（H*V）（mm）
    min_mold_size_vertical = fields.Float(required=False, allow_none=True)  # 最小容模尺寸（横*竖）（H*V）（mm）
    max_mold_size_horizon = fields.Float(required=False, allow_none=True)  # 最大容模尺寸（横*竖）（H*V）（mm）
    max_mold_size_vertical = fields.Float(required=False, allow_none=True)  # 最大容模尺寸（横*竖）（H*V）（mm）
    min_mold_thickness = fields.Float(required=False, allow_none=True)  # 最小容模厚度(mm)
    max_mold_thickness = fields.Float(required=False, allow_none=True)  # 最大容模厚度(mm)
    min_platen_opening = fields.Float(required=False, allow_none=True)  # 模板最小开距(mm)
    max_platen_opening = fields.Float(required=False, allow_none=True)  # 模板最大开距(mm)
    locate_ring_diameter = fields.Float(required=False, allow_none=True)  # 定位圈/法兰孔直径

    pull_rod_size = fields.String(required=False, allow_none=True) # 拉杆连接头尺寸
    pull_rod_diameter = fields.Float(required=False, allow_none=True)  # 拉杆直径
    pull_rod_distance_horizon = fields.Float(required=False, allow_none=True)  # 拉杆间距（横*竖）（H*V）(mm)
    pull_rod_distance_vertical = fields.Float(required=False, allow_none=True)  # 拉杆间距（横*竖）（H*V）(mm)

    clamping_method = fields.String(required=False, allow_none=True)  # 锁模方式
    max_opening_force = fields.Float(required=False, allow_none=True)  # 最大开模力
    max_clamping_force = fields.Float(required=False, allow_none=True)  # 最大锁模力(Ton)
    max_mold_open_stroke = fields.Float(required=False, allow_none=True)  # 开模行程(mm)
    max_clamping_velocity = fields.Float(required=False, allow_none=True)  # 最大合模速度
    max_opening_velocity = fields.Float(required=False, allow_none=True)  # 最大开模速度

    max_ejection_force = fields.Float(required=False, allow_none=True)  # 顶出力
    max_ejection_stroke = fields.Float(required=False, allow_none=True)  # 顶出行程
    ejection_hole_num = fields.Float(required=False, allow_none=True)  # 顶出孔数量
    max_thimble_forward_speed = fields.Float(required=False, allow_none=True)  # 顶针最大顶进速度
    max_thimble_back_speed = fields.Float(required=False, allow_none=True)  # 顶针最大顶退速度

    hydraulic_system_pressure = fields.Float(required=False, allow_none=True)  # 最大系统压力
    motor_power = fields.Float(required=False, allow_none=True)  # 总功率电机（KW）
    heater_power = fields.Float(required=False, allow_none=True)  # 电热功率
    temp_control_zone_num = fields.Float(required=False, allow_none=True)  # 温度控制区数
    main_power = fields.Float(required=False, allow_none=True)  # 工作电压（V）
    power_method = fields.String(required=False, allow_none=True)  # 动力方式:电动机或者液压机
    propulsion_axis = fields.String(required=False, allow_none=True)  # 推进轴线

    machine_weight = fields.Float(required=False, allow_none=True)  # 机器重量
    size_length = fields.Float(required=False, allow_none=True)  # 机台外形尺寸（L*W*H）(mm)
    size_width = fields.Float(required=False, allow_none=True)  # 机台外形尺寸（L*W*H）(mm)
    size_height = fields.Float(required=False, allow_none=True)  # 机台外形尺寸（L*W*H）(mm)
    hopper_capacity = fields.Float(required=False, allow_none=True)  # 料斗容积
    needle_core = fields.String(required=False, allow_none=True)  #是否需要抽芯
    core_pulling = fields.String(required=False, allow_none=True)  # 抽芯（组）
    response_time = fields.Float(required=False, allow_none=True)  # 响应时间
    enhancement_ratio = fields.String(required=False, allow_none=True)  # 增强比
    manufacture_date = fields.Date(required=False, allow_none=True)  # 出厂日期
    manufacture_no = fields.String(required=False, allow_none=True)  # 出厂编码
    remark = fields.String(required=False, allow_none=True)  # 备注

    injectors_info = fields.Nested(MachineInjectorSchema, many=True) # 注射部件信息

    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer()
    