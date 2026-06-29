from extensions.schemas import AbstractBaseSchema, BaseSchema, PaginationBaseSchema
from marshmallow import fields, validate, EXCLUDE



class InjectionUnitSchema(AbstractBaseSchema):
    """注射单元"""
    id = fields.Integer(allow_none=True, metadata={"description": "射台ID"})

    # --- 射台标识 ---
    unit_code = fields.String(load_default="", allow_none=True, metadata={"description": "射台编号"})
    
    # --- 喷嘴参数 ---
    nozzle_type = fields.String(load_default="", allow_none=True, metadata={"description": "喷嘴类型"})
    nozzle_protrusion = fields.Float(allow_none=True, metadata={"description": "喷嘴伸出量 [mm]"})
    nozzle_hole_diameter = fields.Float(allow_none=True, metadata={"description": "喷嘴孔直径 [mm]"})
    nozzle_sphere_radius = fields.Float(allow_none=True, metadata={"description": "喷嘴球半径 [mm]"})
    nozzle_contact_force = fields.Float(allow_none=True, metadata={"description": "喷嘴接触力 [kN]"})

    # --- 螺杆参数 ---
    screw_type = fields.String(load_default="", allow_none=True, metadata={"description": "螺杆类型"})
    screw_diameter = fields.Float(allow_none=True, metadata={"description": "螺杆直径 [mm]"})
    screw_length_to_diameter_ratio = fields.Float(allow_none=True, metadata={"description": "长径比 L/D"})
    screw_cross_sectional_area = fields.Float(allow_none=True, metadata={"description": "螺杆截面积 [mm²]"})
    screw_circumference = fields.Float(allow_none=True, metadata={"description": "螺杆周长 [mm]"})
    screw_compression_ratio = fields.Float(allow_none=True, metadata={"description": "压缩比"})
    screw_enhancement_ratio = fields.Float(allow_none=True, metadata={"description": "增强比"})

    # --- 塑化与注射能力 ---
    plasticizing_capacity = fields.Float(allow_none=True, metadata={"description": "塑化能力 [g/h]"})
    max_injection_stroke = fields.Float(allow_none=True, metadata={"description": "最大注射行程 [mm]"})
    max_injection_volume = fields.Float(allow_none=True, metadata={"description": "理论射胶量 [cm³]"})
    max_injection_weight = fields.Float(allow_none=True, metadata={"description": "理论射胶量 [g]"})
    barrel_heating_power = fields.Float(allow_none=True, metadata={"description": "料筒加热功率 [kW]"})

    # --- 控制系统能力（最大段数）---
    max_injection_stages = fields.Integer(load_default=6, allow_none=True, metadata={"description": "最大注射段数"})
    max_holding_stages = fields.Integer(load_default=5, allow_none=True, metadata={"description": "最大保压段数"})
    max_metering_stages = fields.Integer(load_default=4, allow_none=True, metadata={"description": "最大计量段数"})
    max_temperature_control_zones = fields.Integer(load_default=10, allow_none=True, metadata={"description": "最大温控区域"})

    # --- 单位设置 ---
    pressure_unit = fields.String(load_default="MPa", allow_none=True, metadata={"description": "压力单位"})
    speed_unit = fields.String(load_default="mm/s", allow_none=True, metadata={"description": "速度单位"})
    position_unit = fields.String(load_default="mm", allow_none=True, metadata={"description": "位置单位"})
    time_unit = fields.String(load_default="s", allow_none=True, metadata={"description": "时间单位"})
    back_pressure_unit = fields.String(load_default="MPa", allow_none=True, metadata={"description": "背压单位"})
    screw_rotation_unit = fields.String(load_default="rpm", allow_none=True, metadata={"description": "螺杆转速单位"})
    temperature_unit = fields.String(load_default="℃", allow_none=True, metadata={"description": "温度单位"})

    # --- 成型能力（设备极限）---
    max_injection_pressure = fields.Float(allow_none=True, metadata={"description": "最大注射压力 [MPa]"})
    max_injection_speed = fields.Float(allow_none=True, metadata={"description": "最大注射速度 [mm/s]"})
    max_holding_pressure = fields.Float(allow_none=True, metadata={"description": "最大保压压力 [MPa]"})
    max_holding_speed = fields.Float(allow_none=True, metadata={"description": "最大保压速度 [mm/s]"})
    max_metering_pressure = fields.Float(allow_none=True, metadata={"description": "最大计量压力 [MPa]"})
    max_screw_rotation_speed = fields.Float(allow_none=True, metadata={"description": "最大螺杆转速 [rpm]"})
    max_metering_back_pressure = fields.Float(allow_none=True, metadata={"description": "最大计量背压 [MPa]"})
    max_decompression_pressure = fields.Float(allow_none=True, metadata={"description": "最大松退压力 [MPa]"})
    max_decompression_speed = fields.Float(allow_none=True, metadata={"description": "最大松退速度 [mm/s]"})

    # --- HMI 可设定范围（界面限制）---
    max_set_injection_pressure = fields.Float(allow_none=True, metadata={"description": "最大可设定注射压力 [MPa]"})
    max_set_injection_speed = fields.Float(allow_none=True, metadata={"description": "最大可设定注射速度 [mm/s]"})
    max_set_holding_pressure = fields.Float(allow_none=True, metadata={"description": "最大可设定保压压力 [MPa]"})
    max_set_holding_speed = fields.Float(allow_none=True, metadata={"description": "最大可设定保压速度 [mm/s]"})
    max_set_metering_pressure = fields.Float(allow_none=True, metadata={"description": "最大可设定计量压力 [MPa]"})
    max_set_screw_rotation_speed = fields.Float(allow_none=True, metadata={"description": "最大可设定螺杆转速 [rpm]"})
    max_set_metering_back_pressure = fields.Float(allow_none=True, metadata={"description": "最大可设定计量背压 [MPa]"})
    max_set_decompression_pressure = fields.Float(allow_none=True, metadata={"description": "最大可设定松退压力 [MPa]"})
    max_set_decompression_speed = fields.Float(allow_none=True, metadata={"description": "最大可设定松退速度 [mm/s]"})


