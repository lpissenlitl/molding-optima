from django.db import models
from django.db.models import Max
from extensions.models import BusinessBaseModel


class ProcessCondition(BusinessBaseModel):
    """工艺条件"""
    
    # --- 状态信息 ---
    PROCESS_CONDITION_STATUS_CHOICES = [
        ('draft', '草稿'),          # 初始创建，未开始测试
        ('testing', '测试中'),       # 正在打样/验证（对应多条 ProcessParameter）
        ('approved', '已批准'),      # 合格工艺，可用于量产
        ('rejected', '已废弃'),      # 验证失败，不再使用
        ('obsolete', '已过时'),      # 曾经批准，但被新工艺替代
    ]
    status = models.CharField(null=True, max_length=20, verbose_name="状态")
    
    # --- 基本信息 ---
    condition_code = models.CharField(null=True, max_length=50, verbose_name="工艺条件编号")
    PROCESS_CONDITION_ORIGIN_CHOICES = [
        ('manual_creation', '手工新建'),          # 工程师从零创建
        ('template_based', '基于模板'),           # 从标准/历史模板复制启动
        ('ai_recommendation', 'AI 推荐启动'),      # 系统首次推荐一组参数作为起点
        ('doe_experiment', '实验设计（DOE）'),     # 来自结构化实验计划
        ('legacy_import', '历史工艺导入'),         # 从旧系统迁移
        ('equipment_capture', '设备参数捕获'),     # 来自设备参数
        ('process_transplant', '工艺移植'),      # 来自工艺移植算法
    ]
    origin_type = models.CharField(
        max_length=30,
        choices=PROCESS_CONDITION_ORIGIN_CHOICES,
        null=True,
        verbose_name="工艺起源类型"
    )
    process_context_snapshot = models.JSONField(
        null=True, 
        verbose_name="工艺条件快照",
        help_text="""
        {
            "version": "1.0",
            "captured_at": "2025-12-05T14:30:00Z",

            "machine": {
                "id": "ENGEL-800T-01",
                "model": "ENGEL e-motion 800",
                "screw_diameter": 55,
                "max_injection_volume": 1250,
            },
            "material": {
                "id": "PC-LEXAN-9034",
                "category": "Polycarbonate",
                "manufacturer": "SABIC",
            },
            "mold": {
                "id": "M-2025A",
                "cavities": 8,
                "hot_runner": true,
                "steel_type": "H13"
            },
            "hmi_to_std_mapping": {
                "IP": {
                "HMI_unit": "%",
                "HMI_max": 99,
                "std_unit": "MPa",
                "std_max": 120
                },
                "TEMP": {
                "HMI_unit": "°C",
                "HMI_max": 400,
                "std_unit": "°C",
                "std_max": 400
                }
            }
        }
        """
    )
    
    # --- 模具信息 ---
    mold = models.ForeignKey(
        "masterdata.Mold", 
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
        verbose_name="模具信息"
    )
    shot_index = models.IntegerField(null=True, verbose_name="注射次数")
    
    # --- 注塑机信息 ---
    injection_machine = models.ForeignKey(
        "masterdata.InjectionMoldingMachine",
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
        verbose_name="注塑机信息"
    )
    injection_index = models.IntegerField(null=True, verbose_name="注射单元")
    
    # --- 材料信息 ---
    polymer = models.ForeignKey(
        "masterdata.Polymer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
        verbose_name="材料信息"
    )
    
    class Meta:
        verbose_name = "工艺条件"
        verbose_name_plural = verbose_name


