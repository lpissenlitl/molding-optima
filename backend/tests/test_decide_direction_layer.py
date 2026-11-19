"""第2层（结合实际情况，确定明确的调整方向）的护栏。

参照系 = 第2层的机制口径（见 ``algorithms/decide_direction.py``）与分层约定：
「**歧义消解归第2层**（谁让位 / 谁能同调），第3层只做参数整合」。

这些用例锁的是**机制契约**，不是某张具体优先级表 —— 表由调用方注入。

用例里的 ``_apply`` 就是 **service 层的那条链**：
第2层定方向 → 第3层整合（两步行，让用例也能看清「哪层产出什么」）。
"""
import pytest

from process.algorithms.anchors import resolve_fill_target
from process.algorithms.decide_direction import (
    ScenarioContext,
    ScenarioPolicy,
    build_scenario_context,
    collect_candidates,
    match_conditions,
    priority_table_from_mapping,
    resolve_direction,
    resolve_priority,
    select_policy,
)
from process.algorithms.integrate_params import apply_direction


# 基线：ML_N 357.29 + DDAM 3.5 = MEL 360.79（自洽）
BASE = {
    'met_stg': 1,
    'met_pos_1': 357.29,
    'pst_met_decomp_dist': 3.5,
    'met_end_pos': 360.79,
    'inj_spd_1': 50.0,
    'hold_t_1': 3.0,
    'cool_t': 15.0,
}


def _rec(param, value):
    return {'param': param, 'recommended_value': value}


def _apply(baseline, recommendations, **kwargs):
    """第2层定方向 → 第3层整合（与 service 层同一条链）。

    Returns:
        ``(direction, integrated)`` —— 第2层的方向 + 第3层整合后的参数集。
    """
    candidates = collect_candidates(recommendations, baseline)
    direction = resolve_direction(
        candidates.names,
        candidates.targets,
        baseline,
        **kwargs,
    )
    return direction, apply_direction(baseline, direction)


def test_yielded_candidate_is_not_applied():
    """让位是**显式决定不做** ⇒ 该字段保持旧值，且留痕里能查到为什么。

    参照系：``direction.resolve_priority`` 的让位口径（第 2 条）。
    """
    direction, outcome = _apply(
        BASE,
        [_rec('MEL', 361.0), _rec('DDAM', 5.0)],
        satisfied=('pst_met_decomp_dist',),   # DDAM 目标已达成 ⇒ 让位
    )

    # 让位的候选没落地
    assert outcome.values['pst_met_decomp_dist'] == pytest.approx(3.5)
    # 让位是显式决策，不静默丢弃
    assert 'pst_met_decomp_dist' in direction.decision.yielded
    assert 'pst_met_decomp_dist' not in direction.decision.kept
    # 留痕答得出「为什么没落地」
    assert 'pst_met_decomp_dist' in direction.decision.to_trace()['yielded']


def test_yielded_mel_is_not_translated():
    """**第2层裁决必须先于 MEL 翻译** —— 被让位的 MEL 不得翻成计量位置。

    参照系：分层约定「歧义消解归第2层」+ 「第2层必须看得见 MEL 的意图」
    （若第2层在翻译之后，它只看得到「调计量位置」，规则无处安放）。
    """
    direction, outcome = _apply(
        BASE,
        [_rec('MEL', 361.0)],
        satisfied=('met_end_pos',),          # MEL 让位
    )

    # MEL 被让位 ⇒ 不进翻译 ⇒ 计量位置不动
    assert direction.decision.yielded.keys() == {'met_end_pos'}
    assert direction.mel_targets == ()
    assert outcome.values['met_pos_1'] == pytest.approx(357.29)
    assert 'met_pos_1' not in outcome.landed


