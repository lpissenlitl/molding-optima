"""
fuzzy_core 独立单元测试（不依赖 Django/DB）

运行：
  cd backend
  pytest process/algorithms/fuzzy/fuzzy_core/tests/test_nets.py
  # 或独立跑：
  python -m process.algorithms.fuzzy.fuzzy_core.tests.test_nets
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FUZZY_CORE = os.path.dirname(HERE)
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(FUZZY_CORE))))

# 只把 backend 根目录（包的父目录）加进 sys.path。
# ⚠️ 不要把 `fuzzy/` 目录加进来：那等于宣布「该目录下每个带 __init__.py 的子目录
#    都是顶层包」，于是包内子模块（`fuzzy_core` / `library` …）泄漏成
#    顶层名，将来撞名即**静默劫持**。内核一律用完整点分路径导入。
sys.path.insert(0, BACKEND_ROOT)

from process.algorithms.fuzzy.fuzzy_core.models.features import FuzzyFeature  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.models.nets import (  # noqa: E402
    FuzzyRuleNet,
    NumTskRuleNet,
)
from process.algorithms.fuzzy.fuzzy_core.models.rules import (  # noqa: E402
    FuzzyRule,
    NumTskRule,
    ParticularRules,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
    RuleProfile,
)
from process.algorithms.fuzzy.fuzzy_core.memberships import gaussian_mf, triangular_mf  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.defuzz import defuzz  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.macros import (  # noqa: E402
    ACTION_MAP,
    DEFECT_CONST,
    resolve_bucket,
)


FAIL = '\033[91m'
PASS = '\033[92m'
NC = '\033[0m'


def _assert_eq(actual, expected, label):
    if actual != expected:
        raise AssertionError(f'{label}: expected={expected!r}, actual={actual!r}')


def _assert_close(actual, expected, label, eps=1e-3):
    if abs(actual - expected) >= eps:
        raise AssertionError(f'{label}: expected≈{expected}, actual={actual:.4f}')


def _numtsk_net(rule_array, keywords, priorities):
    """按当前 net 契约构造数值层网络（规则对象 + KeywordProfile）。

    ⚠️ net 不再吃裸 dict：规则串由调用方转成 `NumTskRule`，
    优先级随规则档案走（不再单独传优先级数组）。
    """
    rules = [
        NumTskRule(
            RuleProfile(rule_description=r['rule_description'], priority=p),
            parse_rule(r['rule_description']),
        )
        for r, p in zip(rule_array, priorities)
    ]
    return NumTskRuleNet(rules, list(keywords))


def _fuzzy_net(rule_array, keywords):
    """按当前 net 契约构造提示层网络（Mamdani）。"""
    rules = [
        FuzzyRule(
            RuleProfile(rule_description=r['rule_description']),
            parse_rule(r['rule_description']),
        )
        for r in rule_array
    ]
    return FuzzyRuleNet(rules, list(keywords))


def test_gauss_mf():
    # 统一签名 (x, center, width)：width = 总跨度 = 2σ ⇒ σ=1 对应 width=2
    _assert_close(gaussian_mf(0, 0, 2), 1.0, 'gaussian_mf(0, 0, 2)')
    _assert_close(gaussian_mf(1, 0, 2), float(math.exp(-0.5)), 'gaussian_mf(1, 0, 2)')
    import numpy as np
    arr = gaussian_mf(np.array([0.0, 1.0, 2.0]), 0, 2)
    _assert_eq(len(arr), 3, 'ndarray length')


def test_tri_mf():
    # 统一签名 (x, center, width, shape)：顶点 center=5、底边跨度 10 ⇒ 对称三角形
    _assert_eq(triangular_mf(5, 5, 10, (0.5, 0.5)), 1.0, 'triangular_mf(5, 5, 10) == 1.0')
    _assert_eq(triangular_mf(2, 5, 10, (0.5, 0.5)), 0.4, 'triangular_mf(2, 5, 10) == 0.4')
    _assert_eq(triangular_mf(15, 5, 10, (0.5, 0.5)), 0, 'triangular_mf(15, 5, 10) == 0')


def test_fuzzy_feature():
    ff = FuzzyFeature([0, 200], f_level=3, f_membership_type='gauss')
    _assert_eq(ff.f_level, 3, 'fuzzy_level=3')
    _assert_eq(set(ff.membership_dict.keys()), {'degree_0', 'degree_1', 'degree_2'},
               'membership_dict keys')
    deg_low = ff.get_value_by_level(0, 0)
    _assert_close(deg_low, 1.0, 'low @ x=min', eps=1e-2)
    deg_mid = ff.get_value_by_level(100, 1)
    _assert_close(deg_mid, 1.0, 'mid @ x=mid', eps=1e-2)


def test_fuzzy_rule_parse():
    desc = 'IF inj_pres_1_low AND SHORTSHOT_high THEN hold_time_add_low'
    fr = FuzzyRule(RuleProfile(rule_description=desc), parse_rule(desc))
    _assert_eq(set(fr.r_preconditions.keys()), {'inj_pres_1', 'SHORTSHOT'},
               'conditions keys')
    _assert_eq(set(fr.r_solutions.keys()), {'hold_time'}, 'solutions keys')
    _assert_eq(fr.r_solutions['hold_time']['level'], 'low', 'solution level')
    _assert_eq(fr.r_solutions['hold_time']['action'], 1, 'add action=+1')


def test_numtsk_rule_parse():
    desc = 'IF inj_pres_1_low THEN inj_pres_1_add_10'
    rule = NumTskRule(RuleProfile(rule_description=desc), parse_rule(desc))
    _assert_eq(list(rule.r_preconditions.keys()), ['inj_pres_1'], 'num preconditions')
    _assert_eq(rule.r_solutions['inj_pres_1']['action'], 1, 'add=+1')
    _assert_eq(rule.r_solutions['inj_pres_1']['level'], '10', 'value=10')

    desc_pct = 'IF mol_temp_mid THEN mol_temp_add_5%'
    rule_pct = NumTskRule(RuleProfile(rule_description=desc_pct), parse_rule(desc_pct))
    _assert_eq(rule_pct.r_solutions['mol_temp']['level'], '5%', 'percent rule')

    desc_popup = 'IF SHORTSHOT_high THEN alert_popup_sugg'
    rule_popup = NumTskRule(RuleProfile(rule_description=desc_popup), parse_rule(desc_popup))
    _assert_eq('alert_popup_sugg' in rule_popup.r_extra, True, 'popup r_extra')


def test_particular_rules():
    desc = 'IF SHORTSHOT_high THEN alert_popup_sugg'
    pr = ParticularRules([RuleProfile(rule_description=desc)], [parse_rule(desc)])
    _assert_eq(len(pr.adjust_rule_list), 1, 'parsed 1 rule')
    parsed = pr.adjust_rule_list[0]
    _assert_eq(parsed.get('rule_defect'), 'SHORTSHOT', 'extract defect')
    _assert_eq(parsed.get('rule_output'), 'sugg', 'extract output')


def test_numtsk_inference():
    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_10'},
    ]
    keyword_array = [
        KeywordProfile(keyword='inj_pres_1', lvl=3, min_val=0, max_val=200, step=10),
    ]
    priority_array = [1.0]
    net = _numtsk_net(rule_array, keyword_array, priority_array)
    results, extra = net.predict({'inj_pres_1': 30}, top_k=1)
    _assert_eq(len(results) == 1, True, 'result count == 1')
    if len(results) >= 1:
        rule_str, activation, adjustments = results[0]
        _assert_eq('inj_pres_1' in adjustments, True, 'adjustments contains target')
        _assert_eq(float(activation) > 0, True, 'activation > 0')
    _assert_eq(extra, {}, 'no extra_dict for plain rule')


def test_numtsk_inference_priority():
    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_15'},
    ]
    keyword_array = [
        KeywordProfile(keyword='inj_pres_1', lvl=3, min_val=0, max_val=200, step=10),
    ]
    net = _numtsk_net(rule_array, keyword_array, [1.0, 3.0])
    results, _ = net.predict({'inj_pres_1': 30}, top_k=2)
    _assert_eq(len(results), 2, 'result count == 2')
    _assert_eq(
        'inj_pres_1_add_15' in results[0][0], True,
        'priority=3 规则排在前面',
    )
    # 反转优先级：结论必须跟着换，否则上面那条断言是空转
    net_rev = _numtsk_net(rule_array, keyword_array, [3.0, 1.0])
    results_rev, _ = net_rev.predict({'inj_pres_1': 30}, top_k=2)
    _assert_eq(len(results_rev), 2, 'reversed result count == 2')
    _assert_eq(
        'inj_pres_1_add_5' in results_rev[0][0], True,
        '优先级反转后 add_5 排到前面',
    )


def test_fuzzy_rule_net():
    rule_array = [
        {'rule_description': 'IF SHORTSHOT_high THEN hold_time_add_low'},
    ]
    keyword_array = [
        KeywordProfile(keyword='hold_time', lvl=3, min_val=0, max_val=10, step=4),
    ]
    net = _fuzzy_net(rule_array, keyword_array)
    results = net.predict({'SHORTSHOT': -0.7, 'hold_time': 3}, top_k=1)
    _assert_eq(len(results) >= 1, True, 'mamdani result count >= 1')
    if len(results) >= 1:
        param_name, value, _ = results[0]
        _assert_eq(param_name, 'hold_time', 'param = hold_time')
        _assert_eq(0 <= value <= 4.0, True, 'value in [0, 4]')


def test_macros():
    _assert_eq(resolve_bucket(3, 'low'), 0, "3 档 low → 桶 0")
    _assert_eq(resolve_bucket(3, 'high'), 2, "3 档 high → 桶 2")
    _assert_eq(resolve_bucket(5, 'low'), 1, "5 档 low → 桶 1")
    _assert_eq(resolve_bucket(5, 'high'), 3, "5 档 high → 桶 3")
    _assert_eq(ACTION_MAP['add'], 1, "add=+1")
    _assert_eq(ACTION_MAP['reduce'], -1, "reduce=-1")
    _assert_eq('SHORTSHOT' in DEFECT_CONST, True, "SHORTSHOT in DEFECT_CONST")


def main():
    tests = [
        ('gaussian_mf', test_gauss_mf),
        ('triangular_mf', test_tri_mf),
        ('FuzzyFeature', test_fuzzy_feature),
        ('FuzzyRule parsing', test_fuzzy_rule_parse),
        ('NumTskRule parsing', test_numtsk_rule_parse),
        ('ParticularRules', test_particular_rules),
        ('NumTskRuleNet inference', test_numtsk_inference),
        ('NumTskRuleNet priority', test_numtsk_inference_priority),
        ('FuzzyRuleNet inference', test_fuzzy_rule_net),
        ('macros', test_macros),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            print(f'\n[TEST] {name}')
            fn()
            passed += 1
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
