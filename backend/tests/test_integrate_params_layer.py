"""第3层（整合参数）的护栏。

参照系 = 第3层的机制口径（见 ``algorithms/integrate_params.py``）：
「**把方向变成物理上自洽的参数集**」。

每条用例挂一个**独立于被测实现**的参照系：

- 业务口径：物理关系本身（计量终止位置 = 一段熔胶位置 + 后松退距离）；
- 数值锚点：物理量级（实际注射行程 = 末段熔胶位置 − VP 切换位置）；
- 回落口径：缺段数时怎么办（不崩、不瞎推）；
- 口径边界：新版 expert 的真实口径（多段计量时终止位置锚定储料回退终点）；
- 业务口径：目标已达成 ⇒ 该项让位并留痕。
"""

import pytest

from process.algorithms.anchors import apply_mel_targets, resolve_mel_target
from process.algorithms.integrate_params import (
    diff_numeric_fields,
    integrate,
    propagate,
)


def test_meter_end_position_change_propagates_to_metering_position():
    """参照系（业务口径）：计量终止位置 = 计量最后一段的位置 + 后松退距离。"""
    params = {
        'met_stg': 3,
        'met_end_pos': 360.79,
        'met_pos_3': 357.29,
        'pre_met_decomp_dist': 2.0,
        'pst_met_decomp_dist': 3.5,
    }

    result = propagate(params, {'met_end_pos': 361.0})

    # 361.0 − 3.5 = 357.5（前松退 2.0 不参与：计量终止位置只含后松退）
    assert result.values['met_pos_3'] == pytest.approx(357.5)
    assert result.values['met_end_pos'] == pytest.approx(361.0)
    assert 'met_pos_3' in result.derived_fields


def test_metering_position_change_propagates_to_meter_end_position():
    """参照系（业务口径）：计量终止位置 = 计量最后一段的位置 + 后松退距离（反向联动）。"""
    params = {
        'met_stg': 3,
        'met_end_pos': 360.79,
        'met_pos_3': 357.29,
        'vps_pos': 100.0,
        'pst_met_decomp_dist': 3.5,
    }

    result = propagate(params, {'met_pos_3': 358.0})

    # 358.0 + 3.5 = 361.5（螺杆最终停放位置跟着退）
    assert result.values['met_end_pos'] == pytest.approx(361.5)
    assert 'met_end_pos' in result.derived_fields
    # 熔胶位置动了 ⇒ 实际注射量（ML_N − VPTL）随之变
    assert result.values['met_pos_3'] - result.values['vps_pos'] == pytest.approx(258.0)


def test_back_off_change_moves_end_position_but_not_injection_amount():
    """参照系（业务口径）：储后松退是螺杆回抽量 ⇒ 停放位置跟着变，实际注射量不变。"""
    params = {
        'met_stg': 1,
        'met_end_pos': 360.79,
        'met_pos_1': 357.29,
        'vps_pos': 100.0,
        'pst_met_decomp_dist': 3.5,
    }

    result = propagate(params, {'pst_met_decomp_dist': 5.0})

    # 357.29 + 5.0 = 362.29（螺杆多退一点，防流延余量变大）
    assert result.values['met_end_pos'] == pytest.approx(362.29)
    assert 'met_end_pos' in result.derived_fields
    # 但熔胶位置不动 ⇒ 实际注射量（ML_N − VPTL）不受影响
    assert result.values['met_pos_1'] == pytest.approx(357.29)
    assert result.values['met_pos_1'] - result.values['vps_pos'] == pytest.approx(257.29)


def test_speed_change_leaves_injection_time_untouched():
    """参照系（业务口径）：注射阶段是速度控制，设定时间不由行程反算。"""
    params = {
        'met_stg': 1,
        'met_pos_1': 200.0,
        'vps_pos': 100.0,
        'inj_spd_1': 50.0,
        'inj_t': 2.0,
    }

    result = propagate(params, {'inj_spd_1': 100.0})

    # 速度改了，注射时间不动 —— 设定时间只是设定值，实际时间另有偏差
    assert result.values['inj_t'] == pytest.approx(2.0)
    assert 'inj_t' not in result.derived_fields


def test_injection_time_change_yields_to_speed_freedom():
    """参照系（业务口径）：速度是自由度，改时间的建议让位给速度。"""
    params = {'inj_spd_1': 50.0, 'inj_t': 2.0}

    result = propagate(params, {'inj_t': 3.0})

    assert result.superseded_fields == {'inj_t': 'inj_spd_1'}
    # 让位 = 不生效：值回退为当前值，而不是嘴上说让位却照样用新值
    assert result.values['inj_t'] == pytest.approx(2.0)