def test_empty_table_keeps_all_candidates_in_order():
    """**空表 ⇒ 不裁决** —— 保留集 = 原候选集，顺序不变（不接第2层时的行为）。

    参照系：``PriorityTable`` 的设计（次序是数据；表为空即无次序）。
    """
    recommendations = [
        _rec('MEL', 361.0),
        _rec('DDAM', 5.0),
        _rec('IV0', 45.0),
    ]

    direction, outcome = _apply(BASE, recommendations)

    assert direction.decision.kept == ('met_end_pos', 'pst_met_decomp_dist', 'inj_spd_1')
    assert direction.decision.yielded == {}
    assert direction.decision.deferred == {}
    # MEL 照常翻译成决策量（先定 ML，再确定 MEL）
    assert outcome.values['met_pos_1'] == pytest.approx(357.5)


def test_trace_records_deferred_candidates():
    """暂缓也要留痕 —— 否则留痕答不出「它为什么没落地」。

    参照系：``StrategyDecision.to_trace`` 的留痕完整性口径。
    """
    direction, _outcome = _apply(
        BASE,
        [_rec('IV0', 45.0), _rec('HOLD', 4.0), _rec('CT', 18.0)],
        max_items=1,
    )

    assert len(direction.decision.kept) == 1
    assert direction.decision.deferred
    trace = direction.decision.to_trace()
    assert trace['deferred'] == dict(direction.decision.deferred)
    assert set(trace['deferred']) == set(direction.decision.deferred)


def test_priority_table_is_the_only_source_of_order():
    """次序**只来自数据** —— 换一张表，保留集随之改变。

    参照系：``direction`` 模块红线「本模块不内置任何业务次序」。
    """
    table = priority_table_from_mapping(
        {'met_end_pos': 1, 'pst_met_decomp_dist': 2},
        reasons={'met_end_pos': '充填成形优先', 'pst_met_decomp_dist': '松退次之'},
    )

    direction, _outcome = _apply(
        BASE,
        [_rec('DDAM', 5.0), _rec('MEL', 361.0)],
        table=table,
    )

    assert direction.decision.kept == ('met_end_pos', 'pst_met_decomp_dist')
    assert direction.decision.order == ('met_end_pos', 'pst_met_decomp_dist')


# --- 候选集（进第2层之前的准备）--------------------------------------------


def test_candidates_drop_the_unlandable_suggestions():
    """落不了地的建议**不进候选** —— 不占名额，也不进裁决留痕。

    参照系：``direction.collect_candidates`` 的候选口径。
    """
    candidates = collect_candidates(
        [
            _rec('IV0', 45.0),          # 能落（基线里有 inj_spd_1）
            _rec('HOLD', None),         # 没有推荐值 ⇒ 不进
            _rec('NOT_A_PARAM', 1.0),   # 译不出业务字段名 ⇒ 不进
            _rec('ZZZ', 1.0),           # 译得出但基线里没有 ⇒ 不进
        ],
        BASE,
    )

    assert candidates.names == ('inj_spd_1',)
    assert candidates.targets == {'inj_spd_1': 45.0}


# --- 场景层（场景策略的落点）-------------------------------------------------

#: 带 VPTL 的基线 —— 充填量比例解算需要注射行程（``ML_N − VPTL``）
FILL_BASE = {
    'met_stg': 1,
    'met_pos_1': 357.29,
    'vps_pos': 300.0,
    'pst_met_decomp_dist': 3.5,
    'met_end_pos': 360.79,
    'inj_spd_1': 50.0,
    'cool_t': 15.0,
}

#: FILL_BASE 的当前注射行程（357.29 − 300.0）
CURRENT_STROKE = 57.29


