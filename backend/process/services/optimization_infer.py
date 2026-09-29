"""工艺优化 infer 服务（调用链路编排层，不含算法实现）

对应接口：POST /api/processes/optimization/infer/

职责：Step 1 反查 parent → Step 2 构建基线 → Step 3 调算法 → Step 4 原子落库

设计要点：
- infer 只处理算法优化（人工调整走 manual-adjust 接口）
- 算法侧是接口契约：输入 context，输出 List[Recommendation]，算法实现对本服务透明
- 3 场景调用逻辑一致（基本调参/自动回撤/手动修改），仅 feedback 内容不同
- is_adopted 自动维护：下一轮 ineffective 时改 False
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

from django.db import transaction as db_transaction

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT, ERROR_OPERATION_FAILED, ERROR_REQUIRED_FIELD
from process.models import (
    ProcessCondition,
    ProcessParameter,
    Recommendation,
    TuningRecord,
)
from process.engines.base_engine import EngineRegistry, Recommendation as EngineRecommendation
from process.services.tuning import TuningService

_logger = logging.getLogger(__name__)


# ============================================================================
# 模块级 lazy 引擎注册
#
# 设计原因：
# - 不再走中间层（RecommendationService），编排层直接问 EngineRegistry
# - lazy + 幂等：避免重复注册 + 避免循环依赖（模块被 services.__init__ 预加载）
# ============================================================================
_engines_registered = False


def _ensure_engines_registered() -> None:
    """模块级 lazy 触发引擎注册（幂等）。"""
    global _engines_registered
    if _engines_registered:
        return
    try:
        from process.engines.fuzzy import FuzzyEngine
        if not EngineRegistry.get_engine("fuzzy"):
            EngineRegistry.register("fuzzy", FuzzyEngine())
    except Exception as e:  # noqa: BLE001
        _logger.warning("[optimization_infer] FuzzyEngine 注册失败: %s", e)
    _engines_registered = True


# ============================================================================
# 参数分类（按 prefix 分组，与 Recommendation.recommendations 对齐）
# ============================================================================
# 用于将算法的扁平推荐列表转换为前端 SuggestionGroup 结构
# 单一数据源：新增分类只需在此处加一行
#
# 匹配规则：
# - 带下划线结尾的项 → 按 startswith 前缀匹配（如 inj_pressure → 注射参数）
# - 不带下划线结尾的项 → 按 == 精确字段名匹配（如 noz_temp 本就是完整字段名）
#
# 历史遗留说明（业务合理，不需修复）：
# - brl_temp_ 和 noz_temp 都映射到"料筒温度"：料筒多段（brl_temp_1/2/3/...）
#   与喷嘴（noz_temp）是同一业务组，但参数体系在历史上是分开命名的。
# - pre_met_decomp_ 和 pst_met_decomp_ 图标相同：前后松退在分类名上
#   是不同的（"熔胶前/后松退"），但物理动作相同（解压一下），故图标复用。
_PARAM_CATEGORY_RULES = (
    # ---- 前缀规则（带下划线结尾）----
    ('inj_', ('注射参数', 'mdi:speedometer')),
    ('hold_', ('保压参数', 'mdi:gauge')),
    ('met_', ('熔胶参数', 'mdi:screw-machine-flat-top')),
    ('vps_', ('VP 切换', 'mdi:swap-vertical')),
    ('brl_temp_', ('料筒温度', 'mdi:thermometer')),
    ('cool_', ('冷却参数', 'mdi:snowflake')),
    ('pre_met_decomp_', ('熔胶前松退', 'mdi:arrow-collapse')),
    ('pst_met_decomp_', ('熔胶后松退', 'mdi:arrow-collapse')),
    # ---- 精确字段名规则（不带下划线）----
    # noz_temp 是单字段而非前缀（不需跟段号），故采用精确匹配
    ('noz_temp', ('料筒温度', 'mdi:thermometer')),
)


def _categorize_param(param_name: str) -> Tuple[str, str]:
    """参数名 → (category, icon)

    匹配顺序：
    1. 带下划线结尾的规则项 → 按 startswith 前缀匹配
    2. 不带下划线结尾的规则项 → 按 == 精确匹配
    3. 未匹配则归类为 "其他参数"
    """
    for match_key, (category, icon) in _PARAM_CATEGORY_RULES:
        if match_key.endswith('_'):
            # 前缀匹配（仅对带下划线结尾的规则）
            if param_name.startswith(match_key):
                return category, icon
        else:
            # 精确匹配（仅对不带下划线结尾的规则）
            if param_name == match_key:
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
# snapshot 字段排除集（用于 _snapshot_parameter）
#
# 背景：原实现只排除 id/时间戳/FK，会把 param_source / parameter_no / seq_idx
#       等业务字段也纳入 snapshot。这些字段在 _create_new_parameter 里会被
#       **parameters_dict 展开，导致与显式传入的同名 kwarg 冲突（如
#       param_source='system_inferred'），运行时报 TypeError。
#
# 原则：snapshot 只包含「标量工艺字段」（inj_*/hold_*/met_*/...），业务字段
#       （编号/来源/序号）由 Model/Service 层自行处理。
# ============================================================================

_NON_SNAPSHOT_FIELDS = frozenset({
    # 元数据
    "id", "created_at", "updated_at", "deleted", "deleted_at", "is_deleted",
    # 业务字段（snapshot 外另行处理）
    "parameter_no",       # 业务编号 → Model 层自动生成（PP-{YYYYMM}-{NNNN}）
    "param_source",       # 参数来源 → _create_new_parameter 显式传入
    "seq_idx",            # 序列序号 → Model.save() 自动分配
})


# “无缺陷” sentinel keyword 名称（与前端 constants/special-keywords.DEFECTFREE_KEYWORD_NAME 对齐）
# 业务定义：选DEFECTFREE 时 level / position 均可不填（语义为“本次试模无缺陷”，不需描述）
_DEFECTFREE_KEYWORD_NAME = "DEFECTFREE"


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
        # 触发模块级 lazy 引擎注册（幂等）
        _ensure_engines_registered()

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
        # Step 0: feedback 防御性校验（与前端 validateFeedback 是同一套约束镜像）
        self._validate_feedback(feedback)
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

        # ---------- Step 3: 直接调用算法引擎（无中间层） ----------
        # Step 3a: 构造算法 context（不上 DB，所需数据已在 Step 1 拿齐）
        engine_context = self._build_engine_context(
            condition=condition,
            parent_param=parent_param,
            defect_feedbacks=defect_feedbacks,
        )
        # Step 3b: 调用已注册引擎（纯调用，不查 DB）
        engine_result = self._call_engines(engine_context)
        engine_recommendations = engine_result.get("recommendations", []) or []
        engine_sources = engine_result.get("engine_sources", {}) or {}

        # Step 3.5: fail-fast 守卫 —— 算法未给出推荐时拒绝创建空 round
        # （工艺参数只由算法生成，无推荐 = 无效 round；避免前端误以为成功）
        if not engine_recommendations:
            _logger.warning(
                "[optimization_infer] fail-fast: 无可用推荐 "
                "(condition_id=%s, parent_seq_idx=%s, engine_sources=%s)",
                condition_id, parent_seq_idx, engine_sources,
            )
            raise BizException(
                ERROR_OPERATION_FAILED,
                "推荐算法暂不可用，请稍后重试或联系管理员",
            )

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

    @staticmethod
    def _validate_feedback(feedback: Dict[str, Any]) -> None:
        """Step 0 —— feedback 防御性校验（与前端 validateFeedback 是同一套约束镜像）

        Raises:
            BizException(ERROR_REQUIRED_FIELD): 字段缺失
        """
        defects = feedback.get("defect") or []
        if not isinstance(defects, list) or len(defects) == 0:
            raise BizException(
                ERROR_REQUIRED_FIELD,
                "请填写缺陷反馈信息",
            )

        for i, d in enumerate(defects, 1):
            if not isinstance(d, dict):
                raise BizException(
                    ERROR_REQUIRED_FIELD,
                    f"第 {i} 项缺陷格式错误：应为对象",
                )
            if d.get("keyword_id") is None:
                raise BizException(
                    ERROR_REQUIRED_FIELD,
                    f"第 {i} 项缺陷未选择缺陷类型（keyword_id 必填）",
                )
            is_defect_free = d.get("keyword_name") == _DEFECTFREE_KEYWORD_NAME
            if not is_defect_free:
                if not d.get("level"):
                    raise BizException(
                        ERROR_REQUIRED_FIELD,
                        f"第 {i} 项缺陷未选择缺陷程度",
                    )
                if not d.get("position"):
                    raise BizException(
                        ERROR_REQUIRED_FIELD,
                        f"第 {i} 项缺陷未填写缺陷位置",
                    )

    def _resolve_parent(
        self,
        condition_id: int,
        parent_seq_idx: int,
    ) -> Tuple[ProcessCondition, ProcessParameter]:
        """Step 1 —— 反查 condition + parent_param（两者必须同时存在）"""
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
        """Step 2 —— 构建算法输入基线（user_override > parent_param）"""
        baseline = self._snapshot_parameter(parent_param)

        if user_override:
            # 用户手动修改覆盖基线（仅覆盖显式提供的字段）
            for key, value in user_override.items():
                if value is not None:
                    baseline[key] = value

        return baseline

    @staticmethod
    def _snapshot_parameter(parameter: ProcessParameter) -> Dict[str, Any]:
        """从 ProcessParameter 取标量工艺字段（排除元数据与业务字段，详见 _NON_SNAPSHOT_FIELDS）"""
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

    # ---------- Step 3 实现：直接调用算法引擎（原本是 RecommendationService 的职责） ----------

    def _call_engines(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3b —— 纯调用已注册引擎，不查 DB

        设计：调用方负责构造 context，本方法只负责『调引擎 + 汇总输出』。
        好处：
        - 单元测试可直接传 mock context，无需 setup DB
        - context 字段名是隐式契约，但好处是调用方完全控制上下文内容

        Returns:
            {
                'recommendations': [...],       # 合并后的扁平推荐列表
                'engine_sources': {name: [...]},  # 各引擎输出（用于 source_type 决策）
                'best_recommendation': {...} | None,
            }
        """
        if not context:
            return {
                "recommendations": [],
                "engine_sources": {},
                "best_recommendation": None,
            }

        engines = EngineRegistry.get_engines_by_priority(
            context=context,
            prefer_engines=None,
        )
        if not engines:
            _logger.info("[optimization_infer] 无可用引擎")
            return {
                "recommendations": [],
                "engine_sources": {},
                "best_recommendation": None,
            }

        all_recommendations: List[EngineRecommendation] = []
        engine_sources: Dict[str, List[Dict[str, Any]]] = {}
        for engine in engines:
            try:
                recs = engine.recommend(context) or []
            except Exception as e:  # noqa: BLE001
                _logger.warning(
                    "[optimization_infer] 引擎 %s 推理失败: %s",
                    engine.engine_name, e,
                )
                recs = []
            engine_sources[engine.engine_name] = [r.to_dict() for r in recs]
            all_recommendations.extend(recs)

        # TODO: trend 后处理（worsening *0.5 / improving *1.2 / stable 1.0）
        # TODO: 多引擎同参数合并（按 confidence 取最高）
        merged = [r.to_dict() for r in all_recommendations]

        return {
            "recommendations": merged,
            "engine_sources": engine_sources,
            "best_recommendation": merged[0] if merged else None,
        }

    def _build_engine_context(
        self,
        condition: ProcessCondition,
        parent_param: ProcessParameter,
        defect_feedbacks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Step 3a —— 构造算法引擎输入 context

        不查 DB—— condition / parent_param 由调用方传入。

        iteration_trend 含义：
        - improving: 持续改善，继续当前方向
        - worsening: 持续恶化，需回退或换策略
        - stable: 改善/恶化交替，陷入僵局
        - final: 已达终态
        """
        tuning_history = (
            TuningRecord.objects.filter(process_parameter=parent_param)
            .order_by('-created_at')[:50]
        )

        # 分析迭代趋势（仅取 parent_param 的调参记录）
        trend = TuningService.analyze_iteration_trend(parent_param)
        trend_dict = {
            'trend': trend.trend,
            'improving_count': trend.improving,
            'worsening_count': trend.worsening,
            'unchanged_count': trend.unchanged,
            'last_result': trend.last_result,
            'recommendation': trend.recommendation,
        }

        context: Dict[str, Any] = {
            'process_condition': self._serialize_condition(condition),
            # current_parameters 是算法关键输入：体现当前参数的高低水平，
            # 算法需以此为起点计算调整量
            'current_parameters': self._serialize_parameter(parent_param),
            'defect_feedbacks': defect_feedbacks,
            'tuning_history': [self._serialize_record(r) for r in tuning_history],
            'iteration_trend': trend_dict,
        }

        if condition.injection_machine:
            context['machine'] = self._get_machine_capabilities(condition.injection_machine)

        return context

    @staticmethod
    def _serialize_condition(condition: ProcessCondition) -> Dict[str, Any]:
        return {
            'id': condition.id,
            'condition_no': condition.condition_no,
            'status': condition.status,
            'origin_type': condition.origin_type,
            'mold_id': condition.mold_id,
            'injection_machine_id': condition.injection_machine_id,
            'polymer_id': condition.polymer_id,
            'shot_index': condition.shot_index,
            'injection_index': condition.injection_index,
        }

    @staticmethod
    def _serialize_parameter(parameter: ProcessParameter) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for field in parameter._meta.fields:
            if field.name.startswith('_') or field.name in ('id', 'created_at', 'updated_at'):
                continue
            value = getattr(parameter, field.name, None)
            if value is not None:
                data[field.name] = value
        return data

    @staticmethod
    def _serialize_record(record: TuningRecord) -> Dict[str, Any]:
        return {
            'id': record.id,
            'defect_feedbacks': record.defect_feedbacks,
            'result': record.result,
            'adjustments': record.adjustments,
            'previous_parameter': record.previous_parameter,
            'created_at': record.created_at.isoformat() if record.created_at else None,
        }

    @staticmethod
    def _get_machine_capabilities(machine) -> Dict[str, Any]:
        return {
            'id': machine.id,
            'name': getattr(machine, 'name', str(machine)),
            'capabilities': {},  # TODO: 后续根据实际设备模型完善
        }

    @staticmethod
    def _apply_recommendations_to_baseline(
        baseline: Dict[str, Any],
        engine_recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Step 4a —— 用推荐值覆盖基线字段（仅覆盖基线中存在的字段）"""
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
        """Step 4b —— 扁平推荐按 category 分组，构建 SuggestionGroup（source_type 取最高优先级引擎）"""
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
        """更新上一轮 TuningRecord（缺陷反馈 + 试模结果；取最新一条）"""
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
        """下一轮 ineffective 时将上一轮 Recommendation.is_adopted 改为 False（训练标签自动维护）"""
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
        """Step 5.3 —— 创建新 ProcessParameter（param_source='system_inferred'，seq_idx 由 Model 自动分配）"""
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
        """Step 5.4 —— 创建新 TuningRecord（pending 状态，previous_parameter 自包含快照）"""
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
        """Step 5.5 —— 创建新 Recommendation（is_adopted=True，下一轮 ineffective 自动改 False）"""
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