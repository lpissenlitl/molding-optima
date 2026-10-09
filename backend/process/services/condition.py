"""
工艺条件服务（condition service）

业务核心实体：ProcessCondition（工艺条件）
附属子资源：ProcessParameter（工艺参数 / 调机轮次）

应用场景（按 view_type 区分）：
- view_type='parameter'    工艺参数视图：每条只取最新 parameter
- view_type='optimization' 工艺优化视图：每条取所有 parameters_count + 调机历史
- view_type='all'          完整视图（detail / list 都返回所有字段）

业务动作：
- preview_optimization(condition_id, target_defect)  工艺优化预览（不落库）

设计原则：
- condition 是核心实体，所有 CRUD 都通过 condition
- parameter 是子资源，必须依附 condition
- 业务上 condition 一旦创建不轻易变更，变更 = 新建 condition
- condition 内容允许重复（同样 mold+polymer+machine 可有多个 condition，标识不同试模事件）

合并来源（2026-10-09）：
- record.py（CRUD 子集）
- parameter.py（CRUD 完整 + frontend 转换 + 列表）
- parameter_transformer.py（frontend 字段转换）
- optimization_advice.py（optimization CRUD + chain 调度）
"""
import logging
from datetime import datetime, date, time
from typing import Dict, Any, Optional, List, Tuple

from django.db import transaction
from django.db.models import Q, Count

from extensions.exceptions import (
    BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT,
    ERROR_OPERATION_FAILED, ERROR_REQUIRED_FIELD,
)
from process.models import ProcessCondition, ProcessParameter, RuleMethod
from masterdata.models import Mold, InjectionMoldingMachine, Polymer
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset
from utils.objects import safe_get
from utils.code_generator import generate_unique_code
from process.services.tuning import TuningService

_logger = logging.getLogger(__name__)


# ============================================================================
# 模块级工具：frontend 字段转换
# （合并自 parameter_transformer.py）
# ============================================================================

