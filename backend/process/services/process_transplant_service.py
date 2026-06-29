"""
molding-optima 工艺参数移植 service

根据原注塑机和目标注塑机的规格，按比例缩放工艺参数。

阶段 1：基础算法实现
阶段 2：从 old/mdprocess 提炼更复杂的移植算法（机器自适应、多轴联动等）

注：spec 来源字段（screw_diameter 等）目前从 process_context_snapshot 中读取，
    snapshot 格式待定，阶段 2 完善。
"""
import copy

from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT
from process.models import ProcessParameter


PI = 3.1415926


def _ratio(origin_value, o_max_actual, o_max_set, t_max_actual, t_max_set):
    """
    按比例缩放：
        new = old * (origin_actual * target_set) / (origin_set * target_actual)
    """
    if not origin_value:
        return origin_value
    if o_max_actual is None or o_max_set is None or t_max_actual is None or t_max_set is None:
        return origin_value
    if o_max_set == 0 or t_max_actual == 0:
        return origin_value
    return origin_value * (o_max_actual * t_max_set) / (o_max_set * t_max_actual)


def _position_ratio(origin_value, o_diameter, t_diameter):
    """位置缩放：按螺杆截面积比"""
    if not origin_value or o_diameter is None or t_diameter is None or t_diameter == 0:
        return origin_value
    o_area = PI * (o_diameter ** 2) / 4
    t_area = PI * (t_diameter ** 2) / 4
    return origin_value * (o_area / t_area)


def transplant_process_parameter(
    source_parameter_id: int,
    target_machine_spec: dict,
) -> dict:
    """
    将 source_parameter 的工艺参数按 target_machine_spec 缩放。

    Args:
        source_parameter_id: 源工艺参数 ID
        target_machine_spec: 目标注塑机规格，需包含：
            - screw_diameter
            - max_injection_pressure, max_set_injection_pressure
            - max_injection_velocity, max_set_injection_velocity
            - max_holding_pressure, max_set_holding_pressure
            - max_holding_velocity, max_set_holding_velocity
            - max_metering_pressure, max_set_metering_pressure
            - max_screw_rotation_speed, max_set_screw_rotation_speed
            - max_metering_back_pressure, max_set_metering_back_pressure
            - max_decompression_pressure, max_set_decompression_pressure
            - max_decompression_velocity, max_set_decompression_velocity
    """
    if target_machine_spec.get("screw_diameter") is None:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "目标注塑机规格缺少 screw_diameter")

    t_d = target_machine_spec["screw_diameter"]

    # 占位：阶段 1 不做实际移植计算，等待 snapshot 格式确定后接入
    return {
        "source_parameter_id": source_parameter_id,
        "target_machine_spec": target_machine_spec,
        "message": "工艺移植算法待 process_context_snapshot 格式确定后实现",
    }


def get_process_no_list(company_id=None, mold_id=None, status="approved"):
    """获取已批准的工艺条件列表（用于移植下拉）"""
    from process.models import ProcessCondition

    qs = ProcessCondition.objects.filter(
        is_deleted=False,
    )
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
    from process.models import ProcessParameter as PP

    # 占位实现：返回迁移接口说明
    return {
        "source_process_id": process_id,
        "source_process_no": None,
        "target_machine": {"trademark": mac_trademark, "serial_no": mac_serial_no},
        "message": "请使用 transplant_process_parameter 实施完整移植",
    }