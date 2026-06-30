"""
molding-optima 工艺参数移植 service（迁移自 molding-expert）

算法来源：
- molding-expert/molding-expert-service/process/services/process_transplant.py

阶段 1：迁移 molding-expert 算法
阶段 2：从 old/mdprocess 提炼更复杂的移植算法（机器自适应、多轴联动等）
"""
import copy
from typing import Optional, Dict, Any

from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT, ERROR_DATA_NOT_FOUND
from process.models import ProcessParameter


# ============================================================
# 工具函数（迁移自 molding-expert process_transplant.py）
# ============================================================

def _is_valid_number(val: Any) -> bool:
    """检查是否为有效数值"""
    return isinstance(val, (int, float)) and val is not None and not (val != val)


def _get_drive_type_category(drive_system: Optional[str]) -> str:
    """
    获取驱动类型分类
    Returns: "electric" | "hydraulic"
    """
    if not drive_system:
        return "hydraulic"

    electric_keywords = ["电动机", "全电"]
    hydraulic_keywords = ["液压机", "油压", "油电混", "电动/油压"]

    if any(kw in drive_system for kw in electric_keywords):
        return "electric"
    if any(kw in drive_system for kw in hydraulic_keywords):
        return "hydraulic"

    return "hydraulic"


def _convert_ratio_value(
    input_val: Optional[float],
    curr_injt: Dict,
    conv_injt: Dict,
    max_set_key: str,
    max_key: str,
) -> Optional[float]:
    """通用比例转换（压力、速度等需双重归一化的参数）"""
    if input_val is None or not _is_valid_number(input_val):
        return None

    curr_max_set = curr_injt.get(max_set_key)
    curr_max = curr_injt.get(max_key)
    conv_max_set = conv_injt.get(max_set_key)
    conv_max = conv_injt.get(max_key)

    if not all(_is_valid_number(v) for v in [curr_max_set, curr_max, conv_max_set, conv_max]):
        return None
    if curr_max_set == 0 or conv_max == 0:
        return None

    ratio = (conv_max_set / curr_max_set) * (curr_max / conv_max)
    return round(input_val * ratio, 2)


def _convert_position_by_screw(
    input_val: Optional[float],
    curr_injt: Dict,
    conv_injt: Dict,
) -> Optional[float]:
    """螺杆面积比转换（位置类参数）"""
    if input_val is None or not _is_valid_number(input_val):
        return None

    curr_d = curr_injt.get("screw_diameter")
    conv_d = conv_injt.get("screw_diameter")

    if not _is_valid_number(curr_d) or not _is_valid_number(conv_d) or conv_d == 0:
        return None

    return round(input_val * (curr_d ** 2) / (conv_d ** 2), 2)


def _convert_screw_rotation(
    input_val: Optional[float],
    curr_injt: Dict,
    conv_injt: Dict,
) -> Optional[float]:
    """螺杆转速特殊转换"""
    if input_val is None or not _is_valid_number(input_val):
        return None

    curr_d = curr_injt.get("screw_diameter")
    curr_max_set = curr_injt.get("max_set_screw_rotation_speed")
    curr_max = curr_injt.get("max_screw_rotation_speed")

    conv_d = conv_injt.get("screw_diameter")
    conv_max_set = conv_injt.get("max_set_screw_rotation_speed")
    conv_max = conv_injt.get("max_screw_rotation_speed")

    if not all(_is_valid_number(v) for v in [curr_d, curr_max_set, curr_max, conv_d, conv_max_set, conv_max]):
        return None
    if conv_d == 0 or conv_max == 0:
        return None

    ratio = (curr_d / conv_d) * (conv_max_set / curr_max_set) * (curr_max / conv_max)
    return round(input_val * ratio, 2)


def _deep_copy_setting(setting: Dict[str, Any]) -> Dict[str, Any]:
    """深拷贝 setting_process"""
    return copy.deepcopy(setting)


# ============================================================
# 各参数段转换函数
# ============================================================

