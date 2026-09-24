"""调参记录模型"""

from django.db import models

from extensions.models import BusinessBaseModel


class TuningRecord(BusinessBaseModel):
    """
    工艺调整记录 - 记录一次工艺调整与试模结果

    用于追踪工艺调整过程，包含：
    - 缺陷反馈（一次试模可能多个缺陷）
    - 调整记录（规范化训练样本）
    - 试模结果（迭代状态）
    - 调整前参数快照（独立存储）

    设计说明：
    - 与 ProcessParameter 1:1 同步创建（业务层保证，FK 不加 unique）
    - 缺陷反馈以 JSON 数组存储，支持多个缺陷
    - adjustments 是规范化训练样本，系统自动生成，用户不可定义结构
    - previous_parameter 存储调整前 OLD parameter 的参数
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
    #         "keyword_id": 15,
    #         "keyword_name": "短射",
    #         "level": "high",
    #         "position": "DLWELDLINE3",
    #         "position_3d": null
    #     },
    #     {
    #         "keyword_id": 22,
    #         "keyword_name": "飞边",
    #         "level": "medium",
    #         "position": "DLFLASH2",
    #         "position_3d": null
    #     }
    # ]
    defect_feedbacks = models.JSONField(
        default=list,
        verbose_name="缺陷反馈列表",
        help_text="一次试模可能包含多个缺陷，JSON数组格式"
    )

    # --- 调整记录（JSON，系统自动生成）---
    # adjustments 是规范化训练样本，由系统计算 OLD vs NEW diff 生成
    # 字段名补充说明：取代原 note 字段
    # 用户不能定义其结构（保证格式一致）
    # {
    #     "defects": ["短射", "飞边"],
    #     "changes": [
    #         {
    #             "param": "inj_pres_1",
    #             "before": 50,
    #             "after": 60,
    #             "direction": "increase",
    #             "rule_ref": "rule_001"
    #         }
    #     ],
    #     "tuning_context": {
    #         "iteration": 3,
    #         "previous_result": "worse"
    #     }
    # }
    adjustments = models.JSONField(
        default=dict,
        null=True, blank=True,
        verbose_name="调整记录",
        help_text="规范化调参内容，由系统自动生成（OLD vs NEW diff）"
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

    # --- 调整前参数快照（OLD parameter.parameters）---
    # 表示"这是从哪个工艺调整过来的"
    # 独立存储一份快照，避免联表查询，同时避免依赖 OLD parameter 的不可变性
    previous_parameter = models.JSONField(
        null=True, blank=True,
        verbose_name="调整前参数快照",
        help_text="调整前的工艺参数快照（OLD parameter.parameters）"
    )

    class Meta:
        verbose_name = "调参记录"
        verbose_name_plural = "调参记录"
        ordering = ['-created_at']
