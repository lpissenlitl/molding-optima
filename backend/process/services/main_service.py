"""
molding-optima 工艺基础服务

从 molding-expert 同步对齐，去除陈旧的 injection_unit_id 字段，
改用 injection_machine + injection_index 业务规则推导。
"""
import logging
from datetime import datetime, date, time

from django.db.models import Q

from process.models import ProcessCondition, ProcessParameter
from masterdata.models import Mold, GatingSystem, InjectionMoldingMachine, Polymer
from extensions.exceptions import ERROR_ILLEGAL_ARGUMENT, BizException, ERROR_DATA_NOT_FOUND, ERROR_REQUIRED_FIELD
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset
from utils.objects import safe_get
from utils.code_generator import generate_unique_code
from process.services.process_transformer import _transform_frontend_to_flat, _construct_setting_process_frontend

logger = logging.getLogger(__name__)


# ============================================================
# 辅助函数
# ============================================================

def _create_process_condition(company_id: int, organization_id: int, **kwargs):
    """
    创建工艺条件

    与 molding-expert 差异：
      - 不再保存 injection_unit_id 字段（molding-optima 模型中无此字段）
      - 注射单元通过 injection_machine + injection_index 业务规则推导
    """
    mold_id = kwargs.get("mold_id")
    injection_machine_id = kwargs.get("injection_machine_id")
    polymer_id = kwargs.get("polymer_id")

    if not mold_id:
        raise BizException(ERROR_REQUIRED_FIELD, "模具信息必须存在，且不能为空")
    if not injection_machine_id:
        raise BizException(ERROR_REQUIRED_FIELD, "注塑机信息必须存在，且不能为空")
    if not polymer_id:
        raise BizException(ERROR_REQUIRED_FIELD, "材料信息必须存在，且不能为空")

    mold = Mold.objects.prefetch_related("gating_systems").get(id=mold_id)
    gating_systems = mold.gating_systems.all()
    machine = InjectionMoldingMachine.objects.prefetch_related("injection_units").get(id=injection_machine_id)
    injection_units = machine.injection_units.all()
    polymer = Polymer.objects.get(id=polymer_id)

    # 获取浇注系统信息
    shot_index = kwargs.get("shot_index", 0)
    if gating_systems.count() == 1:
        gating_system = gating_systems.first()
    elif gating_systems.count() > 1 and shot_index < gating_systems.count():
        gating_system = gating_systems[shot_index]
    else:
        raise BizException(ERROR_DATA_NOT_FOUND, "无效注射次序索引")

    # 获取注射单元信息（业务规则：injection_machine + injection_index → InjectionUnit）
    injection_index = kwargs.get("injection_index", 0)
    if injection_units.count() == 1:
        injection_unit = machine.injection_units.first()
    elif injection_units.count() > 1 and injection_index < injection_units.count():
        injection_unit = injection_units[injection_index]
    else:
        raise BizException(ERROR_DATA_NOT_FOUND, "无效注射单元索引")

    # === 后端自动生成的不可变快照（创建时锁定）===
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
            "manufacturer": polymer.manufacturer,
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
                "std_max": injection_unit.max_holding_speed,
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

    # === 前端传入的上下文覆盖值（业务可调）===
    # 优先使用调用方传入的 process_context（前端可控）
    # 未传则为空 dict，后续算法层可从 snapshot 提取默认值
    process_context = kwargs.pop("process_context", None) or {}

    # molding-optima 适配：
    # - 删除 injection_unit_id 字段（模型中无此字段）
    # - 多租户用 company_id / organization_id（BusinessBaseModel FK 的 _id 后缀）
    kwargs.update({
        "company_id": company_id,
        "organization_id": organization_id,
        "status": "draft",
        "condition_no": generate_unique_code("PCOND"),
        "origin_type": "manual_creation",
        "process_context": process_context,
        "process_context_snapshot": process_context_snapshot,
    })
    return ProcessCondition.create_with_check(**kwargs)


# ============================================================
# 创建 / 查询 / 更新 / 删除
# ============================================================

def create_process_parameter(company_id: int, organization_id: int, **kwargs):
    """创建工艺参数"""
    condition_kwargs = kwargs.get("condition")
    parameter_kwargs = kwargs.get("parameter")

    if not condition_kwargs:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺条件信息存在")
    if not parameter_kwargs:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺参数信息存在")

    condition = _create_process_condition(company_id, organization_id, **condition_kwargs)
    parameter_kwargs.update({
        "company_id": company_id,
        "organization_id": organization_id,
        "process_condition_id": condition.id,
        "param_code": generate_unique_code("PPARA"),
        "param_source": "unknown",
    })
    parameter = ProcessParameter.create_with_check(**parameter_kwargs)
    return parameter.to_dict()


def create_process_parameter_frontend(company_id: int, organization_id: int, **kwargs):
    """
    创建工艺参数 (前端嵌套结构格式)
    """
    condition_kwargs = kwargs.get("condition")
    parameter_nested = kwargs.get("parameter", {})
    setting_process = parameter_nested.get("setting_process")

    if not condition_kwargs:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺条件信息存在")
    if not setting_process:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺参数信息存在")

    # 转换前端嵌套结构为扁平格式
    parameter_kwargs = _transform_frontend_to_flat(setting_process)

    condition = _create_process_condition(company_id, organization_id, **condition_kwargs)
    parameter_kwargs.update({
        "company_id": company_id,
        "organization_id": organization_id,
        "process_condition_id": condition.id,
        "param_code": generate_unique_code("PPARA"),
        "param_source": "unknown",
    })
    parameter = ProcessParameter.create_with_check(**parameter_kwargs)

    # 返回前端格式
    return get_process_parameter_frontend(condition.id)


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


