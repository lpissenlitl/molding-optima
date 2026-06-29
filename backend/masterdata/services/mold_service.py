from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_DATA_FOUND, ERROR_REQUIRED_FIELD
from identity.models import User
from masterdata.models import (
    Mold,
    GatingSystem,
    Cavity,
    Gate,
    CoolingSystem,
    EjectionSystem,
)
from django.db import transaction
from utils.validation import validate_pk, validate_id_list
from utils.db import (
    parse_ordering,
    paginate_queryset,
    build_filters
)
from masterdata.services.project_service import create_project
from utils.object_utils import safe_get
import re


# ============================================================
# 辅助函数
# ============================================================

def _get_mold_by_id(mold_id: int) -> Mold:
    """根据模具ID获取模具对象（含关联数据预加载）"""
    mold_id = validate_pk(mold_id, "模具ID")
    mold = Mold.objects.filter(
        pk=mold_id
    ).select_related("project").prefetch_related(
        "gating_systems__cavities__gates",
        "cooling_system", "ejection_system",
    ).first()
    if not mold:
        raise BizException(ERROR_DATA_NOT_FOUND, "模具信息不存在")
    return mold


def _build_mold_dict(mold: Mold) -> dict:
    """构建模具完整数据（含关联系统）"""
    return mold.to_dict(include_rvs=True)


def _validate_mold_no_unique(company_id: int, mold_no: str, exclude_id: int = None):
    """校验模具编号唯一性"""
    if not mold_no:
        raise BizException(ERROR_REQUIRED_FIELD, "模具编号必须存在，且不能为空")
    qs = Mold.objects.filter(mold_no=mold_no, company_id=company_id)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise BizException(ERROR_DATA_FOUND, f"模具编号 {mold_no} 已存在，请勿重复添加！")


def _sync_gates(cavity: Cavity, incoming_gates: list):
    """同步浇口数据：删除不在 incoming 中的，创建/更新 incoming 中的"""
    incoming_ids = {g.get("id") for g in incoming_gates if g.get("id") is not None}
    # 删除
    for gate in cavity.gates.all():
        if gate.id not in incoming_ids:
            gate.delete()
    # 创建/更新
    for gate_kwargs in incoming_gates:
        if gate_kwargs.get("id") is not None:
            gate = Gate.objects.filter(pk=gate_kwargs["id"]).first()
            gate.update_info(cavity=cavity, **gate_kwargs)
        else:
            Gate.create_with_check(cavity=cavity, **gate_kwargs)


def _sync_cavities(gating_system: GatingSystem, incoming_cavities: list):
    """同步型腔数据：删除不在 incoming 中的，创建/更新 incoming 中的（含浇口）"""
    incoming_ids = {c.get("id") for c in incoming_cavities if c.get("id") is not None}
    # 删除
    for cavity in gating_system.cavities.all():
        if cavity.id not in incoming_ids:
            cavity.delete()
    # 创建/更新
    for cavity_kwargs in incoming_cavities:
        if cavity_kwargs.get("id") is not None:
            cavity = Cavity.objects.filter(pk=cavity_kwargs["id"]).first()
            cavity.update_info(gating_system=gating_system, **cavity_kwargs)
        else:
            cavity = Cavity.create_with_check(gating_system=gating_system, **cavity_kwargs)
        # 同步浇口
        if "gates" in cavity_kwargs:
            _sync_gates(cavity, cavity_kwargs["gates"])


def _sync_gating_systems(mold: Mold, incoming_gating_systems: list):
    """同步浇注系统数据：删除不在 incoming 中的，创建/更新 incoming 中的（含型腔、浇口）"""
    incoming_ids = {g.get("id") for g in incoming_gating_systems if g.get("id") is not None}
    # 删除
    for gating_system in mold.gating_systems.all():
        if gating_system.id not in incoming_ids:
            gating_system.delete()
    # 创建/更新
    for gating_system_kwargs in incoming_gating_systems:
        if gating_system_kwargs.get("id") is not None:
            gating_system = GatingSystem.objects.filter(pk=gating_system_kwargs["id"]).first()
            gating_system.update_info(mold=mold, **gating_system_kwargs)
        else:
            gating_system = GatingSystem.create_with_check(mold=mold, **gating_system_kwargs)
        # 同步型腔
        if "cavities" in gating_system_kwargs:
            _sync_cavities(gating_system, gating_system_kwargs["cavities"])


