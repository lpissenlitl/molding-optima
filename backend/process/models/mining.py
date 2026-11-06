"""规则挖掘模型 —— 挖掘产出的候选规则（待人工审核）。

模型清单：
- MiningRule: 候选规则（挖掘产出 + 审核态）
"""

from django.db import models

from extensions.models import BusinessBaseModel


class MiningRule(BusinessBaseModel):
    """
    候选规则 —— 规则挖掘产出的「缺陷 + 参数变更 ⇒ 试模结果」关联规则

    ⚠️ **为什么候选规则要单独建表，而不是直接写 RuleMethod**
    - RuleMethod 是**已生效**规则（会被 FuzzyEngine 直接查询消费）；
      挖出来的规则置信度未经人工确认，直接写进 RuleMethod 等于把
      「统计关联」当成「工艺因果」使用。
    - 候选规则需要**审核态**（pending / approved / rejected）与审核痕迹
      （审核人、审核时间、审核意见）—— RuleMethod 没有这层。
    - 候选规则保留**挖掘指标与证据**（support / confidence / lift / evidence），
      RuleMethod 只有 confidence 一个标量，事后无法复核。

    ⚠️ **重复挖掘只更新不新增**
    自然键是 `rule_hash`（缺陷 + 变更 + 后件的规范化摘要）⇒ 同一规则反复挖出
    时命中同一条记录，只刷新指标；**审核状态不被重置**（已审核的规则
    不因指标微调被打回待审，避免审核流程被反复打断）。
    """

    # --- 规则标识 ---
    rule_code = models.CharField(
        max_length=64,
        verbose_name="规则编码",
        help_text="格式: MR-{YYYYMM}-{NNNNN}，由 service 层生成",
    )
    rule_hash = models.CharField(
        max_length=64,
        verbose_name="规则指纹",
        help_text="sha1(规范化前件+后件)，作为自然键",
    )

    # --- 规则内容（对应挖掘内核的 MinedRule）---
    defects = models.JSONField(
        default=list,
        verbose_name="缺陷列表",
        help_text="前件缺陷（含等级），元素形如 "
                  "[{'name': 'SHORTSHOT', 'level': 'medium'}]；"
                  "缺陷名取算法命名空间英文名",
    )
    changes = models.JSONField(
        default=list,
        verbose_name="参数变更列表",
        help_text="前件变更，形如 [{'param': 'inj_pres_1', 'direction': 'increase'}]",
    )
    consequent = models.CharField(
        max_length=20,
        verbose_name="后件标签",
        help_text="试模结果：qualified / unqualified / improved / worse",
    )

    # --- 挖掘指标 ---
    support = models.FloatField(default=0.0, verbose_name="支持度")
    confidence = models.FloatField(default=0.0, verbose_name="置信度")
    lift = models.FloatField(default=0.0, verbose_name="提升度")

    # --- 证据 ---
    evidence = models.JSONField(
        default=list,
        verbose_name="证据样本",
        help_text="支撑该规则的样本 id 列表，可回溯到调机流水",
    )
    sample_count = models.IntegerField(default=0, verbose_name="证据样本数")
    corpus_cursor = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="语料游标",
        help_text="挖出该规则时的样本池游标（sample_id），用于复现",
    )

    # --- 审核 ---
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="审核状态",
    )
    reviewed_by = models.CharField(
        max_length=64, blank=True, default="", verbose_name="审核人",
    )
    reviewed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="审核时间",
    )
    review_note = models.CharField(
        max_length=500, blank=True, default="", verbose_name="审核意见",
    )

    # --- 落地（approved ⇒ RuleMethod）---
    landed_rule_method_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="已落地的规则方法 id",
        help_text="审核通过后写入的 RuleMethod 主键（未落地为空）",
    )
    landed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="落地时间",
    )
    landed_description = models.CharField(
        max_length=500, blank=True, default="",
        verbose_name="落地的规则文本",
        help_text="落地时生成的 IF...THEN 规则描述快照（便于回溯生成口径）",
    )
    landing_note = models.CharField(
        max_length=500, blank=True, default="",
        verbose_name="落地说明",
        help_text="落地结果说明（跳过的原因、写入的库等）",
    )

    class Meta:
        verbose_name = "候选规则"
        verbose_name_plural = "候选规则"
        unique_together = [('company', 'rule_hash')]
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', '-support']),
        ]