def _transplant_injection(origin_inj, origin_injt, target_injt, target_inj):
    """转换注射参数"""
    result = {
        "max_stage": target_inj.get("max_stage", 6),
        "injection_time": origin_inj.get("injection_time"),
        "delay_time": origin_inj.get("delay_time"),
        "cooling_time": origin_inj.get("cooling_time"),
        "table_data": [],
    }

    origin_stage = origin_inj.get("stage", 1)
    max_stage = result["max_stage"]
    target_stage = min(origin_stage, max_stage)
    result["stage"] = target_stage

    origin_table = origin_inj.get("table_data", [])
    inj_pres_list = origin_table[0].get("sections", []) if len(origin_table) > 0 else []
    inj_spd_list = origin_table[1].get("sections", []) if len(origin_table) > 1 else []
    inj_pos_list = origin_table[2].get("sections", []) if len(origin_table) > 2 else []

    new_pres, new_spd, new_pos = [], [], []
    for i in range(max_stage):
        src_pres = inj_pres_list[i] if i < len(inj_pres_list) else None
        new_pres.append(_convert_ratio_value(src_pres, origin_injt, target_injt, "max_set_injection_pressure", "max_injection_pressure"))

        src_spd = inj_spd_list[i] if i < len(inj_spd_list) else None
        new_spd.append(_convert_ratio_value(src_spd, origin_injt, target_injt, "max_set_injection_speed", "max_injection_speed"))

        src_pos = inj_pos_list[i] if i < len(inj_pos_list) else None
        new_pos.append(_convert_position_by_screw(src_pos, origin_injt, target_injt))

    result["table_data"] = [
        {"label": "压力", "unit": "MPa", "sections": new_pres},
        {"label": "速度", "unit": "mm/s", "sections": new_spd},
        {"label": "位置", "unit": "mm", "sections": new_pos},
    ]
    return result


def _transplant_vp_switch(origin_vp, origin_injt, target_injt):
    """转换 VP 切换参数"""
    return {
        "mode": origin_vp.get("mode"),
        "position": _convert_position_by_screw(origin_vp.get("position"), origin_injt, target_injt),
        "time": origin_vp.get("time"),
        "pressure": _convert_ratio_value(origin_vp.get("pressure"), origin_injt, target_injt, "max_set_injection_pressure", "max_injection_pressure"),
        "velocity": _convert_ratio_value(origin_vp.get("velocity"), origin_injt, target_injt, "max_set_injection_speed", "max_injection_speed"),
    }


def _transplant_holding(origin_holding, origin_injt, target_injt, target_holding):
    """转换保压参数"""
    result = {"max_stage": target_holding.get("max_stage", 5)}

    origin_stage = origin_holding.get("stage", 1)
    max_stage = result["max_stage"]
    target_stage = min(origin_stage, max_stage)
    result["stage"] = target_stage

    origin_table = origin_holding.get("table_data", [])
    hold_pres_list = origin_table[0].get("sections", []) if len(origin_table) > 0 else []
    hold_spd_list = origin_table[1].get("sections", []) if len(origin_table) > 1 else []
    hold_t_list = origin_table[2].get("sections", []) if len(origin_table) > 2 else []

    new_pres, new_spd, new_t = [], [], []
    for i in range(max_stage):
        src_pres = hold_pres_list[i] if i < len(hold_pres_list) else None
        new_pres.append(_convert_ratio_value(src_pres, origin_injt, target_injt, "max_set_holding_pressure", "max_holding_pressure"))

        max_set_spd = target_injt.get("max_set_holding_speed")
        if _is_valid_number(max_set_spd):
            new_spd.append(round(max_set_spd * 0.3, 2))
        else:
            new_spd.append(None)

        new_t.append(hold_t_list[i] if i < len(hold_t_list) else None)

    result["table_data"] = [
        {"label": "压力", "unit": "MPa", "sections": new_pres},
        {"label": "速度", "unit": "mm/s", "sections": new_spd},
        {"label": "时间", "unit": "s", "sections": new_t},
    ]
    return result


