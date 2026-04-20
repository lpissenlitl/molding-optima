from django.db import models
from gis.common.django_ext.models import ExtraBaseModel, BaseModel
from gis.admin.models import Company

from gis.common.django_ext.mongo_dao import BaseDoc


# 工艺初始化
class ProcessIndex(ExtraBaseModel):

    id = models.AutoField(db_column='id', primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    status = models.IntegerField(db_column='status', blank=True, default=0)  # 状态
    process_no = models.CharField(db_column='process_no', max_length=45, null=True)  # 工艺编号
    # 1.手动录入 2.试模参数 3.读取MES 4.工艺移植 5.工艺优化 6.模流分析
    data_sources = models.CharField(db_column='data_sources', max_length=45, null=True)  # 数据来源
    mold_trials_no = models.CharField(db_column='mold_trials_no', max_length=45, null=True)  # 试模次数

    mold_id = models.IntegerField(db_column='mold_id', blank=True, null=True)  # 模具id
    mold_no = models.CharField(db_column='mold_no', max_length=45, null=True)  # 模具编号
    cavity_num = models.CharField(db_column='cavity_num', max_length=45, null=True)  # 型腔数量
    runner_length = models.FloatField(db_column='runner_length', blank=True, null=True)  # 流道长度
    runner_weight = models.FloatField(db_column='runner_weight', blank=True, null=True)  # 流道重量
    gate_type = models.CharField(db_column='gate_type',  max_length=45, null=True)  # 浇口类别
    gate_num = models.IntegerField(db_column='gate_num', blank=True)  # 浇口个数
    gate_shape = models.CharField(db_column='gate_shape',  max_length=45, null=True)  # 浇口形状
    gate_area = models.FloatField(db_column='gate_area', blank=True, null=True)  # 浇口横截面积
    gate_radius = models.FloatField(db_column='gate_radius', blank=True, null=True)  # 浇口半径(圆)
    gate_length = models.FloatField(db_column='gate_length', blank=True, null=True)  # 浇口长(矩形)
    gate_width = models.FloatField(db_column='gate_width', blank=True, null=True)  # 浇口宽(矩形)
    
    inject_part = models.CharField(db_column='inject_part', max_length=45, null=True)  # 工艺射台
    product_no = models.CharField(db_column='product_no', max_length=45, null=True)  # 制品编号
    product_category = models.CharField(db_column='product_category', max_length=45, null=True)  # 制品类别

    product_type = models.CharField(db_column='product_type', max_length=45, null=True)  # 制品类别
    product_name = models.CharField(db_column='product_name', max_length=45, null=True)  # 制品名称
    product_total_weight = models.FloatField(db_column='product_total_weight', blank=True, null=True)  # 总重量
    product_ave_thickness = models.FloatField(db_column='product_ave_thickness', blank=True, null=True)  # 制品平均厚度
    product_max_thickness = models.FloatField(db_column='product_max_thickness', blank=True, null=True)  # 制品最大厚度
    product_max_length = models.FloatField(db_column='product_max_length', blank=True, null=True)  # 制品最大长度

    machine_id = models.IntegerField(db_column='machine_id', blank=True, null=True)  # 注塑机id
    machine_data_source = models.CharField(db_column='machine_data_source', max_length=45, null=True)  # 注塑机来源
    machine_trademark = models.CharField(db_column='machine_trademark', max_length=45, null=True)  # 注塑机类别
    machine_serial_no = models.CharField(db_column='machine_serial_no', max_length=45, null=True)  # 注塑机设备编码

    polymer_id = models.IntegerField(db_column='polymer_id', blank=True, null=True)  # 塑料id
    polymer_abbreviation = models.CharField(db_column='polymer_abbreviation', max_length=45, null=True)  # 塑料简称
    polymer_trademark = models.CharField(db_column='polymer_trademark', max_length=45, null=True)  # 塑料牌号

    injection_stage = models.IntegerField(db_column='injection_stage', blank=True, null=True)  # 注射段数
    holding_stage = models.IntegerField(db_column='holding_stage', blank=True, null=True)  # 计量段数
    VP_switch_mode = models.CharField(db_column='VP_switch_mode', max_length=45, null=True)  # VP切换模式
    metering_stage = models.IntegerField(db_column='metering_stage', blank=True, null=True)  # 计量段数
    decompressure_mode_before_metering = models.CharField(db_column='decompressure_mode_before_metering', max_length=45, null=True)  # 储前松退模式
    decompressure_mode_after_metering = models.CharField(db_column='decompressure_mode_after_metering', max_length=45, null=True)  # 储后松退模式
    barrel_temperature_stage = models.IntegerField(db_column='barrel_temperature_stage', blank=True, null=True)  # 料筒温度段数

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'process_index'


# 规则关键词
class RuleKeyword(ExtraBaseModel):

    id = models.AutoField(db_column='id', primary_key=True)

    name = models.CharField(db_column='name', max_length=45, null=True)  # 关键字的名字
    level = models.IntegerField(db_column='level', blank=True, default=0)  # 模糊级别：3或5
    all_range_min = models.IntegerField(db_column='all_range_min', blank=True, null=True)  # 参数取值范围最小值
    all_range_max = models.IntegerField(db_column='all_range_max', blank=True, null=True)  # 参数取值范围最大值
    action_range_min = models.IntegerField(db_column='action_range_min', blank=True, null=True)  # 参数调整区间最小值
    action_range_max = models.IntegerField(db_column='action_range_max', blank=True, null=True)  # 参数调整区间最大值
    action_max_val = models.IntegerField(db_column='action_max_val', blank=True, null=True)  # 参数调整最大值
    keyword_type = models.CharField(db_column='keyword_type', max_length=45, null=True)  # 类型
    comment = models.CharField(db_column='comment', max_length=45, null=True)  # 注释

    subrule_no = models.CharField(db_column='subrule_no', max_length=45, null=True)
    product_small_type = models.CharField(db_column='product_small_type', max_length=45, null=True)
    polymer_abbreviation = models.CharField(db_column='polymer_abbreviation', max_length=45, null=True)
    rule_type = models.CharField(db_column='rule_type', max_length=45, null=True)
    show_on_page = models.BooleanField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'rule_keyword'


# 规则方法
class RuleMethod(ExtraBaseModel):

    id = models.AutoField(db_column='id', primary_key=True)
    
    polymer_abbreviation = models.CharField(db_column='polymer_abbreviation', max_length=45, null=True)  # 材料类别
    product_small_type = models.CharField(db_column='product_small_type', max_length=45, null=True)  # 制品类别
    rule_description = models.CharField(db_column='rule_description', max_length=500, null=True)  # 规则描述
    rule_explanation = models.CharField(db_column='rule_explanation', max_length=500, null=True)  # 规则解释

    is_auto = models.IntegerField(default=0)
    enable = models.IntegerField(default=0)

    defect_name = models.CharField(db_column='defect_name', max_length=45, null=True)
    defect_desc = models.CharField(db_column='defect_desc', max_length=45, null=True)
    subrule_no = models.CharField(db_column='subrule_no', max_length=45, null=True)
    rule_type = models.CharField(db_column='rule_type', max_length=45, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.IntegerField(default=0)

    priority = models.FloatField()

    class Meta:
        db_table = 'rule_method'


# 暂时未用
class Process(ExtraBaseModel):
    id = models.AutoField(db_column='id', primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    process_no = models.CharField(max_length=45, null=True)
    mold_id = models.IntegerField()
    mold_no = models.CharField(max_length=500, null=True)

    product_name = models.CharField(max_length=500, null=True)
    product_catalog = models.CharField(db_column='product_catalog', max_length=500, null=True)  # 制品大类
    product_type = models.CharField(db_column='product_type', max_length=500, null=True)  # 制品类型

    machine_id = models.IntegerField()
    machine_data_source = models.CharField(max_length=45, null=True)
    machine_trademark = models.CharField(db_column='machine_trademark', max_length=500, null=True)

    polymer_id = models.IntegerField()
    polymer_abbreviation = models.CharField(db_column='polymer_abbreviation', max_length=500, null=True)
    polymer_trademark = models.CharField(db_column='polymer_trademark', max_length=500, null=True)

    max_injection_volume = models.FloatField()
    screw_measure_position = models.FloatField()
    screw_diameter = models.FloatField()
    enhancement_ratio = models.CharField(max_length=45, null=True)
    screw_moving_volume = models.FloatField()
    
    barrel_temperature_stage = models.IntegerField(db_column='barrel_temperature_stage', blank=True, null=True)  # 温度段数	
    nozzle_temperature = models.FloatField(db_column='nozzle_temperature', blank=True, null=True)  # 喷嘴温度	
    nozzle_temperature_upper_tolerance = models.FloatField(db_column='nozzle_temperature_upper_tolerance', blank=True, null=True)  # 喷嘴温度上偏差设定值	
    nozzle_temperature_lower_tolerance = models.FloatField(db_column='nozzle_temperature_lower_tolerance', blank=True, null=True)  # 喷嘴温度下偏差设定值	
    barrel_temperature_1 = models.FloatField(db_column='barrel_temperature_1', blank=True, null=True)  # 料筒温度1段	
    barrel_temperature_upper_tolerance_1 = models.FloatField(db_column='barrel_temperature_upper_tolerance_1', blank=True, null=True)  # 料筒温度1段上偏差设定值	
    barrel_temperature_lower_tolerance_1 = models.FloatField(db_column='barrel_temperature_lower_tolerance_1', blank=True, null=True)  # 料筒温度1段下偏差设定值	
    barrel_temperature_2 = models.FloatField(db_column='barrel_temperature_2', blank=True, null=True)  # 料筒温度2段	
    barrel_temperature_upper_tolerance_2 = models.FloatField(db_column='barrel_temperature_upper_tolerance_2', blank=True, null=True)  # 料筒温度2段上偏差设定值	
    barrel_temperature_lower_tolerance_2 = models.FloatField(db_column='barrel_temperature_lower_tolerance_2', blank=True, null=True)  # 料筒温度2段下偏差设定值	
    barrel_temperature_3 = models.FloatField(db_column='barrel_temperature_3', blank=True, null=True)  # 料筒温度3段	
    barrel_temperature_upper_tolerance_3 = models.FloatField(db_column='barrel_temperature_upper_tolerance_3', blank=True, null=True)  # 料筒温度3段上偏差设定值	
    barrel_temperature_lower_tolerance_3 = models.FloatField(db_column='barrel_temperature_lower_tolerance_3', blank=True, null=True)  # 料筒温度3段下偏差设定值	
    barrel_temperature_4 = models.FloatField(db_column='barrel_temperature_4', blank=True, null=True)  # 料筒温度4段	
    barrel_temperature_upper_tolerance_4 = models.FloatField(db_column='barrel_temperature_upper_tolerance_4', blank=True, null=True)  # 料筒温度4段上偏差设定值	
    barrel_temperature_lower_tolerance_4 = models.FloatField(db_column='barrel_temperature_lower_tolerance_4', blank=True, null=True)  # 料筒温度4段下偏差设定值	
    barrel_temperature_5 = models.FloatField(db_column='barrel_temperature_5', blank=True, null=True)  # 料筒温度5段	
    barrel_temperature_upper_tolerance_5 = models.FloatField(db_column='barrel_temperature_upper_tolerance_5', blank=True, null=True)  # 料筒温度5段上偏差设定值	
    barrel_temperature_lower_tolerance_5 = models.FloatField(db_column='barrel_temperature_lower_tolerance_5', blank=True, null=True)  # 料筒温度5段下偏差设定值	
    barrel_temperature_6 = models.FloatField(db_column='barrel_temperature_6', blank=True, null=True)  # 料筒温度6段	
    barrel_temperature_upper_tolerance_6 = models.FloatField(db_column='barrel_temperature_upper_tolerance_6', blank=True, null=True)  # 料筒温度6段上偏差设定值	
    barrel_temperature_lower_tolerance_6 = models.FloatField(db_column='barrel_temperature_lower_tolerance_6', blank=True, null=True)  # 料筒温度6段下偏差设定值
    barrel_temperature_7 = models.FloatField(db_column='barrel_temperature_7', blank=True, null=True)  # 料筒温度7段	
    barrel_temperature_8 = models.FloatField(db_column='barrel_temperature_8', blank=True, null=True)  # 料筒温度8段	
    barrel_temperature_9 = models.FloatField(db_column='barrel_temperature_9', blank=True, null=True)  # 料筒温度9段		
    injection_stage = models.IntegerField(db_column='injection_stage', blank=True, null=True)  # 注射段数	
    injection_time = models.FloatField(db_column='injection_time', blank=True, null=True)  # 注射时间	
    injection_delay_time = models.FloatField(db_column='injection_delay_time', blank=True, null=True)  # 注射延迟时间	
    injection_pressure_1 = models.FloatField(db_column='injection_pressure_1', blank=True, null=True)  # 注射一段压力
    injection_pressure_2 = models.FloatField(db_column='injection_pressure_2', blank=True, null=True)  # 注射二段压力
    injection_pressure_3 = models.FloatField(db_column='injection_pressure_3', blank=True, null=True)  # 注射三段压力
    injection_pressure_4 = models.FloatField(db_column='injection_pressure_4', blank=True, null=True)  # 注射四段压力
    injection_pressure_5 = models.FloatField(db_column='injection_pressure_5', blank=True, null=True)  # 注射五段压力
    injection_pressure_6 = models.FloatField(db_column='injection_pressure_6', blank=True, null=True)  # 注射六段压力
    injection_velocity_1 = models.FloatField(db_column='injection_velocity_1', blank=True, null=True)  # 注射一段速度
    injection_velocity_2 = models.FloatField(db_column='injection_velocity_2', blank=True, null=True)  # 注射二段速度
    injection_velocity_3 = models.FloatField(db_column='injection_velocity_3', blank=True, null=True)  # 注射三段速度
    injection_velocity_4 = models.FloatField(db_column='injection_velocity_4', blank=True, null=True)  # 注射四段速度
    injection_velocity_5 = models.FloatField(db_column='injection_velocity_5', blank=True, null=True)  # 注射五段速度
    injection_velocity_6 = models.FloatField(db_column='injection_velocity_6', blank=True, null=True)  # 注射六段速度
    injection_ending_position = models.FloatField(db_column='injection_ending_position', blank=True, null=True)  # 注射终止位置
    injection_position_1 = models.FloatField(db_column='injection_position_1', blank=True, null=True)  # 注射一段切换位置
    injection_position_2 = models.FloatField(db_column='injection_position_2', blank=True, null=True)  # 注射二段切换位置
    injection_position_3 = models.FloatField(db_column='injection_position_3', blank=True, null=True)  # 注射三段切换位置
    injection_position_4 = models.FloatField(db_column='injection_position_4', blank=True, null=True)  # 注射四段切换位置
    injection_position_5 = models.FloatField(db_column='injection_position_5', blank=True, null=True)  # 注射五段切换位置
    injection_position_6 = models.FloatField(db_column='injection_position_6', blank=True, null=True)  # 注射六段切换位置
    VP_switch_mode = models.CharField(db_column='VP_switch_mode', max_length=45, blank=True, null=True)  # VP切换模式	
    VP_switch_position = models.FloatField(db_column='VP_switch_position', blank=True, null=True)  # VP切换位置	
    VP_switch_time = models.FloatField(db_column='VP_switch_time', blank=True, null=True)  # VP切换时间	
    VP_switch_pressure = models.FloatField(db_column='VP_switch_pressure', blank=True, null=True)  # VP切换压力	
    VP_switch_velocity = models.FloatField(db_column='VP_switch_velocity', blank=True, null=True)  # VP切换速度	
    holding_stage = models.IntegerField(db_column='holding_stage', blank=True, null=True)  # 保压段数	
    holding_pressure_1 = models.FloatField(db_column='holding_pressure_1', blank=True, null=True)  # 保压一段压力
    holding_pressure_2 = models.FloatField(db_column='holding_pressure_2', blank=True, null=True)  # 保压二段压力
    holding_pressure_3 = models.FloatField(db_column='holding_pressure_3', blank=True, null=True)  # 保压三段压力
    holding_pressure_4 = models.FloatField(db_column='holding_pressure_4', blank=True, null=True)  # 保压四段压力
    holding_pressure_5 = models.FloatField(db_column='holding_pressure_5', blank=True, null=True)  # 保压五段压力
    holding_velocity_1 = models.FloatField(db_column='holding_velocity_1', blank=True, null=True)  # 保压一段速度
    holding_velocity_2 = models.FloatField(db_column='holding_velocity_2', blank=True, null=True)  # 保压二段速度
    holding_velocity_3 = models.FloatField(db_column='holding_velocity_3', blank=True, null=True)  # 保压三段速度
    holding_velocity_4 = models.FloatField(db_column='holding_velocity_4', blank=True, null=True)  # 保压四段速度
    holding_velocity_5 = models.FloatField(db_column='holding_velocity_5', blank=True, null=True)  # 保压五段速度
    holding_time_1 = models.FloatField(db_column='holding_time_1', blank=True, null=True)  # 保压一段时间
    holding_time_2 = models.FloatField(db_column='holding_time_2', blank=True, null=True)  # 保压二段时间
    holding_time_3 = models.FloatField(db_column='holding_time_3', blank=True, null=True)  # 保压三段时间
    holding_time_4 = models.FloatField(db_column='holding_time_4', blank=True, null=True)  # 保压四段时间
    holding_time_5 = models.FloatField(db_column='holding_time_5', blank=True, null=True)  # 保压五段时间
    cooling_time = models.FloatField(db_column='cooling_time', blank=True, null=True)  # 冷却时间	
    metering_mode = models.CharField(db_column='metering_mode', max_length=45, blank=True, null=True)  # 计量模式	
    metering_stage = models.IntegerField(db_column='metering_stage', blank=True, null=True)  # 计量段数	
    metering_delay_time = models.FloatField(db_column='metering_delay_time', blank=True, null=True)  # 计量延迟时间	
    metering_pressure_1 = models.FloatField(db_column='metering_pressure_1', blank=True, null=True)  # 计量一段压力
    metering_pressure_2 = models.FloatField(db_column='metering_pressure_2', blank=True, null=True)  # 计量二段压力
    metering_pressure_3 = models.FloatField(db_column='metering_pressure_3', blank=True, null=True)  # 计量三段压力
    metering_pressure_4 = models.FloatField(db_column='metering_pressure_4', blank=True, null=True)  # 计量四段压力
    metering_screw_rotation_speed_1 = models.FloatField(db_column='metering_screw_rotation_speed_1', blank=True, null=True)  # 计量一段螺杆转速
    metering_screw_rotation_speed_2 = models.FloatField(db_column='metering_screw_rotation_speed_2', blank=True, null=True)  # 计量二段螺杆转速
    metering_screw_rotation_speed_3 = models.FloatField(db_column='metering_screw_rotation_speed_3', blank=True, null=True)  # 计量三段螺杆转速
    metering_screw_rotation_speed_4 = models.FloatField(db_column='metering_screw_rotation_speed_4', blank=True, null=True)  # 计量四段螺杆转速
    metering_back_pressure_1 = models.FloatField(db_column='metering_back_pressure_1', blank=True, null=True)  # 计量一段背压
    metering_back_pressure_2 = models.FloatField(db_column='metering_back_pressure_2', blank=True, null=True)  # 计量二段背压
    metering_back_pressure_3 = models.FloatField(db_column='metering_back_pressure_3', blank=True, null=True)  # 计量三段背压
    metering_back_pressure_4 = models.FloatField(db_column='metering_back_pressure_4', blank=True, null=True)  # 计量四段背压
    metering_position_1 = models.FloatField(db_column='metering_position_1', blank=True, null=True)  # 计量一段切换位置
    metering_position_2 = models.FloatField(db_column='metering_position_2', blank=True, null=True)  # 计量二段切换位置
    metering_position_3 = models.FloatField(db_column='metering_position_3', blank=True, null=True)  # 计量三段切换位置
    metering_position_4 = models.FloatField(db_column='metering_position_4', blank=True, null=True)  # 计量四段切换位置
    metering_ending_position = models.FloatField(db_column='metering_ending_position', blank=True, null=True)  # 计量终止位置
    decompressure_mode_before_metering = models.CharField(db_column='decompressure_mode_before_metering', max_length=45, blank=True, null=True)  # 计量前松退模式
    decompressure_pressure_before_metering = models.FloatField(db_column='decompressure_pressure_before_metering', blank=True, null=True)  # 计量前松退压力
    decompressure_velocity_before_metering = models.FloatField(db_column='decompressure_velocity_before_metering', blank=True, null=True)  # 计量前松退速度
    decompressure_distance_before_metering = models.FloatField(db_column='decompressure_distance_before_metering', blank=True, null=True)  # 计量前松退距离
    decompressure_time_before_metering = models.FloatField(db_column='decompressure_time_before_metering', blank=True, null=True)  # 计量前松退时间
    decompressure_delay_time_before_metering = models.FloatField(db_column='decompressure_delay_time_before_metering', blank=True, null=True)  # 计量前松退延时
    decompressure_mode_after_metering = models.CharField(db_column='decompressure_mode_after_metering', max_length=45, blank=True, null=True)  # 计量后松退模式
    decompressure_pressure_after_metering = models.FloatField(db_column='decompressure_pressure_after_metering', blank=True, null=True)  # 计量后松退压力
    decompressure_velocity_after_metering = models.FloatField(db_column='decompressure_velocity_after_metering', blank=True, null=True)  # 计量后松退速度
    decompressure_distance_after_metering = models.FloatField(db_column='decompressure_distance_after_metering', blank=True, null=True)  # 计量后松退距离
    decompressure_time_after_metering = models.FloatField(db_column='decompressure_time_after_metering', blank=True, null=True)  # 计量后松退时间

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'process'
