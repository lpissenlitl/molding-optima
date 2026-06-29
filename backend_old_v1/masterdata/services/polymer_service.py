from identity.models import User
from django.db import transaction
from masterdata.models import (
    Polymer,
    PolymerRheology,
    PolymerPVT,
    PolymerMechanical,
    PolymerShrinkage,
    Filler,
)
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND


def _check_polymer_filler_composition(composition: dict):
    """检查填充物占比是否合法"""
    filler_id = composition.get("filler_id")
    percentage = composition.get("percentage")

    # 基础字段存在性校验
    if filler_id is None:
        raise ValueError("填充物ID不能为空")  # TODO: 添加自定义错误码
    filler = Filler.objects.filter(pk=filler_id).first()
    if not filler:
        raise ValueError("填充物不存在")  # TODO: 添加自定义错误码
    if percentage <= 0 or percentage > 100:
        raise ValueError("填充物占比范围错误")  # TODO: 添加自定义错误码
    
    composition["ratio"] = percentage / 100
    composition["filler"] = filler
    return composition


def create_polymer(user: User, **kwargs):
    """创建聚合物"""
    # TODO: 验证 user 操作权限
    
    with transaction.atomic():
        kwargs = {
            "company_id": user.company_id,
            "organization_id": user.organization_id,
            **kwargs
        }
        polymer = Polymer.create_with_check(**kwargs)
        # --- 创建性能参数 ---
        if "rheology" in kwargs:
            PolymerRheology.create_with_check(polymer=polymer, **kwargs["rheology"])
        if "pvt" in kwargs:
            PolymerPVT.create_with_check(polymer=polymer, **kwargs["pvt"])
        if "mechanical" in kwargs:
            PolymerMechanical.create_with_check(polymer=polymer, **kwargs["mechanical"])
        if "shrinkage" in kwargs:
            PolymerShrinkage.create_with_check(polymer=polymer, **kwargs["shrinkage"])


def _get_polymer_by_id(polymer_id: int):
    """通过ID获取聚合物对象"""
    polymer_id = validate_pk(polymer_id, "聚合物ID")
    polymer = Polymer.objects.filter(
        id=polymer_id
    ).prefetch_related(
        "rheology", "pvt", "mechanical", "shrinkage"
    ).first()
    if not polymer:
        raise BizException(ERROR_DATA_NOT_FOUND, "该ID对应的聚合物不存在") # TODO: 抛出异常，补充错误码
    return polymer


def get_polymer_info(user: User, polymer_id: int):
    """获取聚合物信息"""
    # TODO: 验证 user 操作权限
    
    polymer = _get_polymer_by_id(polymer_id)
    ret_dict = polymer.to_dict(include_rvs=True)

    return ret_dict


def update_polymer_info(user: User, polymer_id: int, **kwargs):
    """更新聚合物信息"""
    # TODO: 验证 user 操作权限
    
    polymer = _get_polymer_by_id(polymer_id)
    with transaction.atomic():
        polymer.update_info(**kwargs)
        if "rheology" in kwargs:
            PolymerRheology.update_or_create_with_check(lookup_fields=['polymer'], polymer=polymer, **kwargs["rheology"])
        if "pvt" in kwargs:
            PolymerPVT.update_or_create_with_check(lookup_fields=['polymer'], polymer=polymer, **kwargs["pvt"])
        if "mechanical" in kwargs:
            PolymerMechanical.update_or_create_with_check(lookup_fields=['polymer'], polymer=polymer, **kwargs["mechanical"])
        if "shrinkage" in kwargs:
            PolymerShrinkage.update_or_create_with_check(lookup_fields=['polymer'], polymer=polymer, **kwargs["shrinkage"])


def delete_polymer(user: User, polymer_id: int):
    """删除聚合物"""
    # TODO: 验证 user 操作权限
    
    polymer = _get_polymer_by_id(polymer_id)
    polymer.soft_delete()
    

def get_polymer_list(
    user: User, 
    abbreviation: str = None,
    grade: str = None,
    manufacturer: str = None,
    category: str = None,
    data_source: str = None,
    level_code: str = None, 
    vendor_code: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None
):
    """获取聚合物列表"""
    # TODO: 验证 user 操作权限
    company_id = user.company_id
    # 构建查询参数
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "manufacturer": {"input": manufacturer, "column": "manufacturer", "lookup": "icontains"},
        "grade": {"input": grade, "column": "grade", "lookup": "icontains"},
        "abbreviation": {"input": abbreviation, "column": "abbreviation", "lookup": "icontains"},
        "category": {"input": category, "column": "category", "lookup": "icontains"},
        "data_source": {"input": data_source, "column": "data_source", "lookup": "icontains"},
        "level_code": {"input": level_code, "column": "level_code", "lookup": "icontains"},
        "vendor_code": {"input": vendor_code, "column": "vendor_code", "lookup": "icontains"},
    }
    filters = build_filters(filter_map)
    qs = Polymer.objects.filter(**filters)
    
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict() for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, results

def batch_delete_polymer(user: User, ids: list) -> None:
    """批量删除聚合物"""
    # TODO: 验证 user 操作权限
    
    ids = validate_id_list(ids)
    Polymer.batch_soft_delete(ids)