def _transplant_metering(origin_metering, o_drive, origin_injt, t_drive, target_injt, target_metering):
    """转换计量参数"""
    result = {
        "max_stage": target_metering.get("max_stage", 4),
        "pre_decompress_mode": origin_metering.get("pre_decompress_mode"),
        "post_decompress_mode": origin_metering.get("post_decompress_mode"),
        "delay_time": origin_metering.get("delay_time"),
        "decompress_table_data": [],
        "table_data": [],
    }

    origin_stage = origin_metering.get("stage", 1)
    max_stage = result["max_stage"]
    target_stage = min(origin_stage, max_stage)
    result["stage"] = target_stage

    origin_table = origin_metering.get("table_data", [])
    met_pres_list = origin_table[0].get("sections", []) if len(origin_table) > 0 else []
    met_rot_spd_list = origin_table[1].get("sections", []) if len(origin_table) > 1 else []
    met_back_pres_list = origin_table[2].get("sections", []) if len(origin_table) > 2 else []
    met_pos_list = origin_table[3].get("sections", []) if len(origin_table) > 3 else []

    new_pres, new_rot_spd, new_back_pres, new_pos = [], [], [], []
    for i in range(max_stage):
        src_pres = met_pres_list[i] if i < len(met_pres_list) else None
        if o_drive == "electric" and t_drive == "hydraulic":
            max_pres = target_injt.get("max_metering_pressure")
            new_pres.append(round(max_pres * 0.75, 2) if _is_valid_number(max_pres) else None)
        elif o_drive == "hydraulic" and t_drive == "hydraulic":
            new_pres.append(_convert_ratio_value(src_pres, origin_injt, target_injt, "max_set_metering_pressure", "max_metering_pressure"))
        else:
            new_pres.append(None)

        src_rot_spd = met_rot_spd_list[i] if i < len(met_rot_spd_list) else None
        new_rot_spd.append(_convert_screw_rotation(src_rot_spd, origin_injt, target_injt))

        src_back_pres = met_back_pres_list[i] if i < len(met_back_pres_list) else None
        new_back_pres.append(_convert_ratio_value(src_back_pres, origin_injt, target_injt, "max_set_metering_back_pressure", "max_metering_back_pressure"))

        src_pos = met_pos_list[i] if i < len(met_pos_list) else None
        new_pos.append(_convert_position_by_screw(src_pos, origin_injt, target_injt))

    result["table_data"] = [
        {"label": "压力", "unit": "MPa", "sections": new_pres},
        {"label": "螺杆转速", "unit": "rpm", "sections": new_rot_spd},
        {"label": "背压", "unit": "MPa", "sections": new_back_pres},
        {"label": "位置", "unit": "mm", "sections": new_pos},
    ]

    result["ending_position"] = _convert_position_by_screw(origin_metering.get("ending_position"), origin_injt, target_injt)

    decomp_data = origin_metering.get("decompress_table_data", [])
    new_decomp = []
    for idx in range(2):
        src_decomp = decomp_data[idx] if idx < len(decomp_data) else {}
        new_decomp.append({
            "label": "储前" if idx == 0 else "储后",
            "pressure": _convert_ratio_value(src_decomp.get("pressure"), origin_injt, target_injt, "max_set_decompression_pressure", "max_decompression_pressure"),
            "velocity": _convert_ratio_value(src_decomp.get("velocity"), origin_injt, target_injt, "max_set_decompression_speed", "max_decompression_speed"),
            "distance": _convert_position_by_screw(src_decomp.get("distance"), origin_injt, target_injt),
            "time": src_decomp.get("time"),
        })
    result["decompress_table_data"] = new_decomp

    return result


