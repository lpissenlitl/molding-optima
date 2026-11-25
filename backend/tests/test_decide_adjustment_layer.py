"""第2层（结合实际情况，确定明确的调整方案）的护栏。

参照系 = 第2层的机制口径（见 ``services/optimize_chain/decide_adjustment.py``）与分层约定：
「**歧义消解归第2层**（谁让位 / 谁能同调），第3层只做参数整合」。

这些用例锁的是**机制契约**，不是某张具体优先级表 —— 表由调用方注入。

用例里的 ``_apply`` 就是 **service 层的那条链**：
第2层定方向 → 第3层整合（两步行，让用例也能看清「哪层产出什么」）。
"""
import pytest

from process.services.optimize_chain.anchors import FILL_RATIO_MODE, resolve_fill_target
from process.services.optimize_chain.decide_adjustment import (
    ScenarioStrategy,
    collect_candidates,
    collect_facts,
    match_conditions,
    priority_table_from_mapping,
    resolve_priority,
    resolve_scheme,
    select_strategy,
)
from process.services.optimize_chain.integrate_params import apply_scheme


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


def _apply(baseline, recommendations, feedback=None, mold_info=None, **kwargs):
    """第2层定方案 → 第3层整合（与 service 层同一条链）。

    【注意】``feedback`` / ``mold_info`` 是**原料** —— 第3层自己从里面取
    充填量比例口径要的重量（上层不替它挑）。

    Returns:
        ``(scheme, integrated)`` —— 第2层的调整方案 + 第3层整合后的参数集。
    """
    candidates = collect_candidates(recommendations)
    scheme = resolve_scheme(
        candidates.names,
        candidates.targets,
        **kwargs,
    )
    return scheme, apply_scheme(
        baseline, scheme,
        feedback=feedback, mold_info=mold_info,
    )


def test_yielded_candidate_is_not_applied():
    """让位是**显式决定不做** ⇒ 该字段保持旧值，且留痕里能查到为什么。

    参照系：``decide_adjustment.resolve_priority`` 的让位口径（第 2 条）。
    """
    scheme, outcome = _apply(
        BASE,
        [_rec('met_end_pos', 361.0), _rec('pst_met_decomp_dist', 5.0)],
        satisfied=('pst_met_decomp_dist',),   # DDAM 目标已达成 ⇒ 让位
    )

    # 让位的候选没落地
    assert outcome.values['pst_met_decomp_dist'] == pytest.approx(3.5)
    # 让位是显式决策，不静默丢弃
    assert 'pst_met_decomp_dist' in scheme.selection.yielded
    assert 'pst_met_decomp_dist' not in scheme.selection.kept
    # 留痕答得出「为什么没落地」
    assert 'pst_met_decomp_dist' in scheme.selection.to_trace()['yielded']


def test_yielded_mel_is_not_translated():
    """**第2层裁决必须先于 MEL 翻译** —— 被让位的 MEL 不得翻成计量位置。

    参照系：分层约定「歧义消解归第2层」+ 「第2层必须看得见 MEL 的意图」
    （若第2层在翻译之后，它只看得到「调计量位置」，规则无处安放）。
    【注意】翻译在第3层 ⇒ 这里只需验「第2层不把让位的 MEL 带出去」。
    """
    scheme, outcome = _apply(
        BASE,
        [_rec('met_end_pos', 361.0)],
        satisfied=('met_end_pos',),          # MEL 让位
    )

    # MEL 被让位 ⇒ 不进保留集 ⇒ 第3层没东西可翻 ⇒ 计量位置不动
    assert scheme.selection.yielded.keys() == {'met_end_pos'}
    assert scheme.mel_targets == ()
    assert outcome.values['met_pos_1'] == pytest.approx(357.29)
    assert 'met_pos_1' not in outcome.landed


