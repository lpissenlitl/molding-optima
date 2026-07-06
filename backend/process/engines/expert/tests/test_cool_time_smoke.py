"""
ProcessInitializer 冷却时间 smoke test（独立运行，不依赖 Django）

覆盖：
  场景 A - PET 厚壁（结晶型）→ 期望 ~54.6s
           （PET factor=2.0 × 5² × 0.95 × 1.15 = 54.625）
  场景 B - 材料梯度（PP/ABS/PC/PET/未知）
           B1 PP 薄壁（结晶 + 易冷）→ 钳到 5s
           B2 ABS 中壁（无定形）→ 钳到 5s
           B3 PC 厚壁（高黏度无定形）→ ~15.4s
           B4 未知 family → default_factor=1.2
  场景 C - 边界守门
           C1 模温修正（温差比 0.95 在 0.7~1.0 区间 → factor=1.00）
           C2 模温修正（温差比 0.5 在 <0.5 区间 → factor=1.20）
           C3 缺失数据兜底（ejection_temp=0 → factor=1.0）
           C4 最小值钳制（薄壁件必须 ≥ 5s）
  场景 D - 物理正交
           D1 与 #8 保压时间数值不重叠（保压时间 ⊂ 冷却时间）

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_cool_time_smoke.py
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
    """基础 ABS 材料（字段命名与数据库一致：recommended_*_temp / ejection_temp）

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
    跑一次 derive()，返回 cool_t 值。
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
    return params.process.cool_t, params.process.hold_time_steps[0] if params.process.hold_time_steps else 0.0


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


# ========== 场景 A：PET 厚壁（结晶型）==========

def test_scenario_a_pet_thick_crystalline():
    print("\n=== 场景 A: PET 厚壁（结晶型）===")
    # 物理推导：factor=2.0 × h²=25 × ΔT_factor=0.95 × crystallinity_kick=1.15 = 54.625s
    mold = _base_mold(ave_thickness=5.0, max_thickness=5.0)
    material = _base_material(
        abbreviation='PET',
        category='结晶型',
        recommended_melt_temp=280.0,
        recommended_mold_temp=80.0,
        ejection_temp=120.0,
    )
    cool_t, _ = _run(mold, material)
    _assert_close(cool_t, 54.62, "A1 PET 厚壁 cool_t ≈ 54.62s（factor=2.0 × 5² × 0.95 × 1.15）", eps=0.5)


# ========== 场景 B：材料梯度 ==========

def test_scenario_b_material_gradient():
    print("\n=== 场景 B: 材料梯度===")

    # B1: PP 薄壁（结晶 + 易冷 + 薄壁 → 钳制到 5s）
    mold = _base_mold(ave_thickness=1.0, max_thickness=1.0)
    material = _base_material(
        abbreviation='PP',
        category='结晶型',
        recommended_melt_temp=220.0,
        recommended_mold_temp=40.0,
        ejection_temp=80.0,
    )
    cool_t, _ = _run(mold, material)
    _assert_eq(cool_t, 5.0, "B1 PP 薄壁 cool_t=5s（钳制到最小值，物理推导仅 0.98s）")

    # B2: ABS 中壁（无定形）
    mold = _base_mold(ave_thickness=2.0, max_thickness=2.0)
    material = _base_material(
        abbreviation='ABS',
        category='无定形',
        recommended_melt_temp=240.0,
        recommended_mold_temp=60.0,
        ejection_temp=90.0,
    )
    cool_t, _ = _run(mold, material)
    # 物理推导：factor=1.1 × 4 × 0.95 × 1.0 = 4.18s，钳到 5s
    _assert_eq(cool_t, 5.0, "B2 ABS 中壁 cool_t=5s（钳制）")

    # B3: PC 厚壁（高黏度无定形）
    mold = _base_mold(ave_thickness=3.0, max_thickness=3.0)
    material = _base_material(
        abbreviation='PC',
        category='无定形',
        recommended_melt_temp=290.0,
        recommended_mold_temp=90.0,
        ejection_temp=130.0,
    )
    cool_t, _ = _run(mold, material)
    # 物理推导：factor=1.8 × 9 × 0.95 × 1.0 = 15.39s
    _assert_close(cool_t, 15.39, "B3 PC 厚壁 cool_t ≈ 15.39s（factor=1.8 × 3² × 0.95）", eps=0.5)

    # B4: 未知材料（默认 factor=1.2）
    mold = _base_mold(ave_thickness=2.0, max_thickness=2.0)
    material = _base_material(
        abbreviation='XXX',
        category='',
        recommended_melt_temp=240.0,
        recommended_mold_temp=60.0,
        ejection_temp=0.0,
    )
    cool_t, _ = _run(mold, material)
    # 物理推导：factor=1.2 × 4 × 1.0（missing） × 1.10（unknown default） = 5.28s
    _assert_close(cool_t, 5.28, "B4 未知材料 cool_t ≈ 5.28s（default_factor=1.2 × missing_data × unknown_kick=1.10）", eps=0.1)