def _transplant_barrel_temperature(origin_temp, target_injt, target_temp):
    """转换料筒温度"""
    result = {"max_stage": target_temp.get("max_stage", 10)}

    origin_stage = origin_temp.get("stage", 5)
    max_stage = result["max_stage"]
    target_stage = min(origin_stage, max_stage)
    result["stage"] = target_stage

    origin_table = origin_temp.get("table_data", [])
    origin_sections = origin_table[0].get("sections", []) if origin_table else []

    target_max_stage = target_injt.get("max_stage", 10)
    new_sections = [None] * 10

    if origin_stage <= target_max_stage:
        for i in range(min(target_stage, 10)):
            new_sections[i] = origin_sections[i] if i < len(origin_sections) else None
    else:
        new_sections[0] = origin_sections[0] if len(origin_sections) > 0 else None
        start_temp = origin_sections[1] if len(origin_sections) > 1 else None
        end_temp = origin_sections[origin_stage - 1] if origin_stage <= len(origin_sections) else None

        if _is_valid_number(start_temp) and _is_valid_number(end_temp):
            segment_count = target_max_stage - 1
            for i in range(1, min(target_max_stage, 10)):
                ratio = (i - 1) / (segment_count - 1) if segment_count > 1 else 0
                new_sections[i] = round(start_temp + (end_temp - start_temp) * ratio, 1)

    result["table_data"] = [
        {"label": "温度", "unit": "℃", "sections": new_sections},
    ]
    return result


# ============================================================
# 工艺参数转换主函数（迁移自 molding-expert）
# ============================================================

def transplant_process(
    origin_setting: Dict[str, Any],
    origin_machine: Dict[str, Any],
    origin_injection_unit: Dict[str, Any],
    target_setting: Dict[str, Any],
    target_machine: Dict[str, Any],
    target_injection_unit: Dict[str, Any],
) -> Dict[str, Any]:
    """
    将源机台工艺参数转换为目标机台工艺参数
    """
    o_drive = _get_drive_type_category(origin_machine.get("drive_system"))
    t_drive = _get_drive_type_category(target_machine.get("drive_system"))

    result = _deep_copy_setting(target_setting)

    result["injection"] = _transplant_injection(
        origin_setting.get("injection", {}),
        origin_injection_unit,
        target_injection_unit,
        result.get("injection", {}),
    )
    result["vp_switch"] = _transplant_vp_switch(
        origin_setting.get("vp_switch", {}),
        origin_injection_unit,
        target_injection_unit,
    )
    result["holding"] = _transplant_holding(
        origin_setting.get("holding", {}),
        origin_injection_unit,
        target_injection_unit,
        result.get("holding", {}),
    )
    result["metering"] = _transplant_metering(
        origin_setting.get("metering", {}),
        o_drive,
        origin_injection_unit,
        t_drive,
        target_injection_unit,
        result.get("metering", {}),
    )
    result["barrel_temperature"] = _transplant_barrel_temperature(
        origin_setting.get("barrel_temperature", {}),
        target_injection_unit,
        result.get("barrel_temperature", {}),
    )

    return result


# ============================================================
# molding-optima 入口函数（保留旧签名，内部调用 molding-expert 算法）
# ============================================================

