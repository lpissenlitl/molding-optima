"""参数提取专区：按 spec 契约把「原始数据」取成「算法入参」。

两条链路的提取方式**本就不同**（载体、``None`` 口径、守卫各异）⇒ 本模块
**并列提供**各自形态的提取函数，**不强行拉成同一套接口**；调用方按需自取。

真正共用的只有一步 —— 「遍历 spec、按 ``source_model`` 定位数据源、取
``attr_name``」⇒ 由两个取值器承担（ORM 版 / 快照版）；其余各归各家：

- **``None`` 的去留**：ORM 版**不纳入**（只保留有值的字段）；快照版**纳入**
  （前端要能编辑/展示所有 spec 字段）⇒ 各自固定，不做成开关；
- **未知 ``source_model``**：快照版按空 dict 兜底（取到 ``None``）；
  需要显式报错的走**独立守卫**（``_assert_known_sources``），不塞进取值器；
- **维度特有补算**（如 ``gate_radius`` = 直径 / 2、``runner_weight`` 的
  fallback）⇒ 留在各自的维度函数里，不上提。

与 ``field_contract`` 的分工：那边提供【校验机制】
（``audit_field_completeness``），这里提供【提取机制】。

【注意】本模块**同时服务两条链路**，故内部按契约分块、**刻意不做统一**：

- 「优化链路」块：载体是 **ORM 实例**，spec 来自 ``fuzzy/specs.py``
  的 ``OPTIMIZE_*_FIELDS``；
- 「初始化链路」块：载体是**快照 dict**，spec 来自 ``expert/specs.py``
  的 ``*_INFO_FIELDS``。
"""
import logging
from typing import Any, Dict, Mapping

from process.algorithms.expert.specs import (
    MACHINE_INFO_FIELDS,
    MOLD_INFO_SPEC,
    POLYMER_INFO_FIELDS,
)
from process.algorithms.fuzzy.specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OPTIMIZE_MOLD_INFO_FIELDS,
    OPTIMIZE_POLYMER_INFO_FIELDS,
)

_logger = logging.getLogger(__name__)


# --- 共用取值器：真正统一的那一步 ---


