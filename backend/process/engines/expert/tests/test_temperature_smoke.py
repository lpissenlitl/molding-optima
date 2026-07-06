"""
ProcessInitializer 温度族 #19+#20 smoke test（独立运行，不依赖 Django）

覆盖范围：
  场景 A - PP 通用件（直通 + 5 段 + melt=230）→ 基准场景
  场景 B - PA66 含水件（直通 + 5 段 + melt=280）→ I1 family_offset +5℃ 验证
  场景 C - PVC 热敏（锁闭 + 5 段 + melt=190）→ I1 family_offset -5℃ + I2 decrement 5℃ 验证
  场景 D - PC 高黏度（直通 + 5 段 + melt=300）→ I2 decrement 8℃ 验证
  场景 E - 8 段细颗粒（PP）→ I2 stages × 0.8 但上限 8℃ 验证
  场景 F - 边界钳制（F1 noz_temp 上限 / F2 段 N 下限 / F3 Tg 缺失兑底）
  场景 G - 直通 vs 锁闭对照（PP）→ nozzle_offset 修正验证
  场景 H - HDPE 5 段（PE family 解析验证）
  场景 I - 4 段 vs 10 段极端 stages 验证
  场景 J - 幂函数非线性 k=1.2 vs 线性 k=1.0 对比
  场景 K - 材料手册钳制（min/max_melt_temp 触发）→ I5 钳制日志验证
  场景 L - 字段全缺失兑底链
  场景 M - brl_temp_steps 顺序（sections[0]=喷嘴 / [1..N]=料筒段）
  场景 N - 计算与设计文档预期对比

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_temperature_smoke.py
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

# 启用 debug 日志以验证 logger.debug 输出
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(name)s: %(message)s')


# ========== 辅助：构造 context fixture ==========

def _machine(power_method='液压机', nozzle_type='直通型'):
    """标准海天级注塑机（液压+直通）"""
    return {
        'screw_diameter': 40,
        'max_set_injection_pressure': 150.0,
        'max_set_injection_velocity': 100.0,
        'max_set_holding_pressure': 100.0,
        'max_set_holding_velocity': 100.0,
        'max_set_screw_rotation_speed': 150.0,
        'max_set_metering_pressure': 20.0,
        'nozzle_type': nozzle_type,
        'power_method': power_method,
    }


def _base_mold(**overrides):
    """基础 ABS mold（5 段料筒）"""
    m = {
        'product_weight': 50.0,
        'runner_weight': 0.0,
        'ave_thickness': 2.0,
        'max_thickness': 2.0,
        'max_length': 100.0,
        'gate_type': '侧浇口',
        'barrel_temperature_stage': 5,
    }
    m.update(overrides)
    return m


def _base_material(**overrides):
    """基础 ABS 材料（带推荐熔体温度范围 + Tg）"""
    m = {
        'abbreviation': 'ABS',
        'category': '无定形',
        'recommended_melt_temp': 240.0,
        'recommended_mold_temp': 60.0,
        'ejection_temp': 90.0,
        'recommend_shear_linear_speed': 160.0,
        'recommend_back_pressure': 10.0,
        'melt_density': 0.95,
        'min_melt_temp': 220.0,
        'max_melt_temp': 260.0,
        'glass_transition_temp': 100.0,
    }
    m.update(overrides)
    return m


def _run(mold, material, machine=None, process_set=None):
    """
    跑一次 derive()，返回 (noz_temp, brl_temp_stg, brl_temp_steps)
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
    return params.process.noz_temp, params.process.brl_temp_stg, params.process.brl_temp_steps


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


def _assert_list_close(actual, expected, label, eps=0.5):
    if len(actual) != len(expected):
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: length mismatch actual={len(actual)}, expected={len(expected)}"
        )
        return
    for i, (a, e) in enumerate(zip(actual, expected)):
        if abs(a - e) > eps:
            _failures.append(
                f"  {FAIL}[FAIL]{NC} {label}[{i}]: expected={e}, actual={a}"
            )
            return
    _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual} ≈ {expected}")


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


# ========== 场景 A：PP 通用件（直通 + 5 段 + melt=230）基准场景 ==========

