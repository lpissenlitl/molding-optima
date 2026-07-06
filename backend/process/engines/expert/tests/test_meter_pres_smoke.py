"""
ProcessInitializer 计量压力 smoke test（独立运行，不依赖 Django）

覆盖范围：
  场景 A - PP 通用件（液压 + 直通）→ 期望 ~6.6
           （PP low_viscosity，20 × 0.55 × 0.6 × 1.0 = 6.6）
  场景 B - PC 精密件（液压 + 直通）→ 期望 ~11.0
           （PC medium_viscosity，20 × 0.55 × 1.0 × 1.0 = 11.0）
  场景 C - PA66 含水件（液压 + 直通）→ 期望 ~14.3
           （PA66 hygroscopic_high，20 × 0.55 × 1.3 × 1.0 = 14.3）
  场景 D - 全电机 ABS 精密件 → 期望 0（物理正确：全电机无油缸）
  场景 E - 锁闭喷嘴 PC 精密件 → 期望 ~12.1
           （20 × 0.55 × 1.0 × 1.10 = 12.1）
  场景 F - 未知材料保守兜底 → 期望 ~11.0（default family_factor=1.0）
  场景 G - 边界守门
           G1 钳制下限（PVC + 极小 max → 钳到 meter_pres_min）
           G2 钳制上限（PA66 + 极大 max → 钳到 meter_pres_max）
           G3 兜底 level 字符串验证（未知 family → 'default'）

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_meter_pres_smoke.py
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
from process.engines.expert.rule_matcher import InitRuleMatcher  # noqa: E402

PASS = '\033[92m'
FAIL = '\033[91m'
NC = '\033[0m'


# ========== 辅助：构造 context fixture ==========

def _machine(power_method='液压机', nozzle_type='直通型', max_metering_pres=20.0):
    """标准海天级注塑机（液压+直通+max=20）"""
    return {
        'screw_diameter': 40,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': 100.0,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': 100.0,
        'max_set_screw_rotation_speed': 150.0,
        'max_set_metering_pressure': max_metering_pres,
        'nozzle_type': nozzle_type,
        'power_method': power_method,
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
    跑一次 derive()，返回 met_pres_steps[0] 值。
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
    met_pres_list = params.process.met_pres_steps or []
    return met_pres_list[0] if met_pres_list else 0.0


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


# ========== 场景 A：PP 通用件（液压 + 直通）==========

def test_scenario_a_pp_low_viscosity():
    """PP 低黏度结晶材料：family_factor=0.6，应得到 6.6"""
    print("\n=== 场景 A: PP 通用件（液压 + 直通）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PP')
    meter_pres = _run(mold, material)
    # 物理推导：20 × 0.55 × 0.6 × 1.00 = 6.6
    _assert_close(meter_pres, 6.6, "A1 PP 低黏度 meter_pres ≈ 6.6（base_ratio × family × nozzle）", eps=0.5)


# ========== 场景 B：PC 精密件（液压 + 直通）==========

def test_scenario_b_pc_medium_viscosity():
    """PC 高黏度：family_factor=1.0，应得到 11.0（基准）"""
    print("\n=== 场景 B: PC 精密件（液压 + 直通）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PC')
    meter_pres = _run(mold, material)
    # 物理推导：20 × 0.55 × 1.0 × 1.00 = 11.0
    _assert_close(meter_pres, 11.0, "B1 PC 中黏度 meter_pres ≈ 11.0（基准）", eps=0.5)


# ========== 场景 C：PA66 含水件（液压 + 直通）==========

def test_scenario_c_pa66_high_viscosity():
    """PA66 高黏度+吸湿：family_factor=1.3，应得到 14.3"""
    print("\n=== 场景 C: PA66 含水件（液压 + 直通）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PA66')
    meter_pres = _run(mold, material)
    # 物理推导：20 × 0.55 × 1.3 × 1.00 = 14.3
    _assert_close(meter_pres, 14.3, "C1 PA66 高黏度 meter_pres ≈ 14.3（family=1.3）", eps=0.5)


# ========== 场景 D：全电机 ABS 精密件 ==========

def test_scenario_d_electric_machine():
    """全电机无油缸：meter_pres 应为 0（HMI 不显示）"""
    print("\n=== 场景 D: 全电机 ABS 精密件===")
    mold = _base_mold()
    material = _base_material(abbreviation='ABS')
    machine = _machine(power_method='全电机')
    meter_pres = _run(mold, material, machine=machine)
    _assert_eq(meter_pres, 0.0, "D1 全电机 meter_pres == 0（物理正确：无油缸）")


# ========== 场景 E：锁闭喷嘴 PC 精密件 ==========

def test_scenario_e_locking_nozzle():
    """锁闭喷嘴：nozzle_factor=1.10，PC 应得到 13.2"""
    print("\n=== 场景 E: 锁闭喷嘴 PC 精密件===")
    mold = _base_mold()
    material = _base_material(abbreviation='PC')
    machine = _machine(nozzle_type='锁定型')
    meter_pres = _run(mold, material, machine=machine)
    # 物理推导：base=0.6 (锁定) × 1.0 × 1.10 = 12.1? 不对，应是 0.6*1.0*1.1*20 = 13.2
    # 验证：20 × 0.60 × 1.0 × 1.10 = 13.2（锁闭 base_ratio=0.60 + nozzle_factor=1.10）
    _assert_close(meter_pres, 13.2, "E1 锁闭喷嘴 PC meter_pres ≈ 13.2（base=0.6 × 1.0 × 1.10）", eps=0.5)


# ========== 场景 F：未知材料保守兜底 ==========

def test_scenario_f_unknown_material_default():
    """未知 family：fallback 到 default=1.0，应得到 11.0"""
    print("\n=== 场景 F: 未知材料保守兜底===")
    mold = _base_mold()
    material = _base_material(abbreviation='XXX')  # 未知材料
    meter_pres = _run(mold, material)
    # 物理推导：20 × 0.55 × 1.0 × 1.00 = 11.0
    _assert_close(meter_pres, 11.0, "F1 未知 material meter_pres ≈ 11.0（family_factor=1.0 兜底）", eps=0.5)


# ========== 场景 G：边界守门 ==========

def test_scenario_g_boundary_clamp():
    """边界守门：钳制下限/上限是否生效"""
    print("\n=== 场景 G: 边界守门===")

    # G1：极小 max + PVC（family=0.5）→ 应被钳到 meter_pres_min=3.0
    mold = _base_mold()
    material = _base_material(abbreviation='PVC')
    machine = _machine(max_metering_pres=8.0)  # 极小 max
    meter_pres = _run(mold, material, machine=machine)
    # 原始推导：8 × 0.55 × 0.5 × 1.0 = 2.2 → 钳到 3.0
    _assert_ge(meter_pres, 3.0, "G1.1 PVC 极小 max → meter_pres >= meter_pres_min=3.0")
    _assert_le(meter_pres, 3.0, "G1.2 PVC 极小 max → meter_pres <= meter_pres_min=3.0（钳制生效）")

    # G2：极大 max + PA66（family=1.3）→ 应被钳到 meter_pres_max=18.0
    material = _base_material(abbreviation='PA66')
    machine = _machine(max_metering_pres=80.0)  # 极大 max
    meter_pres = _run(mold, material, machine=machine)
    # 原始推导：80 × 0.55 × 1.3 × 1.0 = 57.2 → 钳到 18.0
    _assert_le(meter_pres, 18.0, "G2 PA66 极大 max → meter_pres <= meter_pres_max=18.0（钳制生效）")

    # G3：兜底 level 字符串验证（直接调用内部函数）
    init = ProcessInitializer(
        mold_info=_base_mold(),
        machine_info=_machine(),
        polymer_info=_base_material(),
        process_set={},
    )
    # 关键：必须先 derive() 才会加载 _coeffs
    init.derive()
    coeffs = init._coeffs
    c_met = coeffs.get('metering', {})

    # 已知 family
    factor, level, key_used = init._get_family_meter_viscosity('PP', c_met)
    _assert_close(factor, 0.6, "G3.1 PP family_factor == 0.6", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "G3.2 PP level == 'precise_abbrev'（完整匹配）")
    _assert_eq(key_used, 'PP', "G3.3 PP key_used == 'PP'")

    # 未知 abbreviation 但 family 可解析（如 PA66）
    factor, level, key_used = init._get_family_meter_viscosity('PA66', c_met)
    _assert_close(factor, 1.3, "G3.4 PA66 family_factor == 1.3（精确匹配）", eps=0.01)
    _assert_eq(level, 'precise_abbrev', "G3.5 PA66 level == 'precise_abbrev'")
    _assert_eq(key_used, 'PA66', "G3.6 PA66 key_used == 'PA66'")

    # 未知 abbreviation + family 不可解析
    factor, level, key_used = init._get_family_meter_viscosity('XXX', c_met)
    _assert_close(factor, 1.0, "G3.7 XXX family_factor == 1.0（default）", eps=0.01)
    _assert_eq(level, 'default', "G3.8 XXX level == 'default'")

    # nozzle_factor 字符串验证
    f, l = init._get_nozzle_factor('直通型', c_met)
    _assert_close(f, 1.0, "G3.5 直通 nozzle_factor == 1.0", eps=0.01)
    _assert_eq(l, 'straight', "G3.6 直通 level == 'straight'")

    f, l = init._get_nozzle_factor('锁定型', c_met)
    _assert_close(f, 1.10, "G3.7 锁定 nozzle_factor == 1.10", eps=0.01)
    _assert_eq(l, 'locking', "G3.8 锁定 level == 'locking'")


# ========== 场景 H：动力源分支回归（保持原代码行为）==========

def test_scenario_h_electric_baseline():
    """全电机回归：原代码全电机=0，物理正确（不应破坏）"""
    print("\n=== 场景 H: 动力源分支回归（保持原代码逻辑）===")
    mold = _base_mold()
    material = _base_material(abbreviation='PC')
    machine = _machine(power_method='全电机')
    meter_pres = _run(mold, material, machine=machine)
    # 物理依据：全电机无油缸 → meter_pres = 0
    _assert_eq(meter_pres, 0.0, "H1 全电机（任何材料）→ meter_pres == 0")


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

    test_scenario_a_pp_low_viscosity()
    test_scenario_b_pc_medium_viscosity()
    test_scenario_c_pa66_high_viscosity()
    test_scenario_d_electric_machine()
    test_scenario_e_locking_nozzle()
    test_scenario_f_unknown_material_default()
    test_scenario_g_boundary_clamp()
    test_scenario_h_electric_baseline()

    fail_count = _print_summary()

    # 非零退出码用于 CI 检测
    sys.exit(0 if fail_count == 0 else 1)
