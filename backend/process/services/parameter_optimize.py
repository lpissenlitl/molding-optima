"""工艺优化 infer 服务（调用链路编排层，不含算法实现）

对外入口：
- infer(condition_id, parent_seq_idx, ...)  → POST /api/processes/algorithms/optimize/
- infer_from_provided(parameter, feedback, 三维上下文) —— 纯推理（不查库、不落库），
  **尚无 HTTP 路由**，目前仅测试与脚本直接调用

调用链（infer）：
Step 0 校验 feedback → Step 0.5 提取评价 → Step 1 装配上下文（只读）
→ Step 1b 合格态短路（只落库、不推理）→ Step 0b 入参契约校验
→ Step 2 纯推理 → Step 3 原子落库 → Step 4 组装响应

设计要点：
- is_adopted 自动维护：下一轮 ineffective 时改 False
- 写库点有两处：Step 1b（合格态：只写评价 + 手改参数）与 Step 3（正常轮次：全量落库）；
  用户手改的工艺参数写回父记录，与新建轮次同生共死（详见 _sync_user_modified_parameter）

代码组织：helper 全部为模块顶层函数（不依赖 self），类内只有 infer /
infer_from_provided 两个公开入口 + 静态方法 _infer_kernel（两个入口共用）。
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, TypedDict

from django.db import transaction as db_transaction

from extensions.exceptions import (
    BizException,
    ERROR_DATA_INVALID,
    ERROR_DATA_NOT_FOUND,
    ERROR_ILLEGAL_ARGUMENT,
    ERROR_OPERATION_FAILED,
    ERROR_REQUIRED_FIELD,
)
from process.models import (
    ProcessCondition,
    ProcessParameter,
    Recommendation,
    TuningRecord,
)
from process.algorithms.base import AlgorithmRegistry
from process.algorithms.fuzzy import (
    field_names,  # 命名契约：业务字段名 ↔ 算法字段名（双向映射，契约层唯一真相源）
)
from process.algorithms.fuzzy.over_limit import (
    detect_blocking_over_limits,  # 越限分层口径（device = 设备安全红线 ⇒ 阻断）
)
from process.algorithms.fuzzy.specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OPTIMIZE_POLYMER_INFO_FIELDS,
    OPTIMIZE_MOLD_INFO_FIELDS,
    audit_feedback_defects,  # 缺陷反馈校验（契约层）
    OptimizeDataValidator,  # 入参契约校验器
    resolve_param_limits,  # 机台物理上限 → {参数族: 上限}
)  # 算法入参契约（字段字典）—— service 层按此白名单提取，不传全量 ORM 字段
from .tuning import (  # tuning_result → TuningRecord.result 映射 + 参数快照/训练样本组装（均为唯一真相源）
    NON_SNAPSHOT_FIELDS,
    TUNING_RESULT_MAP,
    build_adjustments,
    is_qualified_result,
    snapshot_parameter,
)

_logger = logging.getLogger(__name__)


# 引擎在各算法模块内注册（`fuzzy/engine.py` / `empirical/empirical_algorithm.py`），
# 由 `process/algorithms/__init__.py` 的 import 链自动触发。


class AlgorithmContext(TypedDict):
    """算法引擎输入 context 的标准格式

    由 Step 2 _compose_algorithm_context 构造，Step 3 _call_algorithms 使用。

    算法侧 recommend 接受 Dict[str, Any]（不限严格 schema），但 Step 2 → Step 3
    之间需要明确契约，否则字段缺失只能运行时发现。TypedDict 保留 Dict 调用风格
    + 提供类型提示 + 0 运行成本。

    字段语义（均为子对象，避免平铺字符串的语义丢失）：
    - machine_info: 设备信息（按 specs 白名单从 InjectionMoldingMachine + 选中的 InjectionUnit 提取）
    - polymer_info: 材料信息（按 specs 白名单从 Polymer 提取，算法内部按需取 abbreviation 等）
    - mold_info: 模具信息（按 specs 白名单从 Mold 提取，算法内部按需取 product_category 等）
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


# --- 参数分类（按 prefix 分组，与 Recommendation.recommendations 对齐） ---
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


# 快照字段排除集（NON_SNAPSHOT_FIELDS）与快照函数（snapshot_parameter）已移至
# .tuning —— 与训练样本组装（build_adjustments）同属一个真相源，
# 避免两处各拍一份快照而口径漂移。


# --- ORM 序列化 + 字段命名翻译 helper ---
#
# 字段命名翻译（业务名 ↔ 算法名）的契约在算法侧
# （process/algorithms/fuzzy/field_names.py），本层只调用，避免两套口径。
# 规则见 field_names.to_algo_name / field_names.to_algo_params。
def _to_full_dict(instance: Any) -> Dict[str, Any]:
    """ORM → 完整 dict（仅排除 ORM 关系字段）"""
    if instance is None:
        return {}
    return {
        f.name: getattr(instance, f.name)
        for f in instance._meta.fields
        if not f.is_relation
    }


def _to_business_param_name(param_name: str) -> str:
    """算法字段名 → 业务字段名（无法翻译时原样返回）

    算法侧返回的 ``param`` 是算法命名空间（``IV0`` / ``BT1`` / ...），
    业务侧字段名是 ``inj_spd_1`` / ``brl_temp_1`` / ...。
    两者不在同一命名空间：不翻译就永远匹配不上 baseline，
    推荐值会被静默丢弃（表现为“算法有推荐，但参数没变”）。
    """
    if not param_name or not isinstance(param_name, str):
        return param_name
    return field_names.to_business_name(param_name) or param_name


