r"""推理层门控与档位桶接线回归测试（不依赖 Django/DB）。

本文件覆盖的是 `test_nets.py` **没有**的部分 —— 后者测的是单个组件
（隶属度函数 / 规则解析 / 常量表），本文件测的是**网络实际连到了哪个桶**
与**门控失效时规则是否失活**。两组断言不可互相替代：

- `test_macros.py` 只验 `resolve_bucket()` 函数本身返回什么；
- 本文件验的是该桶位在 `NumTskRuleNet` / `FuzzyRuleNet` 里**真的接上了**。

⚠️ 三个 C 组用例（C1~C3）是真实缺陷的回归锁，删掉它们等于放弃防线：

- **C1**：旧实现把「隶属度为 0 的门控」从乘积里踢出 ⇒「门控不满足」被当成
  「门控不存在」⇒ **规则反而激活**，会推荐出根本没满足条件的建议。
- **C2**：TSK 主路径缺 `MIN_ACTIVATION_THRESHOLD` 过滤 ⇒ 激活度≈0 的规则以
  delta≈0 混进推荐列表（实测见过 conf=1.68e-282）。
- **C3**：Mamdani 路径同样问题。

⚠️ 构造难度：高斯隶属度下 μ 的最小值约 1.27e-14（=exp(-32)），**永不为 0**
⇒ 光靠正常论域构造不出 C1/C3 的触发条件，因此用 monkeypatch 把某个桶的
隶属度强制为 0。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest process/algorithms/fuzzy/fuzzy_core/tests -q
"""

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

from process.algorithms.fuzzy.fuzzy_core.models.nets import (  # noqa: E402
    FuzzyRuleNet,
    NumTskRuleNet,
)
from process.algorithms.fuzzy.fuzzy_core.models.rules import (  # noqa: E402
    FuzzyRule,
    NumTskRule,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
    RuleProfile,
)


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _kw(lvl, min_val=0, max_val=200, step=10):
    return KeywordProfile(keyword='inj_pres_1', lvl=lvl,
                          min_val=min_val, max_val=max_val, step=step)


def _kw_of(name, lvl=5, min_val=0, max_val=200, step=10):
    """指定字段名的论域定义（`_kw` 是 `inj_pres_1` 的特例）。"""
    return KeywordProfile(keyword=name, lvl=lvl,
                          min_val=min_val, max_val=max_val, step=step)


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


def _connected_buckets(net, row=0):
    """返回某一行规则连接到的桶下标列表。"""
    row_data = net.connected_matrix[row]
    return [i for i, v in enumerate(row_data) if v != 0]


# ---------------------------------------------------------------------------
# 基础推理路径
# ---------------------------------------------------------------------------

def test_numeric_layer_priority_wins():
    """数值层：priority=10 的规则排第一。"""
    rule_array = [
        {'rule_description': 'IF SHORTSHOT_high THEN inj_pres_1_add_10'},
        {'rule_description': 'IF SHORTSHOT_high THEN inj_pres_2_add_5'},
    ]
    keyword_array = [
        # SHORTSHOT 必须有元数据：否则前件被跳过 ⇒ 连接矩阵全 0 ⇒ 激活度 0
        # ⇒ 会被【无效激活过滤】剔除，规则连输出都没有。
        KeywordProfile(keyword='SHORTSHOT', lvl=3, min_val=-1, max_val=0, step=10),
        KeywordProfile(keyword='inj_pres_1', lvl=3, min_val=0, max_val=200, step=10),
        KeywordProfile(keyword='inj_pres_2', lvl=3, min_val=0, max_val=200, step=5),
    ]

    net = _numtsk_net(rule_array, keyword_array, [10.0, 5.0])
    results, _ = net.predict({'SHORTSHOT': -0.7, 'inj_pres_1': 50, 'inj_pres_2': 80}, top_k=2)

    assert len(results) == 2, f'期望 2 条结果，实际 {len(results)}'
    assert 'add_10' in results[0][0], f'priority=10 应胜出，但实际 {results[0][0]}'


def test_advisory_layer_produces_conclusion():
    """提示层：FuzzyRuleNet 能产出结论。"""
    rule_array = [
        {'rule_description': 'IF SHORTSHOT_high THEN hold_time_add_low'},
    ]
    keyword_array = [
        KeywordProfile(keyword='hold_time', lvl=3, min_val=0, max_val=10, step=4),
    ]

    net = _fuzzy_net(rule_array, keyword_array)
    results = net.predict({'SHORTSHOT': -0.7, 'hold_time': 3}, top_k=1)

    assert len(results) >= 1, f'期望至少 1 条结果，实际 {len(results)}'


def test_priority_ordering():
    """优先级加权：priority=3 的规则排第一。"""
    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},   # priority=1
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_15'},  # priority=3
    ]
    keyword_array = [_kw(5)]

    net = _numtsk_net(rule_array, keyword_array, [1.0, 3.0])
    results, _ = net.predict({'inj_pres_1': 30}, top_k=2)

    assert 'add_15' in results[0][0], f'priority=3 应胜出，但 {results[0][0]}'