def test_empty_table_keeps_all_candidates_in_order():
    """**空表 ⇒ 不裁决** —— 保留集 = 原候选集，顺序不变（不接第2层时的行为）。

    参照系：``PriorityTable`` 的设计（次序是数据；表为空即无次序）。
    """
    recommendations = [
        _rec('met_end_pos', 361.0),
        _rec('pst_met_decomp_dist', 5.0),
        _rec('inj_spd_1', 45.0),
    ]

    scheme, outcome = _apply(BASE, recommendations)

    assert scheme.selection.kept == ('met_end_pos', 'pst_met_decomp_dist', 'inj_spd_1')
    assert scheme.selection.yielded == {}
    assert scheme.selection.deferred == {}
    # MEL 照常翻译成决策量（先定 ML，再确定 MEL）
    assert outcome.values['met_pos_1'] == pytest.approx(357.5)


def test_trace_records_deferred_candidates():
    """暂缓也要留痕 —— 否则留痕答不出「它为什么没落地」。

    参照系：``StrategyDecision.to_trace`` 的留痕完整性口径。
    """
    scheme, _outcome = _apply(
        BASE,
        [_rec('inj_spd_1', 45.0), _rec('HOLD', 4.0), _rec('cool_t', 18.0)],
        max_items=1,
    )

    assert len(scheme.selection.kept) == 1
    assert scheme.selection.deferred
    trace = scheme.selection.to_trace()
    assert trace['deferred'] == dict(scheme.selection.deferred)
    assert set(trace['deferred']) == set(scheme.selection.deferred)


def test_priority_table_is_the_only_source_of_order():
    """次序**只来自数据** —— 换一张表，保留集随之改变。

    参照系：``decide_adjustment`` 模块红线「本模块不内置任何业务次序」。
    """
    table = priority_table_from_mapping(
        {'met_end_pos': 1, 'pst_met_decomp_dist': 2},
        reasons={'met_end_pos': '充填成形优先', 'pst_met_decomp_dist': '松退次之'},
    )

    scheme, _outcome = _apply(
        BASE,
        [_rec('pst_met_decomp_dist', 5.0), _rec('met_end_pos', 361.0)],
        table=table,
    )

    assert scheme.selection.kept == ('met_end_pos', 'pst_met_decomp_dist')
    assert scheme.selection.order == ('met_end_pos', 'pst_met_decomp_dist')


# --- 候选集（进第2层之前的准备）--------------------------------------------


def test_candidates_drop_only_non_suggestions():
    """候选集只筛「**根本不算建议**」的条目 —— 不掺合参数。

    参照系：``decide_adjustment.collect_candidates`` 的候选口径：
    没有推荐值 / 不是 ORM 工艺字段 ⇒ 不进；**「本机有没有这个字段的值」不在这里判**
    （本层不读参数集 ⇒ 是工艺量、但本机没值也照样进）。
    """
    candidates = collect_candidates([
        _rec('inj_spd_1', 45.0),      # 是工艺量 ⇒ 进
        _rec('HOLD', None),           # 没有推荐值 ⇒ 不进
        _rec('NOT_A_PARAM', 1.0),     # 不是 ORM 工艺字段 ⇒ 不进
    ])

    assert candidates.names == ('inj_spd_1',)
    assert candidates.targets == {'inj_spd_1': 45.0}


def test_layer2_does_not_check_local_value_presence():
    """**第2层不判「这台机有没有这个字段的值」** —— 规则筛选 ≠ 参数校验。

    参照系：分层约定「第2层只按调机策略筛规则，不掺合参数」——
    第2层不读参数集 ⇒ 「本机有没有值」与「是不是工艺量」分开看。

    ⇒ ``inj_spd_2`` 是**工艺量**、但不在本机基线里 ⇒ 照常进候选、照常落地；
    第3层也**不做存在性兜底**（兜底 = 掩饰错误）。
    """
    candidates = collect_candidates([_rec('inj_spd_2', 45.0)])   # inj_spd_2 ∉ BASE

    # 第2层照样把它当候选
    assert candidates.names == ('inj_spd_2',)

    scheme = resolve_scheme(candidates.names, candidates.targets)
    outcome = apply_scheme(BASE, scheme)

    # 第3层：照写（不剔除、不留痕）
    assert outcome.values['inj_spd_2'] == pytest.approx(45.0)
    assert 'inj_spd_2' in outcome.landed
    assert not any('inj_spd_2' in item for item in outcome.unresolved)


