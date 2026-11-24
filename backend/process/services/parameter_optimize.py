"""工艺优化服务（调用链路编排层，不含算法实现）。

对外入口：
- optimize_from_condition(condition_id, parent_seq_idx, ...)  → POST /api/processes/algorithms/optimize/
- optimize_from_provided(parameter, feedback, 三维上下文) —— 纯推理，不查库也不落库；
  **尚无 HTTP 路由**，目前仅测试与脚本直接调用

调用链（optimize_from_condition）：
反馈转换与契约校验 → 装配上下文（只读）→ 纯推理 → 原子落库 → 组装响应

设计约束：
- 只负责编排，不实现具体推理，算法侧是接口契约
- 只开一个事务，落库阶段的多次写都在 atomic 内完成，避免半成品落库
- 全部为模块顶层函数，无类封装、不依赖 self/cls；公开入口 optimize_from_condition /
  optimize_from_provided + 私有内核 _infer_kernel（入口共用），入参契约校验
  _validate_optimize_inputs 由 _infer_kernel 统一调用

设计要点：
- 自动维护 is_adopted，被建议轮的下一轮 feedback 为 ineffective 时改 False
- 写回用户手改的工艺参数到父记录，与新建轮次同生共死，详见 _record_tuning_round
"""
import logging
from collections.abc import Mapping
from dataclasses import replace
from typing import Dict, Any, List, Optional, Tuple, TypedDict

from django.db import transaction as db_transaction

from extensions.exceptions import (
    BizException,
    ERROR_DATA_NOT_FOUND,
    ERROR_OPERATION_FAILED,
    ERROR_REQUIRED_FIELD,
)
from process.models import (
    ProcessCondition,
    ProcessParameter,
    Recommendation,
    TuningRecord,
)
from process.exceptions import ERROR_PROCESS_UNFIT_PARAM  # 导入「参数不符合机台设定要求」的异常码
from .optimize_chain.decide_direction import (  # 导入第2层的裁决类型与函数，第2层按调机策略筛规则、定调整方向
    AdjustmentPlan,
    PriorityTable,
    ScenarioContext,
    ScenarioStrategy,
    StrategyDecision,
    build_plan,
    build_scenario_context,
    collect_candidates,
    select_strategy,
)
from .optimize_chain.tuning_strategy import (  # 导入第2层的调机策略清单与阶段进度
    derive_stage_progress,
    sorted_scenario_strategies,
)
from .optimize_chain.integrate_params import (  # 导入第3层的参数整合
    IntegratedParams,
    apply_plan,
)
from .optimize_chain.check_params import (
    validate,  # 导入第4层的参数校验
    resolve_range_limits,  # 差值越限的参照系（机台实测注射行程）
)
from process.algorithms.base import AlgorithmRegistry
from .optimize_chain.defect_selection import (  # 导入缺陷选取的算法实现
    select_defect,
)
from process.algorithms.fuzzy.specs import (
    OPTIMIZE_FEEDBACK_FIELDS,
    audit_feedback_defects,  # 导入契约层的缺陷反馈校验
    OptimizeDataValidator,  # 导入入参契约校验器
)  # 导入算法入参契约字段字典，service 层按此白名单提取，不传全量 ORM 字段
from .tuning import (  # 导入 tuning_result 映射与参数快照、训练样本组装，三者同属一个真相源
    NON_SNAPSHOT_FIELDS,
    TUNING_RESULT_MAP,
    build_adjustments,
    is_qualified_result,
    is_round_sealed,
    snapshot_parameter,
)
from process.models.rules import RuleLibrary
from process.algorithms.fuzzy.library.adapters import LibraryRecordAdapter
from process.algorithms.fuzzy.library.contracts import LibraryRecord
from .shared.spec_extract import (  # 导入参数提取 helper，优化与初始化两条链路共用
    extract_machine_info,
    extract_mold_info,
    extract_polymer_info,
)
from .shared.param_limits import (  # 参数限值专区（准备 + 校验，两条链路共用同一判据与文案）
    build_limits,  # 机台可设定上限 → {参数名: 允许区间}（**一张表，所有参数一视同仁**）
    format_unfit_param_message,  # 导入「参数超出机台可设定上限」文案
    guard_parameter_limits,  # 统一的参数区间守卫（位置参数与设定值参数同构）
    to_upper_limits,  # 业务键区间表 → 业务键标量上限表（第4层判越限用）
)
from .shared.param_naming import (  # 导入 ORM 工艺字段判据与中文标签
    is_process_field,
    param_label,
)

_logger = logging.getLogger(__name__)


# 注册各算法模块内的引擎，fuzzy/engine.py 与 empirical/empirical_algorithm.py 各自注册
# 触发靠 process/algorithms/__init__.py 的 import 链


class AlgorithmContext(TypedDict):
    """算法引擎输入 context 的标准格式。

    字段：machine_info / polymer_info / mold_info 按 specs 白名单提取；
    process_parameter 是**业务字段名**（ORM 字段名）；feedback 缺陷已收敛；
    libraries 是本轮可见的规则库档案；
    param_limits 是**业务键区间表**（业务字段名 → 允许区间）。

    【注意】**跨层一律业务命名**：算法名（``IV0`` / ``MEL``）只在算法推理
    内部使用 ⇒ 引擎自己译（``fuzzy/engine.py`` 的 ``to_algo_params`` /
    ``to_family_limits``），不外传。

    【注意】键恒在、值可空 —— 键缺失 = 契约违规（入口会拦），值为空 = 合法业务状态。
    """
    machine_info: Dict[str, Any]
    polymer_info: Dict[str, Any]
    mold_info: Dict[str, Any]
    process_parameter: Dict[str, Any]
    feedback: Dict[str, Any]
    libraries: Optional[List[LibraryRecord]]
    param_limits: Dict[str, Any]


# 收集必需 key 集合，供 _call_algorithms 入口验证
# 取 TypedDict 声明的全部 key，键恒在所以全部必填，派生而非手写，改声明即同步
_REQUIRED_CONTEXT_KEYS = frozenset(AlgorithmContext.__annotations__.keys())


# --- 按 prefix 分组的参数分类，与 Recommendation.recommendations 对齐 ---
_PARAM_CATEGORY_RULES = (
    ('inj_', ('注射参数', 'mdi:speedometer')),
    ('hold_', ('保压参数', 'mdi:gauge')),
    ('met_', ('熔胶参数', 'mdi:screw-machine-flat-top')),
    ('vps_', ('VP 切换', 'mdi:swap-vertical')),
    ('cool_', ('冷却参数', 'mdi:snowflake')),
    ('pre_met_decomp_', ('熔胶前松退', 'mdi:arrow-collapse')),
    ('pst_met_decomp_', ('熔胶后松退', 'mdi:arrow-collapse')),
    ('noz_temp', ('料筒温度', 'mdi:thermometer')),
    ('brl_temp_', ('料筒温度', 'mdi:thermometer')),
)


