"""
注塑机相关 Schema 定义 - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Optional, List
from datetime import date
from pydantic import Field, field_validator

from extensions.schemas import AbstractBaseSchema, BaseSchema, PaginationBaseSchema


class InjectionUnitSchema(AbstractBaseSchema):
    """注射单元"""
    
    id: Optional[int] = Field(None, description="射台ID")
    # --- 射台标识 ---
    unit_code: str = Field(default="", description="射台编号")
    # --- 喷嘴参数 ---
    nozzle_type: str = Field(default="", description="喷嘴类型")
    nozzle_protrusion: Optional[float] = Field(None, description="喷嘴伸出量 [mm]")
    nozzle_hole_diameter: Optional[float] = Field(None, description="喷嘴孔直径 [mm]")
    nozzle_sphere_radius: Optional[float] = Field(None, description="喷嘴球半径 [mm]")
    nozzle_contact_force: Optional[float] = Field(None, description="喷嘴接触力 [kN]")
    # --- 螺杆参数 ---
    screw_type: str = Field(default="", description="螺杆类型")
    screw_diameter: Optional[float] = Field(None, description="螺杆直径 [mm]")
    screw_length_to_diameter_ratio: Optional[float] = Field(None, description="长径比 L/D")
    screw_cross_sectional_area: Optional[float] = Field(None, description="螺杆截面积 [mm²]")
    screw_circumference: Optional[float] = Field(None, description="螺杆周长 [mm]")
    screw_compression_ratio: Optional[float] = Field(None, description="压缩比")
    screw_enhancement_ratio: Optional[float] = Field(None, description="增强比")
    # --- 塑化与注射能力 ---
    plasticizing_capacity: Optional[float] = Field(None, description="塑化能力 [g/h]")
    max_injection_stroke: Optional[float] = Field(None, description="最大注射行程 [mm]")
    max_injection_volume: Optional[float] = Field(None, description="理论射胶量 [cm³]")
    max_injection_weight: Optional[float] = Field(None, description="理论射胶量 [g]")
    barrel_heating_power: Optional[float] = Field(None, description="料筒加热功率 [kW]")
    # --- 控制系统能力（最大段数）---
    max_injection_stages: int = Field(default=6, description="最大注射段数")
    max_holding_stages: int = Field(default=5, description="最大保压段数")
    max_metering_stages: int = Field(default=4, description="最大计量段数")
    max_temperature_control_zones: int = Field(default=10, description="最大温控区域")
    # --- 单位设置 ---
    pressure_unit: str = Field(default="MPa", description="压力单位")
    speed_unit: str = Field(default="mm/s", description="速度单位")
    position_unit: str = Field(default="mm", description="位置单位")
    time_unit: str = Field(default="s", description="时间单位")
    back_pressure_unit: str = Field(default="MPa", description="背压单位")
    screw_rotation_unit: str = Field(default="rpm", description="螺杆转速单位")
    temperature_unit: str = Field(default="℃", description="温度单位")
    # --- 成型能力（设备极限）---
    max_injection_pressure: Optional[float] = Field(None, description="最大注射压力 [MPa]")
    max_injection_speed: Optional[float] = Field(None, description="最大注射速度 [mm/s]")
    max_holding_pressure: Optional[float] = Field(None, description="最大保压压力 [MPa]")
    max_holding_speed: Optional[float] = Field(None, description="最大保压速度 [mm/s]")
    max_metering_pressure: Optional[float] = Field(None, description="最大计量压力 [MPa]")
    max_screw_rotation_speed: Optional[float] = Field(None, description="最大螺杆转速 [rpm]")
    max_metering_back_pressure: Optional[float] = Field(None, description="最大计量背压 [MPa]")
    max_decompression_pressure: Optional[float] = Field(None, description="最大松退压力 [MPa]")
    max_decompression_speed: Optional[float] = Field(None, description="最大松退速度 [mm/s]")
    # --- HMI 可设定范围（界面限制）---
    max_set_injection_pressure: Optional[float] = Field(None, description="最大可设定注射压力 [MPa]")
    max_set_injection_speed: Optional[float] = Field(None, description="最大可设定注射速度 [mm/s]")
    max_set_holding_pressure: Optional[float] = Field(None, description="最大可设定保压压力 [MPa]")
    max_set_holding_speed: Optional[float] = Field(None, description="最大可设定保压速度 [mm/s]")
    max_set_metering_pressure: Optional[float] = Field(None, description="最大可设定计量压力 [MPa]")
    max_set_screw_rotation_speed: Optional[float] = Field(None, description="最大可设定螺杆转速 [rpm]")
    max_set_metering_back_pressure: Optional[float] = Field(None, description="最大可设定计量背压 [MPa]")
    max_set_decompression_pressure: Optional[float] = Field(None, description="最大可设定松退压力 [MPa]")
    max_set_decompression_speed: Optional[float] = Field(None, description="最大可设定松退速度 [mm/s]")


class InjectionMoldingMachineSchema(BaseSchema):
    """注塑机"""
    
    id: Optional[int] = Field(None, description="注塑机ID")
    # --- 状态信息 ---
    status: Optional[str] = Field(None, description="状态")
    # --- 基本信息 ---
    brand: Optional[str] = Field(None, description="品牌")
    model: Optional[str] = Field(None, description="设备型号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    location: Optional[str] = Field(None, description="位置")
    device_no: Optional[str] = Field(None, description="设备编号")
    asset_no: Optional[str] = Field(None, description="资产编号")
    machine_type: Optional[str] = Field(None, description="设备类型")
    drive_system: Optional[str] = Field(None, description="驱动系统")
    unit_count: int = Field(default=1, description="射台数量")
    # --- 控制器信息 ---
    controller_model: str = Field(default="", description="控制器型号")
    controller_version: str = Field(default="", description="控制器版本")
    # --- 通讯能力 ---
    is_comm_enabled: bool = Field(default=False, description="是否支持通讯")
    communication_protocol: str = Field(default="", description="通讯协议")
    communication_ip: Optional[str] = Field(None, description="通讯IP")
    last_comm_time: Optional[str] = Field(None, description="上次通讯时间")
    # --- 默认单位系统（由控制器统一设定） ---
    pressure_unit: str = Field(default='bar', description="压力单位")
    speed_unit: str = Field(default='mm/s', description="速度单位")
    position_unit: str = Field(default='mm', description="位置单位")
    time_unit: str = Field(default='s', description="时间单位")
    back_pressure_unit: str = Field(default='bar', description="背压单位")
    screw_rotation_unit: str = Field(default='rpm', description="螺杆转速单位")
    temperature_unit: str = Field(default='℃', description="温度单位")
    clamping_force_unit: str = Field(default='ton', description="锁模力单位")
    # --- 注射单元 ---
    injection_units: Optional[List[InjectionUnitSchema]] = Field(None, description="射台参数")
    # --- 模板参数 ---
    # 定模板
    fixed_platen_width: Optional[float] = Field(None, description="定模板宽度 [mm]")
    fixed_platen_height: Optional[float] = Field(None, description="定模板高度 [mm]")
    fixed_platen_thickness: Optional[float] = Field(None, description="定模板厚度 [mm]")
    locating_hole_diameter: Optional[float] = Field(None, description="定位孔直径 [mm]")
    # 动模板
    moving_platen_width: Optional[float] = Field(None, description="动模板宽度 [mm]")
    moving_platen_height: Optional[float] = Field(None, description="动模板高度 [mm]")
    moving_platen_thickness: Optional[float] = Field(None, description="动模板厚度 [mm]")
    # --- 拉杆（哥林柱）---
    tie_bar_spacing_width: Optional[float] = Field(None, description="拉杆（格林柱）水平间距 [mm]")
    tie_bar_spacing_height: Optional[float] = Field(None, description="拉杆（格林柱）垂直间距 [mm]")
    tie_bar_diameter: Optional[float] = Field(None, description="拉杆（格林柱）直径 [mm]")
    tie_bar_count: Optional[int] = Field(None, description="拉杆（格林柱）数量")
    # --- 模板间距（物理极限）---
    min_platen_spacing: Optional[float] = Field(None, description="最小模板间距 [mm]")
    max_platen_spacing: Optional[float] = Field(None, description="最大模板间距 [mm]")
    # --- 容模参数（工程推荐） ---
    min_mold_length: Optional[float] = Field(None, description="最小容模水平尺寸 [mm]")
    max_mold_length: Optional[float] = Field(None, description="最大容模水平尺寸 [mm]")
    min_mold_width: Optional[float] = Field(None, description="最小容模垂直尺寸 [mm]")
    max_mold_width: Optional[float] = Field(None, description="最大容模垂直尺寸 [mm]")
    min_mold_thickness: Optional[float] = Field(None, description="最小容模厚度 [mm]")
    max_mold_thickness: Optional[float] = Field(None, description="最大容模厚度 [mm]")
    max_opening_stroke: Optional[float] = Field(None, description="最大开模行程 [mm]")
    # --- 锁模性能 ---
    clamping_type: str = Field(default="", description="锁模类型")
    max_clamping_force: Optional[float] = Field(None, description="最大锁模力 [ton]")
    # --- 顶出系统 ---
    ejection_type: str = Field(default="", description="顶出类型")
    ejection_mode: str = Field(default="", description="顶出模式")
    ejection_stroke: Optional[float] = Field(None, description="顶出行程 [mm]")
    ejection_force: Optional[float] = Field(None, description="顶出力 [kN]")
    # --- 尺寸信息 ---
    size_length: Optional[float] = Field(None, description="机台外形尺寸长 [mm]")
    size_width: Optional[float] = Field(None, description="机台外形尺寸宽 [mm]")
    size_height: Optional[float] = Field(None, description="机台外形尺寸高[mm]")
    machine_weight: Optional[float] = Field(None, description="机台重量 [kg]")
    motor_power: Optional[float] = Field(None, description="电机功率 [kW]")
    heater_power: Optional[float] = Field(None, description="电热功率 [kW]")
    rated_power: Optional[float] = Field(None, description="额定功率 [kW]")
    # --- 日期 ---
    manufacture_date: Optional[date] = Field(None, description="制造日期")
    commissioning_date: Optional[date] = Field(None, description="投产日期")
    
    @field_validator('communication_ip')
    @classmethod
    def validate_ip(cls, v: Optional[str]) -> Optional[str]:
        import re
        if v is None or v == "":
            return v
        pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(pattern, v):
            raise ValueError("请输入有效的IPv4地址")
        return v


class InjectionMachineListSchema(PaginationBaseSchema):
    """注塑机列表"""
    
    status: Optional[str] = Field(None, description="状态")
    brand: Optional[str] = Field(None, description="品牌")
    model: Optional[str] = Field(None, description="型号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    location: Optional[str] = Field(None, description="位置")
    device_no: Optional[str] = Field(None, description="设备编号")
    asset_no: Optional[str] = Field(None, description="资产编号")
    machine_type: Optional[str] = Field(None, description="设备类型")
    drive_system: Optional[str] = Field(None, description="驱动系统")
    unit_count: Optional[int] = Field(None, description="射台数量")