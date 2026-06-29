from django.db import models
from gis.common.django_ext.models import ExtraBaseModel


class Upload(ExtraBaseModel):
    id = models.IntegerField(primary_key=True)
    company_id = models.IntegerField()
    search_id = models.IntegerField()
    search_type = models.CharField(max_length=45)
    filename = models.CharField(max_length=128)
    file_url = models.CharField(max_length=256, default="")
    file_md5 = models.CharField(max_length=128)
    file_type = models.CharField(max_length=32)
    file_size = models.IntegerField()
    slice_status = models.SmallIntegerField(default=0)
    slice_order = models.SmallIntegerField(default=0)
    slice_total = models.SmallIntegerField(default=0)
    finally_md5 = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "upload"
