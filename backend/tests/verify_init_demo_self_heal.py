"""
verify_init_demo_self_heal.py
验证 init_demo 的「自动识别并更新」能力：存量残缺数据能被自动补齐。

模拟两种历史遗留状态：
    场景 A：射台存在但字段残缺（早期 init_demo 只填 6 个基础字段）
    场景 B：射台完全缺失（早期 init_demo 跳过射台生成）

预期：再跑一次 init_demo 后，两种情况都被自动补齐，且不覆盖人工维护的已有值。
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from django.core.management import call_command
from masterdata.models import InjectionMoldingMachine, InjectionUnit

DEVICE_NO = "IMM-DEMO-001"
UNIT_CODE = "IMM-DEMO-001-U1"


def main():
    print("=" * 70)
    print("init_demo 自愈能力验证（自动识别并更新）")
    print("=" * 70)

    failures = []

    # ---------- 场景 A：字段残缺 ----------
    print("\n[场景 A] 射台存在但字段残缺")
    unit = InjectionUnit.objects.get(unit_code=UNIT_CODE)
    # 人工维护值：应当被保留，不被覆盖
    unit.max_set_injection_pressure = 123.0
    unit.update_info(
        max_set_injection_pressure=123.0,
        max_set_injection_speed=None,
        max_set_holding_pressure=None,
        max_set_screw_rotation_speed=None,
        max_injection_pressure=None,
        screw_cross_sectional_area=None,
    )
    print("  置空：max_set_injection_speed / max_set_holding_pressure / "
          "max_set_screw_rotation_speed / max_injection_pressure / screw_cross_sectional_area")
    print("  人工值：max_set_injection_pressure=123.0（应保留）")

    call_command("init_demo", verbosity=0)

    unit.refresh_from_db()
    for field, expect in (
        ("max_set_injection_speed", 90.0),
        ("max_set_holding_pressure", 140.0),
        ("max_set_screw_rotation_speed", 130.0),
        ("max_injection_pressure", 160.0),
        ("screw_cross_sectional_area", 1017.88),
    ):
        actual = getattr(unit, field)
        if actual != expect:
            failures.append(f"场景A {field}: 期望 {expect}，实际 {actual}")
            print(f"  [FAIL] {field}: 期望 {expect}，实际 {actual}")
        else:
            print(f"  [OK] {field} 已自动补齐 = {actual}")

    if unit.max_set_injection_pressure != 123.0:
        failures.append(
            f"场景A 人工值被覆盖: max_set_injection_pressure="
            f"{unit.max_set_injection_pressure}（应为 123.0）"
        )
        print("  [FAIL] 人工维护值被覆盖")
    else:
        print("  [OK] 人工维护值 max_set_injection_pressure=123.0 未被覆盖")

    # ---------- 场景 B：射台缺失 ----------
    print("\n[场景 B] 射台完全缺失")
    machine = InjectionMoldingMachine.objects.get(device_no=DEVICE_NO)
    deleted = InjectionUnit.objects.filter(machine=machine, unit_code=UNIT_CODE).delete()
    print(f"  已删除射台 {UNIT_CODE}（{deleted} 条）")
    assert not InjectionUnit.objects.filter(unit_code=UNIT_CODE).exists()

    call_command("init_demo", verbosity=0)

    if not InjectionUnit.objects.filter(unit_code=UNIT_CODE).exists():
        failures.append("场景B 射台未自动重建")
        print("  [FAIL] 射台未自动重建")
    else:
        unit2 = InjectionUnit.objects.get(unit_code=UNIT_CODE)
        print(f"  [OK] 射台已自动重建（Φ{unit2.screw_diameter}）")
        for field, expect in (
            ("max_set_injection_pressure", 140.0),
            ("max_set_injection_speed", 90.0),
            ("max_set_holding_pressure", 140.0),
            ("max_set_holding_speed", 45.0),
            ("max_set_screw_rotation_speed", 130.0),
            ("max_set_metering_pressure", 10.0),
            ("max_set_metering_back_pressure", 8.0),
            ("max_set_decompression_pressure", 12.0),
        ):
            actual = getattr(unit2, field)
            if actual != expect:
                failures.append(f"场景B {field}: 期望 {expect}，实际 {actual}")
                print(f"  [FAIL] {field}: 期望 {expect}，实际 {actual}")
            else:
                print(f"  [OK] {field} = {actual}")

    # ---------- 恢复现场（把人工值改回 demo 标准值）----------
    InjectionUnit.objects.filter(unit_code=UNIT_CODE).update(
        max_set_injection_pressure=140.0,
    )
    call_command("init_demo", verbosity=0)

    print("\n" + "=" * 70)
    if failures:
        print(f"[FAIL] 共 {len(failures)} 项：")
        for f in failures:
            print("  - " + f)
        return 1
    print("[PASS] 自愈能力验证通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
