
from django.db import models
from extensions.models import AbstractBaseModel


class OperationLog(AbstractBaseModel):
    """操作记录"""
    # ================ 1. 操作人信息（快照） ================
    user_id = models.CharField(max_length=50, null=True, db_index=True, verbose_name="用户ID")
    user_name = models.CharField(max_length=50, db_index=True, verbose_name="用户名称")
    user_role = models.CharField(max_length=255, null=True, verbose_name="用户角色")

    # ================ 2. 公司信息（快照） ================
    com_id = models.CharField(max_length=50, null=True, db_index=True, verbose_name="公司ID")
    com_name = models.CharField(max_length=50, null=True, db_index=True, verbose_name="公司名称")

    # ================ 3. 组织信息（快照） ================
    org_id = models.CharField(max_length=50, null=True, db_index=True, verbose_name="组织ID")
    org_name = models.CharField(max_length=50, null=True, verbose_name="组织名称")
    
    # ================ 5. 操作时间 ================
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")
    
    # ================ 6. 操作类型 ================
    ACTION_CHOICES = [
        ("create", "创建"),
        ("update", "更新"),
        ("delete", "删除"),
        ("view", "查看"),
        ("export", "导出"),
        ("import", "导入"),
        ("login", "登录"),
        ("logout", "登出"),
        ("reset_password", "重置密码"),
        ("change_password", "修改密码"),
    ]
    action = models.CharField(null=True, max_length=20, choices=ACTION_CHOICES, verbose_name="操作类型")
    
    # ================ 7. 操作对象 ================
    target_type = models.CharField(max_length=50, null=True, verbose_name="操作对象类型")
    target_id = models.CharField(max_length=50, null=True, db_index=True, verbose_name="操作对象ID")
    target_name = models.CharField(max_length=50, null=True, verbose_name="操作对象名称")

    # ================ 8. 操作详情 ================
    description = models.CharField(max_length=255, null=True, verbose_name="操作详情")
    
    # ================ 9. 操作结果 ================
    status = models.CharField(
        null=True,
        max_length=20, 
        choices=[("success", "成功"), ("failure", "失败")], 
        default="success",
        verbose_name="操作结果"
    )
    error_summary = models.CharField(max_length=255, null=True, verbose_name="错误摘要")
    
    # ================ 10. 客户端信息 ================
    ip_address = models.CharField(max_length=50, null=True, verbose_name="IP地址")
    user_agent = models.CharField(max_length=255, null=True, verbose_name="用户代理")
    client_type = models.CharField(max_length=50, null=True, verbose_name="客户端类型")
    
    class Meta:
        verbose_name = "操作记录"
        verbose_name_plural = "操作记录"
        ordering = ["-timestamp"]
    