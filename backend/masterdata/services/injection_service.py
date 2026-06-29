from django.db import transaction
from masterdata.models import InjectionMoldingMachine, InjectionUnit
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset
from extensions.exceptions import BizException, ERROR_REQUIRED_FIELD, ERROR_DATA_NOT_FOUND, ERROR_DATA_FOUND


def create_injection_machine(company_id: int, organization_id: int, **kwargs):
    """创建注塑机"""
    device_no = kwargs.get("device_no")
    if not device_no:
        raise BizException(ERROR_REQUIRED_FIELD, "设备编号必须存在，且不能为空")
    if InjectionMoldingMachine.objects.filter(device_no=device_no, company_id=company_id).exists():
        raise BizException(ERROR_DATA_FOUND, f"设备编号 {device_no} 已存在，请勿重复添加！")

    with transaction.atomic():
        kwargs["company_id"] = company_id
        kwargs["organization_id"] = organization_id
        injection_machine = InjectionMoldingMachine.create_with_check(**kwargs)
        for unit_kwargs in kwargs.get("injection_units", []):
            if "id" in unit_kwargs:
                unit_kwargs.pop("id")
            InjectionUnit.create_with_check(machine=injection_machine, **unit_kwargs)

    return _build_injection_machine_dict(injection_machine)


def _get_injection_machine(injection_machine_id: int) -> InjectionMoldingMachine:
    """获取注塑机对象"""
    injection_machine_id = validate_pk(injection_machine_id, "注塑机ID")
    injection_machine = InjectionMoldingMachine.objects.filter(
        pk=injection_machine_id
    ).select_related("time_standard").prefetch_related(
        "injection_units"
    ).first()
    if not injection_machine:
        raise BizException(ERROR_DATA_NOT_FOUND, "注塑机不存在")
    return injection_machine


def _build_injection_machine_dict(injection_machine: InjectionMoldingMachine) -> dict:
    """构建注塑机完整数据（含注射单元和工时标准）"""
    ret_dict = injection_machine.to_dict()
    ret_dict["injection_units"] = [
        unit.to_dict() for unit in injection_machine.injection_units.all()
    ]
    time_standard = getattr(injection_machine, "time_standard", None)
    ret_dict["time_standard"] = time_standard.to_dict() if time_standard else None
    return ret_dict


def _validate_device_no_unique(company_id: int, device_no: str, exclude_id: int = None):
    """校验设备编号唯一性"""
    if not device_no:
        raise BizException(ERROR_REQUIRED_FIELD, "设备编号必须存在，且不能为空")
    qs = InjectionMoldingMachine.objects.filter(device_no=device_no, company_id=company_id)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    if qs.exists():
        raise BizException(ERROR_DATA_FOUND, f"设备编号 {device_no} 已存在，请勿重复添加！")


def get_injection_machine_info(injection_machine_id: int) -> dict:
    """获取注塑机信息"""
    injection_machine = _get_injection_machine(injection_machine_id)
    return _build_injection_machine_dict(injection_machine)


def update_injection_machine(company_id: int, injection_machine_id: int, **kwargs) -> dict:
    """更新注塑机信息"""
    injection_machine = _get_injection_machine(injection_machine_id)
    _validate_device_no_unique(company_id, kwargs.get("device_no"), exclude_id=injection_machine_id)

    with transaction.atomic():
        injection_machine.update_info(**kwargs)
        # 删除前端未传入的注射单元
        incoming_ids = {
            u["id"] for u in kwargs.get("injection_units", [])
            if u.get("id") is not None
        }
        for unit in injection_machine.injection_units.all():
            if unit.id not in incoming_ids:
                unit.delete()
        # 添加/更新注射单元
        for unit_kwargs in kwargs.get("injection_units", []):
            if unit_kwargs.get("id") is not None:
                unit = InjectionUnit.objects.filter(pk=unit_kwargs["id"]).first()
                unit.update_info(machine=injection_machine, **unit_kwargs)
            else:
                InjectionUnit.create_with_check(machine=injection_machine, **unit_kwargs)

    return _build_injection_machine_dict(injection_machine)


def delete_injection_machine(injection_machine_id: int) -> None:
    """删除注塑机"""
    injection_machine = _get_injection_machine(injection_machine_id)
    injection_machine.soft_delete()


def get_injection_machine_list(
    company_id: int,
    brand: str = None,
    model: str = None,
    location: str = None,
    device_no: str = None,
    asset_no: str = None,
    machine_type: str = None,
    unit_count: str = None,
    drive_system: str = None,
    manufacturer: str = None,
    status: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None
) -> tuple:
    """获取注塑机列表"""
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "brand": {"input": brand, "column": "brand", "lookup": "icontains"},
        "model": {"input": model, "column": "model", "lookup": "icontains"},
        "location": {"input": location, "column": "location", "lookup": "icontains"},
        "device_no": {"input": device_no, "column": "device_no", "lookup": "icontains"},
        "asset_no": {"input": asset_no, "column": "asset_no", "lookup": "icontains"},
        "machine_type": {"input": machine_type, "column": "machine_type", "lookup": "icontains"},
        "drive_system": {"input": drive_system, "column": "drive_system", "lookup": "icontains"},
        "unit_count": {"input": unit_count, "column": "unit_count", "lookup": "icontains"},
        "status": {"input": status, "column": "status", "lookup": "icontains"},
    }
    filters = build_filters(filter_map)
    qs = InjectionMoldingMachine.objects.filter(**filters).prefetch_related("injection_units")

    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)

    # 分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict(include_rvs=True) for item in pagination["items"]]
    return pagination["total_count"], results


def batch_delete_injection_machine(ids: list) -> None:
    """批量删除注塑机"""
    ids = validate_id_list(ids, "注塑机ID")
    InjectionMoldingMachine.batch_soft_delete(ids)