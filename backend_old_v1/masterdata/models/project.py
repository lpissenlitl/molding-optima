from extensions.models import BusinessBaseModel
from django.db import models


class Project(BusinessBaseModel):
    """项目主数据（中性化设计，适用内外部项目）"""

    # --- 核心标识 ---
    project_code = models.CharField(max_length=50, verbose_name="项目编号")
    project_name = models.CharField(null=True, max_length=100, verbose_name="项目名称")
    is_draft = models.BooleanField(default=False, verbose_name="是否草稿")

    # --- 发起方信息（中性，可以是模具厂客户，也可以是注塑厂内部） ---
    initiator = models.CharField(null=True, max_length=100, verbose_name="发起方、客户名称等")
    initiation_reference = models.CharField(null=True, max_length=50, verbose_name="发起依据、订单编号等")
    manufacturing_location  = models.CharField(null=True, max_length=100, verbose_name="量产地")
    application_industry = models.CharField(null=True, max_length=100, verbose_name="应用行业")
    manufacturing_method = models.CharField(null=True, max_length=50, verbose_name="制作方式：委外、自制")

    # --- 项目分类与评级 ---
    is_premium = models.BooleanField(default=False, verbose_name="是否高端项目")
    importance_level = models.CharField(max_length=20, null=True, verbose_name="重要程度")
    
    # --- 项目组成员（含执行接口人）---
    project_manager = models.CharField(max_length=50, null=True, verbose_name="项目经理")
    sales_manager = models.CharField(max_length=50, null=True, verbose_name="市场经理")
    project_engineer = models.CharField(max_length=50, null=True, verbose_name="项目组长")
    technical_manager = models.CharField(max_length=50, null=True, verbose_name="技术经理")
    design_leader = models.CharField(max_length=50, null=True, verbose_name="设计师")
    process_engineer = models.CharField(max_length=50, null=True, verbose_name="工艺工程师")
    fitter = models.CharField(max_length=50, null=True, verbose_name="钳工负责人")
    
    # --- 合同与计划节点 ---
    contract_date = models.DateField(null=True, verbose_name="合同日期")
    contract_t1_date = models.DateField(null=True, verbose_name="合同T1日期")
    contract_factory_delivery_date = models.DateField(null=True, verbose_name="合同出厂日期")
    standard_trial_count = models.PositiveSmallIntegerField(null=True, verbose_name="标准试模次数")
    target_new_cycle_days = models.PositiveSmallIntegerField(null=True, verbose_name="目标新制周期（天）")
    target_rework_cycle_days = models.PositiveSmallIntegerField(null=True, verbose_name="目标整改周期（天）")

    # --- 试模相关 ---
    trial_plan_start_date = models.DateField(null=True, verbose_name="试模计划开始日期")
    trial_plan_end_date = models.DateField(null=True, verbose_name="试模计划结束日期")
    next_trial_stage = models.IntegerField(null=True, default=0, verbose_name="下一试模阶段")
    next_trial_iteration = models.IntegerField(null=True, default=0, verbose_name="下一试模迭代")
    is_dry_run_completed = models.BooleanField(null=True, default=False, verbose_name="是否完成空运行")
    
    # --- 实际发生时间 --
    project_kickoff_date = models.DateField(null=True, verbose_name="项目启动日期")
    work_start_date = models.DateField(null=True, verbose_name="开工日期")
    financial_settlement_date = models.DateField(null=True, verbose_name="财务结算日期")
     
    # --- 状态与协作 ---
    status = models.CharField(max_length=20, null=True, verbose_name="项目状态")
    REVIEW_STATUS_CHOICES = [
        ('pending', '待评审'),
        ('approved', '通过'),
        ('rejected', '不通过'),
        ('revision_required', '需修改'),
    ]
    review_status = models.CharField(max_length=20, null=True, verbose_name="评审结果")
    trial_machine = models.CharField(max_length=50, null=True, verbose_name="试模设备")

    # --- 其他 ---
    remarks = models.TextField(null=True, verbose_name="备注")
    created_by = models.ForeignKey(
        "identity.User",
        null=True,
        on_delete=models.SET_NULL
    )
    
    # --- 系统集成字段（支持外部系统，也支持本系统发起的项目） ---
    SROUCE_CHOICES = [
        ('manual', '手动创建'),
        ('sync', '系统同步'),
        ('import', '批量导入')
    ]
    source = models.CharField(max_length=20, null=True, verbose_name="项目来源")
    origin_system = models.CharField(null=True, max_length=50, verbose_name="来源系统")
    reference_id = models.CharField(null=True, max_length=50, verbose_name="参考ID")
    sync_status = models.CharField(null=True, max_length=20, verbose_name="同步状态")
    sync_time = models.DateTimeField(null=True, verbose_name="同步时间")
    
    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"