def test_non_process_params_never_enter_candidates():
    """**不是工艺量的不进候选** ⇒ 下游不需要存在性兜底。

    参照系：候选准入的判据 = **ORM 字段字典**（静态字段定义），不是本机现状 ⇒
    ``IPOS`` / ``CUSION`` 这类规则库专用参数不是工艺量 ⇒ 不进候选
    （否则它们会一路流到落库，把参数集写坏）。
    """
    candidates = collect_candidates([
        _rec('inj_spd_1', 45.0),  # 是工艺量 ⇒ 进
        _rec('IPOS', 1.0),        # 规则库专用参数 ⇒ 不进
        _rec('CUSION', 2.0),      # 规则库专用参数 ⇒ 不进
    ])

    assert candidates.names == ('inj_spd_1',)


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

    参照系：``ScenarioStrategy.preferred_params`` —— 场景是**轮次级**策略，
    排在字段级优先级之前；次序仍然来自**数据**，不在代码里。
    """
    table = priority_table_from_mapping(
        {'pst_met_decomp_dist': 1, 'met_end_pos': 2},
        reasons={'pst_met_decomp_dist': '松退优先', 'met_end_pos': '终止位置次之'},
    )
    scenario = ScenarioStrategy(
        scenario_code='filling_first',
        preferred_params=('met_end_pos',),
        reason='充填成形优先',
    )

    scheme, _outcome = _apply(
        BASE,
        [_rec('pst_met_decomp_dist', 5.0), _rec('met_end_pos', 361.0)],
        table=table,
        strategy=scenario,
    )

    assert scheme.selection.kept == ('met_end_pos', 'pst_met_decomp_dist')
    assert scheme.selection.scenario_code == 'filling_first'
    assert '场景优先' in scheme.selection.kept_reasons['met_end_pos']


def test_scenario_allowed_params_yield_the_rest():
    """准入白名单外的候选**让位**，且理由与「目标已达成」可分辨。

    参照系：``resolve_priority`` 的准入口径（第 2 条）。
    """
    scenario = ScenarioStrategy(
        scenario_code='filling_first',
        allowed_params=('met_end_pos',),
        reason='充填成形优先',
    )

    scheme, outcome = _apply(
        BASE,
        [_rec('met_end_pos', 361.0), _rec('inj_spd_1', 45.0)],
        strategy=scenario,
    )

    assert scheme.selection.kept == ('met_end_pos',)
    assert 'inj_spd_1' in scheme.selection.yielded
    assert '本场景不允许' in scheme.selection.yielded['inj_spd_1']
    # 让位是真不做：值保持旧值
    assert outcome.values['inj_spd_1'] == pytest.approx(50.0)


def test_scenario_max_items_overrides_call_level_limit():
    """场景名额**覆盖**调用级名额。

    参照系：``resolve_priority`` 的名额口径（第 4 条）。
    """
    scenario = ScenarioStrategy(scenario_code='filling_first', max_items=1)

    scheme, _outcome = _apply(
        BASE,
        [_rec('inj_spd_1', 45.0), _rec('cool_t', 18.0)],
        max_items=2,
        strategy=scenario,
    )

    assert len(scheme.selection.kept) == 1
    assert len(scheme.selection.deferred) == 1
    assert '本轮名额已满 ⇒ 暂缓' in scheme.selection.deferred['cool_t']


def test_kept_reasons_record_the_basis():
    """保留项也带**依据** —— 否则反馈回来只能证伪「调了这些量」。

    参照系：``StrategyDecision.kept_reasons`` 的留痕完整性口径。
    """
    table = priority_table_from_mapping(
        {'met_end_pos': 1},
        reasons={'met_end_pos': '充填成形优先'},
    )

    scheme, _outcome = _apply(BASE, [_rec('met_end_pos', 361.0)], table=table)

    assert scheme.selection.kept_reasons['met_end_pos'] == '充填成形优先'
    assert 'kept_reasons' in scheme.selection.to_trace()


def test_no_scenario_keeps_previous_behavior():
    """**无场景 ⇒ 行为与「不接第2层」完全一致**（空表 ⇒ 全保留、原序）。

    参照系：``resolve_priority`` 的「无场景」口径。
    """
    scheme, _outcome = _apply(BASE, [_rec('met_end_pos', 361.0), _rec('pst_met_decomp_dist', 5.0)])

    assert scheme.selection.scenario_code == ''
    assert scheme.selection.kept == ('met_end_pos', 'pst_met_decomp_dist')
    assert scheme.selection.kept_reasons == {}
    assert scheme.selection.yielded == {}


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

    参照系：第3层的充填量目标口径（两种口径互斥）；第2层只把**口径**带出来。
    """
    scenario = ScenarioStrategy(
        scenario_code='filling_first',
        target_modes={'met_end_pos': FILL_RATIO_MODE},
    )
    # 原料：实测制品重量在反馈的观察项里，制品总重在模具上下文里
    feedback = {
        'observations': [
            {'param_key': 'actual_product_weight', 'value': 100.0},
        ],
    }
    mold_info = {'total_product_weight': 110.0}
    facts = collect_facts(feedback, mold_info)

    scheme, outcome = _apply(
        FILL_BASE,
        [_rec('met_end_pos', 361.0)],
        strategy=scenario,
        facts=facts,
        feedback=feedback,
        mold_info=mold_info,
    )

    # 第2层：只记「MEL 目标 + 口径」，**不翻值**
    assert scheme.mel_targets == (361.0,)
    assert scheme.target_modes == {'met_end_pos': FILL_RATIO_MODE}
    assert scheme.assignments == ()
    # 第3层：按比例口径落行程目标值
    assert outcome.values['met_pos_1'] == pytest.approx(300.0 + CURRENT_STROKE * 1.1)
    assert outcome.fill_target is not None
    assert outcome.fill_target.ratio == pytest.approx(1.1)
    assert 'met_pos_1' in outcome.landed


