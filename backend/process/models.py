"""
molding-optima 工艺管理 - 模型

参考 molding-expert-service/process/models.py 的设计：
- 字段命名采用 molding-expert 风格（inj_spd_1, inj_pres_1 等，可读性更好）
- 保留 molding-optima 业务所需的额外字段（status, condition_code, origin_type, shot_index, injection_index）

模型：
- ProcessCondition：工艺条件主表
- ProcessParameter：工艺参数（隶属 ProcessCondition）
- RuleKeyword、RuleMethod：规则（从 old/mdprocess 迁移）

设计原则：
- ProcessCondition 存状态/来源/关键外键
- 非关键文本字段存到 process_context_snapshot JSON（格式待阶段 2 确定）
"""
from django.db import models
from django.db.models import Max

from extensions.models import BusinessBaseModel


class ProcessCondition(BusinessBaseModel):
    """
    工艺条件 - 工艺条件主表

    一条记录对应一组"工艺事件"（参数录入、变更、优化等），
    必须包含模具/机器/材料等上下文。
    """

    # --- 状态信息 ---
    PROCESS_CONDITION_STATUS_CHOICES = [
        ('draft', '草稿'),
        ('testing', '测试中'),
        ('approved', '已批准'),
        ('rejected', '已废弃'),
        ('obsolete', '已过时'),
    ]
    status = models.CharField(null=True, blank=True, max_length=20, verbose_name="状态")

    # --- 基本信息 ---
    condition_code = models.CharField(null=True, blank=True, max_length=50, verbose_name="工艺条件编号")

    PROCESS_CONDITION_ORIGIN_CHOICES = [
        ('manual_creation', '手工新建'),
        ('template_based', '基于模板'),
        ('ai_recommendation', 'AI 推荐启动'),
        ('doe_experiment', '实验设计（DOE）'),
        ('legacy_import', '历史工艺导入'),
        ('equipment_capture', '设备参数捕获'),
        ('process_transplant', '工艺移植'),
    ]
    origin_type = models.CharField(
        max_length=30,
        choices=PROCESS_CONDITION_ORIGIN_CHOICES,
        null=True, blank=True,
        verbose_name="工艺起源类型",
    )

    # --- 上下文快照 JSON ---
    # 阶段 1 中格式待定，仅作为可扩展 JSON 字段保留
    process_context_snapshot = models.JSONField(null=True, blank=True, verbose_name="工艺条件快照")

    # --- 模具信息 ---
    mold = models.ForeignKey(
        "masterdata.Mold",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name="模具信息",
    )
    shot_index = models.IntegerField(null=True, blank=True, verbose_name="注射次数")

    # --- 注塑机信息 ---
    injection_machine = models.ForeignKey(
        "masterdata.InjectionMoldingMachine",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name="注塑机信息",
    )
    injection_index = models.IntegerField(null=True, blank=True, verbose_name="注射单元")

    # --- 材料信息 ---
    polymer = models.ForeignKey(
        "masterdata.Polymer",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name="材料信息",
    )

    class Meta:
        verbose_name = "工艺条件"
        verbose_name_plural = verbose_name