def extract_orm_fields(
    source_orm_map: Mapping[str, Any],
    spec_dict: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    """从 **ORM 实例**取值（``getattr``）—— 优化链路的取值口径。

    - 按 spec 的 ``source_model`` 找对应 ORM 实例，取 ``attr_name`` 的值；
    - ``None`` 值**不纳入**结果（只保留有值的字段）；
    - 未知 ``source_model``（映射里没有该实例）⇒ 取不到值 ⇒ 该字段不出现。

    Args:
        source_orm_map: ``source_model`` → ORM 实例。
        spec_dict: 契约字典（``target_key`` → ``{source_model, attr_name, ...}``）。

    Returns:
        ``{target_key: 值}``。
    """
    extracted: Dict[str, Any] = {}
    for target_key, spec in spec_dict.items():
        source_model = spec.get('source_model')
        attr_name = spec.get('attr_name')
        if not source_model or not attr_name:
            continue
        orm_instance = source_orm_map.get(source_model)
        if orm_instance is None:
            continue
        value = getattr(orm_instance, attr_name, None)
        if value is not None:
            extracted[target_key] = value
    return extracted


def extract_snapshot_fields(
    source_map: Mapping[str, Mapping[str, Any]],
    spec_dict: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    """从**快照 dict**取值（``.get``）—— 初始化链路的取值口径。

    - 按 spec 的 ``source_model`` 找对应子表，取 ``attr_name`` 的值；
    - ``None`` 值**纳入**结果（前端要能编辑/展示所有 spec 字段）；
    - 未知 ``source_model`` ⇒ 按空 dict 兜底 ⇒ 取到 ``None``；
    - 无 ``attr_name`` 的**计算字段**跳过（由维度函数单独处理）。

    Args:
        source_map: ``source_model`` → 该来源的字段字典。
        spec_dict: 契约字典。

    Returns:
        ``{target_key: 值}``。
    """
    extracted: Dict[str, Any] = {}
    for target_key, spec in spec_dict.items():
        attr_name = spec.get('attr_name')
        if not attr_name:
            continue
        data = source_map.get(spec.get('source_model') or '') or {}
        extracted[target_key] = data.get(attr_name)
    return extracted


def _assert_known_sources(
    spec_dict: Mapping[str, Mapping[str, Any]],
    known_sources: tuple,
    spec_name: str,
) -> None:
    """守卫：spec 里出现未知 ``source_model`` ⇒ 显式报错（防静默取错数据）。

    刻意做成**独立守卫**而非取值器的开关 ⇒ 取值器的语义保持单一。

    Args:
        spec_dict: 契约字典。
        known_sources: 本层已处理的 ``source_model`` 集合。
        spec_name: 契约名（用于错误消息）。

    Raises:
        ValueError: 存在未知 ``source_model``。
    """
    for target_key, spec in spec_dict.items():
        if not spec.get('attr_name'):
            continue  # 计算字段：不取值 ⇒ 不涉及 source_model
        source_model = spec.get('source_model')
        if source_model in known_sources:
            continue
        raise ValueError(
            f"{spec_name}['{target_key}'] 的 source_model={source_model!r} "
            f"未在 service 层处理（已知：{' / '.join(known_sources)}）"
        )


# =============================================================================
# 优化链路（ORM 直取 · fuzzy 契约）
# =============================================================================


def extract_machine_info(condition) -> Dict[str, Any]:
    """按 ``OPTIMIZE_MACHINE_INFO_FIELDS`` 契约提取 machine_info（白名单）。

    跨两张表合并：``InjectionMoldingMachine.drive_system``（机器主表）
    + ``InjectionUnit.max_set_*``（按 ``condition.injection_index`` 选 unit；
    索引越界则告警并降级为空）。
    只返回 specs 声明的字段；ORM 元数据不传给算法。

    Args:
        condition: ``ProcessCondition`` 实例。

    Returns:
        ``machine_info``（扁平 dict，``None`` 值不纳入）。
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

    return extract_orm_fields(
        source_orm_map={
            "InjectionMoldingMachine": machine,
            "InjectionUnit": injection_units[injection_index],
        },
        spec_dict=OPTIMIZE_MACHINE_INFO_FIELDS,
    )


def extract_polymer_info(condition) -> Dict[str, Any]:
    """按 ``OPTIMIZE_POLYMER_INFO_FIELDS`` 契约提取 polymer_info（白名单）。

    Args:
        condition: ``ProcessCondition`` 实例。

    Returns:
        ``polymer_info``（扁平 dict，``None`` 值不纳入）。
    """
    polymer = condition.polymer
    if polymer is None:
        return {}
    return extract_orm_fields(
        source_orm_map={"Polymer": polymer},
        spec_dict=OPTIMIZE_POLYMER_INFO_FIELDS,
    )


def extract_mold_info(condition) -> Dict[str, Any]:
    """按 ``OPTIMIZE_MOLD_INFO_FIELDS`` 契约提取 mold_info（白名单）。

    跨四张表合并：**Mold**（主表）+ **GatingSystem**（流道）+ **Cavity**（型腔）
    + **Gate**（浇口）—— 后三张是制品级物理基准的来源（壁厚 / 制品重 / 流道 /
    浇口类型），是冷却时间判级论域的必需输入（见 ``fuzzy/specs.py`` 的
    ``resolve_product_limits``）。

    【注意】**逐级取第一个**（多浇注系统 / 多型腔 / 多浇口时取第一个）：
      与专家引擎侧「多腔取第一个 / 多浇口取第一个」的既有口径一致。
    【注意】若将来出现多射工况，需改为按 ``condition.shot_index`` 选取
      （与 ``parameter_initialize`` 的快照侧口径对齐）。

    【注意】**任一级缺失 ⇒ 该来源的字段全部不出现** ⇒ 调用方回落经验论域，
      **不报错、不阻塞**。

    Args:
        condition: ``ProcessCondition`` 实例。

    Returns:
        ``mold_info``（扁平 dict，``None`` 值不纳入）。
    """
    mold = condition.mold
    if mold is None:
        return {}
    gating = mold.gating_systems.first()
    cavity = gating.cavities.first() if gating is not None else None
    gate = cavity.gates.first() if cavity is not None else None
    return extract_orm_fields(
        source_orm_map={
            "Mold": mold,
            "GatingSystem": gating,
            "Cavity": cavity,
            "Gate": gate,
        },
        spec_dict=OPTIMIZE_MOLD_INFO_FIELDS,
    )


# =============================================================================
# 初始化链路（快照取数 · expert 契约）
# =============================================================================


def resolve_mold_data_sources(mold_snapshot: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """解析 mold 快照的数据源（按 ``source_model`` 拆解）。

    路由关系：
        ``source_model='Mold'``         → ``snapshot['mold']``
        ``source_model='GatingSystem'`` → ``snapshot['gating_system']``
        ``source_model='Cavity'``       → ``snapshot['gating_system']['cavities'][0]``
        ``source_model='Gate'``         → ``snapshot['gating_system']['cavities'][0]['gates'][0]``

    多腔/多浇口场景的子项选取（"取第一个"）由本函数统一封装，
    维度函数不 hardcode ``cavities[0]`` / ``gates[0]``。

    Args:
        mold_snapshot: mold 快照。

    Returns:
        ``source_model`` → 该来源的字段字典。
    """
    sources: Dict[str, Dict[str, Any]] = {}
    sources['Mold'] = mold_snapshot.get('mold') or {}
    sources['GatingSystem'] = mold_snapshot.get('gating_system') or {}

    gating = mold_snapshot.get('gating_system') or {}
    cavities = gating.get('cavities') or []
    if cavities:
        sources['Cavity'] = cavities[0]
        gates = cavities[0].get('gates') or []
        if gates:
            sources['Gate'] = gates[0]
    return sources


def build_machine_info_from_snapshot(
    machine_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """从 machine 快照构建算法入参 machine_info。

    Args:
        machine_snapshot: machine 快照，形如
            ``{"machine": {...}, "injection_unit": {...}}``。

    Returns:
        算法入参 machine_info（扁平 dict，含 None 字段）。

    提取原则：
    - 通用提取：按 ``MACHINE_INFO_FIELDS`` 遍历，【全部提取】（含 None）——
      前端能编辑/展示所有 spec 字段；
    - algorithm 只看 "必填/液压机必填" 字段（"可选" 字段被跳过）。
    """
    machine_data = machine_snapshot.get("machine") or {}
    unit = machine_snapshot.get("injection_unit") or {}

    # 【注意】**先守卫再取值**：spec 扩出未知 source_model 时显式报错，
    #    避免静默取到错数据（守卫独立于取值器，见 _assert_known_sources）。
    _assert_known_sources(
        MACHINE_INFO_FIELDS,
        ('InjectionMoldingMachine', 'InjectionUnit'),
        'MACHINE_INFO_FIELDS',
    )

    # 算法层 ProcessInitializer 负责 drive_system → power_method 转换
    #    这里只把 drive_system 放进去（不动转换逻辑——关注点分离）
    return extract_snapshot_fields(
        source_map={
            'InjectionMoldingMachine': machine_data,
            'InjectionUnit': unit,
        },
        spec_dict=MACHINE_INFO_FIELDS,
    )


def build_polymer_info_from_snapshot(
    polymer_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """从 polymer 快照构建算法入参 polymer_info。

    Args:
        polymer_snapshot: polymer 快照，形如 ``{"polymer": {...}}``。

    Returns:
        算法入参 polymer_info（扁平 dict，含 None 字段）。

    提取原则：
    - 通用提取：按 ``POLYMER_INFO_FIELDS`` 遍历，【全部提取】（含 None）——
      前端能编辑/展示所有 spec 字段；
    - algorithm 只看 "必填" 字段（"可选" 字段被跳过）。
    """
    polymer_data = polymer_snapshot.get("polymer") or {}
    return extract_snapshot_fields(
        source_map={'Polymer': polymer_data},
        spec_dict=POLYMER_INFO_FIELDS,
    )


def build_mold_info_from_snapshot(
    mold_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """从 mold 快照构建算法入参 mold_info。

    Args:
        mold_snapshot: mold 快照，形如
            ``{"mold": {...}, "gating_system": {..., "cavities": [...], "gates": [...]}}``。

    Returns:
        算法入参 mold_info（扁平 dict，含 None 字段）。

    提取原则：
    - 通用提取：按 ``MOLD_INFO_SPEC`` 遍历，【全部提取】（含 None）——
      前端能编辑/展示所有 spec 字段；
    - 特殊 fallback：``runner_weight`` / ``max_length`` 补充计算；
    - 特殊计算：``gate_radius`` = diameter / 2 (or outer_diameter / 2)；
    - 算法层 ``audit_field_completeness`` 只校验 "必填/液压机必填/条件必填" 字段，
      "可选/推荐" 字段提取 None 不影响校验结果（"可选/推荐" 会被跳过）。
    """
    data_sources = resolve_mold_data_sources(mold_snapshot)

    # 1. 通用提取：按 MOLD_INFO_SPEC 遍历，每个字段都提取（含 None）
    #    - attr_name=None 的计算字段跳过（单独处理）
    #    - 可选/推荐字段提取 None（前端能编辑/展示）
    #    - source_model 缺失时（Cavity/Gate 无数据）取空 dict 兜底
    mold_info: Dict[str, Any] = extract_snapshot_fields(
        source_map=data_sources,
        spec_dict=MOLD_INFO_SPEC,
    )

    # 2. 特殊 fallback：runner_weight 优先取 runner_weight，否则取 estimated_runner_weight
    if mold_info.get('runner_weight') is None:
        gating = data_sources.get('GatingSystem') or {}
        est = gating.get('estimated_runner_weight')
        if est is not None:
            mold_info['runner_weight'] = est

    # 3. 特殊 fallback：max_length 优先取 max_flow_length，否则取 flow_ratio * ave_wall_thickness
    if mold_info.get('max_length') is None:
        cavity = data_sources.get('Cavity') or {}
        flow_ratio = cavity.get('flow_ratio')
        ave_thickness = cavity.get('ave_wall_thickness')
        if flow_ratio is not None and ave_thickness is not None:
            mold_info['max_length'] = flow_ratio * ave_thickness

    # 4. 特殊计算：gate_radius = diameter / 2 (or outer_diameter / 2)（spec.attr_name=None）
    #    针阀式/点浇口用 diameter，环形浇口用 outer_diameter
    #    只在未填充时计算（保留可能的“外部覆盖”）
    if mold_info.get('gate_radius') is None:
        gate = data_sources.get('Gate') or {}
        if gate.get('diameter') is not None:
            mold_info['gate_radius'] = gate['diameter'] / 2
        elif gate.get('outer_diameter') is not None:
            mold_info['gate_radius'] = gate['outer_diameter'] / 2

    return mold_info