def _frontend_to_condition_dict(setting_process: dict) -> dict:
    """前端嵌套结构 setting_process → DB 扁平字段

    Args:
        setting_process: 前端嵌套结构

    Returns:
        dict: 扁平化的字段字典，可直接用于创建/更新工艺参数
    """
    flat = {}

    # --- 注射参数 ---
    injection = setting_process.get("injection", {})
    table_data = injection.get("table_data", [])
    if len(table_data) >= 3:
        flat["inj_pres_1"] = table_data[0]["sections"][0]
        flat["inj_pres_2"] = table_data[0]["sections"][1]
        flat["inj_pres_3"] = table_data[0]["sections"][2]
        flat["inj_pres_4"] = table_data[0]["sections"][3]
        flat["inj_pres_5"] = table_data[0]["sections"][4]
        flat["inj_pres_6"] = table_data[0]["sections"][5]
        flat["inj_spd_1"] = table_data[1]["sections"][0]
        flat["inj_spd_2"] = table_data[1]["sections"][1]
        flat["inj_spd_3"] = table_data[1]["sections"][2]
        flat["inj_spd_4"] = table_data[1]["sections"][3]
        flat["inj_spd_5"] = table_data[1]["sections"][4]
        flat["inj_spd_6"] = table_data[1]["sections"][5]
        flat["inj_pos_1"] = table_data[2]["sections"][0]
        flat["inj_pos_2"] = table_data[2]["sections"][1]
        flat["inj_pos_3"] = table_data[2]["sections"][2]
        flat["inj_pos_4"] = table_data[2]["sections"][3]
        flat["inj_pos_5"] = table_data[2]["sections"][4]
        flat["inj_pos_6"] = table_data[2]["sections"][5]
    flat["inj_t"] = injection.get("injection_time")
    flat["inj_dly_t"] = injection.get("delay_time")
    flat["cool_t"] = injection.get("cooling_time")

    # --- VP 切换 ---
    vp_switch = setting_process.get("vp_switch", {})
    flat["vps_mode"] = vp_switch.get("mode")
    flat["vps_pos"] = vp_switch.get("position")
    flat["vps_t"] = vp_switch.get("time")
    flat["vps_pres"] = vp_switch.get("pressure")
    flat["vps_spd"] = vp_switch.get("velocity")

    # --- 保压参数 ---
    holding = setting_process.get("holding", {})
    table_data = holding.get("table_data", [])
    if len(table_data) >= 3:
        flat["hold_pres_1"] = table_data[0]["sections"][0]
        flat["hold_pres_2"] = table_data[0]["sections"][1]
        flat["hold_pres_3"] = table_data[0]["sections"][2]
        flat["hold_pres_4"] = table_data[0]["sections"][3]
        flat["hold_pres_5"] = table_data[0]["sections"][4]
        flat["hold_spd_1"] = table_data[1]["sections"][0]
        flat["hold_spd_2"] = table_data[1]["sections"][1]
        flat["hold_spd_3"] = table_data[1]["sections"][2]
        flat["hold_spd_4"] = table_data[1]["sections"][3]
        flat["hold_spd_5"] = table_data[1]["sections"][4]
        flat["hold_t_1"] = table_data[2]["sections"][0]
        flat["hold_t_2"] = table_data[2]["sections"][1]
        flat["hold_t_3"] = table_data[2]["sections"][2]
        flat["hold_t_4"] = table_data[2]["sections"][3]
        flat["hold_t_5"] = table_data[2]["sections"][4]

    # --- 熔胶参数 ---
    metering = setting_process.get("metering", {})
    table_data = metering.get("table_data", [])
    if len(table_data) >= 4:
        flat["met_pres_1"] = table_data[0]["sections"][0]
        flat["met_pres_2"] = table_data[0]["sections"][1]
        flat["met_pres_3"] = table_data[0]["sections"][2]
        flat["met_pres_4"] = table_data[0]["sections"][3]
        flat["met_rot_spd_1"] = table_data[1]["sections"][0]
        flat["met_rot_spd_2"] = table_data[1]["sections"][1]
        flat["met_rot_spd_3"] = table_data[1]["sections"][2]
        flat["met_rot_spd_4"] = table_data[1]["sections"][3]
        flat["met_back_pres_1"] = table_data[2]["sections"][0]
        flat["met_back_pres_2"] = table_data[2]["sections"][1]
        flat["met_back_pres_3"] = table_data[2]["sections"][2]
        flat["met_back_pres_4"] = table_data[2]["sections"][3]
        flat["met_pos_1"] = table_data[3]["sections"][0]
        flat["met_pos_2"] = table_data[3]["sections"][1]
        flat["met_pos_3"] = table_data[3]["sections"][2]
        flat["met_pos_4"] = table_data[3]["sections"][3]
    decompress_table = metering.get("decompress_table_data", [])
    if len(decompress_table) >= 2:
        flat["pre_met_decomp_pres"] = decompress_table[0].get("pressure")
        flat["pre_met_decomp_spd"] = decompress_table[0].get("velocity")
        flat["pre_met_decomp_t"] = decompress_table[0].get("time")
        flat["pre_met_decomp_dist"] = decompress_table[0].get("distance")
        flat["pst_met_decomp_pres"] = decompress_table[1].get("pressure")
        flat["pst_met_decomp_spd"] = decompress_table[1].get("velocity")
        flat["pst_met_decomp_t"] = decompress_table[1].get("time")
        flat["pst_met_decomp_dist"] = decompress_table[1].get("distance")
    flat["met_lim_t"] = metering.get("delay_time")
    flat["met_end_pos"] = metering.get("ending_position")

    # --- 料筒温度 ---
    barrel_temp = setting_process.get("barrel_temperature", {})
    table_data = barrel_temp.get("table_data", [])
    if len(table_data) >= 1:
        sections = table_data[0]["sections"]
        if len(sections) >= 10:
            flat["noz_temp"] = sections[0]
            flat["brl_temp_1"] = sections[1]
            flat["brl_temp_2"] = sections[2]
            flat["brl_temp_3"] = sections[3]
            flat["brl_temp_4"] = sections[4]
            flat["brl_temp_5"] = sections[5]
            flat["brl_temp_6"] = sections[6]
            flat["brl_temp_7"] = sections[7]
            flat["brl_temp_8"] = sections[8]
            flat["brl_temp_9"] = sections[9]

    return flat