def _param_label(business_name: str) -> str:
    """业务字段名 → 中文标签（取 ProcessParameter 字段的 verbose_name）

    例：``inj_pres_1`` → ``一段注射压力``。

    建议文案面向的是工艺员，必须用中文标签而不是 ``inj_pres_1`` / ``IP0``。
    参数不在 ProcessParameter 里时（规则库专用参数如 ``IPOS`` / ``CUSION``）
    回落到业务字段名本身。
    """
    if not business_name:
        return business_name
    try:
        return ProcessParameter._meta.get_field(business_name).verbose_name
    except Exception:  # noqa: BLE001 —— 字段不存在 / 非模型字段
        return business_name


# --- Step 0：feedback 校验（两个 inference 入口共用） ---
def _validate_feedback(feedback: Dict[str, Any]) -> None:
    """Step 0 —— feedback 防御性校验（与前端 validateFeedback 是同一套约束镜像）

    校验口径与**算法的消费口径对齐**（每一条都有算法侧的理由）：
    - defect 每项是对象                  —— 结构，算法要遍历
    - keyword_name 必填                  —— 查规则的唯一键，缺了必然查不到规则
    - level 必填且是合法档位词            —— 决定命中哪一套调整方案（三档是三套方案，不能混用）；
                                        非法值放行会导致该缺陷的规则被全过滤，
                                        对外只会报「无可用规则」，用户看不出是自己填错了
    - position 必填                     —— 缺陷位置（多段成型下用于定位到对应参数段），
                                        算法侧作为 IF 条件变量使用

    DEFECTFREE（无缺陷）是例外：前端不展示程度/位置输入框，这两项免校验。

    ⚠️ **缺陷列表可以为空**，前提是给了「合格」（tuning_result=qualified）——
       合格态产品没有缺陷，不带缺陷信息。其余评价档位仍要求缺陷列表非空。

    ⚠️ 校验口径落在**算法契约层**（`fuzzy.specs.OPTIMIZE_FEEDBACK_FIELDS` +
       `fuzzy.specs.audit_feedback_defects`），本函数只负责把问题清单转成
       BizException —— 口径不手写第二遍，改契约即同步。

    Raises:
        BizException(ERROR_REQUIRED_FIELD): 字段缺失或取值不合法
    """
    feedback = feedback or {}
    issues = audit_feedback_defects(
        feedback.get("defect"),
        allow_empty=is_qualified_result(feedback.get("tuning_result")),
    )
    if issues:
        raise BizException(ERROR_REQUIRED_FIELD, issues[0])


# --- Step 0b：调优入参契约校验（两个 inference 入口共用） ---
def _validate_optimize_inputs(
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    mold_info: Dict[str, Any],
) -> None:
    """Step 0b —— 调优入参契约校验（`OptimizeDataValidator`）

    校验器是**算法层的对外契约**（`process/algorithms/fuzzy/specs.py`），
    校验失败 ``ValueError`` 转 ``BizException``（400）。

    ⚠️ **为什么在 service 层调**：算法层不 import 业务异常（`BizException`），
    保持 fuzzy 包零业务耦合；错误码与文案由 service 层决定。

    ⚠️ **当前实际拦截面**：三份字段字典里只有 ``machine_info.drive_system``
    标了「必填」，其余全是「可选 / 推荐」⇒ 本校验目前**只拦**
    「机台没填驱动方式」这一件事。

    Raises:
        BizException(ERROR_REQUIRED_FIELD): 入参缺失必填字段
    """
    try:
        OptimizeDataValidator.validate(
            machine_info=machine_info or {},
            polymer_info=polymer_info or {},
            mold_info=mold_info or {},
        )
    except ValueError as exc:
        raise BizException(ERROR_REQUIRED_FIELD, str(exc)) from exc


# --- Step 1：装配推理上下文 ---
class InferContext(TypedDict):
    """Step 1 装配出的推理上下文

    全部来自「读 DB + 用户入参覆盖」，**不含任何写操作**。
    """

    condition: ProcessCondition
    parent_param: ProcessParameter
    baseline: Dict[str, Any]
    machine_info: Dict[str, Any]
    polymer_info: Dict[str, Any]
    mold_info: Dict[str, Any]
    # 用户手改且与库中原值**确实不同**的字段（供落库阶段精确写回）
    user_changed_fields: Dict[str, Any]


def _assemble_context(
    condition_id: int,
    parent_seq_idx: int,
    user_parameter: Optional[Dict[str, Any]],
) -> InferContext:
    """Step 1 —— 装配本轮推理上下文（只读 DB，不落库）

    这一步只回答一个问题：**本轮推理的起点是什么？**
    - condition / parent_param：从 DB 反查（调机树的当前节点）
    - baseline：以 parent_param 为底，用用户手改的值覆盖
    - machine/polymer/mold_info：按 specs.py 白名单从 condition 的关联对象提取

    ⚠️ 不在这里落库：写回父记录属于「提交」，与新建轮次同属一次事务。
    放在这里会造出「参数改了但新轮次没建成」的中间态，
    而且写在事务外，推理失败时无法回滚。
    """
    condition_orm, parent_param_orm = _resolve_parent(
        condition_id=condition_id,
        parent_seq_idx=parent_seq_idx,
    )
    baseline, changed_fields = _resolve_baseline(
        user_parameter=user_parameter,
        base_param_orm=parent_param_orm,
    )
    return InferContext(
        condition=condition_orm,
        parent_param=parent_param_orm,
        baseline=baseline,
        machine_info=_extract_machine_info(condition_orm),
        polymer_info=_extract_polymer_info(condition_orm),
        mold_info=_extract_mold_info(condition_orm),
        user_changed_fields=changed_fields,
    )


# --- Step 1 子步骤：ORM 反查 ---
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


