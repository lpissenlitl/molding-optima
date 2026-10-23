"""桶位移影响面实测：接线 resolve_bucket 后规则行为会怎么变（2026-10-23 第 12 轮）

只读脚本：不写库、不改代码。

回答两个问题：
  1. `sanity_check.py` 的 `case_numeric_layer` 断言是否真的在测「优先级加权」？
     （若前件被跳过 ⇒ 激活度全 0 ⇒ 排序退化为输入顺序 ⇒ 断言空转）
  2. 接线 `resolve_bucket`（按字段级数取桶）后，存量规则的激活度 / 命中率会怎么变？

第 2 问的做法：**不改 nets.py**，而是直接复用 `FuzzyFeature`（高斯参数与现网完全一致）
+ 复刻 `tsk_inference` 的激活度公式（各项 μ 相乘），对同一条规则分别用
「静态桶」和「正确桶」算 μ 再对比。样本取 `ProcessParameter` 实验数据
（经 `_normalize_field_name_by_spec` 归一，与引擎取数路径一致）。

⚠️ 本脚本是**接线前的历史影响面快照**。2026-10-23 已完成接线并整表删除
`HS_MAPPING_DICT` ⇒ 脚本自带旧表快照 `LEGACY_HS_MAPPING_DICT` 复现旧口径做 A/B 对照。

运行：cd backend; python _dev_refs/diag_fuzzy_bucket_shift_impact.py
"""

import collections
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="gbk", errors="replace")
except Exception:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

import numpy as np

_FUZZY_DIR = os.path.join(_BACKEND, "process", "algorithms", "fuzzy")
if _FUZZY_DIR not in sys.path:
    sys.path.insert(0, _FUZZY_DIR)

from fuzzy_core.models.nets import FuzzyFeature, NumTskRuleNet  # noqa: E402
from fuzzy_core.macros import (  # noqa: E402
    EPSILON as EPSILON_CONST,
    LEVEL_WORDS_BY_LVL,
    MIN_ACTIVATION_THRESHOLD,
    resolve_bucket,
)
from fuzzy_core.parsing import is_level_word, split_phase  # noqa: E402

from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine  # noqa: E402
from process.models import ProcessParameter  # noqa: E402
from process.models.rules import RuleKeyword, RuleMethod  # noqa: E402
from process.services.parameter_optimize import _normalize_field_name_by_spec  # noqa: E402

# 旧版全局静态档位表快照（2026-10-23 已从 macros.py 整表删除）：
# 见 `_dev_refs/_legacy_bucket_map.py` —— 本脚本做 A/B 对照需要**旧口径**。
from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT  # noqa: E402


RULE_RE = re.compile(r"^IF\s+(.+?)\s+THEN\s+(.+)$", re.S)


