"""
工艺条件模型
"""

from django.db import models

from extensions.models import BusinessBaseModel


class ProcessCondition(BusinessBaseModel):
    """
    工艺条件 - 工艺条件主表

    一条记录对应一组"工艺事件"（参数录入、变更、优化等），
    必须包含模具/机器/材料等上下文。

    设计原则：
    - 每个 ProcessCondition 对应某一射的工艺
    - 多射场景通过 shot_index + injection_index 区分
    """

    # --- 状态信息 ---
    PROCESS_CONDITION_STATUS_CHOICES = [
        ('draft', '草稿'),           # 初始创建，未开始测试
        ('testing', '测试中'),        # 正在打样/验证
        ('approved', '已批准'),       # 合格工艺，可用于量产
        ('rejected', '已废弃'),       # 验证失败，不再使用
        ('obsolete', '已过时'),       # 曾经批准，但被新工艺替代
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
