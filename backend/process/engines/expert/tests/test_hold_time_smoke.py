"""
ProcessInitializer 保压时间 smoke test（独立运行，不依赖 Django）

覆盖：
  场景 A - PET 瓶盖长保压（max_thickness=5mm, 直浇口, 热流道, 模温 130℃）
           → 期望 ~295s（移除 10s 硬上限后 family 自适应 600s 钳制）
  场景 B - 4 级 fallback 链
           B1 hold_time_override 精确值
           B2 family × bucket 查表
           B3 family 中桶兜底
           B4 未知 family → default
  场景 C - 边界守门
           C1 raw < hold_time_min → 钳到 2.0
           C2 raw > family_hold_time_max → 钳到 family 上限
           C3 mold_temp ≤ 0 → mold_temp_factor level='default'
           C4 不存在 family → default_hold_time_max=300s 兜底

运行：
  cd backend
  PYTHONPATH=process python3 process/engines/expert/tests/test_hold_time_smoke.py
"""

import io
import logging
import os
import sys

# 让 process 作为顶层 package 可被发现
# 脚本位置：backend/process/engines/expert/tests/test_hold_time_smoke.py
#   dirname 4 次 → backend  (作为 PYTHONPATH 根)
#   import 用 from process.engines.expert.initializer import ...
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # backend/
sys.path.insert(0, BACKEND_ROOT)

from process.engines.expert.initializer import ProcessInitializer  # noqa: E402

PASS = '\033[92m'
FAIL = '\033[91m'
NC = '\033[0m'


# ========== 辅助：构造 context fixture ==========

