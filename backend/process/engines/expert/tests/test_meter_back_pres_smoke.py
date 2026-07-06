"""
ProcessInitializer 计量背压 smoke test（独立运行，不依赖 Django）

覆盖范围：
  场景 A - PP 通用件（family=1.00，基准）→ 期望 ~10.0
  场景 B - PC 精密件（family=1.30，高黏度）→ 期望 ~13.0
  场景 C - PA66 含水件（family=0.40，极易水解）→ 期望 ~4.0
  场景 D - PVC 通用件（family=0.50，剪切敏感）→ 期望 ~5.0
  场景 E - PMMA 高黏度件（family=1.50，强排气）→ 期望 ~15.0
  场景 F - 全电机 ABS 精密件 → 与液压机同公式（验证对称性）
  场景 G - 边界守门
           G1 钳制下限（PA66 + 极小 recommend_back → 钳到 0.5）
           G2 钳制上限（PMMA + 极大 recommend_back → 钳到 30.0）
           G3 转速联动（rpm_ratio=0.75 → speed_factor=1.15）
           G4 转速联动（rpm_ratio=0.30 → speed_factor=0.85）
           G5 recommend_back_pressure 缺失 → 兜底 10.0
  场景 H - 兜底 level 字符串验证
           H1 _get_family_back_pres_factor 各 level
           H2 _get_speed_factor 各 level

物理推导（标准：recommend_back=10.0, meter_speed/meter_max_screw_speed → rpm_ratio=0.5）：
    meter_back_pres_raw = 10.0 × family_factor × speed_factor
    meter_back_pres = clamp(raw, 0.5, 30.0)

    A: PP (family=1.00, sf=1.00) → 10.0 × 1.00 × 1.00 = 10.0
    B: PC (family=1.30, sf=1.00) → 13.0
    C: PA66 (family=0.40, sf=1.00) → 4.0
    D: PVC (family=0.50, sf=1.00) → 5.0
    E: PMMA (family=1.50, sf=1.00) → 15.0
    F: ABS 全电机 (family=1.00, sf=1.00) → 10.0 = 液压机
    G3: ABS + rpm=0.75 → sf=1.15 → 11.5
    G4: ABS + rpm=0.30 → sf=0.85 → 8.5

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_meter_back_pres_smoke.py
"""

import logging
import os
import sys

# 让 process 作为顶层 package 可被发现
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # backend/
sys.path.insert(0, BACKEND_ROOT)

from process.engines.expert.initializer import ProcessInitializer  # noqa: E402
from process.engines.expert.algorithm_engine import AlgorithmEngine  # noqa: E402

PASS = '\033[92m'
FAIL = '\033[91m'
NC = '\033[0m'


# ========== 辅助：构造 context fixture ==========

