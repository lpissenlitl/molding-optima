from mongoengine import Document, DateTimeField, IntField
from datetime import datetime


class BaseDoc(Document):
    """
    Django 项目专用的 MongoEngine 文档基类
    使用 Django 的时区系统，确保时间一致性
    """
    created_at = DateTimeField(required=True, default=datetime.now)
    updated_at = DateTimeField(required=True, default=datetime.now)

    meta = {
        "strict": False,
        "abstract": True,
        "allow_inheritance": True
    }

    def save(self, *args, **kwargs):
        now =  datetime.now()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        return super().save(*args, **kwargs)
    
    def update(self, **kwargs):
        self.save()
        return super().update(**kwargs)
    
    def to_dict(self):
        dict_data = self.to_mongo().to_dict()
        if "_id" in dict_data:
            dict_data["_id"] = str(dict_data.pop("_id"))
        return dict_data


class BusinessBaseDoc(BaseDoc):
    """
    当前项目的业务文档基类
    """
    
    company_id = IntField(null=True, verbose_name="所属公司")
    organization_id = IntField(null=True, verbose_name="所属部门")
    project_id = IntField(null=True, verbose_name="所属项目")
    
    meta = {
        "strict": False,
        "abstract": True,
        "allow_inheritance": True
    }
