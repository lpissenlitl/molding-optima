r"""_compute_meter_pres 的动力源分支护栏。

背景：
    ``field_contract.drive_system_to_power_method`` 把 drive_system 标准化为
    '液压机' / '电动机'（不是 '全电机'），故 ``expert/algorithm_engine.py`` 的
    ``_compute_meter_pres`` 与同文件的 ``_compute_suckback_pres`` 统一用
    ``!= '液压机'`` 判断动力源 —— 两处口径必须一致，否则全电机（'电动机'）
    会走错分支 → ``max_set_metering_pressure`` 为 None → TypeError。

覆盖三种 power_method：
    '液压机'  → 走 3 维公式（结果 > 0）
    '电动机'  → 0（全电机无油缸，物理正确）
    '全电机'  → 0（兼容旧词表）
    缺省      → '液压机'（走公式）

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_meter_pres_power_branch.py -q
"""
import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.algorithms.expert.algorithm_engine import AlgorithmEngine  # noqa: E402

BASE_MACH = {
    "nozzle_type": "直通式",
    "max_set_metering_pressure": 20.0,
}

#: coeffs 结构：分组系数（algorithm_engine 内 c_met = coeffs['metering']）
COEFFS = {
    "metering": {
        "meter_pres_ratio_straight": 0.55,
        "meter_pres_min": 0.0,
    }
}


def _make_engine(mach):
    return AlgorithmEngine(
        mold={},
        machine=mach,
        material={},
        process_set={},
        coeffs=COEFFS,
    )


@pytest.mark.parametrize("power_method, expect_positive", [
    ("液压机", True),
    ("电动机", False),      # 全电机无油缸 ⇒ 熔胶压力 0
    ("全电机", False),      # 兼容旧词表
    (None, True),           # 缺省 ⇒ 按液压机走公式
])
def test_meter_pres_follows_power_source_branch(power_method, expect_positive):
    """参照系（业务口径）：熔胶压力只有液压机走公式，全电机为 0。

    【注意】口径必须与 ``_compute_suckback_pres`` 一致（都用 ``!= '液压机'``）
    —— 不一致时全电机会因 ``max_set_metering_pressure`` 为 None 而 TypeError。
    """
    mach = dict(BASE_MACH)
    if power_method is not None:
        mach["power_method"] = power_method

    result = _make_engine(mach)._compute_meter_pres(mach, "PP", COEFFS["metering"])

    if expect_positive:
        assert result > 0, f"动力源={power_method!r} ⇒ meter_pres={result}，期望 > 0"
    else:
        assert result == 0.0, f"动力源={power_method!r} ⇒ meter_pres={result}，期望 == 0"


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_meter_pres_power_branch``。"""
    cases = [
        ("液压机", {"power_method": "液压机"}, True),
        ("电动机（全电机）", {"power_method": "电动机"}, False),
        ("全电机（旧词表，兼容）", {"power_method": "全电机"}, False),
        ("缺省（无 power_method）", {}, True),
    ]
    failed = []
    for name, extra, expect_positive in cases:
        mach = {**BASE_MACH, **extra}
        try:
            result = _make_engine(mach)._compute_meter_pres(mach, "PP", COEFFS["metering"])
        except Exception as exc:  # noqa: BLE001 - 独立跑法需要汇总全部失败
            print(f'  [FAIL] {name}: 抛异常 {exc}')
            failed.append(name)
            continue
        ok = (result > 0) if expect_positive else (result == 0.0)
        if ok:
            print(f'  [OK] {name} → meter_pres={result}')
        else:
            print(f'  [FAIL] {name} → meter_pres={result}')
            failed.append(name)
    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] 共 {len(failed)} 项失败：{failed}')
        return 1
    print('[PASS] 动力源分支行为正确')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())