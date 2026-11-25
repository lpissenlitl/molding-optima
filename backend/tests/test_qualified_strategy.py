# -*- coding: utf-8 -*-
r"""合格态调机 · **策略层契约**。

背景：产品已合格 ⇒ **没有缺陷** ⇒ 缺陷驱动引擎（fuzzy / empirical）零产出
⇒ 候选**由调机策略自带**（``ScenarioStrategy.candidate_params``），
目标值由口径（``step_down`` = 递减步进）在第3层解算。

【注意】**合格与否只由 feedback.tuning_result 说了算** ——
「没有缺陷」「引擎零产出」都**不是**合格的判据（前者可能只是没填，
后者成因很多）⇒ 不得拿它们反推合格态。

【注意】**策略层不产建议值** —— 第2层只产「调哪个 + 什么口径」，
算式在第3层（见 ``services/optimize_chain/integrate_params.apply_scheme``）。

覆盖：
1. 合格态命中「省能耗」场景；非合格态不命中（合格与缺陷互斥）；
2. 算法零产出时场景自带候选；
3. ``step_down`` 口径：目标 = 当前设定 × (1 − 步长)；
4. 缺当前值 ⇒ 不动该字段（不臆造），且被零落地守卫拦住；
5. 缺陷态回归：既有场景不被合格态场景抢；
6. **合格态判定只认 feedback**（「没有缺陷」≠「合格」；引擎零产出不改变判定）。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_qualified_strategy.py -q
"""
import pytest

from process.services.optimize_chain.anchors import STEP_DOWN_MODE, STEP_DOWN_RATIO
from process.services.optimize_chain.decide_adjustment import (
    collect_candidates,
    collect_facts,
    resolve_scheme,
    select_strategy,
    sorted_scenario_strategies,
)
from process.services.optimize_chain.integrate_params import apply_scheme


# 基线：一段注射压力 80（合格态省能耗的调机对象）
BASE = {
    'met_stg': 1,
    'met_pos_1': 357.29,
    'pst_met_decomp_dist': 3.5,
    'met_end_pos': 360.79,
    'inj_spd_1': 50.0,
    'inj_pres_1': 80.0,
    'hold_t_1': 3.0,
    'cool_t': 15.0,
}


def _qualified_context():
    """合格态事实表（本轮评价 = 合格 ⇒ 无缺陷）。"""
    return {'last_tuning_result': 'qualified'}


def _apply(baseline, recommendations, **kwargs):
    """第2层定方案 → 第3层整合（与 service 层同一条链）。"""
    candidates = collect_candidates(recommendations)
    scheme = resolve_scheme(candidates.names, candidates.targets, **kwargs)
    return scheme, apply_scheme(baseline, scheme)


def _qualified_scheme(baseline=BASE):
    """走完整一条链：命中合格态场景 → 裁决 → 整合。"""
    facts = _qualified_context()
    scenario = select_strategy(sorted_scenario_strategies(), facts)
    return _apply(baseline, [], strategy=scenario, facts=facts)


def test_qualified_scenario_matches():
    """合格态 ⇒ 命中「省能耗」场景。"""
    scenario = select_strategy(sorted_scenario_strategies(), _qualified_context())

    assert scenario is not None
    assert scenario.scenario_code == 'qualified_efficiency'


def test_non_qualified_does_not_match_qualified_scenario():
    """非合格态 ⇒ 不命中合格态场景（合格与缺陷互斥，两条策略不抢）。"""
    strategies = sorted_scenario_strategies()

    for result in ('unqualified', 'effective', 'unchanged', 'ineffective', None):
        facts = {
            'defect_codes': ('SHORTSHOT',),
            'actual_weight': 100.0,
            'target_weight': 110.0,
            'fill_gap': 10.0,
            'last_tuning_result': result,
        }
        scenario = select_strategy(strategies, facts)
        assert scenario.scenario_code != 'qualified_efficiency', result


def test_qualified_scenario_carries_its_own_candidate():
    """算法零产出 ⇒ 场景自带候选（第2层只产「调哪个」，不产建议值）。"""
    scheme, _outcome = _qualified_scheme()

    assert scheme.kept == ('inj_pres_1',)
    # 场景候选**不带建议值** ⇒ 不进 assignments ⇒ 目标值由第3层按口径解算
    assert scheme.assignments == ()
    assert scheme.target_modes == {'inj_pres_1': STEP_DOWN_MODE}


def test_step_down_mode_lowers_pressure():
    """递减步进口径：目标 = 当前设定 × (1 − 步长)。"""
    _scheme, outcome = _qualified_scheme()

    assert outcome.values['inj_pres_1'] == pytest.approx(80.0 * (1 - STEP_DOWN_RATIO))
    assert 'inj_pres_1' in outcome.landed
    # 别的一律不动（合格态只降压力，不碰充填与冷却）
    assert outcome.values['cool_t'] == pytest.approx(15.0)
    assert outcome.values['inj_spd_1'] == pytest.approx(50.0)
    assert outcome.values['met_pos_1'] == pytest.approx(357.29)


def test_step_down_without_current_value_keeps_old():
    """缺当前值 ⇒ 不动该字段（不臆造），并被零落地守卫拦住。"""
    base = dict(BASE)
    base.pop('inj_pres_1')

    _scheme, outcome = _qualified_scheme(base)

    assert 'inj_pres_1' not in outcome.values
    assert 'inj_pres_1' not in outcome.landed
    # 零落地 ⇒ 被守卫拦住（不会静默「什么都没调」）
    assert 'inj_pres_1' in (outcome.landing_blocked or ())


def test_defect_state_unaffected():
    """缺陷态回归：短射 + 重量不足 ⇒ 仍走 ``filling_first``（不被合格态场景抢）。"""
    facts = {
        'defect_codes': ('SHORTSHOT',),
        'actual_weight': 100.0,
        'target_weight': 110.0,
        'fill_gap': 10.0,
        'last_tuning_result': 'ineffective',
    }

    scenario = select_strategy(sorted_scenario_strategies(), facts)

    assert scenario.scenario_code == 'filling_first'


def test_qualified_is_judged_by_feedback_only():
    """**合格与否只由 feedback.tuning_result 说了算**。

    【注意】守卫「不得拿『引擎零产出』或『没有缺陷』反推合格态」：
    ① feedback 明确说合格 ⇒ 命中合格态场景；
    ② feedback **没说**合格（同样没有缺陷）⇒ 不命中；
    ③ 引擎零产出**不改变**判定 ⇒ 非合格 + 零产出 ⇒ 零保留项（由 service 层拒）。
    """
    strategies = sorted_scenario_strategies()

    # ① feedback 明确说合格 ⇒ 命中
    facts = collect_facts({'defects': [], 'tuning_result': 'qualified'})
    assert facts['last_tuning_result'] == 'qualified'
    assert select_strategy(strategies, facts).scenario_code == 'qualified_efficiency'

    # ② feedback 没说合格（「没有缺陷」≠「合格」）⇒ 不命中
    facts = collect_facts({'defects': []})
    assert facts.get('last_tuning_result') is None
    scenario = select_strategy(strategies, facts)
    assert scenario.scenario_code != 'qualified_efficiency'

    # ③ 引擎零产出不改变判定 ⇒ 非合格 + 零建议 ⇒ 零保留项（不会误入省能耗）
    scheme, _outcome = _apply(BASE, [], strategy=scenario, facts=facts)
    assert scheme.kept == ()