def _condition_to_frontend_payload(parameter, injection_unit=None) -> dict:
    """DB 扁平字段 → 前端嵌套结构 setting_process

    Args:
        parameter: ProcessParameter 模型实例
        injection_unit: 注射单元（用于获取单位系统）

    Returns:
        dict: 前端嵌套结构的 setting_process
    """
    # 获取单位系统
    if injection_unit:
        pressure_unit = injection_unit.pressure_unit or "MPa"
        speed_unit = injection_unit.speed_unit or "mm/s"
        screw_rotation_unit = injection_unit.screw_rotation_unit or "rpm"
        back_pressure_unit = injection_unit.back_pressure_unit or "MPa"
        temperature_unit = injection_unit.temperature_unit or "℃"
    else:
        pressure_unit = "MPa"
        speed_unit = "mm/s"
        screw_rotation_unit = "rpm"
        back_pressure_unit = "MPa"
        temperature_unit = "℃"

    return {
        "injection": {
            "stage": parameter.inj_stg or 1,
            "max_stage": 6,
            "table_data": [
                {
                    "label": "压力",
                    "unit": pressure_unit,
                    "sections": [
                        parameter.inj_pres_1, parameter.inj_pres_2,
                        parameter.inj_pres_3, parameter.inj_pres_4,
                        parameter.inj_pres_5, parameter.inj_pres_6,
                    ],
                },
                {
                    "label": "速度",
                    "unit": speed_unit,
                    "sections": [
                        parameter.inj_spd_1, parameter.inj_spd_2,
                        parameter.inj_spd_3, parameter.inj_spd_4,
                        parameter.inj_spd_5, parameter.inj_spd_6,
                    ],
                },
                {
                    "label": "位置",
                    "unit": "mm",
                    "sections": [
                        parameter.inj_pos_1, parameter.inj_pos_2,
                        parameter.inj_pos_3, parameter.inj_pos_4,
                        parameter.inj_pos_5, parameter.inj_pos_6,
                    ],
                },
            ],
            "injection_time": parameter.inj_t,
            "delay_time": parameter.inj_dly_t,
            "cooling_time": parameter.cool_t,
        },
        "vp_switch": {
            "mode": parameter.vps_mode or 0,
            "position": parameter.vps_pos,
            "time": parameter.vps_t,
            "pressure": parameter.vps_pres,
            "velocity": parameter.vps_spd,
        },
        "holding": {
            "stage": parameter.hold_stg or 1,
            "max_stage": 5,
            "table_data": [
                {
                    "label": "压力",
                    "unit": pressure_unit,
                    "sections": [
                        parameter.hold_pres_1, parameter.hold_pres_2,
                        parameter.hold_pres_3, parameter.hold_pres_4,
                        parameter.hold_pres_5,
                    ],
                },
                {
                    "label": "速度",
                    "unit": speed_unit,
                    "sections": [
                        parameter.hold_spd_1, parameter.hold_spd_2,
                        parameter.hold_spd_3, parameter.hold_spd_4,
                        parameter.hold_spd_5,
                    ],
                },
                {
                    "label": "时间",
                    "unit": "s",
                    "sections": [
                        parameter.hold_t_1, parameter.hold_t_2,
                        parameter.hold_t_3, parameter.hold_t_4,
                        parameter.hold_t_5,
                    ],
                },
            ],
        },
        "metering": {
            "stage": parameter.met_stg or 1,
            "max_stage": 4,
            "table_data": [
                {
                    "label": "压力",
                    "unit": pressure_unit,
                    "sections": [
                        parameter.met_pres_1, parameter.met_pres_2,
                        parameter.met_pres_3, parameter.met_pres_4,
                    ],
                },
                {
                    "label": "螺杆转速",
                    "unit": screw_rotation_unit,
                    "sections": [
                        parameter.met_rot_spd_1, parameter.met_rot_spd_2,
                        parameter.met_rot_spd_3, parameter.met_rot_spd_4,
                    ],
                },
                {
                    "label": "背压",
                    "unit": back_pressure_unit,
                    "sections": [
                        parameter.met_back_pres_1, parameter.met_back_pres_2,
                        parameter.met_back_pres_3, parameter.met_back_pres_4,
                    ],
                },
                {
                    "label": "位置",
                    "unit": "mm",
                    "sections": [
                        parameter.met_pos_1, parameter.met_pos_2,
                        parameter.met_pos_3, parameter.met_pos_4,
                    ],
                },
            ],
            "pre_decompress_mode": parameter.pre_met_decomp_mode or 0,
            "post_decompress_mode": parameter.pst_met_decomp_mode or 0,
            "decompress_table_data": [
                {
                    "label": "储前",
                    "pressure": parameter.pre_met_decomp_pres,
                    "velocity": parameter.pre_met_decomp_spd,
                    "time": parameter.pre_met_decomp_t,
                    "distance": parameter.pre_met_decomp_dist,
                },
                {
                    "label": "储后",
                    "pressure": parameter.pst_met_decomp_pres,
                    "velocity": parameter.pst_met_decomp_spd,
                    "time": parameter.pst_met_decomp_t,
                    "distance": parameter.pst_met_decomp_dist,
                },
            ],
            "delay_time": parameter.met_lim_t,
            "ending_position": parameter.met_end_pos,
        },
        "barrel_temperature": {
            "stage": parameter.brl_temp_stg or 5,
            "max_stage": 10,
            "table_data": [
                {
                    "label": "温度",
                    "unit": temperature_unit,
                    "sections": [
                        parameter.noz_temp,
                        parameter.brl_temp_1, parameter.brl_temp_2,
                        parameter.brl_temp_3, parameter.brl_temp_4,
                        parameter.brl_temp_5, parameter.brl_temp_6,
                        parameter.brl_temp_7, parameter.brl_temp_8,
                        parameter.brl_temp_9,
                    ],
                },
            ],
        },
    }


