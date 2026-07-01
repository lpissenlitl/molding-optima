"""
工艺参数模型
"""

from django.db import models
from django.db.models import Max

from extensions.models import BusinessBaseModel


class ProcessParameter(BusinessBaseModel):
    """
    工艺参数 - 隶属 ProcessCondition 的具体参数

    字段命名参考 molding-expert（inj_spd_1, inj_pres_1, hold_pres_1 等），
    比旧版 molding-optima 的命名（IV0, IP0, IL0）更可读。

    版本管理：
    - parent_param: 自关联，支持树形版本结构
    - seq_idx: 同一父节点下递增，自动分配
    - param_source: 标记参数来源（手动/AI/设备同步等）
    """

    process_condition = models.ForeignKey(
        "ProcessCondition",
        on_delete=models.CASCADE,
        verbose_name="所属条件",
        related_name="process_parameters",
    )

    # --- 基本信息 ---
    param_code = models.CharField(
        null=True, blank=True,
        max_length=50,
        verbose_name="工艺参数编号",
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
        ('ai_recommended', 'AI 推荐'),
    ]
    param_source = models.CharField(
        max_length=20,
        choices=PARAMETER_SOURCE_CHOICES,
        default="unknown",
        verbose_name="参数来源",
    )

    # --- 版本关系 ---
    parent_param = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="children",
        verbose_name="父版本",
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
            # 自动分配 seq_idx
            last_idx = ProcessParameter.all_objects.filter(
                process_condition=self.process_condition
            ).aggregate(Max('seq_idx'))['seq_idx__max'] or 0
            self.seq_idx = last_idx + 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "工艺参数"
        verbose_name_plural = "工艺参数"
