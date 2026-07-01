"""
规则库模型

包含以下模型：
- RuleLibrary: 规则库顶层，支持多租户/多产品线隔离
- RuleKeyword: 规则关键词（系统级参数元数据）
- TenantKeywordOverride: 租户关键词覆盖
- RuleMethod: 规则方法（模糊规则）
- MinedRule: 挖掘规则结果
- ExpertRule: 专家规则（初始化规则）
"""

from django.db import models

from extensions.models import BusinessBaseModel


class RuleLibrary(BusinessBaseModel):
    """
    规则库 - 规则库顶层，支持多租户/多产品线隔离
    """

    # --- 规则库标识 ---
    library_code = models.CharField(max_length=50, unique=True, verbose_name="规则库编码")
    # 示例: 'general' / 'auto_parts' / 'medical'

    library_name = models.CharField(max_length=100, verbose_name="规则库名称")
    description = models.TextField(null=True, blank=True, verbose_name="规则库描述")

    # --- 归属信息 ---
    OWNER_TYPES = [
        ('system', '系统级'),
        ('tenant', '租户级'),
        ('user', '用户级'),
    ]
    owner_type = models.CharField(max_length=20, choices=OWNER_TYPES, verbose_name="归属类型")

    # --- 规则库元数据 ---
    priority = models.IntegerField(default=0, verbose_name="优先级")
    # 高优先级规则库可覆盖低优先级规则库

    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    # --- 版本管理 ---
    version = models.IntegerField(default=1, verbose_name="版本号")
    parent_library = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        verbose_name="父规则库",
    )

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
    keyword_name = models.CharField(max_length=50, unique=True, verbose_name="关键词名称")
    # 示例: 'inj_pres_1', 'hold_pres_1'

    keyword_alias = models.CharField(max_length=100, verbose_name="关键词别名")
    # 示例: '注射压力1', '保压压力1'

    # --- 参数分组 ---
    PARAM_GROUPS = [
        ('injection', '注射参数'),
        ('holding', '保压参数'),
        ('cooling', '冷却参数'),
        ('metering', '计量参数'),
        ('temperature', '温度参数'),
    ]
    param_group = models.CharField(max_length=20, choices=PARAM_GROUPS, verbose_name="参数分组")

    # --- 通用默认值/推荐范围（无设备数据时的参考值）---
    range_min = models.FloatField(verbose_name="默认最小值")
    range_max = models.FloatField(verbose_name="默认最大值")

    # --- 调整参数 ---
    action_range_min = models.FloatField(null=True, blank=True, verbose_name="调整区间最小值")
    action_range_max = models.FloatField(null=True, blank=True, verbose_name="调整区间最大值")
    action_max_val = models.FloatField(null=True, blank=True, verbose_name="最大调整值")

    # --- 模糊参数 ---
    FUZZY_LEVELS = [(3, '3级'), (5, '5级')]
    fuzzy_level = models.IntegerField(choices=FUZZY_LEVELS, default=3, verbose_name="模糊级别")

    # --- 参数类型 ---
    keyword_type = models.CharField(max_length=45, verbose_name="参数类型")
    # 示例: 'pressure', 'speed', 'time', 'temperature'

    # --- 单位 ---
    unit = models.CharField(max_length=20, verbose_name="单位")
    # 示例: 'MPa', 'mm/s', 's', '℃'

    # --- 分类维度（可选，用于规则匹配）---
    subrule_no = models.CharField(max_length=45, null=True, blank=True, verbose_name="子规则编号")
    product_small_type = models.CharField(max_length=45, null=True, blank=True, verbose_name="产品小类")
    polymer_abbreviation = models.CharField(max_length=45, null=True, blank=True, verbose_name="材料简称")

    class Meta:
        verbose_name = "规则关键词"
        verbose_name_plural = "规则关键词"


class TenantKeywordOverride(BusinessBaseModel):
    """
    租户关键词覆盖 - 租户可覆盖部分 RuleKeyword 行为
    """

    keyword = models.ForeignKey(
        RuleKeyword,
        on_delete=models.CASCADE,
        related_name='tenant_overrides',
        verbose_name="关键词",
    )

    # --- 覆盖的默认值 ---
    action_range_max = models.FloatField(null=True, blank=True, verbose_name="覆盖调整区间最大值")

    # --- 展示偏好 ---
    show_on_page = models.BooleanField(null=True, blank=True, verbose_name="是否在界面展示")
    show_order = models.IntegerField(null=True, blank=True, verbose_name="展示顺序")

    class Meta:
        verbose_name = "租户关键词覆盖"
        verbose_name_plural = "租户关键词覆盖"


