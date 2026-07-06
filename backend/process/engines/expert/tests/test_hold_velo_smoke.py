"""
ProcessInitializer 保压速度 smoke test（独立运行，不依赖 Django）

覆盖：
  场景 A - PET 瓶盖厚壁（max_thickness=5mm）→ 期望 ~11 mm/s
           （PET 0.10 × thick 1.10 = 0.11, × 100 = 11.0）
  场景 B - 材料梯度（PP/ABS/PC/PET/未知）
           B1 PP thin（高流动性 + 防薄壁冻结）→ 27 mm/s
           B2 ABS medium（中位）→ 20 mm/s
           B3 PC medium（高黏度防剪切降解）→ 12 mm/s
           B4 未知 family → default_velo_ratio=0.15
  场景 C - 边界守门
           C1 机器上限钳制（ABS max_hold_velo=200, cap=60, raw=40 < cap）
           C2 PET + thin 极端组合（双重抑制）→ 9 mm/s
  场景 D - 守恒检验（v × t ≫ replenish_len）

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_hold_velo_smoke.py
"""

import io
import logging
import os
import sys

# 让 process 作为顶层 package 可被发现
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # backend/
sys.path.insert(0, BACKEND_ROOT)

from process.engines.expert.initializer import ProcessInitializer  # noqa: E402
from process.engines.expert.algorithm_engine import AlgorithmEngine  # noqa: E402
from process.engines.expert.helpers import parse_material_family  # noqa: E402

PASS = '\033[92m'
FAIL = '\033[91m'
NC = '\033[0m'


# ========== 辅助：构造 context fixture ==========

def _machine(max_hold_velo=100.0):
    """标准海天级注塑机（max_hold_velo 可调）"""
    return {
        'screw_diameter': 40,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': 100.0,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': max_hold_velo,
        'max_set_screw_rotation_speed': 150.0,
        'max_set_metering_pressure': 20.0,
        'nozzle_type': '直通型',
        'power_method': '液压机',
    }


def _base_mold(**overrides):
    """基础 ABS mold（max_thickness=2.0, medium）"""
    m = {
        'product_weight': 50.0,
        'runner_weight': 0.0,
        'ave_thickness': 2.0,
        'max_thickness': 2.0,    # 默认 medium 桶
        'max_length': 100.0,
        'gate_type': '侧浇口',
        'gate_radius': 1.5,
        'gate_length': 1.5,
        'gate_width': 5.0,
    }
    m.update(overrides)
    return m


def _base_material(**overrides):
    """基础 ABS 材料"""
    m = {
        'abbreviation': 'ABS',
        'recommended_melt_temp': 240.0,
        'recommend_shear_linear_speed': 160.0,
        'recommend_back_pressure': 15.0,
        'recommended_mold_temp': 60.0,
        'melt_density': 0.95,
    }
    m.update(overrides)
    return m


def _run_and_capture_log(mold, material, machine=None, process_set=None):
    """
    跑一次 derive()，返回 (hold_velo_sum, captured_log_text, params)。

    hold_velo_sum 用 sum() 取所有段总和（_apply_multi_holding 会拆分）。
    """
    if machine is None:
        machine = _machine()
    if process_set is None:
        process_set = {}

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    target_logger = logging.getLogger('process.engines.expert.initializer')
    target_logger.addHandler(handler)
    prev_level = target_logger.level
    target_logger.setLevel(logging.DEBUG)
    fallback_logger = logging.getLogger('engines.expert.initializer')
    fallback_logger.addHandler(handler)
    prev_level2 = fallback_logger.level
    fallback_logger.setLevel(logging.DEBUG)
    try:
        init = ProcessInitializer(
            mold_info=mold,
            machine_info=machine,
            polymer_info=material,
            process_set=process_set,
        )
        params = init.derive()
    finally:
        target_logger.removeHandler(handler)
        target_logger.setLevel(prev_level)
        fallback_logger.removeHandler(handler)
        fallback_logger.setLevel(prev_level2)

    # 多段保压拆分 [1, 0.5] 后 [v, v/2]，第 1 段 = hold_velo 原值
    hold_velo = params.process.hold_spd_steps[0] if params.process.hold_spd_steps else 0.0
    return hold_velo, buf.getvalue(), params


# ========== 断言辅助 ==========

_failures = []
_passes = []


def _assert_close(actual, expected, label, eps=0.5):
    if abs(actual - expected) <= eps:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.3f} ≈ {expected}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected≈{expected}, actual={actual:.3f}"
        )


def _assert_in(haystack, needle, label):
    if needle in haystack:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: contains '{needle}'")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: '{needle}' not in log tail\n"
            f"    --- log tail ---\n{haystack[-800:]}\n    -----------------"
        )


# ========== 场景 A：PET 瓶盖厚壁 ==========

