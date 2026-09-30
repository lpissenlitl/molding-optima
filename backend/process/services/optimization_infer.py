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
from typing import Dict, Any, List, Optional, Tuple, TypedDict

from django.db import transaction as db_transaction

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT, ERROR_OPERATION_FAILED, ERROR_REQUIRED_FIELD
from process.models import (
    ProcessCondition,
    ProcessParameter,
    Recommendation,
    TuningRecord,
)
from process.engines.base_engine import EngineRegistry, Recommendation as EngineRecommendation
from process.engines.fuzzy import FuzzyEngine  # 用于字段命名约束（FIELD_NAME_ALIAS）

_logger = logging.getLogger(__name__)


# ============================================================================
# 模块级 lazy 引擎注册（避免重复注册 + 避免循环依赖）
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
# 算法接口契约（EngineContext schema）
#
# 设计（2026-09-30 确认）：
# - 虽然算法侧 AIEngineBase.recommend 接受 Dict[str, Any]（不限严格 schema），
#   但 Step 2 → Step 3 之间应有明确的契约文档，否则字段缺失只能运行时发现。
# - 使用 TypedDict：保留 Dict 调用风格 + 提供类型提示 + 0 运行成本。
# - _REQUIRED_CONTEXT_KEYS 是运行期 fail-fast 验证集合。
# ============================================================================
class EngineContext(TypedDict):
    """算法引擎输入 context 的标准格式

    由 Step 2 _build_engine_context 构造，Step 3 _call_engines 使用。

    字段语义：
    - machine: 设备信息（按 injection_index 选中的 InjectionUnit，含 HMI 范围字段）
    - polymer_abbreviation: 材料简称（RuleQueryService L1/L2 特异性匹配）
    - product_category: 产品类别（RuleQueryService L1/L3 特异性匹配）
    - process_parameter: 工艺参数（已翻译为算法侧命名，如 IL1/NT/CT）
    - feedback: 反馈信息（整体透传，不拆分）

    字段全部必填，但 polymer_abbreviation / product_category 允许 None（算法可走 L4 通用规则）。
    """
    machine: Dict[str, Any]
    polymer_abbreviation: Optional[str]
    product_category: Optional[str]
    process_parameter: Dict[str, Any]
    feedback: Dict[str, Any]


