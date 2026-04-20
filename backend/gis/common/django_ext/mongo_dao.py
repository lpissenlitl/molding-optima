from datetime import datetime
import logging

from django.utils import timezone
from django.conf import settings
from mongoengine import Document, DateTimeField


class BaseDoc(Document):
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(required=True)

    meta = {"abstract": True}

    def save(self, **kwargs):
        now = timezone.now()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        return super().save(**kwargs)


    def update(self, **kwargs):
        self.save()
        return super().update(**kwargs)


    def to_dict(self):
        dict_data = self.to_mongo().to_dict()
        if "_id" in dict_data:
            dict_data["_id"] = str(dict_data["_id"])
        if settings.USE_TZ:
            # 如果django的时间包含时区信息
            for key, value in enumerate(dict_data):
                if isinstance(value, datetime):
                    dict_data[key] = timezone.make_aware(value, timezone.utc)
        return dict_data
