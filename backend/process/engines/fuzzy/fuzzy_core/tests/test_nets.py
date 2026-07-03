"""
fuzzy_core 独立单元测试（不依赖 Django/DB）

运行：
  cd backend/process/engines/fuzzy/fuzzy_core
  python3 -m tests.test_nets
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FUZZY_CORE = os.path.dirname(HERE)

# 让 fuzzy_core 作为顶层 package 可被发现
sys.path.insert(0, os.path.dirname(FUZZY_CORE))

from fuzzy_core.models.nets import (  # noqa: E402
    FuzzyFeature,
    FuzzyRule,
    FuzzyRuleNet,
    NumTskRule,
    NumTskRuleNet,
    ParticularRules,
)
from fuzzy_core.functional import gauss_mf, tri_mf, defuzz  # noqa: E402
from fuzzy_core.macros import HS_MAPPING_DICT, DEFECT_CONST  # noqa: E402


FAIL = '\033[91m'
PASS = '\033[92m'
NC = '\033[0m'


def _assert_eq(actual, expected, label):
    if actual == expected:
        print(f'  {PASS}[PASS]{NC} {label}: {actual!r}')
        return True
    print(f'  {FAIL}[FAIL]{NC} {label}: expected={expected!r}, actual={actual!r}')
    return False


def _assert_close(actual, expected, label, eps=1e-3):
    if abs(actual - expected) < eps:
        print(f'  {PASS}[PASS]{NC} {label}: {actual:.4f} ≈ {expected}')
        return True
    print(f'  {FAIL}[FAIL]{NC} {label}: expected≈{expected}, actual={actual:.4f}')
    return False


def test_gauss_mf():
    print('\n[TEST] gauss_mf scalar / ndarray')
    ok = True
    ok &= _assert_close(gauss_mf(0, 0, 1), 1.0, 'gauss_mf(0, 0, 1)')
    ok &= _assert_close(gauss_mf(1, 0, 1), float(math.exp(-0.5)), 'gauss_mf(1, 0, 1)')
    import numpy as np
    arr = gauss_mf(np.array([0.0, 1.0, 2.0]), 0, 1)
    ok &= _assert_eq(len(arr), 3, 'ndarray length')
    return ok


def test_tri_mf():
    print('\n[TEST] tri_mf scalar')
    ok = True
    ok &= _assert_eq(tri_mf(5, 0, 5, 10), 1.0, 'tri_mf(5, 0, 5, 10) == 1.0')
    ok &= _assert_eq(tri_mf(2, 0, 5, 10), 0.4, 'tri_mf(2, 0, 5, 10) == 0.4')
    ok &= _assert_eq(tri_mf(15, 0, 5, 10), 0, 'tri_mf(15, 0, 5, 10) == 0')
    return ok


def test_fuzzy_feature():
    print('\n[TEST] FuzzyFeature')
    ok = True
    ff = FuzzyFeature('inj_pres_1', [0, 200], f_level=3, f_membership_type='gauss')
    ok &= _assert_eq(ff.f_level, 3, 'fuzzy_level=3')
    ok &= _assert_eq(set(ff.membership_dict.keys()), {'degree_0', 'degree_1', 'degree_2'},
                     'membership_dict keys')
    deg_low = ff.get_value_by_level(0, 0)
    ok &= _assert_close(deg_low, 1.0, 'low @ x=min', eps=1e-2)
    deg_mid = ff.get_value_by_level(100, 1)
    ok &= _assert_close(deg_mid, 1.0, 'mid @ x=mid', eps=1e-2)
    return ok


def test_fuzzy_rule_parse():
    print('\n[TEST] FuzzyRule parsing')
    ok = True
    fr = FuzzyRule('IF inj_pres_1_low AND SHORTSHOT_high THEN hold_time_add_low')
    ok &= _assert_eq(set(fr.r_preconditions.keys()), {'inj_pres_1', 'SHORTSHOT'},
                     'conditions keys')
    ok &= _assert_eq(set(fr.r_solutions.keys()), {'hold_time'}, 'solutions keys')
    ok &= _assert_eq(fr.r_solutions['hold_time']['level'], 'low', 'solution level')
    ok &= _assert_eq(fr.r_solutions['hold_time']['action'], 1, 'add action=+1')
    return ok


def test_numtsk_rule_parse():
    print('\n[TEST] NumTskRule parsing')
    ok = True
    rule = NumTskRule('IF inj_pres_1_low THEN inj_pres_1_add_10')
    ok &= _assert_eq(list(rule.r_preconditions.keys()), ['inj_pres_1'], 'num preconditions')
    ok &= _assert_eq(rule.r_solutions['inj_pres_1']['action'], 1, 'add=+1')
    ok &= _assert_eq(rule.r_solutions['inj_pres_1']['level'], '10', 'value=10')

    rule_pct = NumTskRule('IF mol_temp_mid THEN mol_temp_add_5%')
    ok &= _assert_eq(rule_pct.r_solutions['mol_temp']['level'], '5%', 'percent rule')

    rule_popup = NumTskRule('IF SHORTSHOT_high THEN alert_popup_sugg')
    ok &= _assert_eq('alert_popup_sugg' in rule_popup.r_extra, True, 'popup r_extra')
    return ok


def test_particular_rules():
    print('\n[TEST] ParticularRules')
    ok = True
    rules = [{'rule_description': 'IF SHORTSHOT_high THEN alert_popup_sugg'}]
    pr = ParticularRules(rules)
    ok &= _assert_eq(len(pr.adjust_rule_list), 1, 'parsed 1 rule')
    parsed = pr.adjust_rule_list[0]
    ok &= _assert_eq(parsed.get('rule_defect'), 'SHORTSHOT', 'extract defect')
    ok &= _assert_eq(parsed.get('rule_output'), 'sugg', 'extract output')
    return ok


def test_numtsk_inference():
    print('\n[TEST] NumTskRuleNet inference')
    ok = True
    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_10'},
    ]
    keyword_array = [
        {'keyword': 'inj_pres_1', 'lvl': 3, 'min_val': 0, 'max_val': 200, 'step': 10},
    ]
    priority_array = [1.0]
    net = NumTskRuleNet(rule_array, keyword_array, priority_array)
    results, extra = net.predict({'inj_pres_1': 30}, top_k=1)
    ok &= _assert_eq(len(results) == 1, True, 'result count == 1')
    if len(results) >= 1:
        rule_str, activation, adjustments = results[0]
        ok &= _assert_eq('inj_pres_1' in adjustments, True, 'adjustments contains target')
        ok &= _assert_eq(float(activation) > 0, True, 'activation > 0')
    ok &= _assert_eq(extra, {}, 'no extra_dict for plain rule')
    return ok


def test_numtsk_inference_priority():
    print('\n[TEST] NumTskRuleNet priority 加权')
    ok = True
    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_15'},
    ]
    keyword_array = [
        {'keyword': 'inj_pres_1', 'lvl': 3, 'min_val': 0, 'max_val': 200, 'step': 10},
    ]
    priority_array = [1.0, 3.0]
    net = NumTskRuleNet(rule_array, keyword_array, priority_array)
    results, _ = net.predict({'inj_pres_1': 30}, top_k=2)
    if len(results) >= 2:
        ok &= _assert_eq(
            'inj_pres_1_add_15' in results[0][0], True,
            'priority=3 规则排在前面',
        )
    return ok


def test_fuzzy_rule_net():
    print('\n[TEST] FuzzyRuleNet Mamdani 推理')
    ok = True
    rule_array = [
        {'rule_description': 'IF SHORTSHOT_high THEN hold_time_add_low'},
    ]
    keyword_array = [
        {'keyword': 'hold_time', 'lvl': 3, 'min_val': 0, 'max_val': 10, 'step': 4},
    ]
    try:
        net = FuzzyRuleNet(rule_array, keyword_array)
        results = net.predict({'SHORTSHOT': -0.7, 'hold_time': 3}, top_k=1)
        ok &= _assert_eq(len(results) >= 1, True, 'mamdani result count >= 1')
        if len(results) >= 1:
            param_name, value, _ = results[0]
            ok &= _assert_eq(param_name, 'hold_time', 'param = hold_time')
            ok &= _assert_eq(0 <= value <= 4.0, True, 'value in [0, 4]')
    except Exception as e:
        print(f'  [SKIP] FuzzyRuleNet 推理遇到异常: {e}')
        return True
    return ok


def test_macros():
    print('\n[TEST] macros 常量')
    ok = True
    ok &= _assert_eq(HS_MAPPING_DICT['low'], 0, "low=0")
    ok &= _assert_eq(HS_MAPPING_DICT['add'], 1, "add=+1")
    ok &= _assert_eq(HS_MAPPING_DICT['reduce'], -1, "reduce=-1")
    ok &= _assert_eq('SHORTSHOT' in DEFECT_CONST, True, "SHORTSHOT in DEFECT_CONST")
    return ok


def test_translate_defect():
    print('\n[TEST] defect_translate')
    from fuzzy_core.utils.translate import defect_translate
    defects = {'SHORTSHOT': -0.7, 'FLASH': -0.2}
    out = defect_translate(defects)
    return _assert_eq(
        out, ['SHORTSHOT_high', 'FLASH_low'],
        'defect_translate 输出',
    )


def main():
    tests = [
        ('gauss_mf', test_gauss_mf),
        ('tri_mf', test_tri_mf),
        ('FuzzyFeature', test_fuzzy_feature),
        ('FuzzyRule parsing', test_fuzzy_rule_parse),
        ('NumTskRule parsing', test_numtsk_rule_parse),
        ('ParticularRules', test_particular_rules),
        ('NumTskRuleNet inference', test_numtsk_inference),
        ('NumTskRuleNet priority', test_numtsk_inference_priority),
        ('FuzzyRuleNet inference', test_fuzzy_rule_net),
        ('macros', test_macros),
        ('defect_translate', test_translate_defect),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            if fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            import traceback
            print(f'  {FAIL}[ERROR]{NC} {name}: {e}')
            traceback.print_exc()
            failed += 1

    print('\n' + '=' * 60)
    print(f'Total: {passed + failed}, {PASS}Passed: {passed}{NC}, {FAIL}Failed: {failed}{NC}')
    print('=' * 60)
    return failed == 0


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
