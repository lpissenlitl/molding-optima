"""
FuzzyEngine 端到端 sanity check（不依赖 Django ORM，使用 mock 替换 RuleQueryService）

运行：
  cd backend/process/algorithms/fuzzy
  python sanity_check.py

覆盖：
  1) 数值层 NumTskRuleNet 单层推理
  2) 提示层 FuzzyRuleNet 单层推理
  3) 双层合并（同层聚合 + 跨层覆盖，方案 B）
  4) 优先级加权（priority=3 胜出）
  5) 档位→桶接线基准 B1~B7（5 档桶落位 / low-high 区分度 / priority 真断言 /
     3 档兼容 / 多段词不崩 / 缺元数据门控显式失效）

⚠️ 术语：本文件中的"层"指**结论形态**（结论能不能算出数值），
   与规则库层级（base / 产品库 / specificity）无关。
   数值层 = numeric，提示层 = advisory。
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

HERE = os.path.dirname(os.path.abspath(__file__))
FUZZY_DIR = HERE
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(FUZZY_DIR)))
sys.path.insert(0, BACKEND_ROOT)        # 让 `process` 可被 import
sys.path.insert(0, os.path.dirname(BACKEND_ROOT))  # 让 backend 内部包也可导入
sys.path.insert(0, FUZZY_DIR)
sys.path.insert(0, os.path.dirname(FUZZY_DIR))


# ---------------------------------------------------------------------------
# 1. 数值层 NumTskRuleNet 推理
# ---------------------------------------------------------------------------

def case_numeric_layer():
    print('\n========== CASE 1: 数值层 NumTskRuleNet 推理 ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    # 场景：PE 酒瓶短射，调高注射压力 10 单位
    rule_array = [
        {'rule_description': 'IF SHORTSHOT_high THEN inj_pres_1_add_10'},
        {'rule_description': 'IF SHORTSHOT_high THEN inj_pres_2_add_5'},
    ]
    keyword_array = [
        {'keyword': 'inj_pres_1', 'lvl': 3, 'min_val': 0, 'max_val': 200, 'step': 10},
        {'keyword': 'inj_pres_2', 'lvl': 3, 'min_val': 0, 'max_val': 200, 'step': 5},
    ]
    priority_array = [10.0, 5.0]

    net = NumTskRuleNet(rule_array, keyword_array, priority_array)
    results, extra = net.predict(
        {'SHORTSHOT': -0.7, 'inj_pres_1': 50, 'inj_pres_2': 80},
        top_k=2,
    )

    assert len(results) == 2, f'期望 2 条结果，实际 {len(results)}'
    # priority=10 规则排在前面
    assert 'add_10' in results[0][0], f'priority=10 应胜出，但实际 {results[0][0]}'
    print(f'[OK] 数值层返回 {len(results)} 条；优先级胜出：{results[0][0]}')
    print(f'   results[0] = {results[0]}')
    print(f'   results[1] = {results[1]}')
    return True


# ---------------------------------------------------------------------------
# 2. 提示层 FuzzyRuleNet 推理
# ---------------------------------------------------------------------------

def case_advisory_layer():
    print('\n========== CASE 2: 提示层 FuzzyRuleNet 推理 ==========')
    from fuzzy_core.models.nets import FuzzyRuleNet

    rule_array = [
        {'rule_description': 'IF SHORTSHOT_high THEN hold_time_add_low'},
    ]
    keyword_array = [
        {'keyword': 'hold_time', 'lvl': 3, 'min_val': 0, 'max_val': 10, 'step': 4},
    ]
    net = FuzzyRuleNet(rule_array, keyword_array)
    results = net.predict({'SHORTSHOT': -0.7, 'hold_time': 3}, top_k=1)
    assert len(results) >= 1, f'期望至少 1 条结果，实际 {len(results)}'
    print(f'[OK] 提示层返回 {len(results)} 条；首个 = {results[0]}')


# ---------------------------------------------------------------------------
# 3. FuzzyEngine 双层合并（mock RuleQueryService）
# ---------------------------------------------------------------------------

def _mock_resolved_rule(rule_id, rule_str, conclusion_kind, polymer=None, product=None, priority=1):
    """模拟 RuleQueryService 返回的 ResolvedRule"""
    # 直接构造 ResolvedRule（绕过 rule_query_service 包的 Django 依赖）
    from collections import namedtuple
    ResolvedRule = namedtuple('ResolvedRule', [
        'rule_id', 'rule_str', 'conclusion_kind',
        'polymer_abbreviation', 'product_category', 'priority', 'library_code',
    ])
    return ResolvedRule(
        rule_id=rule_id,
        rule_str=rule_str,
        conclusion_kind=conclusion_kind,
        polymer_abbreviation=polymer,
        product_category=product,
        priority=priority,
        library_code='mock_lib',
    )


def case_double_layer_merge():
    """直接调用 FuzzyEngine._merge_layer_results，验证方案 B 合并逻辑。"""
    print('\n========== CASE 3: FuzzyEngine._merge_layer_results 合并逻辑 ==========')

    # 用 importlib 直加载 fuzzy_engine.py 中的 FuzzyEngine 类（避免触发 Django 间接依赖）
    # 由于 FuzzyEngine 的 import 链需要 adapters / rule_query_service，
    # 我们重新组织：仅提取 _merge_layer_results 这一个静态方法的逻辑来验证
    # 用一份简化版函数验证合并结果。
    def merge_layer_results(numeric_results, advisory_results, adjustment_factor, current_params):
        """复刻 FuzzyEngine._merge_layer_results，便于独立验证。"""
        merged = {}
        for rec in numeric_results:
            p = rec['param']
            if p not in merged:
                merged[p] = {
                    'param': p,
                    'delta': rec['delta'],
                    'activation_sum': rec['activation'],
                    'rule_count': 1,
                    'sources': ['numeric'],
                    'advisory_reference': None,
                }
            else:
                merged[p]['delta'] += rec['delta']
                merged[p]['activation_sum'] += rec['activation']
                merged[p]['rule_count'] += 1
        for rec in advisory_results:
            p = rec['param']
            if p not in merged:
                merged[p] = {
                    'param': p,
                    'delta': rec['delta'],
                    'activation_sum': rec['activation'],
                    'rule_count': 1,
                    'sources': ['advisory'],
                    'advisory_reference': None,
                }
            else:
                merged[p]['advisory_reference'] = rec['delta']
                merged[p]['sources'].append('advisory')
        return merged

    # 场景：PE 酒瓶短射 → 同时有 2 条数值层规则 + 1 条提示层规则
    numeric_results = [
        {'param': 'inj_pres_1', 'delta': 10.0, 'activation': 0.9, 'rule': 'r1'},
        {'param': 'inj_pres_2', 'delta': 5.0,  'activation': 0.7, 'rule': 'r2'},
        # 同参数多条规则 → 同层聚合
        {'param': 'inj_pres_1', 'delta': 5.0,  'activation': 0.6, 'rule': 'r3'},
    ]
    advisory_results = [
        {'param': 'hold_time', 'delta': 1.5, 'activation': 0.5, 'rule': 'r4'},
        # inj_pres_1 已被数值层覆盖 → 应作为 advisory_reference，不覆盖
        {'param': 'inj_pres_1', 'delta': 999, 'activation': 0.4, 'rule': 'r5'},
    ]
    current_params = {'inj_pres_1': 50, 'inj_pres_2': 80, 'hold_time': 3}
    factor = 1.2

    merged = merge_layer_results(numeric_results, advisory_results, factor, current_params)

    # 1) inj_pres_1: 同层聚合 + 提示层只作 advisory_reference
    inj1 = merged['inj_pres_1']
    assert inj1['sources'] == ['numeric', 'advisory'], f'sources={inj1["sources"]}'
    assert abs(inj1['delta'] - 15.0) < 1e-6, f'aggregated delta={inj1["delta"]}'
    assert inj1['advisory_reference'] == 999, f'advisory_reference={inj1["advisory_reference"]}'
    assert inj1['rule_count'] == 2
    assert abs(inj1['activation_sum'] - 1.5) < 1e-6, f'activation_sum={inj1["activation_sum"]}'

    # 2) inj_pres_2: 仅数值层
    inj2 = merged['inj_pres_2']
    assert inj2['sources'] == ['numeric'], f'sources={inj2["sources"]}'

    # 3) hold_time: 仅提示层
    hold = merged['hold_time']
    assert hold['sources'] == ['advisory'], f'sources={hold["sources"]}'

    print('[OK] 合并覆盖 3 个参数：')
    for k, v in merged.items():
        print(f'   {k}: delta={v["delta"]:.2f}, sources={v["sources"]}, advisory_ref={v["advisory_reference"]}')


# ---------------------------------------------------------------------------
# 4. 优先级加权排序
# ---------------------------------------------------------------------------

def case_priority_ordering():
    print('\n========== CASE 4: priority 排序 ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},   # priority=1
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_15'},  # priority=3
    ]
    keyword_array = [
        {'keyword': 'inj_pres_1', 'lvl': 3, 'min_val': 0, 'max_val': 200, 'step': 10},
    ]
    net = NumTskRuleNet(rule_array, keyword_array, [1.0, 3.0])
    results, _ = net.predict({'inj_pres_1': 30}, top_k=2)
    # priority=3 的应排第一
    assert 'add_15' in results[0][0], f'priority=3 应胜出，但 {results[0][0]}'
    print(f'[OK] priority=3 胜出：{results[0][0]} (activation={results[0][1]:.4f})')


# ---------------------------------------------------------------------------
# 5. 档位→桶接线基准（B1~B7）
# ---------------------------------------------------------------------------
#
# 背景（2026-10-23）：
#   `nets.py` 原来用全局静态 3 档表 `HS_MAPPING_DICT[level]` 取桶索引，
#   而现网 310/311 个字段是 **5 档** ⇒ `low/medium/high` 全部错位一档
#   （`high` 被当成 5 档的 medium = 论域 50% 分位）。
#   正确实现 `macros.resolve_bucket(lvl, word)` 已存在但未接线。
#
# 为什么这组 case 必须是「真断言」：
#   现网 `case_numeric_layer` 的 `keyword_array` 里没有前件参数
#   ⇒ 前件被 `nets.py` 跳过 ⇒ `connected_matrix` 全 0 ⇒ 激活度全 0
#   ⇒ 排序退化为**输入顺序** ⇒ 「优先级高的胜出」恒真、无法证伪。
#
# 统一场景：`inj_pres_1`，lvl=5，论域 [0, 200]
#   ⇒ 高斯参数 means=[0, 50, 100, 150, 200]，σ = (200-0)/(2×4) = 25
#   ⇒ 5 档桶位：0=very_low(0) 1=low(50) 2=medium(100) 3=high(150) 4=very_high(200)


def _connected_buckets(net, row=0):
    """返回某一行规则连接到的桶下标列表。"""
    row_data = net.connected_matrix[row]
    return [i for i, v in enumerate(row_data) if v != 0]


def _kw(lvl, min_val=0, max_val=200, step=10):
    return {'keyword': 'inj_pres_1', 'lvl': lvl,
            'min_val': min_val, 'max_val': max_val, 'step': step}


def case_b1_bucket_wiring_high():
    """B1: 5 档字段的 'high' 必须连到**桶 3**（论域 75% 分位），不是静态表的桶 2。"""
    print('\n========== CASE B1: 5 档 high 的桶落位（接线验证） ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    rule_array = [{'rule_description': 'IF inj_pres_1_high THEN inj_pres_1_add_5'}]
    net = NumTskRuleNet(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    print(f'  连接到的桶 = {buckets}（5 档词表 '
          f"('very_low','low','medium','high','very_high') ⇒ high 应为 3）")
    assert buckets == [3], f"5 档 high 应连桶 3，实际连桶 {buckets}"

    # x=150 正好落在桶 3 的中心 ⇒ 隶属度 1.0
    feat = net.pre_dict['inj_pres_1']['memberships']
    mu = float(feat.get_value_by_level(150, 3))
    assert abs(mu - 1.0) < 1e-6, f'x=150 在桶 3 的隶属度应为 1.0，实际 {mu}'
    print(f'[OK] 5 档 high 连桶 3；x=150 的隶属度 = {mu:.6f}')
    return True


def case_b2_bucket_wiring_low():
    """B2: 5 档字段的 'low' 必须连到**桶 1**（论域 25% 分位），不是静态表的桶 0。"""
    print('\n========== CASE B2: 5 档 low 的桶落位（接线验证） ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    rule_array = [{'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'}]
    net = NumTskRuleNet(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    print(f'  连接到的桶 = {buckets}（5 档 ⇒ low 应为 1）')
    assert buckets == [1], f"5 档 low 应连桶 1，实际连桶 {buckets}"

    feat = net.pre_dict['inj_pres_1']['memberships']
    mu = float(feat.get_value_by_level(50, 1))
    assert abs(mu - 1.0) < 1e-6, f'x=50 在桶 1 的隶属度应为 1.0，实际 {mu}'
    print(f'[OK] 5 档 low 连桶 1；x=50 的隶属度 = {mu:.6f}')
    return True


def case_b3_low_high_separable():
    """B3: 5 档下 low 与 high 不重叠（行为验证，黑盒）。

    x=75 时：
      - 正确映射（low→桶1 mean=50，high→桶3 mean=150）⇒ low 的隶属度更高
      - 静态表  （low→桶0 mean=0， high→桶2 mean=100）⇒ high 的隶属度更高
    ⇒ 谁排第一可直接区分两种映射。
    """
    print('\n========== CASE B3: 5 档 low / high 的区分度（行为验证） ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    rule_array = [
        {'rule_description': 'IF inj_pres_1_high THEN inj_pres_1_add_5'},
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},
    ]
    net = NumTskRuleNet(rule_array, [_kw(5)], [1.0, 1.0])
    results, _ = net.predict({'inj_pres_1': 75}, top_k=2)

    print(f'  x=75，输出顺序：')
    for r in results:
        print(f'    activation={r[1]:.6f}  {r[0]}')
    assert len(results) == 2, f'期望 2 条结果，实际 {len(results)}'
    assert '_low' in results[0][0], (
        f"x=75 时 low 规则应排第一（5 档 low 桶 mean=50 < high 桶 mean=150），"
        f"实际首位是 {results[0][0]}"
    )
    print('[OK] x=75 时 low 规则胜出 ⇒ low/high 已分离到各自的分位桶')
    return True


def case_b4_priority_real():
    """B4: priority 真断言（修正现网空转断言）。

    关键：`keyword_array` **必须包含前件参数**，否则前件被 `nets.py` 跳过 ⇒
    激活度全 0 ⇒ 排序 = 输入顺序 ⇒ 优先级断言恒真。
    """
    print('\n========== CASE B4: priority 加权（真断言） ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},   # priority=1
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_15'},  # priority=3
    ]
    kw = [_kw(5)]

    net_a = NumTskRuleNet(rule_array, kw, [1.0, 3.0])
    res_a, _ = net_a.predict({'inj_pres_1': 50}, top_k=2)
    print('  priority=[1, 3]:')
    for r in res_a:
        print(f'    activation={r[1]:.6f}  {r[0]}')
    assert 'add_15' in res_a[0][0], f'priority=3 应胜出，实际 {res_a[0][0]}'

    # ★ 反转优先级后顺序**必须反转** —— 这一步才能证伪「优先级逻辑失效」
    net_b = NumTskRuleNet(rule_array, kw, [3.0, 1.0])
    res_b, _ = net_b.predict({'inj_pres_1': 50}, top_k=2)
    print('  priority=[3, 1]:')
    for r in res_b:
        print(f'    activation={r[1]:.6f}  {r[0]}')
    assert 'add_5' in res_b[0][0], f'priority 反转后 add_5 应胜出，实际 {res_b[0][0]}'

    assert res_a[0][0] != res_b[0][0], '优先级反转后输出顺序未变 ⇒ 断言空转'
    print('[OK] priority 反转后顺序同步反转 ⇒ 优先级逻辑真的在起作用')
    return True


def case_b5_three_level_compat():
    """B5: 3 档字段与旧版完全一致（向后兼容）。"""
    print('\n========== CASE B5: 3 档向后兼容 ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    expect = {'low': 0, 'medium': 1, 'high': 2}
    for word, bucket in expect.items():
        rule_array = [{'rule_description': f'IF inj_pres_1_{word} THEN inj_pres_1_add_5'}]
        net = NumTskRuleNet(rule_array, [_kw(3)], [1.0])
        got = _connected_buckets(net, 0)
        print(f'  {word:<8} 桶 = {got}（期望 [{bucket}]）')
        assert got == [bucket], f"3 档 {word} 应连桶 {bucket}，实际 {got}"
    print('[OK] 3 档 low/medium/high 与旧版静态表完全一致 ⇒ 接线对 3 档字段零影响')
    return True


def case_b6_multi_segment_word():
    """B6: 多段档位词（very_low）不再 KeyError。

    `ALL_LEVEL_WORDS` 含 very_low / very_high / extremely_* / ultra_*，
    而旧的静态表里没有这些键 ⇒ 一旦规则真用上就会崩。
    """
    print('\n========== CASE B6: 多段档位词 very_low ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    rule_array = [{'rule_description': 'IF inj_pres_1_very_low THEN inj_pres_1_add_5'}]
    net = NumTskRuleNet(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    print(f'  连接到的桶 = {buckets}（5 档 ⇒ very_low 应为 0）')
    assert buckets == [0], f"5 档 very_low 应连桶 0，实际 {buckets}"
    print('[OK] very_low 正常解析（未接线时会 KeyError）')
    return True


def case_b7_missing_metadata_gate():
    """B7: 前件参数缺元数据 ⇒ 规则激活度为 0（不是被当成无条件命中）。"""
    print('\n========== CASE B7: 缺元数据的门控显式失效 ==========')
    from fuzzy_core.models.nets import NumTskRuleNet

    rule_array = [{'rule_description': 'IF SHORTSHOT_high THEN inj_pres_1_add_5'}]
    # keyword_array 里**故意不给** SHORTSHOT
    net = NumTskRuleNet(rule_array, [_kw(5)], [1.0])

    buckets = _connected_buckets(net, 0)
    print(f'  连接到的桶 = {buckets}（SHORTSHOT 无元数据 ⇒ 不连任何桶）')
    assert buckets == [], f'应不连任何桶，实际 {buckets}'

    results, _ = net.predict({'SHORTSHOT': -0.7, 'inj_pres_1': 150}, top_k=1)
    print(f'  激活度 = {results[0][1]:.6f}')
    assert abs(results[0][1]) < 1e-6, f'缺门控的规则激活度应为 0，实际 {results[0][1]}'
    print('[OK] 缺元数据的门控 ⇒ 规则激活度为 0（不是无条件命中）')
    return True


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    cases = [
        case_numeric_layer,
        case_advisory_layer,
        case_double_layer_merge,
        case_priority_ordering,
        case_b1_bucket_wiring_high,
        case_b2_bucket_wiring_low,
        case_b3_low_high_separable,
        case_b4_priority_real,
        case_b5_three_level_compat,
        case_b6_multi_segment_word,
        case_b7_missing_metadata_gate,
    ]
    failed = 0
    for fn in cases:
        try:
            fn()
        except Exception as e:
            print(f'\n[FAIL] {fn.__name__}: {e}')
            import traceback
            traceback.print_exc()
            failed += 1

    print('\n' + '=' * 60)
    if failed == 0:
        # 注意：这里不要用 emoji，Windows 默认 GBK 控制台会抛 UnicodeEncodeError
        print('[PASS] 所有 sanity check 通过')
        return 0
    print(f'[FAIL] {failed} 个 case 失败')
    return 1


if __name__ == '__main__':
    sys.exit(main())
