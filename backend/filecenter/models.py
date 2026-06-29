from extensions.models import TracedModel, BusinessBaseModel
from django.db import models
import uuid


class File(BusinessBaseModel):
    """文件模型"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="文件UUID")
    filename = models.CharField(max_length=255, verbose_name="原始文件名")
    mime_type = models.CharField(max_length=100, verbose_name="MIME类型")
    FILE_TYPE_CHOICES = [
        ("image", "图片"),
        ("video", "视频"),
        ("document", "文档"),
        ("other", "其他"),
    ]
    type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        verbose_name="文件类别"
    )
    size = models.BigIntegerField(null=True, verbose_name="文件大小（字节）")
    md5 = models.CharField(max_length=32, db_index=True, verbose_name="文件MD5")
    storage_path = models.CharField(max_length=512, verbose_name="存储路径")
    uploaded_by = models.ForeignKey(
        "identity.User", 
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_files",
        verbose_name="上传者"
    )

    class Meta:
        verbose_name = "文件"
        verbose_name_plural = "文件"


class FileReference(TracedModel):
    """文件引用模型"""
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name="references")
    business_id = models.IntegerField(verbose_name="业务ID")
    business_type = models.CharField(max_length=50, verbose_name="业务类型")
    usage_type = models.CharField(max_length=50, verbose_name="使用类型")
    
    class Meta:
        indexes = [
            # 关键索引：快速查找某类业务的某类文件
            models.Index(
                fields=['business_type', 'business_id', 'usage_type'],
                name='file_ref_bus_usage_idx'
            ),
        ]
        verbose_name = "文件引用"
        verbose_name_plural = "文件引用"