def test_both_ends_changed_together_keeps_independent_side():
    """参照系（业务口径）：两端同时改时，**自动计算量让位给独立量**。

    ``MEL`` 在机台上就是自动算出来的（由 ``ML_N + DDAM`` 决定）⇒
    它不与上游争；两端同时改时以 ``ML_N`` 为准重算 ``MEL``，并留痕。
    """
    params = {
        'met_stg': 1,
        'met_end_pos': 360.79,
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
    }

    result = propagate(params, {'met_end_pos': 361.0, 'met_pos_1': 350.0})

    # 以独立量为准：350.0 + 3.5 = 353.5（用户填的 361.0 被覆盖）
    assert result.values['met_end_pos'] == pytest.approx(353.5)
    assert result.values['met_pos_1'] == pytest.approx(350.0)
    assert 'met_end_pos' in result.derived_fields
    # 留痕：说清楚为什么没按用户填的 MEL 生效
    assert result.conflicts


def test_missing_stage_count_leaves_position_untouched():
    """参照系（回落口径）：缺计量段数 ⇒ 末段熔胶位置无法确定 ⇒ 不推导、不臆造。"""
    params = {
        'met_end_pos': 360.79,
        'pst_met_decomp_dist': 3.5,
    }

    result = propagate(params, {'met_end_pos': 361.0})

    assert 'met_pos_1' not in result.values
    assert result.values['met_end_pos'] == pytest.approx(361.0)
    # 回落也要留痕：说清楚为什么没联动
    assert result.unresolved


def test_each_stage_position_is_independent():
    """参照系（业务口径）：各段终点各自独立 —— 想让第一段抽长一点、第二段短一点，
    可以直接设值，不受初始化时的系数划分约束。"""
    params = {
        'met_stg': 3,
        'vps_pos': 100.0,
        'met_pos_1': 105.0,
        'met_pos_2': 120.0,
        'met_pos_3': 130.0,
    }

    result = propagate(params, {'met_pos_1': 108.0, 'met_pos_2': 116.0})

    # 两段各自设值：108 → 116 → 130，不重排、不按系数分配
    assert result.values['met_pos_1'] == pytest.approx(108.0)
    assert result.values['met_pos_2'] == pytest.approx(116.0)
    assert result.values['met_pos_3'] == pytest.approx(130.0)


def test_suckback_chain_break_reverts_the_direct_change():
    """参照系（业务口径）：回抽过程要求各段终点严格递增 ⇒ 违法的直接改动不生效。"""
    params = {
        'met_stg': 3,
        'vps_pos': 100.0,
        'met_pos_1': 105.0,
        'met_pos_2': 120.0,
        'met_pos_3': 130.0,
    }

    result = propagate(params, {'met_pos_2': 135.0})

    # 135 越过第 3 段（130）⇒ 回抽过程不成立 ⇒ 该直接改动回退
    assert result.values['met_pos_2'] == pytest.approx(120.0)
    assert result.unresolved


def test_holding_stages_are_independent():
    """参照系（业务口径）：多段保压各自设定 ⇒ 改一段不动另一段。

    系数表（``_MULTI_HOLD_COEF_MAP``）只属初始化时的一次性划分，
    不得用于优化联动 —— 与多段计量（G2）同口径。
    """
    params = {
        'hold_stg': 3,
        'hold_pres_1': 60.0,
        'hold_pres_2': 45.0,
        'hold_pres_3': 30.0,
        'hold_t_1': 8.0,
        'hold_t_2': 4.0,
        'hold_t_3': 2.0,
    }

    result = propagate(params, {'hold_pres_2': 50.0, 'hold_t_2': 5.0})

    # 改中间一段 ⇒ 只这一段变；其余段保持原值
    assert result.values['hold_pres_2'] == pytest.approx(50.0)
    assert result.values['hold_t_2'] == pytest.approx(5.0)
    assert result.values['hold_pres_1'] == pytest.approx(60.0)
    assert result.values['hold_pres_3'] == pytest.approx(30.0)
    assert result.values['hold_t_1'] == pytest.approx(8.0)
    # 各段独立 ⇒ 没有任何联动推导
    assert result.derived_fields == ()


# --- 写入前的整合（差分 → 传导 → 回填）-------------------------------------


def test_diff_only_reports_numeric_changes():
    """参照系（回落口径）：差分只认「真变了」的数值；新字段 / 非数值不算改动。"""
    previous = {'met_end_pos': 360.79, 'param_source': 'manual_adjusted'}
    current = {'met_end_pos': 360.79, 'param_source': 'system_inferred', 'inj_spd_1': 50.0}

    direct = diff_numeric_fields(previous, current)

    # 值没变不认；字符串不认；新出现的字段没有旧值可比 ⇒ 不认
    assert direct == {}


