"""工艺优化服务（调用链路编排层，不含算法实现）。

对外入口：
- optimize_from_condition(condition_id, parent_seq_idx, ...)  → POST /api/processes/algorithms/optimize/
- optimize_from_provided(parameter, feedback, 三维上下文) —— 纯推理（不查库、不落库），
  **尚无 HTTP 路由**，目前仅测试与脚本直接调用

调用链（optimize_from_condition）：
校验 feedback → 提取评价 → 装配上下文（只读）
→ 纯推理（含三维上下文契约校验）→ 原子落库 → 组装响应

设计约束：
- 算法侧是接口契约：本模块只负责编排，不实现具体推理
- 落库只有一个事务：落库阶段的多次写在一个 atomic 内完成（避免半成品落库）

设计要点：
- is_adopted 自动维护：被建议轮的下一轮 feedback 为 ineffective 时改 False
- 用户手改的工艺参数写回父记录，与新建轮次同生共死（详见 _record_tuning_round）

代码组织：全部为模块顶层函数（无类封装，不依赖 self/cls）；公开入口
optimize_from_condition / optimize_from_provided + 私有内核 _infer_kernel（入口共用）；
入参契约校验 _validate_optimize_inputs 由 _infer_kernel 统一调用。
"""
import logging
from collections.abc import Mapping
from typing import Dict, Any, List, Optional, Tuple, TypedDict

from django.db import transaction as db_transaction

