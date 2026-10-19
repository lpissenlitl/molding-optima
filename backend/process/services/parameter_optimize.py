"""工艺优化 infer 服务（调用链路编排层，不含算法实现）

对应接口：
- FromCondition：POST /api/processes/algorithms/optimize/
- FromProvided：POST /api/processes/algorithms/optimize-from-provided/

职责：Step 1 反查 parent → Step 2 构建基线 → Step 3 调算法 → Step 4 原子落库（仅 FromCondition）

设计要点：
- infer 只处理算法优化（人工调整走 manual-adjust 接口）
- 算法侧是接口契约：输入 context，输出 List[Recommendation]，算法实现对本服务透明
- 3 场景调用逻辑一致（基本调参/自动回撤/手动修改），仅 feedback 内容不同
- is_adopted 自动维护：下一轮 ineffective 时改 False
- FromCondition 落库，FromProvided 纯推理（无 DB 读写，与 initialize.infer_from_provided 同构）

代码组织（2026-10-15 整改）：
- 模块顶层放所有 helper（纯函数，不依赖 self）
- 类内只保留 infer / infer_from_provided 两个公开入口 + __init__
- 遵循 Guido / Hettinger 的"static method 没什么用"建议
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, TypedDict

from django.db import transaction as db_transaction

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_OPERATION_FAILED, ERROR_REQUIRED_FIELD
from process.models import (
    ProcessCondition,
    ProcessParameter,
    Recommendation,
    TuningRecord,
)
from process.algorithms.base import AlgorithmRegistry, Recommendation
from process.algorithms.fuzzy import FuzzyEngine  # 用于字段命名约束（FIELD_NAME_ALIAS）
from process.algorithms.fuzzy.specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OPTIMIZE_POLYMER_INFO_FIELDS,
    OPTIMIZE_MOLD_INFO_FIELDS,
)  # 算法入参契约（字段字典）—— service 层按此白名单提取，不传全量 ORM 字段

_logger = logging.getLogger(__name__)


# ============================================================================
# 模块级 lazy 引擎注册（避免重复注册 + 避免循环依赖）
# ============================================================================
_engines_registered = False


def _ensure_engines_registered() -> None:
    """模块级 lazy 触发引擎注册（幂等）"""
    global _engines_registered
    if _engines_registered:
        return
    try:
        from process.algorithms.fuzzy import FuzzyEngine
        if not AlgorithmRegistry.get_algorithm("fuzzy"):
            AlgorithmRegistry.register("fuzzy", FuzzyEngine())
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimize] FuzzyEngine 注册失败: %s", e)
    _engines_registered = True


# ============================================================================
# 算法接口契约（AlgorithmContext schema）
#
# 设计（2026-09-30 确认）：
# - 虽然算法侧 AIEngineBase.recommend 接受 Dict[str, Any]（不限严格 schema），
#   但 Step 2 → Step 3 之间应有明确的契约文档，否则字段缺失只能运行时发现。
# - 使用 TypedDict：保留 Dict 调用风格 + 提供类型提示 + 0 运行成本。
# - _REQUIRED_CONTEXT_KEYS 是运行期 fail-fast 验证集合。
# ============================================================================
class AlgorithmContext(TypedDict):
    """算法引擎输入 context 的标准格式

    由 Step 2 _compose_algorithm_context 构造，Step 3 _call_algorithms 使用。

    字段语义（均为子对象，避免平铺字符串的语义丢失）：
    - machine_info: 设备信息（按 injection_index 选中的 InjectionUnit 完整 dict，含 HMI 范围字段）
    - polymer_info: 材料信息（必填 dict，算法内部按需取 abbreviation 等。允许为空 {}）
    - mold_info: 模具信息（必填 dict，算法内部按需取 product_category 等。允许为空 {}）
    - process_parameter: 工艺参数（已翻译为算法侧命名，如 IL1/NT/CT）
    - feedback: 反馈信息（整体透传，不拆分）

    命名约定：字段名与 HTTP schema 对齐，也与 parameter_initialize._infer_kernel 形参名对齐
    """
    machine_info: Dict[str, Any]
    polymer_info: Dict[str, Any]
    mold_info: Dict[str, Any]
    process_parameter: Dict[str, Any]
    feedback: Dict[str, Any]


# 必需 key 集合（用于 _call_algorithms 入口验证）
_REQUIRED_CONTEXT_KEYS = frozenset(AlgorithmContext.__annotations__.keys())


# ============================================================================
# 参数分类（按 prefix 分组，与 Recommendation.recommendations 对齐）
# ============================================================================
_PARAM_CATEGORY_RULES = (
    ('inj_', ('注射参数', 'mdi:speedometer')),
    ('hold_', ('保压参数', 'mdi:gauge')),
    ('met_', ('熔胶参数', 'mdi:screw-machine-flat-top')),
    ('vps_', ('VP 切换', 'mdi:swap-vertical')),
    ('brl_temp_', ('料筒温度', 'mdi:thermometer')),
    ('cool_', ('冷却参数', 'mdi:snowflake')),
    ('pre_met_decomp_', ('熔胶前松退', 'mdi:arrow-collapse')),
    ('pst_met_decomp_', ('熔胶后松退', 'mdi:arrow-collapse')),
    ('noz_temp', ('料筒温度', 'mdi:thermometer')),
)


def _categorize_param(param_name: str) -> Tuple[str, str]:
    """参数名 → (category, icon)"""
    for match_key, (category, icon) in _PARAM_CATEGORY_RULES:
        if match_key.endswith('_'):
            if param_name.startswith(match_key):
                return category, icon
        else:
            if param_name == match_key:
                return category, icon
    return '其他参数', 'mdi:cog-outline'


def _direction_from_delta(before: Optional[float], after: Optional[float]) -> Optional[str]:
    """根据 before/after 数值推断调整方向。边界：None / 等值时返回 None。"""
    if before is None or after is None:
        return None
    if after > before:
        return 'increase'
    if after < before:
        return 'decrease'
    return 'hold'


# ============================================================================
# snapshot 字段排除集（用于 _snapshot_parameter）
# ============================================================================
_NON_SNAPSHOT_FIELDS = frozenset({
    # 元数据
    "id", "created_at", "updated_at", "deleted", "deleted_at", "is_deleted",
    # 业务字段（snapshot 外另行处理）
    "parameter_no",
    "param_source",
    "seq_idx",
})


# "无缺陷" sentinel keyword 名称
_DEFECTFREE_KEYWORD_NAME = "DEFECTFREE"


# ============================================================================
# ORM 序列化 + 字段命名翻译 helper
# ============================================================================
def _to_full_dict(instance: Any) -> Dict[str, Any]:
    """ORM → 完整 dict（仅排除 ORM 关系字段）"""
    if instance is None:
        return {}
    return {
        f.name: getattr(instance, f.name)
        for f in instance._meta.fields
        if not f.is_relation
    }


def _normalize_field_name_by_spec(
    params: Dict[str, Any],
    field_spec: Dict[str, str],
) -> Dict[str, Any]:
    """按算法侧声明的字段命名约束做字段名翻译（业务 → 算法）

    Port-Adapter 模式：算法侧声明字段命名约定（FIELD_NAME_ALIAS），
    数据准备层按约束翻译（不感知业务语义）。
    """
    if not field_spec:
        return dict(params)

    normalized: Dict[str, Any] = {}
    for key, value in params.items():
        if key in field_spec:
            normalized[field_spec[key]] = value
            continue
        prefix, sep, suffix = key.rpartition('_')
        if sep and suffix.isdigit() and prefix in field_spec:
            new_key = f"{field_spec[prefix]}{suffix}"
        else:
            new_key = key
        normalized[new_key] = value
    return normalized


# ============================================================================
# Step 0 — feedback 校验（两个 inference 入口共用）
# ============================================================================
def _validate_feedback(feedback: Dict[str, Any]) -> None:
    """Step 0 —— feedback 防御性校验（与前端 validateFeedback 是同一套约束镜像）

    Raises:
        BizException(ERROR_REQUIRED_FIELD): 字段缺失
    """
    defects = feedback.get("defect") or []
    if not isinstance(defects, list) or len(defects) == 0:
        raise BizException(ERROR_REQUIRED_FIELD, "请填写缺陷反馈信息")

    for i, d in enumerate(defects, 1):
        if not isinstance(d, dict):
            raise BizException(ERROR_REQUIRED_FIELD, f"第 {i} 项缺陷格式错误：应为对象")
        if d.get("keyword_name") is None:
            raise BizException(ERROR_REQUIRED_FIELD, f"第 {i} 项缺陷未选择缺陷类型（keyword_name 必填）")
        is_defect_free = d.get("keyword_name") == _DEFECTFREE_KEYWORD_NAME
        if not is_defect_free:
            if not d.get("level"):
                raise BizException(ERROR_REQUIRED_FIELD, f"第 {i} 项缺陷未选择缺陷程度")
            if not d.get("position"):
                raise BizException(ERROR_REQUIRED_FIELD, f"第 {i} 项缺陷未填写缺陷位置")


# ============================================================================
# Step 1 — ORM 反查
# ============================================================================
def _resolve_parent(
    condition_id: int,
    parent_seq_idx: int,
) -> Tuple[ProcessCondition, ProcessParameter]:
    """Step 1 —— 反查 condition + parent_param

    使用 select_related + prefetch_related 预加载：
    - injection_machine / polymer / mold（FK 一级）
    - injection_machine__injection_units（FK 二级，避免 N+1）
    """
    try:
        condition = (
            ProcessCondition.objects
            .select_related('injection_machine', 'polymer', 'mold')
            .prefetch_related('injection_machine__injection_units')
            .get(id=condition_id)
        )
    except ProcessCondition.DoesNotExist as exc:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}") from exc

    try:
        parent_param = ProcessParameter.objects.get(
            process_condition=condition,
            seq_idx=parent_seq_idx,
        )
    except ProcessParameter.DoesNotExist as exc:
        raise BizException(
            ERROR_DATA_NOT_FOUND,
            f"基准工艺参数不存在: condition_id={condition_id}, seq_idx={parent_seq_idx}",
        ) from exc

    return condition, parent_param


# ============================================================================
# Step 2 — 解析 baseline
# ============================================================================
def _resolve_baseline(
    user_parameter: Optional[Dict[str, Any]],
    base_param_orm: ProcessParameter,
) -> Dict[str, Any]:
    """Step 2 —— 解析 baseline（与 condition+seq_idx 对应的基准 parameter 值）

    base_param_orm 命名说明：
    - DB 字段 ProcessParameter.parent_param 是模型层定义，
      表示「基于哪个参数进行调整」，这个语义保留在数据模型中
    - 本函数形参叫 base_param_orm，强调「基准起点 / 推理上下文」语义
      （区别于落库时 parent_param 的父子链语义）

    优先级：
    1. user_parameter 非空 → 先把入参字段持久化到 base_param_orm
       （保证 DB 与本轮推理起点一致），然后从 ORM 读取 baseline
    2. 否则 → 直接从 base_param_orm ORM 读取
    """
    if user_parameter is not None:
        allowed = {
            f.name for f in base_param_orm._meta.fields
            if not f.is_relation and f.name not in _NON_SNAPSHOT_FIELDS
        }
        for key, value in user_parameter.items():
            if value is None:
                continue
            if key not in allowed:
                continue
            setattr(base_param_orm, key, value)
        base_param_orm.save()
    return _to_full_dict(base_param_orm) or {}


def _snapshot_parameter(parameter: ProcessParameter) -> Dict[str, Any]:
    """从 ProcessParameter 取标量工艺字段（排除元数据与业务字段）"""
    snapshot: Dict[str, Any] = {}
    for field in parameter._meta.fields:
        name = field.name
        if name in _NON_SNAPSHOT_FIELDS:
            continue
        if field.is_relation:
            continue
        value = getattr(parameter, name, None)
        if value is not None:
            snapshot[name] = value
    return snapshot


# ============================================================================
# Step 3 — 算法调用与上下文构造
# ============================================================================
def _empty_algorithm_result() -> Dict[str, Any]:
    """统一空返回结构（避免在 _call_algorithms 里重复字面量）"""
    return {
        "recommendations": [],
        "algorithm_sources": {},
        "best_recommendation": None,
    }


def _call_algorithms(context: AlgorithmContext) -> Dict[str, Any]:
    """Step 3 —— 纯调用已注册引擎，不查 DB

    Returns:
        {
            'recommendations': [...],       # 合并后的扁平推荐列表
            'algorithm_sources': {name: [...]},
            'best_recommendation': {...} | None,
        }

    TODO（后续迭代）：
    - trend 后处理
    - 多引擎同参数合并
    """
    if not context:
        _logger.warning("[optimize] _call_algorithms context 为空")
        return _empty_algorithm_result()
    missing = _REQUIRED_CONTEXT_KEYS - set(context.keys())
    if missing:
        _logger.warning("[optimize] _call_algorithms context 缺字段: %s", missing)
        return _empty_algorithm_result()

    engines = AlgorithmRegistry.get_available_algorithms(context)
    engines = sorted(
        engines,
        key=lambda a: AlgorithmRegistry.get_priority(a.algorithm_name),
    )
    if not engines:
        _logger.info("[optimize] 无可用引擎")
        return _empty_algorithm_result()

    all_recommendations: List[Recommendation] = []
    algorithm_sources: Dict[str, List[Dict[str, Any]]] = {}
    for algorithm in engines:
        try:
            recs = algorithm.recommend(context) or []
        except Exception as e:  # noqa: BLE001
            _logger.warning("[optimize] 引擎 %s 推理失败: %s", algorithm.algorithm_name, e)
            recs = []
        algorithm_sources[algorithm.algorithm_name] = [r.to_dict() for r in recs]
        all_recommendations.extend(recs)

    merged = [r.to_dict() for r in all_recommendations]
    return {
        "recommendations": merged,
        "algorithm_sources": algorithm_sources,
        "best_recommendation": merged[0] if merged else None,
    }


def _compose_algorithm_context(
    *,
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    mold_info: Dict[str, Any],
    parameter: Dict[str, Any],
    feedback: Dict[str, Any],
) -> Dict[str, Any]:
    """Step 2 核心 —— 装成 AlgorithmContext（Port-Adapter 模式）

    - 字段选择（业务多 → 算法少）
    - 字段名翻译（业务命名 → 算法命名，按 FuzzyEngine.FIELD_NAME_ALIAS）
    - 上下文组装
    """
    algorithm_params = _normalize_field_name_by_spec(
        parameter, FuzzyEngine.FIELD_NAME_ALIAS,
    )
    return {
        'machine_info': machine_info,
        'polymer_info': polymer_info,
        'mold_info': mold_info,
        'process_parameter': algorithm_params,
        'feedback': feedback,
    }


# ============================================================================
# Step 3 字段提取（按 specs.py 白名单）
# ============================================================================
def _select_injection_unit(condition: ProcessCondition) -> Optional[Any]:
    """按 condition.injection_index 从 InjectionMoldingMachine.injection_units 选一台

    返回该 InjectionUnit 实例（不是 dict），便于后续按 specs 跨表取值。
    未找到则返回 None（由调用方决定是否降级为 {}）。
    """
    machine = condition.injection_machine
    if machine is None:
        return None

    injection_index = condition.injection_index or 0
    injection_units = list(machine.injection_units.all())
    if injection_index < len(injection_units):
        return injection_units[injection_index]

    _logger.warning(
        "[optimize] injection_index=%s 超出 machine(id=%s) 的 injection_units（共 %s 个）",
        injection_index, machine.id, len(injection_units),
    )
    return None


def _extract_orm_fields_by_spec(
    source_orm_map: Dict[str, Any],
    spec_dict: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """【service 层统一提取 helper】按 specs 契约跨 source_model 取值（白名单）

    遍历 spec_dict，对每个 entry 按 source_model 选对应 ORM 实例，
    用 getattr 取 attr_name 值。None 值不纳入返回 dict。

    与 field_contract 的关系：
    - field_contract 提供【校验机制】（audit_field_completeness）
    - 本函数提供【提取机制】（按 spec 从 ORM 取值）
    """
    extracted: Dict[str, Any] = {}
    for spec_key, spec in spec_dict.items():
        source_model = spec.get("source_model")
        attr_name = spec.get("attr_name")
        if not source_model or not attr_name:
            continue
        orm_instance = source_orm_map.get(source_model)
        if orm_instance is None:
            continue
        value = getattr(orm_instance, attr_name, None)
        if value is not None:
            extracted[spec_key] = value
    return extracted


def _extract_machine_info(condition: ProcessCondition) -> Dict[str, Any]:
    """按 OPTIMIZE_MACHINE_INFO_FIELDS 契约提取 machine_info（白名单）

    跨两张表合并：
    - InjectionMoldingMachine.drive_system（机器主表）
    - InjectionUnit.max_set_*（按 injection_index 选 unit）

    只返回 specs 声明的字段；ORM 元数据不传给算法。
    """
    machine = condition.injection_machine
    if machine is None:
        return {}
    selected_unit = _select_injection_unit(condition)
    if selected_unit is None:
        return {}

    return _extract_orm_fields_by_spec(
        source_orm_map={
            "InjectionMoldingMachine": machine,
            "InjectionUnit": selected_unit,
        },
        spec_dict=OPTIMIZE_MACHINE_INFO_FIELDS,
    )


def _extract_polymer_info(condition: ProcessCondition) -> Dict[str, Any]:
    """按 OPTIMIZE_POLYMER_INFO_FIELDS 契约从 Polymer 提取 polymer_info（白名单）"""
    polymer = condition.polymer
    if polymer is None:
        return {}
    return _extract_orm_fields_by_spec(
        source_orm_map={"Polymer": polymer},
        spec_dict=OPTIMIZE_POLYMER_INFO_FIELDS,
    )


def _extract_mold_info(condition: ProcessCondition) -> Dict[str, Any]:
    """按 OPTIMIZE_MOLD_INFO_FIELDS 契约从 Mold 提取 mold_info（白名单）"""
    mold = condition.mold
    if mold is None:
        return {}
    return _extract_orm_fields_by_spec(
        source_orm_map={"Mold": mold},
        spec_dict=OPTIMIZE_MOLD_INFO_FIELDS,
    )


# ============================================================================
# Step 4 — 应用推荐 + 构造 suggestion
# ============================================================================
def _apply_recommendations_to_baseline(
    baseline: Dict[str, Any],
    algorithm_recommendations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Step 4a —— 用推荐值覆盖基线字段（仅覆盖基线中存在的字段）"""
    new_parameter = dict(baseline)
    for rec in algorithm_recommendations:
        param_name = rec.get("param")
        recommended_value = rec.get("recommended_value")
        if param_name and param_name in new_parameter and recommended_value is not None:
            new_parameter[param_name] = recommended_value
    return new_parameter


