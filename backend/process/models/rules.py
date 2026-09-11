"""
规则库模型

包含以下模型：
- RuleLibrary: 规则库顶层，支持多租户/多产品线隔离
- RuleKeyword: 规则关键词（系统级参数元数据）
- RuleMethod: 规则方法（模糊规则）
- ExpertRule: 专家规则（初始化规则）
"""

from django.db import models

from extensions.models import BusinessBaseModel


class RuleLibrary(BusinessBaseModel):
    """
    规则库 - 规则的分组容器，按租户/系统隔离。

    归属设计：
    - 系统默认规则：company=system_demo + owner_type='system'
    - 租户私有规则：company=租户公司 + owner_type='tenant'

    隔离逻辑：
    - 租户可见规则库 = 当前租户 company + system_demo company
    - 租户不可编辑 system_demo 下的规则（仅平台超管可接管后编辑）

    一致性约束：
    - owner_type='system' ⇔ company=system_demo
    - owner_type='tenant' ⇔ company=普通租户
    """

    # --- 规则库标识 ---
    library_code = models.CharField(max_length=50, verbose_name="规则库编码")
    # 业务分类编码，可重复（不同租户/不同分类下可同名）
    # 示例: 'general' / 'auto_parts' / 'medical'

    library_no = models.CharField(
        max_length=20,
        default='',
        null=True, blank=True,
        verbose_name="规则库编号",
    )
    # 格式: RL-{YYYYMM}-{NNNNN}
    # 示例: RL-202609-00001
    # 唯一性约束在 service 层处理

    library_name = models.CharField(max_length=100, verbose_name="规则库名称")
    description = models.TextField(null=True, blank=True, verbose_name="规则库描述")

    # --- 归属信息 ---
    OWNER_TYPES = [
        ('system', '系统级'),
        ('tenant', '租户级'),
    ]
    owner_type = models.CharField(max_length=20, choices=OWNER_TYPES, verbose_name="归属类型")

    # --- 规则库元数据 ---
    priority = models.IntegerField(default=0, verbose_name="优先级")
    # 高优先级规则库可覆盖低优先级规则库

    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    # --- 版本管理 ---
    version = models.IntegerField(default=1, verbose_name="版本号")

    class Meta:
        verbose_name = "规则库"
        verbose_name_plural = "规则库"


class RuleKeyword(BusinessBaseModel):
    """
    规则关键词 - 系统级参数元数据定义

    注意：
    - 取值范围是通用默认值/模拟推荐值，非设备物理极限
    - 实际推理时：设备真实范围 > RuleKeyword 默认值
    """

    # --- 参数标识 ---
    keyword_name = models.CharField(max_length=50, verbose_name="关键词名称")
    # 示例: 'inj_pres_1', 'hold_pres_1'

    keyword_alias = models.CharField(max_length=100, verbose_name="关键词别名")
    # 示例: '注射压力1', '保压压力1'

    # --- 通用默认值/推荐范围（无设备数据时的参考值）---
    range_min = models.FloatField(verbose_name="默认最小值")
    range_max = models.FloatField(verbose_name="默认最大值")

    # --- 调整参数 ---
    action_range_min = models.FloatField(null=True, blank=True, verbose_name="调整区间最小值")
    action_range_max = models.FloatField(null=True, blank=True, verbose_name="调整区间最大值")
    action_max_val = models.FloatField(null=True, blank=True, verbose_name="最大调整值")

    # --- 模糊参数 ---
    FUZZY_LEVELS = [(3, '3级'), (5, '5级'), (7, '7级'), (9, '9级')]
    fuzzy_level = models.IntegerField(choices=FUZZY_LEVELS, default=5, verbose_name="模糊级别")

    # --- 模糊步长 ---
    # 含义：去模糊化的输出粒度。推理输出会取整到 step 的整数倍
    # 例：step=10 时，推理输出"加 12"取整为"加 10"
    # 取值参考：step ≈ (range_max - range_min) / fuzzy_level
    step = models.FloatField(null=True, blank=True, verbose_name="模糊步长")

    # --- 参数类型 ---
    KEYWORD_TYPES = [
        ('pressure', '压力'),
        ('speed', '速度'),
        ('time', '时间'),
        ('temperature', '温度'),
        ('position', '位置'),
        ('force', '力'),
        ('length', '长度'),
        ('weight', '重量'),
    ]
    keyword_type = models.CharField(
        max_length=20,
        choices=KEYWORD_TYPES,
        verbose_name="参数类型",
    )

    # --- 单位 ---
    unit = models.CharField(max_length=20, verbose_name="单位")
    # 示例: 'MPa', 'mm/s', 's', '℃'

    # --- 参数说明 ---
    description = models.TextField(null=True, blank=True, verbose_name="参数说明")
    # 用途：补充描述参数的业务含义、使用场景、注意事项等

    class Meta:
        verbose_name = "规则关键词"
        verbose_name_plural = "规则关键词"
        unique_together = [('company', 'keyword_name')]