def get_process_parameter(condition_id: int):
    """获取工艺参数"""
    condition = _get_process_condition_by_id(condition_id)
    return _construct_return_parameter(condition)


def get_process_parameter_flat(condition_id: int):
    """
    获取工艺参数记录 (扁平化格式)
    """
    condition = _get_process_condition_by_id(condition_id)
    parameter = condition.process_parameters.first()
    if not parameter:
        raise BizException(ERROR_DATA_NOT_FOUND, "工艺参数不存在")

    return parameter.to_dict()


def get_process_parameter_frontend(condition_id: int):
    """
    获取工艺参数记录 (前端适配格式 - 嵌套结构)

    molding-optima 适配：
      - 通过 injection_machine + injection_index 推导注射单元
    """
    condition = _get_process_condition_by_id(condition_id)
    parameter = condition.process_parameters.first()
    if not parameter:
        raise BizException(ERROR_DATA_NOT_FOUND, "工艺参数不存在")

    # 推导注射单元（业务规则：injection_machine + injection_index）
    injection_unit = None
    if condition.injection_machine and condition.injection_index is not None:
        units = condition.injection_machine.injection_units.all()
        idx = condition.injection_index or 0
        if 0 <= idx < units.count():
            injection_unit = units[idx]

    return {
        "condition": {
            "id": condition.id,
            "mold_info": condition.mold.to_dict(include_rvs=True),
            "shot_index": condition.shot_index,
            "gating_system": (condition.process_context_snapshot or {}).get("mold", {}).get("gating_system"),
            "machine_info": condition.injection_machine.to_dict(include_rvs=True),
            "injection_index": condition.injection_index,
            "injection_unit": injection_unit.to_dict() if injection_unit else None,
            "polymer_info": condition.polymer.to_dict(include_rvs=True),
        },
        "parameter": {
            "setting_process": _construct_setting_process_frontend(parameter, injection_unit)
        }
    }


def update_process_parameter(condition_id: int, **kwargs):
    """更新工艺参数"""
    condition = _get_process_condition_by_id(condition_id)

    if "condition" in kwargs:
        condition.update_info(**kwargs.get("condition"))

    if "parameter" in kwargs:
        parameter = condition.process_parameters.first()
        parameter.update_info(**kwargs.get("parameter"))

    return _construct_return_parameter(condition)


def update_process_parameter_frontend(condition_id: int, **kwargs):
    """
    更新工艺参数 (前端嵌套结构格式)
    """
    condition = _get_process_condition_by_id(condition_id)

    if "condition" in kwargs:
        condition.update_info(**kwargs.get("condition"))

    if "parameter" in kwargs:
        parameter_nested = kwargs.get("parameter", {})
        setting_process = parameter_nested.get("setting_process")
        if setting_process:
            parameter_kwargs = _transform_frontend_to_flat(setting_process)
            parameter = condition.process_parameters.first()
            parameter.update_info(**parameter_kwargs)

    return get_process_parameter_frontend(condition_id)


def delete_process_parameter(condition_id: int):
    """删除工艺参数"""
    condition = _get_process_condition_by_id(condition_id)
    condition.soft_delete()


# ============================================================
# 列表查询
# ============================================================

def get_process_parameter_list(
    company_id: int,
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
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "status": {"input": status, "column": "status", "lookup": "exact"},
        "origin_type": {"input": origin_type, "column": "origin_type", "lookup": "icontains"},
        "mold_no": {"input": mold_no, "column": "mold__mold_no", "lookup": "icontains"},
        "machine_model": {"input": machine_model, "column": "injection_machine__model", "lookup": "icontains"},
        "polymer_abbreviation": {"input": polymer_abbreviation, "column": "polymer__abbreviation", "lookup": "icontains"},
    }
    filter_kwargs = build_filters(filter_map)
    qs = ProcessCondition.objects.filter(
        **filter_kwargs
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

    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)

    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [{
        **item.to_dict(),
        "mold_no": safe_get(item, "mold.mold_no"),
        "mold_name": safe_get(item, "mold.mold_name"),
        "mold_type": safe_get(item, "mold.mold_type"),
        "cavity_layout": safe_get(item, "mold.cavity_layout"),
        "product_category": safe_get(item, "mold.product_category"),
        "machine_brand": safe_get(item, "injection_machine.brand"),
        "machine_model": safe_get(item, "injection_machine.model"),
        "machine_device_code": safe_get(item, "injection_machine.device_no"),
        "polymer_abbreviation": safe_get(item, "polymer.abbreviation"),
        "polymer_grade": safe_get(item, "polymer.grade"),
    } for item in pagination["items"]]
    return pagination["total_count"], results


# ============================================================
# 批量操作
# ============================================================

def batch_delete_process_parameter(ids: list):
    """批量删除工艺参数记录"""
    ids = validate_id_list(ids, "工艺参数ID列表")
    return ProcessCondition.batch_soft_delete(ids)