# ---------------------------------------------------------------------------
# 档位 → 桶接线（B 组）
# ---------------------------------------------------------------------------

def test_b1_five_level_high_buckets_to_3():
    """B1: 5 档字段的 'high' 必须连到**桶 3**（论域 75% 分位），不是静态表的桶 2。"""
    rule_array = [{'rule_description': 'IF inj_pres_1_high THEN inj_pres_1_add_5'}]
    net = _numtsk_net(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    assert buckets == [3], f"5 档 high 应连桶 3，实际连桶 {buckets}"

    # x=150 正好落在桶 3 的中心 ⇒ 隶属度 1.0
    feat = net.pre_dict['inj_pres_1']['memberships']
    mu = float(feat.get_value_by_level(150, 3))
    assert abs(mu - 1.0) < 1e-6, f'x=150 在桶 3 的隶属度应为 1.0，实际 {mu}'


def test_b2_five_level_low_buckets_to_1():
    """B2: 5 档字段的 'low' 必须连到**桶 1**（论域 25% 分位），不是静态表的桶 0。"""
    rule_array = [{'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'}]
    net = _numtsk_net(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    assert buckets == [1], f"5 档 low 应连桶 1，实际连桶 {buckets}"

    feat = net.pre_dict['inj_pres_1']['memberships']
    mu = float(feat.get_value_by_level(50, 1))
    assert abs(mu - 1.0) < 1e-6, f'x=50 在桶 1 的隶属度应为 1.0，实际 {mu}'


def test_b3_low_high_separable():
    """B3: 5 档下 low 与 high 不重叠（黑盒行为验证）。

    x=75 时：
      - 正确映射（low→桶1 mean=50，high→桶3 mean=150）⇒ low 的隶属度更高
      - 静态表  （low→桶0 mean=0， high→桶2 mean=100）⇒ high 的隶属度更高
    ⇒ 谁排第一可直接区分两种映射。
    """
    rule_array = [
        {'rule_description': 'IF inj_pres_1_high THEN inj_pres_1_add_5'},
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},
    ]
    net = _numtsk_net(rule_array, [_kw(5)], [1.0, 1.0])
    results, _ = net.predict({'inj_pres_1': 75}, top_k=2)

    assert len(results) == 2, f'期望 2 条结果，实际 {len(results)}'
    assert '_low' in results[0][0], (
        f"x=75 时 low 规则应排第一（5 档 low 桶 mean=50 < high 桶 mean=150），"
        f"实际首位是 {results[0][0]}"
    )


def test_b4_priority_assertion_not_vacuous():
    """B4: priority 真断言 —— 反转优先级后顺序**必须反转**。

    若只断言「priority 高者胜出」，一旦前件全被跳过导致激活度全 0，排序会
    退化成**输入顺序**，断言恒真 ⇒ 变成空转断言。这里用反转做证伪。
    """
    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},   # priority=1
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_15'},  # priority=3
    ]
    kw = [_kw(5)]

    net_a = _numtsk_net(rule_array, kw, [1.0, 3.0])
    res_a, _ = net_a.predict({'inj_pres_1': 50}, top_k=2)
    assert 'add_15' in res_a[0][0], f'priority=3 应胜出，实际 {res_a[0][0]}'

    net_b = _numtsk_net(rule_array, kw, [3.0, 1.0])
    res_b, _ = net_b.predict({'inj_pres_1': 50}, top_k=2)
    assert 'add_5' in res_b[0][0], f'priority 反转后 add_5 应胜出，实际 {res_b[0][0]}'

    assert res_a[0][0] != res_b[0][0], '优先级反转后输出顺序未变 ⇒ 断言空转'


def test_b5_three_level_compat():
    """B5: 3 档字段的桶位映射（low→0 / medium→1 / high→2）。"""
    expect = {'low': 0, 'medium': 1, 'high': 2}
    for word, bucket in expect.items():
        rule_array = [{'rule_description': f'IF inj_pres_1_{word} THEN inj_pres_1_add_5'}]
        net = _numtsk_net(rule_array, [_kw(3)], [1.0])
        got = _connected_buckets(net, 0)
        assert got == [bucket], f"3 档 {word} 应连桶 {bucket}，实际 {got}"


