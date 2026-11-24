"""参数提取专区（``process.services.shared.spec_extract``）的护栏 + **等价性基线**。

公共模块按「两条链路各自形态」并列提供提取函数（ORM 直取 / 快照取数），
**刻意不做统一** ⇒ 这些用例锁两件事：

1. **两个取值器各自的契约**（``test_extract_*``）：
   - ``extract_orm_fields``：``None`` **不纳入**、未知 ``source_model`` 跳过；
   - ``extract_snapshot_fields``：``None`` **纳入**、未知 ``source_model`` 取到 ``None``；
   - 无 ``attr_name`` 的**计算字段**两者都跳过；
2. **等价性基线**（``test_*_matches_legacy``）：把**搬迁前**的各提取器实现
   **原样复制**到本文件当 oracle，断言「搬迁后的输出与搬迁前**逐字段完全一致**」。

【为什么必须有第 2 组】：这次把提取逻辑从两个 service 各抄一份搬到公共模块
⇒ 风险不是「报错」，而是**悄悄变了取值口径**
（``None`` 该留还是该丢、未知 ``source_model`` 该跳还是该报错、
特殊补算的触发条件）⇒ 用 oracle 把旧口径钉死。
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from types import SimpleNamespace

import pytest

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
from process.services.shared.spec_extract import (
    _assert_known_sources,
    build_machine_info_from_snapshot,
    build_mold_info_from_snapshot,
    build_polymer_info_from_snapshot,
    extract_machine_info,
    extract_mold_info,
    extract_polymer_info,
    extract_orm_fields,
    extract_snapshot_fields,
)


# --- oracle：搬迁前的实现（原样复制，用于钉死旧口径） ---


def _legacy_extract_orm_fields_by_spec(source_orm_map, spec_dict):
    """搬迁前的 ``parameter_optimize._extract_orm_fields_by_spec``（已删除）。"""
    extracted = {}
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


def _legacy_resolve_mold_data_sources(mold_snapshot):
    """搬迁前的 ``parameter_initialize._resolve_mold_data_sources``（oracle 自包含）。"""
    sources = {}
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


def _legacy_build_mold_info_from_snapshot(mold_snapshot):
    """搬迁前的 ``parameter_initialize._build_mold_info_from_snapshot``（原样复制）。"""
    data_sources = _legacy_resolve_mold_data_sources(mold_snapshot)
    mold_info = {}

    for target_key, spec in MOLD_INFO_SPEC.items():
        attr_name = spec.get('attr_name')
        if not attr_name:
            continue
        source_model = spec.get('source_model')
        data = data_sources.get(source_model) or {}
        mold_info[target_key] = data.get(attr_name)

    if mold_info.get('runner_weight') is None:
        gating = data_sources.get('GatingSystem') or {}
        est = gating.get('estimated_runner_weight')
        if est is not None:
            mold_info['runner_weight'] = est

    if mold_info.get('max_length') is None:
        cavity = data_sources.get('Cavity') or {}
        flow_ratio = cavity.get('flow_ratio')
        ave_thickness = cavity.get('ave_wall_thickness')
        if flow_ratio is not None and ave_thickness is not None:
            mold_info['max_length'] = flow_ratio * ave_thickness

    if mold_info.get('gate_radius') is None:
        gate = data_sources.get('Gate') or {}
        if gate.get('diameter') is not None:
            mold_info['gate_radius'] = gate['diameter'] / 2
        elif gate.get('outer_diameter') is not None:
            mold_info['gate_radius'] = gate['outer_diameter'] / 2

    return mold_info


def _legacy_build_machine_info_from_snapshot(machine_snapshot):
    """搬迁前的 ``parameter_initialize._build_machine_info_from_snapshot``（原样复制）。"""
    machine_data = machine_snapshot.get("machine") or {}
    unit = machine_snapshot.get("injection_unit") or {}
    machine_info = {}

    for target_key, spec in MACHINE_INFO_FIELDS.items():
        attr_name = spec.get('attr_name')
        if not attr_name:
            continue
        source_model = spec.get('source_model')
        if source_model == 'InjectionMoldingMachine':
            data = machine_data
        elif source_model == 'InjectionUnit':
            data = unit
        else:
            raise ValueError(
                f"MACHINE_INFO_FIELDS['{target_key}'] 的 source_model={source_model!r} "
                f"未在 service 层处理（已知：InjectionMoldingMachine / InjectionUnit）"
            )
        machine_info[target_key] = data.get(attr_name)

    return machine_info


def _legacy_build_polymer_info_from_snapshot(polymer_snapshot):
    """搬迁前的 ``parameter_initialize._build_polymer_info_from_snapshot``（原样复制）。"""
    polymer_data = polymer_snapshot.get("polymer") or {}
    polymer_info = {}

    for target_key, spec in POLYMER_INFO_FIELDS.items():
        attr_name = spec.get('attr_name')
        if not attr_name:
            continue
        polymer_info[target_key] = polymer_data.get(attr_name)

    return polymer_info


# --- 假数据构造 ---


class _FakeManager:
    """related manager 替身（只需 all() / first()）。"""

    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


def _fake_orm(spec_dict, source_model, **extra):
    """按 spec 造一个假 ORM 实例：每个 attr_name 都有**可区分**的值。"""
    attrs = {}
    for spec in spec_dict.values():
        if spec.get('source_model') != source_model:
            continue
        attr_name = spec.get('attr_name')
        if attr_name:
            attrs[attr_name] = '%s.%s' % (source_model, attr_name)
    attrs.update(extra)
    return SimpleNamespace(**attrs)


def _fake_mold_tree(spec_dict):
    """假模具树：Mold -> GatingSystem -> Cavity -> Gate（逐级挂 manager）。"""
    mold = _fake_orm(spec_dict, 'Mold')
    gating = _fake_orm(spec_dict, 'GatingSystem')
    cavity = _fake_orm(spec_dict, 'Cavity')
    gate = _fake_orm(spec_dict, 'Gate')
    cavity.gates = _FakeManager([gate])
    gating.cavities = _FakeManager([cavity])
    mold.gating_systems = _FakeManager([gating])
    return mold


def _fake_optimize_condition():
    """假 condition（优化链路入口）：machine + polymer + mold 三件套。"""
    machine = _fake_orm(OPTIMIZE_MACHINE_INFO_FIELDS, 'InjectionMoldingMachine', id=1)
    unit = _fake_orm(OPTIMIZE_MACHINE_INFO_FIELDS, 'InjectionUnit')
    machine.injection_units = _FakeManager([unit])
    return SimpleNamespace(
        injection_machine=machine,
        injection_index=0,
        polymer=_fake_orm(OPTIMIZE_POLYMER_INFO_FIELDS, 'Polymer'),
        mold=_fake_mold_tree(OPTIMIZE_MOLD_INFO_FIELDS),
    )


def _fake_mold_snapshot(variant):
    """假 mold 快照（初始化链路入口）。

    三种变体，覆盖 ``build_mold_info_from_snapshot`` 的全部分支：

    - ``complete``：spec 字段全有值 => 三处补算**都不触发**（``gate_radius``
      例外：它的 ``attr_name`` 为空 => 通用提取必跳过 => 走计算）；
    - ``sparse``：spec 字段全缺，但保留补算所需的**快照原始值**
      （``estimated_runner_weight`` / ``flow_ratio`` + ``ave_wall_thickness`` /
      ``diameter``）=> 三处补算**全部触发**；
    - ``empty``：全空 => 补算也算不出来。
    """
    if variant == 'empty':
        return {'mold': {}, 'gating_system': None}

    if variant == 'complete':
        mold = dict(_fake_orm(MOLD_INFO_SPEC, 'Mold').__dict__)
        gating = dict(_fake_orm(MOLD_INFO_SPEC, 'GatingSystem').__dict__)
        cavity = dict(_fake_orm(MOLD_INFO_SPEC, 'Cavity').__dict__)
        gate = dict(_fake_orm(MOLD_INFO_SPEC, 'Gate').__dict__)
        gate['diameter'] = 4.0
        gate['outer_diameter'] = 6.0
    else:  # sparse
        mold = {}
        gating = {'estimated_runner_weight': 12.5}
        cavity = {'flow_ratio': 2.5, 'ave_wall_thickness': 2.0}
        gate = {'diameter': 4.0}

    return {
        'mold': mold,
        'gating_system': {
            **gating,
            'cavities': [{**cavity, 'gates': [gate]}],
        },
    }


def _fake_machine_snapshot():
    """假 machine 快照（初始化链路入口）。"""
    return {
        'machine': dict(_fake_orm(MACHINE_INFO_FIELDS, 'InjectionMoldingMachine').__dict__),
        'injection_unit': dict(_fake_orm(MACHINE_INFO_FIELDS, 'InjectionUnit').__dict__),
    }


def _fake_polymer_snapshot():
    """假 polymer 快照（初始化链路入口）。"""
    return {'polymer': dict(_fake_orm(POLYMER_INFO_FIELDS, 'Polymer').__dict__)}


# --- 1. 两个取值器各自的契约 ---


def test_extract_orm_fields_drops_none():
    """ORM 口径：``None`` **不纳入**结果（只保留有值的字段）。"""
    spec = {
        'a': {'source_model': 'Mold', 'attr_name': 'shot_count'},
        'b': {'source_model': 'Mold', 'attr_name': 'absent'},
    }
    result = extract_orm_fields({'Mold': SimpleNamespace(shot_count=7)}, spec)
    assert result == {'a': 7}


def test_extract_orm_fields_skips_unknown_source_model():
    """ORM 口径：未知 ``source_model``（没有该实例）=> 该字段不出现。"""
    spec = {'a': {'source_model': 'NotExists', 'attr_name': 'shot_count'}}
    assert extract_orm_fields({}, spec) == {}


def test_extract_orm_fields_skips_field_without_attr_name():
    """无 attr_name = 计算字段（如 gate_radius）=> 跳过，交给维度函数单独处理。"""
    spec = {
        'plain': {'source_model': 'Mold', 'attr_name': 'shot_count'},
        'computed': {'source_model': 'Mold', 'attr_name': None},
    }
    result = extract_orm_fields({'Mold': SimpleNamespace(shot_count=7)}, spec)
    assert result == {'plain': 7}


def test_extract_snapshot_fields_keeps_none():
    """快照口径：``None`` **纳入**结果（前端要能编辑/展示所有 spec 字段）。"""
    spec = {
        'a': {'source_model': 'Mold', 'attr_name': 'shot_count'},
        'b': {'source_model': 'Mold', 'attr_name': 'absent'},
    }
    result = extract_snapshot_fields({'Mold': {'shot_count': 7}}, spec)
    assert result == {'a': 7, 'b': None}


def test_extract_snapshot_fields_unknown_source_model_yields_none():
    """快照口径：未知 ``source_model`` => 按空 dict 兜底 => ``None``。"""
    spec = {'a': {'source_model': 'NotExists', 'attr_name': 'shot_count'}}
    assert extract_snapshot_fields({}, spec) == {'a': None}


def test_extract_snapshot_fields_skips_field_without_attr_name():
    """快照口径同样跳过无 attr_name 的计算字段。"""
    spec = {
        'plain': {'source_model': 'Mold', 'attr_name': 'shot_count'},
        'computed': {'source_model': 'Mold', 'attr_name': None},
    }
    result = extract_snapshot_fields({'Mold': {'shot_count': 7}}, spec)
    assert result == {'plain': 7}


def test_assert_known_sources_rejects_unknown():
    """守卫：spec 扩出未知 ``source_model`` => 显式报错（防静默取错数据）。"""
    spec = {'x': {'source_model': 'Unknown', 'attr_name': 'a'}}
    with pytest.raises(ValueError) as exc:
        _assert_known_sources(spec, ('InjectionMoldingMachine', 'InjectionUnit'),
                              'MACHINE_INFO_FIELDS')
    assert "MACHINE_INFO_FIELDS['x']" in str(exc.value)
    assert 'InjectionMoldingMachine / InjectionUnit' in str(exc.value)


def test_assert_known_sources_ignores_computed_field():
    """守卫不拦无 attr_name 的计算字段（它不取值，不涉及 source_model）。"""
    spec = {'computed': {'source_model': 'Unknown', 'attr_name': None}}
    _assert_known_sources(spec, ('Mold',), 'MOLD_INFO_SPEC')


# --- 2. 等价性基线：搬迁前后逐字段一致 ---


def test_orm_extraction_matches_legacy():
    """公共 ORM 取值器 == 搬迁前的 ``_extract_orm_fields_by_spec``。"""
    condition = _fake_optimize_condition()
    source_orm_map = {
        'InjectionMoldingMachine': condition.injection_machine,
        'InjectionUnit': condition.injection_machine.injection_units.all()[0],
    }
    spec = dict(OPTIMIZE_MACHINE_INFO_FIELDS)
    spec['missing_source'] = {'source_model': 'NotExists', 'attr_name': 'x'}
    spec['no_attr'] = {'source_model': 'Mold', 'attr_name': None}
    assert extract_orm_fields(source_orm_map, spec) == \
        _legacy_extract_orm_fields_by_spec(source_orm_map, spec)


@pytest.mark.parametrize('variant', ['complete', 'sparse', 'empty'])
def test_initialize_mold_info_matches_legacy(variant):
    """初始化链路的 mold 提取 == 搬迁前（含 runner_weight / max_length / gate_radius 三处补算）。"""
    snapshot = _fake_mold_snapshot(variant)
    assert build_mold_info_from_snapshot(snapshot) == \
        _legacy_build_mold_info_from_snapshot(snapshot)


def test_initialize_machine_info_matches_legacy():
    """初始化链路的 machine 提取 == 搬迁前。"""
    snapshot = _fake_machine_snapshot()
    assert build_machine_info_from_snapshot(snapshot) == \
        _legacy_build_machine_info_from_snapshot(snapshot)


def test_initialize_polymer_info_matches_legacy():
    """初始化链路的 polymer 提取 == 搬迁前。"""
    snapshot = _fake_polymer_snapshot()
    assert build_polymer_info_from_snapshot(snapshot) == \
        _legacy_build_polymer_info_from_snapshot(snapshot)


def test_optimize_extractors_match_legacy():
    """优化链路的三个提取器 == 搬迁前（同一份 source_orm_map + 同一套 spec）。"""
    condition = _fake_optimize_condition()
    unit = condition.injection_machine.injection_units.all()[0]

    machine_map = {
        'InjectionMoldingMachine': condition.injection_machine,
        'InjectionUnit': unit,
    }
    assert extract_machine_info(condition) == \
        _legacy_extract_orm_fields_by_spec(machine_map, OPTIMIZE_MACHINE_INFO_FIELDS)

    polymer_map = {'Polymer': condition.polymer}
    assert extract_polymer_info(condition) == \
        _legacy_extract_orm_fields_by_spec(polymer_map, OPTIMIZE_POLYMER_INFO_FIELDS)

    mold_map = {
        'Mold': condition.mold,
        'GatingSystem': condition.mold.gating_systems.first(),
        'Cavity': condition.mold.gating_systems.first().cavities.first(),
        'Gate': condition.mold.gating_systems.first().cavities.first().gates.first(),
    }
    assert extract_mold_info(condition) == \
        _legacy_extract_orm_fields_by_spec(mold_map, OPTIMIZE_MOLD_INFO_FIELDS)


def test_optimize_extractors_return_empty_on_missing_sources():
    """缺来源时返回空 dict（不报错、不阻塞）——搬迁前后一致。"""
    empty = SimpleNamespace(injection_machine=None, polymer=None, mold=None,
                            injection_index=0)
    assert extract_machine_info(empty) == {}
    assert extract_polymer_info(empty) == {}
    assert extract_mold_info(empty) == {}