def test_scenario_a_pp_baseline():
    print("\n[场景 A] PP 通用件（直通 + 5 段 + melt=230）基准场景")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
    )
    # 推导：noz_offset_straight=-5 + family_offset[PP]=0 → 225
    _assert_eq(noz_temp, 225.0, 'A noz_temp（直通-5+family0=225）')
    _assert_eq(stg, 5, 'A brl_temp_stg')
    # 幂函数 k=1.2, decrement=10, melt=230
    # 预期 [230, 220, 207, 193, 177]
    _assert_list_close(steps, [230.0, 220.0, 207.0, 193.0, 177.0], 'A brl_temp_steps (幂函数 k=1.2)')


# ========== 场景 B：PA66 含水件（直通 + 5 段 + melt=280）I1 family_offset +5℃ 验证 ==========

def test_scenario_b_pa66_family_offset():
    print("\n[场景 B] PA66 含水件（直通 + 5 段 + melt=280）I1 family_offset +5℃ 验证")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PA66', recommended_melt_temp=280.0,
            min_melt_temp=270.0, max_melt_temp=290.0,
            glass_transition_temp=50.0,
        ),
    )
    # 推导：noz_offset_straight=-5 + family_offset[PA]=+5 → 280
    _assert_eq(noz_temp, 280.0, 'B noz_temp（直通-5+family+5=280）')
    # PA family_decrement=8
    _assert_list_close(steps, [280.0, 272.0, 262.0, 250.0, 238.0], 'B brl_temp_steps (PA decrement=8)')


# ========== 场景 C：PVC 热敏（锁闭 + 5 段 + melt=190）I1 -5℃ + I2 5℃ 验证 ==========

def test_scenario_c_pvc_thermal_sensitive():
    print("\n[场景 C] PVC 热敏（锁闭 + 5 段 + melt=190）I1 -5℃ + I2 5℃ 验证")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PVC', recommended_melt_temp=190.0,
            min_melt_temp=170.0, max_melt_temp=210.0,
            glass_transition_temp=80.0,
        ),
        machine=_machine(nozzle_type='锁闭型'),
    )
    # 推导：noz_offset_locking=0 + family_offset[PVC]=-5 → 185
    _assert_eq(noz_temp, 185.0, 'C noz_temp（锁闭0+family-5=185）')
    # PVC family_decrement=5 极平缓
    _assert_list_close(steps, [190.0, 185.0, 178.0, 171.0, 164.0], 'C brl_temp_steps (PVC decrement=5)')


# ========== 场景 D：PC 高黏度（直通 + 5 段 + melt=300）I2 8℃ 验证 ==========

def test_scenario_d_pc_high_viscosity():
    print("\n[场景 D] PC 高黏度（直通 + 5 段 + melt=300）I2 8℃ 验证")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PC', recommended_melt_temp=300.0,
            min_melt_temp=280.0, max_melt_temp=320.0,
            glass_transition_temp=150.0,
        ),
    )
    # 推导：noz_offset_straight=-5 + family_offset[PC]=0 → 295
    _assert_eq(noz_temp, 295.0, 'D noz_temp（直通-5+family0=295）')
    # PC family_decrement=8 平缓
    _assert_list_close(steps, [300.0, 292.0, 282.0, 270.0, 258.0], 'D brl_temp_steps (PC decrement=8)')


# ========== 场景 E：8 段细颗粒（PP）stages × 0.8 但上限 8℃ 验证 ==========

def test_scenario_e_8stages_fine_grain():
    print("\n[场景 E] PP 8 段细颗粒 stages × 0.8 但上限 8℃ 验证")
    noz_temp, stg, steps = _run(
        mold=_base_mold(barrel_temperature_stage=8),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
    )
    _assert_eq(stg, 8, 'E brl_temp_stg')
    # 8 段：decrement = min(10 × 0.8, 8) = 8
    # raw: [230, 222, 212, 200, 188, 175, 161, 150]
    # 段 8 钳制：Tg+30=20, melt-60=170, max(20, 170)=170
    # 150 < 170 → 钳到 170
    _assert_list_close(
        steps,
        [230.0, 222.0, 212.0, 200.0, 188.0, 175.0, 161.0, 170.0],
        'E brl_temp_steps (段 8 钳到 Tg+30/melt-60)',
    )


# ========== 场景 F：边界钳制（3 个子场景）==========