def hr(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def parse_preconditions(rule_desc):
    """抽取规则的前件 (参数名, 档位词)。"""
    m = RULE_RE.match(rule_desc.strip())
    if not m:
        return []
    out = []
    for part in m.group(1).split(" AND "):
        info = split_phase(part)
        name = info.get("name", "")
        level = str(info.get("level", "")).lower()
        if not name or not level:
            continue
        out.append((name, level))
    return out


def _rule_act(gates, ctx, feat, use_correct):
    """单条规则在给定上下文下的激活度（只算在 x 里有值的门控）。

    use_correct=False ⇒ 用旧版静态桶；True ⇒ 用 resolve_bucket 的正确桶。
    """
    a = 1.0
    for name, level, lvl, sb, cb in gates:
        if name not in ctx:
            continue
        try:
            xval = float(ctx[name])
        except (TypeError, ValueError):
            continue
        bucket = cb if use_correct else sb
        a *= float(feat(name, lvl).get_value_by_level(xval, bucket))
    return a


def load_contexts():
    """实验数据归一化成引擎口径的上下文 dict 列表。"""
    pps = list(ProcessParameter.objects.all())
    ctxs = []
    for pp in pps:
        raw = {
            f.name: getattr(pp, f.name, None)
            for f in ProcessParameter._meta.get_fields()
            if f.get_internal_type() in ("FloatField", "IntegerField", "DecimalField")
        }
        raw = {k: v for k, v in raw.items() if v is not None}
        if not raw:
            continue
        norm = _normalize_field_name_by_spec(
            raw,
            FuzzyEngine.FIELD_NAME_ALIAS,
            FuzzyEngine.FIELD_INDEX_OFFSET,
        )
        if norm:
            ctxs.append(norm)
    return ctxs


def main():
    # ======================================================================
    hr("1. sanity_check.case_numeric_layer 的断言强度核查")
    print("  复刻 sanity_check.py 的 CASE 1 场景，检查它到底在测什么")
    print()
    rule_array = [
        {"rule_description": "IF SHORTSHOT_high THEN inj_pres_1_add_10"},
        {"rule_description": "IF SHORTSHOT_high THEN inj_pres_2_add_5"},
    ]
    keyword_array = [
        {"keyword": "inj_pres_1", "lvl": 3, "min_val": 0, "max_val": 200, "step": 10},
        {"keyword": "inj_pres_2", "lvl": 3, "min_val": 0, "max_val": 200, "step": 5},
    ]
    x = {"SHORTSHOT": -0.7, "inj_pres_1": 50, "inj_pres_2": 80}

    net = NumTskRuleNet(rule_array, keyword_array, [10.0, 5.0])
    print("  connected_matrix（门控连接矩阵，1 = 该规则接了哪个桶）:")
    print(net.connected_matrix)
    print()
    _, extra = net.predict(dict(x), top_k=5)
    res_a, _ = net.predict(dict(x), top_k=5)
    print("  priority=[10, 5] 的输出顺序:")
    for r in res_a:
        print(f"    activation={r[1]:.6f}  {r[0]}")
    print()
    print("  ⇒ SHORTSHOT 未出现在 keyword_array ⇒ pre_dict 取不到 ⇒ 前件被跳过")
    print("    ⇒ connected_matrix 全 0 ⇒ 激活度全 0 ⇒ 排序退化为【输入顺序】")
    print()
    net2 = NumTskRuleNet(rule_array, keyword_array, [5.0, 10.0])
    res_b, _ = net2.predict(dict(x), top_k=5)
    print("  priority=[5, 10]（把优先级反过来）的输出顺序:")
    for r in res_b:
        print(f"    activation={r[1]:.6f}  {r[0]}")
    same_order = [r[0] for r in res_a] == [r[0] for r in res_b]
    print()
    print(f"  ⇒ 优先级反转后输出顺序是否变化: {'是' if not same_order else '否（⇒ 断言空转）'}")
    print("    ⇒ sanity_check 的 'priority=10 应胜出' 断言无法证伪优先级逻辑")

    # ======================================================================
    hr("2. 规则库门控结构盘点")
    rules = list(
        RuleMethod.objects.filter(is_deleted=False).filter(is_active=True)
        .values_list("rule_description", "priority")
    )
    priorities = [float(p or 1) for _, p in rules]
    rule_descs = [d for d, _ in rules]
    kws = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}
    ctxs = load_contexts()

    rule_gates = {}          # rule_idx -> [(name, level, lvl, static_bucket, correct_bucket)]
    no_meta = 0
    unresolvable = 0
    for idx, desc in enumerate(rule_descs):
        gates = []
        for name, level in parse_preconditions(desc):
            if not is_level_word(level):
                continue
            kw = kws.get(name)
            if kw is None:
                no_meta += 1
                continue
            lvl = int(kw.fuzzy_level or 3)
            try:
                correct = resolve_bucket(lvl, level)
            except ValueError:
                unresolvable += 1
                continue
            gates.append((name, level, lvl, LEGACY_HS_MAPPING_DICT[level], correct))
        rule_gates[idx] = gates

    total_gates = sum(len(v) for v in rule_gates.values())
    empty_gates = sum(1 for v in rule_gates.values() if not v)
    shifted = sum(
        1 for v in rule_gates.values()
        if any(g[3] != g[4] for g in v)
    )
    print(f"  启用规则数                 : {len(rules)}")
    print(f"  门控引用总数（可判级+有元数据）: {total_gates}")
    print(f"  ★ 门控桶会位移的规则数      : {shifted} ({shifted * 100 // max(len(rules), 1)}%)")
    print(f"  无门控的规则数（激活恒 0）  : {empty_gates}")
    print(f"  前件缺 RuleKeyword 元数据    : {no_meta}")
    print(f"  resolve_bucket 无法解析      : {unresolvable}")

    lvl_cnt = collections.Counter(g[2] for v in rule_gates.values() for g in v)
    print(f"  门控字段级数分布            : {dict(sorted(lvl_cnt.items()))}")

    # 缺陷类字段抽查
    print()
    print("  缺陷类字段的论域/取值抽查（缺陷的档位语义与工艺参数相反）:")
    for dn in ["SHORTSHOT", "BURN", "AIRTRAP", "WELDLINE"]:
        kw = kws.get(dn)
        if not kw:
            continue
        vals = []
        for c in ctxs:
            if dn in c:
                try:
                    vals.append(float(c[dn]))
                except (TypeError, ValueError):
                    pass
        rng = f"[{kw.range_min}, {kw.range_max}]"
        span = f"实测取值 {min(vals):.3f}~{max(vals):.3f}" if vals else "实测取值 无"
        print(f"    {dn:<12} lvl={int(kw.fuzzy_level or 3)}  论域={rng:<12} {span}")

    # ======================================================================
    hr("3. 接线前后：逐样本 × 逐规则的激活度对比（静态桶 vs 正确桶）")
    print(f"  实验样本上下文数: {len(ctxs)}")
    print()
    print("  ⚠️ 建模要点（复刻 nets.py tsk_inference）：")
    print("     · membership_degrees 初值 = EPSILON(1e-7)；只有出现在 x 里的参数才会被真值覆盖")
    print("     · 缺陷字段（如 SHORTSHOT）**不在 process_parameter 里** ⇒ 其桶的隶属度恒为 1e-7")
    print("       ⇒ 缺陷门控对所有规则是【同一个常数因子】，不参与区分（两种映射下都一样）")
    print("     · 因此本次位移的**全部影响都落在工艺参数门控**上")
    print()

    # 预热：把每个 (name, lvl, bucket) 的 FuzzyFeature 缓存起来
    feat_cache = {}

    def feat(name, lvl):
        key = (name, lvl)
        if key not in feat_cache:
            kw = kws[name]
            feat_cache[key] = FuzzyFeature(
                name, [float(kw.range_min), float(kw.range_max)],
                f_level=lvl, f_membership_type="gauss",
            )
        return feat_cache[key]

    hit_delta = collections.Counter()
    abs_hits = []            # (接线前命中数, 接线后命中数)
    act_sum_static = []
    act_sum_correct = []
    top_overlap = []          # 每个样本 top-10 规则的重叠数
    top1_changed = 0
    delta_abs = []            # 逐样本 top-10 建议量级差

    for ctx in ctxs:
        s_act = {}
        c_act = {}
        for idx, gates in rule_gates.items():
            a_s = 1.0
            a_c = 1.0
            for name, level, lvl, sb, cb in gates:
                if name not in ctx:
                    continue          # 不在 x 里 ⇒ 恒为 EPSILON，两种映射相同 ⇒ 跳过
                try:
                    xval = float(ctx[name])
                except (TypeError, ValueError):
                    continue
                f = feat(name, lvl)
                a_s *= float(f.get_value_by_level(xval, sb))
                a_c *= float(f.get_value_by_level(xval, cb))
            s_act[idx] = a_s
            c_act[idx] = a_c

        s_sum = sum(s_act.values())
        c_sum = sum(c_act.values())
        act_sum_static.append(s_sum)
        act_sum_correct.append(c_sum)

        s_hits = sum(1 for v in s_act.values() if v > MIN_ACTIVATION_THRESHOLD)
        c_hits = sum(1 for v in c_act.values() if v > MIN_ACTIVATION_THRESHOLD)
        hit_delta[c_hits - s_hits] += 1
        abs_hits.append((s_hits, c_hits))

        # 排名（复刻 nets.py：归一化激活度 × priority，再按权重降序）
        def rank(act, total):
            return sorted(
                act,
                key=lambda i: -(act[i] / max(total, EPSILON_CONST)) * priorities[i],
            )

        s_rank = rank(s_act, s_sum)
        c_rank = rank(c_act, c_sum)
        top_s = set(s_rank[:10])
        top_c = set(c_rank[:10])
        top_overlap.append(len(top_s & top_c))
        if (s_rank[0] if s_rank else None) != (c_rank[0] if c_rank else None):
            top1_changed += 1

        # 建议量级：把 top-10 的归一化权重加起来（代表“建议强度分布”）
        delta_abs.append(
            (sum(c_act[i] / max(c_sum, EPSILON_CONST) for i in c_rank[:10]),
             sum(s_act[i] / max(s_sum, EPSILON_CONST) for i in s_rank[:10]))
        )

    print(f"  命中规则数（activation > {MIN_ACTIVATION_THRESHOLD}）变化分布:")
    ah = np.array(abs_hits)
    print(f"    样本数 : {len(ctxs)}")
    print(f"    绝对值：接线前 均值 {ah[:, 0].mean():.1f} / 中位 {np.median(ah[:, 0]):.0f}"
          f"   →   接线后 均值 {ah[:, 1].mean():.1f} / 中位 {np.median(ah[:, 1]):.0f}")
    for d in sorted(hit_delta):
        tag = "无变化" if d == 0 else ("↑ 增加" if d > 0 else "↓ 减少")
        print(f"    Δ={d:+4d} 条命中  : {hit_delta[d]:>3} 个样本   {tag}")
    print()
    s_arr = np.array(act_sum_static)
    c_arr = np.array(act_sum_correct)
    print(f"  激活度总和  静态: 均值 {s_arr.mean():.4f}  中位 {np.median(s_arr):.4f}")
    print(f"  激活度总和  正确: 均值 {c_arr.mean():.4f}  中位 {np.median(c_arr):.4f}")
    ratio = np.divide(c_arr, s_arr, out=np.ones_like(c_arr), where=s_arr > 0)
    print(f"  逐样本激活度比值 正确/静态: 均值 {ratio.mean():.4f}  "
          f"最小 {ratio.min():.4f}  最大 {ratio.max():.4f}")
    print()
    ov = np.array(top_overlap)
    print(f"  ★ top-10 规则重叠度（接线前 vs 接线后）: 均值 {ov.mean():.2f}/10  "
          f"最小 {ov.min()}/10  最大 {ov.max()}/10")
    print(f"  ★ top-1 首位规则发生变化的样本数: {top1_changed}/{len(ctxs)}")
    print()
    dd = np.array([abs(c - s) for c, s in delta_abs])
    print(f"  top-10 归一化权重和  静态均值 {np.mean([s for _, s in delta_abs]):.4f}"
          f"  正确均值 {np.mean([c for c, _ in delta_abs]):.4f}")
    print(f"  两者的绝对差：均值 {dd.mean():.4f}  最大 {dd.max():.4f}")

    # 规则级：多少条规则从"能命中"变成"不能命中"
    lost = 0
    gained = 0
    both = 0
    for idx in rule_gates:
        s_fire = sum(
            1 for ctx in ctxs
            if _rule_act(rule_gates[idx], ctx, feat, False) > MIN_ACTIVATION_THRESHOLD
        )
        c_fire = sum(
            1 for ctx in ctxs
            if _rule_act(rule_gates[idx], ctx, feat, True) > MIN_ACTIVATION_THRESHOLD
        )
        if s_fire and not c_fire:
            lost += 1
        elif c_fire and not s_fire:
            gained += 1
        elif s_fire and c_fire:
            both += 1
    print()
    print(f"  规则级命中变化（在 {len(ctxs)} 个样本上）:")
    print(f"    接线前能命中、接线后不能 : {lost}")
    print(f"    接线前不能、接线后能命中 : {gained}")
    print(f"    两者都能命中              : {both}")

    # ======================================================================
    hr("5. 回归基准用例（B1~B7）的期望值验算")
    print("  场景：字段 inj_pres_1，lvl=5，论域 [0, 200]")
    f5 = FuzzyFeature("inj_pres_1", [0.0, 200.0], f_level=5, f_membership_type="gauss")
    print(f"  高斯参数：means={[round(m, 1) for m, _ in f5.membership_dict.values()]}  "
          f"sigma={list(f5.membership_dict.values())[0][1]}")
    print()
    print(f"  {'用例':<6}{'x':>8}{'档位词':>10}{'静态桶':>8}{'μ(静态)':>12}"
          f"{'正确桶':>8}{'μ(正确)':>12}")
    print("  " + "-" * 68)
    for tag, x, word in [
        ("B1", 150.0, "high"),
        ("B2", 50.0, "low"),
        ("B3", 50.0, "high"),
    ]:
        sb = LEGACY_HS_MAPPING_DICT[word]
        cb = resolve_bucket(5, word)
        mu_s = float(f5.get_value_by_level(x, sb))
        mu_c = float(f5.get_value_by_level(x, cb))
        print(f"  {tag:<6}{x:>8.1f}{word:>10}{sb:>8}{mu_s:>12.6f}{cb:>8}{mu_c:>12.6f}")
    print()
    print("  ⇒ B1/B2：接线前 μ=0.1353（错位到相邻桶）、接线后 μ=1.0 ⇒ 【能证伪的断言】")
    print("  ⇒ B3：x=50 时 high 桶 μ=exp(-8)≈0.0003 ⇒ low 与 high 不重叠")
    print()
    print("  3 档向后兼容（lvl=3, [0,200]）：means=[0,100,200], sigma=25")
    f3 = FuzzyFeature("inj_pres_1", [0.0, 200.0], f_level=3, f_membership_type="gauss")
    for word in ("low", "medium", "high"):
        sb = LEGACY_HS_MAPPING_DICT[word]
        cb = resolve_bucket(3, word)
        print(f"    {word:<8} 静态桶={sb}  正确桶={cb}  ⇒ {'一致 ✓' if sb == cb else '不一致 ✗'}")
    print()
    print("  ⇒ B5：3 档下静态表与 resolve_bucket 完全一致 ⇒ 接线对 3 档字段零影响")

    # ======================================================================
    hr("6. 结论")
    print(f"  1. sanity_check.case_numeric_layer 的优先级断言"
          f"{'【空转 —— 激活度全 0，排序=输入顺序】' if same_order else '【有效】'}")
    print(f"  2. 接线 resolve_bucket 后，{shifted}/{len(rules)} 条规则的门控桶会位移")
    print(f"  3. 逐样本命中规则数变化：{dict(sorted(hit_delta.items()))}")
    print(f"  4. 激活度总和均值：{s_arr.mean():.4f} → {c_arr.mean():.4f}")
    print()
    print("  ⇒ 建议：接线前必须先补【真断言】的 lvl=5 回归基准，")
    print("    否则无法证明『改对了』，也无法量化『改了多少』。")

    print()
    print("=" * 100)
    print("影响面实测结束（只读，未写库、未改代码）")
    print("=" * 100)


if __name__ == "__main__":
    main()
