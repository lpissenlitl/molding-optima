"""初始化链路的越限守卫（机台能力校验）—— 护栏。

参照系 = ``process.services.parameter_initialize._guard_initial_params``：
初始化算出来的初值若超出机台能力 ⇒ **拒绝 400**（不落库错参数）。

**一道守卫**（``guard_parameter_limits``）：初值一律跟「允许区间」比 ——
设定值类的上限是机台**可设定上限**，位置类的上限是设备实测**注射行程**
⇒ 位置参数与设定值参数同构（都是设定工艺参数）⇒ **不分类、不设特例**。

这些用例锁的是**机制契约**：

- 初值越限 ⇒ **拒绝**（不是「剔建议、值照写」的半处理）；
- 机台没录上限 ⇒ **不判**（缺数据不等于参数不合理）；
- 边界（正好等于上限）⇒ 不算超（判据是「大于」）；
- 低于下界（设备类来源的下界显式为 0）⇒ 也算越界；
- ``initialize_from_condition`` **不跑推理算法**（复制源参数）⇒ 无初值 ⇒ 不判。
"""
import os
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

import pytest

from extensions.exceptions import BizException, ERROR_DATA_INVALID
from process.services import parameter_initialize as init_mod
from process.services.parameter_initialize import ParameterInitializeService


#: 机台：可设定注射压力上限 100MPa；实测注射行程 200mm
MACHINE = {
    'max_set_injection_pressure': 100.0,
    'max_injection_stroke': 200.0,
}


def _guard(values, machine_info=MACHINE):
    """调初始化链路的守卫（越限 ⇒ 抛异常；不越限 ⇒ 正常返回）。"""
    init_mod._guard_initial_params(
        values=values,
        machine_info=machine_info,
        interface_tag='test',
    )


# --- 设定值类（设备安全红线）---

def test_initial_setting_over_limit_is_rejected():
    """初值超机台可设定上限 ⇒ 拒绝 400（设备安全红线）。"""
    with pytest.raises(BizException) as excinfo:
        _guard({'inj_pres_1': 120.0})
    assert excinfo.value.error_code == ERROR_DATA_INVALID
    assert '超出允许区间' in excinfo.value.detail_message


def test_initial_setting_within_limit_passes():
    """初值在上限内 ⇒ 放行。"""
    _guard({'inj_pres_1': 80.0})


def test_initial_setting_equal_to_limit_passes():
    """正好等于上限 ⇒ 不算超（判据是「大于」而非「大于等于」）。"""
    _guard({'inj_pres_1': 100.0})


def test_missing_machine_setting_limit_is_not_judged():
    """机台没录可设定上限 ⇒ **不判**（缺数据不等于参数不合理）。"""
    _guard({'inj_pres_1': 999.0}, machine_info={})


def test_temperature_params_are_not_judged_by_setting_limit():
    """温度类参数尚未登记允许区间 ⇒ **不判**（将来接入材料推荐值区间后才参与比较）。"""
    _guard({'brl_temp_1': 999.0, 'noz_temp': 999.0})


def test_initial_below_lower_bound_is_rejected():
    """初值低于下界（设备类来源的下界显式为 0）⇒ 拒绝 400。"""
    with pytest.raises(BizException) as excinfo:
        _guard({'inj_pres_1': -5.0})
    assert excinfo.value.error_code == ERROR_DATA_INVALID
    assert '超出允许区间' in excinfo.value.detail_message


# --- 位置类（超注射行程）---

def test_initial_over_stroke_is_rejected():
    """初值超机台注射行程 ⇒ 拒绝 400（位置参数同样是设定值，与设定值类同构）。"""
    with pytest.raises(BizException) as excinfo:
        _guard({'met_end_pos': 291.0})
    assert excinfo.value.error_code == ERROR_DATA_INVALID
    assert '超出允许区间' in excinfo.value.detail_message


def test_missing_machine_stroke_is_not_judged():
    """机台没录行程 ⇒ **不判**。"""
    _guard({'met_end_pos': 291.0}, machine_info={})


# --- 链路接入：initialize_from_provided 走守卫 ---

def test_initialize_from_provided_applies_guard():
    """纯推理入口 ⇒ 初值越限 ⇒ 拒绝（不返回错初值）。"""
    kernel_result = {
        'param_source': 'ai_recommendation',
        'matched_rules': ['DEFAULT'],
        'process': {'inj_pres_steps': [120.0]},
        'mold_temp': {'mold_temp': 50.0},
        'hot_runner': {'valve_num': 0, 'valve_time_steps': []},
    }
    with patch.object(ParameterInitializeService, '_infer_kernel', return_value=kernel_result):
        with pytest.raises(BizException) as excinfo:
            ParameterInitializeService.initialize_from_provided(
                mold_info={}, machine_info=MACHINE, polymer_info={},
            )
    assert excinfo.value.error_code == ERROR_DATA_INVALID


def test_initialize_from_provided_passes_when_within_limit():
    """初值在上限内 ⇒ 正常返回 flat parameter。"""
    kernel_result = {
        'param_source': 'ai_recommendation',
        'matched_rules': ['DEFAULT'],
        'process': {'inj_pres_steps': [80.0]},
        'mold_temp': {'mold_temp': 50.0},
        'hot_runner': {'valve_num': 0, 'valve_time_steps': []},
    }
    with patch.object(ParameterInitializeService, '_infer_kernel', return_value=kernel_result):
        result = ParameterInitializeService.initialize_from_provided(
            mold_info={}, machine_info=MACHINE, polymer_info={},
        )
    assert result['parameter']['inj_pres_1'] == 80.0