from extensions.exceptions import (
    BizException,
    ERROR_DATA_INVALID,
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
from process.algorithms.decide_direction import (  # 第2层：结合实际情况，确定明确的调整方向
    Direction,
    PriorityTable,
    ScenarioContext,
    ScenarioPolicy,
    StrategyDecision,
    collect_candidates,
    resolve_direction,
)
from process.algorithms.anchors import unlandable_params  # 底座：物理关系（只定义一次）
from process.algorithms.integrate_params import (  # 第3层：整合参数
    IntegratedParams,
    apply_direction,
    diff_numeric_fields,
)
from process.algorithms.check_params import validate  # 第4层：校验参数合理性
from process.algorithms.base import AlgorithmRegistry
from process.algorithms.defect_selection import (  # 缺陷选取（实现在算法层；调用时机在 service 的预处理层）
    select_defect,
)
from process.algorithms.fuzzy import (
    field_names,  # 命名契约：业务字段名 ↔ 算法字段名（双向映射，契约层唯一真相源）
)
from process.algorithms.fuzzy.over_limit import (
    OverLimitItem,  # 越限记录（类型标注）
    detect_blocking_over_limits,  # 越限分层口径（device = 设备安全红线 ⇒ 阻断）
    detect_over_stroke_limits,  # 位置类超行程识别（stroke = 产品在本机做不出来 ⇒ 不阻断）
)
from process.algorithms.fuzzy.specs import (
    OPTIMIZE_FEEDBACK_FIELDS,
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OPTIMIZE_POLYMER_INFO_FIELDS,
    OPTIMIZE_MOLD_INFO_FIELDS,
    audit_feedback_defects,  # 缺陷反馈校验（契约层）
    OptimizeDataValidator,  # 入参契约校验器
    resolve_param_limits,  # 机台物理上限 → {参数族: 上限}
    resolve_position_limits,  # 设备实测注射行程 → {位置类参数名/族: 上限}
)  # 算法入参契约（字段字典）—— service 层按此白名单提取，不传全量 ORM 字段
from .tuning import (  # tuning_result → TuningRecord.result 映射 + 参数快照/训练样本组装（均为唯一真相源）
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
from .policies import (  # 第2层的策略读表与组装（业务知识在策略表，代码只负责读+匹配）
    resolve_policies,
)

_logger = logging.getLogger(__name__)


# 引擎在各算法模块内注册（`fuzzy/engine.py` / `empirical/empirical_algorithm.py`），
# 由 `process/algorithms/__init__.py` 的 import 链自动触发。


class AlgorithmContext(TypedDict):
    """算法引擎输入 context 的标准格式。

    由 _compose_algorithm_context 构造，_call_algorithms 使用。

    算法侧 recommend 接受 Dict[str, Any]（不限严格 schema），但 上下文装配 → 算法调用
    之间需要明确契约，否则字段缺失只能运行时发现。TypedDict 保留 Dict 调用风格
    + 提供类型提示 + 0 运行成本。

    字段语义：
    - machine_info: 设备信息（按 specs 白名单从 InjectionMoldingMachine + 选中的 InjectionUnit 提取）
    - polymer_info: 材料信息（按 specs 白名单从 Polymer 提取，算法内部按需取 abbreviation 等）
    - mold_info: 模具信息（按 specs 白名单从 Mold 提取，算法内部按需取 product_category 等）
    - process_parameter: 工艺参数（已翻译为算法侧命名，如 IL1/NT/CT）
    - feedback: 反馈信息（**缺陷已收敛** —— defects 只剩本轮处理的那条，
      另带 defect_selection 留痕；见 :func:`_resolve_defect_selection`）
    - libraries: 本轮可见的规则库档案（由 service 层按租户归属决定；**算法侧不持有租户概念**）

    【注意】**键恒在，值可空** —— 键缺失 = 契约违规（入口会拦），值为空 = 合法业务状态。
    """
    machine_info: Dict[str, Any]
    polymer_info: Dict[str, Any]
    mold_info: Dict[str, Any]
    process_parameter: Dict[str, Any]
    feedback: Dict[str, Any]
    libraries: Optional[List[LibraryRecord]]


# 必需 key 集合（用于 _call_algorithms 入口验证）
# = TypedDict 声明的全部 key（键恒在 ⇒ 全部必填；派生而非手写，改声明即同步）
_REQUIRED_CONTEXT_KEYS = frozenset(AlgorithmContext.__annotations__.keys())


# --- 参数分类（按 prefix 分组，与 Recommendation.recommendations 对齐） ---
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
    """参数名 → (category, icon)。"""
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
    """ORM → 完整 dict（仅排除 ORM 关系字段）。"""
    if instance is None:
        return {}
    return {
        f.name: getattr(instance, f.name)
        for f in instance._meta.fields
        if not f.is_relation
    }


def _to_business_param_name(param_name: str) -> str:
    """算法字段名 → 业务字段名（无法翻译时原样返回）。

    算法侧返回的 ``param`` 是算法命名空间（``IV0`` / ``BT1`` / ...），
    业务侧字段名是 ``inj_spd_1`` / ``brl_temp_1`` / ...。
    两者不在同一命名空间：不翻译就永远匹配不上 baseline，
    推荐值会被静默丢弃（表现为“算法有推荐，但参数没变”）。
    """
    if not param_name or not isinstance(param_name, str):
        return param_name
    return field_names.to_business_name(param_name) or param_name


def _param_label(business_name: str) -> str:
    """业务字段名 → 中文标签（取 ProcessParameter 字段的 verbose_name）。

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


# --- 缺陷反馈整理（预处理层，只做一次）---

def _resolve_defect_selection(feedback: Dict[str, Any]) -> Dict[str, Any]:
    """收敛缺陷反馈 —— 定出本轮处理哪个缺陷（service 预处理层的选取入口）。

    选取规则与留痕结构见 :mod:`process.algorithms.defect_selection`（唯一实现）。

    【注意】**调用限制**：结果供 L1（推理）与 L2（策略）共用 ——
       下游不得再自行选取，否则同一份反馈会推出两个缺陷。
    """
    return select_defect(feedback)


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
    # 用户手改且与库中原值**确实不同**的字段（供落库阶段精确写回）
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
        machine_info=_extract_machine_info(condition_orm),
        polymer_info=_extract_polymer_info(condition_orm),
        mold_info=_extract_mold_info(condition_orm),
        user_changed_fields=changed_fields,
    )


# --- 反查与上下文准备 ---
def _resolve_condition(condition_id: int) -> ProcessCondition:
    """反查工艺条件（含关联对象预加载）。

    预加载：injection_machine / polymer / mold（FK 一级）、
    injection_machine__injection_units（FK 二级，避免 N+1）。
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


# 通用兜底库编码（始终包含在可见库集合内）
BASE_LIBRARY_CODE = 'base'


def _filter_visible_libraries(
    libraries: List[LibraryRecord],
    company_id: Optional[int],
) -> List[LibraryRecord]:
    """按租户归属过滤库档案（可见性判据，**唯一定义处**）。

    库可见 ⟺ `owner_type == 'system'`（全平台公用）
    或（`owner_type == 'tenant'` 且归属租户 == 当前租户）。

    `company_id` 为空（第三方集成 / 离线 runner）⇒ 只留系统库。

    Args:
        libraries: 库档案清单。
        company_id: 当前租户公司主键（None = 无租户上下文）。

    Returns:
        可见的库档案（保持入参顺序）。
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

    可见范围：系统库全平台公用 + 本租户私库；`company_id` 为空
    （第三方集成 / 离线 runner）时只给系统库。

    `library_code` 指定时只用该库（同码的可见库都算），并叠加通用兜底库
    `'base'`；未指定时取全部可见模糊库（兜底库本就在其中）。

    只取启用的模糊库（`library_type='fuzzy'`），按 priority 降序。

    Returns:
        可见库档案列表（`library_id` / `library_code` / `library_name` /
        `owner_type` 齐全，算法侧据此取规则）。
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
    """反查该轮的基准工艺参数（condition + seq_idx 定位）。"""
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

    取值优先级：
    1. 本次提交带了参数 ⇒ 以提交值为准，并把**确实变了**的字段单独列出
    2. 没带 ⇒ 直接用库里的值

    【注意】本函数只在内存里覆盖，不写库——写回由落库阶段在事务内完成。

    Returns:
        (baseline, changed_fields)
        - baseline: 本轮推理起点（提交值优先）
        - changed_fields: 本次提交且与库中原值确实不同的字段
          （值相同的字段不进这个集合，避免无谓的 UPDATE 与 updated_at 变化）
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


def _extract_orm_fields_by_spec(
    source_orm_map: Dict[str, Any],
    spec_dict: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """按 specs 契约跨 source_model 取值（白名单）。

    按 spec 的 ``source_model`` 找对应 ORM 实例，取 ``attr_name`` 的值；
    ``None`` 值不纳入结果。

    与 ``field_contract`` 的分工：那边提供【校验机制】
    （``audit_field_completeness``），这里提供【提取机制】。
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
    """按 OPTIMIZE_MACHINE_INFO_FIELDS 契约提取 machine_info（白名单）。

    跨两张表合并：InjectionMoldingMachine.drive_system（机器主表）
    + InjectionUnit.max_set_*（按 condition.injection_index 选 unit；
      索引越界则告警并降级为空）。
    只返回 specs 声明的字段；ORM 元数据不传给算法。
    """
    machine = condition.injection_machine
    if machine is None:
        return {}

    injection_index = condition.injection_index or 0
    injection_units = list(machine.injection_units.all())
    if injection_index >= len(injection_units):
        _logger.warning(
            "[optimize] injection_index=%s 超出 machine(id=%s) 的 injection_units（共 %s 个）",
            injection_index, machine.id, len(injection_units),
        )
        return {}

    return _extract_orm_fields_by_spec(
        source_orm_map={
            "InjectionMoldingMachine": machine,
            "InjectionUnit": injection_units[injection_index],
        },
        spec_dict=OPTIMIZE_MACHINE_INFO_FIELDS,
    )


def _extract_polymer_info(condition: ProcessCondition) -> Dict[str, Any]:
    """按 OPTIMIZE_POLYMER_INFO_FIELDS 契约从 Polymer 提取 polymer_info（白名单）。"""
    polymer = condition.polymer
    if polymer is None:
        return {}
    return _extract_orm_fields_by_spec(
        source_orm_map={"Polymer": polymer},
        spec_dict=OPTIMIZE_POLYMER_INFO_FIELDS,
    )


def _extract_mold_info(condition: ProcessCondition) -> Dict[str, Any]:
    """按 OPTIMIZE_MOLD_INFO_FIELDS 契约从 Mold 提取 mold_info（白名单）。

    跨四张表合并：**Mold**（主表）+ **GatingSystem**（流道）+ **Cavity**（型腔）
    + **Gate**（浇口）—— 后三张是制品级物理基准的来源（壁厚 / 制品重 / 流道 /
    浇口类型），是冷却时间判级论域的必需输入（见 ``fuzzy/specs.py`` 的
    ``resolve_product_limits``）。

    【注意】**逐级取第一个**（多浇注系统 / 多型腔 / 多浇口时取第一个）：
      与专家引擎侧「多腔取第一个 / 多浇口取第一个」的既有口径一致。
      【注意】若将来出现多射工况，需改为按 ``condition.shot_index`` 选取
      （与 ``parameter_initialize._build_mold_snapshot`` 对齐）。

    【注意】**任一级缺失 ⇒ 该来源的字段全部不出现** ⇒ 调用方回落经验论域，
      **不报错、不阻塞**。
    """
    mold = condition.mold
    if mold is None:
        return {}
    gating = mold.gating_systems.first()
    cavity = gating.cavities.first() if gating is not None else None
    gate = cavity.gates.first() if cavity is not None else None
    return _extract_orm_fields_by_spec(
        source_orm_map={
            "Mold": mold,
            "GatingSystem": gating,
            "Cavity": cavity,
            "Gate": gate,
        },
        spec_dict=OPTIMIZE_MOLD_INFO_FIELDS,
    )


# --- 算法调用与上下文构造 ---
def _empty_algorithm_result() -> Dict[str, Any]:
    """统一空返回结构（避免在 _call_algorithms 里重复字面量）。"""
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

    业务约定：**经验推理只作兜底**。
    - 模糊推理有产出 ⇒ 最终建议集完全取自模糊推理，经验推理整体让位
      （否则同一参数会在建议列表里出现「模糊数值建议 + 经验方向建议」两条：
       工艺员看到的是重复项；若两者方向相反，更是自相矛盾）
    - 模糊推理无产出 ⇒ 由经验推理接手（只给方向、不给数值）

    优先级取自 ``AlgorithmRegistry._priorities``：fuzzy=1 → llm=2 → empirical=3。
    落选引擎的原始产出仍保留在 ``algorithm_sources`` 里
    （供 ``_resolve_primary_source`` 判定 source_type 与日志留痕）。

    【注意】选优**只影响建议集**，不影响 ``parameter``：
       经验推理项本就没有 ``recommended_value``，
       ``collect_candidates`` 早就会跳过它们 ⇒ 参数结果不变。

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
    """调用已注册引擎（各引擎并行）→ 汇总后选优，不查 DB。

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

    - 字段选择（业务多 → 算法少）
    - 字段名翻译（业务命名 → 算法命名，规则见算法侧契约 field_names.to_algo_params）
    - 上下文组装

    `libraries`：本轮可见的规则库档案（**由 service 层按租户归属决定**）——
    算法侧只按这份清单取规则，不持有租户概念。

    `feedback`：**已收敛**的缺陷反馈（见 :func:`_resolve_defect_selection`）。
    """
    algorithm_params = field_names.to_algo_params(parameter)
    return {
        'machine_info': machine_info,
        'polymer_info': polymer_info,
        'mold_info': mold_info,
        'process_parameter': algorithm_params,
        'feedback': feedback,
        'libraries': libraries,
    }


# --- 越限守卫（设备安全红线）---

def _format_limit_number(value: float) -> str:
    """上限 / 当前值的展示格式：整数不带小数尾巴（'100' 而不是 '100.0000'）。"""
    try:
        if float(value) == int(value):
            return str(int(value))
    except (TypeError, ValueError):
        pass
    return ('%.4f' % value).rstrip('0').rstrip('.')


def _format_over_limit_message(items: List[Any]) -> str:
    """越限拒绝文案 —— 说清「哪个参数 / 当前值 / 上限」。

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


def _guard_over_limit_settings(
    *,
    process_parameter: Dict[str, Any],
    machine_info: Dict[str, Any],
    interface_tag: str,
) -> None:
    """越限守卫 —— **设备安全红线**命中即拒绝（400）。

    判定时机：**调用算法之前**（service 预处理层）。
    判据是**纯事实**（当前设定值 vs 机台物理上限）⇒ 不需要结论做参照。

    判据：当前设定值 > 机台物理上限（`specs.resolve_param_limits`）。

    分层（安全分层口径，固化在算法契约层 `over_limit.BLOCKING_LIMIT_SOURCES`）：
      - ``device``（设定值类）—— **操作设备涉及安全** ⇒ 阻断；
      - ``material``（温度类）—— 降解/变色，不涉及设备安全 ⇒ 不阻断（只告警）。

    【注意】缺上限（机台没填）⇒ **不阻断**：缺数据不等于参数不合理。

    Raises:
        BizException(ERROR_DATA_INVALID): 命中设备安全红线
    """
    blocking = detect_blocking_over_limits(
        process_parameter, resolve_param_limits(machine_info))
    if not blocking:
        return
    _logger.warning(
        "[optimize] %s 越限拒绝（设备安全红线）: %s",
        interface_tag, [item.to_trace() for item in blocking])
    raise BizException(ERROR_DATA_INVALID, _format_over_limit_message(blocking))


def _drop_over_stroke_value_recommendations(
    recommendations: List[Dict[str, Any]],
    stroke_items: List[OverLimitItem],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """剔除「已超出行程的位置类参数」的**数值推荐**（只保留 check 告知）。

    矛盾在哪：位置类参数（MEL / IL / ML / VPTL）已经超出机台注射行程，
    而规则层仍可能因**缺陷前件**（如 ``SHORTSHOT_low THEN MEL_add_2``）推荐
    「再往上加」⇒ 一边告诉用户「这台机做不出这个产品」，一边又推一个
    更离谱的数值（实测：MEL 当前 758.07 → 推荐 760.19，行程只有 200mm）。

    处理方式：超行程参数的数值推荐**一律剔除**（不再推、不再写回 baseline），
    只留 :func:`_append_position_over_stroke_notices` 追加的那条 check 告知。

    【注意】剔除的**不是当前值**：baseline 里超行程的原值照旧保留（那是既有工艺的
    事实，抹掉反而看不出问题），本函数只管「别再往上推」。

    【注意】判据与 :func:`collect_candidates` 的入候选判据**严格一致**
    （都是 ``recommended_value is not None``）⇒ 凡是会被写回 baseline 的数值推荐，
    必定在这里被剔除 ⇒ 不会漏网。

    Args:
        recommendations: 本次推理的原始推荐列表（**不修改**，返回新列表）。
        stroke_items: :func:`detect_over_stroke_limits` 的产物。

    Returns:
        ``(保留的推荐列表, 被剔除的推荐列表)``；无超行程时两者分别为
        （入参列表本身, 空列表）。
    """
    if not stroke_items or not recommendations:
        return recommendations, []

    over_names = {item.param_name for item in stroke_items}
    kept: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    for rec in recommendations:
        # 【注意】``param`` 此刻还是**算法名**（MEL / IL0 ...）——本函数在
        #    ``_normalize_recommendations`` **之前**调用，还未译回业务字段名。
        if rec.get("param") in over_names and rec.get("recommended_value") is not None:
            dropped.append(rec)
            continue
        kept.append(rec)
    return kept, dropped


def _append_position_over_stroke_notices(
    recommendations: List[Dict[str, Any]],
    stroke_items: List[OverLimitItem],
) -> List[Dict[str, Any]]:
    """位置类超行程 ⇒ 追加一条「检查」类建议（**告知，不阻断**）。

    与 :func:`_guard_over_limit_settings` 同属「越限处理」的处理层，但**判据
    不同、处理方式必须不同**：

    - 那边 = **设备安全红线**（设定值类超机台可设定上限）⇒ 400 拒绝 ——
      判据是「用户把参数设错了」，改个值就能继续 ⇒ 值得拦；
    - 这边 = **产品与机台能力不匹配**（位置类当前值超设备注射行程）⇒
      **用户改不了**（是产品本身在这台机上做不出来，实测 MEL 56/70 行超行程）
      ⇒ 拦了也没有出路 ⇒ 只**告知**。

    【注意】告知走**既有的 check 通道**（``source='fuzzy.check'`` / ``direction='check'``）
    ⇒ **不改对外契约**：``_normalize_recommendations`` 会自动译业务字段名、生成
    中文标签，``_build_suggestion_payload`` 会按业务字段名自动归组
    （``met_end_pos`` → 熔胶参数 / ``inj_pos_1`` → 注射参数）。

    Args:
        recommendations: 本次推理的原始推荐列表（**不修改**，返回新列表）。
        stroke_items: :func:`detect_over_stroke_limits` 的产物
            （已超出行程的位置类参数）。

    Returns:
        追加了告知条目后的推荐列表；无位置类超行程时**原样返回**。
    """
    if not stroke_items:
        return recommendations

    # 多个位置参数同时超出行程（IL0 / ML0 / MEL 一起超）⇒ 合并成**一条**告知：
    # 它们说的是同一件事（这个产品在本机做不出来），逐条提示只会刷屏。
    # 取**超出量最大**的那项作代表。
    # 【注意】文案三段式：**事实**（哪个参数、超多少）→ **结论**（本机做不出来）
    #    → **出路**（换更大的机）。
    #    出路只给「换机」—— **以产品为目标**（产品形态已定），不给
    #    「减轻制品重量 / 减少型腔数」这类迁就设备的建议。
    top = max(stroke_items, key=lambda item: item.exceeded_by)
    label = _param_label(_to_business_param_name(top.param_name))
    others = len(stroke_items) - 1
    reason = (
        '%s当前 %smm，超出本机注射行程 %smm%s，本机无法生产该制品，请更换行程更大的设备'
        % (label,
           _format_limit_number(top.current_value),
           _format_limit_number(top.limit),
           ('（另有 %d 项超出行程）' % others) if others else '')
    )
    _logger.warning(
        "[optimize] 位置类超行程（仅告知，不阻断）: %s ｜ 告知: %s",
        [item.to_trace() for item in stroke_items], reason)

    # 【注意】**不就地改入参列表**：``_call_algorithms`` 返回的 ``recommendations`` 与
    #    ``algorithm_sources[subtype]`` 是**同一个 list 对象** ⇒ 就地 append 会把
    #    「引擎产出」污染成「引擎产出 + 本层告知」⇒ 选优/溯源口径失真。
    #    这里返回**新列表**，入参保持原样。
    return recommendations + [{
        'param': top.param_name,
        'current_value': top.current_value,
        'recommended_value': None,
        'confidence': None,
        'direction': 'check',
        'source': 'fuzzy.check',
        'reason': reason,
    }]




# --- 应用推荐 + 构造 suggestion ---
def _quantize_numeric_fields(
    params: Dict[str, Any],
    ndigits: int = 2,
) -> Dict[str, Any]:
    """工艺参数字典 → 数值字段量化（最多 ndigits 位小数）。

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


def _unlandable_veto(
    baseline: Dict[str, Any],
    scenario: Optional[ScenarioPolicy],
) -> Dict[str, str]:
    """本轮**落不了地**的候选项 → 让位理由（第2层不该选它当保留项）。

    物理背景（底座声明：:data:`process.algorithms.anchors.FREEDOM_YIELDS`）：
    注射阶段是**速度控制** ⇒ 改「注射时间」要让位给「注射速度」；
    而第3层的让位是**值回退**（改了也不生效）——
    ⇒ 当让位对象本轮不可调（场景禁入 / 基线项）时，
    被让位的量**改了也是白改** ⇒ 不能让它占掉本轮唯一的名额。

    【注意】**不选它 ≠ 丢掉它**：它仍进裁决留痕（让位理由），
    只是不占名额 ⇒ 名额**顺延**到下一个可落地的候选。
    """
    if scenario is None:
        return {}
    blocked = scenario.blocked_params or ()
    available = {name for name, value in baseline.items() if value is not None}
    return {
        name: f'本轮落不了地（让位对象 {free} 不可调）⇒ 让位'
        for name, free in unlandable_params(
            blocked_params=blocked,
            available_params=available,
        ).items()
    }


def _apply_decision_status(
    recommendations: List[Dict[str, Any]],
    decision: StrategyDecision,
) -> List[Dict[str, Any]]:
    """把第2层的裁决状态**就地**回填到每条建议。

    状态三取值（与 :meth:`StrategyDecision.status_of` 一致）：
    ``adopted``（本轮保留并执行）/ ``yielded``（让位）/ ``deferred``（暂缓）。

    【注意】**就地修改**：同一批 dict 既是响应载荷（``_build_suggestion_payload``）
    又是落库载荷（``Recommendation.recommendations``）⇒ 一处回填，
    **当轮响应 / 落库 / 历史轮次回显**三处同时带上状态。

    【注意】**不在候选集的建议不打标**（零变化 / 译不出 / 不在参数表里）
    ⇒ 前端按「有状态才过滤」处理 ⇒ **历史轮次没有状态字段**时
    照常显示，不会被误当成「未采用」。
    """
    for rec in recommendations:
        status, reason = decision.status_of(rec.get('param') or '')
        if status is None:
            continue
        rec['decision_status'] = status
        if reason:
            rec['decision_reason'] = reason
    return recommendations


def _resolve_direction(
    baseline: Dict[str, Any],
    algorithm_recommendations: List[Dict[str, Any]],
    strategy_table: Optional[PriorityTable] = None,
    scenario: Optional[ScenarioPolicy] = None,
    context: Optional[ScenarioContext] = None,
) -> Direction:
    """【第2层】结合实际情况，确定**明确的调整方向**。

    输入：算法给的平级建议（第1层的产出）+ 实际情况 + 策略数据。
    输出：**明确的调整方向** —— 调哪几个、调到什么值、谁让位、谁暂缓。

    注意：算法返回的 ``param`` 是算法命名空间（``IV0`` / ``BT1``），
    必须先译回业务字段名（``inj_spd_1`` / ``brl_temp_1``）才能命中 baseline。

    **方向定在 MEL 翻译之前**（歧义消解归第2层）—— 否则看不见 MEL 的意图
    （只看得到「调计量位置」），规则无处安放。

    【注意】``strategy_table`` 为空且 ``scenario`` 为空 ⇒ **不裁决** ⇒ 行为与
    「不接第2层」完全一致。

    【注意】``context``：**实际情况**（缺陷码 / 实测重量 / 目标重量）。
    场景要求按**充填量比例**解算行程且目标可解 ⇒ MEL 保留项直接落行程目标值，
    不再走「MEL 增量 → 计量位置」口径；目标解不出来 ⇒ 回落增量口径。
    """
    candidates = collect_candidates(
        algorithm_recommendations,
        baseline,
        name_of=_to_business_param_name,
    )
    direction = resolve_direction(
        candidates.names,
        candidates.targets,
        baseline,
        context=context,
        policy=scenario,
        table=strategy_table,
        veto_params=_unlandable_veto(baseline, scenario),
    )

    # 决策留痕：有让位 / 暂缓时才落日志（正常路径不产噪声）
    if direction.decision.yielded or direction.decision.deferred:
        _logger.info('infer direction: %s', direction.decision.to_trace())

    return direction


def _zero_landing_detail(integrated: IntegratedParams) -> str:
    """零落地的原因说明（让位回退 / 硬约束未处理）。

    给工艺员看的**人话**：告诉用户「为什么这一轮调不下去」，
    而不是抛一个无参的「操作失败」。
    """
    parts: List[str] = []
    if integrated.superseded_fields:
        parts.append('让位回退：%s' % '、'.join(
            '%s→%s' % item for item in integrated.superseded_fields))
    if integrated.unresolved:
        parts.append('硬约束未处理：%s' % '；'.join(integrated.unresolved))
    return '；'.join(parts) or '保留项未产生实际变化'


def _guard_zero_landing(
    baseline: Dict[str, Any],
    direction: Direction,
    integrated: IntegratedParams,
    interface_tag: str,
) -> None:
    """零落地守卫 —— **本该落地却一个量都没动** ⇒ 明确报错。

    触发条件（两个都要满足）：

    - 第2层**裁决出了保留项**（说明「本轮该调这个」）；
    - 第3层**实际没有任何字段发生变化**（说明「调了等于没调」）。

    【注意】**为什么要报错**：静默产出一个与上一轮**一模一样**的新轮次，
    用户看到的是「一屏建议、参数没动」，无处追因 ⇒ 宁可明确报错。

    【注意】**不管另一种形态**：第2层**根本没保留任何候选**
    （规则没给出可用调整）属于另一回事，既有行为不变，不在本守卫范围内。
    """
    if not direction.decision.kept:
        return
    if diff_numeric_fields(baseline, integrated.values):
        return
    detail = _zero_landing_detail(integrated)
    _logger.warning(
        '[optimize] %s 零落地（保留项=%s，但无任何参数变化）: %s',
        interface_tag, list(direction.decision.kept), detail,
    )
    raise BizException(
        ERROR_OPERATION_FAILED,
        '本轮调整无法落地（%s）' % detail,
    )


def _resolve_primary_source(algorithm_sources: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
    """选取主要算法来源（按 AlgorithmRegistry._priorities 顺序）。

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
    """数值 → 建议文案用的短字符串（最多 2 位小数，去掉尾随 0）。

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
    """提取规则引用（该建议命中了哪几条规则）。

    来源优先级：
    1. ``matched_rules`` —— 模糊推理引擎透出的**命中规则明细**（开发者模式）。
       每项 = ``{'rule': 规则串, 'weight': 组内占比, 'raw_activation': 原始激活度}``
       ⇒ 取其中的 ``rule`` 字段（**完整规则串**，一眼能看懂命中逻辑）。
    2. ``rule_refs`` —— 算法侧直接给的规则引用列表（兼容其他引擎 / 存量数据）。

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


# --- 调整方向 → 中文（建议文案用） ---
_DIRECTION_CN = {
    "increase": "提高",
    "decrease": "降低",
    "hold": "保持",
    "check": "检查",
}


def build_recommendation_suggestion(recommendation, parameter) -> dict:
    """Recommendation → 前端 Suggestion 结构（历史轮次回显用）。

    锚点语义：Recommendation 挂在**被建议的那个参数**上（FK process_parameter），
    因此「针对该轮参数的建议」就显示在该轮详情区。

    Recommendation.recommendations 存的是【已规范化】的扁平推荐列表
    （业务字段名 + 中文文案 + 已丢弃零变化项），需按业务字段分类重组成前端要的 groups。
    baseline 用该轮参数字段还原 —— 与落库时 _build_suggestion_payload 的过滤口径一致
    （只保留参数表里真实存在的字段）。

    【注意】**不传 applied_values**：落地值在「按建议调整后的那一轮」上，
    而被建议轮的记录里没有它 ⇒ 跨轮取会让回显多一次查询；
    历史轮次的 applied_value 直接不填（前端按「有则用」处理）。

    Args:
        recommendation: Recommendation 实例
        parameter: 该建议所针对的 ProcessParameter（用于还原 baseline）

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
    payload = _build_suggestion_payload(recs, {}, baseline, applied_values=None)
    return {
        "source_type": source_type,
        "groups": payload.get("groups", []),
        "adopted": recommendation.is_adopted,
    }


def _normalize_recommendations(
    algorithm_recommendations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """把算法推荐规范化为「面向用户」的形态（落库与展示共用同一份）。

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
    applied_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """扁平推荐按 category 分组，构建 SuggestionGroup。

    baseline 不为 None 时只保留在 baseline 中存在的推荐字段
    （与 collect_candidates 严格对齐）。

    ``applied_values``：**已采用项的实际落地值**（字段名 → 值）。
    当轮响应传 ``integrated.values``（整合后的最终参数集，**未量化**）；
    历史轮次回显**不传**（落地值在「按建议调整后的那一轮」上 ⇒ 被建议轮没有它）。
    【注意】**只给已采用项**：未采用项的「落地值」就是原值，没有意义。
    """
    source_type = _resolve_primary_source(algorithm_sources) or "none"

    if not algorithm_recommendations:
        return {"source_type": source_type, "groups": []}

    # 一致性过滤：与 collect_candidates 严格对齐
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
        # 裁决状态：adopted 已采用 / yielded 让位 / deferred 暂缓。
        # 【注意】**无状态就不给字段**（历史轮次没有该字段 / 未进候选集）⇒ 前端按「有则用」处理。
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

    接口形态随前端演进（缺陷 ID、3D 点选坐标、业务标签……），
    算法形态只认契约声明的字段 ⇒ 差异全部收在这一层。

    转换规则：
    - 缺陷项按 ``OPTIMIZE_FEEDBACK_FIELDS`` 投影，多余字段不带；
    - ``observations`` 原样透传（算法只读 param_key / value）；
    - ``tuning_result``（本轮试模评价）整体透传。

    【注意】**缺陷列表可以为空**，前提是给了「合格」（``tuning_result=qualified``）——
       合格态产品没有缺陷，不带缺陷信息；其余评价档位要求缺陷列表非空。

    Raises:
        BizException(ERROR_REQUIRED_FIELD): 转换结果不满足算法契约
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

    【注意】校验器抛 ``ValueError``，本函数转成 ``BizException``（400）——
       错误码与文案由 service 层决定（算法层不依赖业务异常）。

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


# --- 落库 helper（DB 操作） ---
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

    本段的三个动作都落在**同一个锚点**（parent_param = 当前活动轮）：

    **parameter**（下一轮建议的 base，也是反馈的载体）
      - 无 changed_fields（基于库中原值）⇒ 不动；
      - 用户改了字段 ⇒ 同步到库，保证 DB 与用户实际在用的参数一致
        （只写真正变化的字段；tuning-feedback 不写 ProcessParameter）；
      - 归档轮次（已有评价、参数锁死）⇒ 跳过并记 warning：参数是「当时实际用的工艺」，
        写回会改写归档（不影响子轮次：基线已按用户改值覆盖）；
      - 【注意】必须在落库阶段写回：放到装配阶段会造出「参数改了但新轮次没建成」的
        中间态，且在事务外无法回滚。

    **tuning_record**（该 parameter 的调机记录：缺陷反馈 + 实测观察 + 试模结果）
      - 缺陷与效果标签写到**本 parameter 自己**的记录（不写到父轮）：
        界面上的「第 N 轮」= 参数(N) + 反馈(N)；
      - 实测观察同样写本轮自己的记录（算法用实测重量派生充填缺口，
        留痕后才能复盘当初的判定依据）；
      - 记录不存在 ⇒ 补建（业务层保证 1:1，这里兜底）。

    **recommendation**（针对本 parameter 给的算法推荐，照它调 ⇒ 下一轮参数）
      - 挂在本 parameter 上；is_adopted 默认 True，等下一轮 feedback 来结算。

    【注意】**参数名容易误读**：parent_param 是【本次提交反馈的那一轮】（第 N 轮），
    不是“上一轮已完成的轮次”（infer 请求的 parent_seq_idx 就是当前活动轮的 seq_idx）。

    【注意】三个动作**互不阻断**：「用户没改字段」是最常见路径，
    若 parameter 段提前退出 ⇒ 整轮 feedback 与推荐都会丢。
    """
    # ---- parameter：确定成「这一轮实际在用的值」----
    # 【注意】这一段**不 return**：tuning_record 的写入与「参数改没改」无关，
    #    「用户没改字段」是最常见路径，在此退出 ⇒ 整轮反馈丢失。
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

    # ---- tuning_record：反馈落到它上面（创建或更新）----
    record = (
        TuningRecord.objects
        .filter(process_parameter=parent_param)
        .order_by("-created_at")
        .first()
    )
    if record is None:
        # 补建。previous_parameter = 父节点**派生时**的快照（diff 的 OLD 侧）。
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

    # 合格态：产品无缺陷 ⇒ 缺陷信息一律丢弃。
    # 【注意】必须**显式置空**（而不是靠 `if defect_feedbacks:` 守卫跳过）：
    #    守卫会让空数组不写入，于是「先填过缺陷、后改判合格」时历史缺陷会残留。
    if is_qualified_result(tuning_result):
        record.defect_feedbacks = []
    elif defect_feedbacks:
        record.defect_feedbacks = defect_feedbacks

    # 实测观察与缺陷分开处理：合格态**保留**实测观察
    # （合格与否与实测值无关 —— 充填缺口等派生量在合格态同样有意义）
    record.observations = observations

    # 映射表共用 tuning.TUNING_RESULT_MAP（唯一真相源）
    # 未命中（如 null）⇒ 保持原值不动，避免误写
    mapped_result = TUNING_RESULT_MAP.get(tuning_result) if tuning_result else None
    if mapped_result:
        record.result = mapped_result

    # 规范化训练样本：变更（两快照差异）+ 本轮缺陷 + 上下文
    # 【注意】record 若是新建的，其 process_parameter 会重新读库
    #    ⇒ 拿到的是本轮最新值
    record.adjustments = build_adjustments(record)

    record.save()

    # ---- recommendation：针对本 parameter 的算法推荐（照它调 ⇒ 下一轮参数）----
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

    parameters_dict 来自 baseline（父记录全量快照），含父记录的
    id / created_at / param_source / seq_idx 等系统字段，直接展开会与
    create() 的显式入参冲突（multiple values for keyword argument），
    故按 NON_SNAPSHOT_FIELDS 过滤后再落库。

    【注意】入参须**已是收口后的自洽参数集** —— 收口在算法内核（纯推理那一步）统一做
    （那里同时产出落库值与响应值 ⇒ 两者同源）；此处不重复收口。

    **TuningRecord 与参数天然 1:1 ⇒ 同批创建**（result=pending，等该轮自身试模反馈）：
    - **不写入 defect_feedbacks / observations**（固定为空）：新轮次尚未试模，
      没有属于它自己的缺陷与实测值。
      配对语义见 _record_tuning_round —— 缺陷与效果标签只能落在参数(N) 自己的
      TuningRecord 上；父轮的缺陷已写入父轮自己的记录，不复制到子轮（否则回显串轮）。
    - previous_parameter = 父轮参数的快照（diff 的 OLD 侧），供后续轮次比对。
    """
    writable = {
        k: v for k, v in parameters_dict.items()
        if k not in NON_SNAPSHOT_FIELDS
    }
    # 租户归属继承父记录（同 condition 内必一致）
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
        condition_id: 工艺条件 ID（必填）
        parent_seq_idx: 基准业务编号（必填）
        parameter: 手动修改覆盖（可选，flat 字段对齐 ProcessParameterSchema；
                   None 表示从 ORM 反查 parent_param 作 baseline，前端 UI 改了的
                   工艺参数需先由前端 parameterToFlat 翻译为 flat dict 再传入）
        feedback: 反馈信息（嵌套 dict，可选）

    Returns:
        {
            "parameter": {...},
            "suggestion": {
                "source_type": str,
                "recommendation_id": int,
                "groups": [...]
            }
        }
    """
    feedback = feedback or {}
    # Step 0: 接口反馈 → 算法入参（转换 + 契约校验）
    algorithm_feedback = _to_algorithm_feedback(feedback)

    # ---------- Step 1: 装配推理上下文（只读 DB，不落库）----------
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

    # ---------- Step 2: 纯推理（与 DB 无关）----------
    new_parameter_dict, suggestion_payload, algorithm_recommendations = _infer_kernel(
        machine_info=machine_info,
        mold_info=mold_info,
        polymer_info=polymer_info,
        baseline=baseline,
        feedback=algorithm_feedback,
        interface_tag=f"infer(condition_id={condition_id}, parent_seq_idx={parent_seq_idx})",
        # 本轮可见的规则库（租户隔离在 service 层完成）
        libraries=_resolve_visible_libraries(condition_orm.company_id),
    )

    # ---------- Step 3: 原子事务落库 ----------
    with db_transaction.atomic():
        # 本轮试模评价（取自接口反馈原文；转换接头对它只做透传）
        tuning_result = feedback.get("tuning_result")

        # 3.1 结算父轮的建议采纳状态（用本轮 feedback 完成反馈标记）
        _settle_recommendation_adoption(
            parent_param=parent_param_orm,
            tuning_result=tuning_result,
        )

        # 3.2 记录这一轮：参数同步 + 用户反馈（TuningRecord）+ 算法推荐（Recommendation）
        recommendation = _record_tuning_round(
            parent_param=parent_param_orm,
            changed_fields=ctx["user_changed_fields"],
            # 落库留痕用**业务原样**缺陷（保留 3D 坐标等业务字段），非算法那份投影
            defect_feedbacks=feedback.get("defects") or [],
            # 实测观察同样落业务原样（转换头对 observations 不做投影）
            observations=feedback.get("observations") or [],
            tuning_result=tuning_result,
            algorithm_recommendations=algorithm_recommendations,
            source_type=suggestion_payload.get("source_type") or "fuzzy_rule",
        )

        # 3.3 创建下一轮（ProcessParameter + 它自己的 TuningRecord，1:1 天然一体）
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
    """【FromProvided 入口】纯推理 —— 不查 DB、不落库。

    适用场景：
    - 第三方集成（其库内无我们的 masterdata）
    - 算法试算（前端 dry-run）
    - 单元测试 / 烟测

    与 optimize_from_condition() 的关键差异：
    - 不传 condition_id / parent_seq_idx（无 ORM）
    - 三维上下文由调用方直传
    - 无反查 parent、无落库
    - 响应不含 recommendation_id，parameter 无 id / seq_idx（未落库）
    """
    feedback = feedback or {}
    # Step 0: 接口反馈 → 算法入参（与 optimize_from_condition() 同一套转换与校验）
    algorithm_feedback = _to_algorithm_feedback(feedback)
    # 调 _infer_kernel 纯推理（与 optimize_from_condition() 走同一函数）
    # 第 3 个返回值 algorithm_recommendations 无需落库（FromProvided 是纯推理）
    new_parameter_dict, suggestion_payload, _ = _infer_kernel(
        machine_info=machine_info or {},
        polymer_info=polymer_info or {},
        mold_info=mold_info or {},
        baseline=parameter,
        feedback=algorithm_feedback,
        interface_tag="infer_from_provided",
        # 【注意】**无租户上下文**（第三方集成 / 算法试算 / 烟测）
        #    ⇒ 只取系统公共库（租户私库不外泄）
        libraries=_resolve_visible_libraries(None),
    )

    return {
        "parameter": new_parameter_dict,       # 未落库 ⇒ 无 id / seq_idx
        "suggestion": suggestion_payload,      # 无 recommendation_id
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
    """【纯算法内核】6 维 dict
    → (new_parameter, suggestion, algorithm_recommendations)

    同名对应 ``parameter_initialize._infer_kernel`` —— 但**入参维度不同**
    （那条是 4 维 + ``company_id``，专家引擎在算法层持有租户概念）。
    不依赖 self/cls，无副作用。

    Args:
        machine_info: 设备 dict（HMI 范围由算法自挑）
        polymer_info: 材料 dict（含 abbreviation）
        mold_info: 模具 dict（含 product_category）
        baseline: 调优基线（flat 字段，对齐 ProcessParameterSchema）
        feedback: **算法侧投影**的缺陷反馈（defects 只剩 keyword_name / level /
            position，另带 observations / tuning_result）—— 转换见
            :func:`_to_algorithm_feedback`；**本函数内收敛** defects
            （见 :func:`_resolve_defect_selection`）
        interface_tag: fail-fast 日志前缀
        libraries: 本轮可见的规则库档案（**由 service 层按租户归属决定**）——
            算法侧只按这份清单取规则，不持有租户概念

    Returns:
        (new_parameter_dict, suggestion_payload, algorithm_recommendations)
        - new_parameter_dict: 应用推荐后的扁平 dict
        - suggestion_payload: {source_type, groups}，groups 已按 baseline 过滤
        - algorithm_recommendations: **已规范化**的推荐列表（业务字段名 +
          中文文案 + 丢弃零变化项 + 回填裁决状态）—— 落库与展示共用这一份

    Raises:
        BizException(ERROR_REQUIRED_FIELD): 三维上下文缺失必填字段
        BizException(ERROR_OPERATION_FAILED): 算法无任何推荐
    """
    # 入参契约校验（论域上界缺失 → 判级失真，提前拒）
    _validate_optimize_inputs(machine_info, polymer_info, mold_info)
    
    # ---------- 预处理层：选缺陷（收敛成 1 条）+ 输入参数校验 ----------
    # 【注意】**只收敛一次** ⇒ L1（推理）与 L2（策略）共用这一份
    #    ⇒ 同一份反馈不会推出两个缺陷。
    feedback = _resolve_defect_selection(feedback)
    # 缺陷选取留痕（**选了谁 / 按什么规则 / 跳过了谁**）
    _logger.info(
        '[optimize] %s 缺陷选取: %s',
        interface_tag, feedback.get('defect_selection'),
    )

    # 【注意】判的是**当前设定值** vs 机台物理上限（**纯事实**）⇒ 不等结论、直接拒。
    #    超限往往就是「推不出结论」的根因 ⇒ 先报根因比报「推荐算法暂不可用」准确。
    #    （参数按算法命名判定 —— 翻译规则见 field_names.to_algo_params）
    _guard_over_limit_settings(
        process_parameter=field_names.to_algo_params(baseline),
        machine_info=machine_info,
        interface_tag=interface_tag,
    )

    # ---------- 第1层：调算法（出一堆平级建议）----------
    # 装成 AlgorithmContext（service 内实现细节）
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

    # fail-fast 守卫（基于算法原始输出：有没有给出推荐）
    if not raw_recommendations:
        _logger.warning(
            "[optimize] %s fail-fast: 无可用推荐 (algorithm_sources=%s)",
            interface_tag, algorithm_sources,
        )
        raise BizException(
            ERROR_OPERATION_FAILED,
            "推荐算法暂不可用，请稍后重试或联系管理员",
        )

    # 位置类超行程：剔除该参数的**数值推荐** + 追加一条 check 告知
    # （**告知，不阻断**）—— 详见 _drop_over_stroke_value_recommendations
    #   与 _append_position_over_stroke_notices。
    # 【注意】必须放在 fail-fast **之后**：否则「只有超行程告知、没有任何数值建议」会被
    #    fail-fast 当成「有推荐」而放行，掩盖真正的「推不出结论」。
    stroke_items = detect_over_stroke_limits(
        algorithm_context.get('process_parameter') or {},
        resolve_position_limits(machine_info),
    )
    raw_recommendations, dropped_recommendations = (
        _drop_over_stroke_value_recommendations(raw_recommendations, stroke_items)
    )
    if dropped_recommendations:
        # 留痕：剔了什么、为什么（超行程的参数不能再往上推）
        _logger.warning(
            "[optimize] 剔除超行程位置参数的数值推荐: %s ｜ 超行程参数: %s",
            [{'param': rec.get('param'),
              'current': rec.get('current_value'),
              'recommended': rec.get('recommended_value')}
             for rec in dropped_recommendations],
            [item.to_trace() for item in stroke_items],
        )
    raw_recommendations = _append_position_over_stroke_notices(
        raw_recommendations, stroke_items,
    )

    # 规范化：业务字段名 + 业务文案 + 过滤零变化项
    # （落库与展示共用这一份，Recommendation.recommendations 存的就是它）
    algorithm_recommendations = _normalize_recommendations(raw_recommendations)

    # 第2层的策略数据：**业务知识在策略清单文件**（场景 / 优先集 / 名额 /
    # 目标口径）—— 这里只做「读取 + 匹配 + 组装」；没命中 ⇒ 不裁决。
    # 【注意】场景条件引用**本轮实际处理的缺陷**（收敛后的 `feedback['defects']`）
    #    ⇒ 只能在本层算（调用方拿不到收敛结果）。
    policy_resolution = resolve_policies(
        feedback=feedback,
        mold_info=mold_info,
    )

    # 阶段进度留痕 —— 本轮哪些阶段还有缺陷、当前该推进哪一步。
    # 【注意】场景匹配**引用**它：``current_stage`` 经
    #    ``ScenarioContext.extra`` 注入 ⇒ 策略清单可据此判场景
    #    （如「短射 + 仍在打足阶段 ⇒ 充填量优先」）。
    _logger.info(
        '[optimize] %s 阶段进度: %s',
        interface_tag,
        (policy_resolution.stage_progress.to_trace()
         if policy_resolution.stage_progress else None),
    )

    # ---------- 第2层：结合实际情况，确定明确的调整方向 ----------
    direction = _resolve_direction(
        baseline=baseline,
        algorithm_recommendations=algorithm_recommendations,
        strategy_table=(policy_resolution.priority_table if policy_resolution else None),
        scenario=(policy_resolution.scenario if policy_resolution else None),
        context=(policy_resolution.context if policy_resolution else None),
    )

    # 裁决状态回填到建议（**就地**）⇒ 响应 / 落库 / 历史回显三处一致
    _apply_decision_status(algorithm_recommendations, direction.decision)

    # ---------- 第3层：整合参数（写入方向 + 锚点传导自洽）----------
    # 放在这里 ⇒ **落库值与响应值同源**（响应体就是这份 dict）。
    integrated = apply_direction(baseline, direction, previous=baseline)
    if integrated.touched:
        _logger.info('infer integration: %s', integrated.summary())

    # 零落地守卫：**本该落地却一个量都没动** ⇒ 明确报错
    # （不静默产出「与上一轮一模一样」的新轮次）
    _guard_zero_landing(baseline, direction, integrated, interface_tag)

    # ---------- 第4层：校验参数合理性（只报不阻断）----------
    # 出口参数统一量化（最多 2 位小数）—— 落库（``_create_new_round``）
    # 与响应（``parameter``）同源于此 ⇒ 「DB / 响应」两处口径一致。
    # 【注意】**建议文案里的值不量化**（``applied_value`` 取自未量化的
    # ``integrated.values``，``recommended_value`` 取自算法原始推荐值）⇒
    # 与前端 ``appliedText`` 的 1e-9 比较**同口径**（两边都不量化）⇒ 不误判。
    new_parameter_dict = _quantize_numeric_fields(integrated.values)
    validation = validate(new_parameter_dict)
    if not validation.ok:
        _logger.info('infer validation: %s', validation.summary())
    suggestion_payload = _build_suggestion_payload(
        algorithm_recommendations=algorithm_recommendations,
        algorithm_sources=algorithm_sources,
        baseline=baseline,
        applied_values=integrated.values,
    )
    return new_parameter_dict, suggestion_payload, algorithm_recommendations


__all__ = ["optimize_from_condition", "optimize_from_provided", "build_recommendation_suggestion"]