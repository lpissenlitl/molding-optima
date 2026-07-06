"""
ProcessInitializer 注射时间 smoke test（独立运行，不依赖 Django）

覆盖（#5 算法方向 A 重构 v2：自包含 family 填充效率驱动）：
  场景 A - PP 薄壁（基准 fill_efficiency=0.85）
  场景 B - PC 薄壁（fill_efficiency=0.40 高黏度）
  场景 C - PP 厚壁（钳制上限触发）
  场景 D - PA 高黏度（fill_efficiency 最低 0.35）
  场景 E - 未知 family（兜底 default_fill_efficiency=0.60）
  场景 F - 自包含验证（不依赖 #4 inj_velo）
  场景 G - 边界守门
  场景 H - family 差异化对比

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_inj_time_smoke.py
"""

import io
import logging
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, BACKEND_ROOT)

from process.engines.expert.initializer import ProcessInitializer

PASS = '\033[92m'
FAIL = '\033[91m'
NC = '\033[0m'


def _machine(max_velo=100.0):
    return {
        'screw_diameter': 40,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': max_velo,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': 100.0,
        'max_set_screw_rotation_speed': 150.0,
        'max_set_metering_pressure': 20.0,
        'nozzle_type': '直通型',
        'power_method': '液压机',
    }


def _mold(product_weight=50.0, max_thickness=2.0, ave_thickness=2.0, max_length=100.0, **overrides):
    m = {
        'product_weight': product_weight,
        'runner_weight': 0.0,
        'ave_thickness': ave_thickness,
        'max_thickness': max_thickness,
        'max_length': max_length,
        'gate_type': '侧浇口',
        'gate_radius': 1.5,
        'gate_length': 1.5,
        'gate_width': 5.0,
    }
    m.update(overrides)
    return m


def _material(abbrev='ABS', melt_temp=240.0, **overrides):
    m = {
        'abbreviation': abbrev,
        'recommended_melt_temp': melt_temp,
        'recommend_shear_linear_speed': 160.0,
        'recommend_back_pressure': 10.0,
        'recommended_mold_temp': 60.0,
        'melt_density': 0.95,
    }
    m.update(overrides)
    return m


def _run_and_capture_log(mold, material, machine=None, process_set=None):
    if machine is None:
        machine = _machine()
    if process_set is None:
        process_set = {}

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    for name in ['process.engines.expert.initializer', 'engines.expert.initializer']:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        prev_level = lg.level
        lg.setLevel(logging.DEBUG)
    try:
        init = ProcessInitializer(mold_info=mold, machine_info=machine, polymer_info=material, process_set=process_set)
        params = init.derive()
    finally:
        for name in ['process.engines.expert.initializer', 'engines.expert.initializer']:
            lg = logging.getLogger(name)
            lg.removeHandler(handler)

    proc = params.process
    return (
        proc.inj_t,
        proc.inj_pos_steps[0] if proc.inj_pos_steps else 0.0,
        buf.getvalue(),
    )


_failures = []
_passes = []


def _assert_close(actual, expected, label, eps=0.05):
    if abs(actual - expected) <= eps:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.3f} ≈ {expected}")
    else:
        _failures.append(f"  {FAIL}[FAIL]{NC} {label}: expected≈{expected}, actual={actual:.3f}")


def _assert_ge(actual, threshold, label):
    if actual >= threshold - 0.001:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.3f} ≥ {threshold}")
    else:
        _failures.append(f"  {FAIL}[FAIL]{NC} {label}: expected≥{threshold}, actual={actual:.3f}")


def _assert_le(actual, threshold, label):
    if actual <= threshold + 0.001:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.3f} ≤ {threshold}")
    else:
        _failures.append(f"  {FAIL}[FAIL]{NC} {label}: expected≤{threshold}, actual={actual:.3f}")


def _assert_in(haystack, needle, label):
    if needle in haystack:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: contains '{needle}'")
    else:
        _failures.append(f"  {FAIL}[FAIL]{NC} {label}: '{needle}' not in log")