def test_scenario_f1_noz_temp_clamp_upper():
    """F1: noz_temp_raw 超过 max_melt + tolerance → 钳到上限"""
    print("\n[场景 F1] noz_temp 上限钳制（ABS melt=320 max=280+10=290）")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='ABS', recommended_melt_temp=320.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=100.0,
        ),
    )
    # raw = 320 + (-5) + 0 = 315；max+10=290；315 > 290 → 钳到 290
    _assert_eq(noz_temp, 290.0, 'F1 noz_temp 钳到 max+10=290')


def test_scenario_f2_segment_n_clamp():
    """F2: 段 N 低于 Tg+30 → 钳到 Tg+30"""
    print("\n[场景 F2] 段 N 下限钳制（极端 PP 5 段，raw 段 N < Tg+30）")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=200.0,  # Tg=200（极端高）
        ),
    )
    # Tg+30=230=melt → 段 N 至少 230（但 ≤ melt-5=225）
    # 钳上限 melt-5=225
    _assert_le(steps[-1], 225.0, 'F2 段 N ≤ melt-5=225（防料口过热）')
    _assert_ge(steps[-1], 230.0 - 60.0, 'F2 段 N ≥ melt-60=170')


def test_scenario_f3_tg_missing_fallback():
    """F3: Tg 字段缺失 → 默认下限用 melt-60"""
    print("\n[场景 F3] Tg 字段缺失兑底（默认 melt-60）")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            # glass_transition_temp 缺失
        ),
    )
    # 5 段：raw [230, 220, 207, 193, 177]
    # 段 N raw 177 vs melt-60=170, 177 > 170 → 不钳
    _assert_eq(steps[-1], 177.0, 'F3 段 N 不触发钳制（Tg 缺失兑底 melt-60=170, 177>170）')


# ========== 场景 G：直通 vs 锁闭对照（PP）==========

def test_scenario_g_straight_vs_locking():
    print("\n[场景 G] 直通 vs 锁闭喷嘴对照（PP 5 段）")
    noz_straight, _, _ = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
        machine=_machine(nozzle_type='直通型'),
    )
    noz_locking, _, _ = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
        machine=_machine(nozzle_type='锁闭型'),
    )
    # 直通 -5, 锁闭 0
    _assert_eq(noz_straight, 225.0, 'G 直通 noz_temp=225')
    _assert_eq(noz_locking, 230.0, 'G 锁闭 noz_temp=230')
    _assert_eq(noz_locking - noz_straight, 5.0, 'G 锁闭 - 直通 = 5（差异=1.0 倍 nozzle_offset）')


# ========== 场景 H：HDPE 5 段（PE family 解析）==========

def test_scenario_h_hdpe_pe_family():
    print("\n[场景 H] HDPE 5 段（_parse_family 把 HDPE→PE 验证）")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='HDPE', recommended_melt_temp=200.0,
            min_melt_temp=180.0, max_melt_temp=240.0,
            glass_transition_temp=-100.0,
        ),
    )
    # HDPE → PE → family_offset[PE]=0 → noz = 200 - 5 = 195
    _assert_eq(noz_temp, 195.0, 'H HDPE→PE 直通 noz_temp=195')
    # PE family_decrement=10
    # raw [200, 190, 178, 163, 147]
    # 段 N raw 147 vs Tg+30=-70 vs melt-60=140, max(-70, 140)=140, 147>140 → 不钳
    _assert_list_close(steps, [200.0, 190.0, 177.0, 163.0, 147.0], 'H HDPE 5 段递减')


# ========== 场景 I：4 段（min）vs 10 段（max）极端 stages ==========

def test_scenario_i_extreme_stages():
    print("\n[场景 I] 4 段（min）vs 10 段（max）极端 stages 验证")
    # 4 段
    noz_4, stg_4, steps_4 = _run(
        mold=_base_mold(barrel_temperature_stage=4),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
    )
    # 10 段（> 7 阈值走细颗粒）
    noz_10, stg_10, steps_10 = _run(
        mold=_base_mold(barrel_temperature_stage=10),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
    )
    _assert_eq(stg_4, 4, 'I4 stg=4')
    _assert_eq(stg_10, 10, 'I10 stg=10')
    # 4 段：decrement=10, raw [230, 220, 207, 193]
    _assert_list_close(steps_4, [230.0, 220.0, 207.0, 193.0], 'I4 brl_temp_steps')
    # 10 段：decrement=8（10×0.8），raw [230, 222, 212, 200, 188, 175, 161, 150, ...]
    # 段 N 钳制：Tg+30=20, melt-60=170, 150 < 170 → 钳
    _assert_eq(steps_10[0], 230.0, 'I10 段 1 = melt（钳上限）')
    _assert_eq(steps_10[-1], 170.0, 'I10 段 N 钳到 max(Tg+30, melt-60)=170')