# ============================================================================
# 私有工具：创建 condition + 内部查询
# ============================================================================

def _create_process_condition(company_id: int, organization_id: int, **kwargs):
    """创建 ProcessCondition（含 process_context_snapshot 构建）

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
            },
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
            "IP": {"HMI_unit": injection_unit.pressure_unit, "HMI_max": injection_unit.max_set_injection_pressure,
                    "std_unit": "MPa", "std_max": injection_unit.max_injection_pressure},
            "IV": {"HMI_unit": injection_unit.speed_unit, "HMI_max": injection_unit.max_set_injection_speed,
                    "std_unit": "mm/s", "std_max": injection_unit.max_injection_speed},
            "PP": {"HMI_unit": injection_unit.pressure_unit, "HMI_max": injection_unit.max_set_holding_pressure,
                    "std_unit": "MPa", "std_max": injection_unit.max_holding_pressure},
            "PV": {"HMI_unit": injection_unit.speed_unit, "HMI_max": injection_unit.max_set_holding_speed,
                    "std_unit": "MPa", "std_max": injection_unit.max_holding_speed},
            "MP": {"HMI_unit": injection_unit.pressure_unit, "HMI_max": injection_unit.max_set_metering_back_pressure,
                    "std_unit": "MPa", "std_max": injection_unit.max_metering_back_pressure},
            "MSR": {"HMI_unit": injection_unit.screw_rotation_unit, "HMI_max": injection_unit.max_set_screw_rotation_speed,
                     "std_unit": "rpm", "std_max": injection_unit.max_screw_rotation_speed},
            "MBP": {"HMI_unit": injection_unit.back_pressure_unit, "HMI_max": injection_unit.max_set_metering_back_pressure,
                     "std_unit": "MPa", "std_max": injection_unit.max_metering_back_pressure},
            "DP": {"HMI_unit": injection_unit.pressure_unit, "HMI_max": injection_unit.max_set_decompression_pressure,
                    "std_unit": "MPa", "std_max": injection_unit.max_decompression_pressure},
            "DV": {"HMI_unit": injection_unit.speed_unit, "HMI_max": injection_unit.max_set_decompression_speed,
                    "std_unit": "mm/s", "std_max": injection_unit.max_decompression_speed},
        },
    }

    # === 前端传入的上下文覆盖值（业务可调）===
    process_context = kwargs.pop("process_context", None) or {}

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


def _get_process_condition_by_id(condition_id: int) -> ProcessCondition:
    """获取 ProcessCondition ORM 对象（私有）"""
    condition_id = validate_pk(condition_id, "工艺条件ID")
    condition = ProcessCondition.objects.filter(
        id=condition_id
    ).prefetch_related(
        "process_parameters", "mold__gating_systems", "injection_machine__injection_units",
    ).select_related(
        "mold", "injection_machine", "polymer"
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, "工艺条件不存在")
    return condition


# ============================================================================
# CRUD 基础服务
# ============================================================================

@transaction.atomic
def create_condition(company_id: int, organization_id: int, **kwargs):
    """创建工艺条件 + 第一条工艺参数

    Args:
        kwargs:
            - condition: dict 工艺条件字段
            - parameter: dict 工艺参数字段（DB 扁平格式）
            - 或 setting_process: dict 工艺参数字段（前端嵌套格式）—— 通过 parameter_nested 传入

    Returns:
        dict: condition 详情（含 parameter）
    """
    condition_kwargs = kwargs.get("condition")
    parameter_kwargs = kwargs.get("parameter")
    parameter_nested = kwargs.get("parameter_nested", {})

    if not condition_kwargs:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺条件信息存在")
    if not parameter_kwargs and not parameter_nested.get("setting_process"):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺参数信息存在")

    # frontend 嵌套格式 → flat
    if not parameter_kwargs and parameter_nested.get("setting_process"):
        parameter_kwargs = _frontend_to_condition_dict(parameter_nested["setting_process"])

    condition = _create_process_condition(company_id, organization_id, **condition_kwargs)
    parameter_kwargs.update({
        "company_id": company_id,
        "organization_id": organization_id,
        "process_condition_id": condition.id,
        "param_code": generate_unique_code("PPARA"),
        "param_source": "unknown",
    })
    ProcessParameter.create_with_check(**parameter_kwargs)
    return get_condition(condition.id, view_type="parameter")


@transaction.atomic
def update_condition(condition_id: int, **kwargs):
    """更新工艺条件 + 工艺参数

    Args:
        kwargs:
            - condition: dict 要更新的 condition 字段
            - parameter: dict 要更新的 parameter 字段（DB 扁平格式）
    """
    condition = _get_process_condition_by_id(condition_id)

    if "condition" in kwargs:
        condition.update_info(**kwargs.get("condition"))

    if "parameter" in kwargs:
        parameter = condition.process_parameters.first()
        if parameter:
            parameter.update_info(**kwargs.get("parameter"))

    return get_condition(condition_id, view_type="parameter")


@transaction.atomic
def update_condition_frontend(condition_id: int, **kwargs):
    """更新工艺条件 + 工艺参数（前端嵌套结构格式）"""
    condition = _get_process_condition_by_id(condition_id)

    if "condition" in kwargs:
        condition.update_info(**kwargs.get("condition"))

    if "parameter" in kwargs:
        parameter_nested = kwargs.get("parameter", {})
        setting_process = parameter_nested.get("setting_process")
        if setting_process:
            parameter_kwargs = _frontend_to_condition_dict(setting_process)
            parameter = condition.process_parameters.first()
            if parameter:
                parameter.update_info(**parameter_kwargs)

    return get_condition_frontend(condition_id)


@transaction.atomic
def delete_condition(condition_id: int):
    """软删工艺条件（级联软删 parameter）"""
    condition = _get_process_condition_by_id(condition_id)
    condition.soft_delete()


@transaction.atomic
def batch_delete_condition(ids: list):
    """批量软删工艺条件"""
    ids = validate_id_list(ids, "工艺条件ID列表")
    return ProcessCondition.batch_soft_delete(ids)


# ============================================================================
# 详情 / 列表查询
# ============================================================================

def get_condition(condition_id: int, view_type: str = "parameter") -> dict:
    """获取工艺条件详情

    Args:
        condition_id: 工艺条件 ID
        view_type:
            - 'parameter'    返回 condition + 关联 parameter（取最新）
            - 'optimization' 返回 condition + parameters_count
            - 'all'          返回 condition + 所有 parameters 详情
    """
    condition = _get_process_condition_by_id(condition_id)

    if view_type == "optimization":
        return {
            "condition_id": condition_id,
            "status": condition.status,
            "origin_type": condition.origin_type,
            "process_context_snapshot": condition.process_context_snapshot,
            "parameters_count": condition.process_parameters.count(),
        }

    if view_type == "all":
        return {
            **condition.to_dict(include_rvs=True),
            "mold_info": condition.mold.to_dict(include_rvs=True),
            "machine_info": condition.injection_machine.to_dict(include_rvs=True),
            "polymer_info": condition.polymer.to_dict(include_rvs=True),
            "parameters": [p.to_dict() for p in condition.process_parameters.all()],
        }

    # default: 'parameter'
    ret_dict = condition.to_dict(include_rvs=True)
    ret_dict.update({
        "mold_info": condition.mold.to_dict(include_rvs=True),
        "machine_info": condition.injection_machine.to_dict(include_rvs=True),
        "polymer_info": condition.polymer.to_dict(include_rvs=True),
    })
    return ret_dict


def get_condition_frontend(condition_id: int) -> dict:
    """获取工艺条件详情（前端嵌套结构格式）

    用于"移植（Transplant）"页和"参数表单（ProcessParameterForm）"加载前端结构。
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
            "setting_process": _condition_to_frontend_payload(parameter, injection_unit),
        },
    }


