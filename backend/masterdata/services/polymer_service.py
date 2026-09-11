"""
Polymer（聚合物）服务层

设计原则
========
1. 数据库关系
   - Polymer 与四张 Moldflow 参数子表（PolymerRheology / PVT / Mechanical / Shrinkage）
     均为普通 ForeignKey，不加 unique
   - 一个 Polymer 在业务上最多对应"一组"仿真参数，由 service 统一保证

2. 业务约束（不允许其他模块绕过）
   - 同步入口：_upsert_property(model_cls, polymer, data)
   - 删除入口：_delete_property(model_cls, polymer)
   - 创建时四张表统一创建（事务）
   - 更新时四张表统一按"是否提供"决定"创建/更新/删除"

3. API 输出
   - 默认输出单对象形式的 rheology / pvt / mechanical / shrinkage
   - 该组装仅在 polymer_service 中进行，to_dict() 不再伪装反向关系
"""
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


# 四张 Moldflow 参数子表，按业务顺序固定
MOLDFLOW_PROPERTY_MODELS = [
    ("rheology",   PolymerRheology),
    ("pvt",        PolymerPVT),
    ("mechanical", PolymerMechanical),
    ("shrinkage",  PolymerShrinkage),
]


# ============================================================
# 内部辅助
# ============================================================

def _get_polymer_by_id(polymer_id: int) -> Polymer:
    """通过ID获取聚合物对象（含 Moldflow 参数预加载）"""
    polymer_id = validate_pk(polymer_id, "聚合物ID")
    polymer = Polymer.objects.filter(
        id=polymer_id
    ).prefetch_related(
        "rheology_set", "pvt_set", "mechanical_set", "shrinkage_set"
    ).first()
    if not polymer:
        raise BizException(ERROR_DATA_NOT_FOUND, "该ID对应的聚合物不存在")
    return polymer


def _get_single_property(model_cls, polymer, raise_on_duplicate: bool = True):
    """
    获取该 Polymer 对应的单条 Moldflow 参数记录

    业务约束：一个 Polymer 对每种参数最多一条
    - 0 条：返回 None
    - 1 条：返回该对象
    - 多条：默认抛出异常（避免静默吞掉重复数据）
    """
    qs = model_cls.objects.filter(polymer=polymer)
    count = qs.count()
    if count == 0:
        return None
    if count > 1 and raise_on_duplicate:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            f"{model_cls.__name__} 对应 Polymer 存在 {count} 条记录，请联系管理员修复数据",
        )
    return qs.first()


def _upsert_property(model_cls, polymer, data: dict):
    """
    业务唯一的参数同步入口：upsert 语义

    - 已存在：更新字段
    - 不存在：创建记录
    - 数据为空 dict：删除已有记录（视为"取消该类参数"）
    """
    if data is None:
        return  # 调用方没有传该类参数，视为"不动"

    data = {k: v for k, v in data.items() if v is not None}
    existing = _get_single_property(model_cls, polymer)

    if not data:
        # 调用方明确传了空 dict，删除已有记录
        if existing is not None:
            existing.delete()
        return

    if existing is None:
        model_cls.create_with_check(polymer=polymer, **data)
    else:
        for field, value in data.items():
            setattr(existing, field, value)
        existing.save()


def _sync_moldflow_properties(polymer: Polymer, kwargs: dict, is_create: bool = False):
    """
    同步四张 Moldflow 参数子表

    - is_create=True：四张表统一 create（kwargs 中只处理提供的 key）
    - is_create=False：根据 kwargs 中每个 key 的值决定 upsert / 删除
    """
    for key, model_cls in MOLDFLOW_PROPERTY_MODELS:
        if key not in kwargs:
            continue
        data = kwargs[key]
        if is_create:
            if not data:
                continue
            model_cls.create_with_check(polymer=polymer, **data)
        else:
            _upsert_property(model_cls, polymer, data)


def _assemble_moldflow_properties(polymer: Polymer) -> dict:
    """
    业务层组装单对象形式的 Moldflow 参数

    数据库层的关系是 ForeignKey（一对多），prefetch 拿到的是 QuerySet；
    业务层约定最多一条，所以这里取第一条。

    返回：
    {
        "rheology": {...} 或 None,
        "pvt":      {...} 或 None,
        "mechanical": {...} 或 None,
        "shrinkage":  {...} 或 None,
    }
    """
    result = {}
    for key, model_cls in MOLDFLOW_PROPERTY_MODELS:
        obj = _get_single_property(model_cls, polymer, raise_on_duplicate=False)
        if obj is None:
            result[key] = None
        else:
            result[key] = obj.to_dict()
    return result


def _build_polymer_dict(polymer: Polymer) -> dict:
    """构建聚合物完整数据（含 Moldflow 参数）"""
    data = polymer.to_dict()
    data.update(_assemble_moldflow_properties(polymer))
    return data


# ============================================================
# 公开 API
# ============================================================

def create_polymer(company_id: int, organization_id: int, **kwargs) -> dict:
    """
    创建聚合物

    如果传入了 Moldflow 参数（rheology / pvt / mechanical / shrinkage），
    会在同一事务中统一创建。
    """
    kwargs["company_id"] = company_id
    kwargs["organization_id"] = organization_id

    with transaction.atomic():
        polymer = Polymer.create_with_check(**kwargs)
        _sync_moldflow_properties(polymer, kwargs, is_create=True)

    return _build_polymer_dict(polymer)


def get_polymer_info(polymer_id: int) -> dict:
    """获取聚合物信息（含 Moldflow 参数）"""
    polymer = _get_polymer_by_id(polymer_id)
    return _build_polymer_dict(polymer)


def update_polymer_info(polymer_id: int, **kwargs) -> dict:
    """
    更新聚合物信息

    同步策略：
    - kwargs 中包含的 Moldflow key：根据其值（非空 dict=更新，空 dict=删除，None=不变）
    - kwargs 中未包含的 Moldflow key：保持不变
    """
    polymer = _get_polymer_by_id(polymer_id)

    with transaction.atomic():
        polymer.update_info(**kwargs)
        _sync_moldflow_properties(polymer, kwargs, is_create=False)

    return _build_polymer_dict(polymer)


def delete_polymer(polymer_id: int) -> None:
    """
    删除聚合物（软删除）

    Moldflow 参数子表通过 on_delete=CASCADE 一并删除（物理删除，因为子表本身不维护软删除状态）
    """
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
    """获取聚合物列表（不含 Moldflow 参数）"""
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
    """批量删除聚合物（软删除）"""
    ids = validate_id_list(ids, "聚合物ID")
    Polymer.batch_soft_delete(ids)
