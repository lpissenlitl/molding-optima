"""
molding-optima 工艺专家调优 service

阶段 1 实现：基于规则的工艺参数建议。
阶段 2 将补充：基于 process_context_snapshot 的精细化算法（snapshot 格式待定）。
"""
import logging

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND
from process.models import ProcessCondition, ProcessParameter, RuleMethod

_logger = logging.getLogger(__name__)


# 缺陷类型与编码映射
DEFECT_CODE_MAP = {
    "短射": {"code": "B000", "name": "short_shot", "position_key": "B001", "feedback_key": "B002"},
    "缩水": {"code": "B003", "name": "shrinkage", "position_key": "B004", "feedback_key": "B005"},
    "飞边": {"code": "B006", "name": "flash", "position_key": "B007", "feedback_key": "B008"},
    "熔接痕": {"code": "B009", "name": "weld_line", "position_key": "B010", "feedback_key": "B011"},
    "困气": {"code": "B012", "name": "air_trap", "position_key": "B013", "feedback_key": "B014"},
    "气纹": {"code": "B015", "name": "gas_veins", "position_key": "B016", "feedback_key": "B017"},
    "烧焦": {"code": "B018", "name": "burn", "position_key": "B019", "feedback_key": "B020"},
    "料花": {"code": "B021", "name": "material_flower", "position_key": "B022", "feedback_key": "B023"},
    "色差": {"code": "B024", "name": "aberration", "position_key": "B025", "feedback_key": "B026"},
    "水波纹": {"code": "B027", "name": "water_ripple", "position_key": "B028", "feedback_key": "B029"},
    "脱模不良": {"code": "B030", "name": "hard_demolding", "position_key": "B031", "feedback_key": "B032"},
    "顶白": {"code": "B033", "name": "top_white", "position_key": "B034", "feedback_key": "B035"},
    "变形": {"code": "B036", "name": "warping", "position_key": "B037", "feedback_key": "B038"},
    "尺寸偏大": {"code": "B039", "name": "oversize", "position_key": "B040", "feedback_key": "B041"},
    "尺寸偏小": {"code": "B042", "name": "undersize", "position_key": "B043", "feedback_key": "B044"},
    "浇口印": {"code": "B045", "name": "gate_mark", "position_key": "B046", "feedback_key": "B047"},
    "阴阳面": {"code": "B048", "name": "shading", "position_key": "B049", "feedback_key": "B050"},
}


def build_defect_info(defect_feedback: dict) -> list:
    """
    根据缺陷反馈构建 defect_info 列表。
    defect_feedback: { "B000": "level", "B001": "position", "B002": "feedback", ... }
    """
    defect_info = []
    for label, defect_reflect in DEFECT_CODE_MAP.items():
        item = {
            "label": label,
            "desc": defect_reflect["name"].upper(),
            "level": "无缺陷",
            "position": "缺陷位置不指定",
            "count": 0,
            "feedback": None,
            "remark": None,
        }
        degree_key = defect_reflect["code"]
        if defect_feedback.get(degree_key) and defect_feedback[degree_key] != "无缺陷":
            item["level"] = defect_feedback[degree_key]
            item["position"] = defect_feedback.get(
                defect_reflect["position_key"], "缺陷位置不指定",
            ) or "缺陷位置不指定"
            item["feedback"] = defect_feedback.get(defect_reflect["feedback_key"])
            item["count"] += 1
        defect_info.append(item)
    return defect_info


