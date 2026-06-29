from django.db import transaction
from django.db.models import Q
from identity.models import User
from process.models import ProcessCondition, ProcessParameter
from masterdata.models import Mold, GatingSystem, InjectionMoldingMachine, InjectionUnit, Polymer
from extensions.exceptions import ERROR_ILLEGAL_ARGUMENT, BizException, ERROR_DATA_NOT_FOUND, ERROR_REQUIRED_FIELD
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset 
from utils.object_utils import safe_get
from datetime import timedelta, datetime, date, time
from utils.code_generator import generate_unique_code


def _create_process_condition(user: User, **kwargs):
    """创建工艺条件"""

    # --- 参数校验 ---
    if "mold_id" not in kwargs or not kwargs["mold_id"]:
        raise BizException(ERROR_REQUIRED_FIELD, "模具信息必须存在， 且不能为空")
    if "injection_machine_id" not in kwargs or not kwargs["injection_machine_id"]:
        raise BizException(ERROR_REQUIRED_FIELD, "注塑机信息必须存在， 且不能为空")
    if "polymer_id" not in kwargs or not kwargs["polymer_id"]:
        raise BizException(ERROR_REQUIRED_FIELD, "材料信息必须存在， 且不能为空")
    
    # --- 构建工艺条件快照 ---
    try:
        mold = Mold.objects.prefetch_related("gating_systems").get(id=kwargs["mold_id"])
        gating_systems = mold.gating_systems.all()
        print("gating_systems:", gating_systems)
        machine = InjectionMoldingMachine.objects.prefetch_related("injection_units").get(id=kwargs["injection_machine_id"])
        injection_units = machine.injection_units.all()
        print("injection_units:", injection_units)
        polymer = Polymer.objects.get(id=kwargs["polymer_id"])

        # 获取浇注系统信息
        gating_system: GatingSystem = None
        shot_index = kwargs["shot_index"] if "shot_index" in kwargs else 0
        if gating_systems.count() == 1:  # 浇注系统数量为 1
            gating_system = gating_systems.first()
        elif gating_system.count() > 1 and shot_index < gating_systems.count():  # 浇注系统数量 > 1 且 shot_index 存在
            gating_system = gating_systems[shot_index]
        else:
            raise BizException(ERROR_DATA_NOT_FOUND, "无效注射次序索引")
        
        # 获取注射单元信息
        injection_unit: InjectionUnit = None
        injection_index = kwargs["injection_index"] if "injection_index" in kwargs else 0
        if injection_units.count() == 1:  # 注塑机单元数量为 1
            injection_unit = machine.injection_units.first()
        elif injection_units.count() > 1 and injection_index < injection_units.count():  # 注塑机单元数量 > 1
            injection_unit = injection_units[kwargs["injection_index"]]
        else:
            raise BizException(ERROR_DATA_NOT_FOUND, "无效注射单元索引")
        
        process_context_snapshot = {
            "version": "1.0",
            "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mold": {
                "mold_no": mold.mold_no,
                "mold_name": mold.mold_name,
                "mold_type": mold.mold_type,
                "cavity_layout": mold.cavity_layout,
                "shot_index": shot_index,
                "gating_system": {
                    "runner_type": gating_system.runner_type,
                }
            },
            "machine": {
                "brand": machine.brand,
                "model": machine.model,
                "device_no": machine.device_no,
                "machine_type": machine.machine_type,
                "drive_system": machine.drive_system,
                "unit_count": machine.unit_count,
                "injection_index": injection_index,
                "injection_unit": {
                    "screw_diameter": injection_unit.screw_diameter,
                },
            },
            "polymer": {
                "abbreviation": polymer.abbreviation,
                "grade": polymer.grade,
                "macnufacturer": polymer.manufacturer,
            },
            "hmi_to_std_mapping": {
                "IP": {
                    "HMI_unit": injection_unit.pressure_unit,
                    "HMI_max": injection_unit.max_set_injection_pressure,
                    "std_unit": "MPa",
                    "std_max": injection_unit.max_injection_pressure,
                },
                "IV": {
                    "HMI_unit": injection_unit.speed_unit,
                    "HMI_max": injection_unit.max_set_injection_speed,
                    "std_unit": "mm/s",
                    "std_max": injection_unit.max_injection_speed,
                },
                "PP": {
                    "HMI_unit": injection_unit.pressure_unit,
                    "HMI_max": injection_unit.max_set_holding_pressure,
                    "std_unit": "MPa",
                    "std_max": injection_unit.max_holding_pressure,
                },
                "PV": { 
                    "HMI_unit": injection_unit.speed_unit,
                    "HMI_max": injection_unit.max_set_holding_speed,
                    "std_unit": "MPa",
                    "std_max": injection_unit.max_holding_speed ,
                },
                "MP": {
                    "HMI_unit": injection_unit.pressure_unit,
                    "HMI_max": injection_unit.max_set_metering_back_pressure,
                    "std_unit": "MPa",
                    "std_max": injection_unit.max_metering_back_pressure,
                },
                "MSR": {
                    "HMI_unit": injection_unit.screw_rotation_unit,
                    "HMI_max": injection_unit.max_set_screw_rotation_speed,
                    "std_unit": "rpm",
                    "std_max": injection_unit.max_screw_rotation_speed,
                },
                "MBP": {
                    "HMI_unit": injection_unit.back_pressure_unit,
                    "HMI_max": injection_unit.max_set_metering_back_pressure,
                    "std_unit": "MPa",
                    "std_max": injection_unit.max_metering_back_pressure,  
                },
                "DP": {
                    "HMI_unit": injection_unit.pressure_unit,
                    "HMI_max": injection_unit.max_set_decompression_pressure,
                    "std_unit": "MPa",
                    "std_max": injection_unit.max_decompression_pressure,
                },
                "DV": { 
                    "HMI_unit": injection_unit.speed_unit,
                    "HMI_max": injection_unit.max_set_decompression_speed,
                    "std_unit": "mm/s",
                    "std_max": injection_unit.max_decompression_speed,
                },
            }
        }
        
        kwargs = {
            **kwargs,
            "company_id": user.company_id,
            "organization_id": user.organization_id,
            "injection_unit_id": injection_unit.id,
            "status": "draft",
            "condition_code": generate_unique_code("PCOND"),
            "origin_type": "manual_creation",
            "process_context_snapshot": process_context_snapshot,
        }
        return ProcessCondition.create_with_check(**kwargs)
        
    except Exception as e:  # noqa
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"参数错误{e}")