def test_scenario_a_pet_cap_long_hold():
    print("\n=== 场景 A: PET 瓶盖厚壁（PET 0.10 × thick 1.10 → 11 mm/s）===")
    mold = _base_mold(
        max_thickness=5.0,    # thick 桶 (>3.0)
        max_length=80.0,
        gate_type='直浇口',
        runner_weight=0.0,    # 热流道
    )
    material = _base_material(
        abbreviation='PET',
        recommended_mold_temp=130.0,  # ultra_high（仅保压时间使用）
    )

    hold_velo, log, params = _run_and_capture_log(mold, material)

    # 调试：手动重算
    init_dbg = ProcessInitializer(mold_info=mold, machine_info=_machine(), polymer_info=material)
    coeffs = init_dbg.rule_matcher.match({
        'machine': _machine(), 'material': material, 'mold': mold, 'process_set': {}
    })
    init_dbg._engine = AlgorithmEngine(mold=mold, machine=_machine(), material=material, process_set={}, coeffs=coeffs)
    ch = coeffs.get('holding', {})
    fam_dbg = parse_material_family('PET')
    bucket_dbg, _ = init_dbg.engine._get_thickness_bucket(5.0, coeffs.get('injection', {}))
    fvr, lvl_dbg = init_dbg.engine._get_family_hold_velo_ratio(fam_dbg, ch)
    gfv_dbg = init_dbg.engine._get_gate_factor_for_hold_velo(bucket_dbg, ch)
    raw_dbg = 100 * fvr * gfv_dbg
    cap_dbg = 100 * ch.get('max_safe_hold_velo_ratio', 0.30)
    print(f"  [debug PET] family={fam_dbg} bucket={bucket_dbg} fvr={fvr}({lvl_dbg}) "
          f"gfv={gfv_dbg} raw={raw_dbg:.3f} cap={cap_dbg:.3f}")
    print(f"  [debug PET] hold_spd_steps={params.process.hold_spd_steps} sum={hold_velo:.3f}")

    # 理论值：100 × 0.10 (PET) × 1.10 (thick) = 11.0, cap = 30.0
    _assert_close(hold_velo, 11.0, "PET 瓶盖厚壁 raw=11.0mm/s（PET 0.10 × thick 1.10）")

    # 日志必须显示 family=PET, level=family
    _assert_in(log, "family=PET", "日志 family=PET")
    _assert_in(log, "level=family", "日志 velo level=family")
    _assert_in(log, "gate_factor_velo=1.100", "日志 gate_factor_velo=1.100 (thick)")


# ========== 场景 B：材料梯度 ==========

def test_scenario_b_material_gradient():
    print("\n=== 场景 B: 材料梯度（PP/ABS/PC/未知）===")

    # B1: PP thin 薄壁（高流动性 + 防薄壁冻结 → 偏高）
    mold = _base_mold(max_thickness=1.0)  # thin 桶
    material = _base_material(abbreviation='PP')
    hold_velo, log, _ = _run_and_capture_log(mold, material)
    # 100 × 0.30 (PP) × 0.90 (thin) = 27.0
    _assert_close(hold_velo, 27.0, "B1 PP thin 偏高补缩 raw=27.0mm/s")
    _assert_in(log, "family=PP", "B1 日志 family=PP")
    _assert_in(log, "gate_factor_velo=0.900", "B1 日志 gate_factor_velo=0.900 (thin)")

    # B2: ABS medium 中位
    mold = _base_mold(max_thickness=2.0)  # medium 桶
    material = _base_material(abbreviation='ABS')
    hold_velo, log, _ = _run_and_capture_log(mold, material)
    # 100 × 0.20 (ABS) × 1.00 (medium) = 20.0
    _assert_close(hold_velo, 20.0, "B2 ABS medium 中位 raw=20.0mm/s")
    _assert_in(log, "family=ABS", "B2 日志 family=ABS")
    _assert_in(log, "gate_factor_velo=1.000", "B2 日志 gate_factor_velo=1.000 (medium)")

    # B3: PC medium 高黏度防剪切降解
    mold = _base_mold(max_thickness=2.0)
    material = _base_material(abbreviation='PC')
    hold_velo, log, _ = _run_and_capture_log(mold, material)
    # 100 × 0.12 (PC) × 1.00 (medium) = 12.0
    _assert_close(hold_velo, 12.0, "B3 PC medium 高黏度偏低防剪切降解 raw=12.0mm/s")
    _assert_in(log, "family=PC", "B3 日志 family=PC")
    _assert_in(log, "family_velo_ratio=0.120", "B3 日志 family_velo_ratio=0.120 (PC)")

    # B4: 未知 family 兜底
    mold = _base_mold(max_thickness=2.0)
    material = _base_material(abbreviation='UNKNOWN_MATERIAL_XYZ')
    hold_velo, log, _ = _run_and_capture_log(mold, material)
    # 100 × 0.15 (default) × 1.00 (medium) = 15.0
    _assert_close(hold_velo, 15.0, "B4 未知 family → default_velo_ratio=0.15 raw=15.0mm/s")
    _assert_in(log, "level=default", "B4 日志 velo level=default")