def get_condition_list(
    view_type: str = "parameter",
    company_id: int = None,
    status: str = None,
    origin_type: str = None,
    mold_no: str = None,
    machine_model: str = None,
    polymer_abbreviation: str = None,
    start_date: date = None,
    end_date: date = None,
    sort: str = None,
    page_no: int = None,
    page_size: int = None,
) -> Tuple[int, List[dict]]:
    """获取工艺条件列表（按 view_type 区分应用场景）

    Args:
        view_type:
            - 'parameter'    工艺参数视图：每条 condition + 最新 parameter
            - 'optimization' 工艺优化视图：每条 condition + parameters_count
        company_id, status, origin_type, ...   过滤条件
    """
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
    ).annotate(
        parameters_count=Count("process_parameters"),
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

    # 构造结果（按 view_type 区分返回字段）
    results = []
    for item in pagination["items"]:
        result = {
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
            "parameters_count": item.parameters_count,
        }
        if view_type == "parameter":
            # 工艺参数模式：附加最新一条 parameter
            latest = item.process_parameters.order_by("-sequence_index").first()
            if latest:
                result["parameter"] = latest.to_dict()
        results.append(result)

    return pagination["total_count"], results


# ============================================================================
# 工艺优化相关查询
# ============================================================================

def get_condition_with_history(condition_id: int) -> dict:
    """获取工艺条件详情（含调机轮次）

    业务：工艺优化页加载时使用，展示 condition + 关联的 parameter 数量。
    """
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, "该工艺条件不存在")

    parameters = ProcessParameter.objects.filter(
        process_condition_id=condition_id,
        is_deleted=False,
    ).order_by("sequence_index")

    return {
        "condition_id": condition_id,
        "status": condition.status,
        "origin_type": condition.origin_type,
        "process_context_snapshot": condition.process_context_snapshot,
        "parameters_count": parameters.count(),
    }