class InjectionMoldingMachineSchema(BaseSchema):
    """注塑机"""
    id = fields.Integer(dump_only=True, metadata={"description": "注塑机ID"})
    # --- 状态信息 ---
    status = fields.String(allow_none=True, metadata={"description": "状态"})
    # --- 基本信息 ---
    brand = fields.String(allow_none=True, metadata={"description": "品牌"})
    model = fields.String(allow_none=True, metadata={"description": "设备型号"})
    manufacturer = fields.String(allow_none=True, metadata={"description": "制造商"})
    location = fields.String(allow_none=True, metadata={"description": "位置"})
    device_no = fields.String(allow_none=True, metadata={"description": "设备编号"})
    asset_no = fields.String(allow_none=True, metadata={"description": "资产编号"})
    machine_type = fields.String(allow_none=True, metadata={"description": "设备类型"})
    drive_system = fields.String(allow_none=True, metadata={"description": "驱动系统"})
    unit_count = fields.Integer(load_default=1, allow_none=True, metadata={"description": "射台数量"})
    
    # --- 控制器信息 ---
    controller_model = fields.String(load_default="", allow_none=True, metadata={"description": "控制器型号"})
    controller_version = fields.String(load_default="", allow_none=True, metadata={"description": "控制器版本"})
    
    # --- 通讯能力 ---
    is_comm_enabled = fields.Boolean(load_default=False, allow_none=True, metadata={"description": "是否支持通讯"})
    communication_protocol = fields.String(load_default="", allow_none=True, metadata={"description": "通讯协议"})
    communication_ip = fields.String(
        allow_none=True,
        validate=validate.Regexp(
            r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
            error="请输入有效的IPv4地址"
        ),
        metadata={"description": "通讯IP"}
    )
    last_comm_time = fields.DateTime(allow_none=True, metadata={"description": "上次通讯时间"})
    
    # --- 默认单位系统（由控制器统一设定） ---
    pressure_unit = fields.String(load_default='bar', allow_none=True, metadata={"description": "压力单位"})
    speed_unit = fields.String(load_default='mm/s', allow_none=True, metadata={"description": "速度单位"})
    position_unit = fields.String(load_default='mm', allow_none=True, metadata={"description": "位置单位"})
    time_unit = fields.String(load_default='s', allow_none=True, metadata={"description": "时间单位"})
    back_pressure_unit = fields.String(load_default='bar', allow_none=True, metadata={"description": "背压单位"})
    screw_rotation_unit = fields.String(load_default='rpm', allow_none=True, metadata={"description": "螺杆转速单位"})
    temperature_unit = fields.String(load_default='℃', allow_none=True, metadata={"description": "温度单位"})
    clamping_force_unit = fields.String(load_default='ton', allow_none=True, metadata={"description": "锁模力单位"})
    
    # --- 注射单元 ---
    injection_units = fields.Nested(InjectionUnitSchema, many=True, unknown=EXCLUDE, metadata={"description": "射台参数"})
    
    # --- 模板参数 ---
    # 定模板
    fixed_platen_width = fields.Float(allow_none=True, metadata={"description": "定模板宽度 [mm]"})
    fixed_platen_height = fields.Float(allow_none=True, metadata={"description": "定模板高度 [mm]"})
    fixed_platen_thickness = fields.Float(allow_none=True, metadata={"description": "定模板厚度 [mm]"})
    locating_hole_diameter = fields.Float(allow_none=True, metadata={"description": "定位孔直径 [mm]"})
    
    # 动模板
    moving_platen_width = fields.Float(allow_none=True, metadata={"description": "动模板宽度 [mm]"})
    moving_platen_height = fields.Float(allow_none=True, metadata={"description": "动模板高度 [mm]"})
    moving_platen_thickness = fields.Float(allow_none=True, metadata={"description": "动模板厚度 [mm]"})
    
    # --- 拉杆（哥林柱）---
    tie_bar_spacing_width = fields.Float(allow_none=True, metadata={"description": "拉杆（格林柱）水平间距 [mm]"})
    tie_bar_spacing_height = fields.Float(allow_none=True, metadata={"description": "拉杆（格林柱）垂直间距 [mm]"})
    tie_bar_diameter = fields.Float(allow_none=True, metadata={"description": "拉杆（格林柱）直径 [mm]"})
    tie_bar_count = fields.Integer(allow_none=True, metadata={"description": "拉杆（格林柱）数量"})
    
    # --- 模板间距（物理极限）---
    min_platen_spacing = fields.Float(allow_none=True, metadata={"description": "最小模板间距 [mm]"})
    max_platen_spacing = fields.Float(allow_none=True, metadata={"description": "最大模板间距 [mm]"})
    
    # --- 容模参数（工程推荐） ---
    min_mold_length = fields.Float(allow_none=True, metadata={"description": "最小容模水平尺寸 [mm]"})
    max_mold_length = fields.Float(allow_none=True, metadata={"description": "最大容模水平尺寸 [mm]"})
    min_mold_width = fields.Float(allow_none=True, metadata={"description": "最小容模垂直尺寸 [mm]"})
    max_mold_width = fields.Float(allow_none=True, metadata={"description": "最大容模垂直尺寸 [mm]"})
    min_mold_thickness = fields.Float(allow_none=True, metadata={"description": "最小容模厚度 [mm]"})
    max_mold_thickness = fields.Float(allow_none=True, metadata={"description": "最大容模厚度 [mm]"})
    max_opening_stroke = fields.Float(allow_none=True, metadata={"description": "最大开模行程 [mm]"})
    
    # --- 锁模性能 ---
    clamping_type = fields.String(load_default="", allow_none=True, metadata={"description": "锁模类型"})
    max_clamping_force = fields.Float(allow_none=True, metadata={"description": "最大锁模力 [ton]"})
    
    # --- 顶出系统---
    ejection_type = fields.String(load_default="", allow_none=True, metadata={"description": "顶出类型"})
    ejection_mode = fields.String(load_default="", allow_none=True, metadata={"description": "顶出模式"})
    ejection_stroke = fields.Float(allow_none=True, metadata={"description": "顶出行程 [mm]"})
    ejection_force = fields.Float(allow_none=True, metadata={"description": "顶出力 [kN]"})
    
    # --- 尺寸信息 ---
    size_length = fields.Float(allow_none=True, metadata={"description": "机台外形尺寸长 [mm]"})
    size_width = fields.Float(allow_none=True, metadata={"description": "机台外形尺寸宽 [mm]"})
    size_height = fields.Float(allow_none=True, metadata={"description": "机台外形尺寸高[mm]"})
    machine_weight = fields.Float(allow_none=True, metadata={"description": "机台重量 [kg]"})
    motor_power = fields.Float(allow_none=True, metadata={"description": "电机功率 [kW]"})
    heater_power = fields.Float(allow_none=True, metadata={"description": "电热功率 [kW]"})
    rated_power = fields.Float(allow_none=True, metadata={"description": "额定功率 [kW]"})
    
    # --- 日期 ---
    manufacture_date = fields.Date(allow_none=True, metadata={"description": "制造日期"})
    commissioning_date = fields.Date(allow_none=True, metadata={"description": "投产日期"})
   

class InjectionMachineListSchema(PaginationBaseSchema):
    """注塑机列表"""
    status = fields.String(allow_none=True, metadata={"description": "状态"})
    brand = fields.String(allow_none=True, metadata={"description": "品牌"})
    model = fields.String(allow_none=True, metadata={"description": "型号"})
    manufacturer = fields.String(allow_none=True, metadata={"description": "制造商"})
    location = fields.String(allow_none=True, metadata={"description": "位置"})
    device_no = fields.String(allow_none=True, metadata={"description": "设备编号"})
    asset_no = fields.String(allow_none=True, metadata={"description": "资产编号"})
    machine_type = fields.String(allow_none=True, metadata={"description": "设备类型"})
    drive_system = fields.String(allow_none=True, metadata={"description": "驱动系统"})
    unit_count = fields.Integer(allow_none=True, metadata={"description": "射台数量"}) 