# ========== 场景 C：边界守门 ==========

def test_scenario_c_boundary_guards():
    print("\n=== 场景 C: 边界守门（机器钳制 + 极端组合）===")

    # C1: 机器上限钳制（ABS max_hold_velo=200, raw=40, cap=60，未触发钳制）
    mold = _base_mold(max_thickness=2.0)
    material = _base_material(abbreviation='ABS')
    machine = _machine(max_hold_velo=200.0)
    hold_velo, log, _ = _run_and_capture_log(mold, material, machine=machine)
    # 200 × 0.20 (ABS) × 1.00 (medium) = 40.0, cap = 200 × 0.30 = 60.0
    # 40 < 60，未触发钳制，最终 = 40
    _assert_close(hold_velo, 40.0, "C1 ABS max_hold_velo=200 raw=40mm/s < cap=60mm/s, 未触发钳制")
    _assert_in(log, "cap 60.00mm/s", "C1 日志 cap=60.00mm/s")

    # C2: PET + thin 极端组合（双重抑制）
    mold = _base_mold(max_thickness=1.0)  # thin 桶
    material = _base_material(abbreviation='PET')
    hold_velo, log, _ = _run_and_capture_log(mold, material)
    # 100 × 0.10 (PET) × 0.90 (thin) = 9.0
    _assert_close(hold_velo, 9.0, "C2 PET+thin 极端组合（双重抑制）raw=9.0mm/s")
    _assert_in(log, "family=PET", "C2 日志 family=PET")
    _assert_in(log, "gate_factor_velo=0.900", "C2 日志 gate_factor_velo=0.900 (thin)")


# ========== 场景 D：守恒检验（v × t ≫ replenish_len） ==========

def test_scenario_d_conservation_check():
    print("\n=== 场景 D: 守恒检验（PET 瓶盖场景，v × t ≫ replenish_len）===")
    mold = _base_mold(
        max_thickness=5.0,
        max_length=80.0,
        gate_type='直浇口',
        runner_weight=0.0,
    )
    material = _base_material(
        abbreviation='PET',
        recommended_mold_temp=130.0,
    )

    hold_velo, log, params = _run_and_capture_log(mold, material)
    # 守恒检验用 sum（多段累积），保压时间 coefs=[0.5, 0.5]，sum = hold_time 原值
    hold_spd_total = sum(params.process.hold_spd_steps) if params.process.hold_spd_steps else 0.0
    hold_time_total = sum(params.process.hold_time_steps) if params.process.hold_time_steps else 0.0

    # replenish_len 估算（从注射参数：shrink_rate + pvt_compress ≈ 0.020 + 0.015 = 0.035,
    # product_weight=50g, melt_density=0.95, screw_diameter=40mm）
    # replenish_len ≈ 0.035 × 50 / 0.95 / (π × 40² / 4) × 1000 ≈ 1.5~3 mm
    # 保守估算：replenish_len ≈ 3 mm
    # 守恒：v × t = 11.0 × 295 ≈ 3245 mm >> 3 mm ✓
    estimated_replenish_len = 3.0  # mm
    vt_product = hold_spd_total * hold_time_total
    print(f"  [debug conservation] hold_spd_total={hold_spd_total:.3f}mm/s × hold_time={hold_time_total:.3f}s "
          f"= {vt_product:.2f}mm, estimated replenish_len ≈ {estimated_replenish_len:.1f}mm")
    if vt_product > 10 * estimated_replenish_len:
        _passes.append(
            f"  {PASS}[PASS]{NC} 守恒检验: v×t={vt_product:.2f}mm ≫ replenish_len≈{estimated_replenish_len:.1f}mm "
            f"(比值 {vt_product / estimated_replenish_len:.0f}x)"
        )
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} 守恒检验失败: v×t={vt_product:.2f}mm 不满足 ≫ replenish_len≈{estimated_replenish_len:.1f}mm"
        )


# ========== 主入口 ==========

def main():
    test_scenario_a_pet_cap_long_hold()
    test_scenario_b_material_gradient()
    test_scenario_c_boundary_guards()
    test_scenario_d_conservation_check()

    print("\n" + "=" * 70)
    print("保压速度 smoke test 汇总")
    print("=" * 70)
    for p in _passes:
        print(p)
    for f in _failures:
        print(f)
    print("-" * 70)
    print(f"通过: {len(_passes)}    失败: {len(_failures)}")
    print("=" * 70)

    sys.exit(0 if len(_failures) == 0 else 1)


if __name__ == "__main__":
    main()