# ========== 场景 J：幂函数非线性 k=1.2 vs 线性 k=1.0 对比 ==========

def test_scenario_j_power_function_vs_linear():
    print("\n[场景 J] 幂函数 k=1.2 非线性 vs 线性（间接验证）")
    # 5 段 PP 230, decrement=10
    # 线性 k=1.0 预期：[230, 220, 210, 200, 190]
    # 幂函数 k=1.2 实际：[230, 220, 207, 193, 177]
    # 段 3 差异最大：幂函数 193 vs 线性 200，差 7
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
    )
    # 幂函数 k=1.2
    _assert_list_close(steps, [230.0, 220.0, 207.0, 193.0, 177.0], 'J 幂函数 k=1.2 验证')
    # 段 3：幂函数 < 线性（k>1 加速递减）
    linear_step3 = 230 - 3 * 10
    _assert_lt = steps[3] < linear_step3
    if _assert_lt:
        _passes.append(f"  {PASS}[PASS]{NC} J 段 3 幂函数 {steps[3]} < 线性 {linear_step3}（k=1.2 加速递减）")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} J 段 3 幂函数 {steps[3]} >= 线性 {linear_step3}"
        )


# ========== 场景 K：材料手册钳制（min/max_melt_temp 触发）==========

def test_scenario_k_material_handbook_clamp():
    print("\n[场景 K] 材料手册钳制（min/max_melt_temp 触发）")
    # raw noz=320+(-5)+0=315，max=280+10=290，钳到 290
    noz, _, _ = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='ABS', recommended_melt_temp=320.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=100.0,
        ),
    )
    _assert_eq(noz, 290.0, 'K noz_temp 钳到 max_melt+tol=290')

    # 反向：raw noz=180+(-5)+0=175，min=190-10=180，钳到 180
    noz_low, _, _ = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='ABS', recommended_melt_temp=180.0,
            min_melt_temp=190.0, max_melt_temp=240.0,
            glass_transition_temp=100.0,
        ),
    )
    _assert_eq(noz_low, 180.0, 'K noz_temp 钳到 min_melt-tol=180')


# ========== 场景 L：字段全缺失兑底链 ==========

def test_scenario_l_all_fields_missing():
    print("\n[场景 L] 字段全缺失兑底链（glass_transition_temp 缺失 + min/max 缺失）")
    noz_temp, stg, steps = _run(
        mold=_base_mold(),
        material={
            'abbreviation': 'PP', 'category': '无定形',
            'recommended_melt_temp': 230.0,
            'melt_density': 0.91,
            # min_melt_temp / max_melt_temp / glass_transition_temp 全缺失
        },
    )
    # 兑底：min=melt-40=190, max=melt+40=270, Tg=-999
    # noz_offset=230-5=225, in [190-10, 270+10]=[180, 280], 不钳
    _assert_eq(noz_temp, 225.0, 'L 字段全缺失兑底链 noz_temp=225')
    # 5 段：decrement=10, k=1.2, Tg=-999 兑底用 melt-60=170
    # raw [230, 220, 207, 193, 177], 段 N 177 > 170 → 不钳
    _assert_list_close(steps, [230.0, 220.0, 207.0, 193.0, 177.0], 'L brl_temp_steps 兑底链')


# ========== 场景 M：brl_temp_steps 顺序（与 process_transformer 对齐）==========

def test_scenario_m_steps_order():
    print("\n[场景 M] brl_temp_steps 顺序（与 process_transformer.py L113-118 对齐：sections[0]=喷嘴 / [1..N]=料筒段）")
    # process_transformer.py:
    #   flat["noz_temp"] = temp_sections[0]
    #   flat[f"brl_temp_{i}"] = temp_sections[i]   (i=1..9)
    # 所以 brl_temp_steps[0] = brl_temp_1（最热，紧邻喷嘴）
    _, _, steps = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
    )
    # 验证：steps[0] 最热（接近 melt），steps[-1] 最冷（远离 melt）
    _assert_eq(steps[0], 230.0, 'M 段 1（紧邻喷嘴）= melt=230（最热）')
    _assert_lt_last = steps[-1] < steps[0]
    if _assert_lt_last:
        _passes.append(f"  {PASS}[PASS]{NC} M 段 N={steps[-1]} < 段 1={steps[0]}（递减方向正确）")
    else:
        _failures.append(f"  {FAIL}[FAIL]{NC} M 段 N={steps[-1]} >= 段 1={steps[0]}（递减方向错误）")


