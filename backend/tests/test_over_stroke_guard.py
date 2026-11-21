"""位置类超行程守卫的护栏。

参照系 = ``process.services.over_limit_guard.guard_position_over_stroke``：
位置类参数（MEL / IL / ML / VPTL）超出设备实测注射行程 ⇒ **拒绝本轮处理**
（初始化与优化两条链路共用同一守卫、同一错误码、同一文案、同一条出路：「换机」）。

这些用例锁的是**机制契约**：

- 超行程 ⇒ **报错**（不是「剔建议、值照写」的半处理，也不是事后回退）；
- 缺机台行程 ⇒ **不判**（缺数据不等于参数不合理）；
- 边界（正好等于行程）⇒ 不算超（判据是「大于」）。
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

import pytest

from extensions.exceptions import BizException
from process.exceptions import ERROR_PROCESS_OVER_STROKE
from process.services.over_limit_guard import guard_position_over_stroke


#: 机台：实测最大注射行程 200mm
MACHINE = {'max_injection_stroke': 200.0}


def _guard(values, machine_info=MACHINE):
    """调守卫（超行程 ⇒ 抛异常；不超 ⇒ 正常返回）。"""
    guard_position_over_stroke(
        values=values,
        machine_info=machine_info,
        scope='optimize',
        interface_tag='test',
    )


def test_over_stroke_is_rejected():
    """落地值超出行程 ⇒ 拒绝（不是半处理）。"""
    with pytest.raises(BizException) as excinfo:
        _guard({'met_end_pos': 291.0})
    assert excinfo.value.error_code == ERROR_PROCESS_OVER_STROKE
    assert '超出本机注射行程' in excinfo.value.detail_message
    assert '请更换行程更大的设备' in excinfo.value.detail_message


def test_not_over_stroke_passes():
    """没超行程 ⇒ 放行。"""
    _guard({'met_end_pos': 195.0})


def test_value_equal_to_limit_passes():
    """正好等于行程 ⇒ 不算超（判据是「大于」而非「大于等于」）。"""
    _guard({'met_end_pos': 200.0})


def test_missing_machine_stroke_is_not_judged():
    """机台没录行程 ⇒ **不判**（缺数据不等于参数不合理）。"""
    _guard({'met_end_pos': 291.0}, machine_info={})


def test_multiple_over_stroke_merged_into_one_message():
    """多项超行程 ⇒ 合并成一条（另 N 项），代表项取超出量最大的那个。"""
    with pytest.raises(BizException) as excinfo:
        _guard({'met_end_pos': 291.0, 'vps_pos': 260.0})
    message = excinfo.value.detail_message
    assert '另有 1 项超出行程' in message
    # MEL 超 91mm > VPTL 超 60mm ⇒ 代表项是熔胶终止位置
    assert '熔胶终止位置' in message
