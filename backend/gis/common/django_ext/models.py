#! -*- coding: utf-8 -*-
import json

from django.db import models
from django.db.models import ManyToManyField, ForeignKey

from gis.common.django_ext.json import JsonEncoder
import math

class ExtraBaseModel(models.Model):
    """
    为了兼容已经存在的数据库的数据，因此创建此类
    """

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, fields=None, exclude=None, return_many_to_many=False):
        """
        返回dict结构对象。
        :param fields: 如果指定fields，则只返回fields里的字段数据
        :param exclude: 如果指定exclude, 则不返回exclude里的字段数据，即使该字段在fields里指定了也不返回
        :param return_many_to_many: 是否返回model里的 ManyToManyField 字段数据, 从性能考虑默认不加载
        :return: dict结构数据
        """
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if fields and f.name not in fields:
                continue
            if exclude and f.name in exclude:
                continue
            if isinstance(f, ManyToManyField):
                if self.pk is None or not return_many_to_many:
                    continue
            if isinstance(f, ForeignKey):
                data[f.name + "_id"] = f.value_from_object(self)
            elif isinstance(f, ManyToManyField):
                data[f.name] = [e.to_dict() for e in f.value_from_object(self)]
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        abstract = True


class BaseModel(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class ListField(models.CharField):
    """
    自定义ListField，解决如下数据转换问题:
    '1|2|3'  <->  [1, 2, 3]
    """

    def __init__(self, base_type=str, separator="|", trim=False, *args, **kwargs):
        self.separator = separator
        self.base_type = base_type
        self.trim = trim
        super().__init__(*args, **kwargs)

    def get_db_prep_save(self, value, connection):
        # 允许直接返回默认设置的值，不用检查
        if self.default is not None and self.default == value:
            return self.default
        if not value:
            return None
        assert isinstance(value, list)
        for v in value:
            assert isinstance(v, self.base_type)
        if self.trim:
            return self.separator.join(str(v) for v in value)
        else:
            return (
                self.separator
                + self.separator.join(str(v) for v in value)
                + self.separator
            )

    def to_python(self, value):
        if not value:
            if value is not None:
                return []
            return None

        if "N/A" == value:
            return None

        return [self.base_type(v) for v in value.split(self.separator) if v]

    def get_prep_value(self, value):
        if self.trim:
            return self.separator.join(str(v) for v in value)
        return (
            self.separator + self.separator.join(str(v) for v in value) + self.separator
        )

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)


class DictField(models.CharField):
    """
    自定义DictField，解决如下数据转换问题:
    能支持json.dumps和json.loads处理的数据结构。
    """

    def get_db_prep_save(self, value, connection):
        if value is None:
            value = dict()
        assert isinstance(value, dict)
        return json.dumps(value, cls=JsonEncoder)

    def to_python(self, value):
        if not value:
            return dict()
        return json.loads(value)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)


def paginate(query, page_no, page_size):
    # 举例,如果搜索page_no是5,下一次默认还是5,而如果带着条件过滤,返回的数量有可能小于page_size,导致不能显示.计算最大页面号
    max_page_no = math.ceil(query.count() / page_size)

    # 如果结果数量不足一页大小，将页面号降低到最接近的值
    if query.count() < page_size:
        page_no = max(1, max_page_no)  # 如果搜索结果为空，将页面号设置为1
    else:
        page_no = min(page_no, max_page_no)  # 否则将页面号设置为当前页号和最大页号中较小的一个

    return query[((page_no - 1) * page_size): page_no * page_size]  # noqa: E203