def _categorize_param(param_name: str) -> Tuple[str, str]:
    """按字段名前缀把参数归类，供前端分组展示。

    Args:
        param_name: 业务字段名。

    Returns:
        Tuple[str, str]: (category, icon) —— 中文分类名与 mdi 图标名；
            匹配不到前缀规则时归入「其他参数」。
    """
    for match_key, (category, icon) in _PARAM_CATEGORY_RULES:
        if match_key.endswith('_'):
            if param_name.startswith(match_key):
                return category, icon
        else:
            if param_name == match_key:
                return category, icon
    return '其他参数', 'mdi:cog-outline'


def _direction_from_delta(before: Optional[float], after: Optional[float]) -> Optional[str]:
    """根据 before/after 数值推断调整方向。

    Args:
        before: 调整前的值，None 表示未知。
        after: 调整后的值，None 表示未知。

    Returns:
        Optional[str]: 'increase' / 'decrease' / 'hold'；任一端为 None 时返回 None。
    """
    if before is None or after is None:
        return None
    if after > before:
        return 'increase'
    if after < before:
        return 'decrease'
    return 'hold'


# 快照字段排除集 NON_SNAPSHOT_FIELDS 与快照函数 snapshot_parameter 见 .tuning
# 与训练样本组装 build_adjustments 同属一个真相源，避免两处各拍一份快照而口径漂移


# --- ORM 序列化 helper ---
# 字段名一律用 ORM 字段名（业务命名）⇒ 序列化出口不做任何改名
def _to_full_dict(instance: Any) -> Dict[str, Any]:
    """ORM → 完整 dict（仅排除 ORM 关系字段）。

    Args:
        instance: ORM 模型实例，None 表示无实例。

    Returns:
        Dict[str, Any]: 实例的全部普通字段 → 值；instance 为 None 时返回空字典。
    """
    if instance is None:
        return {}
    return {
        f.name: getattr(instance, f.name)
        for f in instance._meta.fields
        if not f.is_relation
    }


# --- 装配推理上下文 ---
class InferContext(TypedDict):
    """装配出的推理上下文。

    全部来自「读 DB + 用户入参覆盖」，**不含任何写操作**。
    """

    condition: ProcessCondition
    parent_param: ProcessParameter
    baseline: Dict[str, Any]
    machine_info: Dict[str, Any]
    polymer_info: Dict[str, Any]
    mold_info: Dict[str, Any]
    # 收集用户手改且与库中原值**确实不同**的字段，供落库阶段精确写回
    user_changed_fields: Dict[str, Any]


def _resolve_infer_context(
    condition_id: int,
    parent_seq_idx: int,
    submitted_parameter: Optional[Dict[str, Any]],
) -> InferContext:
    """反查并装配本轮推理上下文（只读 DB，不落库）。

    这一步只回答一个问题：**本轮推理的起点是什么？**
    - condition / parent_param：从 DB 反查（调机树的当前节点）
    - baseline：以库里的 parent_param 为底，用本次提交的值覆盖
    - machine/polymer/mold_info：按 specs.py 白名单从 condition 的关联对象提取

    Args:
        condition_id: 工艺条件 ID。
        parent_seq_idx: 基准业务编号。
        submitted_parameter: 本次提交的手动覆盖值，None 表示未提交。

    Returns:
        InferContext: 装配好的推理上下文 —— condition / parent_param / baseline /
            三维上下文 / 用户改动字段。

    【注意】不在这里落库：写回父记录属于「提交」，与新建轮次同属一次事务。
    放在这里会造出「参数改了但新轮次没建成」的中间态，
    而且写在事务外，推理失败时无法回滚。
    """
    condition_orm = _resolve_condition(condition_id=condition_id)
    parent_param_orm = _resolve_parent_parameter(
        condition=condition_orm,
        parent_seq_idx=parent_seq_idx,
    )
    baseline, changed_fields = _resolve_baseline(
        submitted_parameter=submitted_parameter,
        parent_param_orm=parent_param_orm,
    )
    return InferContext(
        condition=condition_orm,
        parent_param=parent_param_orm,
        baseline=baseline,
        machine_info=extract_machine_info(condition_orm),
        polymer_info=extract_polymer_info(condition_orm),
        mold_info=extract_mold_info(condition_orm),
        user_changed_fields=changed_fields,
    )


# --- 反查与上下文准备 ---
def _resolve_condition(condition_id: int) -> ProcessCondition:
    """反查工艺条件（含关联对象预加载）。

    预加载：injection_machine / polymer / mold（FK 一级）、
    injection_machine__injection_units（FK 二级，避免 N+1）。

    Args:
        condition_id: 工艺条件主键。

    Returns:
        ProcessCondition: 工艺条件实例，关联对象已预加载。

    Raises:
        BizException(ERROR_DATA_NOT_FOUND): 工艺条件不存在。
    """
    try:
        return (
            ProcessCondition.objects
            .select_related('injection_machine', 'polymer', 'mold')
            .prefetch_related('injection_machine__injection_units')
            .get(id=condition_id)
        )
    except ProcessCondition.DoesNotExist as exc:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}") from exc


# 取通用兜底库编码，始终包含在可见库集合内
BASE_LIBRARY_CODE = 'base'


def _filter_visible_libraries(
    libraries: List[LibraryRecord],
    company_id: Optional[int],
) -> List[LibraryRecord]:
    """按租户归属过滤库档案（可见性判据的唯一定义处）。

    Args:
        libraries: 库档案清单。
        company_id: 当前租户公司主键，None 表示无租户上下文。

    Returns:
        List[LibraryRecord]: 可见的库档案，保持入参顺序；无租户时只留系统库。

    【注意】库可见 ⟺ 系统库（全平台公用），或归属租户 == 当前租户。
    """
    visible = []
    for lib in libraries:
        owner_type = lib.owner_type or 'system'
        if owner_type == 'system':
            visible.append(lib)
        elif company_id is not None and lib.company_id == company_id:
            visible.append(lib)
    return visible