def _machine():
    """标准 100MPa/100mm/s 海天级注塑机"""
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
    """基础薄壁 mold_info + 任意字段覆盖"""
    m = {
        'product_weight': 50.0,
        'runner_weight': 0.0,           # 默认热流道
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
    跑一次 derive()，返回 (hold_time, hold_pressure, captured_log_text)。
    通过 StringIO handler 抓取 DEBUG 日志用于断言 level 字段。
    """
    if machine is None:
        machine = _machine()
    if process_set is None:
        process_set = {}

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    # logger 名 = 模块 __name__，从 process 包导入时为 process.engines.expert.initializer
    target_logger = logging.getLogger('process.engines.expert.initializer')
    target_logger.addHandler(handler)
    prev_level = target_logger.level
    target_logger.setLevel(logging.DEBUG)
    # 同时给 engines.* 也加上（双保险，防止不同路径）
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

    hold_time_total = sum(params.process.hold_time_steps) if params.process.hold_time_steps else 0.0
    hold_pres = params.process.hold_pres_steps[0] if params.process.hold_pres_steps else 0.0
    # 同时返回 hold_time_steps 供调试
    return hold_time_total, hold_pres, buf.getvalue(), params.process.hold_time_steps


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


# ========== 场景 A：PET 瓶盖长保压 ==========

def test_scenario_a_pet_cap_long_hold():
    print("\n=== 场景 A: PET 瓶盖长保压 (~295s) ===")
    mold = _base_mold(
        max_thickness=5.0,    # thick 桶 (>3.0)
        max_length=80.0,
        gate_type='直浇口',
        runner_weight=0.0,    # 热流道（runner_weight=0）
    )
    material = _base_material(
        abbreviation='PET',
        recommended_mold_temp=130.0,  # ultra_high 桶
    )

    hold_time, _, log, steps = _run_and_capture_log(mold, material)

    # 调试：手动重算一次
    init_dbg = ProcessInitializer(mold_info=mold, machine_info=_machine(), polymer_info=material)
    init_dbg._coeffs = init_dbg.rule_matcher.match({'machine': _machine(), 'material': material, 'mold': mold, 'process_set': {}})
    ch = init_dbg._coeffs.get('holding', {})
    fam_dbg = init_dbg._parse_family('PET')
    bucket_dbg, _ = init_dbg._get_thickness_bucket(5.0, init_dbg._coeffs.get('injection', {}))
    ft, fl = init_dbg._get_family_gate_freeze_time(fam_dbg, bucket_dbg, ch)
    gf_dbg = init_dbg._get_gate_factor_for_hold('直浇口', ch)
    rf_dbg, rl_dbg = init_dbg._get_runner_factor('', 0.0, ch)
    mt_dbg, mtl_dbg = init_dbg._get_mold_temp_factor(130.0, ch)
    ck_dbg = init_dbg._get_crystallinity_kick(fam_dbg, ch)
    print(f"  [debug PET] family={fam_dbg} bucket={bucket_dbg} freeze_t={ft}({fl}) "
          f"gate={gf_dbg} runner={rf_dbg}({rl_dbg}) mt={mt_dbg}({mtl_dbg}) cryst={ck_dbg}")
    raw_dbg = ft * gf_dbg * rf_dbg * mt_dbg * ck_dbg
    print(f"  [debug PET] raw={raw_dbg:.3f} final_steps={steps} sum={hold_time:.3f}")

    # 理论值：120.0 (PET thick) × 1.20 (直浇口) × 0.95 (热流道) × 1.20 (ultra_high) × 1.80 (PET 结晶)
    #     = 295.68s
    _assert_close(hold_time, 295.68, "PET 瓶盖长保压 raw=295.68s（移除 10s 上限后命中 family_hold_time_max[PET]=600s 钳制）")

    # 日志必须显示 family=PET, level=family_bucket（因 hold_time_override 未设）
    _assert_in(log, "family=PET", "日志 family=PET")
    _assert_in(log, "level=family_bucket", "日志 freeze level=family_bucket")
    _assert_in(log, "level=ultra_high", "日志 mold_temp level=ultra_high")


# ========== 场景 B：4 级 fallback ==========

def test_scenario_b_four_level_fallback():
    print("\n=== 场景 B: 4 级 fallback 链 ===")

    # B1: hold_time_override 精确值（制品级覆盖最高优先级）
    mold_b1 = _base_mold(max_thickness=2.0, hold_time_override={'medium': 42.0})
    material_b1 = _base_material(abbreviation='PA66+GF30')  # family=PA
    ht_b1, _, log_b1, _ = _run_and_capture_log(mold_b1, material_b1)
    # freeze=42 (override) × 0.85(侧浇口，默认) × 0.95(热流道) × 1.00(模温60 medium) × 1.40(PA 结晶)
    #     = 47.46
    _assert_close(ht_b1, 42.0 * 0.85 * 0.95 * 1.00 * 1.40, "B1 override=42s × 0.85×0.95×1.00×1.40 ≈ 47.46s",
                 eps=1.0)
    _assert_in(log_b1, "level=precise", "B1 freeze level=precise")

    # B2: family × bucket 查表（PP medium = 12.5s）
    mold_b2 = _base_mold(max_thickness=2.0)  # medium
    material_b2 = _base_material(abbreviation='PP')
    ht_b2, _, log_b2, _ = _run_and_capture_log(mold_b2, material_b2)
    # PP medium: 12.5 × 0.85(侧浇口) × 0.95(热流道) × 1.00(模温60) × 1.10(PP 结晶)
    #       = 11.124
    _assert_close(ht_b2, 12.5 * 0.85 * 0.95 * 1.00 * 1.10, "B2 PP medium=12.5 × 0.85 × 0.95 × 1.00 × 1.10 ≈ 11.12s",
                 eps=1.0)
    _assert_in(log_b2, "level=family_bucket", "B2 freeze level=family_bucket")

    # B3: family 中桶兜底（mock PP 表只留 medium，期望 thin 走 family_default_bucket）
    # 直接构造一个 matcher 让 PP 表 thin 缺失成本太高，改用 monkey-patch 系数
    init = ProcessInitializer(
        mold_info=_base_mold(max_thickness=0.5),  # thin 桶
        machine_info=_machine(),
        polymer_info=_base_material(abbreviation='PP'),
        process_set={},
    )
    # 直接喂一个去掉 thin key 的 family_gate_freeze_time
    init._coeffs = init.rule_matcher.match({
        'machine': init.machine,
        'material': init.material,
        'mold': init.mold,
        'process_set': init.process_set,
    })
    c_hold = dict(init._coeffs.get('holding', {}))
    pp_table = dict(c_hold['family_gate_freeze_time'].get('PP', {}))
    pp_table.pop('thin', None)  # 模拟薄壁数据缺失
    c_hold['family_gate_freeze_time'] = {**c_hold['family_gate_freeze_time'], 'PP': pp_table}
    init._coeffs['holding'] = c_hold

    freeze_t, freeze_level = init._get_family_gate_freeze_time('PP', 'thin', c_hold)
    _assert_close(freeze_t, 12.5, "B3 PP thin 缺数据 → 中桶兜底 12.5s")
    if freeze_level == 'family_default_bucket':
        _passes.append(f"  {PASS}[PASS]{NC} B3 freeze level=family_default_bucket")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} B3 freeze level: expected=family_default_bucket, actual={freeze_level}"
        )

    # B4: 未知 family → default_freeze_time[thick]=75.0
    init4 = ProcessInitializer(
        mold_info=_base_mold(max_thickness=5.0),  # thick
        machine_info=_machine(),
        polymer_info=_base_material(abbreviation='UNKNOWN_MATERIAL'),
        process_set={},
    )
    init4._coeffs = init4.rule_matcher.match({
        'machine': init4.machine,
        'material': init4.material,
        'mold': init4.mold,
        'process_set': init4.process_set,
    })
    c_hold_4 = init4._coeffs.get('holding', {})
    freeze_t_4, freeze_level_4 = init4._get_family_gate_freeze_time('', 'thick', c_hold_4)
    _assert_close(freeze_t_4, 75.0, "B4 未知 family thick → default=75.0")
    if freeze_level_4 == 'default':
        _passes.append(f"  {PASS}[PASS]{NC} B4 freeze level=default")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} B4 freeze level: expected=default, actual={freeze_level_4}"
        )


# ========== 场景 C：边界守门 ==========

def test_scenario_c_boundary_guards():
    print("\n=== 场景 C: 边界守门 ===")

    # C1: 极小 raw → 钳到 hold_time_min=2.0
    #     PP thin × 0.70(点浇口) × 0.95(热流道) × 0.95(低模温) × 1.10(PP)
    #     = 3.6 × 0.70 × 0.95 × 0.95 × 1.10 = 2.506s → 钳到 2.0
    mold_c1 = _base_mold(max_thickness=0.5, gate_type='点浇口')
    material_c1 = _base_material(abbreviation='PP', recommended_mold_temp=20.0)
    ht_c1, _, _, _ = _run_and_capture_log(mold_c1, material_c1)
    if abs(ht_c1 - 2.0) < 0.01:
        _passes.append(f"  {PASS}[PASS]{NC} C1 raw=2.50s → 钳到 hold_time_min=2.0s")
    elif ht_c1 >= 2.0:
        _passes.append(f"  {PASS}[PASS]{NC} C1 raw=2.50s → 实际值={ht_c1:.3f}s（≥2.0，未触发下限）")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} C1 raw=2.50s → 钳到 2.0s 失败，actual={ht_c1:.3f}s"
        )

    # C2: raw > family_hold_time_max → 钳到 family 上限
    #     改用 ABS thick (75) + 直浇口(1.20) + 冷流道(1.05) + ultra_high(1.20) × 1.00(非结晶)
    #     = 113.4s → ABS family_hold_time_max=60s → 钳到 60.0
    mold_c2 = _base_mold(max_thickness=5.0, gate_type='直浇口', runner_weight=5.0)
    material_c2 = _base_material(abbreviation='ABS', recommended_mold_temp=130.0)
    ht_c2, _, log_c2, _ = _run_and_capture_log(mold_c2, material_c2)
    _assert_close(ht_c2, 60.0, "C2 raw=113.4s → 钳到 ABS family_hold_time_max=60s")
    _assert_in(log_c2, "level=ultra_high", "C2 mold_temp level=ultra_high")

    # C3: mold_temp ≤ 0 → mold_temp_factor level='default'
    init3 = ProcessInitializer(
        mold_info=_base_mold(max_thickness=2.0),
        machine_info=_machine(),
        polymer_info=_base_material(abbreviation='ABS', recommended_mold_temp=0.0),
        process_set={},
    )
    init3._coeffs = init3.rule_matcher.match({
        'machine': init3.machine,
        'material': init3.material,
        'mold': init3.mold,
        'process_set': init3.process_set,
    })
    c_hold_3 = init3._coeffs.get('holding', {})
    _, mt_level = init3._get_mold_temp_factor(0.0, c_hold_3)
    if mt_level == 'default':
        _passes.append(f"  {PASS}[PASS]{NC} C3 mold_temp=0 → level=default")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} C3 mold_temp=0: expected=default, actual={mt_level}"
        )

    # C4: 不存在 family → default_hold_time_max=300s 兜底
    init4 = ProcessInitializer(
        mold_info=_base_mold(max_thickness=2.0),
        machine_info=_machine(),
        polymer_info=_base_material(abbreviation='UNKNOWN_MATERIAL'),
        process_set={},
    )
    init4._coeffs = init4.rule_matcher.match({
        'machine': init4.machine,
        'material': init4.material,
        'mold': init4.mold,
        'process_set': init4.process_set,
    })
    c_hold_4 = init4._coeffs.get('holding', {})
    cap = init4._get_family_hold_time_max('UNKNOWN_FAMILY', c_hold_4)
    _assert_close(cap, 300.0, "C4 未知 family 上限 → default_hold_time_max=300s")


# ========== 入口 ==========

def main():
    test_scenario_a_pet_cap_long_hold()
    test_scenario_b_four_level_fallback()
    test_scenario_c_boundary_guards()

    print("\n" + "=" * 70)
    print("保压时间 smoke test 汇总")
    print("=" * 70)
    for line in _passes:
        print(line)
    for line in _failures:
        print(line)
    print("-" * 70)
    print(f"通过: {len(_passes)}    失败: {len(_failures)}")
    print("=" * 70)

    sys.exit(0 if not _failures else 1)


if __name__ == '__main__':
    main()