def test_scenario_a_pp_thin():
    print("\n=== 场景 A: PP 薄壁（基准 fill_efficiency=0.85）===")
    mold = _mold(max_thickness=1.0, ave_thickness=1.0)
    material = _material(abbrev='PP', melt_temp=220.0)

    inj_t, _, log = _run_and_capture_log(mold, material)

    _assert_close(inj_t, 0.6, "A1 PP薄壁 inj_t ≈ 0.6s（钳制到 PP-thin min_t）", eps=0.05)
    _assert_in(log, "fill_efficiency=0.850", "A2 日志 fill_efficiency=0.850")
    _assert_in(log, "fill_level=family", "A3 日志 fill_level=family")
    _assert_in(log, "equivalent_velo=85.00mm/s", "A4 日志 equivalent_velo=85.00mm/s")
    _assert_in(log, "bucket=thin", "A5 日志 bucket=thin")


def test_scenario_b_pc_thin():
    print("\n=== 场景 B: PC 薄壁（fill_efficiency=0.40）===")
    mold = _mold(max_thickness=1.0, ave_thickness=1.0)
    material = _material(abbrev='PC', melt_temp=290.0)

    inj_t, _, log = _run_and_capture_log(mold, material)

    _assert_close(inj_t, 1.025, "B1 PC薄壁 inj_t ≈ 1.025s（inj_time_geo 命中窗口）", eps=0.05)
    _assert_in(log, "fill_efficiency=0.400", "B2 日志 fill_efficiency=0.400")
    _assert_in(log, "equivalent_velo=40.00mm/s", "B3 日志 equivalent_velo=40.00mm/s")


def test_scenario_c_pp_thick():
    print("\n=== 场景 C: PP 厚壁（钳制上限触发）===")
    mold = _mold(max_thickness=4.0, ave_thickness=4.0)
    material = _material(abbrev='PP', melt_temp=220.0)

    inj_t, _, log = _run_and_capture_log(mold, material)

    _assert_close(inj_t, 1.2, "C1 PP厚壁 inj_t ≈ 1.2s（钳制到 PP-thick min_t）", eps=0.05)
    _assert_in(log, "fill_efficiency=0.850", "C2 日志 fill_efficiency=0.850")
    _assert_in(log, "bucket=thick", "C3 日志 bucket=thick")


def test_scenario_d_pa_medium():
    print("\n=== 场景 D: PA 中壁（fill_efficiency=0.35 最低）===")
    mold = _mold(max_thickness=2.0, ave_thickness=2.0)
    material = _material(abbrev='PA66', melt_temp=280.0)

    inj_t, _, log = _run_and_capture_log(mold, material)

    _assert_close(inj_t, 1.152, "D1 PA中壁 inj_t ≈ 1.152s", eps=0.05)
    _assert_in(log, "fill_efficiency=0.350", "D2 日志 fill_efficiency=0.350（PA 最低）")
    _assert_in(log, "equivalent_velo=35.00mm/s", "D3 日志 equivalent_velo=35.00mm/s")


def test_scenario_e_unknown_family():
    print("\n=== 场景 E: 未知 family（兜底 default_fill_efficiency=0.60）===")
    mold = _mold(max_thickness=2.0, ave_thickness=2.0)
    material = _material(abbrev='XXX_UNKNOWN', melt_temp=240.0)

    inj_t, _, log = _run_and_capture_log(mold, material)

    _assert_close(inj_t, 0.667, "E1 未知family inj_t ≈ 0.667s", eps=0.05)
    _assert_in(log, "fill_efficiency=0.600", "E2 日志 fill_efficiency=0.600（默认）")
    _assert_in(log, "fill_level=default", "E3 日志 fill_level=default")
    _assert_in(log, "family=unknown", "E4 日志 family=unknown")


def test_scenario_f_self_contained():
    print("\n=== 场景 F: 自包含验证（#5 等效速度由 max_velo×fill_efficiency 决定）===")
    mold = _mold(max_thickness=2.0, ave_thickness=2.0)
    material = _material(abbrev='PP', melt_temp=220.0)

    _, _, log_100 = _run_and_capture_log(mold, material, machine=_machine(max_velo=100.0))
    _assert_in(log_100, "equivalent_velo=85.00mm/s", "F1 max_velo=100 → equivalent_velo=85.00")
    _assert_in(log_100, "inj_time_geo=0.475s", "F2 max_velo=100 → inj_time_geo=0.475s")

    _, _, log_200 = _run_and_capture_log(mold, material, machine=_machine(max_velo=200.0))
    _assert_in(log_200, "equivalent_velo=170.00mm/s", "F3 max_velo=200 → equivalent_velo=170.00")
    _assert_in(log_200, "inj_time_geo=0.238s", "F4 max_velo=200 → inj_time_geo=0.238s（反比变化）")


