from extensions.models import AbstractBaseModel, BusinessBaseModel
from django.db import models


class AuxiliaryEquipment(BusinessBaseModel):
    """
    辅助装置台账（资源池模式）
    
    按类型管理总量与可用量，用于快速核对资源是否充足。
    假设同一类型设备规格一致，不区分品牌/型号。
    
    示例：
      - 模温机：总数 5 台，可用 2 台 → 还可申请最多 2 台
      - 干燥机：总数 3 台，可用 0 台 → 无法申请
    """
    equipment_name = models.CharField(max_length=50, verbose_name="名称")
    equipment_type = models.CharField(max_length=50, verbose_name="类型")
    specification = models.CharField(max_length=50, null=True, verbose_name="规格")
    total_count = models.PositiveIntegerField(default=0, verbose_name="数量")
    available_count = models.PositiveIntegerField(default=0, verbose_name="可用数量")
    remarks = models.TextField(null=True, verbose_name="备注")

    class Meta:
        verbose_name = "辅助装置"
        verbose_name_plural = "辅助装置"