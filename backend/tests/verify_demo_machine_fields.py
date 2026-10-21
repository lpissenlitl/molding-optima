"""
verify_demo_machine_fields.py
验证 init_demo 生成的注塑机/射台数据能通过两套算法入参契约的校验。

背景（2026-10-20）：
    init_demo 早期只给 InjectionUnit 填了 6 个基础字段（喷嘴/螺杆/直径/行程/
    射胶量/塑化量），缺 max_set_*（HMI 可设定上限），
    导致工艺推理（expert）与调优（fuzzy）的入参校验直接拦截，报错形如：
        machine_info.max_set_injection_pressure (最大可设定注射压力 [MPa]（HMI）)
        ... 共 8 项

本脚本：
    1. 从库里读出全部 demo 注塑机及其射台
    2. 按 expert 契约（MACHINE_INFO_FIELDS）提取 machine_info 并核查必填完整性
    3. 按 fuzzy 契约（OPTIMIZE_MACHINE_INFO_FIELDS）提取 machine_info 并跑
       OptimizeDataValidator（含真实 polymer / mold 上下文）
    4. 额外校验数据自洽性：HMI 可设定上限 ≤ 设备极限
    5. 端到端：跑一遍真实的工艺参数推理（infer），验证不再被入参校验拦截
       （推理会写库，这里包在事务里回滚，不留脏数据）

用法：
    cd backend
    ..\\.venv\\Scripts\\python.exe tests\\verify_demo_machine_fields.py
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from masterdata.models import InjectionMoldingMachine, Mold, Polymer
from process.algorithms.expert.specs import MACHINE_INFO_FIELDS
from process.algorithms.field_contract import (
    audit_field_completeness,
    drive_system_to_power_method,
)
from process.algorithms.fuzzy.specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OptimizeDataValidator,
)
from process.services.parameter_initialize import ParameterInitializeService

# 设备极限 → HMI 可设定上限 的对应关系（用于校验 demo 数据是否自洽）
_LIMIT_PAIRS = (
    ("max_injection_pressure", "max_set_injection_pressure"),
    ("max_injection_speed", "max_set_injection_speed"),
    ("max_holding_pressure", "max_set_holding_pressure"),
    ("max_holding_speed", "max_set_holding_speed"),
    ("max_screw_rotation_speed", "max_set_screw_rotation_speed"),
    ("max_metering_pressure", "max_set_metering_pressure"),
    ("max_metering_back_pressure", "max_set_metering_back_pressure"),
    ("max_decompression_pressure", "max_set_decompression_pressure"),
    ("max_decompression_speed", "max_set_decompression_speed"),
)


def _extract_by_spec(spec, machine, unit):
    """按 spec 的 (source_model, attr_name) 从 ORM 提取扁平 dict"""
    result = {}
    for target_key, field_spec in spec.items():
        attr_name = field_spec.get("attr_name")
        if not attr_name:
            continue
        source = machine if field_spec.get("source_model") == "InjectionMoldingMachine" else unit
        result[target_key] = getattr(source, attr_name, None)
    return result


def main():
    print("=" * 70)
    print("init_demo 射台字段完整性验证（expert 契约 + fuzzy 契约）")
    print("=" * 70)

    machines = list(
        InjectionMoldingMachine.objects.filter(
            device_no__startswith="IMM-DEMO",
        ).prefetch_related("injection_units").order_by("device_no")
    )
    assert machines, "库里没有 demo 注塑机，请先执行 python manage.py init_demo"

    polymer = Polymer.objects.filter(abbreviation="PP").first()
    mold = Mold.objects.filter(mold_no__startswith="MOLD-DEMO").first()
    assert polymer is not None, "找不到 demo 材料 PP"
    assert mold is not None, "找不到 demo 模具"

    polymer_info = {
        "abbreviation": polymer.abbreviation,
        "min_melt_temp": polymer.min_melt_temp,
        "max_melt_temp": polymer.max_melt_temp,
        "recommended_melt_temp": polymer.recommended_melt_temp,
        "min_mold_temp": polymer.min_mold_temp,
        "max_mold_temp": polymer.max_mold_temp,
        "recommended_mold_temp": polymer.recommended_mold_temp,
    }
    mold_info = {
        "product_category": mold.product_category,
        "target_cycle_time": mold.target_cycle_time,
    }

    failures = []
    total_units = 0

    for machine in machines:
        is_hydraulic = drive_system_to_power_method(machine.drive_system) == "液压机"
        kind = "液压机" if is_hydraulic else "电动机"
        print(f"\n- {machine.device_no} ({machine.brand} {machine.model}) "
              f"drive_system={machine.drive_system} → {kind}")

        for unit in machine.injection_units.all().order_by("unit_code"):
            total_units += 1
            print(f"    · {unit.unit_code} (Φ{unit.screw_diameter})")

            # ---- 1. expert 契约（工艺推理 initialize）----
            expert_info = _extract_by_spec(MACHINE_INFO_FIELDS, machine, unit)
            missing = audit_field_completeness(
                expert_info, MACHINE_INFO_FIELDS, "machine_info",
                is_hydraulic=is_hydraulic,
            )
            if missing:
                failures.append(
                    f"[expert] {machine.device_no}/{unit.unit_code} 缺失: " + "；".join(missing)
                )
                print(f"        [FAIL] expert 缺失 {len(missing)} 项")
            else:
                print("        [OK] expert 契约必填字段齐全")

            # ---- 2. fuzzy 契约（调优 optimize）----
            fuzzy_info = _extract_by_spec(
                OPTIMIZE_MACHINE_INFO_FIELDS, machine, unit
            )
            try:
                OptimizeDataValidator.validate(fuzzy_info, polymer_info, mold_info)
                print("        [OK] fuzzy 契约校验通过")
            except ValueError as e:
                failures.append(
                    f"[fuzzy] {machine.device_no}/{unit.unit_code}: {e}"
                )
                print(f"        [FAIL] fuzzy 校验未通过: {e}")

            # ---- 3. 数据自洽性：HMI 可设定上限 ≤ 设备极限 ----
            for limit_key, set_key in _LIMIT_PAIRS:
                limit_val = getattr(unit, limit_key, None)
                set_val = getattr(unit, set_key, None)
                if limit_val is None or set_val is None:
                    continue
                if set_val > limit_val:
                    msg = (f"{machine.device_no}/{unit.unit_code} {set_key}={set_val} "
                           f"> 设备极限 {limit_key}={limit_val}")
                    failures.append(f"[自洽] {msg}")
                    print(f"        [FAIL] {msg}")

    print("\n" + "=" * 70)
    print(f"共检查 {len(machines)} 台注塑机 / {total_units} 个射台")

    # ---- 4. 端到端：真实跑一遍工艺参数推理（写库后回滚）----
    print("\n" + "=" * 70)
    print("端到端：工艺参数推理（ParameterInitializeService.infer）")
    print("=" * 70)
    e2e_failures = _verify_end_to_end(mold, polymer, machines)
    failures.extend(e2e_failures)

    if failures:
        print(f"\n[FAIL] 共 {len(failures)} 项问题：")
        for f in failures:
            print("  - " + f)
        return 1
    print("\n[PASS] 全部 demo 射台字段齐全，自洽性校验通过")
    return 0


def _verify_end_to_end(mold, polymer, machines):
    """端到端推理验证（事务内跑 + 回滚，不留脏数据）"""
    from django.db import transaction

    failures = []
    for machine in machines:
        unit_count = machine.injection_units.count()
        for injection_index in range(unit_count):
            try:
                with transaction.atomic():
                    result = ParameterInitializeService.infer(
                        mold_id=mold.id,
                        injection_machine_id=machine.id,
                        polymer_id=polymer.id,
                        shot_index=0,
                        injection_index=injection_index,
                    )
                    transaction.set_rollback(True)
                print(f"  [OK] {machine.device_no} 射台#{injection_index + 1} "
                      f"推理成功（condition_id={result.get('condition_id')}）")
            except Exception as e:
                failures.append(f"[e2e] {machine.device_no} 射台#{injection_index + 1}: {e}")
                print(f"  [FAIL] {machine.device_no} 射台#{injection_index + 1}: {e}")
    return failures


if __name__ == "__main__":
    sys.exit(main())
