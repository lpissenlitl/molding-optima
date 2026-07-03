"""
molding-optima 工艺优化 service

阶段 1：基于 DEFECT_OPTIMIZATION_HINTS 硬编码字典（兜底）
阶段 2（当前）：优先调用 FuzzyEngine，无规则时回退到阶段 1 字典
阶段 3（规划）：基于 process_context_snapshot 写优化建议到字段中
"""
import logging

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND
from process.models import ProcessCondition, ProcessParameter, RuleMethod
from process.services.tuning_service import ProcessTuningService

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
    添加工艺优化任务。

    执行顺序：
      1. FuzzyEngine 推理（按 target_defect + 上下文 + iteration_trend）
      2. FuzzyEngine 无结果时 → 回退到 DEFECT_OPTIMIZATION_HINTS 硬编码字典
      3. 返回 adjustments（带 source 标记，便于前后端区分）

    阶段 3：将基于 process_context_snapshot 写优化建议到字段中。
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

    # 3. 优先调用 FuzzyEngine
    adjustments, source = _infer_via_fuzzy_engine(
        condition=condition,
        current_params=current_params,
        target_defect=target_defect,
    )

    # 4. FuzzyEngine 无结果 → 兑底到硬编码字典
    if not adjustments and target_defect and target_defect in DEFECT_OPTIMIZATION_HINTS:
        hint = DEFECT_OPTIMIZATION_HINTS[target_defect]
        for param_code in hint["increase"]:
            current_val = _get_param_value(current_params, param_code)
            adjustments.append({
                "param": param_code,
                "direction": "increase",
                "current_value": current_val,
                "suggestion": f"调高 {param_code}",
                "recommended_value": None,
                "confidence": None,
                "reason": "fallback_dict",
            })
        for param_code in hint["decrease"]:
            current_val = _get_param_value(current_params, param_code)
            adjustments.append({
                "param": param_code,
                "direction": "decrease",
                "current_value": current_val,
                "suggestion": f"调低 {param_code}",
                "recommended_value": None,
                "confidence": None,
                "reason": "fallback_dict",
            })
        source = "fallback_dict"

    return {
        "condition_id": condition_id,
        "target_defect": target_defect,
        "matched_rules": matched_rules,
        "adjustments": adjustments,
        "source": source,
    }


def _infer_via_fuzzy_engine(
    condition: ProcessCondition,
    current_params: list,
    target_defect: str,
) -> tuple:
    """
    调用 FuzzyEngine 推理（骨架接入，未调通端到端）。

    Returns:
        (adjustments, source) —— source 可能是 'fuzzy_engine' / 'fuzzy_unavailable' / 'fuzzy_error'

    设计约束（临时）：
      - 趈势后处理、推荐应用、多引擎合并均未实现，只走 FuzzyEngine 单一路径
      - defect_name 译文统一、polymer_category / product_category 提取方式后续调
      - FuzzyEngine 不可用 / 异常时返回 ([], 'fuzzy_unavailable')，调用方回退到硬编码字典
    """
    if not target_defect:
        return [], "fuzzy_unavailable"

    try:
        # Lazy import：避免 init 阶段循环依赖，service 依赖逆向 engines 也可以
        from process.engines.fuzzy import FuzzyEngine
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize_service] FuzzyEngine 导入失败: %s", e)
        return [], "fuzzy_unavailable"

    # 构造 FuzzyEngine 输入 context（骨架）
    # TODO: polymer_category / product_category 从 Polymer / Mold 提取（当前从 condition.snapshot.overrides 读）
    parameter_snapshot = {}
    if current_params:
        first_param = current_params[0]
        for field in first_param._meta.fields:
            if field.name.startswith('_') or field.name in ['id', 'created_at', 'updated_at']:
                continue
            value = getattr(first_param, field.name, None)
            if value is not None:
                parameter_snapshot[field.name] = value

    # 趋垫分析（复用 recommendation_service 的 iteration_trend）
    try:
        first_param = current_params[0] if current_params else None
        if first_param:
            trend = ProcessTuningService.analyze_iteration_trend(first_param)
            trend_dict = {
                "trend": trend.trend,
                "improving_count": trend.improving,
                "worsening_count": trend.worsening,
                "unchanged_count": trend.unchanged,
                "last_result": trend.last_result,
            }
        else:
            trend_dict = {"trend": "unknown"}
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize_service] iteration_trend 分析失败: %s", e)
        trend_dict = {"trend": "unknown"}

    overrides = (condition.process_context_snapshot or {}).get("overrides", {}) \
        if hasattr(condition, "process_context_snapshot") else {}

    fuzzy_context = {
        "defect_name": target_defect,  # TODO: 中文→SHORTSHOT 译文表
        "defect_feedbacks": [{"defect_name": target_defect}],
        "process_parameter": parameter_snapshot,
        "iteration_trend": trend_dict,
        "polymer_category": overrides.get("polymer_category"),
        "product_category": overrides.get("product_category"),
        "rule_library_code": None,
    }

    # 调用 FuzzyEngine（暂不接 EngineRegistry，单引擎路径）
    try:
        engine = FuzzyEngine()
        if not engine.is_available(fuzzy_context):
            return [], "fuzzy_unavailable"
        recommendations = engine.recommend(fuzzy_context)
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize_service] FuzzyEngine 推理失败: %s", e)
        return [], "fuzzy_error"

    # Recommendation -> adjustments 格式转换
    adjustments = []
    for rec in recommendations or []:
        param_name = rec.param_name
        current_val = parameter_snapshot.get(param_name)
        adjustments.append({
            "param": param_name,
            "direction": _infer_direction(current_val, rec.recommended_value),
            "current_value": current_val,
            "recommended_value": rec.recommended_value,
            "confidence": rec.confidence,
            "reason": rec.reason,
            "source": rec.source or "fuzzy_rule",
        })

    return adjustments, "fuzzy_engine"


def _infer_direction(current_value, recommended_value) -> str:
    """根据当前值与推荐值推断调整方向。"""
    if current_value is None or recommended_value is None:
        return "adjust"
    if recommended_value > current_value:
        return "increase"
    if recommended_value < current_value:
        return "decrease"
    return "adjust"


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