class ProcessParameter(BusinessBaseModel):
    """
    工艺参数 - 隶属 ProcessCondition 的具体参数

    字段命名参考 molding-expert（inj_spd_1, inj_pres_1, hold_pres_1 等），
    比旧版 molding-optima 的命名（IV0, IP0, IL0）更可读。
    """

    process_condition = models.ForeignKey(
        ProcessCondition,
        on_delete=models.CASCADE,
        verbose_name="所属条件",
        related_name="process_parameters",
    )

    # --- 基本信息 ---
    param_code = models.CharField(
        null=True, blank=True,
        max_length=50,
        verbose_name="工艺参数编号",
        help_text="工艺参数编号",
    )

    PARAMETER_SOURCE_CHOICES = [
        ('unknown', '未知'),
        ('manual', '手工录入'),
        ('import', '外部导入'),
        ('algorithm_init', '算法初始化'),
        ('system_inferred', '系统推理'),
        ('manual_adjusted', '人工调整'),
        ('equipment_sync', '设备同步'),
        ('template_copy', '模板复制'),
    ]
    param_source = models.CharField(
        null=True, blank=True,
        max_length=20,
        verbose_name="参数来源",
        choices=PARAMETER_SOURCE_CHOICES,
        default="unknown",
    )

    parent_param = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="children",
    )

    seq_idx = models.IntegerField(
        null=True, blank=True,
        verbose_name="序列序号",
        default=0,
    )

    # --- 注射参数 (6段) ---
    inj_stg = models.IntegerField(null=True, blank=True, verbose_name="注射段数 1-6")

    inj_spd_1 = models.FloatField(null=True, blank=True, verbose_name="一段注射速度")
    inj_spd_2 = models.FloatField(null=True, blank=True, verbose_name="二段注射速度")
    inj_spd_3 = models.FloatField(null=True, blank=True, verbose_name="三段注射速度")
    inj_spd_4 = models.FloatField(null=True, blank=True, verbose_name="四段注射速度")
    inj_spd_5 = models.FloatField(null=True, blank=True, verbose_name="五段注射速度")
    inj_spd_6 = models.FloatField(null=True, blank=True, verbose_name="六段注射速度")

    inj_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段注射压力")
    inj_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段注射压力")
    inj_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段注射压力")
    inj_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段注射压力")
    inj_pres_5 = models.FloatField(null=True, blank=True, verbose_name="五段注射压力")
    inj_pres_6 = models.FloatField(null=True, blank=True, verbose_name="六段注射压力")

    inj_pos_1 = models.FloatField(null=True, blank=True, verbose_name="一段注射位置")
    inj_pos_2 = models.FloatField(null=True, blank=True, verbose_name="二段注射位置")
    inj_pos_3 = models.FloatField(null=True, blank=True, verbose_name="三段注射位置")
    inj_pos_4 = models.FloatField(null=True, blank=True, verbose_name="四段注射位置")
    inj_pos_5 = models.FloatField(null=True, blank=True, verbose_name="五段注射位置")
    inj_pos_6 = models.FloatField(null=True, blank=True, verbose_name="六段注射位置")

    inj_t = models.FloatField(null=True, blank=True, verbose_name="注射时间")
    inj_dly_t = models.FloatField(null=True, blank=True, verbose_name="注射延时")

    # --- VP 切换参数 ---
    vps_mode = models.IntegerField(null=True, blank=True, verbose_name="VP切换模式")
    vps_pos = models.FloatField(null=True, blank=True, verbose_name="VP切换位置")
    vps_t = models.FloatField(null=True, blank=True, verbose_name="VP切换时间")
    vps_pres = models.FloatField(null=True, blank=True, verbose_name="VP切换压力")
    vps_spd = models.FloatField(null=True, blank=True, verbose_name="VP切换速度")

    # --- 保压参数 (5段) ---
    hold_stg = models.IntegerField(null=True, blank=True, verbose_name="保压段数 1-5")

    hold_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段保压压力")
    hold_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段保压压力")
    hold_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段保压压力")
    hold_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段保压压力")
    hold_pres_5 = models.FloatField(null=True, blank=True, verbose_name="五段保压压力")

    hold_spd_1 = models.FloatField(null=True, blank=True, verbose_name="一段保压速度")
    hold_spd_2 = models.FloatField(null=True, blank=True, verbose_name="二段保压速度")
    hold_spd_3 = models.FloatField(null=True, blank=True, verbose_name="三段保压速度")
    hold_spd_4 = models.FloatField(null=True, blank=True, verbose_name="四段保压速度")
    hold_spd_5 = models.FloatField(null=True, blank=True, verbose_name="五段保压速度")

    hold_t_1 = models.FloatField(null=True, blank=True, verbose_name="一段保压时间")
    hold_t_2 = models.FloatField(null=True, blank=True, verbose_name="二段保压时间")
    hold_t_3 = models.FloatField(null=True, blank=True, verbose_name="三段保压时间")
    hold_t_4 = models.FloatField(null=True, blank=True, verbose_name="四段保压时间")
    hold_t_5 = models.FloatField(null=True, blank=True, verbose_name="五段保压时间")

    # --- 冷却参数 ---
    cool_t = models.FloatField(null=True, blank=True, verbose_name="冷却时间")

    # --- 熔胶参数 (4段) ---
    met_stg = models.IntegerField(null=True, blank=True, verbose_name="熔胶段数 1-4")

    met_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段熔胶压力")
    met_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段熔胶压力")
    met_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段熔胶压力")
    met_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段熔胶压力")

    met_rot_spd_1 = models.FloatField(null=True, blank=True, verbose_name="一段螺杆转速")
    met_rot_spd_2 = models.FloatField(null=True, blank=True, verbose_name="二段螺杆转速")
    met_rot_spd_3 = models.FloatField(null=True, blank=True, verbose_name="三段螺杆转速")
    met_rot_spd_4 = models.FloatField(null=True, blank=True, verbose_name="四段螺杆转速")

    met_back_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段背压")
    met_back_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段背压")
    met_back_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段背压")
    met_back_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段背压")

    met_pos_1 = models.FloatField(null=True, blank=True, verbose_name="一段熔胶位置")
    met_pos_2 = models.FloatField(null=True, blank=True, verbose_name="二段熔胶位置")
    met_pos_3 = models.FloatField(null=True, blank=True, verbose_name="三段熔胶位置")
    met_pos_4 = models.FloatField(null=True, blank=True, verbose_name="四段熔胶位置")

    # --- 松退参数 ---
    pre_met_decomp_mode = models.IntegerField(null=True, blank=True, verbose_name="熔胶前松退模式")
    pre_met_decomp_pres = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退压力")
    pre_met_decomp_spd = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退速度")
    pre_met_decomp_t = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退时间")
    pre_met_decomp_dist = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退距离")

    pst_met_decomp_mode = models.IntegerField(null=True, blank=True, verbose_name="熔胶后松退模式")
    pst_met_decomp_pres = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退压力")
    pst_met_decomp_spd = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退速度")
    pst_met_decomp_t = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退时间")
    pst_met_decomp_dist = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退距离")

    met_lim_t = models.FloatField(null=True, blank=True, verbose_name="熔胶延时")
    met_end_pos = models.FloatField(null=True, blank=True, verbose_name="熔胶终止位置")

    # --- 料筒温度参数 (10段) ---
    brl_temp_stg = models.IntegerField(null=True, blank=True, verbose_name="料筒温度段数 1-10")
    noz_temp = models.FloatField(null=True, blank=True, verbose_name="喷嘴温度")
    brl_temp_1 = models.FloatField(null=True, blank=True, verbose_name="一段料筒温度")
    brl_temp_2 = models.FloatField(null=True, blank=True, verbose_name="二段料筒温度")
    brl_temp_3 = models.FloatField(null=True, blank=True, verbose_name="三段料筒温度")
    brl_temp_4 = models.FloatField(null=True, blank=True, verbose_name="四段料筒温度")
    brl_temp_5 = models.FloatField(null=True, blank=True, verbose_name="五段料筒温度")
    brl_temp_6 = models.FloatField(null=True, blank=True, verbose_name="六段料筒温度")
    brl_temp_7 = models.FloatField(null=True, blank=True, verbose_name="七段料筒温度")
    brl_temp_8 = models.FloatField(null=True, blank=True, verbose_name="八段料筒温度")
    brl_temp_9 = models.FloatField(null=True, blank=True, verbose_name="九段料筒温度")

    def save(self, *args, **kwargs):
        if self.pk is None:
            last_idx = ProcessParameter.all_objects.filter(
                process_condition=self.process_condition
            ).aggregate(Max('seq_idx'))['seq_idx__max'] or 0

            self.seq_idx = last_idx + 1

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "工艺参数"
        verbose_name_plural = "工艺参数"