class ProcessParameter(BusinessBaseModel):
    """工艺详情"""
    
    process_condition = models.ForeignKey(
        ProcessCondition, 
        on_delete=models.CASCADE,
        verbose_name="所属条件",
        related_name="process_parameters"
    )
    
    # --- 基本信息 ---
    parameter_code = models.CharField(
        max_length=50, 
        verbose_name="工艺参数编号",
        help_text="工艺参数编号"
    )

    PARAMETER_SOURCE_CHOICES = [
        ('unknown', '未知'),
        ('manual', '手工录入'),
        ('import', '外部导入'),
        ('algorithm_init', '算法初始化'),       # 通过初始化算法生成
        ('system_inferred', '系统推理'),        # 基于缺陷/反馈自动推理出的新参数
        ('manual_adjusted', '人工调整'),        # 用户手动修改
        ('equipment_sync', '设备同步'),         # 从机台读取的实际运行值
        ('template_copy', '模板复制'),          # 从历史工艺复制而来
    ]
    parameter_source = models.CharField(
        null=True,
        max_length=20,
        verbose_name="参数来源",
        choices=PARAMETER_SOURCE_CHOICES,
        default="unknown",
    )

    parent_parameter = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        related_name="children",
    )
    
    sequence_index = models.IntegerField(
        null=True,
        verbose_name="序列序号",
        default=0,
    )
    
    # --- 注射参数 ---
    injection_stages = models.IntegerField(null=True, verbose_name="注射段数 1-6")
    IV0 = models.FloatField(null=True, verbose_name="第一段注射速度")
    IP0 = models.FloatField(null=True, verbose_name="第一段注射压力")
    IL0 = models.FloatField(null=True, verbose_name="第一段注射位置")
    IV1 = models.FloatField(null=True, verbose_name="第二段注射速度")
    IP1 = models.FloatField(null=True, verbose_name="第二段注射压力")
    IL1 = models.FloatField(null=True, verbose_name="第二段注射位置")
    IV2 = models.FloatField(null=True, verbose_name="第三段注射速度")
    IP2 = models.FloatField(null=True, verbose_name="第三段注射压力")
    IL2 = models.FloatField(null=True, verbose_name="第三段注射位置")
    IV3 = models.FloatField(null=True, verbose_name="第四段注射速度")
    IP3 = models.FloatField(null=True, verbose_name="第四段注射压力")
    IL3 = models.FloatField(null=True, verbose_name="第四段注射位置")
    IV4 = models.FloatField(null=True, verbose_name="第五段注射速度")
    IP4 = models.FloatField(null=True, verbose_name="第五段注射压力")
    IL4 = models.FloatField(null=True, verbose_name="第五段注射位置")
    IV5 = models.FloatField(null=True, verbose_name="第六段注射速度")
    IP5 = models.FloatField(null=True, verbose_name="第六段注射压力")
    IL5 = models.FloatField(null=True, verbose_name="第六段注射位置")
    IT = models.FloatField(null=True, verbose_name="注射时间")
    IDT = models.FloatField(null=True, verbose_name="注射延时")
    
    # --- VP 切换参数 ---
    VPTM = models.IntegerField(null=True, verbose_name="VP切换模式")
    VPTL = models.FloatField(null=True, verbose_name="VP切换位置")
    VPTT = models.FloatField(null=True, verbose_name="VP切换时间")
    VPTP = models.FloatField(null=True, verbose_name="VP切换压力")
    VPTV = models.FloatField(null=True, verbose_name="VP切换速度")
    
    # --- 保压参数 ---
    holding_stages = models.IntegerField(null=True, verbose_name="保压段数 1-5")
    PP0 = models.FloatField(null=True, verbose_name="第一段保压压力")
    PV0 = models.FloatField(null=True, verbose_name="第一段保压速度")
    PT0 = models.FloatField(null=True, verbose_name="第一段保压时间")
    PP1 = models.FloatField(null=True, verbose_name="第二段保压压力")
    PV1 = models.FloatField(null=True, verbose_name="第二段保压速度")
    PT1 = models.FloatField(null=True, verbose_name="第二段保压时间")
    PP2 = models.FloatField(null=True, verbose_name="第三段保压压力")
    PV2 = models.FloatField(null=True, verbose_name="第三段保压速度")
    PT2 = models.FloatField(null=True, verbose_name="第三段保压时间")
    PP3 = models.FloatField(null=True, verbose_name="第四段保压压力")
    PV3 = models.FloatField(null=True, verbose_name="第四段保压速度")
    PT3 = models.FloatField(null=True, verbose_name="第四段保压时间")
    PP4 = models.FloatField(null=True, verbose_name="第五段保压压力")
    PV4 = models.FloatField(null=True, verbose_name="第五段保压速度")
    PT4 = models.FloatField(null=True, verbose_name="第五段保压时间")
    
    # --- 冷却参数 ---
    CT = models.FloatField(null=True, verbose_name="冷却时间")
    
    # --- 熔胶参数 ---
    metering_stages = models.IntegerField(null=True, verbose_name="熔胶段数 1-4")
    MP0 = models.FloatField(null=True, verbose_name="第一段熔胶压力")
    MSR0 = models.FloatField(null=True, verbose_name="第一段螺杆转速")
    MBP0 = models.FloatField(null=True, verbose_name="第一段背压")
    ML0 = models.FloatField(null=True, verbose_name="第一段熔胶位置")
    MP1 = models.FloatField(null=True, verbose_name="第二段熔胶压力")
    MSR1 = models.FloatField(null=True, verbose_name="第二段螺杆转速")
    MBP1 = models.FloatField(null=True, verbose_name="第二段背压")
    ML1 = models.FloatField(null=True, verbose_name="第二段熔胶位置")
    MP2 = models.FloatField(null=True, verbose_name="第三段熔胶压力")
    MSR2 = models.FloatField(null=True, verbose_name="第三段螺杆转速")
    MBP2 = models.FloatField(null=True, verbose_name="第三段背压")
    ML2 = models.FloatField(null=True, verbose_name="第三段熔胶位置")
    MP3 = models.FloatField(null=True, verbose_name="第四段熔胶压力")
    MSR3 = models.FloatField(null=True, verbose_name="第四段螺杆转速")
    MBP3 = models.FloatField(null=True, verbose_name="第四段背压")
    ML3 = models.FloatField(null=True, verbose_name="第四段熔胶位置")
    
    DMBM = models.IntegerField(null=True, verbose_name="熔胶前松退模式")
    DPBM = models.FloatField(null=True, verbose_name="熔胶前松退压力")
    DVBM = models.FloatField(null=True, verbose_name="熔胶前松退速度")
    DTBM = models.FloatField(null=True, verbose_name="熔胶前松退时间")
    DDBM = models.FloatField(null=True, verbose_name="熔胶前松退距离")

    DMAM = models.IntegerField(null=True, verbose_name="熔胶后松退模式")
    DPAM = models.FloatField(null=True, verbose_name="熔胶后松退压力")
    DVAM = models.FloatField(null=True, verbose_name="熔胶后松退速度")
    DTAM = models.FloatField(null=True, verbose_name="熔胶后松退时间")
    DDAM = models.FloatField(null=True, verbose_name="熔胶后松退距离")
    
    MDT = models.FloatField(null=True, verbose_name="熔胶延时")
    MEL = models.FloatField(null=True, verbose_name="熔胶终止位置")
    
    # --- 料筒温度参数 ---
    barrel_temperature_stages = models.IntegerField(null=True, verbose_name="料筒温度段数 1-8")
    NT = models.FloatField(null=True, verbose_name="料筒温度")
    BT1 = models.FloatField(null=True, verbose_name="第一段料筒温度")
    BT2 = models.FloatField(null=True, verbose_name="第二段料筒温度")
    BT3 = models.FloatField(null=True, verbose_name="第三段料筒温度")
    BT4 = models.FloatField(null=True, verbose_name="第四段料筒温度")
    BT5 = models.FloatField(null=True, verbose_name="第五段料筒温度")
    BT6 = models.FloatField(null=True, verbose_name="第六段料筒温度")
    BT7 = models.FloatField(null=True, verbose_name="第七段料筒温度")
    BT8 = models.FloatField(null=True, verbose_name="第八段料筒温度")
    BT9 = models.FloatField(null=True, verbose_name="第九段料筒温度")
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            last_idx = ProcessParameter.all_objects.filter(
                process_condition=self.process_condition
            ).aggregate(Max('sequence_index'))['sequence_index__max'] or 0
            
            self.sequence_index = last_idx + 1
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "工艺参数"
        verbose_name_plural = "工艺参数"