def get_condition_history(condition_id: int) -> List[dict]:
    """获取某工艺的调机历史（按 created_at 倒序）"""
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    history = ProcessParameter.objects.filter(
        process_condition_id=condition_id,
        is_deleted=False,
    ).order_by("-created_at")
    return [h.to_dict() for h in history]


@transaction.atomic
def update_condition_info(condition_id: int, **params):
    """更新工艺条件字段（不涉及 parameter）

    注：业务上 condition 一旦创建不轻易变更；如需调整建议新建 condition。
    """
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, "该工艺条件不存在")
    condition.update_info(**params)
    return condition.to_dict()


# ============================================================================
# 业务动作：工艺优化预览（不落库）
# （合并自 optimization_advice.add_process_optimization + chain 调度）
# ============================================================================

# 中文缺陷名 → 英文 defect_code 译文表（与 RuleMethod.defect_code 对齐）
DEFECT_NAME_MAP = {
    "短射": "SHORTSHOT",
    "缩水": "SINK_MARK",
    "飞边": "FLASH",
    "熔接痕": "WELD_LINE",
    "困气": "TRAP",
    "气纹": "FLOW_MARK",
    "烧焦": "BURN",
    "料花": "FLOW_LINE",
    "色差": "COLOR_SHIFT",
    "水波纹": "RIPPLE",
    "脱模不良": "EJECT_DIFFICULT",
    "顶白": "WHITENING",
    "变形": "WARPAGE",
    "尺寸偏大": "OVERSIZE",
    "尺寸偏小": "UNDERSIZE",
    "浇口印": "GATE_MARK",
    "阴阳面": "BRIGHT_DARK",
}

