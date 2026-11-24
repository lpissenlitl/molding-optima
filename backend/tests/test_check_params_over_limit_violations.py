"""第4层「参数超出机台可设定上限」判定的护栏。

参照系 = ``process.services.optimize_chain.check_params.detect_over_limit_violations``：
参数超出机台对它设定的可设定上限 ⇒ **第4层**判出。

【注意】**所有参数一视同仁**：位置参数（``met_end_pos`` / ``inj_pos_1`` /
``met_pos_1`` / ``vps_pos``）与压力 / 速度参数
同构 —— 都是「设定工艺参数」，上限都是「这台机器这个能力项最多能设到多少」
⇒ 只判一条，不分两类。

这些用例锁的是**机制契约**：

- 超上限 ⇒ 第4层报出（``over_limit_violations`` 非空 ⇒ ``ok`` 为假）；
- **设定值类也判**（统一口径的落点：以前只判位置类）；
- 缺参照系（不传 ``machine_limits``）⇒ **不判**（缺数据不等于参数不合理）；
- 边界（正好等于上限）⇒ 不算超（判据是「大于」）；
- **业务命名进 / 业务命名判**（``met_end_pos`` / ``inj_pos_1`` 原样判定，不翻译）；
- **溯源**：越限项带 ``limit_field``（上限取自哪个设备字段）；
- **文案单一源**：第4层报出的项走 ``format_unfit_param_message``。
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.services.optimize_chain.check_params import (
    detect_over_limit_violations,
    validate,
)
from process.services.shared.param_limits import (
    build_limits,
    format_unfit_param_message,
    to_upper_limits,
)

#: 机台：实测最大注射行程 200mm + 最大可设定注射压力 100MPa
MACHINE = {
    'max_injection_stroke': 200.0,
    'max_set_injection_pressure': 100.0,
}
LIMITS = to_upper_limits(build_limits(MACHINE))


def test_over_limit_is_reported():
    """超上限 ⇒ 第4层报出（不是静默放行）。"""
    report = validate({'met_end_pos': 291.0}, machine_limits=LIMITS)
    assert not report.ok
    assert [item.param_name for item in report.over_limit_violations] == ['met_end_pos']
    assert report.over_limit_violations[0].limit == 200.0
    assert report.over_limit_violations[0].exceeded_by == 91.0


def test_setting_params_are_judged_too():
    """【统一口径】压力类参数同样按「它自己的上限」判（不再只判位置类）。"""
    report = validate({'inj_pres_1': 150.0}, machine_limits=LIMITS)
    assert not report.ok
    assert [item.param_name for item in report.over_limit_violations] == ['inj_pres_1']
    assert report.over_limit_violations[0].limit == 100.0
    # 溯源：上限取自哪个设备字段（信息量比「来源类型」标记更大）
    assert report.over_limit_violations[0].limit_field == 'max_set_injection_pressure'


def test_position_param_traces_stroke_field():
    """位置类参数的溯源字段 = 机台实测行程。"""
    report = validate({'met_end_pos': 291.0}, machine_limits=LIMITS)
    assert report.over_limit_violations[0].limit_field == 'max_injection_stroke'


def test_business_names_are_judged_as_is():
    """业务命名进 ⇒ 业务命名判（分段 + 整段都覆盖）。"""
    report = validate(
        {
            'inj_pos_1': 260.0,
            'met_pos_1': 300.0,
            'met_end_pos': 291.0,
            'vps_pos': 260.0,
        },
        machine_limits=LIMITS,
    )
    assert sorted(
        item.param_name for item in report.over_limit_violations
    ) == ['inj_pos_1', 'met_end_pos', 'met_pos_1', 'vps_pos']


def test_missing_reference_is_not_judged():
    """没传参照系 ⇒ 不判。"""
    report = validate({'met_end_pos': 291.0})
    assert report.ok
    assert not report.over_limit_violations


def test_missing_machine_limits_gives_empty_table():
    """机台没录上限 ⇒ 参照系为空 ⇒ 不判（不臆造限值）。"""
    report = validate(
        {'met_end_pos': 291.0},
        machine_limits=to_upper_limits(build_limits({})),
    )
    assert report.ok


def test_value_equal_to_limit_passes():
    """正好等于上限 ⇒ 不算超（判据是「大于」而非「大于等于」）。"""
    report = validate({'met_end_pos': 200.0}, machine_limits=LIMITS)
    assert report.ok


def test_detect_returns_empty_without_limits():
    """识别函数：缺参照系 ⇒ 空列表（不臆造）。"""
    assert detect_over_limit_violations({'met_end_pos': 291.0}, {}) == []


def test_over_limit_message_merges_multiple_items():
    """多处超限 ⇒ 合并成一条（另 N 项），代表项取超出量最大的那个。"""
    values = {'met_end_pos': 291.0, 'vps_pos': 260.0}
    report = validate(values, machine_limits=LIMITS)
    message = format_unfit_param_message(report.over_limit_violations)
    assert '另有 1 项超出可设定上限' in message
    # 熔胶终止位置超 91mm > VP 切换位置超 60mm ⇒ 代表项是熔胶终止位置
    assert '熔胶终止位置' in message
