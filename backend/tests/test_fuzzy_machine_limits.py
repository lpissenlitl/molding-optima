r"""机台物理上限 → 推荐值裁剪（2026-10-27 新增护栏）

覆盖三段：
  1. specs.resolve_param_limits   —— machine_info → {算法参数前缀: 上限}
  2. specs.lookup_param_limit     —— 算法参数名 → 该参数的上限
  3. engine._apply_machine_limits —— 越限封顶 + 方向重算 + 留痕

参照系（均独立于被测实现，不是"实现 == 它自己调的另一个函数"）：
  - 机台物理上限：InjectionUnit.max_set_* 的 ORM 字段名（业务事实）
  - 参数命名：field_names 的「业务前缀 ↔ 算法前缀」映射（既有契约）
  - 物理约束：推荐值不得超出 HMI 可设定范围 —— 操作工输不进去就是无效建议

⚠️ 不依赖规则库数据：直接构造 AlgorithmRecommendation 喂给裁剪方法。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_fuzzy_machine_limits.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.algorithms.base import AlgorithmRecommendation  # noqa: E402
from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.specs import (  # noqa: E402
    lookup_param_limit,
    resolve_param_limits,
)


# 一台液压机的完整上限（对照 InjectionUnit 的实际取值）
MACHINE_INFO = {
    "drive_system": "全液压驱动",
    "max_set_injection_pressure": 100.0,
    "max_set_injection_speed": 80.0,
    "max_set_holding_pressure": 90.0,
    "max_set_holding_speed": 70.0,
    "max_set_screw_rotation_speed": 200.0,
    "max_set_metering_pressure": 100.0,
    "max_set_metering_back_pressure": 15.0,
    "max_set_decompression_pressure": 20.0,
}


def _rec(param_name, current, recommended, direction):
    return AlgorithmRecommendation(
        param_name=param_name,
        current_value=current,
        recommended_value=recommended,
        confidence=0.9,
        reason="模糊推理 (sources=['numeric'])",
        source='fuzzy.numeric',
        direction=direction,
    )


def test_resolve_param_limits_maps_fields():
    """machine_info 的上限字段 → 算法参数前缀映射。"""
    limits = resolve_param_limits(MACHINE_INFO)

    assert limits['IP'] == 100.0, limits      # 注射压力
    assert limits['IV'] == 80.0, limits       # 注射速度
    assert limits['PP'] == 90.0, limits       # 保压压力
    assert limits['PV'] == 70.0, limits       # 保压速度
    assert limits['MSR'] == 200.0, limits     # 螺杆转速
    assert limits['MP'] == 100.0, limits      # 熔胶压力
    assert limits['MBP'] == 15.0, limits      # 熔胶背压


def test_resolve_param_limits_skips_missing():
    """机台没填上限 → 该参数无上限（不补默认值、不拦请求）。"""
    limits = resolve_param_limits({"drive_system": "全液压驱动"})

    assert limits == {}, limits


def test_lookup_param_limit_by_segment():
    """带段号的分段参数取到对应上限（段号不参与上限判定）。"""
    limits = resolve_param_limits(MACHINE_INFO)

    assert lookup_param_limit('IP0', limits) == 100.0
    assert lookup_param_limit('IV3', limits) == 80.0


def test_lookup_param_limit_ignores_whole_params():
    """整段参数（无数字后缀）没有机台上限，不参与裁剪。"""
    limits = resolve_param_limits(MACHINE_INFO)

    # IPOS=注射位置、NT=喷嘴温度、MT=模温 —— 都不是分段参数
    assert lookup_param_limit('IPOS', limits) is None
    assert lookup_param_limit('NT', limits) is None
    assert lookup_param_limit('MT', limits) is None
    # 不带段号的分段参数也不认（避免与整段参数混淆）
    assert lookup_param_limit('IP', limits) is None


def test_apply_machine_limits_clips_to_ceiling():
    """越限 ⇒ 封顶到机台上限。"""
    engine = FuzzyEngine()
    limits = resolve_param_limits(MACHINE_INFO)

    rec = _rec('IP0', current=60.0, recommended=180.0, direction='increase')
    engine._apply_machine_limits([rec], limits)

    assert rec.recommended_value == 100.0, rec.recommended_value
    # 封顶后仍高于当前值 ⇒ 方向不变
    assert rec.direction == 'increase', rec.direction
    # 裁剪事实留痕
    reports = [r for r in engine._field_reports if r['layer'] == 'machine_limits']
    assert len(reports) == 1, engine._field_reports
    assert reports[0]['param'] == 'IP0'
    assert reports[0]['clipped_to'] == 100.0
    assert reports[0]['origin_value'] == 180.0


def test_apply_machine_limits_refixes_direction_down():
    """当前值已超上限时，封顶后方向要改成 decrease（不能仍显示 increase）。"""
    engine = FuzzyEngine()
    limits = resolve_param_limits(MACHINE_INFO)

    rec = _rec('IV0', current=110.0, recommended=106.3, direction='decrease')
    engine._apply_machine_limits([rec], limits)

    assert rec.recommended_value == 80.0, rec.recommended_value
    assert rec.direction == 'decrease', rec.direction


def test_apply_machine_limits_keeps_in_range():
    """未越限 ⇒ 值与方向都不动，也不留痕。"""
    engine = FuzzyEngine()
    limits = resolve_param_limits(MACHINE_INFO)

    rec = _rec('IP0', current=60.0, recommended=63.7, direction='increase')
    engine._apply_machine_limits([rec], limits)

    assert rec.recommended_value == 63.7, rec.recommended_value
    assert rec.direction == 'increase', rec.direction
    assert not [r for r in engine._field_reports if r['layer'] == 'machine_limits']


def test_apply_machine_limits_without_limits():
    """机台没填上限 ⇒ 不裁剪、不拦（缺数据不等于不能给建议）。"""
    engine = FuzzyEngine()

    rec = _rec('IP0', current=60.0, recommended=180.0, direction='increase')
    engine._apply_machine_limits([rec], {})

    assert rec.recommended_value == 180.0, rec.recommended_value
    assert rec.direction == 'increase', rec.direction


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_fuzzy_machine_limits``。"""
    cases = [
        test_resolve_param_limits_maps_fields,
        test_resolve_param_limits_skips_missing,
        test_lookup_param_limit_by_segment,
        test_lookup_param_limit_ignores_whole_params,
        test_apply_machine_limits_clips_to_ceiling,
        test_apply_machine_limits_refixes_direction_down,
        test_apply_machine_limits_keeps_in_range,
        test_apply_machine_limits_without_limits,
    ]
    failed = []
    for fn in cases:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - 独立跑法需要汇总全部失败
            print(f'[FAIL] {fn.__name__}: {exc}')
            failed.append(fn.__name__)
    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] {len(failed)}/{len(cases)} 个用例失败：{failed}')
        return 1
    print(f'[PASS] {len(cases)}/{len(cases)} 个用例通过')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
