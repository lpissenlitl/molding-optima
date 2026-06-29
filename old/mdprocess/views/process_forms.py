from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema


class GetProcessListSchema(BaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)  # 所属公司
    mold_id = fields.Integer(required=False, allow_none=True)
    product_catalog = fields.String(required=False, allow_none=True)  # 制品大类
    product_type = fields.String(required=False, allow_none=True)  # 制品类型

    process_no = fields.Integer(required=False, allow_none=True)
    data_sources = fields.String(required=False, allow_none=True)  # 数据来源
    mold_trials_no = fields.String(required=False, allow_none=True)  # 试模次数
    machine_id = fields.Integer(required=False, allow_none=True)
    machine_data_source= fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    polymer_id = fields.Integer(required=False, allow_none=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    product_name= fields.String(required=False, allow_none=True)
    product_catalog= fields.String(required=False, allow_none=True)
    product_type= fields.String(required=False, allow_none=True)
    polymer_abbreviation= fields.String(required=False, allow_none=True)
    polymer_trademark= fields.String(required=False, allow_none=True)


# 工艺参数
class ProcessSchema(BaseSchema):

    id = fields.Integer(required=False, allow_none=True)  # 工艺记录id
    company_id = fields.Integer(required=False, allow_none=True)  # 所属公司

    mold_id = fields.Integer(required=False, allow_none=True)
    product_catalog = fields.String(required=False, allow_none=True)  # 制品大类
    product_type = fields.String(required=False, allow_none=True)  # 制品类型

    machine_id = fields.Integer(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    polymer_id = fields.Integer(required=False, allow_none=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)

    process_no = fields.String(required=False, allow_none=True)
    data_sources = fields.String(required=False, allow_none=True)  # 数据来源
    mold_trials_no = fields.String(required=False, allow_none=True)  # 试模次数
    mold_no = fields.String(required=False, allow_none=True)

    product_name = fields.String(required=False, allow_none=True)
    product_catalog = fields.String(required=False, allow_none=True)  # 制品大类
    product_type = fields.String(required=False, allow_none=True)  # 制品类型

    machine_id = fields.Integer(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    polymer_id = fields.Integer(required=False, allow_none=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)

    max_injection_volume = fields.Float(required=False, allow_none=True)
    screw_measure_position = fields.Float(required=False, allow_none=True)
    screw_diameter = fields.Float(required=False, allow_none=True)
    enhancement_ratio = fields.String(required=False, allow_none=True)
    screw_moving_volume = fields.Float(required=False, allow_none=True)
    

    barrel_temperature_stage = fields.Integer(required=False, allow_none=True)  # 温度段数	
    nozzle_temperature = fields.Float(required=False, allow_none=True)  # 喷嘴温度	
    nozzle_temperature_upper_tolerance = fields.Float(required=False, allow_none=True)  # 喷嘴温度上偏差设定值	
    nozzle_temperature_lower_tolerance = fields.Float(required=False, allow_none=True)  # 喷嘴温度下偏差设定值	
    barrel_temperature_1 = fields.Float(required=False, allow_none=True)  # 料筒温度1段	
    barrel_temperature_upper_tolerance_1 = fields.Float(required=False, allow_none=True)  # 料筒温度1段上偏差设定值	
    barrel_temperature_lower_tolerance_1 = fields.Float(required=False, allow_none=True)  # 料筒温度1段下偏差设定值	
    barrel_temperature_2 = fields.Float(required=False, allow_none=True)  # 料筒温度2段	
    barrel_temperature_upper_tolerance_2 = fields.Float(required=False, allow_none=True)  # 料筒温度2段上偏差设定值	
    barrel_temperature_lower_tolerance_2 = fields.Float(required=False, allow_none=True)  # 料筒温度2段下偏差设定值	
    barrel_temperature_3 = fields.Float(required=False, allow_none=True)  # 料筒温度3段	
    barrel_temperature_upper_tolerance_3 = fields.Float(required=False, allow_none=True)  # 料筒温度3段上偏差设定值	
    barrel_temperature_lower_tolerance_3 = fields.Float(required=False, allow_none=True)  # 料筒温度3段下偏差设定值	
    barrel_temperature_4 = fields.Float(required=False, allow_none=True)  # 料筒温度4段	
    barrel_temperature_upper_tolerance_4 = fields.Float(required=False, allow_none=True)  # 料筒温度4段上偏差设定值	
    barrel_temperature_lower_tolerance_4 = fields.Float(required=False, allow_none=True)  # 料筒温度4段下偏差设定值	
    barrel_temperature_5 = fields.Float(required=False, allow_none=True)  # 料筒温度5段	
    barrel_temperature_upper_tolerance_5 = fields.Float(required=False, allow_none=True)  # 料筒温度5段上偏差设定值	
    barrel_temperature_lower_tolerance_5 = fields.Float(required=False, allow_none=True)  # 料筒温度5段下偏差设定值	
    barrel_temperature_6 = fields.Float(required=False, allow_none=True)  # 料筒温度6段	
    barrel_temperature_upper_tolerance_6 = fields.Float(required=False, allow_none=True)  # 料筒温度6段上偏差设定值	
    barrel_temperature_lower_tolerance_6 = fields.Float(required=False, allow_none=True)  # 料筒温度6段下偏差设定值	
    barrel_temperature_7 = fields.Float(required=False, allow_none=True)  # 料筒温度7段	
    barrel_temperature_8 = fields.Float(required=False, allow_none=True)  # 料筒温度8段	
    barrel_temperature_9 = fields.Float(required=False, allow_none=True)  # 料筒温度9段	
    injection_stage = fields.Integer(required=False, allow_none=True)  # 注射段数	
    injection_time =fields.Float(required=False, allow_none=True)  # 注射时间	
    injection_delay_time = fields.Float(required=False, allow_none=True)  # 注射延迟时间	
    injection_pressure_1 = fields.Float(required=False, allow_none=True)  # 注射一段压力
    injection_pressure_2 = fields.Float(required=False, allow_none=True)  # 注射二段压力
    injection_pressure_3 = fields.Float(required=False, allow_none=True)  # 注射三段压力
    injection_pressure_4 = fields.Float(required=False, allow_none=True)  # 注射四段压力
    injection_pressure_5 = fields.Float(required=False, allow_none=True)  # 注射五段压力
    injection_pressure_6 = fields.Float(required=False, allow_none=True)  # 注射六段压力
    injection_velocity_1 = fields.Float(required=False, allow_none=True)  # 注射一段速度
    injection_velocity_2 = fields.Float(required=False, allow_none=True)  # 注射二段速度
    injection_velocity_3 = fields.Float(required=False, allow_none=True)  # 注射三段速度
    injection_velocity_4 = fields.Float(required=False, allow_none=True)  # 注射四段速度
    injection_velocity_5 = fields.Float(required=False, allow_none=True)  # 注射五段速度
    injection_velocity_6 = fields.Float(required=False, allow_none=True)  # 注射六段速度
    injection_ending_position = fields.Float(required=False, allow_none=True)  # 注射终止位置
    injection_position_1 = fields.Float(required=False, allow_none=True)  # 注射一段切换位置
    injection_position_2 = fields.Float(required=False, allow_none=True)  # 注射二段切换位置
    injection_position_3 = fields.Float(required=False, allow_none=True)  # 注射三段切换位置
    injection_position_4 = fields.Float(required=False, allow_none=True)  # 注射四段切换位置
    injection_position_5 = fields.Float(required=False, allow_none=True)  # 注射五段切换位置
    injection_position_6 = fields.Float(required=False, allow_none=True)  # 注射六段切换位置
    VP_switch_mode = fields.String(required=False, allow_none=True)  # VP切换模式	
    VP_switch_position = fields.Float(required=False, allow_none=True)  # VP切换位置	
    VP_switch_time = fields.Float(required=False, allow_none=True)  # VP切换时间	
    VP_switch_pressure = fields.Float(required=False, allow_none=True)  # VP切换压力	
    VP_switch_velocity = fields.Float(required=False, allow_none=True)  # VP切换速度	
    holding_stage = fields.Float(required=False, allow_none=True)  # 保压段数	
    holding_pressure_1 = fields.Float(required=False, allow_none=True)  # 保压一段压力
    holding_pressure_2 = fields.Float(required=False, allow_none=True)  # 保压二段压力
    holding_pressure_3 = fields.Float(required=False, allow_none=True)  # 保压三段压力
    holding_pressure_4 = fields.Float(required=False, allow_none=True)  # 保压四段压力
    holding_pressure_5 = fields.Float(required=False, allow_none=True)  # 保压五段压力
    holding_velocity_1 = fields.Float(required=False, allow_none=True)  # 保压一段速度
    holding_velocity_2 = fields.Float(required=False, allow_none=True)  # 保压二段速度
    holding_velocity_3 = fields.Float(required=False, allow_none=True)  # 保压三段速度
    holding_velocity_4 = fields.Float(required=False, allow_none=True)  # 保压四段速度
    holding_velocity_5 = fields.Float(required=False, allow_none=True)  # 保压五段速度
    holding_time_1 = fields.Float(required=False, allow_none=True)  # 保压一段时间
    holding_time_2 = fields.Float(required=False, allow_none=True)  # 保压二段时间
    holding_time_3 = fields.Float(required=False, allow_none=True)  # 保压三段时间
    holding_time_4 = fields.Float(required=False, allow_none=True)  # 保压四段时间
    holding_time_5 = fields.Float(required=False, allow_none=True)  # 保压五段时间
    cooling_time = fields.Float(required=False, allow_none=True)  # 冷却时间	
    metering_mode = fields.String(required=False, allow_none=True)  # 计量模式	
    metering_stage = fields.Integer(required=False, allow_none=True)  # 计量段数	
    metering_delay_time = fields.Float(required=False, allow_none=True)  # 计量延迟时间	
    metering_pressure_1 = fields.Float(required=False, allow_none=True)  # 计量一段压力
    metering_pressure_2 = fields.Float(required=False, allow_none=True)  # 计量二段压力
    metering_pressure_3 = fields.Float(required=False, allow_none=True)  # 计量三段压力
    metering_pressure_4 = fields.Float(required=False, allow_none=True)  # 计量四段压力
    metering_screw_rotation_speed_1 = fields.Float(required=False, allow_none=True)  # 计量一段螺杆转速
    metering_screw_rotation_speed_2 = fields.Float(required=False, allow_none=True)  # 计量二段螺杆转速
    metering_screw_rotation_speed_3 = fields.Float(required=False, allow_none=True)  # 计量三段螺杆转速
    metering_screw_rotation_speed_4 = fields.Float(required=False, allow_none=True)  # 计量四段螺杆转速
    metering_back_pressure_1 = fields.Float(required=False, allow_none=True)  # 计量一段背压
    metering_back_pressure_2 = fields.Float(required=False, allow_none=True)  # 计量二段背压
    metering_back_pressure_3 = fields.Float(required=False, allow_none=True)  # 计量三段背压
    metering_back_pressure_4 = fields.Float(required=False, allow_none=True)  # 计量四段背压
    metering_position_1 = fields.Float(required=False, allow_none=True)  # 计量一段切换位置
    metering_position_2 = fields.Float(required=False, allow_none=True)  # 计量二段切换位置
    metering_position_3 = fields.Float(required=False, allow_none=True)  # 计量三段切换位置
    metering_position_4 = fields.Float(required=False, allow_none=True)  # 计量四段切换位置
    metering_ending_position = fields.Float(required=False, allow_none=True)  # 计量终止位置
    decompressure_mode_before_metering = fields.String(required=False, allow_none=True)  # 计量前松退模式
    decompressure_pressure_before_metering = fields.Float(required=False, allow_none=True)  # 计量前松退压力
    decompressure_velocity_before_metering = fields.Float(required=False, allow_none=True)  # 计量前松退速度
    decompressure_distance_before_metering = fields.Float(required=False, allow_none=True)  # 计量前松退距离
    decompressure_time_before_metering = fields.Float(required=False, allow_none=True)  # 计量前松退时间
    decompressure_delay_time_before_metering = fields.Float(required=False, allow_none=True)  # 计量前松退延时
    decompressure_mode_after_metering = fields.String(required=False, allow_none=True)  # 计量后松退模式
    decompressure_pressure_after_metering = fields.Float(required=False, allow_none=True)  # 计量后松退压力
    decompressure_velocity_after_metering = fields.Float(required=False, allow_none=True)  # 计量后松退速度
    decompressure_distance_after_metering = fields.Float(required=False, allow_none=True)  # 计量后松退距离
    decompressure_time_after_metering = fields.Float(required=False, allow_none=True)  # 计量后松退时间


class HandleMultipleProcessSchema(BaseSchema):
    process_id_list = fields.List(fields.Integer())
    flag = fields.String(default="default") # 标记处理方式