def test_without_fill_target_mel_uses_delta():
    """无充填量目标 ⇒ 回落 MEL 增量口径（旧 MEL + ΔMEL）。

    参照系：``anchors.resolve_mel_target`` 的两步式推算。
    """
    scheme, outcome = _apply(FILL_BASE, [_rec('met_end_pos', 361.0)])

    assert scheme.mel_targets == (361.0,)
    assert outcome.values['met_pos_1'] == pytest.approx(357.5)
    assert outcome.fill_target is None


def test_layer2_gives_direction_not_landed_values():
    """**第2层只给「方向 + 口径」，不求落地值**。

    参照系：分层约定「**改成多少归第3层**」—— 第2层不碰参数
    ⇒ ``MEL`` 只以「目标值 + 口径」的形式带出去，不翻成计量位置。
    """
    scheme, _outcome = _apply(BASE, [_rec('met_end_pos', 361.0)])

    # MEL 保留 ⇒ 带的是「目标值 + 口径」，不是「已翻好的计量位置」
    assert 'met_end_pos' in scheme.kept
    assert scheme.mel_targets == (361.0,)
    assert scheme.assignments == ()


def test_layer2_carries_absolute_values_of_plain_fields():
    """**非派生量**的目标值是绝对值 ⇒ 第2层原样带出，可直接落地。

    参照系：分层约定「非派生量不必等第3层」—— 只有派生量（MEL）才需换算。
    """
    scheme, outcome = _apply(BASE, [_rec('pst_met_decomp_dist', 5.0)])

    assert scheme.assignments == (('pst_met_decomp_dist', 5.0),)
    assert scheme.mel_targets == ()
    assert outcome.values['pst_met_decomp_dist'] == pytest.approx(5.0)


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