class RuleKeyword(BusinessBaseModel):
    """规则关键词 - 用于工艺优化的关键字匹配"""

    KEYWORD_TYPE_CHOICES = [
        ("defect", "缺陷"),
        ("material", "材料"),
        ("machine", "机器"),
        ("mold", "模具"),
        ("process", "工艺"),
    ]
    keyword_type = models.CharField(
        max_length=45,
        choices=KEYWORD_TYPE_CHOICES,
        verbose_name="关键字类型",
    )

    name = models.CharField(null=True, blank=True, max_length=45, verbose_name="关键字名称")
    level = models.IntegerField(default=0, verbose_name="模糊级别：3或5")
    all_range_min = models.IntegerField(null=True, blank=True, verbose_name="参数取值范围最小值")
    all_range_max = models.IntegerField(null=True, blank=True, verbose_name="参数取值范围最大值")
    action_range_min = models.IntegerField(null=True, blank=True, verbose_name="参数调整区间最小值")
    action_range_max = models.IntegerField(null=True, blank=True, verbose_name="参数调整区间最大值")
    action_max_val = models.IntegerField(null=True, blank=True, verbose_name="参数调整最大值")
    comment = models.CharField(null=True, blank=True, max_length=200, verbose_name="注释")

    subrule_no = models.CharField(null=True, blank=True, max_length=45, verbose_name="子规则编号")
    product_small_type = models.CharField(null=True, blank=True, max_length=45, verbose_name="制品小类")
    polymer_abbreviation = models.CharField(null=True, blank=True, max_length=45, verbose_name="塑料简称")
    rule_type = models.CharField(null=True, blank=True, max_length=45, verbose_name="规则类型")
    show_on_page = models.BooleanField(null=True, blank=True, verbose_name="是否在页面显示")

    class Meta:
        verbose_name = "规则关键词"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(
                fields=["subrule_no", "keyword_type"],
                name="rule_keyword_subrule_type_idx",
            ),
        ]


