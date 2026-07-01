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
    - recommendations 格式由 source_type 决定
    - is_adopted + adopted_param 形成采纳闭环
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

    # --- 采纳状态 ---
    is_adopted = models.BooleanField(
        default=False,
        verbose_name="是否已采纳",
    )

    adopted_param = models.ForeignKey(
        "ProcessParameter",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="adopted_from_recommendations",
        verbose_name="采纳后的参数版本",
    )

    class Meta:
        verbose_name = "推荐结果"
        verbose_name_plural = "推荐结果"
        ordering = ['-created_at']