class RuleMethod(BusinessBaseModel):
    """
    规则方法 - 缺陷→参数调整规则
    属于某个规则库，按租户/产品线隔离
    """

    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='rule_methods',
        verbose_name="所属规则库",
    )

    # --- 规则标识 ---
    subrule_no = models.CharField(max_length=45, verbose_name="子规则编号")
    rule_code = models.CharField(max_length=50, verbose_name="规则编码")

    # --- 匹配条件 ---
    polymer_category = models.CharField(max_length=45, null=True, blank=True, verbose_name="材料类别")
    product_category = models.CharField(max_length=45, null=True, blank=True, verbose_name="产品类别")

    # --- 缺陷信息 ---
    defect_name = models.CharField(max_length=45, verbose_name="缺陷名称")
    defect_desc = models.CharField(max_length=200, null=True, blank=True, verbose_name="缺陷描述")

    # --- 规则内容 ---
    rule_description = models.TextField(verbose_name="规则描述")
    rule_explanation = models.TextField(null=True, blank=True, verbose_name="规则解释")

    # --- 规则内容（JSON格式）---
    # 示例:
    # {
    #     "conditions": [
    #         {"param": "inj_pres_1", "operator": "<", "value": 60}
    #     ],
    #     "adjustments": [
    #         {"param": "inj_pres_1", "action": "increase", "value": 10}
    #     ]
    # }
    rule_content = models.JSONField(verbose_name="规则内容")

    # --- 规则元数据 ---
    rule_type = models.CharField(max_length=45, verbose_name="规则类型")
    priority = models.FloatField(default=1.0, verbose_name="优先级")
    confidence = models.FloatField(default=1.0, verbose_name="置信度")

    # --- 启用控制 ---
    is_auto = models.BooleanField(default=True, verbose_name="是否自动应用")
    enable = models.BooleanField(default=True, verbose_name="是否启用")

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
        unique_together = ['rule_library', 'rule_code']


class MinedRule(BusinessBaseModel):
    """
    挖掘规则 - 规则挖掘引擎生成的结果，待审核入库
    """

    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='mined_rules',
        verbose_name="所属规则库",
    )

    # --- 规则内容 ---
    # 示例:
    # {
    #     "defect_type": "短射",
    #     "conditions": [...],
    #     "adjustments": [...],
    #     "confidence": 0.85,
    #     "support": 15,
    #     "lift": 2.3
    # }
    rule_content = models.JSONField(verbose_name="规则内容")

    # --- 统计信息 ---
    support_count = models.IntegerField(verbose_name="支持次数")
    confidence = models.FloatField(verbose_name="置信度")
    lift = models.FloatField(verbose_name="提升度")

    # --- 审核状态 ---
    REVIEW_STATUS = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS,
        default='pending',
        verbose_name="审核状态",
    )

    # --- 审核信息 ---
    reviewed_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_mined_rules',
        verbose_name="审核人",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    review_comment = models.TextField(null=True, blank=True, verbose_name="审核意见")

    class Meta:
        verbose_name = "挖掘规则"
        verbose_name_plural = "挖掘规则"
        ordering = ['-created_at']


class ExpertRule(BusinessBaseModel):
    """
    专家规则 - 工艺初始化引擎使用的专家规则
    用于 ExpertEngine 根据模具/材料/机台推理初始工艺参数
    """

    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='expert_rules',
        verbose_name="所属规则库",
    )

    # --- 规则标识 ---
    rule_code = models.CharField(max_length=50, unique=True, verbose_name="规则编码")
    rule_name = models.CharField(max_length=100, verbose_name="规则名称")
    description = models.TextField(null=True, blank=True, verbose_name="规则描述")

    # --- 规则条件（数组格式）---
    # 无条件规则（conditions=[]）表示默认规则，始终匹配
    # 支持的条件格式：
    # [
    #     {'field': 'polymer.abbreviation', 'operator': 'in', 'value': ['ABS', 'PC']},
    #     {'field': 'product.ave_thickness', 'operator': 'gte', 'value': 2.0}
    # ]
    # 支持的 operator: exact, in, not_in, gte, lte, gt, lt
    conditions = models.JSONField(default=list, verbose_name="匹配条件")

    # --- 规则系数（直接值）---
    # 直接存储系数值，计算逻辑在代码中实现
    # {
    #     'inj_pres_ratio': 0.65,
    #     'hold_pres_base': 0.25,
    #     'hold_pres_thickness_factor': 10,
    #     'hold_velo_ratio': 0.15
    # }
    coefficients = models.JSONField(default=dict, verbose_name="规则系数")

    # --- 规则元数据 ---
    priority = models.IntegerField(default=100, verbose_name="优先级")
    # 数字越小优先级越高，默认为100，DEFAULT规则设为9999

    SOURCE_TYPES = [
        ('expert', '专家经验'),
        ('rule_miner', '规则挖掘'),
        ('llm', '大模型生成'),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_TYPES, verbose_name="规则来源")

    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    # --- 版本管理 ---
    version = models.IntegerField(default=1, verbose_name="版本号")
    parent_rule = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        verbose_name="父规则",
    )

    class Meta:
        verbose_name = "专家规则"
        verbose_name_plural = "专家规则"
        ordering = ['priority']
