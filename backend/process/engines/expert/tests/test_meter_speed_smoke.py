"""
ProcessInitializer 计量螺杆转速 smoke test（独立运行，不依赖 Django）

覆盖范围：
  场景 A - PP 通用件（family_factor=1.10）→ ratio_raw 钳制后适中
  场景 B - PC 精密件（family_factor=0.55）→ ratio_raw 钳到下限 0.30
  场景 C - PA66 含水件（family_factor=0.50）→ ratio_raw 钳到下限 0.30
  场景 D - 全电机 ABS → 与液压机走同一公式（验证对称性）
  场景 E - 短 L/D=16（ld_factor=1.05）→ 比 standard 高 5%
  场景 F - 长 L/D=24（ld_factor=0.95）→ 比 standard 低 5%
  场景 G - 边界守门
           G1 钳制下限（极小 v_surface + 大 max → 钳到 0.30 × max）
           G2 钳制上限（大 v_surface + 小 max → 钳到 0.75 × max）
           G3 L/D 字段缺失 → 兜底 1.00
  场景 H - 兜底 level 字符串验证
           H1 _get_family_meter_shear_ratio 各 level
           H2 _get_ld_correction 各桶 level

物理推导（标准：D=40, v=160, max_screw_speed=150, L/D=20 默认）：
    ratio_raw = 60 × v × family × ld / (40 × π × 150)
              = 60 × 160 × family × ld / 18849.6
              ≈ 0.5093 × family × ld

    A: PP (family=1.10) → ratio_raw=0.5603 → 84.05 rpm
    B: PC (family=0.55) → ratio_raw=0.2801 → 钳到 0.30 → 45.0 rpm
    C: PA66 (family=0.50) → ratio_raw=0.2546 → 钳到 0.30 → 45.0 rpm
    D: 全电机 ABS (family=1.00) → 与液压机同公式 → 76.39 rpm
    E: ABS + L/D=16 (family=1.00, ld=1.05) → ratio_raw=0.5347 → 80.21 rpm
    F: ABS + L/D=24 (family=1.00, ld=0.95) → ratio_raw=0.4838 → 72.57 rpm

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_meter_speed_smoke.py
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
             screw_diameter=40.0, screw_ld_ratio=20.0):
    """标准海天级注塑机（液压+直通+max=150rpm+L/D=20）"""
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
        'screw_length_to_diameter_ratio': screw_ld_ratio,
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
    """基础 ABS 材料（字段命名与数据库一致）

    说明：代码中所有材料参数字段名与数据库字段命名保持一致。
    测试 fixture 走 algorithm 输入路径，使用与数据库同名的字段名以避免认知差异。
    """
    m = {
        'abbreviation': 'ABS',
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
    """
    跑一次 derive()，返回 met_rot_spd_steps[0] 值。
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
    met_rot_spd_list = params.process.met_rot_spd_steps or []
    return met_rot_spd_list[0] if met_rot_spd_list else 0.0


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


# ========== 场景 A：PP 通用件 ==========

