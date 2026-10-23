"""Step 1：用真实数据填满「一条规则的旅程」。

用途（交接文档 §6 Step 1）：
    挑 4 条真实规则，覆盖【纯数值 / 带缺陷前件 / 百分比动作 / 提示类(adjust)】，
    用真实 RuleKeyword 论域 + 一组示例参数值，跑出每一步的**真实中间值**：
        解析 → 校验 → 隶属度函数参数(峰位/σ) → 列区间 → 矩阵置位
        → 每列隶属度 → 规则激活度 → 归一化权重 → 最终建议

只读诊断脚本：不修改任何生产代码。
所有数值均来自 DB 真实数据（RuleMethod / RuleKeyword），非手写占位。

用法：
    python _dev_refs/diag_fuzzy_rule_journey.py
"""
import os
import sys
from collections import OrderedDict

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# 控制台默认 GBK，输出含中文/符号，统一改 UTF-8（否则 ⇒/⚠ 会抛 UnicodeEncodeError）
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # pragma: no cover
    pass

import django  # noqa: E402

django.setup()

import numpy as np  # noqa: E402

from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT
from process.algorithms.fuzzy.adapters import RuleKeywordAdapter  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.macros import (  # noqa: E402
    LEVEL_WORDS_BY_LVL,
    resolve_bucket,
)
from process.algorithms.fuzzy.fuzzy_core.models.nets import (  # noqa: E402
    NumTskRuleNet,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import (  # noqa: E402
    classify_name,
    is_level_word,
    parse_rule,
)
from process.algorithms.fuzzy.services.rule_query_service import (  # noqa: E402
    RuleQueryContext,
    RuleQueryService,
)
from process.models.rules import RuleKeyword, RuleMethod  # noqa: E402

SEP = "=" * 78


# ---------------------------------------------------------------------------
# 代表性规则（按 RuleMethod.id 固定，保证可复现）
# ---------------------------------------------------------------------------
PICKED_RULES = [
    (623, "R1 纯数值·单前件"),
    (31, "R2 纯数值·缺陷前件+参数门控"),
    (1427, "R3 百分比动作"),
    (88, "R4 提示类(adjust)"),
]


def rule_line(char="-"):
    print(char * 78)


def kv(key, value):
    print(f"      {key:<22} {value}")


def sample_value(keyword_name, ratio=0.75):
    """示例参数值：取 RuleKeyword 论域的 ratio 分位（确定性，可复现）。

    ratio=0.75 ⇒ 「参数偏高」工况，正好检验 high 档位语义。
    """
    kw = RuleKeyword.objects.filter(
        keyword_name=keyword_name, is_deleted=False).first()
    if not kw:
        return None
    return round(float(kw.range_min) + ratio * (
        float(kw.range_max) - float(kw.range_min)), 4)


def load_keywords(names):
    """完全复用生产路径的元数据加载（get_keywords_by_names 内不排序 ⇒ 隐式契约）。"""
    return RuleKeywordAdapter.get_keywords_by_names(sorted(names))


def membership_degrees(net, x):
    """复刻 nets.NumTskRuleNet.tsk_inference 的第一层（隶属度层）。"""
    num_degrees = net.connected_matrix.shape[1]
    degrees = np.zeros(shape=(num_degrees,)) + 1e-7
    for k in x:
        if k not in net.pre_set:
            continue
        if not net.pre_dict[k]:
            continue
        idx = net.pre_dict[k]['index']
        f_k = net.pre_dict[k]['memberships']
        for i in range(f_k.f_level):
            degrees[idx + i] = f_k.get_value_by_level(x[k], i)
    return degrees


def trace_single_rule(rule, tag):
    """单规则网：把一条规则的 8 个阶段逐个摊开。"""
    rule_line("=")
    print(f"{tag}")
    rule_line("=")

    desc = rule.rule_description.strip()
    kv("RuleMethod.id", rule.id)
    kv("defect_code", rule.defect_code)
    kv("polymer / product", f"{rule.polymer_abbreviation} / {rule.product_category}")
    kv("priority", rule.priority)
    kv("rule_description", desc)

    # ---- 阶段 1：词法解析 ----
    rule_line()
    print("  【阶段1】词法解析 parse_rule()")
    parsed = parse_rule(desc)
    for p in parsed['preconditions']:
        kv("  前件", f"name={p.get('name')!r} level={p.get('level')!r} "
                     f"kind={p.get('kind')!r} "
                     f"类别={classify_name(p.get('name'))}")
    for s in parsed['solutions']:
        kv("  结论", f"name={s.get('name')!r} action={s.get('action')!r} "
                     f"value={s.get('value')!r} kind={s.get('kind')!r}")

    # ---- 阶段 2：校验 ----
    rule_line()
    print("  【阶段2】校验（是否有元数据 / 档位词是否合法）")
    param_names = set()
    for p in parsed['preconditions']:
        n = p.get('name')
        if classify_name(n) == 'defect' or n.startswith('DL'):
            continue
        param_names.add(n)
    for s in parsed['solutions']:
        if s.get('name'):
            param_names.add(s['name'])
    kw_map = {k['keyword']: k for k in load_keywords(param_names)}
    for p in parsed['preconditions']:
        n = p.get('name')
        lvl = str(p.get('level', '')).lower()
        if classify_name(n) == 'defect':
            kv("  前件·缺陷", f"{n}_{lvl} → 不参与激活（缺陷无连续论域）")
            continue
        if n not in kw_map:
            kv("  前件·参数", f"{n}_{lvl} → ✗ 无 RuleKeyword 元数据 ⇒ 静默跳过")
            continue
        if not is_level_word(lvl):
            kv("  前件·参数", f"{n}_{lvl} → ✗ 档位词非法（非 level word）⇒ 跳过")
            continue
        meta = kw_map[n]
        try:
            bucket_e2 = resolve_bucket(meta['lvl'], lvl)
        except ValueError as e:
            bucket_e2 = f"ERR({e})"
        bucket_now = LEGACY_HS_MAPPING_DICT.get(lvl)
        mark = "  ⚠️ 桶语义不一致" if bucket_e2 != bucket_now else ""
        kv("  前件·参数", f"{n}_{lvl} → 元数据有 ✓ lvl={meta['lvl']} "
                          f"论域=[{meta['min_val']},{meta['max_val']}] "
                          f"现行桶={bucket_now} E2桶={bucket_e2}{mark}")

    # ---- 阶段 3：模糊化（隶属度函数参数） ----
    rule_line()
    print("  【阶段3】模糊化 FuzzyFeature（峰位 / σ）")
    if not kw_map:
        print("      （无参数元数据，无隶属度函数）")
    for name, meta in kw_map.items():
        lvl_n = meta['lvl']
        lo, hi = meta['min_val'], meta['max_val']
        sigma = (hi - lo) / (2 * (lvl_n - 1))
        means = np.r_[lo, np.quantile([lo, hi],
                                      np.arange(1, lvl_n - 1) / (lvl_n - 1)), hi]
        words = LEVEL_WORDS_BY_LVL.get(lvl_n, ())
        print(f"      {name}: lvl={lvl_n} 论域=[{lo}, {hi}] σ={sigma}")
        for i in range(lvl_n):
            word = words[i] if i < len(words) else "?"
            print(f"        桶{i}  峰位={float(means[i]):>8.3f}  σ={sigma:>8.3f}"
                  f"  词表[{i}]={word!r}")

    # ---- 阶段 4~6：列布局 / 矩阵置位 / 每列隶属度 ----
    rule_line()
    print("  【阶段4-6】列布局 / 矩阵置位 / 每列隶属度")

    is_check = any(s.get('action') in ('adjust', 'popup')
                   for s in parsed['solutions'])
    if is_check:
        print("      ⚠️ 该规则被 NumTskRuleNet._is_check_rule 排除（结论是 adjust/popup）")
        print("      ⇒ rule_nums=0、connected_matrix 形状=(0, 0)")
        print("      ⇒ 不进入数值层推理；走【提示层】路径（见下方 advisory 段）")
        return {
            'rule_id': rule.id,
            'desc': desc,
            'activation': None,
            'has_gate': None,
            'layer': 'advisory',
        }

    rule_array = [{'rule_description': desc}]
    keyword_dicts = load_keywords(param_names)
    net = NumTskRuleNet(rule_array, keyword_dicts, [float(rule.priority or 1.0)])

    for name, meta in net.pre_dict.items():
        idx = meta['index']
        print(f"      前件字段 {name}: index={idx} "
              f"列区间=[{idx}, {idx + meta['lvl'] - 1}] lvl={meta['lvl']}")
    for name, meta in net.sol_dict.items():
        print(f"      结论字段 {name}: index={meta['index']} (TSK 输出占 1 列)")

    row = 0
    nz = np.nonzero(net.connected_matrix[row])[0]
    print(f"      connected_matrix 形状={net.connected_matrix.shape} "
          f"第 {row} 行非零列={list(nz)}")
    if len(nz):
        for c in nz:
            owner = None
            for name, meta in net.pre_dict.items():
                if meta['index'] <= c < meta['index'] + meta['lvl']:
                    owner = name
            print(f"        列{c} ← 字段 {owner} 的桶 {c - net.pre_dict[owner]['index']}")

    # 示例参数值
    x = {}
    for p in parsed['preconditions']:
        n = p.get('name')
        if classify_name(n) == 'defect' or n.startswith('DL'):
            continue
        if n in kw_map:
            x[n] = sample_value(n)
    print(f"      示例参数值: {x}")
    degrees = membership_degrees(net, x)
    for name, meta in net.pre_dict.items():
        idx = meta['index']
        vals = [round(float(v), 6) for v in degrees[idx:idx + meta['lvl']]]
        print(f"        {name} 隶属度(桶0..{meta['lvl'] - 1}) = {vals}")

    # ---- 阶段 7：激活度 ----
    rule_line()
    print("  【阶段7】规则激活度（prod 连接）")
    rule_matrix = net.connected_matrix * degrees
    conditions = rule_matrix[row, rule_matrix[row] != 0]
    activation = float(np.prod(conditions)) if conditions.size else 0.0
    kv("  参与相乘的门控列", list(np.nonzero(conditions)[0]))
    kv("  各门控隶属度", [round(float(c), 6) for c in conditions])
    kv("  激活度 (prod)", round(activation, 8))
    if conditions.size == 0:
        print("      ⚠️ 无任何门控列 ⇒ 激活度恒为 0 ⇒ 该规则在数值层**完全失效**")

    # ---- 阶段 8：归一化 + 最终建议 ----
    rule_line()
    print("  【阶段8】归一化权重 + 最终建议（单规则网 ⇒ 权重=1）")
    acts = np.array([activation])
    norm = activation / max(acts.sum(), 1e-7)
    kv("  activations_sum", round(float(acts.sum()), 8))
    kv("  归一化权重", round(float(norm), 8))
    kv("  priority 加权后", round(float(norm * (rule.priority or 1.0)), 8))
    for name, meta in net.sol_dict.items():
        val = float(net.solution_matrix[row][meta['index']])
        kv("  solution_matrix", f"{name} = {val}")
        if x.get(name) is not None and net.rule_classify[row] == 1:
            kv("  百分比基准", f"当前值 {x[name]} × {val} = "
                              f"{round(x[name] * val, 6)}")
        kv("  delta = 结论值 × 权重", round(val * float(norm), 8))
    return {
        'rule_id': rule.id,
        'desc': desc,
        'activation': activation,
        'has_gate': bool(conditions.size),
        'layer': 'numeric',
    }


def scenario_production(ratio=0.75, label='偏高工况'):
    """生产规模场景：真实上下文 → 真实规则集 → 完整推理 → 最终推荐。

    ratio: 示例工艺参数统一取论域的 ratio 分位（0.75=偏高 / 0.25=偏低）。
    """
    rule_line("=")
    print(f"【生产规模场景 · {label}】缺陷=SHORTSHOT/high 材料=PP 产品=酒瓶")
    rule_line("=")

    ctx = RuleQueryContext(
        defect_name='SHORTSHOT',
        defect_level='high',
        defect_position=None,
        polymer_abbreviation='PP',
        product_category='酒瓶',
        rule_library_code=None,
    )
    rules = RuleQueryService.get_rules(ctx)
    kv("命中规则数", len(rules))
    split = RuleQueryService.split_by_conclusion_kind(rules)
    kv("  数值层 numeric", len(split['numeric']))
    kv("  提示层 advisory", len(split['advisory']))

    numeric_rules = split['numeric']
    param_names = set()
    for r in numeric_rules:
        for p in parse_rule(r.rule_str)['preconditions']:
            n = p.get('name')
            if classify_name(n) == 'defect' or n.startswith('DL'):
                continue
            param_names.add(n)
        for s in parse_rule(r.rule_str)['solutions']:
            if s.get('name'):
                param_names.add(s['name'])

    keyword_dicts = load_keywords(param_names)
    kv("涉及参数数", len(param_names))
    kv("命中元数据数", len(keyword_dicts))
    missing = sorted(param_names - {k['keyword'] for k in keyword_dicts})
    kv("无元数据参数", missing)

    # 示例工艺参数：按论域 ratio 分位
    x = {}
    for name in sorted(param_names):
        v = sample_value(name, ratio=ratio)
        if v is not None:
            x[name] = v
    kv("示例参数取值", f"论域 {ratio:.0%} 分位 → {x}")

    net = NumTskRuleNet(
        RuleQueryService.to_rule_array(numeric_rules),
        keyword_dicts,
        RuleQueryService.get_priority_array(numeric_rules),
    )
    kv("矩阵形状", net.connected_matrix.shape)

    # 归一化【前】的原始激活度（prod 结果），用于看清门控本身的强度
    degrees = membership_degrees(net, x)
    rule_matrix = net.connected_matrix * degrees
    raw_acts = []
    for i in range(net.rule_nums):
        conds = rule_matrix[i, rule_matrix[i] != 0]
        raw_acts.append(float(np.prod(conds)) if conds.size else 0.0)
    print("\n  --- 逐规则原始激活度（归一化前）---")
    for i in range(net.rule_nums):
        gate_cols = np.nonzero(rule_matrix[i])[0]
        gates = []
        for c in gate_cols:
            for fname, fmeta in net.pre_dict.items():
                if fmeta['index'] <= c < fmeta['index'] + fmeta['lvl']:
                    gates.append(f"{fname}#{c - fmeta['index']}")
                    break
        print(f"      {net.rule_dict[i].r_rule:<62} "
              f"raw={raw_acts[i]:.8f}  门控={gates}")

    results, extra = net.predict(x, top_k=len(numeric_rules))
    acts = np.array([r[1] for r in results])
    kv("激活度>0 的规则数", int((acts > 0).sum()))
    kv("激活度最大值", round(float(acts.max()) if acts.size else 0.0, 8))
    kv("激活度之和(归一化分母)", round(float(acts.sum()), 8))

    print("\n  --- 权重 Top 12 ---")
    for rule_str, activation, adjustments in results[:12]:
        kv("规则", rule_str)
        kv("  归一化权重×priority", round(float(activation), 8))
        for p, v in adjustments.items():
            kv("  结论", f"{p} = {round(float(v), 6)}")
    # 聚合到参数级（复刻 FuzzyEngine._merge_layer_results 的同层聚合）
    merged = OrderedDict()
    for rule_str, activation, adjustments in results:
        for p, v in adjustments.items():
            cur = merged.setdefault(p, {'delta': 0.0, 'act': 0.0, 'n': 0})
            cur['delta'] += float(v) * float(activation)
            cur['act'] += float(activation)
            cur['n'] += 1

    print("\n  --- 参数级聚合结果（推荐值 = 当前值 + delta）---")
    for p, info in merged.items():
        cur_val = x.get(p, 0.0)
        print(f"      {p:<10} 当前={cur_val:>9.3f}  规则数={info['n']:<3} "
              f"激活度合计={round(info['act'], 6):<10} "
              f"delta={round(info['delta'], 6):>10}  "
              f"推荐={round(cur_val + info['delta'], 4)}")
    return merged, x


def analyze_zero_gate_rules():
    """全库量化：有多少规则在数值层**没有任何有效门控**（激活度恒为 0）。"""
    rule_line("=")
    print("【全库量化】无有效门控的规则（激活度恒 0）")
    rule_line("=")

    kw_names = set(RuleKeyword.objects.filter(is_deleted=False)
                   .values_list('keyword_name', flat=True))
    all_rules = list(RuleMethod.objects.filter(
        is_deleted=False, is_active=True).values_list('id', 'rule_description'))

    zero_gate = []
    with_worse = 0
    numeric_total = 0
    for rid, desc in all_rules:
        parsed = parse_rule(desc)
        sols = parsed['solutions']
        if any(s.get('action') in ('adjust', 'popup') for s in sols):
            continue                      # 提示类不进数值层
        numeric_total += 1
        gates = []
        worse_seen = False
        for p in parsed['preconditions']:
            n = p.get('name')
            lvl = str(p.get('level', '')).lower()
            if lvl == 'worse':
                worse_seen = True
                continue
            if classify_name(n) == 'defect' or n.startswith('DL'):
                continue                  # 缺陷/缺陷位置：不参与激活
            if not is_level_word(lvl):
                continue                  # 非法档位词：跳过
            if n not in kw_names:
                continue                  # 无元数据：跳过
            gates.append(f"{n}_{lvl}")
        if worse_seen:
            with_worse += 1
        if not gates:
            zero_gate.append((rid, desc))

    kv("数值层规则总数", numeric_total)
    kv("含 worse 前件的规则数", with_worse)
    kv("无有效门控（激活度恒 0）", len(zero_gate))
    pct = len(zero_gate) / max(numeric_total, 1)
    kv("占比", f"{pct:.2%}")

    # 按成因分类
    reason_cnt = {'仅缺陷前件': 0, '仅 worse 前件': 0, '其他': 0}
    for rid, desc in zero_gate:
        parsed = parse_rule(desc)
        pres = parsed['preconditions']
        non_defect = [p for p in pres
                      if classify_name(p.get('name')) != 'defect'
                      and not str(p.get('name', '')).startswith('DL')]
        if not non_defect:
            reason_cnt['仅缺陷前件'] += 1
        elif all(str(p.get('level', '')).lower() == 'worse' for p in non_defect):
            reason_cnt['仅 worse 前件'] += 1
        else:
            reason_cnt['其他'] += 1
    print("      --- 无门控成因分布 ---")
    for k, v in reason_cnt.items():
        kv(f"  {k}", v)

    print("\n      --- 无有效门控的规则清单 ---")
    for rid, desc in zero_gate[:20]:
        print(f"        #{rid:<6} {desc}")
    if len(zero_gate) > 20:
        print(f"        ...（其余 {len(zero_gate) - 20} 条见脚本输出）")
    return zero_gate


def verify_against_real_engine(x, merged):
    """对拍：直接跑真实编排层 FuzzyEngine.recommend，与本脚本复刻的聚合逐项比对。

    目的：避免「自证式测试」——本脚本的聚合逻辑是手写复刻的，
    必须用真实引擎输出验证，否则等于自己证明自己。
    """
    from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine

    rule_line("=")
    print("【对拍】真实 FuzzyEngine.recommend() vs 本脚本复刻的聚合")
    rule_line("=")

    context = {
        'feedback': {'defect': [{'keyword_name': 'SHORTSHOT',
                                 'level': 'high', 'position': None}]},
        'process_parameter': dict(x),
        'iteration_trend': {'trend': 'stable'},
        'machine_info': {},
        'polymer_info': {'abbreviation': 'PP'},
        'mold_info': {'product_category': '酒瓶'},
        'rule_library_code': None,
    }
    engine = FuzzyEngine()
    recs = engine.recommend(context)

    real = {r.param_name: r for r in recs}
    kv("真实引擎 Recommendation 数", len(recs))

    ok = True
    print(f"      {'参数':<10} {'复刻 delta':>14} {'真实 delta':>14}  一致")
    for p, info in merged.items():
        r = real.get(p)
        if r is None:
            print(f"      {p:<10} {info['delta']:>14.6f} {'<缺失>':>14}  ✗")
            ok = False
            continue
        real_delta = (r.recommended_value - r.current_value)
        same = abs(real_delta - info['delta']) < 1e-6
        ok = ok and same
        print(f"      {p:<10} {info['delta']:>14.6f} {real_delta:>14.6f}  "
              f"{'✓' if same else '✗'}")
    print(f"      => 对拍结果: {'全部一致 ✓' if ok else '存在差异 ✗'}")
    return ok


def bucket_semantics():
    """量化 ❶：现行 LEGACY_HS_MAPPING_DICT vs resolve_bucket 的桶语义差异及其影响。"""
    rule_line("=")
    print("【档位语义对照】5 档字段上 low/medium/high 的桶与峰位")
    rule_line("=")
    words = LEVEL_WORDS_BY_LVL[5]
    print(f"      5 档词表 LEVEL_WORDS_BY_LVL[5] = {words}")
    print(f"      现行 LEGACY_HS_MAPPING_DICT: low={LEGACY_HS_MAPPING_DICT['low']} "
          f"medium={LEGACY_HS_MAPPING_DICT['medium']} high={LEGACY_HS_MAPPING_DICT['high']}")
    print(f"      E2  resolve_bucket : "
          f"low={resolve_bucket(5, 'low')} "
          f"medium={resolve_bucket(5, 'medium')} "
          f"high={resolve_bucket(5, 'high')}")
    print()
    print("      峰位分布（论域归一化到 0~1）：")
    for name, bucket in (('low', LEGACY_HS_MAPPING_DICT['low']),
                         ('medium', LEGACY_HS_MAPPING_DICT['medium']),
                         ('high', LEGACY_HS_MAPPING_DICT['high'])):
        e2 = resolve_bucket(5, name)
        print(f"        {name:<7} 现行桶{bucket} → 峰位 {bucket / 4:.0%}"
              f"   |  E2桶{e2} → 峰位 {e2 / 4:.0%}")

    print()
    print("      影响量化：参数取论域 75% 分位时，「high」门控的隶属度")
    lo, hi = 0.0, 120.0
    sigma = (hi - lo) / (2 * (5 - 1))
    peak_gap = 2 * sigma          # 相邻桶峰位间距 = 论域宽 / (lvl-1)
    x = lo + 0.75 * (hi - lo)
    m_now = float(np.exp(-((x - (lo + 2 * peak_gap)) ** 2) / (2 * sigma ** 2)))
    m_e2 = float(np.exp(-((x - (lo + 3 * peak_gap)) ** 2) / (2 * sigma ** 2)))
    print(f"        IV0=75%分位={x} σ={sigma}")
    print(f"        现行语义(high→桶2,峰位{lo + 2 * peak_gap}) → 隶属度 {m_now:.6f}")
    print(f"        E2 语义(high→桶3,峰位{lo + 3 * peak_gap}) → 隶属度 {m_e2:.6f}")
    print(f"        => 同一条规则的门控强度相差 {m_e2 / max(m_now, 1e-9):.2f} 倍")


def main():
    print(SEP)
    print("Step 1 · 一条规则的旅程（真实数据）")
    print(SEP)

    bucket_semantics()

    print()
    rule_line("=")
    print("【单规则逐阶段追踪】")
    rule_line("=")

    summaries = []
    for rid, tag in PICKED_RULES:
        rule = RuleMethod.objects.filter(id=rid, is_deleted=False).first()
        if not rule:
            print(f"\n[跳过] RuleMethod#{rid} 不存在")
            continue
        print()
        summaries.append(trace_single_rule(rule, tag))

    print()
    rule_line("=")
    print("【提示类规则的编排层路径】")
    rule_line("=")
    for rid, tag in PICKED_RULES:
        rule = RuleMethod.objects.filter(id=rid, is_deleted=False).first()
        if not rule:
            continue
        sols = parse_rule(rule.rule_description)['solutions']
        for s in sols:
            if s.get('action') in ('adjust', 'popup'):
                print(f"  #{rid} {rule.rule_description}")
                print(f"    -> RuleQueryService.classify_conclusion_kind = 'advisory'")
                print(f"    -> FuzzyEngine._is_check_rule = True")
                print(f"    -> 提示文本 advice = {s.get('value')!r}")
                print(f"    -> delta=0.0, recommended_value=None, direction='check'")
                print(f"    -> ⚠️ 不参与数值层聚合（不进 NumTskRuleNet）")
                print(f"    -> ⚠️ 前件 CLAMP_worse 不是档位词 ⇒ 即使进数值层也无门控")
                break

    print()
    merged, x = scenario_production(0.75, '偏高工况（论域 75% 分位）')
    print()
    scenario_production(0.25, '偏低工况（论域 25% 分位）')
    print()
    verify_against_real_engine(x, merged)
    print()
    analyze_zero_gate_rules()

    print()
    rule_line("=")
    print("【单规则追踪小结】")
    rule_line("=")
    for s in summaries:
        if s['layer'] == 'advisory':
            print(f"  #{s['rule_id']:<6} activation={'n/a':<12} 提示层（不进数值层）")
        else:
            gate = "有门控" if s['has_gate'] else "无门控 => 激活度恒 0"
            print(f"  #{s['rule_id']:<6} activation={s['activation']:.8f}  {gate}")
        print(f"          {s['desc']}")


if __name__ == '__main__':
    main()