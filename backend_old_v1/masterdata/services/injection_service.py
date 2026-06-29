from identity.models import User
from django.db import transaction
from masterdata.models import InjectionMoldingMachine, InjectionUnit
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset
from extensions.exceptions import BizException, ERROR_REQUIRED_FIELD, ERROR_DATA_NOT_FOUND, ERROR_DATA_FOUND

def create_injection_machine(user: User, **kwargs):
    """创建注塑机"""
    # TODO: 验证 user 操作权限
    if "device_no" not in kwargs or kwargs["device_no"] == "":
        raise BizException(ERROR_REQUIRED_FIELD, "设备编号必须存在， 且不能为空")
    if InjectionMoldingMachine.objects.filter(device_no=kwargs["device_no"], company=user.company).exists():
        raise BizException(ERROR_DATA_FOUND, f'设备编号 {kwargs["device_no"]} 已存在，请勿重复添加！')

    # 创建注塑机信息
    with transaction.atomic():
        kwargs = {
            "company_id": user.company_id,
            "organization_id": user.organization_id,
            **kwargs
        }
        injection_machine = InjectionMoldingMachine.create_with_check(**kwargs)
        # 创建注射单元信息
        for injection_unit_kwargs in kwargs.get("injection_units", []):
            if "id" in injection_unit_kwargs: injection_unit_kwargs.pop("id")
            InjectionUnit.create_with_check(machine=injection_machine, **injection_unit_kwargs)
    

def _get_injection_machine(injection_machine_id: int) -> InjectionMoldingMachine:
    """获取注塑机对象"""
    injection_machine_id = validate_pk(injection_machine_id, "注塑机ID")
    injection_machine = InjectionMoldingMachine.objects.filter(
        pk=injection_machine_id
    ).select_related("time_standard").prefetch_related(
        "injection_units"
    ).first()
    if not injection_machine:
        raise BizException(ERROR_DATA_NOT_FOUND, "注塑机不存在")  # TODO: 添加自定义错误码
    return injection_machine
    

def get_injection_machine_info(user: User, injection_machine_id: int) -> dict:
    """获取注塑机信息"""
    # TODO: 验证 user 操作权限
    
    injection_machine = _get_injection_machine(injection_machine_id)
    ret_dict = injection_machine.to_dict()
    ret_dict["injection_units"] = [
        injection_unit.to_dict() for injection_unit in injection_machine.injection_units.all()
    ]
    if hasattr(injection_machine, "time_standard") and injection_machine.time_standard:
        ret_dict["time_standard"] = injection_machine.time_standard.to_dict()
    else:
        ret_dict["time_standard"] = None
    return ret_dict


def update_injection_machine(user: User, injection_machine_id: int, **kwargs) -> dict:
    """更新注塑机信息"""
    # TODO: 验证 user 操作权限
    
    injection_machine = _get_injection_machine(injection_machine_id)
    
    if "device_no" not in kwargs or kwargs["device_no"] == "":
        raise BizException(ERROR_REQUIRED_FIELD, "设备编号必须存在， 且不能为空")
    if InjectionMoldingMachine.objects.filter(device_no=kwargs["device_no"], company=user.company).exclude(pk=injection_machine_id).exists():
        raise BizException(ERROR_DATA_FOUND, f'设备编号 {kwargs["device_no"]} 已存在，请勿重复添加！')
    with transaction.atomic():
        injection_machine.update_info(**kwargs)
        # 删除不存在的注射单元信息
        for injection_unit in injection_machine.injection_units.all():
            if not any(injection_unit_kwargs.get("id") == injection_unit.id for injection_unit_kwargs in kwargs["injection_units"]):
                injection_unit.delete()
        # 添加/更新注射单元信息
        for injection_unit_kwargs in kwargs.get("injection_units", []):
            if "id" in injection_unit_kwargs and injection_unit_kwargs["id"] is not None:
                injection_unit = InjectionUnit.objects.filter(pk=injection_unit_kwargs["id"]).first()
                injection_unit.update_info(machine=injection_machine, **injection_unit_kwargs)
            else:
                InjectionUnit.create_with_check(machine=injection_machine, **injection_unit_kwargs)


def delete_injection_machine(user: User, injection_machine_id: int) -> None:
    """删除注塑机"""
    # TODO: 验证 user 操作权限
    
    injection_machine = _get_injection_machine(injection_machine_id)
    injection_machine.soft_delete()
    

def get_injection_machine_list(
    user: User, 
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
) -> dict:
    """获取注塑机列表"""

    # TODO: 验证 user 操作权限

    company_id = user.company_id
    # 构建查询参数
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
        
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict(include_rvs=True) for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, results


def batch_delete_injection_machine(user: User, ids: list) -> None:
    """批量删除注塑机"""
    # TODO: 验证 user 操作权限
    ids = validate_id_list(ids)
    InjectionMoldingMachine.batch_soft_delete(ids)