
from django.db import models, transaction
from django.db.models import ForeignKey, ManyToManyField
from functools import lru_cache
from utils.db import build_filters, parse_ordering, paginate_queryset
from datetime import datetime


class AbstractBaseModel(models.Model):
    """
    模型公共方法
    """
    id = models.BigAutoField(primary_key=True, unique=True)
    def __repr__(self):
        return str(self.to_dict())
    
    @classmethod
    @lru_cache(maxsize=256)
    def get_allowed_fields(
        cls,
        exclude_auto_fields=True, 
        exclude_primary_key=True
    ):
        """
        获取模型允许外部设置的字段白名单（自动缓存）

        :param exclude_relations: 是否排除外键、多对多等关系字段
        :param exclude_auto_fields: 是否排除 auto_now, auto_now_add 字段
        :param exclude_primary_key: 是否排除主键字段
        :return: 字段名集合 set
        """
        # 如果模型显式定义了 allowed_fields，优先使用
        if hasattr(cls, 'allowed_fields') and isinstance(cls.allowed_fields, (list, tuple, set)):
            return set(cls.allowed_fields)
        
        fields = set()
        for f in cls._meta.get_fields():
            if not f.concrete:  # 跳过虚拟字段（如反向外键、多对多反向）
                continue
            if f.many_to_many or f.one_to_many:  # 只排除 M2M 和 reverse relations
                continue
            if exclude_primary_key and f.primary_key:  # 排除主键
                continue
            if exclude_auto_fields and (getattr(f, 'auto_now', False) or getattr(f, 'auto_now_add', False)):  # 排除自动时间字段
                continue
            fields.add(f.name)
            
            # 添加 _id 后缀，用于支持 cls_id 字段
            if isinstance(f, ForeignKey):
                fields.add(f.name + '_id')
            
        return fields
    
    @classmethod
    def get_editable_fields(cls):
        """
        快捷方法：返回默认的可编辑字段（排除关系、自动字段、主键）
        """
        return cls.get_allowed_fields()
    
    def to_dict(
        self, 
        fields=None, 
        exclude=None, 
        include_fk=False,
        include_m2m=False,
        include_rvs=False
    ):
        """
        返回 dict 结构对象

        Args:
            fields: 如果指定 fields, 则只返回 fields 里的字段数据.
            exclude: 如果指定 exclude, 则不返回 exclude 里的字段数据.
        """
        data = {}

        # 1. 处理普通字段和外键
        for f in self._meta.concrete_fields:
            if fields and f.name not in fields:
                continue
            if exclude and f.name in exclude:
                continue
            if isinstance(f, ForeignKey):
                if include_fk:  # 添加外键字段
                    data[f.name] = getattr(self, f.name).to_dict() if getattr(self, f.name) else None
                else:
                    data[f.name + "_id"] = f.value_from_object(self)
            else:
                data[f.name] = f.value_from_object(self)

        # 2. 处理 ManyToMany
        if include_m2m:
            for f in self._meta.many_to_many:
                if include_rvs and self.pk:
                    try:
                        data[f.name] = [obj.to_dict() for obj in f.value_from_object(self).all()]
                    except Exception:
                        data[f.name] = []

        # 3. 处理 Reverse Relation
        if include_rvs:
            # 处理 多对一 关系
            if hasattr(self, '_prefetched_objects_cache'):
                for rel_name, qs in self._prefetched_objects_cache.items():
                    data[rel_name] = [obj.to_dict(include_rvs=True) for obj in qs]
            
            # 处理 一对一 关系            
            for rel in self._meta.related_objects:
                if rel.one_to_one:
                    # 获取反向的 related field 对象
                    related_model = rel.related_model
                    try:
                        related_obj = getattr(self, rel.name)
                    except related_model.DoesNotExist:
                        # 当关系不存在时，Django 可能抛出 DoesNotExist 异常
                        related_obj = None

                    if related_obj is None:
                        # 创建一个该模型的新实例（未保存，所有字段为默认值）
                        related_obj = related_model()

                    data[rel.name] = related_obj.to_dict()
            
        return data
    
    @classmethod
    def create_with_check(cls, **kwargs):
        """
        封装一层创建方法，检验并过滤无效字段
        """
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in cls.get_allowed_fields()}
        return cls.objects.create(**filtered_kwargs)

    @classmethod
    def _get_default_lookup_fields(cls):
        """返回推荐的查找字段"""
        fields = []
        for f in cls._meta.fields:
            if f.primary_key or (f.unique and not f.null and not isinstance(f, models.FileField)):
                fields.append(f.name)
        return fields or ['id']
    
    @classmethod
    def update_or_create_with_check(cls, lookup_fields=None, **kwargs):
        """
        安全的 update_or_create
        :param lookup_fields: 用于查找的字段名，如 ['id'], ['username']
        :param kwargs: 字段值
        """
        allowed = cls.get_allowed_fields()

        filtered = {k: v for k, v in kwargs.items() if k in allowed}

        if not filtered:
            raise ValueError("至少需要提供一个有效字段")

        # 推断 lookup_fields
        if lookup_fields is None:
            lookup_fields = cls._get_default_lookup_fields()

        # 分离
        lookup = {k: v for k, v in filtered.items() if k in lookup_fields}
        defaults = {k: v for k, v in filtered.items() if k not in lookup_fields}

        if not lookup:
            raise ValueError(f"查找字段 {lookup_fields} 未在参数中提供")

        return cls.objects.update_or_create(defaults=defaults, **lookup)
    
    @classmethod
    def get_queryset_by_filter_map(cls, filter_map):
        """根据筛选条件获取queryset"""
        filters = build_filters(filter_map)
        qs = cls.objects.filter(**filters)
        return qs
    
    @classmethod
    def get_paginated_response_by_filter_map(cls, filter_map, page_no, page_size, sort):
        qs = cls.get_queryset_by_filter_map(filter_map)

        # 排序需求
        sort = sort or "-id"
        ordering = parse_ordering(sort)
        qs = qs.order_by(*ordering)
        
        # 数据分页
        pagination = paginate_queryset(qs, page_no, page_size)
        results = [item.to_dict() for item in pagination["items"]]
        total = pagination["total_count"]
        
        return total, results

    def update_info(self, allow_fields=None, **kwargs):
        """
        通用字段更新方法
        支持部分字段更新，自动事务
        """
        if allow_fields is None:
            allow_fields = self.__class__.get_allowed_fields()
        else:
            allow_fields = set(allow_fields)

        valid_args = {
            k : v for k, v in kwargs.items()
            if k in allow_fields and hasattr(self, k)
        }
        
        if not valid_args:
            return self  # 无有效字段，直接返回
        
        update_fields = set(valid_args.keys())
        
        # 自动处理 auto_now 字段（如 updated_at）
        for field in self._meta.fields:
            if getattr(field, 'auto_now', False):
                value = datetime.now() if isinstance(field, models.DateTimeField) else True
                setattr(self, field.name, value)
                update_fields.add(field.name)  # ✅ 强制加入 update_fields
        
        with transaction.atomic():
            for k, v in valid_args.items():
                setattr(self, k, v)
            self.save(update_fields=update_fields)
        
        return self
    
    class Meta:
        abstract = True