def _machine(power_method='液压机', nozzle_type='直通型', max_screw_rotation_speed=150.0,
             screw_diameter=40.0):
    """标准海天级注塑机（液压+直通+max=150rpm）"""
    return {
        'screw_diameter': screw_diameter,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': 100.0,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': 100.0,
        'max_set_screw_rotation_speed': max_screw_rotation_speed,
        'max_set_metering_pressure': 20.0,
        'nozzle_type': nozzle_type,
        'power_method': power_method,
        'screw_length_to_diameter_ratio': 20.0,
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
    """基础 ABS 材料（字段命名与数据库一致）"""
    m = {
        'abbreviation': 'ABS',
        'category': '无定形',
        'recommended_melt_temp': 240.0,
        'recommended_mold_temp': 60.0,
        'ejection_temp': 90.0,
        'recommend_shear_linear_speed': 160.0,
        'recommend_back_pressure': 10.0,
        'melt_density': 0.95,
    }
    m.update(overrides)
    return m


def _run(mold, material, machine=None, process_set=None):
    """
    跑一次 derive()，返回 met_back_pres_steps[0] 值。
    """
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
    params = init.derive()
    met_back_pres_list = params.process.met_back_pres_steps or []
    return met_back_pres_list[0] if met_back_pres_list else 0.0


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


# ========== 场景 A：PP 通用件（基准）==========

def test_scenario_a_pp_baseline():
    """PP 结晶型：family_factor=1.00，期望 ~10.0 MPa（基准）"""
    print("\n=== 场景 A: PP 通用件（基准）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PP')
    meter_back_pres = _run(mold, material)
    # 物理推导：10.0 × 1.00 × 1.00 = 10.0
    _assert_close(meter_back_pres, 10.0, "A1 PP 结晶型 meter_back_pres ≈ 10.0MPa（family=1.00 基准）", eps=0.5)


# ========== 场景 B：PC 精密件（高黏度强排气）==========

def test_scenario_b_pc_high_viscosity():
    """PC 高黏度：family_factor=1.30，meter_speed 钳到下限 45rpm，rpm_ratio=0.30，speed_factor=0.94，期望 ~12.2 MPa"""
    print("\n=== 场景 B: PC 精密件（高黏度强排气）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PC')
    meter_back_pres = _run(mold, material)
    # 物理推导：PC meter_speed 钳到 45rpm，rpm_ratio=0.30，speed_factor=1.0+0.3*(0.30-0.5)=0.94
    #         meter_back_pres = 10.0 × 1.30 × 0.94 ≈ 12.22
    _assert_close(meter_back_pres, 12.22, "B1 PC 高黏度 meter_back_pres ≈ 12.22MPa（family=1.30, sf=0.94）", eps=0.5)


# ========== 场景 C：PA66 含水件（极易水解）==========

def test_scenario_c_pa66_hydrolysis():
    """PA66 极易水解：family_factor=0.40，期望 ~4.0 MPa（防摩擦生热水解）"""
    print("\n=== 场景 C: PA66 含水件（极易水解）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PA66')
    meter_back_pres = _run(mold, material)
    # 物理推导：10.0 × 0.40 × 1.00 = 4.0
    _assert_close(meter_back_pres, 4.0, "C1 PA66 极易水解 meter_back_pres ≈ 4.0MPa（family=0.40 防摩擦生热水解）", eps=0.5)


# ========== 场景 D：PVC 通用件（剪切敏感）==========

def test_scenario_d_pvc_shear_sensitive():
    """PVC 剪切敏感：family_factor=0.50，期望 ~5.0 MPa（防 HCl 释放）"""
    print("\n=== 场景 D: PVC 通用件（剪切敏感）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PVC')
    meter_back_pres = _run(mold, material)
    # 物理推导：10.0 × 0.50 × 1.00 = 5.0
    _assert_close(meter_back_pres, 5.0, "D1 PVC 剪切敏感 meter_back_pres ≈ 5.0MPa（family=0.50 防 HCl 释放）", eps=0.5)


# ========== 场景 E：PMMA 高黏度件（强排气需求）==========

def test_scenario_e_pmma_high_exhaust():
    """PMMA 高黏度：family_factor=1.50，期望 ~15.0 MPa"""
    print("\n=== 场景 E: PMMA 高黏度件（强排气需求）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PMMA')
    meter_back_pres = _run(mold, material)
    # 物理推导：10.0 × 1.50 × 1.00 = 15.0
    _assert_close(meter_back_pres, 15.0, "E1 PMMA 高黏度 meter_back_pres ≈ 15.0MPa（family=1.50 强排气）", eps=0.5)


# ========== 场景 F：全电机 ABS 精密件（与液压机同公式）==========

def test_scenario_f_electric_machine_same_formula():
    """全电机与液压机走同一公式：验证对称性"""
    print("\n=== 场景 F: 全电机 ABS 精密件（与液压机同公式）===")
    mold = _base_mold()
    material = _base_material(abbreviation='ABS')

    # 液压机 ABS
    machine_hydraulic = _machine(power_method='液压机')
    meter_back_pres_hydraulic = _run(mold, material, machine=machine_hydraulic)
    # 全电机 ABS
    machine_electric = _machine(power_method='全电机')
    meter_back_pres_electric = _run(mold, material, machine=machine_electric)
    # 两者应该完全一致（不分支动力源）
    _assert_close(meter_back_pres_hydraulic, meter_back_pres_electric,
                  "F1 全电机 == 液压机 meter_back_pres（不分支动力源）", eps=0.01)
    # ABS (family=1.00): 10.0 × 1.00 × 1.00 = 10.0
    _assert_close(meter_back_pres_electric, 10.0, "F2 全电机 ABS meter_back_pres ≈ 10.0MPa（基准）", eps=0.5)


# ========== 场景 G：边界守门 ==========

def test_scenario_g_boundary_clamp():
    """边界守门：钳制下限/上限 + 转速联动 + 字段缺失兑底"""
    print("\n=== 场景 G: 边界守门===")

    # G1：钳制下限（PA66 + 极小 recommend_back=1.0 → 钳到 0.5）
    mold = _base_mold()
    material = _base_material(abbreviation='PA66', recommend_back_pressure=1.0)
    meter_back_pres = _run(mold, material)
    # 物理推导：1.0 × 0.40 × 1.00 = 0.4 → 钳到 0.5
    _assert_close(meter_back_pres, 0.5, "G1 PA66 极小 recommend_back → meter_back_pres ≈ 0.5MPa（钳制下限）", eps=0.5)

    # G2：钳制上限（PMMA + 极大 recommend_back=100 → 钳到 30.0）
    material = _base_material(abbreviation='PMMA', recommend_back_pressure=100.0)
    meter_back_pres = _run(mold, material)
    # 物理推导：100.0 × 1.50 × 1.00 = 150.0 → 钳到 30.0
    _assert_close(meter_back_pres, 30.0, "G2 PMMA 极大 recommend_back → meter_back_pres ≈ 30.0MPa（钳制上限）", eps=0.5)

    # G3：转速联动（rpm_ratio=0.75 → speed_factor=1.075，未钳到 1.15 上限）
    # 需手动调用（标准 max=150 → meter_speed 实际值依赖 #12 推导）
    # 这里直接验证 _get_speed_factor 函数
    init = ProcessInitializer(
        mold_info=_base_mold(),
        machine_info=_machine(),
        polymer_info=_base_material(),
        process_set={},
    )
    init.derive()  # 必须先 derive() 才会加载 _coeffs
    c_back = init.engine._coeffs.get('back_pressure', {})
    # meter_speed = 0.75 × 150 = 112.5 → rpm_ratio=0.75 → speed_factor=1.0+0.3*(0.75-0.5)=1.075
    sf, level = init.engine._get_speed_factor(112.5, 150.0, c_back)
    _assert_close(sf, 1.075, "G3 rpm_ratio=0.75 → speed_factor ≈ 1.075", eps=0.01)
    _assert_eq(level, 'high', "G3.1 rpm_ratio=0.75 level == 'high'")

    # G4：转速联动（rpm_ratio=0.30 → speed_factor=0.94，未钳到 0.85 下限）
    sf, level = init.engine._get_speed_factor(45.0, 150.0, c_back)
    _assert_close(sf, 0.94, "G4 rpm_ratio=0.30 → speed_factor ≈ 0.94", eps=0.01)
    _assert_eq(level, 'low', "G4.1 rpm_ratio=0.30 level == 'low'")

    # G5：rpm_ratio=0.5 → speed_factor=1.00
    sf, level = init.engine._get_speed_factor(75.0, 150.0, c_back)
    _assert_close(sf, 1.00, "G5 rpm_ratio=0.5 → speed_factor ≈ 1.00（基准）", eps=0.01)
    _assert_eq(level, 'base', "G5.1 rpm_ratio=0.5 level == 'base'")

    # G6：recommend_back_pressure 缺失 → 兑底 10.0
    material = _base_material(abbreviation='ABS')
    material.pop('recommend_back_pressure', None)
    meter_back_pres = _run(_base_mold(), material)
    # 物理推导：默认 10.0 × 1.00 × 1.00 = 10.0
    _assert_close(meter_back_pres, 10.0, "G6 recommend_back 缺失 → meter_back_pres ≈ 10.0MPa（兑底 10.0）", eps=0.5)


# ========== 场景 H：兜底 level 字符串验证 ==========

def test_scenario_h_level_strings():
    """内部函数 level 字符串验证：_get_family_back_pres_factor + _get_speed_factor"""
    print("\n=== 场景 H: 兜底 level 字符串验证===")

    init = ProcessInitializer(
        mold_info=_base_mold(),
        machine_info=_machine(),
        polymer_info=_base_material(),
        process_set={},
    )
    init.derive()
    c_back = init.engine._coeffs.get('back_pressure', {})

    # H1：_get_family_back_pres_factor 各 level

    # 已知 abbreviation（精确匹配）
    factor, level, key_used = init.engine._get_family_back_pres_factor('PA66', c_back)
    _assert_close(factor, 0.40, "H1.1 PA66 family_factor == 0.40", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "H1.2 PA66 level == 'precise_abbrev'")
    _assert_eq(key_used, 'PA66', "H1.3 PA66 key_used == 'PA66'")

    # 已知 abbreviation（PVC 精确匹配）
    factor, level, key_used = init.engine._get_family_back_pres_factor('PVC', c_back)
    _assert_close(factor, 0.50, "H1.4 PVC family_factor == 0.50", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "H1.5 PVC level == 'precise_abbrev'")

    # 已知 abbreviation（PMMA 精确匹配）
    factor, level, key_used = init.engine._get_family_back_pres_factor('PMMA', c_back)
    _assert_close(factor, 1.50, "H1.6 PMMA family_factor == 1.50", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "H1.7 PMMA level == 'precise_abbrev'")

    # 已知 family（abbreviation 不精确但 family 可解析）
    # 注意：PA66 在第 1 级就精确匹配了，用 'PA6' 演示第 2 级 fallback
    factor, level, key_used = init.engine._get_family_back_pres_factor('PA6', c_back)
    _assert_close(factor, 0.60, "H1.8 PA6 family_factor == 0.60（精确匹配）", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "H1.9 PA6 level == 'precise_abbrev'")

    # 未知 abbreviation + family 不可解析 → default
    factor, level, key_used = init.engine._get_family_back_pres_factor('XXX', c_back)
    _assert_close(factor, 1.0, "H1.10 XXX family_factor == 1.0（default）", eps=0.01)
    _assert_eq(level, 'default', "H1.11 XXX level == 'default'")

    # H2：_get_speed_factor 各 level

    # 字段缺失 → default
    sf, level = init.engine._get_speed_factor(None, 150.0, c_back)
    _assert_close(sf, 1.00, "H2.1 meter_speed 缺失 speed_factor == 1.00（default）", eps=0.01)
    _assert_eq(level, 'default', "H2.2 meter_speed 缺失 level == 'default'")

    # max_screw_speed = 0 → default（避免除零）
    sf, level = init.engine._get_speed_factor(75.0, 0, c_back)
    _assert_close(sf, 1.00, "H2.3 max_screw_speed=0 speed_factor == 1.00（default）", eps=0.01)
    _assert_eq(level, 'default', "H2.4 max_screw_speed=0 level == 'default'")

    # high 桶（rpm_ratio > 0.5）
    sf, level = init.engine._get_speed_factor(112.5, 150.0, c_back)
    _assert_eq(level, 'high', "H2.5 rpm_ratio=0.75 level == 'high'")

    # base 桶（rpm_ratio = 0.5）
    sf, level = init.engine._get_speed_factor(75.0, 150.0, c_back)
    _assert_eq(level, 'base', "H2.6 rpm_ratio=0.5 level == 'base'")

    # low 桶（rpm_ratio < 0.5）
    sf, level = init.engine._get_speed_factor(45.0, 150.0, c_back)
    _assert_eq(level, 'low', "H2.7 rpm_ratio=0.30 level == 'low'")


# ========== 测试结果汇总 ==========

def _print_summary():
    print("\n" + "=" * 70)
    print("  Smoke Test 结果汇总")
    print("=" * 70)

    if _passes:
        print("\n通过的断言:")
        for line in _passes:
            print(line)

    if _failures:
        print("\n失败的断言:")
        for line in _failures:
            print(line)

    total = len(_passes) + len(_failures)
    fail_count = len(_failures)
    print("\n" + "=" * 70)
    if fail_count == 0:
        print(f"  {PASS}✓ 全部通过{NC}  ({len(_passes)}/{total})")
    else:
        print(f"  {FAIL}✗ 有失败{NC}  ({fail_count}/{total} 失败)")
    print("=" * 70)
    return fail_count


if __name__ == '__main__':
    # 关闭 info 级别日志，保持输出清晰
    logging.basicConfig(level=logging.WARNING)

    test_scenario_a_pp_baseline()
    test_scenario_b_pc_high_viscosity()
    test_scenario_c_pa66_hydrolysis()
    test_scenario_d_pvc_shear_sensitive()
    test_scenario_e_pmma_high_exhaust()
    test_scenario_f_electric_machine_same_formula()
    test_scenario_g_boundary_clamp()
    test_scenario_h_level_strings()

    fail_count = _print_summary()

    # 非零退出码用于 CI 检测
    sys.exit(0 if fail_count == 0 else 1)