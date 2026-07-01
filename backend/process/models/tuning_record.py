"""
调试记录模型
"""

from django.db import models

from extensions.models import BusinessBaseModel


class TuningRecord(BusinessBaseModel):
    """
    工艺调参记录 - 记录一次调参与试模结果

    用于追踪工艺调整过程，包含：
    - 缺陷反馈（一次试模可能多个缺陷）
    - 试模结果（迭代状态，支持多轮调试）
    - 当次参数快照（冗余存储，方便查询）

    设计说明：
    - 一个 ProcessParameter 可对应多条 TuningRecord（多轮迭代）
    - 缺陷反馈以 JSON 数组存储，支持多个缺陷
    - parameter_snapshot 冗余存储，避免关联查询
    - 迭代状态：pending → improved/worse → qualified/unqualified
    """

    process_parameter = models.ForeignKey(
        "ProcessParameter",
        on_delete=models.CASCADE,
        related_name="tuning_records",
        verbose_name="工艺参数",
    )

    # --- 缺陷反馈（JSON 数组）---
    # [
    #     {
    #         "defect_type": "短射",
    #         "level": "medium",
    #         "position": "产品边缘",
    #         "image_url": "..."
    #     },
    #     {
    #         "defect_type": "飞边",
    #         "level": "light",
    #         "position": "分型线"
    #     }
    # ]
    defect_feedbacks = models.JSONField(
        default=list,
        verbose_name="缺陷反馈列表",
        help_text="一次试模可能包含多个缺陷，JSON数组格式"
    )

    # --- 调参备注 ---
    note = models.CharField(
        max_length=500,
        null=True, blank=True,
        verbose_name="调参备注",
    )

    # --- 试模结果（迭代状态）---
    # 状态流转：待验证 → 有改善/恶化/无变化 → 合格/不合格
    TRIAL_RESULT_CHOICES = [
        ('pending', '待验证'),        # 刚提交，等待试模
        ('improved', '有改善'),      # 参数调整后缺陷有所改善
        ('worse', '效果变差'),        # 调整后问题更严重
        ('unchanged', '无变化'),      # 调整后没有效果
        ('qualified', '合格'),       # 达到质量要求
        ('unqualified', '不合格'),    # 无法达到要求，需换方案
    ]
    result = models.CharField(
        max_length=20,
        choices=TRIAL_RESULT_CHOICES,
        default='pending',
        verbose_name="试模结果",
        help_text="描述本次试模的效果，用于追踪调参迭代过程"
    )

    # --- 结果详情 ---
    # 记录本次调整的具体效果描述，如"短射问题改善30%", "飞边消失"
    result_detail = models.CharField(
        max_length=500,
        null=True, blank=True,
        verbose_name="结果详情",
        help_text="具体描述本次调整的效果"
    )

    # --- 参数快照（冗余存储）---
    # 存储当次试模使用的完整参数，方便查询
    parameter_snapshot = models.JSONField(
        null=True, blank=True,
        verbose_name="参数快照",
    )

    class Meta:
        verbose_name = "调参记录"
        verbose_name_plural = "调参记录"
        ordering = ['-created_at']