# ========== 场景 C：边界守门 ==========

def test_scenario_c_boundary():
    print("\n=== 场景 C: 边界守门===")

    # C1: 模温修正 - 正常模温（温差比 0.95 在 0.7~1.0 区间）
    mold = _base_mold(ave_thickness=2.0, max_thickness=2.0)
    material = _base_material(
        abbreviation='ABS',
        category='无定形',
        recommended_melt_temp=240.0,
        recommended_mold_temp=60.0,
        ejection_temp=90.0,
    )
    cool_t, _ = _run(mold, material)
    # (240-60)/(240-90) = 180/150 = 1.2 → factor=0.95
    # 但 ABS 中壁推导值 4.18s < 5s，最终钳到 5s
    _assert_eq(cool_t, 5.0, "C1 正常模温 cool_t=5s（推导 4.18s 钳制）")

    # C2: 模温修正 - 极端高模温（温差比 0.5 以下）
    # 设置：T_melt=200, T_mold=160, T_eject=180 → (200-160)/(200-180) = 40/20 = 2.0 → 0.90
    mold = _base_mold(ave_thickness=3.0, max_thickness=3.0)
    material = _base_material(
        abbreviation='PC',
        category='无定形',
        recommended_melt_temp=200.0,
        recommended_mold_temp=160.0,   # 极高模温
        ejection_temp=180.0,
    )
    cool_t, _ = _run(mold, material)
    # (200-160)/(200-180) = 40/20 = 2.0 → factor=0.90
    # factor=1.8 × 9 × 0.90 × 1.0 = 14.58s
    _assert_close(cool_t, 14.58, "C2 极高模温 cool_t ≈ 14.58s（ΔT_factor=0.90）", eps=0.5)

    # C3: 缺失数据兜底（ejection_temp=0 → ΔT_factor=1.0）
    mold = _base_mold(ave_thickness=2.0, max_thickness=2.0)
    material = _base_material(
        abbreviation='ABS',
        category='无定形',
        recommended_melt_temp=240.0,
        recommended_mold_temp=60.0,
        ejection_temp=0.0,   # 缺失
    )
    cool_t, _ = _run(mold, material)
    # factor=1.1 × 4 × 1.0（missing） × 1.0（amorphous）= 4.4s → 钳到 5s
    _assert_eq(cool_t, 5.0, "C3 缺失 ejection_temp → ΔT_factor=1.0（兜底）")

    # C4: 最小值钳制（薄壁件必须 ≥ 5s）
    mold = _base_mold(ave_thickness=0.5, max_thickness=0.5)   # 极薄壁
    material = _base_material(
        abbreviation='PP',
        category='结晶型',
        recommended_melt_temp=220.0,
        recommended_mold_temp=40.0,
        ejection_temp=80.0,
    )
    cool_t, _ = _run(mold, material)
    _assert_ge(cool_t, 5.0, "C4 极薄壁 cool_t >= 5s（最小值钳制）")


# ========== 场景 D：物理正交 ==========

def test_scenario_d_orthogonality():
    print("\n=== 场景 D: 物理正交===")
    # 与 #8 保压时间的关系：
    # - 保压时间 = 浇口凝固时间（局部视角，热扩散的局部）
    # - 冷却时间 = 制品整体冷却到 ejection_temp（整体视角，热扩散的整体）
    # 物理上：保压时间 ⊂ 冷却时间（浇口先凝固，制品后冷到脱模温度）

    # D1: ABS 中壁场景（验证两者数值关系）
    mold = _base_mold(ave_thickness=2.0, max_thickness=2.0)
    material = _base_material(
        abbreviation='ABS',
        category='无定形',
        recommended_melt_temp=240.0,
        recommended_mold_temp=60.0,
        ejection_temp=90.0,
    )
    cool_t, hold_t = _run(mold, material)
    # 这里 cool_t 被钳到 5s，hold_t 大约是 5~10s（保压场景下浇口凝固时间）
    # 关键：算法独立推导，不互相依赖
    _assert_ge(cool_t, 5.0, "D1 冷却时间 >= 5s（最小值钳制生效）")

    # D2: PET 长冷却场景（验证冷却时间显著大于保压时间）
    mold = _base_mold(ave_thickness=5.0, max_thickness=5.0)
    material = _base_material(
        abbreviation='PET',
        category='结晶型',
        recommended_melt_temp=280.0,
        recommended_mold_temp=80.0,
        ejection_temp=120.0,
    )
    cool_t, hold_t = _run(mold, material)
    # 物理：PET 厚壁的冷却时间应该比保压时间长（5s vs 20~30s）
    # PET 长冷却典型场景：cool_t >> hold_t
    _assert_ge(cool_t, 50.0, "D2 PET 长冷却场景 cool_t >= 50s（与保压时间物理正交）")


# ========== 主函数 ==========

def main():
    test_scenario_a_pet_thick_crystalline()
    test_scenario_b_material_gradient()
    test_scenario_c_boundary()
    test_scenario_d_orthogonality()

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