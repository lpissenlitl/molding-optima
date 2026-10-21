"""
verify_meter_pres_power_branch.py
验证 _compute_meter_pres 的动力源分支在标准化 power_method 词表下行为正确。

背景（2026-10-20）：
    field_contract.drive_system_to_power_method 把 drive_system 标准化为
    '液压机' / '电动机'（不是 '全电机'），而 expert/algorithm_engine.py
    的 _compute_meter_pres 原先判断 `== '全电机'`，导致：
      - 全电机（'电动机'）走错分支 → max_set_metering_pressure 为 None → TypeError
      - 同文件的 _compute_suckback_pres 却用 `!= '液压机'`，两处口径不一致
    → 已把 _compute_meter_pres 统一为 `!= '液压机'`。

本脚本直接调用 _compute_meter_pres，验证三种 power_method：
    '液压机'  → 走 3 维公式（结果 > 0）
    '电动机'  → 0（全电机无油缸，物理正确）
    '全电机'  → 0（兼容旧词表）
    缺省      → '液压机'（走公式）
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.algorithms.expert.algorithm_engine import AlgorithmEngine


def main():
    print("=" * 70)
    print("_compute_meter_pres 动力源分支验证")
    print("=" * 70)

    base_mach = {
        "nozzle_type": "直通式",
        "max_set_metering_pressure": 20.0,
    }

    # coeffs 结构：分组系数（algorithm_engine 内 c_met = coeffs['metering']）
    coeffs = {
        "metering": {
            "meter_pres_ratio_straight": 0.55,
            "meter_pres_min": 0.0,
        }
    }

    def _make_engine(mach: dict) -> AlgorithmEngine:
        return AlgorithmEngine(
            mold={},
            machine=mach,
            material={},
            process_set={},
            coeffs=coeffs,
        )

    cases = [
        ("液压机", {"power_method": "液压机"}, True),
        ("电动机（全电机）", {"power_method": "电动机"}, False),
        ("全电机（旧词表，兼容）", {"power_method": "全电机"}, False),
        ("缺省（无 power_method）", {}, True),
    ]

    failures = []
    for name, extra, expect_positive in cases:
        mach = {**base_mach, **extra}
        try:
            result = _make_engine(mach)._compute_meter_pres(mach, "PP", coeffs["metering"])
        except Exception as e:
            failures.append(f"{name}: 抛异常 {e}")
            print(f"  [FAIL] {name}: 抛异常 {e}")
            continue

        ok = (result > 0) if expect_positive else (result == 0.0)
        if ok:
            print(f"  [OK] {name} → meter_pres={result}")
        else:
            failures.append(f"{name}: 期望 {'>0' if expect_positive else '==0'}，实际 {result}")
            print(f"  [FAIL] {name} → meter_pres={result}（期望 "
                  f"{'>0' if expect_positive else '==0'}）")

    print("=" * 70)
    if failures:
        print(f"[FAIL] 共 {len(failures)} 项：")
        for f in failures:
            print("  - " + f)
        return 1
    print("[PASS] 动力源分支行为正确")
    return 0


if __name__ == "__main__":
    sys.exit(main())