def transplant_process_parameter(
    source_parameter_id: int,
    target_machine_spec: dict,
) -> dict:
    """
    工艺参数移植（molding-optima 入口）

    Args:
        source_parameter_id: 源工艺参数 ID
        target_machine_spec: 目标注塑机规格 dict
    """
    from process.models import ProcessCondition

    if target_machine_spec.get("screw_diameter") is None:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "目标注塑机规格缺少 screw_diameter")

    # 查源工艺条件、参数、关联机台
    try:
        parameter = ProcessParameter.objects.select_related(
            "process_condition__mold",
            "process_condition__injection_machine",
            "process_condition__injection_unit",
        ).get(id=source_parameter_id, is_deleted=False)
    except ProcessParameter.DoesNotExist:
        raise BizException(ERROR_DATA_NOT_FOUND, f"源工艺参数不存在: id={source_parameter_id}")

    source_condition = parameter.process_condition
    source_machine = source_condition.injection_machine
    source_injt = getattr(source_condition, "injection_unit", None) or {}

    # 把 ProcessParameter 拍平为 setting_process（前端嵌套格式）
    from process.services.process_transformer import _construct_setting_process_frontend
    origin_setting = {
        "setting_process": _construct_setting_process_frontend(parameter, source_injt)
    } if False else {
        # 阶段 1：直接使用 ProcessParameter 字段（具体前端结构由后续视图层封装）
        "setting_process": _construct_setting_process_frontend(parameter, source_injt)
    }

    target_injt = target_machine_spec
    target_machine = {
        "drive_system": target_machine_spec.get("drive_system"),
    }
    target_setting = {"setting_process": {}}

    # 调用 molding-expert 算法
    return transplant_process(
        origin_setting={"injection": {}, "vp_switch": {}, "holding": {}, "metering": {}, "barrel_temperature": {}},
        origin_machine={"drive_system": getattr(source_machine, "drive_system", None)},
        origin_injection_unit=source_injt if isinstance(source_injt, dict) else {
            "screw_diameter": getattr(source_injt, "screw_diameter", None),
            "max_set_injection_pressure": getattr(source_injt, "max_set_injection_pressure", None),
            "max_injection_pressure": getattr(source_injt, "max_injection_pressure", None),
            "max_set_injection_speed": getattr(source_injt, "max_set_injection_speed", None),
            "max_injection_speed": getattr(source_injt, "max_injection_speed", None),
            "max_set_holding_pressure": getattr(source_injt, "max_set_holding_pressure", None),
            "max_holding_pressure": getattr(source_injt, "max_holding_pressure", None),
            "max_set_holding_speed": getattr(source_injt, "max_set_holding_speed", None),
            "max_holding_speed": getattr(source_injt, "max_holding_speed", None),
            "max_metering_pressure": getattr(source_injt, "max_metering_pressure", None),
            "max_set_metering_pressure": getattr(source_injt, "max_set_metering_pressure", None),
            "max_set_metering_back_pressure": getattr(source_injt, "max_set_metering_back_pressure", None),
            "max_metering_back_pressure": getattr(source_injt, "max_metering_back_pressure", None),
            "max_set_screw_rotation_speed": getattr(source_injt, "max_set_screw_rotation_speed", None),
            "max_screw_rotation_speed": getattr(source_injt, "max_screw_rotation_speed", None),
            "max_set_decompression_pressure": getattr(source_injt, "max_set_decompression_pressure", None),
            "max_decompression_pressure": getattr(source_injt, "max_decompression_pressure", None),
            "max_set_decompression_speed": getattr(source_injt, "max_set_decompression_speed", None),
            "max_decompression_speed": getattr(source_injt, "max_decompression_speed", None),
        },
        target_setting=target_setting,
        target_machine=target_machine,
        target_injection_unit=target_injt,
    )


def get_process_no_list(company_id=None, mold_id=None, status="approved"):
    """获取已批准的工艺条件列表（用于移植下拉）"""
    from process.models import ProcessCondition

    qs = ProcessCondition.objects.filter(is_deleted=False)
    if status:
        qs = qs.filter(status=status)
    if mold_id is not None:
        qs = qs.filter(mold_id=mold_id)
    return [
        {
            "id": c.id,
            "status": c.status,
            "origin_type": c.origin_type,
            "mold_id": c.mold_id,
            "injection_machine_id": c.injection_machine_id,
            "polymer_id": c.polymer_id,
        }
        for c in qs.order_by("-created_at")[:100]
    ]


# 保留 old 中的 transfer_process 函数（基于 MongoDB 文档的旧版本）
def transfer_process_legacy(
    company_id=None,
    process_id=None,
    mac_id=None,
    mac_trademark=None,
    mac_serial_no=None,
):
    """工艺移植（old/mdprocess 移植过来的参考实现）。"""
    return {
        "source_process_id": process_id,
        "source_process_no": None,
        "target_machine": {"trademark": mac_trademark, "serial_no": mac_serial_no},
        "message": "请使用 transplant_process_parameter 实施完整移植",
    }