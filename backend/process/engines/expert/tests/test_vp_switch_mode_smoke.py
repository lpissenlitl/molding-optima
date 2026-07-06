"""
ProcessInitializer VP 切换模式 smoke test（独立运行，不依赖 Django）

覆盖：
  场景 A - 默认位置切换（mode=0）
           vps_pos = inj_pos（来自算法 #1+#2）
  场景 B - 用户指定 vps_mode int
           B1 mode=1 时间 → vps_t = inj_time × 0.95
           B2 mode=2 压力 → vps_pres = inj_pres × 0.85
           B3 mode=3 位置&时间 → 两个值都填
  场景 C - 字符串兼容（VP_switch_mode 字段）
           C1 "位置" → mode=0
           C2 "时间" → mode=1
           C3 "压力" → mode=2（显式映射）
           C4 "位置&时间" → mode=3
           C5 "其他" → mode=2（兜底）
  场景 D - 边界守门
           D1 vps_mode 越界（>=4）→ 回退到字符串/默认
           D2 mode=3 字段独立性：vps_pres 必须保持 0

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_vp_switch_mode_smoke.py
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

PASS = '\033[92m'
FAIL = '\033[91m'
NC = '\033[0m'


# ========== 辅助：构造 context fixture ==========

def _machine():
    """标准海天级注塑机"""
    return {
        'screw_diameter': 40,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': 100.0,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': 100.0,
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
        'max_thickness': 2.0,
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
    跑一次 derive()，返回 (vps_mode, vps_pos, vps_t, vps_pres, captured_log_text)。
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

    proc = params.process
    return (
        proc.vps_mode,
        proc.vps_pos,
        proc.vps_t,
        proc.vps_pres,
        buf.getvalue(),
    )


# ========== 断言辅助 ==========

_failures = []
_passes = []


def _assert_eq(actual, expected, label):
    if actual == expected:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual} == {expected}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected={expected}, actual={actual}"
        )


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


# ========== 场景 A：默认位置切换 ==========

def test_scenario_a_default_position():
    print("\n=== 场景 A: 默认位置切换（无 process_set 输入）===")
    mold = _base_mold()
    material = _base_material()

    mode, pos, t, pres, log = _run_and_capture_log(mold, material, process_set={})

    _assert_eq(mode, 0, "A1 默认 mode=0（位置切换）")
    _assert_close(pos, 10.88, "A2 vps_pos ≈ 10.88（来自 inj_pos=cushion+replenish）", eps=0.5)
    _assert_eq(t, 0, "A3 vps_t=0（位置模式不填时间）")
    _assert_eq(pres, 0, "A4 vps_pres=0（位置模式不填压力）")
    _assert_in(log, "VP 切换参数", "A5 日志输出 VP 切换参数")


# ========== 场景 B：用户指定 vps_mode int ==========

def test_scenario_b_user_int():
    print("\n=== 场景 B: 用户指定 vps_mode int（4 种模式）===")
    mold = _base_mold()
    material = _base_material()

    # B1: 时间切换 mode=1
    mode, pos, t, pres, log = _run_and_capture_log(mold, material, process_set={'vps_mode': 1})
    _assert_eq(mode, 1, "B1.1 mode=1（时间切换）")
    _assert_eq(pos, 0, "B1.2 vps_pos=0（时间模式不填位置）")
    _assert_close(t, 0.97, "B1.3 vps_t ≈ 0.97s（inj_time × 0.95 ≈ 1.07 × 0.95）", eps=0.05)
    _assert_eq(pres, 0, "B1.4 vps_pres=0（时间模式不填压力）")
    _assert_in(log, "source=explicit", "B1.5 日志 source=explicit")

    # B2: 压力切换 mode=2
    mode, pos, t, pres, log = _run_and_capture_log(mold, material, process_set={'vps_mode': 2})
    _assert_eq(mode, 2, "B2.1 mode=2（压力切换）")
    _assert_eq(pos, 0, "B2.2 vps_pos=0（压力模式不填位置）")
    _assert_eq(t, 0, "B2.3 vps_t=0（压力模式不填时间）")
    _assert_close(pres, 59.6, "B2.4 vps_pres ≈ 59.6MPa（inj_pres × 0.85）", eps=1.0)
    _assert_in(log, "source=explicit", "B2.5 日志 source=explicit")

    # B3: 位置&时间 mode=3
    mode, pos, t, pres, log = _run_and_capture_log(mold, material, process_set={'vps_mode': 3})
    _assert_eq(mode, 3, "B3.1 mode=3（位置&时间）")
    _assert_close(pos, 10.88, "B3.2 vps_pos ≈ 10.88mm（inj_pos 推导）", eps=0.5)
    _assert_close(t, 0.97, "B3.3 vps_t ≈ 0.97s（inj_time × 0.95）", eps=0.05)
    _assert_eq(pres, 0, "B3.4 vps_pres=0（位置&时间模式不填压力）")


# ========== 场景 C：字符串兼容 ==========

def test_scenario_c_string_legacy():
    print("\n=== 场景 C: 字符串兼容 VP_switch_mode 字段===")
    mold = _base_mold()
    material = _base_material()

    # C1: 位置
    mode, _, _, _, log = _run_and_capture_log(mold, material, process_set={'VP_switch_mode': '位置'})
    _assert_eq(mode, 0, "C1 \"位置\" → mode=0")
    _assert_in(log, "source=legacy_string", "C1 日志 source=legacy_string")

    # C2: 时间
    mode, _, t, _, _ = _run_and_capture_log(mold, material, process_set={'VP_switch_mode': '时间'})
    _assert_eq(mode, 1, "C2 \"时间\" → mode=1")
    _assert_close(t, 0.97, "C2 vps_t ≈ 0.97s", eps=0.05)

    # C3: 压力（新增显式映射）
    mode, _, _, pres, _ = _run_and_capture_log(mold, material, process_set={'VP_switch_mode': '压力'})
    _assert_eq(mode, 2, "C3 \"压力\" → mode=2（显式映射）")
    _assert_close(pres, 59.6, "C3 vps_pres ≈ 59.6MPa", eps=1.0)

    # C4: 位置&时间
    mode, pos, t, _, _ = _run_and_capture_log(mold, material, process_set={'VP_switch_mode': '位置&时间'})
    _assert_eq(mode, 3, "C4 \"位置&时间\" → mode=3")
    _assert_close(pos, 10.88, "C4 vps_pos ≈ 10.88mm", eps=0.5)
    _assert_close(t, 0.97, "C4 vps_t ≈ 0.97s", eps=0.05)

    # C5: 其他 → 兜底到压力
    mode, _, _, pres, _ = _run_and_capture_log(mold, material, process_set={'VP_switch_mode': '其他'})
    _assert_eq(mode, 2, "C5 \"其他\" → mode=2（兜底）")
    _assert_close(pres, 59.6, "C5 vps_pres ≈ 59.6MPa（兜底到压力）", eps=1.0)


# ========== 场景 D：边界守门 ==========

def test_scenario_d_boundary():
    print("\n=== 场景 D: 边界守门===")
    mold = _base_mold()
    material = _base_material()

    # D1: vps_mode 越界 → 回退到字符串
    mode, pos, _, _, _ = _run_and_capture_log(mold, material, process_set={'vps_mode': 5, 'VP_switch_mode': '时间'})
    _assert_eq(mode, 1, "D1.1 vps_mode=5 越界 → 回退到字符串（\"时间\"→ mode=1）")

    # D2: vps_mode 越界 + 无字符串 → 默认位置
    mode, pos, _, _, _ = _run_and_capture_log(mold, material, process_set={'vps_mode': 5})
    _assert_eq(mode, 0, "D2.1 vps_mode=5 越界 + 无字符串 → mode=0（默认）")
    _assert_close(pos, 10.88, "D2.2 vps_pos ≈ 10.88mm", eps=0.5)

    # D3: 整数优先于字符串（明确指定时优先）
    mode, pos, t, _, _ = _run_and_capture_log(mold, material, process_set={'vps_mode': 3, 'VP_switch_mode': '时间'})
    _assert_eq(mode, 3, "D3.1 vps_mode=3 优先于 VP_switch_mode='时间'")
    _assert_close(pos, 10.88, "D3.2 vps_pos ≈ 10.88mm", eps=0.5)
    _assert_close(t, 0.97, "D3.3 vps_t ≈ 0.97s", eps=0.05)


# ========== 主函数 ==========

def main():
    test_scenario_a_default_position()
    test_scenario_b_user_int()
    test_scenario_c_string_legacy()
    test_scenario_d_boundary()

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
        print(f"\n{PASS}✓ All smoke test assertions passed!{NC}")
        sys.exit(0)


if __name__ == '__main__':
    main()