# 工艺参数字段白名单（仅数值型字段，避免非数值字段进入 FuzzyEngine）
PROCESS_PARAM_FIELDS = (
    [f'inj_spd_{i}' for i in range(1, 7)]
    + [f'inj_pres_{i}' for i in range(1, 7)]
    + [f'inj_pos_{i}' for i in range(1, 7)]
    + ['inj_t', 'inj_dly_t']
    + ['vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd']
    + [f'hold_pres_{i}' for i in range(1, 6)]
    + [f'hold_spd_{i}' for i in range(1, 6)]
    + [f'hold_t_{i}' for i in range(1, 6)]
    + ['cool_t']
    + [f'met_pres_{i}' for i in range(1, 5)]
    + [f'met_rot_spd_{i}' for i in range(1, 5)]
    + [f'met_back_pres_{i}' for i in range(1, 5)]
    + [f'met_pos_{i}' for i in range(1, 5)]
    + ['pre_met_decomp_pres', 'pre_met_decomp_spd', 'pre_met_decomp_t', 'pre_met_decomp_dist']
    + ['pst_met_decomp_pres', 'pst_met_decomp_spd', 'pst_met_decomp_t', 'pst_met_decomp_dist']
    + ['met_lim_t', 'met_end_pos']
    + ['noz_temp'] + [f'brl_temp_{i}' for i in range(1, 10)]
)


def _translate_defect_name(chinese_name: str) -> str:
    """中文缺陷名 → 英文 defect_code（供 FuzzyEngine 查询 RuleMethod）"""
    if not chinese_name:
        return ""
    if chinese_name in DEFECT_NAME_MAP:
        return DEFECT_NAME_MAP[chinese_name]
    return chinese_name


def _extract_process_parameters(current_params: list) -> dict:
    """从 ProcessParameter 列表提取数值型工艺参数（chain 输入）"""
    snapshot = {}
    if not current_params:
        return snapshot
    first_param = current_params[0]
    for field_name in PROCESS_PARAM_FIELDS:
        value = getattr(first_param, field_name, None)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            snapshot[field_name] = float(value)
    return snapshot


def _build_optimization_context(
    condition: ProcessCondition,
    current_params: list,
    target_defect: str,
) -> dict:
    """构造 chain 调度所需的 context"""
    defect_name_en = _translate_defect_name(target_defect) if target_defect else ""
    parameter_snapshot = _extract_process_parameters(current_params)

    trend_dict = {"trend": "unknown"}
    try:
        first_param = current_params[0] if current_params else None
        if first_param:
            trend = TuningService.analyze_iteration_trend(first_param)
            trend_dict = {
                "trend": trend.trend,
                "improving_count": trend.improving,
                "worsening_count": trend.worsening,
                "unchanged_count": trend.unchanged,
                "last_result": trend.last_result,
            }
    except Exception as e:  # noqa: BLE001
        _logger.warning("[condition] iteration_trend 分析失败: %s", e)

    overrides = {}
    snapshot = getattr(condition, "process_context_snapshot", None) or {}
    if isinstance(snapshot, dict):
        overrides = snapshot.get("overrides", {}) or {}

    return {
        "defect_name": defect_name_en,
        "feedback": {
            "defect": [
                {
                    "defect_name": defect_name_en,
                    "defect_name_zh": target_defect,
                }
            ] if defect_name_en else [],
        },
        "process_parameter": parameter_snapshot,
        "iteration_trend": trend_dict,
        "polymer_abbreviation": overrides.get("polymer_abbreviation"),
        "product_category": overrides.get("product_category"),
        "rule_library_code": overrides.get("rule_library_code"),
    }


def _infer_direction(current_value, recommended_value) -> str:
    """根据当前值与推荐值推断调整方向"""
    if current_value is None or recommended_value is None:
        return "adjust"
    if recommended_value > current_value:
        return "increase"
    if recommended_value < current_value:
        return "decrease"
    return "adjust"


def _recommendations_to_adjustments(recommendations: list, context: dict) -> List[dict]:
    """Recommendation 列表 → 旧版 adjustments 格式（保持 API 兼容）"""
    parameter_snapshot = context.get("process_parameter") or {}
    adjustments: List[dict] = []
    for rec in recommendations:
        current_val = parameter_snapshot.get(rec.param_name)
        adjustments.append({
            "param": rec.param_name,
            "direction": _infer_direction(current_val, rec.recommended_value),
            "current_value": current_val,
            "recommended_value": rec.recommended_value,
            "confidence": rec.confidence,
            "reason": rec.reason,
            "source": rec.source or "engine",
        })
    return adjustments


