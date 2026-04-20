"""
胶料服务
"""
import logging
from django.db import transaction
from gis.common.django_ext.models import paginate
from gis.common.exceptions import BizException

from hsmolding.exceptions import ERROR_DATA_EXIST, ERROR_DATA_NOT_EXIST
from hsmolding.models import Polymer


error_message = ""


# 添加胶料信息
def _add_polymer(params: dict):
    polymer = Polymer()
    for name in params:
        if hasattr(Polymer, name):
            setattr(polymer, name, params[name])
    polymer.save()
    return polymer


# 添加胶料信息接口
def add_polymer(params):
    trademark = params.get("trademark")
    company_id = params.get("company_id")
    polymers = Polymer.objects.filter(trademark=trademark, company_id=company_id).order_by("id")
    if len(polymers) == 0:
        with transaction.atomic():
            polymer = _add_polymer(params)
            # return polymer.to_dict()
            return { "id": polymer.id }
    else:
        raise BizException(ERROR_DATA_EXIST, f'该塑料牌号 {trademark} 已存在')


# 获取胶料信息
def _get_polymer(polymer_id):
    if polymer_id:
        polymer = Polymer.objects.filter(id=polymer_id).first()
        if not polymer:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该胶料不存在")
        polymer_info = polymer.to_dict()
        return polymer_info


# 获取胶料信息接口
def get_polymer(polymer_id):
    if polymer_id:
        return _get_polymer(polymer_id)


# 更新胶料信息
def _update_polymer(polymer_id, params):
    # 更新时,如果trademark已存在,且不属于当前塑料,那么给出提示
    trademark = params.get('trademark')
    if trademark is not None:
        if Polymer.objects.exclude(pk=polymer_id).filter(trademark=trademark).exists():
            raise BizException(ERROR_DATA_EXIST, "相同塑料牌号")
    if params and polymer_id:
        polymer = Polymer.objects.filter(pk=polymer_id).first()
        if polymer:
            for key, value in params.items():
                setattr(polymer, key, value)
            polymer.save()
        else:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该胶料不存在")

# 更新胶料信息接口
def update_polymer(polymer_id, params):
    if polymer_id:
        _update_polymer(polymer_id, params)
    # return get_polymer(polymer_id)
    return { "id": polymer_id }


# 删除胶料接口
def delete_polymer(polymer_id):
    if polymer_id:
        polymer = Polymer.objects.filter(pk=polymer_id).first()
        if polymer:
            polymer.delete()
        else:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该胶料不存在")

# 获取胶料列表
def get_list_of_polymer(
    page_no=None, 
    page_size=None, 
    abbreviation=None, 
    trademark=None, 
    series=None, 
    manufacturer=None, 
    company_id=None, 
    polymer_id_list=None
):
    query = Polymer.objects.all()
    if abbreviation:
        query = query.filter(abbreviation__icontains=abbreviation)
    if trademark:
        query = query.filter(trademark__icontains=trademark)
    if series:
        query = query.filter(series__icontains=series)
    if manufacturer:
        query = query.filter(manufacturer__icontains=manufacturer)
    if company_id:
        allow_ids = [ -1, company_id ]
        query = query.filter(company_id__in=allow_ids)
    if polymer_id_list:
        query = query.filter(pk__in=polymer_id_list)
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    return total_count, [e.to_dict() for e in query]


# 删除多条胶料
def delete_multiple_polymer(polymer_id_list: list):
    for polymer_id in polymer_id_list:
        delete_polymer(polymer_id)


# 胶料列表 excel导出
def list_polymer_view(polymer_id_list):
    query = Polymer.objects.values_list("id", "abbreviation", "trademark", "manufacturer", "filler","recommend_melt_temperature", "recommend_mold_temperature", "dry_temperature", "dry_time", "updated_at").filter(pk__in=polymer_id_list)
    return query


# 获取胶料种类列表 options
def list_polymer_abbreviation(company_id=None):
    query = Polymer.objects.filter(company_id__in=[ -1, company_id ]).values_list("abbreviation").distinct()
    return [ { "value": item[0] } for item in query]


# 塑料牌号列表 options
def list_polymer_trademark(
        company_id=None,
        abbreviation=None,
        trademark=None 
    ):
    query = Polymer.objects.filter(company_id__in=[ -1, company_id ]).filter(deleted=0).all()
    if abbreviation:
        query = query.filter(abbreviation=abbreviation)
    if trademark:
        query = query.filter(trademark__icontains=trademark)
    query = query.values("id", "abbreviation", "trademark", "manufacturer", "category", "recommend_melt_temperature").order_by("abbreviation")

    return [{ 
        "id": item.get("id"),
        "abbreviation": item.get("abbreviation"),
        "trademark": item.get("trademark"),
        "manufacturer": item.get("manufacturer"),
        "category": item.get("category"),
        "recommend_melt_temperature": item.get("recommend_melt_temperature")
    } for item in query]


# 根据列头获取下拉提示
def get_prompt_list_of_column(column: str, input_str: str, company_id: int = None):
    items = []
    if company_id:
        query = Polymer.objects.filter(company_id__in=[-1, company_id]).filter(deleted=0) # 过滤公司&已删除
    else:
        query = Polymer.objects.all()
    if column == "abbreviation":
        items = query.filter(abbreviation__icontains=input_str).values_list("abbreviation", flat=True).order_by("abbreviation").distinct()
    if column == "trademark":
        items = query.filter(trademark__icontains=input_str).values_list("trademark", flat=True).order_by("trademark").distinct()
    return list(items)