# ============================================================
# 公开 API
# ============================================================

def create_mold(user: User, **kwargs):
    """
    创建模具
    注意：此方法暂时需要 user，因为可能自动创建项目（create_project 需要 operator 写审计字段）
    """
    company_id = user.company_id
    organization_id = user.organization_id
    _validate_mold_no_unique(company_id, kwargs.get("mold_no"))

    with transaction.atomic():
        # 如果没有项目ID，自动创建一个草稿项目
        if not kwargs.get("project_id"):
            project_info = create_project(
                company_id=company_id,
                organization_id=organization_id,
                operator=user,
                is_draft=True
            )
            kwargs["project_id"] = project_info["id"]

        # 创建模具
        kwargs["company_id"] = company_id
        kwargs["organization_id"] = organization_id
        mold = Mold.create_with_check(**kwargs)

        # 创建浇注系统（含型腔、浇口）
        _sync_gating_systems(mold, kwargs.get("gating_systems", []))

        # 创建冷却系统
        if "cooling_system" in kwargs:
            CoolingSystem.create_with_check(mold=mold, **kwargs["cooling_system"])

        # 创建顶出系统
        if "ejection_system" in kwargs:
            EjectionSystem.create_with_check(mold=mold, **kwargs["ejection_system"])

    return _build_mold_dict(mold)


def get_mold_info(mold_id: int) -> dict:
    """获取模具信息"""
    mold = _get_mold_by_id(mold_id)
    return _build_mold_dict(mold)


def update_mold_info(company_id: int, mold_id: int, **kwargs) -> dict:
    """更新模具信息"""
    mold = _get_mold_by_id(mold_id)
    _validate_mold_no_unique(company_id, kwargs.get("mold_no"), exclude_id=mold_id)

    with transaction.atomic():
        mold.update_info(**kwargs)

        # 更新浇注系统（含型腔、浇口）
        if "gating_systems" in kwargs:
            _sync_gating_systems(mold, kwargs["gating_systems"])

        # 更新冷却系统（修复：原代码错误地嵌套在 gating_systems 判断内）
        if "cooling_system" in kwargs:
            CoolingSystem.update_or_create_with_check(mold=mold, **kwargs["cooling_system"])

        # 更新顶出系统（修复：原代码错误地嵌套在 gating_systems 判断内）
        if "ejection_system" in kwargs:
            EjectionSystem.update_or_create_with_check(mold=mold, **kwargs["ejection_system"])

    return _build_mold_dict(mold)


def delete_mold(mold_id: int) -> None:
    """删除模具"""
    mold = _get_mold_by_id(mold_id)
    mold.soft_delete()


def get_mold_list(
    company_id: int,
    mold_no: str = None,
    mold_name: str = None,
    category: str = None,
    structure: str = None,
    cavity_layout: str = None,
    manufacturing_method: str = None,
    status: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None,
) -> tuple:
    """获取模具列表"""
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "mold_no": {"input": mold_no, "column": "mold_no", "lookup": "icontains"},
        "mold_name": {"input": mold_name, "column": "mold_name", "lookup": "icontains"},
        "category": {"input": category, "column": "category", "lookup": "icontains"},
        "structure": {"input": structure, "column": "structure", "lookup": "exact"},
        "cavity_layout": {"input": cavity_layout, "column": "cavity_layout", "lookup": "exact"},
        "manufacturing_method": {"input": manufacturing_method, "column": "project__manufacturing_method", "lookup": "exact"},
        "status": {"input": status, "column": "status", "lookup": "exact"},
    }

    filters = build_filters(filter_map)
    qs = Mold.objects.filter(**filters).select_related("project")

    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)

    # 分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [
        {
            **item.to_dict(),
            "manufacturing_method": safe_get(item, "project.manufacturing_method"),
        }
        for item in pagination["items"]
    ]
    return pagination["total_count"], results


def batch_delete_mold(ids: list) -> None:
    """批量删除模具"""
    ids = validate_id_list(ids, "模具ID列表")
    Mold.batch_soft_delete(ids)