def test_scenario_a_pp_high_shear():
    """PP 流动性好：family_factor=1.10，应得到 ~84.05rpm"""
    print("\n=== 场景 A: PP 通用件（液压 + 直通 + L/D=20）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PP')
    meter_speed = _run(mold, material)
    # 物理推导：ratio_raw = 60×160×1.10×1.00 / 18849.6 ≈ 0.5603
    #         meter_speed = 0.5603 × 150 ≈ 84.05
    _assert_close(meter_speed, 84.05, "A1 PP 流动性好 meter_speed ≈ 84.05rpm（family=1.10）", eps=0.5)


# ========== 场景 B：PC 精密件 ==========

def test_scenario_b_pc_conservative():
    """PC 高黏度：family_factor=0.55，ratio_raw 应被钳到下限 0.30，meter_speed=45"""
    print("\n=== 场景 B: PC 精密件（液压 + 直通 + L/D=20）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PC')
    meter_speed = _run(mold, material)
    # 物理推导：ratio_raw = 60×160×0.55×1.00 / 18849.6 ≈ 0.2801 → 钳到 0.30
    #         meter_speed = 0.30 × 150 = 45.0
    _assert_close(meter_speed, 45.0, "B1 PC 高黏度 meter_speed ≈ 45.0rpm（钳制下限生效）", eps=0.5)


# ========== 场景 C：PA66 含水件 ==========

def test_scenario_c_pa66_most_conservative():
    """PA66 最保守：family_factor=0.50，钳制下限"""
    print("\n=== 场景 C: PA66 含水件（液压 + 直通 + L/D=20）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PA66')
    meter_speed = _run(mold, material)
    # 物理推导：ratio_raw = 60×160×0.50×1.00 / 18849.6 ≈ 0.2546 → 钳到 0.30
    #         meter_speed = 0.30 × 150 = 45.0
    _assert_close(meter_speed, 45.0, "C1 PA66 偏保守 meter_speed ≈ 45.0rpm（钳制下限生效）", eps=0.5)


# ========== 场景 D：全电机 ABS 精密件（与液压机同公式）==========

def test_scenario_d_electric_machine_same_formula():
    """全电机与液压机走同一公式：验证对称性"""
    print("\n=== 场景 D: 全电机 ABS 精密件（与液压机同公式）===")
    mold = _base_mold()
    material = _base_material(abbreviation='ABS')

    # 液压机 ABS
    machine_hydraulic = _machine(power_method='液压机')
    meter_speed_hydraulic = _run(mold, material, machine=machine_hydraulic)
    # 全电机 ABS
    machine_electric = _machine(power_method='全电机')
    meter_speed_electric = _run(mold, material, machine=machine_electric)
    # 两者应该完全一致（不分支动力源）
    _assert_close(meter_speed_hydraulic, meter_speed_electric,
                  "D1 全电机 == 液压机 meter_speed（不分支动力源）", eps=0.01)
    # ABS (family=1.00): ratio_raw = 60×160×1.00×1.00 / 18849.6 ≈ 0.5093
    #                   meter_speed = 0.5093 × 150 ≈ 76.39
    _assert_close(meter_speed_electric, 76.39, "D2 全电机 ABS meter_speed ≈ 76.39rpm（基准）", eps=0.5)


# ========== 场景 E：短 L/D ABS（L/D=16）==========

def test_scenario_e_short_ld():
    """短 L/D=16：ld_factor=1.05，应比 standard 高 5%"""
    print("\n=== 场景 E: 短 L/D ABS（L/D=16 → ld_factor=1.05）===")
    mold = _base_mold()
    material = _base_material(abbreviation='ABS')
    machine = _machine(screw_ld_ratio=16.0)
    meter_speed = _run(mold, material, machine=machine)
    # 物理推导：ratio_raw = 60×160×1.00×1.05 / 18849.6 ≈ 0.5347
    #         meter_speed = 0.5347 × 150 ≈ 80.21
    _assert_close(meter_speed, 80.21, "E1 短 L/D=16 ABS meter_speed ≈ 80.21rpm（ld_factor=1.05）", eps=0.5)


# ========== 场景 F：长 L/D ABS（L/D=24）==========

def test_scenario_f_long_ld():
    """长 L/D=24：ld_factor=0.95，应比 standard 低 5%"""
    print("\n=== 场景 F: 长 L/D ABS（L/D=24 → ld_factor=0.95）===")
    mold = _base_mold()
    material = _base_material(abbreviation='ABS')
    machine = _machine(screw_ld_ratio=24.0)
    meter_speed = _run(mold, material, machine=machine)
    # 物理推导：ratio_raw = 60×160×1.00×0.95 / 18849.6 ≈ 0.4838
    #         meter_speed = 0.4838 × 150 ≈ 72.57
    _assert_close(meter_speed, 72.57, "F1 长 L/D=24 ABS meter_speed ≈ 72.57rpm（ld_factor=0.95）", eps=0.5)


# ========== 场景 G：边界守门 ==========

def test_scenario_g_boundary_clamp():
    """边界守门：钳制下限/上限 + L/D 字段缺失兜底"""
    print("\n=== 场景 G: 边界守门===")

    # G1：钳制下限（PA66 + 极大 max_screw_speed=300 → ratio_raw=0.127 → 钳到 0.30）
    mold = _base_mold()
    material = _base_material(abbreviation='PA66')
    machine = _machine(max_screw_rotation_speed=300.0)  # 极大 max
    meter_speed = _run(mold, material, machine=machine)
    # 物理推导：ratio_raw = 60×160×0.50×1.00 / (40×π×300) ≈ 0.1273 → 钳到 0.30
    #         meter_speed = 0.30 × 300 = 90.0
    _assert_close(meter_speed, 90.0, "G1 PA66 极大 max → meter_speed ≈ 90.0rpm（钳制下限生效）", eps=0.5)

    # G2：钳制上限（PP + 极小 max_screw_speed=30 → ratio_raw=2.80 → 钳到 0.75）
    material = _base_material(abbreviation='PP')
    machine = _machine(max_screw_rotation_speed=30.0)  # 极小 max
    meter_speed = _run(mold, material, machine=machine)
    # 物理推导：ratio_raw = 60×160×1.10×1.00 / (40×π×30) ≈ 2.8014 → 钳到 0.75
    #         meter_speed = 0.75 × 30 = 22.5
    _assert_close(meter_speed, 22.5, "G2 PP 极小 max → meter_speed ≈ 22.5rpm（钳制上限生效）", eps=0.5)

    # G3：L/D 字段缺失 → 兜底 1.00（与 L/D=20 standard 相同）
    material = _base_material(abbreviation='ABS')
    machine_no_ld = {
        'screw_diameter': 40,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': 100.0,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': 100.0,
        'max_set_screw_rotation_speed': 150.0,
        'max_set_metering_pressure': 20.0,
        'nozzle_type': '直通型',
        'power_method': '液压机',
        # 故意不设置 screw_length_to_diameter_ratio（缺失）
    }
    meter_speed_no_ld = _run(mold, material, machine=machine_no_ld)
    # 物理推导：ratio_raw = 60×160×1.00×1.00 / 18849.6 ≈ 0.5093（兜底 ld=1.00）
    #         meter_speed = 0.5093 × 150 ≈ 76.39
    _assert_close(meter_speed_no_ld, 76.39, "G3 L/D 缺失 → meter_speed ≈ 76.39rpm（兜底 ld_factor=1.00）", eps=0.5)


# ========== 场景 H：兜底 level 字符串验证 ==========

def test_scenario_h_level_strings():
    """内部函数 level 字符串验证：_get_family_meter_shear_ratio + _get_ld_correction"""
    print("\n=== 场景 H: 兜底 level 字符串验证===")

    init = ProcessInitializer(
        mold_info=_base_mold(),
        machine_info=_machine(),
        polymer_info=_base_material(),
        process_set={},
    )
    init.derive()  # 必须先 derive() 才会加载 _coeffs
    coeffs = init.engine._coeffs
    c_met = coeffs.get('metering', {})

    # H1：_get_family_meter_shear_ratio 各 level

    # 已知 abbreviation（精确匹配）
    factor, level, key_used = init.engine._get_family_meter_shear_ratio('PP', c_met)
    _assert_close(factor, 1.10, "H1.1 PP family_factor == 1.10", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "H1.2 PP level == 'precise_abbrev'（完整匹配）")
    _assert_eq(key_used, 'PP', "H1.3 PP key_used == 'PP'")

    # 已知 family（abbreviation 不精确但 family 可解析）
    factor, level, key_used = init.engine._get_family_meter_shear_ratio('PA66', c_met)
    _assert_close(factor, 0.50, "H1.4 PA66 family_factor == 0.50（精确匹配）", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "H1.5 PA66 level == 'precise_abbrev'")
    _assert_eq(key_used, 'PA66', "H1.6 PA66 key_used == 'PA66'")

    # 未知 abbreviation + family 不可解析 → default
    factor, level, key_used = init.engine._get_family_meter_shear_ratio('XXX', c_met)
    _assert_close(factor, 1.0, "H1.7 XXX family_factor == 1.0（default）", eps=0.01)
    _assert_eq(level, 'default', "H1.8 XXX level == 'default'")

    # H2：_get_ld_correction 各桶 level

    # 字段缺失 → default
    factor, level = init.engine._get_ld_correction(None, c_met)
    _assert_close(factor, 1.00, "H2.1 L/D 缺失 ld_factor == 1.00（default）", eps=0.01)
    _assert_eq(level, 'default', "H2.2 L/D 缺失 level == 'default'")

    # short L/D=16
    factor, level = init.engine._get_ld_correction(16.0, c_met)
    _assert_close(factor, 1.05, "H2.3 L/D=16 ld_factor == 1.05（short）", eps=0.01)
    _assert_eq(level, 'short', "H2.4 L/D=16 level == 'short'")

    # standard L/D=20
    factor, level = init.engine._get_ld_correction(20.0, c_met)
    _assert_close(factor, 1.00, "H2.5 L/D=20 ld_factor == 1.00（standard）", eps=0.01)
    _assert_eq(level, 'standard', "H2.6 L/D=20 level == 'standard'")

    # long L/D=24
    factor, level = init.engine._get_ld_correction(24.0, c_met)
    _assert_close(factor, 0.95, "H2.7 L/D=24 ld_factor == 0.95（long）", eps=0.01)
    _assert_eq(level, 'long', "H2.8 L/D=24 level == 'long'")

    # 边界 L/D=18（standard）
    factor, level = init.engine._get_ld_correction(18.0, c_met)
    _assert_eq(level, 'standard', "H2.9 L/D=18（边界）level == 'standard'")

    # 边界 L/D=22（standard）
    factor, level = init.engine._get_ld_correction(22.0, c_met)
    _assert_eq(level, 'standard', "H2.10 L/D=22（边界）level == 'standard'")


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

    test_scenario_a_pp_high_shear()
    test_scenario_b_pc_conservative()
    test_scenario_c_pa66_most_conservative()
    test_scenario_d_electric_machine_same_formula()
    test_scenario_e_short_ld()
    test_scenario_f_long_ld()
    test_scenario_g_boundary_clamp()
    test_scenario_h_level_strings()

    fail_count = _print_summary()

    # 非零退出码用于 CI 检测
    sys.exit(0 if fail_count == 0 else 1)