def test_facts_derive_fill_gap():
    """派生量：充填缺口 = 制品总重 − 实测重量。

    参照系：``services/optimize_chain/decide_adjustment.py`` 的派生量口径。
    """
    facts = collect_facts(
        _feedback(actual_weight=95.0),
        {'total_product_weight': 100.0},
    )

    assert facts['defect_codes'] == ('SHORTSHOT',)
    assert facts['actual_weight'] == pytest.approx(95.0)
    assert facts['target_weight'] == pytest.approx(100.0)
    assert facts['fill_gap'] == pytest.approx(5.0)


def test_missing_observation_blocks_the_scenario():
    """**缺数据 ⇒ 条件不成立**（不臆造）⇒ 落回更宽松的场景。

    参照系：``match_conditions`` 的「缺数据不命中」口径。
    """
    facts = collect_facts(_feedback(), {'total_product_weight': 100.0})

    assert facts.get('actual_weight') is None
    assert facts.get('fill_gap') is None
    assert match_conditions(FILLING_CONDITIONS, facts) is False


def test_conditions_are_and_semantics():
    """条件是 **AND**：缺一条不成立 ⇒ 场景不命中。

    参照系：``match_conditions`` 的 AND 口径。
    """
    # 缺陷对、但重量达标（无缺口）⇒ 不命中
    facts = collect_facts(
        _feedback(actual_weight=105.0),
        {'total_product_weight': 100.0},
    )
    assert match_conditions(FILLING_CONDITIONS, facts) is False

    # 重量有缺口、但缺陷不对 ⇒ 不命中
    facts = collect_facts(
        _feedback(defect='FLASH', actual_weight=95.0),
        {'total_product_weight': 100.0},
    )
    assert match_conditions(FILLING_CONDITIONS, facts) is False


def test_select_strategy_picks_the_first_matched():
    """命中多条 ⇒ 取**第一条**（最具体优先，排序由调用方保证）。

    参照系：``select_strategy`` 的「取第一条而非合并」口径。
    """
    default_spec = ScenarioStrategy(scenario_code='default_one_adjust', conditions=(), max_items=1)
    filling_spec = ScenarioStrategy(
        scenario_code='filling_first',
        conditions=tuple(FILLING_CONDITIONS),
        preferred_params=('met_end_pos',),
        max_items=1,
        target_modes={'met_end_pos': FILL_RATIO_MODE},
    )

    facts = collect_facts(
        _feedback(actual_weight=95.0),
        {'total_product_weight': 100.0},
    )
    other = collect_facts(
        _feedback(defect='FLASH', actual_weight=95.0),
        {'total_product_weight': 100.0},
    )

    # 候选已按「归属 → 优先级」排好序：更具体的在前
    assert select_strategy([filling_spec, default_spec], facts) is filling_spec
    # 没有短射 ⇒ 只有默认口径命中
    assert select_strategy([filling_spec, default_spec], other) is default_spec
    # 一条都不命中 ⇒ None ⇒ 不裁决
    assert select_strategy([filling_spec], other) is None


def test_unknown_operator_does_not_match():
    """**未知操作符 ⇒ 不命中**（不猜）—— 条件写错时表现为「策略没生效」。

    参照系：``match_conditions`` 的「未知操作符不命中」口径。
    """
    facts = collect_facts(
        _feedback(actual_weight=95.0),
        {'total_product_weight': 100.0},
    )

    assert match_conditions(
        [{'field': 'defect_codes', 'operator': 'starts_with', 'value': 'SHORT'}],
        facts,
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