# 必需 key 集合（用于 _call_engines 入口验证；None 值也算“存在”）
_REQUIRED_CONTEXT_KEYS = frozenset(EngineContext.__annotations__.keys())


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
# Step 1 数据准备层 helper
#
# _to_full_dict(instance) ：ORM → 完整 dict（仅排除 ORM 关系字段）
#
# 设计边界：
# - Step 1 不做字段选择 / 重命名 / 裁剪，只做 ORM → dict 的转换。
# - 字段选择是 Step 2 (_build_engine_context) 的职责。
# - 仅排除 ORM 关系字段（ForeignKey / OneToOne 等），避免 ORM 对象嵌套到 dict。
# - ORM 元数据（id / created_at / updated_at / is_deleted / deleted_at）和业务字段
#   （parameter_no / param_source / seq_idx）保留在 dict 中，后续由 Step 2 决定是否裁剪。
# ============================================================================
def _to_full_dict(instance: Any) -> Dict[str, Any]:
    """ORM → 完整 dict（仅排除 ORM 关系字段，避免对象嵌套）。"""
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
    """按算法侧声明的字段命名约束（FIELD_NAME_ALIAS）做字段名翻译（业务 → 算法）

    Port-Adapter 模式：
    - 算法侧声明字段命名约定（FIELD_NAME_ALIAS，每个引擎各自声明）
    - 数据准备层按约束翻译（不感知业务语义）
    - 业务编排层只懂业务 dict

    翻译规则示例：
        'inj_pos_1' + spec={'inj_pos': 'IL'}       → 'IL1'         （前缀 + 数字后缀映射）
        'noz_temp'  + spec={'noz_temp': 'NT'}      → 'NT'          （完整字段名映射）
        'cool_t'    + spec={'cool_t': 'CT'}        → 'CT'          （完整字段名映射，注意 cool_t 不是“原样保留”）
        'met_lim_t' + spec={...完整业务映射...}    → 'met_lim_t'   （边界 case：算法侧未启用嫧胶延时）

    Args:
        params: 业务命名 dict
        field_spec: 算法侧声明的 prefix/完整字段名 → 算法 prefix/完整名映射

    Returns:
        翻译后的算法命名 dict（新 dict，不修改原对象）
    """
    if not field_spec:
        return dict(params)  # 无映射时快路径

    normalized: Dict[str, Any] = {}
    for key, value in params.items():
        # 优先 1：完整字段名映射（如 noz_temp → NT、vps_pos → VPTL）
        if key in field_spec:
            normalized[field_spec[key]] = value
            continue
        # 优先 2：前缀 + 数字后缀映射（如 inj_pos_1 → IL1、brl_temp_3 → BT3）
        # 注意：必须保证后缀是纯数字，避免 noz_temp 被拆成 noz + temp
        prefix, sep, suffix = key.rpartition('_')
        if sep and suffix.isdigit() and prefix in field_spec:
            new_key = f"{field_spec[prefix]}{suffix}"  # 直接拼接算法 prefix + 序号
        else:
            new_key = key  # 无映射或拆错位置，原样保留
        normalized[new_key] = value
    return normalized


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
        # Step 0: feedback 防御性校验
        self._validate_feedback(feedback)

        # ---------- Step 1: 构建基准参数（反查 + ORM→dict 标准化 + baseline 构建）----------
        condition_orm, parent_param_orm = self._resolve_parent(
            condition_id=condition_id,
            parent_seq_idx=parent_seq_idx,
        )
        parameter_data = _to_full_dict(parent_param_orm)
        baseline = self._build_baseline(
            parameter_data=parameter_data,
            user_override=parameter,
        )

        # ---------- Step 2: 构造算法 context（build condition 在内部） ----------
        engine_context = self._build_engine_context(
            condition=condition_orm,
            parameter=baseline,
            feedback=feedback,
        )
        
        # ---------- Step 3: 调用已注册算法引擎（纯调用，不查 DB） ----------
        engine_result = self._call_engines(engine_context)
        engine_recommendations = engine_result.get("recommendations", []) or []
        engine_sources = engine_result.get("engine_sources", {}) or {}

        # fail-fast 守卫：算法未给出推荐时拒绝创建空 round
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
        # Step 5 入口一次性从 feedback 提取（贴近使用方，不跨步共享）
        defect_feedbacks = feedback.get("defect", []) or []
        tuning_result = feedback.get("tuning_result")
        with db_transaction.atomic():
            # 5.1 更新上一轮 TuningRecord（缺陷反馈 + 试模结果）
            self._update_previous_tuning_record(
                parent_param=parent_param_orm,
                defect_feedbacks=defect_feedbacks,
                tuning_result=tuning_result,
            )

            # 5.2 更新上一轮 Recommendation.is_adopted（训练标签）
            self._update_previous_recommendation_is_adopted(
                parent_param=parent_param_orm,
                tuning_result=tuning_result,
            )

            # 5.3 创建新 ProcessParameter
            new_param = self._create_new_parameter(
                condition=condition_orm,
                parent_param=parent_param_orm,
                parameters_dict=new_parameter_dict,
            )

            # 5.4 创建新 TuningRecord（pending 状态，等待下次反馈）
            self._create_new_tuning_record(
                new_param=new_param,
                parent_param=parent_param_orm,
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
            if d.get("keyword_name") is None:
                raise BizException(
                    ERROR_REQUIRED_FIELD,
                    f"第 {i} 项缺陷未选择缺陷类型（keyword_name 必填）",
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
        """Step 1 —— 反查 condition + parent_param（两者必须同时存在）

        使用 select_related + prefetch_related 预加载：
        - injection_machine / polymer / mold（FK 一级，select_related）
        - injection_machine__injection_units（FK 二级，prefetch_related）
          → _build_engine_context 按 injection_index 选 InjectionUnit 时避免 N+1
        """
        try:
            condition = (
                ProcessCondition.objects
                .select_related('injection_machine', 'polymer', 'mold')
                .prefetch_related('injection_machine__injection_units')
                .get(id=condition_id)
            )
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
        parameter_data: Dict[str, Any],
        user_override: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Step 1 —— 构建 baseline（编排方法：纯 dict 操作）

        接收 dict 输入，支持多种来源：
        - ORM 序列化后的 parameter_data（来自 _to_full_dict）
        - 前端直接传入的 parameter_data（纯参数）
        - 其他业务场景传入的 dict

        不查 DB——数据访问由 infer() 完成。
        """
        baseline = dict(parameter_data)

        if user_override:
            # 用户手动修改覆盖 baseline（仅覆盖显式提供的字段）
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

    # ---------- Step 3 实现：调用已注册算法引擎 ----------

    def _call_engines(self, context: EngineContext) -> Dict[str, Any]:
        """Step 3 —— 纯调用已注册引擎，不查 DB

        Args:
            context: 算法入参（5 字段 schema，见 EngineContext）
                字段齐全性在本函数入口校验，避免转发到引擎后才报错。

        Returns:
            {
                'recommendations': [...],       # 合并后的扁平推荐列表
                'engine_sources': {name: [...]},  # 各引擎输出（用于 source_type 决策）
                'best_recommendation': {...} | None,
            }

        TODO（后续迭代）：
        - trend 后处理（worsening *0.5 / improving *1.2 / stable 1.0）
        - 多引擎同参数合并（按 confidence 取最高）
        """
        # ---- 入口验证：5 字段 schema 完整性 ----
        # 不齐全直接返回空（让调用方 fail-fast 在 278-285 报 BizException）
        if not context:
            _logger.warning("[optimization_infer] _call_engines context 为空")
            return self._empty_engine_result()
        missing = _REQUIRED_CONTEXT_KEYS - set(context.keys())
        if missing:
            _logger.warning(
                "[optimization_infer] _call_engines context 缺字段: %s", missing,
            )
            return self._empty_engine_result()

        engines = EngineRegistry.get_engines_by_priority(
            context=context,
            prefer_engines=None,
        )
        if not engines:
            _logger.info("[optimization_infer] 无可用引擎")
            return self._empty_engine_result()

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

    @staticmethod
    def _empty_engine_result() -> Dict[str, Any]:
        """统一空返回结构（避免在 _call_engines 里重复字面量）"""
        return {
            "recommendations": [],
            "engine_sources": {},
            "best_recommendation": None,
        }

    def _build_engine_context(
        self,
        condition: ProcessCondition,
        parameter: Dict[str, Any],
        feedback: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Step 2 —— 构造算法引擎输入 context（业务 → 算法 翻译边界）

        边界职责（Port-Adapter 模式）：
        - 字段选择（业务多 → 算法少）
        - 字段名翻译（业务命名 → 算法命名，按 FuzzyEngine.FIELD_NAME_ALIAS）
        - 上下文组装（machine / process_parameter / feedback / 规则查询参数）

        业务编排层（Step 1）只懂业务；数据准备层（Step 2）是唯一翻译边界；
        算法层（Step 3）是纯函数，不该懂业务命名。

        与 parameter_init 的关键差异：
        - parameter_init: mold_info + polymer_info + machine_info 完整提取 → 初始工艺推理
        - optimization_infer: machine（InjectionUnit HMI 范围）+ baseline + defect → 缺陷修正推理
        """
        machine = self._extract_machine_unit(condition)
        polymer_abbreviation = (
            condition.polymer.abbreviation
            if condition.polymer else None
        )
        product_category = (
            condition.mold.product_category
            if condition.mold else None
        )

        # 数据准备层职责：业务命名 → 算法命名（按算法约束翻译）
        # 当前 FuzzyEngine.FIELD_NAME_ALIAS 为空 dict，业务命名 == 算法命名 → no-op
        algorithm_params = _normalize_field_name_by_spec(
            parameter, FuzzyEngine.FIELD_NAME_ALIAS,
        )

        context: Dict[str, Any] = {
            'machine': machine,
            'polymer_abbreviation': polymer_abbreviation,
            'product_category': product_category,
            'process_parameter': algorithm_params,
            'feedback': feedback,
        }

        return context

    @staticmethod
    def _extract_machine_unit(condition: ProcessCondition) -> Dict[str, Any]:
        """按 condition.injection_index 从 InjectionMoldingMachine.injection_units 选一台

        返回该 InjectionUnit 的完整字段 dict（不含 FK），供算法自挑 HMI 范围字段。
        未找到则返回 {}（不抛错，由下游 fail-fast 守卫阻断）。
        """
        machine = condition.injection_machine
        if machine is None:
            return {}

        injection_index = condition.injection_index or 0
        injection_units = list(machine.injection_units.all())
        if injection_index < len(injection_units):
            return _to_full_dict(injection_units[injection_index])

        _logger.warning(
            "[optimization_infer] injection_index=%s 超出 machine(id=%s) 的 injection_units（共 %s 个）",
            injection_index, machine.id, len(injection_units),
        )
        return {}

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