def test_scenario_preferred_params_lead_the_order():
    """场景优先集把充填成形提到最前。

    参照系：``ScenarioPolicy.preferred_params`` —— 场景是**轮次级**策略，
    排在字段级优先级之前；次序仍然来自**数据**，不在代码里。
    """
    table = priority_table_from_mapping(
        {'pst_met_decomp_dist': 1, 'met_end_pos': 2},
        reasons={'pst_met_decomp_dist': '松退优先', 'met_end_pos': '终止位置次之'},
    )
    scenario = ScenarioPolicy(
        scenario_code='filling_first',
        preferred_params=('met_end_pos',),
        reason='充填成形优先',
    )

    direction, _outcome = _apply(
        BASE,
        [_rec('DDAM', 5.0), _rec('MEL', 361.0)],
        table=table,
        policy=scenario,
    )

    assert direction.decision.kept == ('met_end_pos', 'pst_met_decomp_dist')
    assert direction.decision.scenario_code == 'filling_first'
    assert '场景优先' in direction.decision.kept_reasons['met_end_pos']


def test_scenario_allowed_params_yield_the_rest():
    """准入白名单外的候选**让位**，且理由与「目标已达成」可分辨。

    参照系：``resolve_priority`` 的准入口径（第 2 条）。
    """
    scenario = ScenarioPolicy(
        scenario_code='filling_first',
        allowed_params=('met_end_pos',),
        reason='充填成形优先',
    )

    direction, outcome = _apply(
        BASE,
        [_rec('MEL', 361.0), _rec('IV0', 45.0)],
        policy=scenario,
    )

    assert direction.decision.kept == ('met_end_pos',)
    assert 'inj_spd_1' in direction.decision.yielded
    assert '本场景不允许' in direction.decision.yielded['inj_spd_1']
    # 让位是真不做：值保持旧值
    assert outcome.values['inj_spd_1'] == pytest.approx(50.0)


def test_scenario_max_items_overrides_call_level_limit():
    """场景名额**覆盖**调用级名额。

    参照系：``resolve_priority`` 的名额口径（第 4 条）。
    """
    scenario = ScenarioPolicy(scenario_code='filling_first', max_items=1)

    direction, _outcome = _apply(
        BASE,
        [_rec('IV0', 45.0), _rec('CT', 18.0)],
        max_items=2,
        policy=scenario,
    )

    assert len(direction.decision.kept) == 1
    assert len(direction.decision.deferred) == 1
    assert '本轮名额已满 ⇒ 暂缓' in direction.decision.deferred['cool_t']


def test_kept_reasons_record_the_basis():
    """保留项也带**依据** —— 否则反馈回来只能证伪「调了这些量」。

    参照系：``StrategyDecision.kept_reasons`` 的留痕完整性口径。
    """
    table = priority_table_from_mapping(
        {'met_end_pos': 1},
        reasons={'met_end_pos': '充填成形优先'},
    )

    direction, _outcome = _apply(BASE, [_rec('MEL', 361.0)], table=table)

    assert direction.decision.kept_reasons['met_end_pos'] == '充填成形优先'
    assert 'kept_reasons' in direction.decision.to_trace()


def test_no_scenario_keeps_previous_behavior():
    """**无场景 ⇒ 行为与「不接第2层」完全一致**（空表 ⇒ 全保留、原序）。

    参照系：``resolve_priority`` 的「无场景」口径。
    """
    direction, _outcome = _apply(BASE, [_rec('MEL', 361.0), _rec('DDAM', 5.0)])

    assert direction.decision.scenario_code == ''
    assert direction.decision.kept == ('met_end_pos', 'pst_met_decomp_dist')
    assert direction.decision.kept_reasons == {}
    assert direction.decision.yielded == {}


# --- 充填量目标（按重量比例重算行程）---------------------------------


def test_fill_target_scales_stroke_by_weight_ratio():
    """充填量目标 = 当前行程 × 重量比；落点是末段计量位置。

    参照系：``anchors.resolve_fill_target`` 的物理口径（行程 ∝ 充填量 ∝ 重量）。
    """
    target = resolve_fill_target(FILL_BASE, target_weight=110.0, actual_weight=100.0)

    assert target is not None
    assert target.field_name == 'met_pos_1'
    assert target.ratio == pytest.approx(1.1)
    assert target.current_stroke == pytest.approx(CURRENT_STROKE)
    assert target.target_value == pytest.approx(300.0 + CURRENT_STROKE * 1.1)