def _resolve_primary_source(algorithm_sources: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
    """选取主要算法来源（按 AlgorithmRegistry._priorities 顺序）

    返回引擎 subtype（fuzzy / rule_miner / llm ...）。
    """
    priority_order = ('expert', 'fuzzy', 'rule_miner', 'llm', 'doe', 'ga')
    for subtype in priority_order:
        if algorithm_sources.get(subtype):
            return subtype
    for subtype, recs in algorithm_sources.items():
        if recs:
            return subtype
    return None


def _build_description(rec: Dict[str, Any]) -> str:
    """构造建议文本。优先 reason，否则 "调整 {param} {direction} → {value}"。"""
    reason = rec.get("reason") or ""
    if reason:
        return reason

    param = rec.get("param", "")
    before = rec.get("current_value")
    after = rec.get("recommended_value")
    direction = _direction_from_delta(before, after)
    direction_cn = {
        "increase": "增大",
        "decrease": "减小",
        "hold": "保持",
    }.get(direction or "", "调整")

    if before is not None and after is not None:
        return f"{direction_cn} {param}: {before} → {after}"
    return f"{direction_cn} {param}: {after}"


def _extract_rule_refs(rec: Dict[str, Any]) -> List[str]:
    """提取规则引用（当前算法侧 Recommendation 无规则引用字段，预留接口）"""
    refs = rec.get("rule_refs") or []
    if isinstance(refs, list):
        return [str(r) for r in refs]
    return []


def _build_suggestion_payload(
    algorithm_recommendations: List[Dict[str, Any]],
    algorithm_sources: Dict[str, List[Dict[str, Any]]],
    baseline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Step 4b —— 扁平推荐按 category 分组，构建 SuggestionGroup

    baseline 不为 None 时只保留在 baseline 中存在的推荐字段
    （与 _apply_recommendations_to_baseline 严格对齐）。
    """
    source_type = _resolve_primary_source(algorithm_sources) or "none"

    if not algorithm_recommendations:
        return {"source_type": source_type, "groups": []}

    # 一致性过滤：与 _apply_recommendations_to_baseline 严格对齐
    if baseline is not None:
        filtered_recs = [
            rec for rec in algorithm_recommendations
            if rec.get("param") in baseline
        ]
    else:
        filtered_recs = algorithm_recommendations

    if not filtered_recs:
        return {"source_type": source_type, "groups": []}

    grouped: Dict[str, Dict[str, Any]] = {}
    for rec in filtered_recs:
        param_name = rec.get("param", "")
        category, icon = _categorize_param(param_name)

        if category not in grouped:
            grouped[category] = {"category": category, "icon": icon, "items": []}

        grouped[category]["items"].append({
            "description": _build_description(rec),
            "direction": _direction_from_delta(
                rec.get("current_value"),
                rec.get("recommended_value"),
            ),
            "rule_refs": _extract_rule_refs(rec),
        })

    return {
        "source_type": source_type,
        "groups": list(grouped.values()),
    }


# ============================================================================
# 纯算法内核（Step 3+4）—— 对应 parameter_initialize._infer_kernel
#
# 设计（2026-10-15 二次调整）：从模块顶层函数改为类内 @staticmethod
# - 与 parameter_initialize._infer_kernel 同构同同名（都在类内，都是私有）
# - 两个入口共用（infer / infer_from_provided）
# ============================================================================


# ============================================================================
# 落库 helper（DB 操作，纯函数 / 无 self 依赖）
# ============================================================================
def _update_previous_tuning_record(
    parent_param: ProcessParameter,
    defect_feedbacks: List[Dict[str, Any]],
    tuning_result: Optional[str],
) -> None:
    """更新上一轮 TuningRecord（缺陷反馈 + 试模结果；取最新一条）"""
    previous_record = (
        TuningRecord.objects
        .filter(process_parameter=parent_param)
        .order_by("-created_at")
        .first()
    )
    if previous_record is None:
        _logger.warning(
            "[optimize] 父参数缺少 TuningRecord: parameter_id=%s（业务层应保证 1:1）",
            parent_param.id,
        )
        return

    if defect_feedbacks:
        previous_record.defect_feedbacks = defect_feedbacks

    if tuning_result in ("effective", "ineffective"):
        previous_record.result = {
            "effective": "improved",
            "ineffective": "worse",
        }[tuning_result]

    previous_record.save()


def _update_previous_recommendation_is_adopted(
    parent_param: ProcessParameter,
    tuning_result: Optional[str],
) -> None:
    """下一轮 ineffective 时将上一轮 Recommendation.is_adopted 改为 False（训练标签）"""
    if tuning_result != "ineffective":
        return

    previous_recommendation = (
        Recommendation.objects
        .filter(process_parameter=parent_param)
        .order_by("-created_at")
        .first()
    )
    if previous_recommendation is None:
        return

    if previous_recommendation.is_adopted:
        previous_recommendation.is_adopted = False
        previous_recommendation.save(update_fields=["is_adopted", "updated_at"])


def _create_new_parameter(
    condition: ProcessCondition,
    parent_param: ProcessParameter,
    parameters_dict: Dict[str, Any],
) -> ProcessParameter:
    """Step 5.3 —— 创建新 ProcessParameter（param_source='system_inferred'）"""
    return ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=parent_param,
        param_source="system_inferred",
        **parameters_dict,
    )


def _create_new_tuning_record(
    new_param: ProcessParameter,
    parent_param: ProcessParameter,
    defect_feedbacks: List[Dict[str, Any]],
) -> TuningRecord:
    """Step 5.4 —— 创建新 TuningRecord（pending 状态）"""
    previous_parameter_snapshot = _snapshot_parameter(parent_param)
    return TuningRecord.objects.create(
        process_parameter=new_param,
        defect_feedbacks=defect_feedbacks,
        result="pending",
        previous_parameter=previous_parameter_snapshot,
    )


def _create_new_recommendation(
    new_param: ProcessParameter,
    algorithm_recommendations: List[Dict[str, Any]],
    source_type: str,
) -> Recommendation:
    """Step 5.5 —— 创建新 Recommendation（is_adopted=True，下一轮 ineffective 自动改 False）"""
    return Recommendation.objects.create(
        process_parameter=new_param,
        source_type=source_type or "fuzzy_rule",
        recommendations=algorithm_recommendations,
        is_adopted=True,
    )


# ============================================================================
# infer 服务（主类）
# ============================================================================
class ParameterOptimizeService:
    """工艺优化 infer 服务 —— 调用链路编排

    设计约束：
    - 算法侧是接口契约：本服务只负责编排，不实现具体推理
    - 所有 Step 在一个原子事务内完成（避免半成品落库）

    类的职责边界（2026-10-15 整改）：
    - 仅保留 2 个公开入口 infer / infer_from_provided + __init__
    - 其他 helper 全部为模块顶层函数（不依赖 self / 遵循 Python 之父 Guido 的
      "static method 没什么用" 建议）
    - 调用形式与 view 层一致：service.infer() / service.infer_from_provided()
    """

    def __init__(self):
        # 触发模块级 lazy 引擎注册（幂等）
        _ensure_engines_registered()

    def infer(
        self,
        condition_id: int,
        parent_seq_idx: int,
        parameter: Optional[Dict[str, Any]] = None,
        feedback: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        工艺优化 infer 主入口

        Args:
            condition_id: 工艺条件 ID（必填）
            parent_seq_idx: 基准业务编号（必填）
            parameter: 手动修改覆盖（可选，flat 字段对齐 ProcessParameterSchema；
                       None 表示从 ORM 反查 parent_param 作 baseline，前端 UI 改了的
                       工艺参数需先由前端 parameterToFlat 翻译为 flat dict 再传入）
            feedback: 反馈信息（嵌套 dict，可选）

        Returns:
            {
                "new_parameter": {...},
                "suggestion": {
                    "source_type": str,
                    "recommendation_id": int,
                    "groups": [...]
                }
            }
        """
        feedback = feedback or {}
        # Step 0: feedback 防御性校验
        _validate_feedback(feedback)

        # ---------- Step 1: 反查 ORM（condition + parent_param）----------
        condition_orm, parent_param_orm = _resolve_parent(
            condition_id=condition_id,
            parent_seq_idx=parent_seq_idx,
        )

        # ---------- Step 2: 解析 baseline（用户入参优先，否则 ORM）----------
        # 注意：_resolve_baseline 的形参 base_param_orm 与 ORM 字段 parent_param
        # 指同一个实例，但语义不同：base = 推理上下文，parent = 落库父子链
        baseline = _resolve_baseline(
            user_parameter=parameter,
            base_param_orm=parent_param_orm,
        )

        # ---------- Step 3: 提取 3 个算法入参 dict（按 specs.py 白名单）----------
        # service 层只传 specs 声明的字段，不传 ORM 元数据也不传其他业务字段。
        # 跨表场景：machine_info 从 InjectionMoldingMachine + InjectionUnit 合并。
        machine_info = _extract_machine_info(condition_orm)
        polymer_info = _extract_polymer_info(condition_orm)
        mold_info = _extract_mold_info(condition_orm)

        # ---------- Step 4: 纯推理（与 DB 无关）----------
        new_parameter_dict, suggestion_payload, algorithm_recommendations = self._infer_kernel(
            machine_info=machine_info,
            polymer_info=polymer_info,
            mold_info=mold_info,
            baseline=baseline,
            feedback=feedback,
            interface_tag=f"infer(condition_id={condition_id}, parent_seq_idx={parent_seq_idx})",
        )

        # ---------- Step 5: 原子事务落库 ----------
        # Step 5 入口一次性从 feedback 提取（贴近使用方，不跨步共享）
        defect_feedbacks = feedback.get("defect", []) or []
        tuning_result = feedback.get("tuning_result")
        with db_transaction.atomic():
            # 5.1 更新上一轮 TuningRecord（缺陷反馈 + 试模结果）
            _update_previous_tuning_record(
                parent_param=parent_param_orm,
                defect_feedbacks=defect_feedbacks,
                tuning_result=tuning_result,
            )

            # 5.2 更新上一轮 Recommendation.is_adopted（训练标签）
            _update_previous_recommendation_is_adopted(
                parent_param=parent_param_orm,
                tuning_result=tuning_result,
            )

            # 5.3 创建新 ProcessParameter
            new_param = _create_new_parameter(
                condition=condition_orm,
                parent_param=parent_param_orm,
                parameters_dict=new_parameter_dict,
            )

            # 5.4 创建新 TuningRecord（pending 状态，等待下次反馈）
            _create_new_tuning_record(
                new_param=new_param,
                parent_param=parent_param_orm,
                defect_feedbacks=defect_feedbacks,
            )

            # 5.5 创建新 Recommendation
            recommendation = _create_new_recommendation(
                new_param=new_param,
                algorithm_recommendations=algorithm_recommendations,
                source_type=suggestion_payload.get("source_type") or "fuzzy_rule",
            )

        # ---------- Step 6: 组装响应 ----------
        return {
            "new_parameter": {
                **new_parameter_dict,
                "parameter_id": new_param.id,
                "seq_idx": new_param.seq_idx,
            },
            "suggestion": {
                **suggestion_payload,
                "recommendation_id": recommendation.id,
            },
        }

    def infer_from_provided(
        self,
        parameter: Dict[str, Any],
        feedback: Dict[str, Any],
        mold_info: Dict[str, Any],
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """【FromProvided 入口】纯推理 infer —— 不查 DB、不落库

        适用场景：
        - 第三方集成（其库内无我们的 masterdata）
        - 算法试算（前端 dry-run）
        - 单元测试 / 烟测

        与 infer() 的关键差异：
        - 不传 condition_id / parent_seq_idx（无 ORM）
        - 三维上下文由调用方直传
        - 无 Step 1 反查 parent、无 Step 5 落库
        - 响应不含 recommendation_id / new_parameter.parameter_id / seq_idx

        设计（2026-10-15 二次调整）：从顶层函数改回类内实例方法
        - 保持与 view 层调用形式一致（service.infer() / service.infer_from_provided()）
        - 与 parameter_initialize 的类内 @classmethod infer_from_provided 同构（都在类内）
        """
        feedback = feedback or {}
        # Step 0: feedback 防御性校验（与 infer() 同套约束镜像）
        _validate_feedback(feedback)

        # 调 self._infer_kernel 纯推理（与 infer() 走同一函数）
        # 第 3 个返回值 algorithm_recommendations 无需落库（FromProvided 是纯推理）
        new_parameter_dict, suggestion_payload, _ = self._infer_kernel(
            machine_info=machine_info or {},
            polymer_info=polymer_info or {},
            mold_info=mold_info or {},
            baseline=parameter,
            feedback=feedback,
            interface_tag="infer_from_provided",
        )

        return {
            "new_parameter": new_parameter_dict,    # 无 parameter_id / seq_idx
            "suggestion": suggestion_payload,         # 无 recommendation_id
        }

    # ============================================================
    # 纯算法内核（Step 3+4）—— 私有方法，三个入口共用
    # ============================================================
    @staticmethod
    def _infer_kernel(
        *,
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        mold_info: Dict[str, Any],
        baseline: Dict[str, Any],
        feedback: Dict[str, Any],
        interface_tag: str,
        fail_fast_message: str = "推荐算法暂不可用，请稍后重试或联系管理员",
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
        """【Step 3+4 纯算法内核】5 维 dict → (new_parameter, suggestion, algorithm_recommendations)

        私有方法（_ 前缀）：从模块顶层函数调整为类内 @staticmethod
        - 两个公开入口（infer / infer_from_provided）共用本方法
        - 不依赖 self/cls，无副作用

        对应 parameter_initialize._infer_kernel（同构同名设计）。

        Args:
            machine_info: 设备 dict（HMI 范围由算法自挑）
            polymer_info: 材料 dict（含 abbreviation）
            mold_info: 模具 dict（含 product_category）
            baseline: 调优基线（flat 字段，对齐 ProcessParameterSchema）
            feedback: 缺陷反馈
            interface_tag: fail-fast 日志前缀
            fail_fast_message: BizException 文案

        Returns:
            (new_parameter_dict, suggestion_payload, algorithm_recommendations)
            - new_parameter_dict: 应用推荐后的扁平 dict
            - suggestion_payload: {source_type, groups}，groups 已按 baseline 过滤
            - algorithm_recommendations: 算法原始推荐列表（infer 落库用）

        Raises:
            BizException(ERROR_OPERATION_FAILED): 算法无任何推荐
        """
        # 装成 AlgorithmContext（service 内实现细节）
        algorithm_context = _compose_algorithm_context(
            machine_info=machine_info,
            polymer_info=polymer_info,
            mold_info=mold_info,
            parameter=baseline,
            feedback=feedback,
        )

        algorithm_result = _call_algorithms(algorithm_context)
        algorithm_recommendations = algorithm_result.get("recommendations", []) or []
        algorithm_sources = algorithm_result.get("algorithm_sources", {}) or {}

        # fail-fast 守卫
        if not algorithm_recommendations:
            _logger.warning(
                "[optimize] %s fail-fast: 无可用推荐 (algorithm_sources=%s)",
                interface_tag, algorithm_sources,
            )
            raise BizException(ERROR_OPERATION_FAILED, fail_fast_message)

        new_parameter_dict = _apply_recommendations_to_baseline(
            baseline=baseline,
            algorithm_recommendations=algorithm_recommendations,
        )
        suggestion_payload = _build_suggestion_payload(
            algorithm_recommendations=algorithm_recommendations,
            algorithm_sources=algorithm_sources,
            baseline=baseline,
        )
        return new_parameter_dict, suggestion_payload, algorithm_recommendations


__all__ = ["ParameterOptimizeService"]