class TracedModel(AbstractBaseModel):
    """
    带追踪信息的模型，所有业务模型应继承此类。

    提供：
    - id: 主键（自动）
    - created_at: 创建时间（自动）
    - updated_at: 创建时间（自动）
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        verbose_name = "追踪模型"
        verbose_name_plural = "追踪模型"


class SoftDeleteManager(models.Manager):
    """软删除模型管理器"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(TracedModel):
    """
    基础模型，支持审计、软删除，CURD基础。

    提供：
    - id: 主键（自动）
    - created_at: 创建时间（自动）
    - updated_at: 更新时间（自动）
    - is_deleted: 软删除标记
    - deleted_at: 删除时间
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    def soft_delete(self):
        """软删除"""
        if self.is_deleted: return
        
        with transaction.atomic():
            self.is_deleted = True
            self.updated_at = datetime.now()
            self.deleted_at = datetime.now()
            self.save(update_fields=["is_deleted", "updated_at", "deleted_at"])

        return self
    
    @classmethod
    def batch_soft_delete(cls, ids: list):
        """批量软删除"""
        return cls.objects.filter(
            id__in=ids
        ).update(
            is_deleted=True, 
            updated_at=datetime.now(), 
            deleted_at=datetime.now()
        )
    
    @classmethod
    def get_prompt_list_of_column(
        cls, 
        column: str, 
        input: str, 
        with_id: bool = False,
        limit: int = 100,
        filter_columns: dict[str, str] | None = None,
        sub_column: str | None = None,
        extra_filters: dict[str, object] | None = None,
    ):
        """
        获取指定字段的模糊搜索下拉提示列表（常用于前端 autocomplete）。

        该方法在当前模型上执行模糊查询（icontains），返回去重后的结果，支持附加过滤、
        返回 ID、拼接子字段等功能，适用于构建动态下拉选项。

        Args:
            column (str): 
                主要搜索字段名（必须是模型的有效字段）。将在该字段上执行 
                ``icontains`` 模糊匹配，匹配内容由 ``input`` 参数提供。
            
            input (str): 
                用户输入的搜索关键词。用于在 ``column`` 字段中进行不区分大小写的
                子字符串匹配（如 SQL 中的 ``ILIKE '%input%'``）。

            with_id (bool, optional): 
                是否在返回结果中包含数据库主键 ID。默认为 ``False``。
                - 若为 ``True``，每个结果项包含 ``"id"`` 和 ``"value"``；
                - 若为 ``False``，仅包含 ``"value"``。

            limit (int, optional): 
                最大返回结果数量。默认为 100。

            filter_columns (dict[str, str] | None, optional): 
                额外的过滤条件字典，用于对其他字段进行模糊匹配。
                格式：``{"字段名": "过滤值"}``，每个键值对会转换为 
                ``字段名__icontains=过滤值`` 加入查询条件。
                仅适用于文本类型字段；对布尔、数字或外键字段使用可能导致异常或无效查询。

            sub_column (str | None, optional): 
                可选的辅助字段名。当 ``with_id=True`` 且提供此参数时，
                返回的 ``value`` 将拼接为主字段和子字段的组合，格式为：
                ``"{column} ({sub_column})"``。
                例如：column="name", sub_column="code" → "iPhone (IP15)"。

        Returns:
            list[dict]: 
                返回字典列表，每个字典代表一个下拉选项：
                - 若 ``with_id=False``: ``[{"value": "匹配值"}, ...]``
                - 若 ``with_id=True`` 且无 ``sub_column``: 
                ``[{"id": 123, "value": "匹配值"}, ...]``
                - 若 ``with_id=True`` 且有 ``sub_column``: 
                ``[{"id": 123, "value": "主值 (子值)"}, ...]``

        Example:
            # 搜索 name 包含 "john" 的用户，返回 ID 和 name
            User.get_prompt_list_of_column(
                column="name",
                input="john",
                with_id=True
            )
            # → [{"id": 5, "value": "John Doe"}, ...]

            # 搜索产品名称，同时过滤 code 字段，并拼接分类
            Product.get_prompt_list_of_column(
                column="name",
                input="phone",
                with_id=True,
                sub_column="category",
                filter_columns={"code": "A1"}
            )
            # → [{"id": 101, "value": "SmartPhone (Electronics)"}, ...]
        """
        # 安全校验字段名
        # allowed_fields = {f.name for f in cls._meta.get_fields()}
        # if column not in allowed_fields:
        #     raise ValueError(f"Invalid column: {column}")
        # if sub_column and sub_column not in allowed_fields:
        #     raise ValueError(f"Invalid sub_column: {sub_column}")
        # 构建基础过滤
        filters = {f"{column}__icontains": input}
        if filter_columns: 
            for key, value in filter_columns.items():
                # 跳过 None 和空字符串（避免无意义查询）
                if value is None:
                    continue

                # 如果是字符串，先规范化空格
                if isinstance(value, str):
                    normalized = value.strip()
                    if normalized == "":  # 规范化后为空，跳过
                        continue
                    filters[f"{key}__icontains"] = normalized
                else:
                    filters[key] = value
        # 额外过滤（注意：仅适用于文本字段！当前主要为过滤company_id进行租户隔离）
        if extra_filters:
            filters.update(extra_filters)  
        qs = cls.objects.filter(**filters)
        ret_list = []
        if with_id:
            if sub_column:
                qs = qs.values_list("id", column, sub_column).distinct().order_by("-id")[:limit]
                ret_list = [{"id": item[0], "value": f'{item[1]} ({item[2]})' } for item in qs]
            else:
                qs = qs.values_list("id", column).distinct().order_by("-id")[:limit]
                ret_list = [{"id": item[0], "value": item[1]} for item in qs]
        else:
            qs = qs.values_list(column).distinct().order_by(column)[:limit]
            print("qs:", qs)
            ret_list = [{"value": item[0]} for item in qs]
        return ret_list
        
    class Meta:
        abstract = True
        verbose_name = "基础模型"
        verbose_name_plural = "基础模型"
        indexes = [
            models.Index(fields=['is_deleted', '-created_at']),  # 分页+过滤
            models.Index(fields=['-updated_at']),
            models.Index(fields=['is_deleted']),  # 单独过滤场景
        ]


class BusinessBaseModel(BaseModel):
    """
    业务模型，提供公司、组织归属
    - company: 公司
    - organization: 组织
    """
    company = models.ForeignKey(
        "identity.Company",
        null=True,
        on_delete=models.CASCADE,
        verbose_name="所属公司"
    )
    
    organization = models.ForeignKey(
        "identity.Organization",
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="所属部门"
    )
    
    class Meta:
        abstract = True
        verbose_name = "业务模型"
        verbose_name_plural = "业务模型"