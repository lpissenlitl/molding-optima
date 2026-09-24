"""molding-optima 工艺优化 infer 服务

对应接口：
- POST /api/processes/optimization/infer/

职责（**调用链路编排层**，不含算法实现）：
  Step 1: 入口适配   —— condition_id + parent_seq_idx 反查 parent_param
  Step 2: 数据准备   —— parent_param.parameters 作为基线，可选 parameter 覆盖
  Step 3: 推理算法   —— 委托给 recommendation_service.get_recommendations()（接口契约）
  Step 4: 落库       —— ProcessParameter + TuningRecord + Recommendation 原子事务

设计要点：
- infer 只处理算法优化（人工调整走 manual-adjust 接口）
- 算法侧是接口契约：输入 context（condition + defect + parameter + tuning_result），
  输出 List[Recommendation]（param_name + recommended_value）。算法侧具体实现
  （fuzzy / rule_miner / llm）对本服务透明
- 3 场景调用逻辑一致（基本调参 / 自动回撤 / 手动修改），仅 feedback 内容不同
- is_adopted 是自动维护的训练标签：下一轮 ineffective 时自动改 False
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

from django.db import transaction as db_transaction

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT
from process.models import (
    ProcessCondition,
    ProcessParameter,
    Recommendation,
    TuningRecord,
)
from process.services.recommendation_service import ProcessRecommendationService

_logger = logging.getLogger(__name__)


# ============================================================================
# 参数分类（按 prefix 分组，与 Recommendation.recommendations 对齐）
# ============================================================================
# 用于将算法的扁平推荐列表转换为前端 SuggestionGroup 结构
# 单一数据源：新增分类只需在此处加一行

_PARAM_CATEGORY_MAP = (
    ('inj_', ('注射参数', 'mdi:speedometer')),
    ('hold_', ('保压参数', 'mdi:gauge')),
    ('met_', ('熔胶参数', 'mdi:screw-machine-flat-top')),
    ('vps_', ('VP 切换', 'mdi:swap-vertical')),
    ('brl_temp_', ('料筒温度', 'mdi:thermometer')),
    ('noz_temp', ('料筒温度', 'mdi:thermometer')),
    ('cool_', ('冷却参数', 'mdi:snowflake')),
    ('pre_met_decomp_', ('熔胶前松退', 'mdi:arrow-collapse')),
    ('pst_met_decomp_', ('熔胶后松退', 'mdi:arrow-collapse')),
)


def _categorize_param(param_name: str) -> Tuple[str, str]:
    """参数名 → (category, icon)

    未匹配到前缀则归类为 "其他参数"。
    """
    for prefix, (category, icon) in _PARAM_CATEGORY_MAP:
        if param_name.startswith(prefix) or param_name == prefix.rstrip('_'):
            return category, icon
    return '其他参数', 'mdi:cog-outline'


def _direction_from_delta(before: Optional[float], after: Optional[float]) -> Optional[str]:
    """根据 before/after 数值推断调整方向

    边界处理：None / 等值时返回 None。
    """
    if before is None or after is None:
        return None
    if after > before:
        return 'increase'
    if after < before:
        return 'decrease'
    return 'hold'


# ============================================================================
# infer 服务（主类）
# ============================================================================

class OptimizationInferService:
    """工艺优化 infer 服务 —— 调用链路编排

    设计约束：
    - 算法侧是接口契约：本服务只负责编排，不实现具体推理
    - 所有 Step 在一个原子事务内完成（避免半成品落库）
    """

    def __init__(self):
        # 复用现有推荐服务（已注册 FuzzyEngine / RuleMiner / LLM 等）
        self._recommendation_service = ProcessRecommendationService()

    # ---------- 公开入口 ----------

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
            parameter: 手动修改覆盖（可选，结构化 dict）
            feedback: 反馈信息（嵌套 dict，可选）

        Returns:
            {
                "new_parameter": {...},          # 新工艺参数（含 parameter_id）
                "suggestion": {
                    "source_type": str,
                    "recommendation_id": int,
                    "groups": [
                        {"category": str, "icon": str, "items": [...]}
                    ]
                }
            }
        """
        feedback = feedback or {}
        defect_feedbacks = feedback.get("defect", []) or []
        observations = feedback.get("observations", []) or []
        tuning_result = feedback.get("tuning_result")

        # ---------- Step 1: 反查 parent_param ----------
        condition, parent_param = self._resolve_parent(
            condition_id=condition_id,
            parent_seq_idx=parent_seq_idx,
        )

        # ---------- Step 2: 构建基线参数 ----------
        baseline = self._build_baseline(
            parent_param=parent_param,
            user_override=parameter,
        )

        # ---------- Step 3: 调用算法（接口契约） ----------
        engine_result = self._recommendation_service.get_recommendations(
            process_condition_id=condition_id,
            defect_feedbacks=defect_feedbacks,
        )
        engine_recommendations = engine_result.get("recommendations", []) or []
        engine_sources = engine_result.get("engine_sources", {}) or {}

        # ---------- Step 4: 应用推荐 → 新参数 + 建议展示 ----------
        new_parameter_dict = self._apply_recommendations_to_baseline(
            baseline=baseline,
            engine_recommendations=engine_recommendations,
        )
        suggestion_payload = self._build_suggestion_payload(
            engine_recommendations=engine_recommendations,
            engine_sources=engine_sources,
        )

        # ---------- Step 5: 原子事务落库 ----------
        with db_transaction.atomic():
            # 5.1 更新上一轮 TuningRecord（缺陷反馈 + 试模结果）
            self._update_previous_tuning_record(
                parent_param=parent_param,
                defect_feedbacks=defect_feedbacks,
                tuning_result=tuning_result,
            )

            # 5.2 更新上一轮 Recommendation.is_adopted（训练标签）
            self._update_previous_recommendation_is_adopted(
                parent_param=parent_param,
                tuning_result=tuning_result,
            )

            # 5.3 创建新 ProcessParameter
            new_param = self._create_new_parameter(
                condition=condition,
                parent_param=parent_param,
                parameters_dict=new_parameter_dict,
            )

            # 5.4 创建新 TuningRecord（pending 状态，等待下次反馈）
            self._create_new_tuning_record(
                new_param=new_param,
                parent_param=parent_param,
                defect_feedbacks=defect_feedbacks,
            )

            # 5.5 创建新 Recommendation
            recommendation = self._create_new_recommendation(
                new_param=new_param,
                engine_recommendations=engine_recommendations,
                engine_sources=engine_sources,
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

    # ---------- Step 实现 ----------

    def _resolve_parent(
        self,
        condition_id: int,
        parent_seq_idx: int,
    ) -> Tuple[ProcessCondition, ProcessParameter]:
        """Step 1 —— 反查 condition + parent_param

        业务约束：
        - condition_id 必须存在
        - parent_seq_idx 必须在该 condition 下能找到对应的 ProcessParameter
        """
        try:
            condition = ProcessCondition.objects.get(id=condition_id)
        except ProcessCondition.DoesNotExist as exc:
            raise BizException(
                ERROR_DATA_NOT_FOUND,
                f"工艺条件不存在: id={condition_id}",
            ) from exc

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

    def _build_baseline(
        self,
        parent_param: ProcessParameter,
        user_override: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Step 2 —— 构建算法输入基线

        优先级：user_override > parent_param 字段值
        基线是算法的"当前工艺"，算法返回的是"调整后的工艺"。
        """
        baseline = self._snapshot_parameter(parent_param)

        if user_override:
            # 用户手动修改覆盖基线（仅覆盖显式提供的字段）
            for key, value in user_override.items():
                if value is not None:
                    baseline[key] = value

        return baseline

    @staticmethod
    def _snapshot_parameter(parameter: ProcessParameter) -> Dict[str, Any]:
        """从 ProcessParameter 构建参数快照 dict

        仅包含标量工艺字段（inj_*/hold_*/met_*/...），不包含元数据（id/created_at/...）
        """
        snapshot: Dict[str, Any] = {}
        for field in parameter._meta.fields:
            name = field.name
            # 排除元数据字段与外键
            if name in {"id", "created_at", "updated_at", "deleted", "deleted_at", "is_deleted"}:
                continue
            if field.is_relation:
                continue
            value = getattr(parameter, name, None)
            if value is not None:
                snapshot[name] = value
        return snapshot

    @staticmethod
    def _apply_recommendations_to_baseline(
        baseline: Dict[str, Any],
        engine_recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Step 4a —— 应用算法推荐到基线，得到新工艺参数

        算法侧 Recommendation 格式：
            {
                "param": str,            # 参数名
                "current_value": float,  # 当前值
                "recommended_value": float,  # 推荐值
                "confidence": float,
                "reason": str,
                "source": str,
            }

        应用规则：用推荐值覆盖对应字段（仅当字段在基线中存在）。
        """
        new_parameter = dict(baseline)
        for rec in engine_recommendations:
            param_name = rec.get("param")
            recommended_value = rec.get("recommended_value")
            if param_name and param_name in new_parameter and recommended_value is not None:
                new_parameter[param_name] = recommended_value
        return new_parameter

    def _build_suggestion_payload(
        self,
        engine_recommendations: List[Dict[str, Any]],
        engine_sources: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Step 4b —— 构建前端 Suggestion 展示对象

        转换链：engine Recommendation (扁平) → 按 category 分组 → SuggestionGroup

        source_type 选取策略：
        - 取优先级最高的引擎名（expert > fuzzy > rule_miner > llm > ...）
        - 若无推荐则 source_type='none'
        """
        source_type = self._resolve_primary_source(engine_sources) or "none"

        if not engine_recommendations:
            return {
                "source_type": source_type,
                "groups": [],
            }

        # 按 category 分组
        grouped: Dict[str, Dict[str, Any]] = {}
        for rec in engine_recommendations:
            param_name = rec.get("param", "")
            category, icon = _categorize_param(param_name)

            if category not in grouped:
                grouped[category] = {"category": category, "icon": icon, "items": []}

            grouped[category]["items"].append({
                "description": self._build_description(rec),
                "direction": _direction_from_delta(
                    rec.get("current_value"),
                    rec.get("recommended_value"),
                ),
                "rule_refs": self._extract_rule_refs(rec),
            })

        return {
            "source_type": source_type,
            "groups": list(grouped.values()),
        }

    @staticmethod
    def _resolve_primary_source(engine_sources: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        """选取主要算法来源

        优先级顺序与 EngineRegistry._priorities 对齐。
        返回引擎 subtype（fuzzy / rule_miner / llm ...）。
        """
        priority_order = ('expert', 'fuzzy', 'rule_miner', 'llm', 'doe', 'ga')
        for subtype in priority_order:
            if engine_sources.get(subtype):
                return subtype
        # 兜底：取任意一个非空源
        for subtype, recs in engine_sources.items():
            if recs:
                return subtype
        return None

    @staticmethod
    def _build_description(rec: Dict[str, Any]) -> str:
        """构造建议文本

        优先使用 reason，否则用 "调整 {param} {direction} → {value}" 格式。
        """
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

    @staticmethod
    def _extract_rule_refs(rec: Dict[str, Any]) -> List[str]:
        """提取规则引用

        当前算法侧 Recommendation 无规则引用字段，预留接口。
        """
        refs = rec.get("rule_refs") or []
        if isinstance(refs, list):
            return [str(r) for r in refs]
        return []

    # ---------- 落库实现 ----------

    @staticmethod
    def _update_previous_tuning_record(
        parent_param: ProcessParameter,
        defect_feedbacks: List[Dict[str, Any]],
        tuning_result: Optional[str],
    ) -> None:
        """更新上一轮 TuningRecord（缺陷反馈 + 试模结果）

        - 业务层保证：每个 parameter 至少有 1 个 TuningRecord（1:1）
        - 若有多条，取最新一条（业务约定）
        """
        previous_record = (
            TuningRecord.objects
            .filter(process_parameter=parent_param)
            .order_by("-created_at")
            .first()
        )
        if previous_record is None:
            _logger.warning(
                "[infer] 父参数缺少 TuningRecord: parameter_id=%s（业务层应保证 1:1）",
                parent_param.id,
            )
            return

        if defect_feedbacks:
            previous_record.defect_feedbacks = defect_feedbacks

        if tuning_result in ("effective", "ineffective"):
            # mapping: tuning_result → TuningRecord.result
            previous_record.result = {
                "effective": "improved",
                "ineffective": "worse",
            }[tuning_result]

        previous_record.save()

    @staticmethod
    def _update_previous_recommendation_is_adopted(
        parent_param: ProcessParameter,
        tuning_result: Optional[str],
    ) -> None:
        """更新上一轮 Recommendation.is_adopted（训练标签）

        业务规则（原则 9）：
        - infer 创建 Recommendation 时默认 is_adopted=True
        - 下一轮 tuning_result='ineffective' → 改为 False（训练标签）
        - 下一轮 tuning_result='effective' 或 null → 保持 True
        """
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

    @staticmethod
    def _create_new_parameter(
        condition: ProcessCondition,
        parent_param: ProcessParameter,
        parameters_dict: Dict[str, Any],
    ) -> ProcessParameter:
        """Step 5.3 —— 创建新 ProcessParameter

        - parent_param：指向旧参数（保留版本树）
        - param_source='system_inferred'（来自系统推理）
        - seq_idx：由 Model.save() 自动分配（condition 内全局递增）
        """
        return ProcessParameter.objects.create(
            process_condition=condition,
            parent_param=parent_param,
            param_source="system_inferred",
            **parameters_dict,
        )

    @staticmethod
    def _create_new_tuning_record(
        new_param: ProcessParameter,
        parent_param: ProcessParameter,
        defect_feedbacks: List[Dict[str, Any]],
    ) -> TuningRecord:
        """Step 5.4 —— 创建新 TuningRecord

        - 状态：pending（等待试模反馈）
        - previous_parameter：旧参数的快照（用于训练样本自包含）
        - defect_feedbacks：当前轮的缺陷反馈（前置传递）
        """
        previous_parameter_snapshot = (
            OptimizationInferService._snapshot_parameter(parent_param)
        )
        return TuningRecord.objects.create(
            process_parameter=new_param,
            defect_feedbacks=defect_feedbacks,
            result="pending",
            previous_parameter=previous_parameter_snapshot,
        )

    @staticmethod
    def _create_new_recommendation(
        new_param: ProcessParameter,
        engine_recommendations: List[Dict[str, Any]],
        engine_sources: Dict[str, List[Dict[str, Any]]],
    ) -> Recommendation:
        """Step 5.5 —— 创建新 Recommendation

        - source_type：来自主要算法（fuzzy_rule / rule_miner / llm / ...）
        - recommendations：扁平推荐列表（与 Model.recommendations JSONField 对齐）
        - is_adopted：默认 True（自动维护，下一轮 ineffective 时改 False）
        """
        source_type = (
            OptimizationInferService._resolve_primary_source(engine_sources)
            or "fuzzy_rule"
        )
        return Recommendation.objects.create(
            process_parameter=new_param,
            source_type=source_type,
            recommendations=engine_recommendations,
            is_adopted=True,
        )


__all__ = [
    "OptimizationInferService",
]