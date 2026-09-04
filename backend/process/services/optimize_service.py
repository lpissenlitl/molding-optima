"""
molding-optima 工艺优化 service

阶段 1：基于 DEFECT_OPTIMIZATION_HINTS 硬编码字典（兜底）
阶段 2（已完成）：优先调用 FuzzyEngine，无规则时回退到阶段 1 字典
阶段 3（规划）：基于 process_context_snapshot 写优化建议到字段中
"""
import logging
from typing import Optional

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


# 中文缺陷名 → 英文 defect_name 译文表（与 RuleMethod.defect_name 对齐）
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


def translate_defect_name(chinese_name: str) -> str:
    """中文缺陷名 → 英文 defect_name（供 FuzzyEngine 查询 RuleMethod）。"""
    if not chinese_name:
        return ""
    if chinese_name in DEFECT_NAME_MAP:
        return DEFECT_NAME_MAP[chinese_name]
    # 兜底：原文返回（可能是英文）
    return chinese_name


def get_fuzzy_engine():
    """
    获取 FuzzyEngine 实例（优先 EngineRegistry，避免重复初始化）。
    """
    try:
        from process.engines.base_engine import EngineRegistry
        engine = EngineRegistry.get_engine('fuzzy')
        if engine is not None:
            return engine
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize_service] 从 EngineRegistry 获取 FuzzyEngine 失败: %s", e)

    # 兑底：直接 import 并实例化
    try:
        from process.engines.fuzzy import FuzzyEngine
        return FuzzyEngine()
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize_service] FuzzyEngine 实例化失败: %s", e)
        return None


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


def _extract_process_parameters(current_params: list) -> dict:
    """从 ProcessParameter 列表提取数值型工艺参数（FuzzyEngine 输入）。

    仅提取 PROCESS_PARAM_FIELDS 白名单内的数值字段，避免非数值字段进入
    FuzzyEngine 造成 keyword 解析错误。
    """
    snapshot = {}
    if not current_params:
        return snapshot

    first_param = current_params[0]
    for field_name in PROCESS_PARAM_FIELDS:
        value = getattr(first_param, field_name, None)
        # 仅保留数值字段
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            snapshot[field_name] = float(value)
    return snapshot


def _infer_via_fuzzy_engine(
    condition: ProcessCondition,
    current_params: list,
    target_defect: str,
) -> tuple:
    """
    调用 FuzzyEngine 推理（阶段 2 完成）。

    路由顺序：
      1. 从 EngineRegistry 获取 FuzzyEngine 实例
      2. 中文 defect_name → 英文（DEFECT_NAME_MAP）
      3. 提取数值型工艺参数快照（PROCESS_PARAM_FIELDS 白名单）
      4. 分析迭代趋势（ProcessTuningService.analyze_iteration_trend）
      5. 调用 FuzzyEngine.recommend(context)
      6. Recommendation → adjustments 格式转换

    Returns:
        (adjustments, source) —— source 可能是：
        - 'fuzzy_engine': FuzzyEngine 成功返回推荐
        - 'fuzzy_unavailable': FuzzyEngine 不可用（is_available False）
        - 'fuzzy_error': FuzzyEngine 推理异常
    """
    if not target_defect:
        return [], "fuzzy_unavailable"

    engine = get_fuzzy_engine()
    if engine is None:
        return [], "fuzzy_unavailable"

    # 1. 翻译中文 defect_name → 英文
    defect_name_en = translate_defect_name(target_defect)

    # 2. 提取工艺参数快照
    parameter_snapshot = _extract_process_parameters(current_params)

    # 3. 趋势分析（复用 tuning_service）
    trend_dict = {"trend": "unknown"}
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
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize_service] iteration_trend 分析失败: %s", e)

    # 4. 从 process_context_snapshot 读取 polymer_category / product_category
    overrides = {}
    snapshot = getattr(condition, 'process_context_snapshot', None) or {}
    if isinstance(snapshot, dict):
        overrides = snapshot.get('overrides', {}) or {}

    fuzzy_context = {
        "defect_name": defect_name_en,
        "defect_feedbacks": [{"defect_name": defect_name_en}],
        "process_parameter": parameter_snapshot,
        "iteration_trend": trend_dict,
        "polymer_category": overrides.get("polymer_category"),
        "product_category": overrides.get("product_category"),
        "rule_library_code": overrides.get("rule_library_code"),
    }

    # 5. 调用 FuzzyEngine
    try:
        if not engine.is_available(fuzzy_context):
            _logger.info("[optimize_service] FuzzyEngine 不可用 (defect=%s, trend=%s)",
                         defect_name_en, trend_dict.get("trend"))
            return [], "fuzzy_unavailable"
        recommendations = engine.recommend(fuzzy_context)
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize_service] FuzzyEngine 推理失败: %s", e, exc_info=True)
        return [], "fuzzy_error"

    if not recommendations:
        _logger.info("[optimize_service] FuzzyEngine 未返回推荐 (defect=%s)", defect_name_en)
        return [], "fuzzy_unavailable"

    # 6. Recommendation → adjustments 格式转换
    adjustments = []
    for rec in recommendations:
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

    _logger.info("[optimize_service] FuzzyEngine 返回 %d 条推荐 (defect=%s)",
                 len(adjustments), defect_name_en)
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