def test_fill_target_without_data_returns_none():
    """缺数据 ⇒ 返回 ``None``（回落口径：不臆造），不静默算个假的。

    参照系：``anchors`` 模块的回落约定。
    """
    # 实测重量非正
    assert resolve_fill_target(FILL_BASE, target_weight=110.0, actual_weight=0) is None
    # 缺 VPTL / 缺当前 ML_N
    assert resolve_fill_target(
        {'met_stg': 1, 'met_pos_1': 357.29}, target_weight=110.0, actual_weight=100.0
    ) is None


def test_fill_target_replaces_mel_delta():
    """有充填量目标 ⇒ **不走 MEL 增量**，直接落行程目标值。

    参照系：第2层的充填量目标口径（两种口径互斥）。
    """
    scenario = ScenarioPolicy(scenario_code='filling_first', target_mode='fill_ratio')
    context = ScenarioContext(actual_weight=100.0, target_weight=110.0, fill_gap=10.0)

    direction, outcome = _apply(
        FILL_BASE,
        [_rec('MEL', 361.0)],
        policy=scenario,
        context=context,
    )

    assert direction.mel_targets == ()
    assert outcome.values['met_pos_1'] == pytest.approx(300.0 + CURRENT_STROKE * 1.1)
    assert direction.fill_target is not None
    assert direction.fill_target.ratio == pytest.approx(1.1)
    assert 'met_pos_1' in outcome.landed


def test_without_fill_target_mel_uses_delta():
    """无充填量目标 ⇒ 回落 MEL 增量口径（旧 MEL + ΔMEL）。

    参照系：``anchors.resolve_mel_target`` 的两步式推算。
    """
    direction, outcome = _apply(FILL_BASE, [_rec('MEL', 361.0)])

    assert direction.mel_targets == (361.0,)
    assert outcome.values['met_pos_1'] == pytest.approx(357.5)
    assert direction.fill_target is None


# --- 场景判定（第2层的入口：这一轮属于哪类情形）-------------------------------


#: 「充填成形优先」触发条件（短射 + 充填不足）
FILLING_CONDITIONS = [
    {'field': 'defect_codes', 'operator': 'contains', 'value': 'SHORTSHOT'},
    {'field': 'fill_gap', 'operator': 'gt', 'value': 0},
]


def _feedback(defect='SHORTSHOT', actual_weight=None):
    """构造一份反馈（缺陷码 + 实测观察）。"""
    observations = []
    if actual_weight is not None:
        observations.append({'param_key': 'actual_product_weight', 'value': actual_weight})
    return {
        'defects': [{'keyword_name': defect, 'level': 'low'}] if defect else [],
        'observations': observations,
    }


def test_scenario_context_derives_fill_gap():
    """派生量：充填缺口 = 制品总重 − 实测重量。

    参照系：``algorithms/decide_direction.py`` 的派生量口径。
    """
    context = build_scenario_context(
        _feedback(actual_weight=95.0),
        {'total_product_weight': 100.0},
    )

    assert context.defect_codes == ('SHORTSHOT',)
    assert context.actual_weight == pytest.approx(95.0)
    assert context.target_weight == pytest.approx(100.0)
    assert context.fill_gap == pytest.approx(5.0)


def test_missing_observation_blocks_the_scenario():
    """**缺数据 ⇒ 条件不成立**（不臆造）⇒ 落回更宽松的场景。

    参照系：``match_conditions`` 的「缺数据不命中」口径。
    """
    context = build_scenario_context(_feedback(), {'total_product_weight': 100.0})

    assert context.actual_weight is None
    assert context.fill_gap is None
    assert match_conditions(FILLING_CONDITIONS, context) is False