def test_scenario_g_boundary():
    print("\n=== 场景 G: 边界守门===")

    # G1: max_inj_velo=0 → 退化到 min_t
    mold = _mold(max_thickness=2.0, ave_thickness=2.0)
    material = _material(abbrev='ABS', melt_temp=240.0)
    inj_t, _, log = _run_and_capture_log(mold, material, machine=_machine(max_velo=0.0))
    _assert_close(inj_t, 0.6, "G1 max_velo=0 退化到 ABS-medium min_t=0.6s", eps=0.05)
    _assert_in(log, "equivalent_velo=0.00mm/s", "G2 日志 equivalent_velo=0.00mm/s（除零保护）")

    # G3: 默认 family_fill_efficiency 缺失 → 兜底 0.60
    mold = _mold(max_thickness=2.0, ave_thickness=2.0)
    material = _material(abbrev='UNKNOWN_X', melt_temp=240.0)
    _, _, log = _run_and_capture_log(mold, material)
    _assert_in(log, "fill_level=default", "G3 未识别 family → fill_level=default")

    # G4: product_weight 极大 → inj_len 极大 → 钳到 max_t
    mold_huge = _mold(product_weight=2000.0, max_thickness=2.0, ave_thickness=2.0)
    material = _material(abbrev='PP', melt_temp=220.0)
    inj_t, _, _ = _run_and_capture_log(mold_huge, material)
    _assert_le(inj_t, 2.5, "G4 PP超重件（2000g）→ inj_t ≤ 2.5s（钳到 max_t）")

    # G5: product_weight 极小 → 钳到 min_t
    mold_tiny = _mold(product_weight=0.5, max_thickness=2.0, ave_thickness=2.0)
    material = _material(abbrev='PP', melt_temp=220.0)
    inj_t, _, _ = _run_and_capture_log(mold_tiny, material)
    _assert_ge(inj_t, 0.8, "G5 PP超轻件（0.5g）→ inj_t ≥ 0.8s（钳到 min_t）")


def test_scenario_h_family_diff():
    print("\n=== 场景 H: family 差异化对比===")
    mold = _mold(max_thickness=2.0, ave_thickness=2.0)

    _, _, log_pp = _run_and_capture_log(mold, _material(abbrev='PP', melt_temp=220.0))
    _assert_in(log_pp, "fill_efficiency=0.850", "H1 PP fill_efficiency=0.850（高流动性）")

    _, _, log_pc = _run_and_capture_log(mold, _material(abbrev='PC', melt_temp=290.0))
    _assert_in(log_pc, "fill_efficiency=0.400", "H2 PC fill_efficiency=0.400（高黏度）")

    _, _, log_pvc = _run_and_capture_log(mold, _material(abbrev='PVC', melt_temp=180.0))
    _assert_in(log_pvc, "fill_efficiency=0.300", "H3 PVC fill_efficiency=0.300（极易分解，最慢）")


def main():
    test_scenario_a_pp_thin()
    test_scenario_b_pc_thin()
    test_scenario_c_pp_thick()
    test_scenario_d_pa_medium()
    test_scenario_e_unknown_family()
    test_scenario_f_self_contained()
    test_scenario_g_boundary()
    test_scenario_h_family_diff()

    print("\n" + "=" * 60)
    print(f"  Total: {len(_passes) + len(_failures)} assertions")
    print(f"  {PASS}PASS{NC}: {len(_passes)}")
    print(f"  {FAIL}FAIL{NC}: {len(_failures)}")
    print("=" * 60)

    if _failures:
        print("\n--- Failures ---")
        for f in _failures:
            print(f)
        sys.exit(1)
    else:
        print(f"\n{PASS}[OK] All smoke test assertions passed!{NC}")
        sys.exit(0)


if __name__ == '__main__':
    main()