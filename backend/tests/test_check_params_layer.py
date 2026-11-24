"""第4层（校验参数合理性）的护栏。

参照系 = 第4层的机制口径（见 ``services/optimize_chain/check_params.py``）：
「**只识别，不处理**」—— 越限的处置落在 service 层，识别层只透传事实。

三类检查各自的参照系：

- 差值越限：设备物理行程（约束的是**位移**，不是单个位置）；
- 经验窗口：材料 × 壁厚的经验区间；
- 锚点自检：锚点关系本身（与第3层共用同一批锚点事实）。
"""

import pytest

from process.services.optimize_chain.check_params import (
    detect_anchor_violations,
    detect_range_violations,
    detect_window_violations,
    validate,
)


def test_injection_time_outside_window_is_detected():
    """参照系（业务口径）：工艺窗口是经验区间，越界即该建议无效。"""
    params = {'inj_t': 8.0}

    violations = detect_window_violations(params, {'inj_t': (1.0, 5.0)})

    assert [item.field for item in violations] == ['inj_t']
    assert violations[0].bound == 'upper'
    assert violations[0].actual == pytest.approx(8.0)


def test_holding_time_window_violation_detected():
    """参照系（业务口径）：保压时间是经验窗口（材料族 × 壁厚）⇒ 越界即无效。"""
    params = {'hold_stg': 2, 'hold_t_1': 6.0, 'hold_t_2': 12.0}

    violations = detect_window_violations(
        params,
        {'hold_t_1': (2.0, 10.0), 'hold_t_2': (2.0, 10.0)},
    )

    assert [item.field for item in violations] == ['hold_t_2']
    assert violations[0].bound == 'upper'
    assert violations[0].actual == pytest.approx(12.0)


def test_range_violation_detected_by_difference_not_by_single_value():
    """参照系（业务口径）：设备行程约束的是位移，不是单个位置。"""
    params = {
        'met_stg': 2,
        'met_pos_2': 300.0,
        'vps_pos': 50.0,
        'met_end_pos': 280.0,
    }

    violations = detect_range_violations(params, {'injection_stroke': 200.0})

    # 300 − 50 = 250 > 200 ⇒ 超限；两个单值都不等于这个限值，单独比较查不出来
    assert [item.range_id for item in violations] == ['injection_stroke']
    assert violations[0].actual == pytest.approx(250.0)


def test_anchor_violation_detected_when_end_position_mismatches():
    """参照系（业务口径）：计量终止位置 = 末段熔胶位置 + 后松退距离 ⇒ 对不上就是失配。"""
    params = {
        'met_stg': 3,
        'met_end_pos': 363.79,          # 应为 357.29 + 3.5 = 360.79
        'met_pos_3': 357.29,
        'pst_met_decomp_dist': 3.5,
    }

    violations = detect_anchor_violations(params)

    assert [item.anchor_id for item in violations] == ['g1.meter_end_position']
    assert violations[0].members == ('met_end_pos', 'met_pos_3', 'pst_met_decomp_dist')


def test_anchor_check_silent_when_relation_holds():
    """参照系（业务口径）：关系成立时不报 —— 失配要能检出，但不该满屏都是。"""
    params = {
        'met_stg': 1,
        'met_end_pos': 360.79,          # = 357.29 + 3.5
        'met_pos_1': 357.29,
        'vps_pos': 100.0,
        'pst_met_decomp_dist': 3.5,
    }

    assert detect_anchor_violations(params) == []


def test_suckback_chain_break_reported_by_anchor_check():
    """参照系（业务口径）：回抽过程要求各段终点严格递增 ⇒ 断裂要能检出。"""
    params = {
        'met_stg': 3,
        'vps_pos': 100.0,
        'met_pos_1': 105.0,
        'met_pos_2': 120.0,
        'met_pos_3': 110.0,             # 越过第 2 段 ⇒ 回抽过程不成立
        'met_end_pos': 113.5,
        'pst_met_decomp_dist': 3.5,
    }

    violations = detect_anchor_violations(params)

    assert [item.anchor_id for item in violations] == ['g2.suckback_chain']


# --- 第4层的统一入口：一次跑完三类检查 --------------------------------------


def test_validate_reports_the_anchor_mismatch():
    """参照系（业务口径）：新建轮次没有旧值可比 ⇒ 第3层不传导，失配要由第4层报出来。"""
    params = {
        'met_stg': 1,
        'met_end_pos': 361.0,          # 与 met_pos_1 不自洽
        'met_pos_1': 357.29,
        'pst_met_decomp_dist': 3.5,
    }

    outcome = validate(params)

    assert not outcome.ok
    assert [item.anchor_id for item in outcome.anchor_violations] == ['g1.meter_end_position']
    assert outcome.messages()


def test_validate_is_ok_when_everything_holds():
    """参照系（业务口径）：没查出问题 ⇒ ``ok``（不产噪声）。"""
    params = {
        'met_stg': 1,
        'met_end_pos': 360.79,
        'met_pos_1': 357.29,
        'vps_pos': 100.0,
        'pst_met_decomp_dist': 3.5,
        'inj_t': 3.0,
    }

    outcome = validate(
        params,
        limits={'injection_stroke': 300.0},
        windows={'inj_t': (1.0, 5.0)},
    )

    assert outcome.ok
    assert outcome.messages() == ()


def test_validate_collects_all_three_kinds():
    """参照系：三类检查**一次跑完** —— 差值越限 / 工艺窗口 / 锚点失配。"""
    params = {
        'met_stg': 1,
        'met_end_pos': 400.0,          # 与 met_pos_1 不自洽（锚点失配）
        'met_pos_1': 300.0,
        'vps_pos': 50.0,               # 注射行程 250 > 200 ⇒ 差值越限
        'pst_met_decomp_dist': 3.5,
        'inj_t': 8.0,                  # 超出窗口 (1, 5)
    }

    outcome = validate(
        params,
        limits={'injection_stroke': 200.0},
        windows={'inj_t': (1.0, 5.0)},
    )

    assert not outcome.ok
    assert [item.range_id for item in outcome.range_violations] == ['injection_stroke']
    assert [item.field for item in outcome.window_violations] == ['inj_t']
    assert [item.anchor_id for item in outcome.anchor_violations] == ['g1.meter_end_position']
    assert len(outcome.messages()) == 3