def _resolve_visible_libraries(
    company_id: Optional[int],
    library_code: Optional[str] = None,
) -> List[LibraryRecord]:
    """解析本轮可见的规则库档案（租户隔离在 service 层完成）。

    Args:
        company_id: 当前租户公司主键，None 表示无租户上下文。
        library_code: 指定的库编码，None 表示不指定。

    Returns:
        List[LibraryRecord]: 可见的模糊库档案，按 priority 降序；指定 library_code 时
            只取该库，并叠加通用兜底库 base。

    【注意】company_id 为空（第三方集成 / 离线 runner）时只给系统库。
    """
    records = [
        LibraryRecordAdapter.to_record(lib)
        for lib in RuleLibrary.objects.filter(is_active=True, library_type='fuzzy')
    ]
    if library_code is not None:
        records = [record for record in records
                   if record.library_code in (library_code, BASE_LIBRARY_CODE)]

    visible = _filter_visible_libraries(records, company_id)
    return sorted(visible, key=lambda record: -record.priority)


def _resolve_parent_parameter(
    condition: ProcessCondition,
    parent_seq_idx: int,
) -> ProcessParameter:
    """反查该轮的基准工艺参数（condition + seq_idx 定位）。

    Args:
        condition: 所属工艺条件。
        parent_seq_idx: 基准业务编号。

    Returns:
        ProcessParameter: 该轮的基准工艺参数实例。

    Raises:
        BizException(ERROR_DATA_NOT_FOUND): 基准工艺参数不存在。
    """
    try:
        return ProcessParameter.objects.get(
            process_condition=condition,
            seq_idx=parent_seq_idx,
        )
    except ProcessParameter.DoesNotExist as exc:
        raise BizException(
            ERROR_DATA_NOT_FOUND,
            f"基准工艺参数不存在: condition_id={condition.id}, seq_idx={parent_seq_idx}",
        ) from exc