class RuleMethod(BusinessBaseModel):
    """规则方法 - 工艺调优的规则定义"""

    RULE_TYPE_CHOICES = [
        ("defect_fix", "缺陷修复"),
        ("process_optimize", "工艺优化"),
        ("machine_setup", "机器调试"),
    ]
    rule_type = models.CharField(
        max_length=45,
        choices=RULE_TYPE_CHOICES,
        verbose_name="规则类型",
    )

    polymer_abbreviation = models.CharField(null=True, blank=True, max_length=45, verbose_name="材料类别")
    product_small_type = models.CharField(null=True, blank=True, max_length=45, verbose_name="制品类别")
    rule_description = models.CharField(null=True, blank=True, max_length=500, verbose_name="规则描述")
    rule_explanation = models.CharField(null=True, blank=True, max_length=500, verbose_name="规则解释")

    is_auto = models.IntegerField(default=0, verbose_name="是否自动应用")
    enable = models.IntegerField(default=0, verbose_name="是否启用")

    defect_name = models.CharField(null=True, blank=True, max_length=45, verbose_name="缺陷名称")
    defect_desc = models.CharField(null=True, blank=True, max_length=200, verbose_name="缺陷描述")
    subrule_no = models.CharField(null=True, blank=True, max_length=45, verbose_name="子规则编号")
    priority = models.FloatField(default=0.0, verbose_name="优先级")

    class Meta:
        verbose_name = "规则方法"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(
                fields=["subrule_no", "rule_type"],
                name="rule_method_subrule_type_idx",
            ),
        ]