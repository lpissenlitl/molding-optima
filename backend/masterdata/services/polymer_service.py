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
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT


# ============================================================
# 辅助函数
# ============================================================

def _get_polymer_by_id(polymer_id: int) -> Polymer:
    """通过ID获取聚合物对象（含性能参数预加载）"""
    polymer_id = validate_pk(polymer_id, "聚合物ID")
    polymer = Polymer.objects.filter(
        id=polymer_id
    ).prefetch_related(
        "rheology", "pvt", "mechanical", "shrinkage"
    ).first()
    if not polymer:
        raise BizException(ERROR_DATA_NOT_FOUND, "该ID对应的聚合物不存在")
    return polymer


def _build_polymer_dict(polymer: Polymer) -> dict:
    """构建聚合物完整数据（含性能参数）"""
    return polymer.to_dict(include_rvs=True)


def _check_polymer_filler_composition(composition: dict):
    """
    检查填充物占比是否合法
    返回补充了 ratio 和 filler 对象的 composition
    """
    filler_id = composition.get("filler_id")
    percentage = composition.get("percentage")

    if filler_id is None:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "填充物ID不能为空")
    filler = Filler.objects.filter(pk=filler_id).first()
    if not filler:
        raise BizException(ERROR_DATA_NOT_FOUND, "填充物不存在")
    if percentage is None or percentage <= 0 or percentage > 100:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "填充物占比必须在 0-100 之间")

    composition["ratio"] = percentage / 100
    composition["filler"] = filler
    return composition


def _sync_performance_properties(polymer: Polymer, kwargs: dict, is_create: bool = False):
    """
    同步性能参数（流变/PVT/机械/收缩）
    is_create=True 时创建，is_create=False 时更新或创建
    """
    property_models = {
        "rheology": PolymerRheology,
        "pvt": PolymerPVT,
        "mechanical": PolymerMechanical,
        "shrinkage": PolymerShrinkage,
    }
    for key, model_cls in property_models.items():
        if key not in kwargs:
            continue
        if is_create:
            model_cls.create_with_check(polymer=polymer, **kwargs[key])
        else:
            model_cls.update_or_create_with_check(
                lookup_fields=['polymer'],
                polymer=polymer,
                **kwargs[key]
            )


# ============================================================
# 公开 API
# ============================================================

def create_polymer(company_id: int, organization_id: int, **kwargs):
    """创建聚合物"""
    kwargs["company_id"] = company_id
    kwargs["organization_id"] = organization_id

    with transaction.atomic():
        polymer = Polymer.create_with_check(**kwargs)
        _sync_performance_properties(polymer, kwargs, is_create=True)

    return _build_polymer_dict(polymer)


def get_polymer_info(polymer_id: int) -> dict:
    """获取聚合物信息"""
    polymer = _get_polymer_by_id(polymer_id)
    return _build_polymer_dict(polymer)


def update_polymer_info(polymer_id: int, **kwargs) -> dict:
    """更新聚合物信息"""
    polymer = _get_polymer_by_id(polymer_id)

    with transaction.atomic():
        polymer.update_info(**kwargs)
        _sync_performance_properties(polymer, kwargs, is_create=False)

    return _build_polymer_dict(polymer)


def delete_polymer(polymer_id: int) -> None:
    """删除聚合物"""
    polymer = _get_polymer_by_id(polymer_id)
    polymer.soft_delete()


def get_polymer_list(
    company_id: int,
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
) -> tuple:
    """获取聚合物列表"""
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

    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)

    # 分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict() for item in pagination["items"]]
    return pagination["total_count"], results


def batch_delete_polymer(ids: list) -> None:
    """批量删除聚合物"""
    ids = validate_id_list(ids, "聚合物ID")
    Polymer.batch_soft_delete(ids)