def test_b6_multi_segment_word():
    """B6: 多段档位词（very_low）能接上桶位。

    `ALL_LEVEL_WORDS` 含 very_low / very_high / extremely_* / ultra_*，
    桶位必须能接住这些词，否则规则一旦真用上就会崩。
    """
    rule_array = [{'rule_description': 'IF inj_pres_1_very_low THEN inj_pres_1_add_5'}]
    net = _numtsk_net(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    assert buckets == [0], f"5 档 very_low 应连桶 0，实际 {buckets}"


def test_b7_missing_metadata_gate():
    """B7: 前件参数缺元数据 ⇒ 规则激活度为 0（不是被当成无条件命中）。"""
    rule_array = [{'rule_description': 'IF SHORTSHOT_high THEN inj_pres_1_add_5'}]
    # keyword_array 里**故意不给** SHORTSHOT
    net = _numtsk_net(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    assert buckets == [], f'应不连任何桶，实际 {buckets}'

    results, _ = net.predict({'SHORTSHOT': -0.7, 'inj_pres_1': 150}, top_k=1)
    acts = [r[1] for r in results]
    # 缺元数据 ⇒ 前件不连任何桶 ⇒ 激活度 0。
    # 修复后激活度 0 的规则会被【无效激活过滤】剔除，所以表现是「不输出」
    # 而不是「输出但激活度为 0」—— 两者等价。
    assert not results or all(abs(a) < 1e-6 for a in acts), (
        f'缺门控的规则激活度应为 0，实际 {acts}'
    )


# ---------------------------------------------------------------------------
# TSK 推理层缺陷基准（C 组）
# ---------------------------------------------------------------------------

def test_c1_zero_degree_gate_blocks_rule():
    """C1: 门控隶属度为 0 ⇒ 规则激活度必须为 0（TSK 主路径）。"""
    rule_array = [{
        'rule_description': 'IF inj_pres_1_high AND inj_pres_2_low THEN inj_pres_1_add_5',
    }]
    kw = [_kw_of('inj_pres_1', 5), _kw_of('inj_pres_2', 5)]
    net = _numtsk_net(rule_array, kw, [1.0])

    # 让 inj_pres_1 的 high 桶（level 3）隶属度恒为 0
    feat = net.pre_dict['inj_pres_1']['memberships']
    origin = feat.get_value_by_level

    def _zero_at_high(x, level):
        return 0.0 if level == 3 else origin(x, level)

    feat.get_value_by_level = _zero_at_high

    results, _ = net.predict({'inj_pres_1': 150, 'inj_pres_2': 50}, top_k=5)
    acts = [r[1] for r in results]
    assert all(abs(a) < 1e-9 for a in acts), (
        f'门控隶属度为 0 时规则激活度必须为 0，实际 {acts}'
        f'（旧实现把 0 的门控踢出乘积 ⇒ 规则反而激活）'
    )


def test_c2_low_activation_no_conclusion():
    """C2: 权重过低的规则不产出结论（不进推荐列表）。"""
    rule_array = [
        {'rule_description': 'IF inj_pres_1_high THEN inj_pres_1_add_5'},
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_2_add_5'},
    ]
    kw = [_kw_of('inj_pres_1', 5), _kw_of('inj_pres_2', 5)]
    net = _numtsk_net(rule_array, kw, [1.0, 1.0])

    # x=150：high 桶（mean=150）μ=1.0；low 桶（mean=50）μ=exp(-8)≈3.35e-4
    results, _ = net.predict({'inj_pres_1': 150}, top_k=5)

    assert len(results) == 1, (
        f'低激活度规则（low 桶在 x=150 时 μ=exp(-8)≈3.35e-4）不应产出结论，'
        f'实际输出 {len(results)} 条'
    )
    assert 'inj_pres_1' in results[0][2], f'应保留 high 规则，实际 {results[0][2]}'


def test_c3_mamdani_zero_degree_gate():
    """C3: Mamdani 路径同样不能"踢出"隶属度 0 的门控。"""
    rule_array = [{
        'rule_description': 'IF inj_pres_1_high AND inj_pres_2_low THEN inj_pres_1_add_low',
    }]
    kw = [_kw_of('inj_pres_1', 5), _kw_of('inj_pres_2', 5)]
    net = _fuzzy_net(rule_array, kw)

    feat = net.pre_dict['inj_pres_1']['memberships']
    origin = feat.get_value_by_level

    def _zero_at_high(x, level):
        return 0.0 if level == 3 else origin(x, level)

    feat.get_value_by_level = _zero_at_high

    results = net.inference({'inj_pres_1': 150, 'inj_pres_2': 50})
    acts = [r[2][0] for r in results]
    assert all(abs(a) < 1e-9 for a in acts), (
        f'Mamdani 门控隶属度为 0 时激活度必须为 0，实际 {acts}'
    )


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_inference_gates``。"""
    cases = [
        test_numeric_layer_priority_wins,
        test_advisory_layer_produces_conclusion,
        test_priority_ordering,
        test_b1_five_level_high_buckets_to_3,
        test_b2_five_level_low_buckets_to_1,
        test_b3_low_high_separable,
        test_b4_priority_assertion_not_vacuous,
        test_b5_three_level_compat,
        test_b6_multi_segment_word,
        test_b7_missing_metadata_gate,
        test_c1_zero_degree_gate_blocks_rule,
        test_c2_low_activation_no_conclusion,
        test_c3_mamdani_zero_degree_gate,
    ]
    failed = []
    for fn in cases:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - 独立跑法需要汇总全部失败
            print(f'[FAIL] {fn.__name__}: {exc}')
            failed.append(fn.__name__)
    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] {len(failed)}/{len(cases)} 个用例失败：{failed}')
        return 1
    print(f'[PASS] {len(cases)}/{len(cases)} 个用例通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