# class StandardParameter(BusinessBaseModel):
#     """工艺参数（标准量，暂时不用）"""
#     process_parameter = models.OneToOneField(
#         ProcessParameter, 
#         on_delete=models.CASCADE, 
#         verbose_name="工艺参数",
#         related_name="standard_parameter"
#     )

#     # --- 注射参数 ---
#     stage = models.IntegerField(null=True, verbose_name="注射段数 1-6")
#     injection_speed_1 = models.FloatField(null=True, verbose_name="第一段注射速度")
#     injection_pressure_1 = models.FloatField(null=True, verbose_name="第一段注射压力")
#     injection_position_1 = models.FloatField(null=True, verbose_name="第一段注射位置")
#     injection_speed_2 = models.FloatField(null=True, verbose_name="第二段注射速度")
#     injection_pressure_2 = models.FloatField(null=True, verbose_name="第二段注射压力")
#     injection_position_2 = models.FloatField(null=True, verbose_name="第二段注射位置")
#     injection_speed_3 = models.FloatField(null=True, verbose_name="第三段注射速度")
#     injection_pressure_3 = models.FloatField(null=True, verbose_name="第三段注射压力")
#     injection_position_3 = models.FloatField(null=True, verbose_name="第三段注射位置")
#     injection_speed_4 = models.FloatField(null=True, verbose_name="第四段注射速度")
#     injection_pressure_4 = models.FloatField(null=True, verbose_name="第四段注射压力")
#     injection_position_4 = models.FloatField(null=True, verbose_name="第四段注射位置")
#     injection_speed_5 = models.FloatField(null=True, verbose_name="第五段注射速度")
#     injection_pressure_5 = models.FloatField(null=True, verbose_name="第五段注射压力")
#     injection_position_5 = models.FloatField(null=True, verbose_name="第五段注射位置")
#     injection_speed_6 = models.FloatField(null=True, verbose_name="第六段注射速度")
#     injection_pressure_6 = models.FloatField(null=True, verbose_name="第六段注射压力")
#     injection_position_6 = models.FloatField(null=True, verbose_name="第六段注射位置")
#     injection_time = models.FloatField(null=True, verbose_name="注射时间")
#     delay_time = models.FloatField(null=True, verbose_name="注射延时")
    