def _run_optimization_chain(context: dict) -> Tuple[List[dict], str]:
    """运行优化 chain

    调度顺序：
      1. 取出 AlgorithmRegistry 中 algorithm_type='optimization' 的算法
         （按 priority 排序：fuzzy → llm）
      2. chain 调用，第一个返回非空推荐的引擎胜出
      3. 主 chain 全部失败 → empirical 兜底
      4. empirical 也不可用 → 抛 BizException(OPERATION_FAILED)
    """
    from process.algorithms.base import AlgorithmRegistry

    candidates = AlgorithmRegistry.get_algorithms_by_type("optimization")
    if not candidates:
        raise BizException(
            ERROR_OPERATION_FAILED,
            "无任何优化算法注册",
        )

    # 分离 empirical 兜底（写死最后一步）
    primary_chain = [a for a in candidates if a.algorithm_subtype != "empirical"]
    empirical = AlgorithmRegistry.get_algorithm("empirical")

    # 主 chain 调度
    for algorithm in primary_chain:
        if not algorithm.is_available(context):
            _logger.info(
                "[chain] %s 不可用, 跳过 (defect=%s)",
                algorithm.algorithm_subtype, context.get("defect_name"),
            )
            continue
        try:
            recommendations = algorithm.recommend(context)
        except Exception as e:  # noqa: BLE001
            _logger.warning(
                "[chain] %s 推理异常: %s", algorithm.algorithm_subtype, e, exc_info=True,
            )
            continue
        if recommendations:
            adjustments = _recommendations_to_adjustments(recommendations, context)
            _logger.info(
                "[chain] %s 返回 %d 条推荐 (defect=%s)",
                algorithm.algorithm_subtype, len(adjustments), context.get("defect_name"),
            )
            return adjustments, algorithm.algorithm_subtype
        _logger.info(
            "[chain] %s 未返回推荐 (defect=%s)",
            algorithm.algorithm_subtype, context.get("defect_name"),
        )

    # 经验推理兜底
    if empirical and empirical.is_available(context):
        try:
            recommendations = empirical.recommend(context)
        except Exception as e:  # noqa: BLE001
            _logger.warning("[chain] empirical 推理异常: %s", e, exc_info=True)
            recommendations = None
        if recommendations:
            adjustments = _recommendations_to_adjustments(recommendations, context)
            _logger.info(
                "[chain] empirical 返回 %d 条推荐 (defect=%s)",
                len(adjustments), context.get("defect_name"),
            )
            return adjustments, "empirical"

    raise BizException(
        ERROR_OPERATION_FAILED,
        f"所有优化算法均无可用推荐 (defect={context.get('defect_name')})",
    )


def preview_optimization(
    condition_id: int,
    target_defect: str = None,
) -> dict:
    """工艺优化预览（不落库，仅返回建议）

    Args:
        condition_id: 工艺条件 ID
        target_defect: 目标缺陷名（中文）

    Returns:
        {
            'condition_id': ...,
            'target_defect': ...,
            'matched_rules': [...],
            'adjustments': [...],
            'source': 'fuzzy' | 'llm' | 'empirical'
        }

    Raises:
        BizException(OPERATION_FAILED): 整个 chain 都无可用推荐

    注：与 parameter_optimize.optimize 的区别 —— preview_optimization 不落库，
        仅返回建议。落库的完整 infer 走 parameter_optimize service。
    """
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    # 1. 获取当前工艺参数
    parameters = ProcessParameter.objects.filter(
        process_condition_id=condition_id,
        is_deleted=False,
    ).order_by("sequence_index")
    current_params = list(parameters)

    # 2. 匹配规则（库内已有规则信息，用于返回展示）
    matched_rules = []
    if target_defect:
        rules = RuleMethod.objects.filter(
            defect_label=target_defect,
            is_active=True,
            is_deleted=False,
        ).order_by("-priority")
        for rule in rules:
            matched_rules.append({
                "id": rule.id,
                "rule_description": rule.rule_description,
                "defect_label": rule.defect_label,
                "priority": rule.priority,
            })

    # 3. 构造 context
    context = _build_optimization_context(condition, current_params, target_defect)

    # 4. chain 调度
    adjustments, source = _run_optimization_chain(context)

    return {
        "condition_id": condition_id,
        "target_defect": target_defect,
        "matched_rules": matched_rules,
        "adjustments": adjustments,
        "source": source,
    }
