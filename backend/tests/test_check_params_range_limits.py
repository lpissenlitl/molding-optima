"""第4层「差值越限」判定的护栏。

参照系 = ``process.services.optimize_chain.check_params.resolve_range_limits``：
限值表按 ``RANGE_CHECKS`` 产出 ⇒ 检查项与限值表一一对应，
限值取机台实测注射行程（与「超出机台可设定上限」**同源**）。

这些用例锁的是**机制契约**：

- 限值表与检查项**一一对应**（加检查项不必改接线）；
- 缺机台行程 ⇒ 限值表为空 ⇒ **不判**（缺数据不等于参数不合理）；
- 差值超行程 ⇒ 第4层报出（``range_violations`` 非空 ⇒ ``ok`` 为假）；
- 差值口径与单参数口径是**两个独立判据**（不互相顶替）；
- **差值越限不落在** ``over_limit_violations`` ⇒ 出口只读后者 ⇒ 不触发拒绝。
"""
import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.services.optimize_chain.check_params import (
    RANGE_CHECKS,
    resolve_range_limits,
    validate,
)
from process.services.shared.param_limits import (
    build_limits,
    read_positive_float,
    to_upper_limits,
)

#: 机台：实测最大注射行程 200mm
MACHINE = {'max_injection_stroke': 200.0}
LIMITS = resolve_range_limits(MACHINE)


def test_limits_table_matches_range_checks():
    """限值表与检查项**一一对应** —— 接线不靠手抄键名。"""
    assert set(LIMITS) == {str(check['range_id']) for check in RANGE_CHECKS}


def test_limits_table_carries_the_machine_stroke():
    """限值 = 机台实测行程。"""
    assert LIMITS == {'injection_stroke': 200.0}


def test_stroke_limit_is_the_same_source_as_declared_limits():
    """行程是**同一个源** ⇒ 差值口径与单参数口径不会各说各话。"""
    assert read_positive_float(MACHINE, 'max_injection_stroke') == 200.0
    assert set(to_upper_limits(build_limits(MACHINE)).values()) == {200.0}
    # 差值检查项声明的上限字段 = 单参数侧用的那个字段（同一个源）
    assert {str(check['limit_field']) for check in RANGE_CHECKS} == {'max_injection_stroke'}


def test_missing_machine_stroke_gives_empty_limits():
    """机台没录行程 ⇒ 限值表为空 ⇒ 不检查（不臆造限值）。"""
    assert resolve_range_limits({}) == {}
    assert resolve_range_limits({'max_injection_stroke': None}) == {}
    assert resolve_range_limits({'max_injection_stroke': 0}) == {}
    assert resolve_range_limits({'max_injection_stroke': -5}) == {}
    assert resolve_range_limits({'max_injection_stroke': 'abc'}) == {}
    assert resolve_range_limits({'max_injection_stroke': [200]}) == {}


def test_range_violation_is_reported_after_wiring():
    """差值超行程 ⇒ 第4层报出（不是静默放行）。"""
    report = validate(
        {'met_stg': 1, 'met_pos_1': 300.0, 'vps_pos': 50.0},
        limits=LIMITS,
    )

    assert not report.ok
    assert [item.range_id for item in report.range_violations] == ['injection_stroke']
    assert report.range_violations[0].actual == pytest.approx(250.0)
    assert report.range_violations[0].limit == 200.0


def test_last_stage_member_follows_stage_count():
    """``{last}`` 跟随熔胶段数 ⇒ 判的是**实际末段**的位置。"""
    report = validate(
        {'met_stg': 2, 'met_pos_2': 300.0, 'vps_pos': 50.0},
        limits=LIMITS,
    )

    assert [item.range_id for item in report.range_violations] == ['injection_stroke']
    assert report.range_violations[0].members == ('met_pos_2', 'vps_pos')


def test_difference_within_limit_is_not_reported():
    """差值不超 ⇒ 不报（差值口径与单参数口径**各判各的**）。"""
    report = validate(
        {'met_stg': 1, 'met_pos_1': 180.0, 'vps_pos': 50.0},
        limits=LIMITS,
    )

    assert not report.range_violations


def test_value_equal_to_limit_passes():
    """正好等于行程 ⇒ 不算超（判据是「大于」而非「大于等于」）。"""
    report = validate(
        {'met_stg': 1, 'met_pos_1': 250.0, 'vps_pos': 50.0},
        limits=LIMITS,
    )

    assert not report.range_violations


def test_missing_reference_is_not_judged():
    """没传限值表 ⇒ 不判。"""
    report = validate({'met_stg': 1, 'met_pos_1': 300.0, 'vps_pos': 50.0})

    assert report.ok
    assert not report.range_violations


def test_missing_member_value_is_not_judged():
    """成员缺值 ⇒ 不报（不臆造差值）。"""
    report = validate(
        {'met_stg': 1, 'met_pos_1': 300.0},
        limits=LIMITS,
    )

    assert not report.range_violations


def test_missing_stage_count_is_not_judged():
    """缺熔胶段数 ⇒ 定位不到末段 ⇒ 不报。"""
    report = validate(
        {'met_pos_1': 300.0, 'vps_pos': 50.0},
        limits=LIMITS,
    )

    assert not report.range_violations


def test_difference_check_does_not_touch_over_limit_violations():
    """差值越限**不落** ``over_limit_violations`` ⇒ 出口只读后者 ⇒ 不触发拒绝。"""
    report = validate(
        {'met_stg': 1, 'met_pos_1': 300.0, 'vps_pos': 50.0},
        limits=LIMITS,
        machine_limits=to_upper_limits(build_limits(MACHINE)),
    )

    assert [item.range_id for item in report.range_violations] == ['injection_stroke']
    assert [item.param_name for item in report.over_limit_violations] == ['met_pos_1']