#     # --- VP 切换参数 ---
#     vp_switch_mode = models.CharField(max_length=20, null=True, verbose_name="VP切换模式")
#     vp_switch_position = models.FloatField(null=True, verbose_name="VP切换位置")
#     vp_switch_time = models.FloatField(null=True, verbose_name="VP切换时间")
#     vp_switch_pressure = models.FloatField(null=True, verbose_name="VP切换压力")
#     vp_switch_speed = models.FloatField(null=True, verbose_name="VP切换速度")
    
#     # --- 保压参数 ---
#     stage = models.IntegerField(null=True, verbose_name="保压段数 1-5")
#     holding_pressure_1 = models.FloatField(null=True, verbose_name="第一段保压压力")
#     holding_speed_1 = models.FloatField(null=True, verbose_name="第一段保压速度")
#     holding_time_1 = models.FloatField(null=True, verbose_name="第一段保压时间")
#     holding_pressure_2 = models.FloatField(null=True, verbose_name="第二段保压压力")
#     holding_speed_2 = models.FloatField(null=True, verbose_name="第二段保压速度")
#     holding_time_2 = models.FloatField(null=True, verbose_name="第二段保压时间")
#     holding_pressure_3 = models.FloatField(null=True, verbose_name="第三段保压压力")
#     holding_speed_3 = models.FloatField(null=True, verbose_name="第三段保压速度")
#     holding_time_3 = models.FloatField(null=True, verbose_name="第三段保压时间")
#     holding_pressure_4 = models.FloatField(null=True, verbose_name="第四段保压压力")
#     holding_speed_4 = models.FloatField(null=True, verbose_name="第四段保压速度")
#     holding_time_4 = models.FloatField(null=True, verbose_name="第四段保压时间")
#     holding_pressure_5 = models.FloatField(null=True, verbose_name="第五段保压压力")
#     holding_speed_5 = models.FloatField(null=True, verbose_name="第五段保压速度")
#     holding_time_5 = models.FloatField(null=True, verbose_name="第五段保压时间")
    
#     # --- 冷却参数 ---
#     cooling_time = models.FloatField(null=True, verbose_name="冷却时间")
    