def _resolve_baseline(
    submitted_parameter: Optional[Dict[str, Any]],
    parent_param_orm: ProcessParameter,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """解析 baseline（本轮推理的起始参数）。

    Args:
        submitted_parameter: 本次提交的手动覆盖值，None 表示未提交。
        parent_param_orm: 库里的父轮参数。

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: (baseline, changed_fields)。
            baseline 以提交值为优先；changed_fields 只含本次提交且与原值确实不同的字段。

    【注意】本函数只在内存里覆盖，不写库（写回由落库阶段在事务内完成）。
    """
    changed_fields: Dict[str, Any] = {}
    if submitted_parameter is not None:
        allowed = {
            f.name for f in parent_param_orm._meta.fields
            if not f.is_relation and f.name not in NON_SNAPSHOT_FIELDS
        }
        for key, value in submitted_parameter.items():
            if value is None:
                continue
            if key not in allowed:
                continue
            if getattr(parent_param_orm, key) == value:
                continue
            setattr(parent_param_orm, key, value)
            changed_fields[key] = value
    return _to_full_dict(parent_param_orm) or {}, changed_fields


# --- 算法调用与上下文构造 ---
def _empty_algorithm_result() -> Dict[str, Any]:
    """统一空返回结构（避免在 _call_algorithms 里重复字面量）。

    Returns:
        Dict[str, Any]: 空结果骨架 —— recommendations 空列表、两个分组字典为空、best 为 None。
    """
    return {
        "recommendations": [],
        "algorithm_sources": {},
        "algorithm_names": {},
        "best_recommendation": None,
    }


def _select_algorithm_result(
    algorithm_sources: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """汇总后选优：最终建议集只取优先级最高的那个有产出的引擎。

    Args:
        algorithm_sources: {subtype: 该引擎的推荐列表}，含全部引擎的产出。

    Returns:
        List[Dict[str, Any]]: 选中的推荐列表；所有引擎都无产出时为空列表。

    【注意】经验推理只作兜底 —— 模糊推理有产出就整体让位，否则同一参数会出现
        「模糊数值建议 + 经验方向建议」两条；落选引擎的原始产出仍留在 algorithm_sources。
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
    """调用已注册引擎（各引擎并行）→ 汇总后选优，不查 DB。

    Args:
        context: 装配好的算法上下文。

    Returns:
        Dict[str, Any]: 含 recommendations（选优后的建议列表）、algorithm_sources
            （按 subtype 分组）、algorithm_names（按 name 分组，展示用）、
            best_recommendation。

    【注意】algorithm_sources 的 key 必须是 subtype —— 下游按 subtype 优先级表匹配
        primary source，用中文 name 当 key 会匹配不到。
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

    # 汇总后选优，各引擎仍并行调用，但最终建议集只采用优先级最高的那个有产出的引擎
    merged = _select_algorithm_result(algorithm_sources)
    return {
        "recommendations": merged,
        "algorithm_sources": algorithm_sources,
        "algorithm_names": algorithm_names,
        "best_recommendation": merged[0] if merged else None,
    }


def _compose_algorithm_context(
    *,
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    mold_info: Dict[str, Any],
    parameter: Dict[str, Any],
    feedback: Dict[str, Any],
    libraries: Optional[List[LibraryRecord]] = None,
) -> AlgorithmContext:
    """装成 AlgorithmContext（Port-Adapter 模式）。

    - 上下文组装（字段的挑选在 spec_extract 侧完成）
    - **设备上限表解析**（``machine_info`` → 上限表）：取值在 service 层完成，
      算法层只收「已经取好的值」⇒ 算法层不碰 ORM 字段名。

    Args:
        machine_info: 设备上下文。
        polymer_info: 材料上下文。
        mold_info: 模具上下文。
        parameter: 业务命名的参数字典。
        feedback: **已收敛**的缺陷反馈（由 ``optimize_chain.defect_selection.select_defect`` 收敛）。
        libraries: 本轮可见的规则库档案，None 表示不限定。

    Returns:
        AlgorithmContext: 算法引擎的标准输入 context。

    【注意】`libraries` **由 service 层按租户归属决定** ——
    算法侧只按这份清单取规则，不持有租户概念。
    """
    return {
        'machine_info': machine_info,
        'polymer_info': polymer_info,
        'mold_info': mold_info,
        # 工艺参数：**业务字段名**（ORM 字段名）⇒ 算法名不外传，
        # 引擎内部自己译（``fuzzy/engine.py`` 的 ``to_algo_params``）
        'process_parameter': parameter,
        'feedback': feedback,
        'libraries': libraries,
        # 机台可设定上限表（**service 层取值**）：缺值 ⇒ 空表 ⇒ 算法层按「缺权威源」处理
        # （回落经验域、不裁剪、不报错）。
        # 【注意】**只有一张表**：位置参数与压力 / 速度参数同构 ⇒ 全部参数
        # 都走同一条判定路径（上限取自哪个设备字段，由 service 层配置决定）。
        # 【注意】**传的是业务键区间表**：「业务键 → 算法族」的对应关系归算法层
        # （``fuzzy/device_limits.to_family_limits``）⇒ 翻译在算法内部做。
        'param_limits': build_limits(machine_info),
    }


# --- 越限守卫，设备安全红线与参数超可设定上限 ---
# 实现见 :mod:`process.services.shared.param_limits`，初始化与优化两条链路共用同一判据。


# --- 应用推荐 + 构造 suggestion ---
def _quantize_numeric_fields(
    params: Dict[str, Any],
    ndigits: int = 2,
) -> Dict[str, Any]:
    """量化工艺参数里的数值字段（最多 2 位小数）。

    Args:
        params: 业务字段名 → 值的参数字典。
        ndigits: 保留的小数位数，默认 2。

    Returns:
        Dict[str, Any]: 数值字段被量化后的新字典；非数值字段（str / datetime /
            None / bool）原样保留。

    【注意】量化口径与建议文案的 _format_value 一致 ⇒ 建议文案里的数字与
        参数表里的数字长得一样。
    """
    out: Dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            out[key] = value
            continue
        quantized = round(value, ndigits)
        # 归一 -0.0 为 0.0，否则会渲染成 "-0"
        out[key] = 0.0 if quantized == 0 else quantized
    return out


def _apply_decision_status(
    recommendations: List[Dict[str, Any]],
    decision: StrategyDecision,
) -> List[Dict[str, Any]]:
    """把第2层的裁决状态就地回填到每条建议。

    Args:
        recommendations: 建议列表，原地修改。
        decision: 第2层的裁决结果。

    Returns:
        List[Dict[str, Any]]: 同一份建议列表，就地补上 decision_status / decision_reason。

    【注意】状态三取值：adopted（保留执行）/ yielded（让位）/ deferred（暂缓）；
        不在候选集里的建议不打标 ⇒ 历史轮次没有状态字段时照常显示，不会被误当成「未采用」。
    """
    for rec in recommendations:
        status, reason = decision.status_of(rec.get('param') or '')
        if status is None:
            continue
        rec['decision_status'] = status
        if reason:
            rec['decision_reason'] = reason
    return recommendations


def _decide_plan_by_strategy(
    algorithm_recommendations: List[Dict[str, Any]],
    priority_table: Optional[PriorityTable] = None,
    scenario: Optional[ScenarioStrategy] = None,
    context: Optional[ScenarioContext] = None,
) -> AdjustmentPlan:
    """按调机策略筛选规则，给出明确的调整计划。

    Args:
        algorithm_recommendations: 算法给的平级建议（第1层产出）。
        priority_table: 场景给出的优先级表，None 表示不裁决。
        scenario: 匹配到的调机场景，None 表示不裁决。
        context: 实际情况，含缺陷码、实测重量、充填缺口等。

    Returns:
        AdjustmentPlan: 调整计划 —— 调哪几个、谁让位、谁暂缓、按什么口径调。

    【注意】优先级表与场景都为空 ⇒ 不裁决 ⇒ 行为与「不接第2层」一致。
    """
    candidates = collect_candidates(algorithm_recommendations)
    plan = build_plan(
        candidates.names,
        candidates.targets,
        context=context,
        strategy=scenario,
        table=priority_table,
    )

    # 记决策留痕，有让位或暂缓时才落日志，正常路径不产噪声
    if plan.selection.yielded or plan.selection.deferred:
        _logger.info('infer plan: %s', plan.selection.to_trace())

    return plan


def _fill_weights(
    context: Optional[ScenarioContext],
) -> Optional[Tuple[float, float]]:
    """取按充填量比例调行程要用的两个重量：制品总重、实测制品重量。

    Args:
        context: 调机场景上下文，None 表示场景未命中。

    Returns:
        Optional[Tuple[float, float]]: (制品总重, 实测制品重量)；缺任一个 ⇒ 返回 None ⇒
            第3层回落「MEL 增量」口径（不臆造）。
    """
    if context is None:
        return None
    if context.target_weight is None or context.actual_weight is None:
        return None
    return (context.target_weight, context.actual_weight)


def _zero_landing_detail(integrated: IntegratedParams) -> str:
    """零落地的原因说明（让位回退 / 硬约束未处理）。

    给工艺员看的**人话**：告诉用户「为什么这一轮调不下去」，
    而不是抛一个无参的「操作失败」。

    Args:
        integrated: 第3层参数整合的产出。

    Returns:
        str: 原因说明文案；既无让位也无硬约束时给默认说明。
    """
    parts: List[str] = []
    if integrated.superseded_fields:
        parts.append('让位回退：%s' % '、'.join(
            '%s→%s' % item for item in integrated.superseded_fields))
    if integrated.unresolved:
        parts.append('硬约束未处理：%s' % '；'.join(integrated.unresolved))
    return '；'.join(parts) or '保留项未产生实际变化'


def _resolve_primary_source(algorithm_sources: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
    """选取主要算法来源（引擎 subtype）。

    按本函数的 subtype 优先级表取第一个有产出的引擎（该表与
    ``AlgorithmRegistry.get_priority`` 不是同一份）。

    Args:
        algorithm_sources: {subtype: 该引擎的推荐列表}，含全部引擎的产出。

    Returns:
        Optional[str]: 引擎 subtype（fuzzy / llm / empirical ...）；全部引擎都无产出时返回 None。
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
    """数值 → 建议文案用的短字符串（最多 2 位小数，去掉尾随 0）。

    例：``5.61938912816577`` → ``5.62``；``70.0`` → ``70``。

    模糊推理的推荐值是浮点运算结果，直接渲染会是一长串小数，
    工艺员读不动也没法照着调机。

    Args:
        value: 待渲染的值，None 表示空值。

    Returns:
        str: 渲染后的短字符串；None 渲染成空串，非数值按原样转字符串。
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

    Args:
        rec: 单条推荐记录。

    Returns:
        str: 面向工艺员的中文建议文案。
    """
    label = rec.get("param_label") or rec.get("param", "")
    before = rec.get("current_value")
    after = rec.get("recommended_value")
    direction = rec.get("direction") or _direction_from_delta(before, after)
    source = rec.get("source") or ""

    # 处理检查/弹窗类建议，算法已给出提示文本，直接用
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
    """提取规则引用（该建议命中了哪几条规则）。

    来源优先级：
    1. ``matched_rules`` —— 模糊推理引擎透出的**命中规则明细**（开发者模式）。
       每项 = ``{'rule': 规则串, 'weight': 组内占比, 'raw_activation': 原始激活度}``
       ⇒ 取其中的 ``rule`` 字段（**完整规则串**，一眼能看懂命中逻辑）。
    2. ``rule_refs`` —— 算法侧直接给的规则引用列表（兼容其他引擎 / 存量数据）。

    Args:
        rec: 单条推荐记录。

    Returns:
        List[str]: 命中的规则串列表；两种来源都没有时为空列表。

    【注意】**只取规则串，不改任何数值** —— 本函数只影响展示，不参与建议值计算。
    """
    matched = rec.get("matched_rules")
    refs: List[str] = []
    if isinstance(matched, list):
        for item in matched:
            if isinstance(item, dict):
                rule = item.get("rule")
                if rule:
                    refs.append(str(rule))
            elif isinstance(item, str) and item:
                refs.append(item)
    if refs:
        return refs
    raw = rec.get("rule_refs") or []
    if isinstance(raw, list):
        return [str(r) for r in raw]
    return []


# --- 调整方向译成中文，供建议文案用 ---
_DIRECTION_CN = {
    "increase": "提高",
    "decrease": "降低",
    "hold": "保持",
    "check": "检查",
}


def build_recommendation_suggestion(recommendation, parameter) -> dict:
    """Recommendation → 前端 Suggestion 结构（历史轮次回显用）。

    Args:
        recommendation: Recommendation 实例。
        parameter: 该建议所针对的 ProcessParameter，用于还原 baseline。

    Returns:
        dict: {source_type, groups, adopted}。

    【注意】不传 applied_values —— 落地值在「按建议调整后的那一轮」上，被建议轮的
        记录里没有它 ⇒ 历史轮次的 applied_value 直接不填（前端按「有则用」处理）。
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
    payload = _build_suggestion_payload(recs, {}, baseline, applied_values=None)
    return {
        "source_type": source_type,
        "groups": payload.get("groups", []),
        "adopted": recommendation.is_adopted,
    }


def _normalize_recommendations(
    algorithm_recommendations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """把算法推荐规范化为面向用户的形态：译回业务字段名、丢掉零变化项、重写业务文案。

    Args:
        algorithm_recommendations: 算法给的推荐列表，元素就地修改。

    Returns:
        List[Dict[str, Any]]: 规范化后的推荐列表（落库与展示共用这一份）。

    【注意】丢弃零变化项是去噪、不是取舍 —— 取舍归第2层。
    """
    normalized: List[Dict[str, Any]] = []
    for rec in algorithm_recommendations:
        before = rec.get("current_value")
        after = rec.get("recommended_value")

        # 丢弃零变化项，推荐值与当前值实质相同
        if before is not None and after is not None:
            try:
                if abs(float(after) - float(before)) < 1e-9:
                    continue
            except (TypeError, ValueError):
                pass

        # 【注意】``param`` 已是业务字段名（算法层出口译好）⇒ 这里只补中文标签；
        #   不是工艺字段的（规则库专用参数）不给标签，原样保留。
        param = rec.get("param")
        rec["param"] = param
        rec["param_label"] = param_label(param) if is_process_field(param) else param
        rec["reason"] = _build_description(rec)
        normalized.append(rec)
    return normalized


def _build_suggestion_payload(
    algorithm_recommendations: List[Dict[str, Any]],
    algorithm_sources: Dict[str, List[Dict[str, Any]]],
    baseline: Optional[Dict[str, Any]] = None,
    applied_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """扁平推荐按 category 分组，构建 SuggestionGroup。

    Args:
        algorithm_recommendations: 规范化后的推荐列表。
        algorithm_sources: {subtype: 该引擎的推荐列表}，用于取主要来源。
        baseline: 本轮基线参数，None 表示不过滤。
        applied_values: 已采用项的实际落地值，None 表示不填落地值。

    Returns:
        Dict[str, Any]: {"source_type": ..., "groups": [...]}；无可见推荐时 groups 为空列表。

    【注意】baseline 不为 None 时只保留在 baseline 中存在的推荐字段
    （**展示层过滤** —— 与候选准入的「是不是工艺量」同口径）。

    ``applied_values``：**已采用项的实际落地值**（字段名 → 值）。
    当轮响应传 ``integrated.values``（整合后的最终参数集，**未量化**）；
    历史轮次回显**不传**（落地值在「按建议调整后的那一轮」上 ⇒ 被建议轮没有它）。
    【注意】**只给已采用项**：未采用项的「落地值」就是原值，没有意义。
    """
    source_type = _resolve_primary_source(algorithm_sources) or "none"

    if not algorithm_recommendations:
        return {"source_type": source_type, "groups": []}

    # 做展示层过滤，本机没有的字段不展示
    # 过滤与分类都按**业务字段名**，算法命名空间的前缀规则匹配不到
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

        item = {
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
        }
        # 回填裁决状态，adopted 已采用 / yielded 让位 / deferred 暂缓。
        # 【注意】**无状态就不给字段**，历史轮次没有该字段或未进候选集 ⇒ 前端按「有则用」处理。
        status = rec.get("decision_status")
        if status:
            item["decision_status"] = status
            reason = rec.get("decision_reason")
            if reason:
                item["decision_reason"] = reason
            if status == "adopted" and applied_values is not None:
                applied = applied_values.get(param_name)
                if applied is not None:
                    item["applied_value"] = applied
        grouped[category]["items"].append(item)

    return {
        "source_type": source_type,
        "groups": list(grouped.values()),
    }


def _to_algorithm_feedback(feedback: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """把接口反馈整理成算法入参（转换接头）。

    Args:
        feedback: 接口形态的反馈字典。

    Returns:
        Dict[str, Any]: 算法契约形态的反馈字典。

    Raises:
        BizException(ERROR_REQUIRED_FIELD): 转换结果不满足算法契约。

    【注意】缺陷列表可以为空 —— 前提是给了「合格」（tuning_result=qualified）。
    """
    feedback = feedback or {}
    defects = []
    for item in feedback.get("defects") or []:
        if not isinstance(item, Mapping):
            # 非法项原样带过去，交给契约校验报「第 N 项」
            defects.append(item)
            continue
        defects.append({k: item.get(k) for k in OPTIMIZE_FEEDBACK_FIELDS})

    algorithm_feedback = {
        "defects": defects,
        "observations": list(feedback.get("observations") or []),
        "tuning_result": feedback.get("tuning_result"),
    }
    issues = audit_feedback_defects(
        algorithm_feedback["defects"],
        allow_empty=is_qualified_result(feedback.get("tuning_result")),
    )
    if issues:
        raise BizException(ERROR_REQUIRED_FIELD, issues[0])
    return algorithm_feedback


def _validate_optimize_inputs(
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    mold_info: Dict[str, Any],
) -> None:
    """校验三维上下文的入参契约（契约层 ``OptimizeDataValidator``）。

    Args:
        machine_info: 设备上下文。
        polymer_info: 材料上下文。
        mold_info: 模具上下文。

    Raises:
        BizException(ERROR_REQUIRED_FIELD): 入参缺失必填字段

    【注意】校验器抛 ``ValueError``，本函数转成 ``BizException``（400）——
       错误码与文案由 service 层决定（算法层不依赖业务异常）。
    """
    try:
        OptimizeDataValidator.validate(
            machine_info=machine_info or {},
            polymer_info=polymer_info or {},
            mold_info=mold_info or {},
        )
    except ValueError as exc:
        raise BizException(ERROR_REQUIRED_FIELD, str(exc)) from exc


# --- 落库 helper，DB 操作 ---
def _record_tuning_round(
    parent_param: ProcessParameter,
    changed_fields: Dict[str, Any],
    defect_feedbacks: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
    tuning_result: Optional[str],
    algorithm_recommendations: List[Dict[str, Any]],
    source_type: str,
) -> Recommendation:
    """记录这一轮调机：明确 base parameter，把反馈写入它的 TuningRecord，并挂上算法推荐。

    Args:
        parent_param: 当前活动轮，本轮三个动作都落在它身上。
        changed_fields: 用户手改且与库中原值确实不同的字段。
        defect_feedbacks: 本轮缺陷反馈，业务原样。
        observations: 本轮实测观察，业务原样。
        tuning_result: 本轮试模评价。
        algorithm_recommendations: 本轮的算法推荐。
        source_type: 建议来源类型。

    Returns:
        Recommendation: 挂在本轮上的算法推荐。

    【注意】三个动作互不阻断 —— 「用户没改字段」是最常见路径，任一段提前退出都会把
        整轮反馈与推荐丢掉。
    """
    # ---- parameter：确定成「这一轮实际在用的值」----
    # parent_param 指的是【本次提交反馈的那一轮】也就是第 N 轮，不是「上一轮已完成的轮次」
    # 【注意】这一段**不 return**：tuning_record 的写入与「参数改没改」无关。
    if changed_fields:
        if is_round_sealed(parent_param):
            _logger.warning(
                "[optimize/infer] 父轮已归档，跳过参数写回: parameter_id=%s",
                parent_param.id,
            )
        else:
            for key, value in changed_fields.items():
                setattr(parent_param, key, value)
            parent_param.save(update_fields=[*changed_fields.keys(), "updated_at"])

    # ---- tuning_record：反馈落到它上面，创建或更新 ----
    record = (
        TuningRecord.objects
        .filter(process_parameter=parent_param)
        .order_by("-created_at")
        .first()
    )
    if record is None:
        # 补建记录，previous_parameter 取父节点**派生时**的快照，即 diff 的 OLD 侧。
        base_record = None
        if parent_param.parent_param_id:
            base_record = (
                TuningRecord.objects
                .filter(process_parameter_id=parent_param.parent_param_id)
                .order_by("-created_at")
                .first()
            )
        _logger.warning(
            "[optimize] 父参数缺少 TuningRecord，补建: parameter_id=%s（业务层应保证 1:1）",
            parent_param.id,
        )
        record = TuningRecord(
            process_parameter=parent_param,
            defect_feedbacks=[],
            result="pending",
            previous_parameter=(base_record.previous_parameter if base_record else None),
        )

    # 丢弃合格态的缺陷信息，合格态产品无缺陷。
    # 【注意】必须**显式置空**，不能靠 `if defect_feedbacks:` 守卫跳过：
    #    守卫会让空数组不写入，于是「先填过缺陷、后改判合格」时历史缺陷会残留。
    if is_qualified_result(tuning_result):
        record.defect_feedbacks = []
    elif defect_feedbacks:
        record.defect_feedbacks = defect_feedbacks

    # 分开处理实测观察与缺陷，合格态**保留**实测观察
    # 合格与否与实测值无关，充填缺口等派生量在合格态同样有意义
    record.observations = observations

    # 查映射表 tuning.TUNING_RESULT_MAP，唯一真相源
    # 未命中（如 null）⇒ 保持原值不动，避免误写
    mapped_result = TUNING_RESULT_MAP.get(tuning_result) if tuning_result else None
    if mapped_result:
        record.result = mapped_result

    # 规范化训练样本，含变更、本轮缺陷与上下文，变更取两快照差异
    # 【注意】record 若是新建的，其 process_parameter 会重新读库
    #    ⇒ 拿到的是本轮最新值
    record.adjustments = build_adjustments(record)

    record.save()

    # ---- recommendation：针对本 parameter 的算法推荐，照它调就是下一轮参数 ----
    return Recommendation.objects.create(
        process_parameter=parent_param,
        source_type=source_type or "fuzzy_rule",
        recommendations=algorithm_recommendations,
        is_adopted=True,
    )


def _settle_recommendation_adoption(
    parent_param: ProcessParameter,
    tuning_result: Optional[str],
) -> None:
    """结算**父轮**的建议采纳状态（用本轮 feedback 完成反馈标记）。

    判定对象 = **parent_param 的父轮**（被建议的那一轮）：
    建那一轮时给出的建议，决定了本轮参数长什么样 ⇒ 本轮 feedback 反映的就是它的成败。

    Args:
        parent_param: 当前活动轮（其父轮才是被建议的那一轮）。
        tuning_result: 本轮试模评价。

    【注意】锚点语义：Recommendation 挂在**被建议的参数**上 ⇒
    「P_N 是否被采纳」= 查 P_N 自己的 Recommendation；
    反过来，要更新「P_{N-1} 给出的建议」的采纳状态，就得查 parent_param 的父轮。

    只在 ineffective 时置 False：本轮变差 ⇒ 那条建议没被采纳。
    """
    if tuning_result != "ineffective":
        return

    advised_param_id = parent_param.parent_param_id
    if not advised_param_id:
        return

    recommendation = (
        Recommendation.objects
        .filter(process_parameter_id=advised_param_id)
        .order_by("-created_at")
        .first()
    )
    if recommendation is None:
        return

    if recommendation.is_adopted:
        recommendation.is_adopted = False
        recommendation.save(update_fields=["is_adopted", "updated_at"])


def _create_new_round(
    condition: ProcessCondition,
    parent_param: ProcessParameter,
    parameters_dict: Dict[str, Any],
) -> ProcessParameter:
    """创建新轮次：ProcessParameter + 它自己的 TuningRecord（业务上两者 1:1，同批建）。

    Args:
        condition: 所属工艺条件。
        parent_param: 父轮参数。
        parameters_dict: 本轮参数值，须已是收口后的自洽参数集。

    Returns:
        ProcessParameter: 新轮次的 ProcessParameter，其 TuningRecord 同批建好。

    【注意】收口在算法内核统一做（那里同时产出落库值与响应值 ⇒ 两者同源），此处不重复收口。
    """
    writable = {
        k: v for k, v in parameters_dict.items()
        if k not in NON_SNAPSHOT_FIELDS
    }
    # 继承父记录的租户归属，同 condition 内必一致
    writable["company_id"] = parent_param.company_id
    writable["organization_id"] = parent_param.organization_id

    new_param = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=parent_param,
        param_source="system_inferred",
        **writable,
    )

    TuningRecord.objects.create(
        process_parameter=new_param,
        defect_feedbacks=[],
        observations=[],
        result="pending",
        previous_parameter=snapshot_parameter(parent_param),
    )

    return new_param


def optimize_from_condition(
    condition_id: int,
    parent_seq_idx: int,
    parameter: Optional[Dict[str, Any]] = None,
    feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """工艺优化主入口（基于已有 condition 开启调优轮次）。

    Args:
        condition_id: 工艺条件 ID（必填）。
        parent_seq_idx: 基准业务编号（必填）。
        parameter: 手动修改覆盖（可选），flat 字段需先由前端 parameterToFlat 翻译；
            None 表示从 ORM 反查 parent_param 作 baseline。
        feedback: 反馈信息（嵌套 dict，可选）。

    Returns:
        Dict[str, Any]: {"parameter": {...}, "suggestion": {"source_type",
            "recommendation_id", "groups"}}。

    Raises:
        BizException: 入参缺失、三维上下文不满足、或本轮无可用推荐。
    """
    feedback = feedback or {}
    # ---------- Step 0：转换接口反馈为算法入参，并做契约校验 ----------
    algorithm_feedback = _to_algorithm_feedback(feedback)

    # ---------- Step 1：装配推理上下文，只读 DB 不落库 ----------
    ctx = _resolve_infer_context(
        condition_id=condition_id,
        parent_seq_idx=parent_seq_idx,
        submitted_parameter=parameter,
    )
    condition_orm = ctx["condition"]
    parent_param_orm = ctx["parent_param"]
    baseline = ctx["baseline"]
    machine_info = ctx["machine_info"]
    polymer_info = ctx["polymer_info"]
    mold_info = ctx["mold_info"]

    # ---------- Step 2：纯推理，与 DB 无关 ----------
    new_parameter_dict, suggestion_payload, algorithm_recommendations = _infer_kernel(
        machine_info=machine_info,
        mold_info=mold_info,
        polymer_info=polymer_info,
        baseline=baseline,
        feedback=algorithm_feedback,
        interface_tag=f"infer(condition_id={condition_id}, parent_seq_idx={parent_seq_idx})",
        # 取本轮可见的规则库，租户隔离在 service 层完成
        libraries=_resolve_visible_libraries(condition_orm.company_id),
    )

    # ---------- Step 3：原子事务落库 ----------
    with db_transaction.atomic():
        # 取本轮试模评价，取自接口反馈原文，转换接头对它只做透传
        tuning_result = feedback.get("tuning_result")

        # 3.1 结算父轮的建议采纳状态，用本轮 feedback 完成反馈标记
        _settle_recommendation_adoption(
            parent_param=parent_param_orm,
            tuning_result=tuning_result,
        )

        # 3.2 记录这一轮，同步参数、写入用户反馈 TuningRecord、挂上算法推荐 Recommendation
        recommendation = _record_tuning_round(
            parent_param=parent_param_orm,
            changed_fields=ctx["user_changed_fields"],
            # 落库留痕用**业务原样**缺陷，保留 3D 坐标等业务字段，不用算法那份投影
            defect_feedbacks=feedback.get("defects") or [],
            # 实测观察同样落业务原样，转换头对 observations 不做投影
            observations=feedback.get("observations") or [],
            tuning_result=tuning_result,
            algorithm_recommendations=algorithm_recommendations,
            source_type=suggestion_payload.get("source_type") or "fuzzy_rule",
        )

        # 3.3 创建下一轮，ProcessParameter 与它自己的 TuningRecord 天然 1:1
        new_param = _create_new_round(
            condition=condition_orm,
            parent_param=parent_param_orm,
            parameters_dict=new_parameter_dict,
        )

    # ---------- Step 4: 组装响应 ----------
    return {
        "parameter": new_param.to_dict(),
        "suggestion": {
            **suggestion_payload,
            "recommendation_id": recommendation.id,
        },
    }


def optimize_from_provided(
    parameter: Dict[str, Any],
    feedback: Dict[str, Any],
    mold_info: Dict[str, Any],
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
) -> Dict[str, Any]:
    """纯推理入口 —— 不查 DB、不落库（第三方集成 / 前端试算 / 单元测试用）。

    Args:
        parameter: 参数字典，作为本轮推理的 baseline。
        feedback: 反馈信息。
        mold_info: 模具上下文，由调用方直传。
        machine_info: 设备上下文，由调用方直传。
        polymer_info: 材料上下文，由调用方直传。

    Returns:
        Dict[str, Any]: 与 optimize_from_condition 同结构，但无 recommendation_id、
            parameter 里无 id / seq_idx（未落库）。

    【注意】与主入口的差异：不传 condition_id / parent_seq_idx，不反查父轮、不落库。
    """
    feedback = feedback or {}
    # ---------- Step 0：转换接口反馈为算法入参，与 optimize_from_condition() 同一套转换与校验 ----------
    algorithm_feedback = _to_algorithm_feedback(feedback)
    # 调 _infer_kernel 纯推理，与 optimize_from_condition() 走同一函数
    # 第 3 个返回值 algorithm_recommendations 无需落库，FromProvided 是纯推理
    new_parameter_dict, suggestion_payload, _ = _infer_kernel(
        machine_info=machine_info or {},
        polymer_info=polymer_info or {},
        mold_info=mold_info or {},
        baseline=parameter,
        feedback=algorithm_feedback,
        interface_tag="infer_from_provided",
        # 【注意】**无租户上下文**，第三方集成 / 算法试算 / 烟测都属此类
        #    ⇒ 只取系统公共库，租户私库不外泄
        libraries=_resolve_visible_libraries(None),
    )

    return {
        "parameter": new_parameter_dict,       # 未落库，所以无 id / seq_idx
        "suggestion": suggestion_payload,      # 未落库，所以无 recommendation_id
    }

# --- 纯算法内核 —— 私有方法，入口共用 ---
def _infer_kernel(
    *,
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    mold_info: Dict[str, Any],
    baseline: Dict[str, Any],
    feedback: Dict[str, Any],
    interface_tag: str,
    libraries: Optional[List[LibraryRecord]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """推理一轮调优，算出应用推荐后的参数、建议分组和推荐明细。

    Args:
        machine_info: 设备上下文。
        polymer_info: 材料上下文。
        mold_info: 模具上下文。
        baseline: 调优基线参数，扁平字段名对应数值。
        feedback: 缺陷反馈。接口形态转算法形态见 :func:`_to_algorithm_feedback`。
        interface_tag: 日志前缀。
        libraries: 本轮可见的规则库档案。

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]: 应用推荐后的参数、
            建议分组载荷、推荐明细列表。

    Raises:
        BizException: 三维上下文缺失、当前设定值超机台可设定上限、算法无可用推荐、
            本轮无任何参数变化、产出位置类超出行程。
    """
    # ---------- 预处理层：入参校验 + 缺陷选取 ----------
    # 校验设备、材料、模具的必填字段，缺失则不进行推理
    _validate_optimize_inputs(machine_info, polymer_info, mold_info)

    # 选取缺陷，按优先级从入参里挑出本轮要处理的那一条（预处理层只做一次，L1 / L2 共用）
    feedback = select_defect(feedback)
    _logger.info(
        '[optimize] %s 缺陷选取: %s',
        interface_tag, feedback.get('defect_selection'),
    )
    # 校验基线越限：当前设定值超出允许区间则直接拒（位置参数同样是设定值，不分类）
    guard_parameter_limits(
        parameters=baseline,
        limits=build_limits(machine_info),
        scope='optimize',
        interface_tag=interface_tag,
    )

    # ---------- 第1层：调算法，出一堆平级建议 ----------
    # 组装算法入参，把三维上下文和基线装成算法能吃的入参
    algorithm_context = _compose_algorithm_context(
        machine_info=machine_info,
        polymer_info=polymer_info,
        mold_info=mold_info,
        parameter=baseline,
        feedback=feedback,
        libraries=libraries,
    )
    algorithm_result = _call_algorithms(algorithm_context)
    raw_recommendations = algorithm_result.get("recommendations", []) or []
    algorithm_sources = algorithm_result.get("algorithm_sources", {}) or {}

    # 检查引擎产出，一条建议都没给则直接拒
    if not raw_recommendations:
        _logger.warning(
            "[optimize] %s fail-fast: 无可用推荐 (algorithm_sources=%s)",
            interface_tag, algorithm_sources,
        )
        raise BizException(
            ERROR_OPERATION_FAILED,
            "推荐算法暂不可用，请稍后重试或联系管理员",
        )

    # 归一化建议，译成业务字段名并配上中文说明，丢掉值没变的项
    algorithm_recommendations = _normalize_recommendations(raw_recommendations)

    # ---------- 第2层：结合实际情况，确定明确的调整方向 ----------
    # 组装实际情况，含缺陷码、实测重量、制品总重、充填缺口与本轮选中的缺陷
    scenario_context = build_scenario_context(feedback, mold_info)
    # 推导阶段进度，看本轮哪些阶段还有缺陷、当前该推进哪一步
    stage_progress = derive_stage_progress(scenario_context.defect_codes)
    scenario_context = replace(
        scenario_context,
        extra={**scenario_context.extra, 'current_stage': stage_progress.current},
    )
    _logger.info('[optimize] %s 阶段进度: %s', interface_tag, stage_progress.to_trace())

    # 匹配调机场景，按当前情况从策略清单里选，匹配不上就不裁决
    strategies = sorted_scenario_strategies()
    scenario = select_strategy(strategies, scenario_context) if strategies else None
    priority_table = scenario.priority_table if scenario else None

    # 裁决调整方案，从候选里挑出本轮要采用的，定下谁让位、谁暂缓、按什么口径调
    plan = _decide_plan_by_strategy(
        algorithm_recommendations=algorithm_recommendations,
        priority_table=priority_table,
        scenario=scenario,
        context=scenario_context,
    )
    # 回填裁决状态到建议，让前端和落库看到的是同一份
    algorithm_recommendations = _apply_decision_status(
        algorithm_recommendations, plan.selection,
    )
    # 取出制品总重和实测制品重量，按充填量比例调行程时要用
    fill_weights = _fill_weights(scenario_context)

    # ---------- 第3层：整合参数，写入方向并保证锚点传导自洽 ----------
    # 应用调整计划，把计划写进参数，并按物理联动把连带量算出来
    integrated = apply_plan(
        baseline, plan, previous=baseline,
        fill_weights=fill_weights,
    )
    if integrated.touched:
        _logger.info('infer integration: %s', integrated.summary())

    # 检查落地情况，一个值都没变说明白跑了一轮，中止
    if integrated.landing_blocked:
        detail = _zero_landing_detail(integrated)
        _logger.warning(
            '[optimize] %s 零落地（保留项=%s，但无任何参数变化）: %s',
            interface_tag, list(integrated.landing_blocked), detail,
        )
        raise BizException(
            ERROR_OPERATION_FAILED,
            '本轮调整无法落地（%s）' % detail,
        )

    # ---------- 出口定稿：量化（落库/响应的同一份值，L4 也据此判定） ----------
    # 量化出口值，统一保留两位小数
    new_parameter_dict = _quantize_numeric_fields(integrated.values)

    # ---------- 第4层：校验参数合理性，只识别不改值 ----------
    validation = validate(
        new_parameter_dict,
        limits=resolve_range_limits(machine_info),
        machine_limits=to_upper_limits(build_limits(machine_info)),
    )
    if not validation.ok:
        _logger.info('infer validation: %s', validation.summary())

    # ---------- 出口：读校验结论 + 载荷组装 ----------
    # 检查参数是否超出机台对它设定的可设定上限，超出即机台设不进去 ⇒ 拒绝本轮
    if validation.over_limit_violations:
        message = format_unfit_param_message(validation.over_limit_violations)
        _logger.warning(
            '[optimize] %s 参数超出机台可设定上限，拒绝处理: %s ｜ %s',
            interface_tag,
            [item.to_trace() for item in validation.over_limit_violations],
            message,
        )
        raise BizException(ERROR_PROCESS_UNFIT_PARAM, message)

    # 组装建议分组，按分类归拢后交给前端
    suggestion_payload = _build_suggestion_payload(
        algorithm_recommendations=algorithm_recommendations,
        algorithm_sources=algorithm_sources,
        baseline=baseline,
        applied_values=integrated.values,
    )
    return new_parameter_dict, suggestion_payload, algorithm_recommendations


__all__ = ["optimize_from_condition", "optimize_from_provided", "build_recommendation_suggestion"]