# --- Step 1 子步骤：解析 baseline ---
def _resolve_baseline(
    user_parameter: Optional[Dict[str, Any]],
    base_param_orm: ProcessParameter,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Step 1 —— 解析 baseline（与 condition+seq_idx 对应的基准 parameter 值）

    base_param_orm 与 ORM 字段 parent_param 指同一实例，但语义不同：
    base = 推理上下文，parent = 落库父子链。

    优先级：
    1. user_parameter 非空 → 把入参字段覆盖到 base_param_orm（**仅内存，不落库**），
       然后从 ORM 读取 baseline
    2. 否则 → 直接从 base_param_orm ORM 读取

    ⚠️ 本函数**不写库**。写回父记录由落库阶段（Step 3）在事务内完成——
    「父记录改写」与「新建轮次」必须同生共死。

    Returns:
        (baseline, changed_fields)
        - baseline: 本轮推理起点（用户入参优先）
        - changed_fields: 用户手改且与库中原值**确实不同**的字段。
          值相同的字段不进这个集合，避免无谓的 UPDATE 与 updated_at 变化。
    """
    changed_fields: Dict[str, Any] = {}
    if user_parameter is not None:
        allowed = {
            f.name for f in base_param_orm._meta.fields
            if not f.is_relation and f.name not in NON_SNAPSHOT_FIELDS
        }
        for key, value in user_parameter.items():
            if value is None:
                continue
            if key not in allowed:
                continue
            if getattr(base_param_orm, key) == value:
                continue
            setattr(base_param_orm, key, value)
            changed_fields[key] = value
    return _to_full_dict(base_param_orm) or {}, changed_fields


# --- Step 3：算法调用与上下文构造 ---
def _empty_algorithm_result() -> Dict[str, Any]:
    """统一空返回结构（避免在 _call_algorithms 里重复字面量）"""
    return {
        "recommendations": [],
        "algorithm_sources": {},
        "algorithm_names": {},
        "best_recommendation": None,
    }


def _select_algorithm_result(
    algorithm_sources: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Step 3b —— 汇总后选优：最终建议集只取优先级最高的那个有产出的引擎。

    业务约定：**经验推理只作兜底**。
    - 模糊推理有产出 ⇒ 最终建议集完全取自模糊推理，经验推理整体让位
      （否则同一参数会在建议列表里出现「模糊数值建议 + 经验方向建议」两条：
       工艺员看到的是重复项；若两者方向相反，更是自相矛盾）
    - 模糊推理无产出 ⇒ 由经验推理接手（只给方向、不给数值）

    优先级取自 ``AlgorithmRegistry._priorities``：fuzzy=1 → llm=2 → empirical=3。
    落选引擎的原始产出仍保留在 ``algorithm_sources`` 里
    （供 ``_resolve_primary_source`` 判定 source_type 与日志留痕）。

    ⚠️ 选优**只影响建议集**，不影响 ``new_parameter``：
       经验推理项本就没有 ``recommended_value``，
       ``_apply_recommendations_to_baseline`` 早就会跳过它们 ⇒ 参数结果不变。

    Args:
        algorithm_sources: {subtype: 该引擎的推荐列表}（全部引擎的产出）

    Returns:
        选中的推荐列表；所有引擎都无产出时返回空列表
    """
    for subtype, payload in sorted(
        algorithm_sources.items(),
        key=lambda kv: AlgorithmRegistry.get_priority(kv[0]),
    ):
        if payload:
            _logger.info(
                "[optimize] 选优: 采用 %s 的 %d 条建议（各引擎产出: %s）",
                subtype, len(payload),
                {k: len(v) for k, v in algorithm_sources.items()},
            )
            return payload
    return []


def _call_algorithms(context: AlgorithmContext) -> Dict[str, Any]:
    """Step 3 —— 调用已注册引擎（各引擎并行）→ 汇总后选优，不查 DB

    Returns:
        {
            'recommendations': [...],       # 选优后的最终建议列表
            'algorithm_sources': {subtype: [...]},   # key = algorithm_subtype（fuzzy / empirical）
            'algorithm_names': {name: [...]},        # key = algorithm_name（展示用）
            'best_recommendation': {...} | None,
        }

    说明：`algorithm_sources` 的 key 用 **subtype** 而不是 name。
    下游 `_resolve_primary_source` 按 subtype 优先级表（fuzzy / llm / ...）
    匹配 primary source；用中文 name（'模糊推理'）当 key 时永远匹配不到，
    `source_type` 恒为 'none'。
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
        key=lambda a: AlgorithmRegistry.get_priority(a.algorithm_subtype),
    )
    if not engines:
        _logger.info("[optimize] 无可用引擎")
        return _empty_algorithm_result()

    algorithm_sources: Dict[str, List[Dict[str, Any]]] = {}
    algorithm_names: Dict[str, List[Dict[str, Any]]] = {}
    for algorithm in engines:
        try:
            recs = algorithm.recommend(context) or []
        except Exception as e:  # noqa: BLE001
            _logger.warning("[optimize] 引擎 %s 推理失败: %s", algorithm.algorithm_name, e)
            recs = []
        payload = [r.to_dict() for r in recs]
        algorithm_sources[algorithm.algorithm_subtype] = payload
        algorithm_names[algorithm.algorithm_name] = payload

    # 汇总后选优：各引擎仍并行调用，但最终建议集只采用优先级最高的那个有产出的引擎
    merged = _select_algorithm_result(algorithm_sources)
    return {
        "recommendations": merged,
        "algorithm_sources": algorithm_sources,
        "algorithm_names": algorithm_names,
        "best_recommendation": merged[0] if merged else None,
    }


def _extract_context_overrides(condition_orm: ProcessCondition) -> Dict[str, Any]:
    """取工艺条件里保存的**上下文覆盖项**（建档时人工指定的精度旋钮）。

    目前真正影响选库的只有 `rule_library_code`（显式指定用哪个规则库）：
    - **不指定 ⇒ 全量模糊库**，适用性交由规则自身标注的材料 / 产品维度判定
      （`RuleService.matches_context` + `resolve_specificity`）；
    - **显式指定 ⇒ 只用它**（引擎 `engine.py` 读 `context['rule_library_code']`）——
      用户已圈定范围时尊重用户的指定。

    ⚠️ 取不到就返回空 dict ⇒ 调用方按「未指定」处理（= 全量模糊库）。
    """
    snapshot = getattr(condition_orm, 'process_context_snapshot', None) or {}
    if not isinstance(snapshot, dict):
        return {}
    overrides = snapshot.get('overrides') or {}
    return overrides if isinstance(overrides, dict) else {}


def _compose_algorithm_context(
    *,
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    mold_info: Dict[str, Any],
    parameter: Dict[str, Any],
    feedback: Dict[str, Any],
    rule_library_code: Optional[str] = None,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Step 2 核心 —— 装成 AlgorithmContext（Port-Adapter 模式）

    - 字段选择（业务多 → 算法少）
    - 字段名翻译（业务命名 → 算法命名，规则见算法侧契约 field_names.to_algo_params）
    - 上下文组装

    `rule_library_code`：显式指定规则库（None = 全部模糊库，适用性交由规则级判定）。

    `company_id`：当前租户（**规则库可见性上下文**）—— 系统库对所有租户公用，
    租户私库只对归属租户可见（判据在算法侧共用编排层）。
    None = **无租户上下文** ⇒ 不过滤（保持现状全量）。
    """
    algorithm_params = field_names.to_algo_params(parameter)
    return {
        'machine_info': machine_info,
        'polymer_info': polymer_info,
        'mold_info': mold_info,
        'process_parameter': algorithm_params,
        'feedback': feedback,
        'rule_library_code': rule_library_code,
        'company_id': company_id,
    }


# --- 越限守卫（设备安全红线）---

def _format_limit_number(value: float) -> str:
    """上限 / 当前值的展示格式：整数不带小数尾巴（'100' 而不是 '100.0000'）"""
    try:
        if float(value) == int(value):
            return str(int(value))
    except (TypeError, ValueError):
        pass
    return ('%.4f' % value).rstrip('0').rstrip('.')


def _format_over_limit_message(items: List[Any]) -> str:
    """越限拒绝文案 —— 说清「哪个参数 / 当前值 / 上限」

    否则用户只看到一个「数据无效」，无从下手改。
    """
    details = []
    for item in items[:3]:
        details.append('%s 当前 %s 超出机台上限 %s'
                       % (item.business_name or item.param_name,
                          _format_limit_number(item.current_value),
                          _format_limit_number(item.limit)))
    if len(items) > 3:
        details.append('等 %d 项' % len(items))
    return '；'.join(details) + '，该设定超出设备可设定范围，请修正后再试'


def _summarize_conclusions(
    blocking: List[Any],
    recommendations: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """越限参数在**同期 recommendations** 里的结论（**只留痕**，不参与判定）。

    为什么留：判定发生在 recommendations **之后**（用户口径：「有了结论才能讨论
    参数是否合理」）⇒ 事后要能查证「拒绝的那一刻，结论是什么」。

    Args:
        blocking: 命中的越限项。
        recommendations: 本次推理的原始推荐列表（``to_dict()`` 后的 dict）。

    Returns:
        {算法参数名: 结论摘要}；无结论的参数标为「无结论」。
    """
    if not blocking:
        return {}
    index: Dict[str, Dict[str, Any]] = {}
    for rec in recommendations or []:
        if isinstance(rec, dict):
            index.setdefault(rec.get('param'), rec)

    out: Dict[str, Any] = {}
    for item in blocking:
        rec = index.get(item.param_name)
        if rec is None:
            out[item.param_name] = '无结论'
            continue
        out[item.param_name] = '→ %s（conf=%s, %s）' % (
            rec.get('recommended_value'), rec.get('confidence'),
            rec.get('direction'))
    return out


def _guard_blocking_over_limits(
    *,
    process_parameter: Dict[str, Any],
    machine_info: Dict[str, Any],
    interface_tag: str,
    recommendations: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """越限守卫 —— **设备安全红线**命中即拒绝（400）

    判定时机（用户口径）：**recommendations 产出之后**。
    「参数是否合理」要以结论为参照 ⇒ 不能在推理前就下判断；
    本守卫跑在 `_call_algorithms` 之后，与 fail-fast 同属 recommendations 阶段。

    判据：当前设定值 > 机台物理上限（`specs.resolve_param_limits`）。

    分层（安全分层口径，固化在算法契约层 `over_limit.BLOCKING_LIMIT_SOURCES`）：
      - ``device``（设定值类）—— **操作设备涉及安全** ⇒ 阻断；
      - ``material``（温度类）—— 降解/变色，不涉及设备安全 ⇒ 不阻断（只告警）。

    ⚠️ 缺上限（机台没填）⇒ **不阻断**：缺数据不等于参数不合理。

    Raises:
        BizException(ERROR_DATA_INVALID): 命中设备安全红线
    """
    blocking = detect_blocking_over_limits(
        process_parameter, resolve_param_limits(machine_info))
    if not blocking:
        return
    _logger.warning(
        "[optimize] %s 越限拒绝（设备安全红线）: %s ｜ 同期结论: %s",
        interface_tag, [item.to_trace() for item in blocking],
        _summarize_conclusions(blocking, recommendations))
    raise BizException(ERROR_DATA_INVALID, _format_over_limit_message(blocking))


# --- Step 3：字段提取（按 specs.py 白名单） ---
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

    与 field_contract 的关系：field_contract 提供【校验机制】
    （audit_field_completeness），本函数提供【提取机制】。
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

    跨两张表合并：InjectionMoldingMachine.drive_system（机器主表）
    + InjectionUnit.max_set_*（按 injection_index 选 unit）。
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


# --- Step 4：应用推荐 + 构造 suggestion ---
def _quantize_numeric_fields(
    params: Dict[str, Any],
    ndigits: int = 2,
) -> Dict[str, Any]:
    """工艺参数字典 → 数值字段量化（最多 ndigits 位小数）

    模糊推理的推荐值是「当前值 + Σ(规则结论值 × 组内占比)」，
    加权平均的产物天然带长小数（inj_spd_1: 30 → 32.053805467920334）——
    工艺员读不动，参数表显示成一串浮点尾数，DB 里也存着同样的脏值。

    只动**数值**字段：str / datetime / None / bool 原样保留
    （bool 是 int 的子类，必须先排除，否则 True 会被量化成 1）。

    量化口径与建议文案的 ``_format_value`` 一致（最多 2 位小数），
    保证「建议文案里的数字」与「参数表里的数字」长得一样。
    """
    out: Dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            out[key] = value
            continue
        quantized = round(value, ndigits)
        # -0.0 归一为 0.0（否则会渲染成 "-0"）
        out[key] = 0.0 if quantized == 0 else quantized
    return out


def _apply_recommendations_to_baseline(
    baseline: Dict[str, Any],
    algorithm_recommendations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Step 4a —— 用推荐值覆盖基线字段（仅覆盖基线中存在的字段）

    注意：算法返回的 ``param`` 是算法命名空间（``IV0`` / ``BT1``），
    必须先译回业务字段名（``inj_spd_1`` / ``brl_temp_1``）才能命中 baseline。

    出口统一量化（最多 2 位小数）—— 本函数是 optimize 路径**唯一的值出口**，
    落库（``_create_new_parameter``）与响应（``new_parameter``）同源于此，
    量化一次即可让「DB / 响应 / 建议文案」三处数字口径一致。
    """
    new_parameter = dict(baseline)
    for rec in algorithm_recommendations:
        param_name = _to_business_param_name(rec.get("param"))
        recommended_value = rec.get("recommended_value")
        if param_name and param_name in new_parameter and recommended_value is not None:
            new_parameter[param_name] = recommended_value
    return _quantize_numeric_fields(new_parameter)


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


def _format_value(value: Any) -> str:
    """数值 → 建议文案用的短字符串（最多 2 位小数，去掉尾随 0）

    例：``5.61938912816577`` → ``5.62``；``70.0`` → ``70``。

    模糊推理的推荐值是浮点运算结果，直接渲染会是一长串小数，
    工艺员读不动也没法照着调机。
    """
    if value is None:
        return ''
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(num - round(num)) < 1e-9:
        return str(int(round(num)))
    return f"{num:.2f}".rstrip('0').rstrip('.')


def _build_description(rec: Dict[str, Any]) -> str:
    """构造面向用户的建议文案。

    契约（前端 types/optimization.ts 的 SuggestionItem.description）：
    形如 ``降低一段注射压力：70 → 60``，而不是算法内部状态。

    - 参数名用中文标签（``一段注射压力``），不用 ``inj_pres_1`` / ``IP0``
    - 方向优先取 ``rec['direction']``（经验推理只给方向不给数值，
      从 before/after 推不出来）；没有则从数值差推
    - 经验推理无数值（recommended_value=None）→ 只说方向
    - 检查/弹窗类（``fuzzy.check``）→ 保留算法给出的提示文本
    """
    label = rec.get("param_label") or rec.get("param", "")
    before = rec.get("current_value")
    after = rec.get("recommended_value")
    direction = rec.get("direction") or _direction_from_delta(before, after)
    source = rec.get("source") or ""

    # 检查/弹窗类建议：算法已给出提示文本，直接用
    if source == "fuzzy.check":
        return rec.get("reason") or f"建议检查{label}"

    prefix = "经验推理建议" if source.startswith("empirical") else "模糊推理建议"
    action_cn = _DIRECTION_CN.get(direction or "", "调整")

    if before is not None and after is not None and before != after:
        return (
            f"{prefix}{action_cn}{label}："
            f"{_format_value(before)} → {_format_value(after)}"
        )
    if direction in ("increase", "decrease"):
        return f"{prefix}{action_cn}{label}"
    return f"{prefix}维持{label}不变"


def _extract_rule_refs(rec: Dict[str, Any]) -> List[str]:
    """提取规则引用（当前算法侧 AlgorithmRecommendation 无规则引用字段，预留接口）"""
    refs = rec.get("rule_refs") or []
    if isinstance(refs, list):
        return [str(r) for r in refs]
    return []


# --- 调整方向 → 中文（建议文案用） ---
_DIRECTION_CN = {
    "increase": "提高",
    "decrease": "降低",
    "hold": "保持",
    "check": "检查",
}


def build_recommendation_suggestion(recommendation, parameter) -> dict:
    """Recommendation → 前端 Suggestion 结构（历史轮次回显用）

    锚点语义：Recommendation 挂在它所属的那一轮参数上（FK process_parameter），
    因此该轮的建议就属于该轮、显示在该轮详情区。

    Recommendation.recommendations 存的是【已规范化】的扁平推荐列表
    （业务字段名 + 中文文案 + 已丢弃零变化项），需按业务字段分类重组成前端要的 groups。
    baseline 用该轮参数字段还原 —— 与落库时 _build_suggestion_payload 的过滤口径一致
    （只保留参数表里真实存在的字段）。

    Args:
        recommendation: Recommendation 实例
        parameter: 该建议所属的 ProcessParameter（用于还原 baseline）

    Returns:
        {source_type, groups, adopted}
    """
    recs = recommendation.recommendations or []
    source_type = recommendation.source_type or "none"
    if not recs:
        return {
            "source_type": source_type,
            "groups": [],
            "adopted": recommendation.is_adopted,
        }

    baseline = {
        f.name: getattr(parameter, f.name, None)
        for f in parameter._meta.fields
        if not f.is_relation
    }
    payload = _build_suggestion_payload(recs, {}, baseline)
    return {
        "source_type": source_type,
        "groups": payload.get("groups", []),
        "adopted": recommendation.is_adopted,
    }


def _normalize_recommendations(
    algorithm_recommendations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """把算法推荐规范化为「面向用户」的形态（落库与展示共用同一份）

    三件事：

    1. ``param`` 译回业务字段名（算法名 → 业务名）
    2. 丢弃**零变化项**（推荐值 == 当前值）：这些来自激活度 ~0 的规则，
       是数值噪声（置信度 1e-32 量级），写回业务字段也是原值，
       只会把"保持不变"当成建议推给工艺员
    3. ``reason`` 重写为业务文案（参数名用中文标签）

    必须在**落库前**调用：``Recommendation.recommendations`` 存的就是这份，
    否则库里存的是 ``模糊推理 (sources=['numeric'])`` 这种内部状态。

    Returns:
        规范化后的推荐列表（元素就地修改）
    """
    normalized: List[Dict[str, Any]] = []
    for rec in algorithm_recommendations:
        before = rec.get("current_value")
        after = rec.get("recommended_value")

        # 零变化项：推荐值与当前值实质相同 → 丢弃
        if before is not None and after is not None:
            try:
                if abs(float(after) - float(before)) < 1e-9:
                    continue
            except (TypeError, ValueError):
                pass

        param = _to_business_param_name(rec.get("param"))
        rec["param"] = param
        rec["param_label"] = _param_label(param)
        rec["reason"] = _build_description(rec)
        normalized.append(rec)
    return normalized


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
    # （过滤与分类都按**业务字段名**，算法命名空间的前缀规则匹配不到）
    if baseline is not None:
        filtered_recs = [
            rec for rec in algorithm_recommendations
            if _to_business_param_name(rec.get("param")) in baseline
        ]
    else:
        filtered_recs = algorithm_recommendations

    if not filtered_recs:
        return {"source_type": source_type, "groups": []}

    grouped: Dict[str, Dict[str, Any]] = {}
    for rec in filtered_recs:
        param_name = _to_business_param_name(rec.get("param", ""))
        category, icon = _categorize_param(param_name)

        if category not in grouped:
            grouped[category] = {"category": category, "icon": icon, "items": []}

        grouped[category]["items"].append({
            "param": param_name,
            "description": rec.get("reason") or _build_description(rec),
            "direction": (
                rec.get("direction")
                or _direction_from_delta(
                    rec.get("current_value"),
                    rec.get("recommended_value"),
                )
            ),
            "current_value": rec.get("current_value"),
            "recommended_value": rec.get("recommended_value"),
            "rule_refs": _extract_rule_refs(rec),
        })

    return {
        "source_type": source_type,
        "groups": list(grouped.values()),
    }


# --- 落库 helper（DB 操作，纯函数 / 无 self 依赖） ---
def _sync_user_modified_parameter(
    parent_param: ProcessParameter,
    changed_fields: Dict[str, Any],
) -> None:
    """Step 3 —— 把用户手改的参数写回父记录

    业务不变式：**DB 里的记录必须等于用户实际在用的参数**。
    用户在前端改了工艺参数、不点【保存试模结果】直接点【获取优化工艺】时，
    只有这里能把改动落库（tuning-feedback 不写 ProcessParameter）。

    为什么放在落库阶段而不是装配上下文时：
    「父记录改写」与「新建轮次」是同一件事的两面，必须同生共死。
    放在装配阶段会造出「参数改了但新轮次没建成」的中间态，
    而且写在事务外，推理失败时无法回滚。

    只写**真正变化**的字段：值相同的字段不进 UPDATE，
    避免写放大与无谓的 updated_at 变化。
    """
    if not changed_fields:
        return
    for key, value in changed_fields.items():
        setattr(parent_param, key, value)
    parent_param.save(update_fields=[*changed_fields.keys(), "updated_at"])


def _update_previous_tuning_record(
    parent_param: ProcessParameter,
    defect_feedbacks: List[Dict[str, Any]],
    tuning_result: Optional[str],
) -> None:
    """更新被评价轮次的 TuningRecord（缺陷反馈 + 试模结果；取最新一条）

    ⚠️ **参数名容易误读**：parent_param 是【本次提交反馈的那一轮】（第 N 轮），
    不是“上一轮已完成的轮次”。infer 请求里的 parent_seq_idx 就是当前活动轮的 seq_idx，
    所以这里的 parent_param 即第 N 轮本身。

    配对语义：界面上的「第 N 轮」= 参数(N) + 反馈(N)，反馈属于该轮参数自身的试模结果，
    因此缺陷与效果标签都写到 parent_param 自己的 TuningRecord 上，不写到它的父轮。

    tuning_result：首轮 qualified/unqualified，第 2 轮起 qualified + effective/unchanged/ineffective
    """
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

    # 合格态：产品无缺陷 ⇒ 缺陷信息一律丢弃。
    # ⚠️ 必须**显式置空**（而不是靠 `if defect_feedbacks:` 守卫跳过）：
    #    守卫会让空数组不写入，于是「先填过缺陷、后改判合格」时历史缺陷会残留。
    if is_qualified_result(tuning_result):
        previous_record.defect_feedbacks = []
    elif defect_feedbacks:
        previous_record.defect_feedbacks = defect_feedbacks

    # 映射表共用 tuning.TUNING_RESULT_MAP（唯一真相源）
    # 未命中（如 null）⇒ 保持原值不动，避免误写
    mapped_result = TUNING_RESULT_MAP.get(tuning_result) if tuning_result else None
    if mapped_result:
        previous_record.result = mapped_result

    # 规范化训练样本：变更（两快照差异）+ 本轮缺陷 + 上下文
    # ⚠️ previous_record 是从库里查的，其 process_parameter 会重新读库
    #    ⇒ 拿到的是本轮最新值
    previous_record.adjustments = build_adjustments(previous_record)

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
    """Step 3.4 —— 创建新 ProcessParameter（param_source='system_inferred'）

    parameters_dict 来自 baseline（_to_full_dict 全量快照），含父记录的
    id / created_at / param_source / seq_idx 等系统字段，直接展开会与
    create() 的显式入参冲突（multiple values for keyword argument），
    故按 NON_SNAPSHOT_FIELDS 过滤后再落库。
    """
    writable = {
        k: v for k, v in parameters_dict.items()
        if k not in NON_SNAPSHOT_FIELDS
    }
    # 租户归属继承父记录（同 condition 内必一致）
    writable["company_id"] = parent_param.company_id
    writable["organization_id"] = parent_param.organization_id

    return ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=parent_param,
        param_source="system_inferred",
        **writable,
    )


def _create_new_tuning_record(
    new_param: ProcessParameter,
    parent_param: ProcessParameter,
) -> TuningRecord:
    """Step 3.5 —— 创建新 TuningRecord（pending 状态，等待该轮自身试模反馈）

    ⚠️ **不写入 defect_feedbacks**（固定为空）：新轮次尚未试模，没有属于它自己的缺陷。
    配对语义：界面上的「第 N 轮」= 参数(N) + 反馈(N)，二者同属一轮试模；
    参数(N) 的缺陷与效果标签只能落在参数(N) 自己的 TuningRecord 上。
    父轮的缺陷已由 _update_previous_tuning_record 写入父轮自己的 TuningRecord，
    不在此处复制到子轮（否则子轮会挂上不属于它的缺陷，回显时串轮）。
    """
    previous_parameter_snapshot = snapshot_parameter(parent_param)
    return TuningRecord.objects.create(
        process_parameter=new_param,
        defect_feedbacks=[],
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


# --- infer 服务（主类） ---
class ParameterOptimizeService:
    """工艺优化 infer 服务 —— 调用链路编排

    设计约束：
    - 算法侧是接口契约：本服务只负责编排，不实现具体推理
    - 落库各自成事务：Step 1b（合格态）与 Step 3（正常轮次）各自 atomic，
      Step 3 内的多次写在一个事务内完成（避免半成品落库）
    - 公开入口：infer / infer_from_provided
    """

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

        # Step 0.5: 从 feedback 一次性提取本轮评价（贴近使用方，不跨步重复解析）
        tuning_result = feedback.get("tuning_result")
        defect_feedbacks = feedback.get("defect", []) or []

        # ---------- Step 1: 装配推理上下文（只读 DB，不落库）----------
        ctx = _assemble_context(
            condition_id=condition_id,
            parent_seq_idx=parent_seq_idx,
            user_parameter=parameter,
        )
        condition_orm = ctx["condition"]
        parent_param_orm = ctx["parent_param"]
        baseline = ctx["baseline"]
        machine_info = ctx["machine_info"]
        polymer_info = ctx["polymer_info"]
        mold_info = ctx["mold_info"]

        # ---------- Step 1b: 合格态短路（不跑 fuzzy、不建新轮次）----------
        # 产品已合格 ⇒ 没有缺陷可驱动优化 ⇒ 当前这套缺陷驱动的流程没有意义。
        # 但本轮评价**仍要落库**（写回手改参数 + 写合格标签 + 丢弃缺陷），
        # 提交通道保持可用，为「合格状态下的优化需求」预留扩展点。
        if is_qualified_result(tuning_result):
            with db_transaction.atomic():
                # 1b.1 写回用户手改的参数（DB 与用户实际在用的参数保持一致）
                _sync_user_modified_parameter(
                    parent_param=parent_param_orm,
                    changed_fields=ctx["user_changed_fields"],
                )
                # 1b.2 写本轮评价（合格标签 + 丢弃缺陷）
                _update_previous_tuning_record(
                    parent_param=parent_param_orm,
                    defect_feedbacks=defect_feedbacks,
                    tuning_result=tuning_result,
                )
            return {
                "new_parameter": None,
                "suggestion": None,
                "skipped": True,
                "skip_reason": "qualified",
                "message": "产品已合格，本轮仅记录评价，未进行工艺优化",
            }

        # Step 0b: 入参契约校验（论域上界缺失 → 判级失真，提前拒）
        _validate_optimize_inputs(machine_info, polymer_info, mold_info)
        # 建档时人工指定的上下文覆盖项（目前只有 rule_library_code 有效）
        overrides = _extract_context_overrides(condition_orm)

        # ---------- Step 2: 纯推理（与 DB 无关）----------
        new_parameter_dict, suggestion_payload, algorithm_recommendations = self._infer_kernel(
            machine_info=machine_info,
            polymer_info=polymer_info,
            mold_info=mold_info,
            baseline=baseline,
            feedback=feedback,
            interface_tag=f"infer(condition_id={condition_id}, parent_seq_idx={parent_seq_idx})",
            rule_library_code=overrides.get('rule_library_code'),
            # 当前租户（规则库可见性）—— 取自工艺条件的归属公司
            company_id=condition_orm.company_id,
        )

        # ---------- Step 3: 原子事务落库 ----------
        with db_transaction.atomic():
            # 3.1 写回用户手改的参数（DB 与用户实际在用的参数保持一致）
            _sync_user_modified_parameter(
                parent_param=parent_param_orm,
                changed_fields=ctx["user_changed_fields"],
            )

            # 3.2 更新上一轮 TuningRecord（缺陷反馈 + 试模结果）
            _update_previous_tuning_record(
                parent_param=parent_param_orm,
                defect_feedbacks=defect_feedbacks,
                tuning_result=tuning_result,
            )

            # 3.3 更新上一轮 Recommendation.is_adopted（训练标签）
            _update_previous_recommendation_is_adopted(
                parent_param=parent_param_orm,
                tuning_result=tuning_result,
            )

            # 3.4 创建新 ProcessParameter
            new_param = _create_new_parameter(
                condition=condition_orm,
                parent_param=parent_param_orm,
                parameters_dict=new_parameter_dict,
            )

            # 3.5 创建新 TuningRecord（pending 状态，等待该轮自身试模反馈）
            _create_new_tuning_record(
                new_param=new_param,
                parent_param=parent_param_orm,
            )

            # 3.6 创建新 Recommendation
            recommendation = _create_new_recommendation(
                new_param=new_param,
                algorithm_recommendations=algorithm_recommendations,
                source_type=suggestion_payload.get("source_type") or "fuzzy_rule",
            )

        # ---------- Step 4: 组装响应 ----------
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
        """
        feedback = feedback or {}
        # Step 0: feedback 防御性校验（与 infer() 同套约束镜像）
        _validate_feedback(feedback)
        # Step 0a: 合格态不支持纯推理 —— 本入口是「按缺陷算一版新参数」，
        # 合格态没有缺陷可驱动，硬跑会落到 fail-fast 报「推荐算法暂不可用」（误导）
        if is_qualified_result(feedback.get("tuning_result")):
            raise BizException(
                ERROR_ILLEGAL_ARGUMENT,
                "产品已合格，无需进行工艺优化",
            )
        # Step 0b: 入参契约校验（三维由调用方直传，同样要过契约）
        _validate_optimize_inputs(machine_info, polymer_info, mold_info)

        # 调 self._infer_kernel 纯推理（与 infer() 走同一函数）
        # 第 3 个返回值 algorithm_recommendations 无需落库（FromProvided 是纯推理）
        new_parameter_dict, suggestion_payload, _ = self._infer_kernel(
            machine_info=machine_info or {},
            polymer_info=polymer_info or {},
            mold_info=mold_info or {},
            baseline=parameter,
            feedback=feedback,
            interface_tag="infer_from_provided",
            # ⚠️ **无租户上下文**（第三方集成 / 算法试算 / 烟测）
            #    ⇒ 不过滤（保持现状全量），不改变既有行为
            company_id=None,
        )

        return {
            "new_parameter": new_parameter_dict,    # 无 parameter_id / seq_idx
            "suggestion": suggestion_payload,         # 无 recommendation_id
        }

    # --- 纯算法内核（Step 3+4）—— 私有方法，两个入口共用 ---
    @staticmethod
    def _infer_kernel(
        *,
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        mold_info: Dict[str, Any],
        baseline: Dict[str, Any],
        feedback: Dict[str, Any],
        interface_tag: str,
        rule_library_code: Optional[str] = None,
        company_id: Optional[int] = None,
        fail_fast_message: str = "推荐算法暂不可用，请稍后重试或联系管理员",
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
        """【Step 3+4 纯算法内核】5 维 dict → (new_parameter, suggestion, algorithm_recommendations)

        对应 parameter_initialize._infer_kernel（同构同名设计）。
        不依赖 self/cls，无副作用。

        Args:
            machine_info: 设备 dict（HMI 范围由算法自挑）
            polymer_info: 材料 dict（含 abbreviation）
            mold_info: 模具 dict（含 product_category）
            baseline: 调优基线（flat 字段，对齐 ProcessParameterSchema）
            feedback: 缺陷反馈
            interface_tag: fail-fast 日志前缀
            fail_fast_message: BizException 文案
            company_id: 当前租户（**规则库可见性上下文**）—— None = 无租户
                上下文 ⇒ 不过滤（保持现状全量）。

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
            rule_library_code=rule_library_code,
            company_id=company_id,
        )

        algorithm_result = _call_algorithms(algorithm_context)
        raw_recommendations = algorithm_result.get("recommendations", []) or []
        algorithm_sources = algorithm_result.get("algorithm_sources", {}) or {}

        # 越限守卫（**recommendations 阶段**的判定，详见 _guard_blocking_over_limits）
        #
        # 放在 fail-fast **之前**：超限往往就是「推不出结论」的根因，
        # 先报根因（参数超出设备可设定范围）比报「推荐算法暂不可用」准确。
        _guard_blocking_over_limits(
            process_parameter=algorithm_context.get('process_parameter') or {},
            machine_info=machine_info,
            interface_tag=interface_tag,
            recommendations=raw_recommendations,
        )

        # fail-fast 守卫（基于算法原始输出：有没有给出推荐）
        if not raw_recommendations:
            _logger.warning(
                "[optimize] %s fail-fast: 无可用推荐 (algorithm_sources=%s)",
                interface_tag, algorithm_sources,
            )
            raise BizException(ERROR_OPERATION_FAILED, fail_fast_message)

        # 规范化：业务字段名 + 业务文案 + 过滤零变化项
        # （落库与展示共用这一份，Recommendation.recommendations 存的就是它）
        algorithm_recommendations = _normalize_recommendations(raw_recommendations)

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