def test_conditions_are_and_semantics():
    """条件是 **AND**：缺一条不成立 ⇒ 场景不命中。

    参照系：``match_conditions`` 的 AND 口径。
    """
    # 缺陷对、但重量达标（无缺口）⇒ 不命中
    context = build_scenario_context(
        _feedback(actual_weight=105.0),
        {'total_product_weight': 100.0},
    )
    assert match_conditions(FILLING_CONDITIONS, context) is False

    # 重量有缺口、但缺陷不对 ⇒ 不命中
    context = build_scenario_context(
        _feedback(defect='FLASH', actual_weight=95.0),
        {'total_product_weight': 100.0},
    )
    assert match_conditions(FILLING_CONDITIONS, context) is False


def test_select_policy_picks_the_first_matched():
    """命中多条 ⇒ 取**第一条**（最具体优先，排序由调用方保证）。

    参照系：``select_policy`` 的「取第一条而非合并」口径。
    """
    default_spec = ScenarioPolicy(scenario_code='default_one_adjust', conditions=(), max_items=1)
    filling_spec = ScenarioPolicy(
        scenario_code='filling_first',
        conditions=tuple(FILLING_CONDITIONS),
        preferred_params=('met_end_pos',),
        max_items=1,
        target_mode='fill_ratio',
    )

    context = build_scenario_context(
        _feedback(actual_weight=95.0),
        {'total_product_weight': 100.0},
    )
    other = build_scenario_context(
        _feedback(defect='FLASH', actual_weight=95.0),
        {'total_product_weight': 100.0},
    )

    # 候选已按「归属 → 优先级」排好序：更具体的在前
    assert select_policy([filling_spec, default_spec], context) is filling_spec
    # 没有短射 ⇒ 只有默认口径命中
    assert select_policy([filling_spec, default_spec], other) is default_spec
    # 一条都不命中 ⇒ None ⇒ 不裁决
    assert select_policy([filling_spec], other) is None


def test_unknown_operator_does_not_match():
    """**未知操作符 ⇒ 不命中**（不猜）—— 条件写错时表现为「策略没生效」。

    参照系：``match_conditions`` 的「未知操作符不命中」口径。
    """
    context = build_scenario_context(
        _feedback(actual_weight=95.0),
        {'total_product_weight': 100.0},
    )

    assert match_conditions(
        [{'field': 'defect_codes', 'operator': 'starts_with', 'value': 'SHORT'}],
        context,
    ) is False


# --- 优先级裁决（不经过方向求解的纯机制口径）---------------------------------


def test_satisfied_candidate_yields_with_trace():
    """参照系（业务口径）：目标已达成的项让位，且让位可追溯。"""
    table = priority_table_from_mapping(
        {'met_end_pos': 1, 'hold_pres_1': 2},
        reasons={'hold_pres_1': '充填量已达标'},
        groups={'met_end_pos': 'filling', 'hold_pres_1': 'holding'},
    )

    decision = resolve_priority(
        ['hold_pres_1', 'met_end_pos'],
        table,
        satisfied=['hold_pres_1'],
    )

    assert decision.kept == ('met_end_pos',)
    assert 'hold_pres_1' in decision.yielded
    assert '充填量已达标' in decision.yielded['hold_pres_1']
    assert decision.to_trace()['yielded']


def test_candidate_beyond_quota_is_deferred_not_dropped():
    """参照系（业务口径）：名额用满时，多余项暂缓并留痕，不静默丢弃。"""
    table = priority_table_from_mapping(
        {'met_end_pos': 1, 'inj_spd_1': 2, 'hold_pres_1': 3},
    )

    decision = resolve_priority(
        ['hold_pres_1', 'inj_spd_1', 'met_end_pos'],
        table,
        max_items=2,
    )

    assert decision.kept == ('met_end_pos', 'inj_spd_1')
    assert decision.deferred == {'hold_pres_1': '本轮名额已满 ⇒ 暂缓'}
    # 三项一个都不能少：暂缓项仍在完整次序里
    assert decision.order == ('met_end_pos', 'inj_spd_1', 'hold_pres_1')
