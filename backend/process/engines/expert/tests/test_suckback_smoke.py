"""
ProcessInitializer 松退参数族（#15-#18）smoke test（v1.1，独立运行，不依赖 Django）

覆盖范围（设计文档 §7）：
  场景 A - PP 通用件（液压+直通+冷流道+侧浇口）→ P=3.32, D=3.32, V=50.0
  场景 B - PA66 含水件（液压+直通+冷流道+侧浇口）→ P=4.32, D=2.16, V=42.5
  场景 C - PC 精密件（液压+直通+冷流道+侧浇口）→ P=3.66, D=2.66, V=37.5
  场景 D - PVC 低黏度（液压+直通+冷流道+侧浇口）→ P=1.66, D=3.99, V=50.0
  场景 E - ABS 锁闭喷嘴（液压+锁闭+冷流道+侧浇口）→ P=3.85, D=3.85, V=40.0
  场景 F - 全电机 ABS 直通 → P=0（全电机）, D=3.32, V=20.0
  场景 G - ABS 热流道+侧浇口 → D=6.16（runner_factor=1.60 生效）
  场景 H - ABS 热流道+点浇口 → D=8.01（gate_factor=1.30 生效）
  场景 I - 🔴 switch 手柄（ABS+锁闭+热流道+针阀式点浇口）→ D=10.47（业内实测 10mm）
  场景 J - 边界钳上限（max_set=100）→ P 钳到 5.0
  场景 K - 边界钳下限（max_set=2）→ P 钳到 1.0
  场景 L - 冷流道场景下 gate_factor 不叠加（gate_factor=1.00）
  场景 M - #18 met_end_pos 公式透明（met_pos + pst_dist）

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_suckback_smoke.py
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

def _machine(power_method='液压机', nozzle_type='直通型', max_metering_pres=14.0,
             max_decomp_velo=50.0):
    """标准海天级注塑机（液压+直通+max_meter=14MPa, max_decomp_velo=50mm/s）"""
    return {
        'screw_diameter': 40,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': 100.0,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': 100.0,
        'max_set_screw_rotation_speed': 150.0,
        'max_set_metering_pressure': max_metering_pres,
        'max_set_decompression_velocity': max_decomp_velo,
        'nozzle_type': nozzle_type,
        'power_method': power_method,
    }


def _base_mold(runner_type='冷流道', runner_weight=30.0, gate_type='侧浇口', **overrides):
    """基础 mold：冷流道 + 侧浇口"""
    m = {
        'product_weight': 50.0,
        'runner_weight': runner_weight,
        'runner_type': runner_type,
        'ave_thickness': 2.0,
        'max_thickness': 3.0,
        'max_length': 100.0,
        'gate_type': gate_type,
        'gate_radius': 1.5,
        'gate_length': 1.5,
        'gate_width': 5.0,
    }
    m.update(overrides)
    return m


def _base_material(abbreviation='ABS', **overrides):
    """基础材料：ABS"""
    m = {
        'abbreviation': abbreviation,
        'category': '无定形',
        'recommended_melt_temp': 240.0,
        'recommended_mold_temp': 60.0,
        'ejection_temp': 90.0,
        'recommend_shear_linear_speed': 160.0,
        'recommend_back_pressure': 15.0,
        'melt_density': 0.95,
    }
    m.update(overrides)
    return m


def _run(mold, material, machine=None, process_set=None):
    """跑一次 derive()，返回 ProcessParams"""
    if machine is None:
        machine = _machine()
    if process_set is None:
        process_set = {}

    init = ProcessInitializer(
        mold_info=mold,
        machine_info=machine,
        polymer_info=material,
        process_set=process_set,
    )
    return init.derive()


# ========== 断言辅助 ==========

_failures = []
_passes = []


def _assert_close(actual, expected, label, eps=0.05):
    if abs(actual - expected) <= eps:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.3f} ≈ {expected}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected≈{expected}, actual={actual:.3f}"
        )


def _assert_ge(actual, min_val, label):
    if actual >= min_val:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.2f} >= {min_val}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected>={min_val}, actual={actual:.2f}"
        )


def _assert_le(actual, max_val, label):
    if actual <= max_val:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.2f} <= {max_val}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected<={max_val}, actual={actual:.2f}"
        )


def _assert_eq(actual, expected, label):
    if actual == expected:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual} == {expected}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected={expected}, actual={actual}"
        )


# ========== 场景 A：PP 通用件（液压+直通+冷流道+侧浇口）==========
# P=14×0.25×1.00×1.00×0.95 = 3.32, D=3.5×1.00×0.95×1.00×1.00 = 3.32, V=50×1.00×1.00 = 50
def test_a_pp():
    print("\n[场景 A] PP 通用件（液压+直通+冷流道+侧浇口）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='PP'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 3.32, 'P')
    _assert_close(proc.pst_met_decomp_dist, 3.32, 'D')
    _assert_close(proc.pst_met_decomp_spd, 50.0, 'V')
    _assert_ge(proc.pst_met_decomp_t, 0.06, 'T (≥min_time)')


# ========== 场景 B：PA66 含水件（液压+直通+冷流道+侧浇口）==========
# family=PA66, family_dist_factor=0.65, family_pres_factor=1.30
# P=14×0.25×1.30×1.00×0.95 = 4.32, D=3.5×0.65×0.95×1.00×1.00 = 2.16, V=50×0.85×1.00 = 42.5
def test_b_pa66():
    print("\n[场景 B] PA66 含水件（液压+直通+冷流道+侧浇口）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='PA66'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 4.32, 'P')
    _assert_close(proc.pst_met_decomp_dist, 2.16, 'D')
    _assert_close(proc.pst_met_decomp_spd, 42.5, 'V')


# ========== 场景 C：PC 精密件（液压+直通+冷流道+侧浇口）==========
# family=PC, family_dist_factor=0.80, family_pres_factor=1.10
# P=14×0.25×1.10×1.00×0.95 = 3.66, D=3.5×0.80×0.95×1.00×1.00 = 2.66, V=50×0.75×1.00 = 37.5
def test_c_pc():
    print("\n[场景 C] PC 精密件（液压+直通+冷流道+侧浇口）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='PC'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 3.66, 'P')
    _assert_close(proc.pst_met_decomp_dist, 2.66, 'D')
    _assert_close(proc.pst_met_decomp_spd, 37.5, 'V')


# ========== 场景 D：PVC 低黏度（液压+直通+冷流道+侧浇口）==========
# family=PVC, family_dist_factor=1.20, family_pres_factor=0.50
# P=14×0.25×0.50×1.00×0.95 = 1.66, D=3.5×1.20×0.95×1.00×1.00 = 3.99, V=50×1.10×1.00 = 55→钳50
def test_d_pvc():
    print("\n[场景 D] PVC 低黏度（液压+直通+冷流道+侧浇口）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='PVC'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 1.66, 'P')
    _assert_close(proc.pst_met_decomp_dist, 3.99, 'D')
    _assert_close(proc.pst_met_decomp_spd, 50.0, 'V (钳上限)')


# ========== 场景 E：ABS 锁闭喷嘴（液压+锁闭+冷流道+侧浇口）==========
# nozzle_locked: pres_factor=1.10, dist_factor=1.10, velo_factor=0.80
# P=14×0.25×1.00×1.00×1.10 = 3.85, D=3.5×1.00×1.10×1.00×1.00 = 3.85, V=50×1.00×0.80 = 40
def test_e_abs_locked():
    print("\n[场景 E] ABS 锁闭喷嘴（液压+锁闭+冷流道+侧浇口）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='ABS'),
        machine=_machine(nozzle_type='锁闭型'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 3.85, 'P')
    _assert_close(proc.pst_met_decomp_dist, 3.85, 'D')
    _assert_close(proc.pst_met_decomp_spd, 40.0, 'V')


# ========== 场景 F：全电机 ABS 直通（冷流道+侧浇口）==========
# P=0（全电机）, D=3.32, V=20.0
def test_f_electric():
    print("\n[场景 F] 全电机 ABS 直通（冷流道+侧浇口）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='ABS'),
        machine=_machine(power_method='全电机'),
    ).process
    _assert_eq(proc.pst_met_decomp_pres, 0.0, 'P=0（全电机）')
    _assert_close(proc.pst_met_decomp_dist, 3.32, 'D')
    _assert_close(proc.pst_met_decomp_spd, 20.0, 'V (electric_default_velo)')


# ========== 场景 G：ABS 热流道+侧浇口（v1.1 runner_factor 验证）==========
# runner_factor=1.60, gate_factor=1.00（侧浇口不叠加）
# P=3.85（同E）, D=3.5×1.00×1.10×1.60×1.00 = 6.16, V=40.0（同E）
def test_g_hot_runner():
    print("\n[场景 G] ABS 热流道+侧浇口（v1.1 runner_factor 验证）")
    proc = _run(
        mold=_base_mold(runner_type='热流道', runner_weight=0, gate_type='侧浇口'),
        material=_base_material(abbreviation='ABS'),
        machine=_machine(nozzle_type='锁闭型'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 3.85, 'P')
    _assert_close(proc.pst_met_decomp_dist, 6.16, 'D (runner_factor=1.60)')
    _assert_close(proc.pst_met_decomp_spd, 40.0, 'V')


# ========== 场景 H：ABS 热流道+点浇口（v1.1 gate_factor 验证）==========
# runner_factor=1.60, gate_factor=1.30
# D=3.5×1.00×1.10×1.60×1.30 = 8.01
def test_h_hot_runner_point_gate():
    print("\n[场景 H] ABS 热流道+点浇口（v1.1 gate_factor 验证）")
    proc = _run(
        mold=_base_mold(runner_type='热流道', runner_weight=0, gate_type='点浇口'),
        material=_base_material(abbreviation='ABS'),
        machine=_machine(nozzle_type='锁闭型'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 3.85, 'P')
    _assert_close(proc.pst_met_decomp_dist, 8.01, 'D (runner×1.60 × gate×1.30)')


# ========== 场景 I：🔴 switch 手柄（ABS+锁闭+热流道+针阀式点浇口）==========
# runner_factor=1.60, gate_factor=1.70
# D=3.5×1.00×1.10×1.60×1.70 = 10.47（业内实测 10mm，误差 4.7%）
def test_i_switch_handle():
    print("\n[场景 I] 🔴 switch 手柄（ABS+锁闭+热流道+针阀式点浇口）")
    proc = _run(
        mold=_base_mold(runner_type='热流道', runner_weight=0, gate_type='针阀式点浇口'),
        material=_base_material(abbreviation='ABS'),
        machine=_machine(nozzle_type='锁闭型'),
    ).process
    _assert_close(proc.pst_met_decomp_pres, 3.85, 'P')
    _assert_close(proc.pst_met_decomp_dist, 10.47, 'D (业内实测 10mm)')
    _assert_close(proc.pst_met_decomp_spd, 40.0, 'V')
    _assert_close(proc.pst_met_decomp_t, 0.26, 'T (D/V)')


# ========== 场景 J：边界钳上限（max_set=100）==========
def test_j_upper_bound():
    print("\n[场景 J] 边界钳上限（max_set=100）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='PP'),
        machine=_machine(max_metering_pres=100.0),
    ).process
    # PP family_pres_factor=1.00 → P_raw = 100×0.25×1.00×1.00×0.95 = 23.75 → 钳到 5.0
    _assert_close(proc.pst_met_decomp_pres, 5.0, 'P (钳到 max_pressure=5.0)')


# ========== 场景 K：边界钳下限（max_set=2）==========
def test_k_lower_bound():
    print("\n[场景 K] 边界钳下限（max_set=2）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='侧浇口'),
        material=_base_material(abbreviation='PP'),
        machine=_machine(max_metering_pres=2.0),
    ).process
    # PP family_pres_factor=1.00 → P_raw = 2×0.25×1.00×1.00×0.95 = 0.475 → 钳到 1.0
    _assert_close(proc.pst_met_decomp_pres, 1.0, 'P (钳到 min_pressure=1.0)')


# ========== 场景 L：冷流道+针阀式点浇口（gate_factor 不叠加）==========
# 验证 gate_factor 仅热流道生效：runner_factor=1.00, gate_factor=1.00
# D=3.5×1.00×0.95×1.00×1.00 = 3.32（与场景 A 相同）
def test_l_cold_runner_ignores_gate():
    print("\n[场景 L] 冷流道+针阀式点浇口（gate_factor 不叠加验证）")
    proc = _run(
        mold=_base_mold(runner_type='冷流道', runner_weight=30, gate_type='针阀式点浇口'),
        material=_base_material(abbreviation='PP'),
    ).process
    # runner_factor=1.00（冷流道）, gate_factor=1.00（冷流道下不叠加）
    _assert_close(proc.pst_met_decomp_dist, 3.32, 'D (gate_factor 不叠加)')


# ========== 场景 M：#18 met_end_pos 公式透明 ==========
# met_end_pos = met_pos_steps[0] + pst_met_decomp_dist
def test_m_met_end_pos():
    print("\n[场景 M] #18 met_end_pos 公式透明")
    proc = _run(
        mold=_base_mold(runner_type='热流道', runner_weight=0, gate_type='针阀式点浇口'),
        material=_base_material(abbreviation='ABS'),
        machine=_machine(nozzle_type='锁闭型'),
    ).process
    # met_pos_steps 是 #14 算法输出，pst_dist=10.47
    # met_end_pos = met_pos_steps[0] + pst_dist（公式透明）
    expected_met_end = proc.met_pos_steps[0] + proc.pst_met_decomp_dist
    _assert_close(proc.met_end_pos, expected_met_end, 'met_end_pos = met_pos + pst_dist')
    print(f"    met_pos_steps[0]={proc.met_pos_steps[0]:.2f} + "
          f"pst_dist={proc.pst_met_decomp_dist:.2f} = "
          f"met_end_pos={proc.met_end_pos:.2f}")


# ========== 场景 N：钳制上限保护（D 不超过 12mm）==========
def test_n_max_dist_clamp():
    print("\n[场景 N] 钳制上限保护（D 不超过 12mm）")
    proc = _run(
        mold=_base_mold(runner_type='热流道', runner_weight=0, gate_type='针阀式点浇口'),
        material=_base_material(abbreviation='ABS'),
        machine=_machine(nozzle_type='锁闭型'),
    ).process
    _assert_le(proc.pst_met_decomp_dist, 12.0, 'D ≤ max_dist=12.0')


# ========== 主入口 ==========

def main():
    # 屏蔽日志输出，避免污染 smoke test 输出
    logging.disable(logging.CRITICAL)

    print("=" * 70)
    print("ProcessInitializer 松退参数族（#15-#18）smoke test v1.1")
    print("=" * 70)

    test_a_pp()
    test_b_pa66()
    test_c_pc()
    test_d_pvc()
    test_e_abs_locked()
    test_f_electric()
    test_g_hot_runner()
    test_h_hot_runner_point_gate()
    test_i_switch_handle()
    test_j_upper_bound()
    test_k_lower_bound()
    test_l_cold_runner_ignores_gate()
    test_m_met_end_pos()
    test_n_max_dist_clamp()

    # 输出汇总
    print("\n" + "=" * 70)
    print(f"测试结果汇总")
    print("=" * 70)
    for line in _passes:
        print(line)
    for line in _failures:
        print(line)
    print(f"\n通过: {len(_passes)}")
    print(f"失败: {len(_failures)}")
    print("=" * 70)

    if _failures:
        sys.exit(1)
    else:
        print(f"{PASS}✅ 全部 smoke test 通过！松退族 #15-#18 实施完成。{NC}")
        sys.exit(0)


if __name__ == '__main__':
    main()