def test_integrate_applies_link_from_diff():
    """参照系（业务口径）：改计量终止位置 ⇒ 计量位置跟着反推（写入前的数据体检）。"""
    previous = {
        'met_stg': 1,
        'met_end_pos': 360.79,
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
    }
    current = dict(previous)
    current['met_end_pos'] = 361.0

    outcome = integrate(current, previous)

    assert outcome.values['met_end_pos'] == pytest.approx(361.0)
    assert outcome.values['met_pos_1'] == pytest.approx(357.5)
    assert outcome.direct_fields == ('met_end_pos',)
    assert outcome.derived_fields == ('met_pos_1',)


def test_integrate_without_previous_does_not_propagate():
    """参照系（回落口径）：新建轮次没有旧值可比 ⇒ 不臆造改动。"""
    values = {
        'met_stg': 1,
        'met_end_pos': 361.0,          # 与 met_pos_1 不自洽
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
    }

    outcome = integrate(values)

    # 没有传导（met_pos_1 不被改成 357.5）
    assert outcome.values['met_pos_1'] == pytest.approx(357.29)
    assert outcome.derived_fields == ()


def test_integrate_leaves_unrelated_fields_untouched():
    """参照系（业务口径）：传导只碰锚点关系涉及的量 ⇒ 其它参数原样落库。"""
    previous = {
        'met_stg': 1,
        'met_end_pos': 360.79,
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
        'inj_spd_1': 50.0,
        'inj_t': 2.0,
    }
    current = dict(previous)
    current['met_end_pos'] = 361.0
    current['inj_spd_1'] = 55.0

    outcome = integrate(current, previous)

    assert outcome.values['inj_spd_1'] == pytest.approx(55.0)   # 不受牵连
    assert outcome.values['inj_t'] == pytest.approx(2.0)         # 不受牵连
    assert outcome.values['met_pos_1'] == pytest.approx(357.5)   # 被联动


# --- MEL 目标 ⇒ 决策量（先定 ML，再确定 MEL）-------------------------------


def test_mel_target_resolves_to_metering_position():
    """参照系（业务口径）：停放位置 = 计量位置 + 储后松退 ⇒ 目标 MEL 落在计量位置上。"""
    previous = {
        'met_stg': 1,
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
        'met_end_pos': 360.79,
    }

    field_name, ml_value = resolve_mel_target(previous, 361.0, previous=previous)

    assert field_name == 'met_pos_1'
    assert ml_value == pytest.approx(357.5)      # 357.29 + (361.0 − 360.79)


def test_mel_target_is_satisfied_through_metering_position():
    """参照系（业务口径）：MEL 目标最终要被满足，但**先定 ML** ⇒ MEL 由 ML 算出。

    机台上真正会被调的是计量位置与储后松退，MEL 只是算法侧的标 ⇒
    算法给 MEL 目标时，先落成计量位置，MEL 再由它算出 —— 表达上永远是
    「根据 ML 确定 MEL」。
    """
    previous = {
        'met_stg': 1,
        'met_end_pos': 360.79,
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
    }
    current = dict(previous)

    # 先定 ML：MEL 目标翻成决策量（MEL 本身不被碰）
    landed = apply_mel_targets(current, [361.0], previous=previous)

    assert landed == ('met_pos_1',)
    assert current['met_pos_1'] == pytest.approx(357.5)
    assert current['met_end_pos'] == pytest.approx(360.79)   # MEL 没被直接改

    # 再确定 MEL：由计量位置 + 松退算出 —— 目标恰好被满足
    outcome = integrate(current, previous)

    assert outcome.values['met_end_pos'] == pytest.approx(361.0)
    assert outcome.values['met_pos_1'] == pytest.approx(357.5)
    # MEL 从来不是决策量 ⇒ 不构成「两端同时改」
    assert outcome.conflicts == ()


def test_mel_and_ddam_adjustments_stack_on_metering_position():
    """参照系（业务口径）：``ΔDDAM`` 不叠加到计量位置，它落在 ``MEL`` 那一侧。

    两步式：1. ``ML_N 基准 = 原MEL − 原DDAM``；
    2. ``MEL_新 = ML_N + DDAM + ΔDDAM + ΔMEL``。
    ⇒ 落库的计量位置 = ``原ML_N + ΔMEL``；终止位置随松退距离自然后移。
    """
    previous = {
        'met_stg': 1,
        'met_end_pos': 360.79,
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
    }
    current = dict(previous)
    current['pst_met_decomp_dist'] = 5.0        # 同批也调了储后松退（ΔDDAM = +1.5）

    # 算法给的 MEL 目标 = 旧 MEL + 10
    landed = apply_mel_targets(current, [370.79], previous=previous)

    assert landed == ('met_pos_1',)
    # ML_N = (原MEL − 原DDAM) + ΔMEL = 357.29 + 10（ΔDDAM 不叠加）
    assert current['met_pos_1'] == pytest.approx(367.29)

    # MEL 再由 ML_N + DDAM 算出 = 367.29 + 5.0 = 372.29
    outcome = integrate(current, previous)

    assert outcome.values['met_end_pos'] == pytest.approx(372.29)
