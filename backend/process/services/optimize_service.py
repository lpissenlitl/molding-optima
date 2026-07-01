"""
molding-optima 工艺优化 service

阶段 1 实现：基于规则的工艺优化。
阶段 2 将补充：基于 process_context_snapshot 的精细化算法。
"""
import logging

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND
from process.models import ProcessCondition, ProcessParameter, RuleMethod

_logger = logging.getLogger(__name__)


# 优化目标：缺陷类型与建议的目标参数
DEFECT_OPTIMIZATION_HINTS = {
    "短射": {"increase": ["inj_pres_1", "inj_spd_1", "inj_t"], "decrease": []},
    "缩水": {"increase": ["hold_pres_1", "hold_t_1", "cool_t"], "decrease": []},
    "飞边": {"increase": [], "decrease": ["inj_pres_1", "inj_spd_1"]},
    "熔接痕": {"increase": ["brl_temp_1", "brl_temp_2", "brl_temp_3", "inj_spd_1"], "decrease": []},
    "困气": {"increase": ["vps_pos"], "decrease": ["inj_spd_1"]},
    "气纹": {"increase": ["cool_t", "brl_temp_1"], "decrease": ["inj_spd_1"]},
    "烧焦": {"increase": [], "decrease": ["inj_spd_1", "brl_temp_1", "brl_temp_2"]},
    "料花": {"increase": ["brl_temp_1", "brl_temp_2"], "decrease": ["inj_spd_1"]},
    "色差": {"increase": ["brl_temp_1", "brl_temp_2", "brl_temp_3"], "decrease": []},
    "水波纹": {"increase": ["brl_temp_1", "cool_t"], "decrease": []},
    "脱模不良": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    "顶白": {"increase": [], "decrease": ["hold_pres_1", "hold_spd_1"]},
    "变形": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    "尺寸偏大": {"increase": [], "decrease": ["hold_pres_1", "hold_t_1"]},
    "尺寸偏小": {"increase": ["hold_pres_1", "hold_t_1"], "decrease": []},
    "浇口印": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    "阴阳面": {"increase": ["brl_temp_1", "brl_temp_2", "inj_spd_1"], "decrease": []},
}


def get_process_optimization(condition_id):
    """获取工艺优化详情（基于 ProcessCondition）"""
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, "该工艺优化记录不存在")

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


def add_process_optimization(
    company_id: int,
    organization_id: int,
    condition_id: int,
    target_defect: str = None,
) -> dict:
    """
    添加工艺优化任务（基于规则匹配）。

    阶段 1：返回规则匹配结果，不实际写新记录。
    阶段 2：将基于 process_context_snapshot 写优化建议到字段中。
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

    # 2. 匹配规则
    matched_rules = []
    if target_defect:
        rules = RuleMethod.objects.filter(
            defect_name=target_defect,
            enable=1,
            is_deleted=False,
        ).order_by("-priority")
        for rule in rules:
            matched_rules.append({
                "id": rule.id,
                "rule_type": rule.rule_type,
                "rule_description": rule.rule_description,
                "defect_name": rule.defect_name,
                "priority": rule.priority,
            })

    # 3. 给出参数调整建议
    adjustments = []
    if target_defect and target_defect in DEFECT_OPTIMIZATION_HINTS:
        hint = DEFECT_OPTIMIZATION_HINTS[target_defect]
        for param_code in hint["increase"]:
            current_val = _get_param_value(current_params, param_code)
            adjustments.append({
                "param": param_code,
                "direction": "increase",
                "current_value": current_val,
                "suggestion": f"调高 {param_code}",
            })
        for param_code in hint["decrease"]:
            current_val = _get_param_value(current_params, param_code)
            adjustments.append({
                "param": param_code,
                "direction": "decrease",
                "current_value": current_val,
                "suggestion": f"调低 {param_code}",
            })

    return {
        "condition_id": condition_id,
        "target_defect": target_defect,
        "matched_rules": matched_rules,
        "adjustments": adjustments,
    }


def update_process_optimization(condition_id: int, **params):
    """更新工艺条件（实际就是更新 ProcessCondition）"""
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, "该工艺优化记录不存在")
    condition.update_info(**params)
    return condition.to_dict()


def get_optimization_history(condition_id):
    """
    获取某工艺的优化历史。
    阶段 2 完善：process_context_snapshot.data_sources 标记。
    """
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    # 占位实现：返回当前条件的所有参数
    history = ProcessParameter.objects.filter(
        process_condition_id=condition_id,
        is_deleted=False,
    ).order_by("-created_at")
    return [h.to_dict() for h in history]


def _get_param_value(parameters, param_code):
    """从参数列表中获取指定参数的值（取第一段）"""
    if not parameters:
        return None
    first_param = parameters[0]
    return getattr(first_param, param_code, None)