# ========== 场景 N：与设计文档 §7 场景完全一致 ==========

def test_scenario_n_design_doc_consistency():
    print("\n[场景 N] 与设计文档 §7 场景验证（5 段/8 段全场景）")
    # §7.1 PP 通用件
    _, _, steps_a = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PP', recommended_melt_temp=230.0,
            min_melt_temp=200.0, max_melt_temp=280.0,
            glass_transition_temp=-10.0,
        ),
    )
    # §7.2 PA66
    _, _, steps_b = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PA66', recommended_melt_temp=280.0,
            min_melt_temp=270.0, max_melt_temp=290.0,
            glass_transition_temp=50.0,
        ),
    )
    # §7.3 PVC
    _, _, steps_c = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PVC', recommended_melt_temp=190.0,
            min_melt_temp=170.0, max_melt_temp=210.0,
            glass_transition_temp=80.0,
        ),
        machine=_machine(nozzle_type='锁闭型'),
    )
    # §7.4 PC
    _, _, steps_d = _run(
        mold=_base_mold(),
        material=_base_material(
            abbreviation='PC', recommended_melt_temp=300.0,
            min_melt_temp=280.0, max_melt_temp=320.0,
            glass_transition_temp=150.0,
        ),
    )
    # 与设计文档 §7 完全一致（±1℃ 误差容差）
    # 注：4^1.2 ≈ 5.278（非线性幂函数），代码会经过 round(_,1) + round(_,0) 两层，
    # 另外 Python round 使用 banker's rounding（half-to-even）。
    # 例如：178.513 → round(_,1) → 178.5 → round(_,0) → 178.0（偶数方向）
    # PP:    T[3] = 192.63 → 192.6 → 193；T[4] = 177.22 → 177.2 → 177
    # PA66:  T[3] = 250.10 → 250.1 → 250；T[4] = 237.78 → 237.8 → 238
    # PVC:   T[3] = 171.31 → 171.3 → 171；T[4] = 163.61 → 163.6 → 164
    # PC:    T[3] = 270.10 → 270.1 → 270；T[4] = 257.78 → 257.8 → 258
    _assert_list_close(steps_a, [230.0, 220.0, 207.0, 193.0, 177.0], 'N §7.1 PP 5 段', eps=0.5)
    _assert_list_close(steps_b, [280.0, 272.0, 262.0, 250.0, 238.0], 'N §7.2 PA66 5 段', eps=0.5)
    _assert_list_close(steps_c, [190.0, 185.0, 178.0, 171.0, 164.0], 'N §7.3 PVC 5 段', eps=0.5)
    _assert_list_close(steps_d, [300.0, 292.0, 282.0, 270.0, 258.0], 'N §7.4 PC 5 段', eps=0.5)


# ========== 主入口 ==========

if __name__ == '__main__':
    test_scenario_a_pp_baseline()
    test_scenario_b_pa66_family_offset()
    test_scenario_c_pvc_thermal_sensitive()
    test_scenario_d_pc_high_viscosity()
    test_scenario_e_8stages_fine_grain()
    test_scenario_f1_noz_temp_clamp_upper()
    test_scenario_f2_segment_n_clamp()
    test_scenario_f3_tg_missing_fallback()
    test_scenario_g_straight_vs_locking()
    test_scenario_h_hdpe_pe_family()
    test_scenario_i_extreme_stages()
    test_scenario_j_power_function_vs_linear()
    test_scenario_k_material_handbook_clamp()
    test_scenario_l_all_fields_missing()
    test_scenario_m_steps_order()
    test_scenario_n_design_doc_consistency()

    # 抑制 debug 日志输出
    print("\n" + "=" * 70)
    print("温度族 #19+#20 smoke test 汇总")
    print("=" * 70)
    for line in _passes:
        print(line)
    for line in _failures:
        print(line)

    print("=" * 70)
    print(f"通过: {len(_passes)}    失败: {len(_failures)}")
    print("=" * 70)

    if _failures:
        raise SystemExit(1)
    print("✅ 全部 #19+#20 温度族 smoke test 通过！")

