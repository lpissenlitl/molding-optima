"""
推荐结果模型
"""

from django.db import models

from extensions.models import BusinessBaseModel


class Recommendation(BusinessBaseModel):
    """
    推荐结果 - 基于缺陷反馈的智能推荐

    可扩展的 AI 推荐插槽，支持多种 AI 算法：
    - fuzzy_rule: 模糊规则推理
    - rule_miner: 规则挖掘学习
    - llm: 大语言模型
    - doe: 实验设计优化

    设计说明：
    - 职责单一：只记录算法推荐内容，不存储训练样本
    - 训练样本统一归到 TuningRecord.adjustments
    - is_adopted 是自动维护的训练标签，不需用户主动调用
    - recommendations 格式由 source_type 决定
    """

    process_parameter = models.ForeignKey(
        "ProcessParameter",
        on_delete=models.CASCADE,
        related_name="recommendations",
        verbose_name="工艺参数",
    )

    # --- 推荐来源 ---
    SOURCE_TYPE_CHOICES = [
        ('fuzzy_rule', '模糊规则推理'),
        ('rule_miner', '规则挖掘学习'),
        ('llm', '大语言模型'),
        ('doe', '实验设计优化'),
        ('genetic', '遗传算法'),
    ]
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        verbose_name="推荐来源类型",
    )

    # --- 推荐方案（JSON 格式）---
    # fuzzy_rule 格式：
    # [
    #     {
    #         "defect": "短射",
    #         "param": "inj_pres_1",
    #         "action": "increase",
    #         "current_value": 50,
    #         "recommended_value": 60,
    #         "confidence": 0.85
    #     }
    # ]
    #
    # llm 格式：
    # [
    #     {
    #         "strategy": "...",
    #         "params": {...},
    #         "reasoning": "..."
    #     }
    # ]
    recommendations = models.JSONField(
        default=list,
        verbose_name="推荐方案列表",
    )

    # --- 采纳状态（训练标签）---
    # 默认 True，下一轮 tuning_result = 'ineffective' 时改为 False
    # 不需用户主动调用（不需要 adopt 接口）
    is_adopted = models.BooleanField(
        default=True,
        verbose_name="是否被采纳",
        help_text="默认 True，下一轮 ineffective 时自动改为 False（训练标签）"
    )

    class Meta:
        verbose_name = "推荐结果"
        verbose_name_plural = "推荐结果"
        ordering = ['-created_at']