def suggest_expert_adjustment(condition_id: int, defect_feedback: dict) -> dict:
    """
    专家调优：根据缺陷反馈匹配规则，给出调整建议。

    Args:
        condition_id: 工艺条件 ID
        defect_feedback: 缺陷反馈字典
    """
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    # 1. 提取有缺陷的标签
    defect_labels = [
        label for label, info in DEFECT_CODE_MAP.items()
        if defect_feedback.get(info["code"]) and defect_feedback[info["code"]] != "无缺陷"
    ]

    if not defect_labels:
        return {
            "condition_id": condition_id,
            "matched_rules": [],
            "suggested_adjustments": [],
            "message": "无缺陷，无需调优",
        }

    # 2. 匹配规则
    matched_rules = []
    for label in defect_labels:
        rules = RuleMethod.objects.filter(
            defect_name=label,
            enable=1,
            is_deleted=False,
        ).order_by("-priority")

        for rule in rules:
            matched_rules.append({
                "id": rule.id,
                "rule_type": rule.rule_type,
                "rule_description": rule.rule_description,
                "rule_explanation": rule.rule_explanation,
                "defect_name": rule.defect_name,
                "subrule_no": rule.subrule_no,
                "priority": rule.priority,
            })

    # 3. 给出参数调整建议
    suggested_adjustments = []
    for rule_data in matched_rules:
        adjustment = _map_rule_to_adjustment(rule_data, defect_labels)
        if adjustment:
            suggested_adjustments.append(adjustment)

    return {
        "condition_id": condition_id,
        "matched_rules": matched_rules,
        "suggested_adjustments": suggested_adjustments,
    }


def _map_rule_to_adjustment(rule_data: dict, defect_labels: list) -> dict:
    """将规则映射为参数调整建议（简化版）"""
    defect_name = rule_data.get("defect_name", "")

    adjustment_map = {
        "短射": {
            "target_params": ["inj_pres_1", "inj_spd_1", "vps_pos", "inj_t"],
            "direction": "increase",
            "suggestion": "提高注射压力/速度、延长注射时间或调整 VP 切换位置",
        },
        "缩水": {
            "target_params": ["hold_pres_1", "PP1", "hold_t_1", "PT1", "cool_t"],
            "direction": "increase",
            "suggestion": "提高保压压力、延长保压时间和冷却时间",
        },
        "飞边": {
            "target_params": ["inj_pres_1", "inj_spd_1", "vps_pos", "cool_t"],
            "direction": "decrease",
            "suggestion": "降低注射压力/速度、调整 VP 切换位置、增加锁模力",
        },
        "熔接痕": {
            "target_params": ["brl_temp_1", "brl_temp_2", "brl_temp_3", "inj_spd_1", "cool_t"],
            "direction": "increase",
            "suggestion": "提高料筒温度和注射速度",
        },
        "困气": {
            "target_params": ["inj_spd_1", "vps_pos", "cool_t"],
            "direction": "adjust",
            "suggestion": "降低注射速度、调整 VP 切换位置、检查模具排气",
        },
        "烧焦": {
            "target_params": ["inj_spd_1", "brl_temp_1", "brl_temp_2"],
            "direction": "decrease",
            "suggestion": "降低注射速度和料筒温度、检查排气",
        },
        "变形": {
            "target_params": ["cool_t", "hold_t_1", "PT1"],
            "direction": "increase",
            "suggestion": "延长冷却时间、调整保压时间均匀分布",
        },
        "顶白": {
            "target_params": ["hold_pres_1", "hold_spd_1"],
            "direction": "decrease",
            "suggestion": "降低保压压力和速度",
        },
    }

    base = adjustment_map.get(defect_name, {
        "target_params": [],
        "direction": "adjust",
        "suggestion": f"根据 {defect_name} 缺陷调优",
    })

    return {
        "rule_id": rule_data["id"],
        "defect_name": defect_name,
        "target_params": base["target_params"],
        "direction": base["direction"],
        "suggestion": base["suggestion"],
        "rule_description": rule_data.get("rule_description"),
    }


def get_defect_template() -> list:
    """获取所有缺陷类型模板（前端下拉用）"""
    return [
        {
            "label": label,
            "desc": info["name"],
            "code": info["code"],
        }
        for label, info in DEFECT_CODE_MAP.items()
    ]


def create_expert_optimization(
    company_id: int,
    organization_id: int,
    condition_id: int,
    defect_feedback: dict,
    actual_product_weight: float = None,
) -> dict:
    """
    创建专家调优记录。

    阶段 1：直接返回匹配规则和建议，不实际写新记录。
    阶段 2：将通过 process_context_snapshot 写入专家调优的具体策略。
    """
    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()
    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    result = suggest_expert_adjustment(condition_id, defect_feedback)
    defect_info = build_defect_info(defect_feedback)

    return {
        "source_condition_id": condition_id,
        "defect_info": defect_info,
        "matched_rules": result["matched_rules"],
        "suggested_adjustments": result["suggested_adjustments"],
    }