#     # --- 熔胶参数 ---
#     stage = models.IntegerField(null=True, verbose_name="熔胶段数 1-4")
#     metering_pressure_1 = models.FloatField(null=True, verbose_name="第一段熔胶压力")
#     metering_screw_rotation_speed_1 = models.FloatField(null=True, verbose_name="第一段螺杆转速")
#     metering_back_pressure_1 = models.FloatField(null=True, verbose_name="第一段背压")
#     metering_position_1 = models.FloatField(null=True, verbose_name="第一段熔胶位置")
#     metering_pressure_2 = models.FloatField(null=True, verbose_name="第二段熔胶压力")
#     metering_screw_rotation_speed_2 = models.FloatField(null=True, verbose_name="第二段螺杆转速")
#     metering_back_pressure_2 = models.FloatField(null=True, verbose_name="第二段背压")
#     metering_position_2 = models.FloatField(null=True, verbose_name="第二段熔胶位置")
#     metering_pressure_3 = models.FloatField(null=True, verbose_name="第三段熔胶压力")
#     metering_screw_rotation_speed_3 = models.FloatField(null=True, verbose_name="第三段螺杆转速")
#     metering_back_pressure_3 = models.FloatField(null=True, verbose_name="第三段背压")
#     metering_position_3 = models.FloatField(null=True, verbose_name="第三段熔胶位置")
#     metering_pressure_4 = models.FloatField(null=True, verbose_name="第四段熔胶压力")
#     metering_screw_rotation_speed_4 = models.FloatField(null=True, verbose_name="第四段螺杆转速")
#     metering_back_pressure_4 = models.FloatField(null=True, verbose_name="第四段背压")
#     metering_position_4 = models.FloatField(null=True, verbose_name="第四段熔胶位置")
    
#     pre_decompress_mode = models.CharField(max_length=20, null=True, verbose_name="熔胶前松退模式")
#     decompressure_pressure_before_metering = models.FloatField(null=True, verbose_name="熔胶前松退压力")
#     decompressure_speed_before_metering = models.FloatField(null=True, verbose_name="熔胶前松退速度")
#     decompressure_distance_before_metering = models.FloatField(null=True, verbose_name="熔胶前松退距离")
#     decompressure_time_before_metering = models.FloatField(null=True, verbose_name="熔胶前松退时间")

#     post_decompress_mode = models.CharField(max_length=20, null=True, verbose_name="熔胶后松退模式")
#     decompressure_pressure_after_metering = models.FloatField(null=True, verbose_name="熔胶后松退压力")
#     decompressure_speed_after_metering = models.FloatField(null=True, verbose_name="熔胶后松退速度")
#     decompressure_distance_after_metering = models.FloatField(null=True, verbose_name="熔胶后松退距离")
#     decompressure_time_after_metering = models.FloatField(null=True, verbose_name="熔胶后松退时间")
    
#     delay_time = models.FloatField(null=True, verbose_name="熔胶延时")
#     metering_end_location = models.FloatField(null=True, verbose_name="熔胶结束位置")
    
#     # --- 料筒温度参数 ---
#     barrel_temperature_stage = models.IntegerField(null=True, verbose_name="料筒温度段数 1-8")
#     nozzle_temperature = models.FloatField(null=True, verbose_name="料筒温度")
#     barrel_temperature_1 = models.FloatField(null=True, verbose_name="第一段料筒温度")
#     barrel_temperature_2 = models.FloatField(null=True, verbose_name="第二段料筒温度")
#     barrel_temperature_3 = models.FloatField(null=True, verbose_name="第三段料筒温度")
#     barrel_temperature_4 = models.FloatField(null=True, verbose_name="第四段料筒温度")
#     barrel_temperature_5 = models.FloatField(null=True, verbose_name="第五段料筒温度")
#     barrel_temperature_6 = models.FloatField(null=True, verbose_name="第六段料筒温度")
#     barrel_temperature_7 = models.FloatField(null=True, verbose_name="第七段料筒温度")
    
#     class Meta:
#         verbose_name = "标准参数"
#         verbose_name_plural = verbose_name
