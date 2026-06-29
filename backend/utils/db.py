from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT
from django.core.paginator import Paginator, Page, EmptyPage, PageNotAnInteger
from typing import List, Any, Type, Set
from django.db import models

def parse_ordering(sort: str, allowed_fields: set = None, strict = True) -> List[str]:
    """
    将类似 "+username,-age" 的排序字符串解析为 Django order_by 兼容的字段列表。

    :param sort: 排序字符串，支持 +field, -field
    :param allowed_fields: 允许的字段名集合，用于安全过滤
    :param strict: 是否严格检查字段名，如果为 True，则不允许非法字段
    :return: 可用于 order_by(*result) 的列表
    """
    ordering = []
    for field in sort.split(','):
        field = field.strip()
        if not field: continue
        
        if field.startswith('+'):
            clean_field = field[1:]
            prefix = ''
        elif field.startswith('-'):
            clean_field = field[1:]
            prefix = '-'
        else:
            clean_field = field
            prefix = ''
        
        # 检查字段名，严格模式下不允许非法字段
        if allowed_fields and clean_field not in allowed_fields:
            if strict:
                raise BizException(ERROR_ILLEGAL_ARGUMENT, f"不被允许的排序字段：{field}")
            else:
                continue
        
        ordering.append(prefix + clean_field)
    
    return ordering


def paginate_queryset(
    queryset: Type[models.QuerySet],
    page_no: int,
    page_size: int
):
    """
    对 Queryset 进行分页。
    """
    paginator = Paginator(queryset, page_size)
    
    try:
        page = paginator.page(page_no)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    
    return {
        "items": page.object_list,
        "page_no": page.number,
        "page_size": page_size,
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "has_next": page.has_next(),
        "has_prev": page.has_previous(),
    }


def build_filters(filter_map: dict):
    """
    根据 filter_map 构建 Django ORM 查询条件
    支持 exact, icontains, isnull 等 lookup
    """
    filters = {}
    for field, config in filter_map.items():
        value = config["input"]
        column = config["column"]
        lookup = config["lookup"]

        # 跳过空值（None、""），但保留 False 和 0
        if value is None and field not in ["company_id"]:
            continue
        if type(value) == str:  # 忽略空字符串
            if not value.strip(): continue
        if lookup == "isnull":
            # 特殊处理：isnull, 如果不是 bool，忽略（或可抛警告）
            if isinstance(value, bool):  # 只接受布尔值
                filters[f"{column}__isnull"] = value
        elif lookup == "exact":
            filters[f"{column}"] = value         
        else:
            filters[f"{column}__{lookup}"] = value

    return filters


class QueryFilterBuilder:
    def __init__(self):
        self.map = {}
        
    def add(self, field_name, input_value, column=None, lookup="exact"):
        self.map[field_name] = {
            "input": input_value,
            "column": column or field_name,
            "lookup": lookup,
        }
        return self

    def build(self):
        return build_filters(self.map)