class RuleMethod(BusinessBaseModel):
    """
    规则方法 - 缺陷→参数调整规则
    属于某个规则库，按租户/产品线隔离
    """

    # --- 关联关系 ---
    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='rule_methods',
        verbose_name="所属规则库",
    )

    # --- 规则标识 ---
    # 格式: RM-{YYYYMM}-{NNNNN}
    rule_no = models.CharField(
        max_length=20,
        null=True, blank=True,
        verbose_name="规则编号",
    )

    # --- 规则内容 ---
    rule_description = models.TextField(verbose_name="规则描述")
    rule_explanation = models.TextField(null=True, blank=True, verbose_name="规则解释")

    # --- 匹配条件（留空 = 不限）---
    # polymer_abbreviation 与 Polymer.abbreviation 对齐
    polymer_abbreviation = models.CharField(max_length=45, null=True, blank=True, verbose_name="材料缩写")
    product_category = models.CharField(max_length=45, null=True, blank=True, verbose_name="产品类别")

    # --- 缺陷信息（识别用，不绑定主数据）---
    defect_label = models.CharField(max_length=45, null=True, blank=True, verbose_name="缺陷名称")
    defect_code = models.CharField(max_length=45, null=True, blank=True, verbose_name="缺陷标识")

    # --- 规则元数据 ---
    priority = models.IntegerField(default=1, verbose_name="优先级（0~10）")
    confidence = models.FloatField(default=1.0, verbose_name="置信度（0~1）")

    # --- 启用控制 ---
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    # --- 规则来源 ---
    SOURCE_TYPES = [
        ('expert', '专家经验'),
        ('rule_miner', '规则挖掘'),
        ('llm', '大模型生成'),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_TYPES, verbose_name="规则来源")

    class Meta:
        verbose_name = "规则方法"
        verbose_name_plural = "规则方法"


class ExpertRule(BusinessBaseModel):
    """
    工艺参数初始化系数
    通过 priority + conditions 实现分层覆盖
    """

    # --- 关联 ---
    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='expert_rules',
        verbose_name="所属规则库",
    )

    # --- 规则标识 ---
    rule_code = models.CharField(max_length=50, verbose_name="规则编码")
    rule_name = models.CharField(max_length=100, verbose_name="规则名称")

    # --- 匹配与系数 ---
    # conditions: 匹配条件（AND），空数组表示默认规则
    # 示例: [{'field': 'polymer.abbreviation', 'operator': 'exact', 'value': 'ABS'}]
    conditions = models.JSONField(default=list, verbose_name="匹配条件")
    # coefficients: 覆盖系数字典，与内置默认值深度合并
    # 示例: {'holding': {'hold_pres_inj_ratio_max': 0.85}}
    coefficients = models.JSONField(default=dict, verbose_name="规则系数")

    # --- 元数据 ---
    priority = models.IntegerField(default=100, verbose_name="优先级")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        verbose_name = "专家规则"
        verbose_name_plural = "专家规则"
        ordering = ['priority']
        unique_together = [('rule_library', 'rule_code')]