def create_process_parameter(user: User, **kwargs):
    """创建工艺参数"""

    if "condition" not in kwargs:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺条件信息存在")
    if "parameter" not in kwargs:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺参数信息存在")
    
    condition = _create_process_condition(user, **kwargs.get("condition"))
    parameter = kwargs.get("parameter")
    parameter_kwargs = {
        **parameter,
        "company_id": user.company_id,
        "organization_id": user.organization_id,
        "process_condition_id": condition.id,
        "paramter_code": generate_unique_code("PPARA"),
        "prameter_source": "unknown"
    }
    parameter = ProcessParameter.create_with_check(**parameter_kwargs)    
    return parameter.to_dict()


def _get_process_condition_by_id(condition_id: int) -> ProcessCondition:
    """获取工艺条件对象"""
    condition_id = validate_pk(condition_id, "工艺条件ID")
    condition = ProcessCondition.objects.filter(
        id=condition_id
    ).prefetch_related(
        "process_parameters", "mold__gating_systems", "injection_machine__injection_units",
    ).select_related(
        "mold", "injection_machine", "polymer"
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, "工艺初始化不存在")
    return condition


def _construct_return_parameter(condition: ProcessCondition):
    """构造返回工艺参数记录"""
    ret_dict = condition.to_dict(include_rvs=True)
    ret_dict.update({
        "mold_info": condition.mold.to_dict(include_rvs=True),
        "machine_info": condition.injection_machine.to_dict(include_rvs=True),
        "polymer_info": condition.polymer.to_dict(include_rvs=True),
    })
    
    return ret_dict


def get_process_parameter(user: User, condition_id: int):
    """获取工艺参数"""
    condition = _get_process_condition_by_id(condition_id)

    return _construct_return_parameter(condition)


def update_process_parameter(user: User, condition_id: int, **kwargs):
    """更新工艺参数"""
    condition = _get_process_condition_by_id(condition_id)

    if "condition" in kwargs:
        condition.update_info(**kwargs.get("condition"))

    if "parameter" in kwargs:
        parameter = condition.process_parameters.first()
        parameter_kwargs = kwargs.get("parameter")
        parameter.update_info(**parameter_kwargs)

    return _construct_return_parameter(condition)

def delete_process_parameter(user: User, condition_id: int):
    """删除工艺参数"""
    condition = _get_process_condition_by_id(condition_id)
    condition.delete()


def get_process_parameter_list(
    user: User,
    status: str = None,
    origin_type: str = None,
    mold_no: str = None,
    machine_model: str = None,
    polymer_abbreviation: str = None,
    start_date: date = None,
    end_date: date = None,
    sort: str = None,
    page_no: int = None,
    page_size: int = None
):
    """获取工艺参数列表"""

    # 构建查询参数
    filter_map = {
        "company_id": {"input": user.company_id, "column": "company_id", "lookup": "exact"},
        "status": {"input": status, "column": "status", "lookup": "exact"},
        "origin_type": {"input": origin_type, "column": "origin_type", "lookup": "icontains"},
        "mold_no": {"input": mold_no, "column": "mold__mold_no", "lookup": "icontains"},
        "machine_model": {"input": machine_model, "column": "injection_machine__model", "lookup": "icontains"},
        "polymer_abbreviation": {"input": polymer_abbreviation, "column": "polymer__abbrivation", "lookup": "icontains"},
    }
    filter = build_filters(filter_map)
    qs = ProcessCondition.objects.filter(
        **filter
    ).select_related(
        "mold", "injection_machine", "polymer"
    ).prefetch_related(
        "process_parameters"
    )
    
    # 单独处理日期范围：created_at 在 [start_date, end_date] 之间
    if start_date is not None or end_date is not None:
        date_filters = Q()
        if start_date is not None:
            date_filters &= Q(created_at__gte=datetime.combine(start_date, time.min))
        if end_date is not None:
            date_filters &= Q(created_at__lte=datetime.combine(end_date, time.max))
        qs = qs.filter(date_filters)
    
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)

    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [{
        **item.to_dict(),
        "mold_no": safe_get(item,"mold.mold_no"),
        "mold_name": safe_get(item, "mold.mold_name"),
        "mold_type": safe_get(item, "mold.mold_type"),
        "cavity_layout": safe_get(item, "mold.cavity_layout"),
        "product_category": safe_get(item, "mold.product_category"),
        "machine_brand": safe_get(item, "injection_machine.brand"),
        "machine_model": safe_get(item, "injection_machine.model"),
        "machine_device_code": safe_get(item, "injection_machine.device_no"),
        "polymer_abbreviation": safe_get(item, "polymer.abbreviation"),
        "polymer_grade": safe_get(item, "polymer.grade"),
    } for item in pagination["items"] ]
    total = pagination["total_count"]

    return total, results

def batch_delete_process_parameter(ids: list):
    """批量删除工艺参数记录"""
    ids = validate_id_list(ids, "工艺参数ID列表")
    return ProcessCondition.batch_soft_delete(ids)