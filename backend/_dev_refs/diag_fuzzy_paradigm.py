"""度量：模糊推理在这个场景里的**边际贡献**到底有多大

2026-10-22

回答一个设计层面的问题：「这部分用模糊推理是否合适？」

在讨论实现之前先量化一个事实：
  模糊推理相对「硬阈值 + 查表」的唯一独特优势 = **软性折中**，
  即在多条规则同时部分成立时按隶属度加权，而不是非黑即白。

如果这个优势在当前规则库 + 真实工艺参数上几乎不起作用，
那么引入整套模糊推理（隶属度、矩阵门控、归一化）的成本就远超收益。

度量项（全部在「已修正」语义 S3 下计算 —— 现状语义是错的，指标无意义）：
  M1  命中规则数分布           → 每次推理有几条规则参与
  M2  激活度分布               → 命中规则是「满激活」还是「部分激活」
  M3  同参数并发命中数         → 同一参数上几条规则同时竞争（融合的前提）
  M4  模糊化的边际贡献         → 把激活度二值化后，输出变化多少
  M5  单命中场景占比           → 只命中 1 条时模糊推理完全无作用
  M6  建议值 vs 规则写的调整量 → 是不是就是个查表系统

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_paradigm.py
"""

import os
import sys
from collections import Counter, defaultdict

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

import numpy as np

from process.models.rules import RuleKeyword, RuleMethod
from process.algorithms.fuzzy.fuzzy_core.functional import gauss_mf
from process.algorithms.fuzzy.fuzzy_core.parsing import (
    classify_name,
    is_level_word,
    parse_rule,
)

MAX_SNAPSHOTS = 20
BINARY_THRESHOLD = 0.9      # 激活度 > 0.9 视为「满激活」
PARTIAL_LO = 0.05           # 激活度落在 (0.05, 0.9] 视为「部分激活」


def hr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# 档位词表（按参数自己的 fuzzy_level 定位桶 = E2 修法）
LEVEL_WORDS_BY_LVL = {
    3: ["low", "mid", "high"],
    5: ["very_low", "low", "mid", "high", "very_high"],
    7: ["extremely_low", "very_low", "low", "mid", "medium", "high", "very_high"],
}


def level_to_bucket(word, f_level):
    words = LEVEL_WORDS_BY_LVL.get(f_level) or LEVEL_WORDS_BY_LVL[3]
    w = str(word or "").lower()
    if w == "medium":
        w = "mid"
    return words.index(w) if w in words else None


def build_feature(kw):
    lo, hi = float(kw.range_min), float(kw.range_max)
    lvl = int(kw.fuzzy_level or 3)
    if hi <= lo:
        hi = lo + 1.0
    sigma = (hi - lo) / (2 * (lvl - 1))
    means = np.r_[lo, np.quantile([lo, hi], np.arange(1, lvl - 1) / (lvl - 1)), hi]
    return [float(m) for m in means], float(sigma)


def bucket_word(x_val, kw):
    """硬分桶：按分位点把 x 划入一个档位，返回该档位词。论域外返回 None。"""
    lo, hi = float(kw.range_min), float(kw.range_max)
    lvl = int(kw.fuzzy_level or 3)
    if hi <= lo:
        return None
    pos = (x_val - lo) / (hi - lo)
    if pos < 0.0 or pos > 1.0:
        return None
    words = LEVEL_WORDS_BY_LVL.get(lvl) or LEVEL_WORDS_BY_LVL[3]
    idx = min(int(pos * lvl), lvl - 1)
    return words[idx] if idx < len(words) else None


def infer_detail(rules, keywords, x, defects, defect_level, hard=False):
    """S3 语义推理（档位动态 + 按参数分组 + 缺陷前件不当门控），返回中间量。

    rules: [(rule_str, priority)]
    defects: 本次场景的缺陷名集合
    defect_level: 本次场景的缺陷档位
    hard=True 时用硬分桶代替高斯隶属度（离散查表对照组）
    """
    feats = {n: build_feature(kw) for n, kw in keywords.items() if n in x}
    per_param = defaultdict(list)
    detail = []          # (param, x_val, in_range, act)

    for desc, pri in rules:
        parsed = parse_rule(desc)
        acts = []
        for pre in parsed.get("preconditions", []) or []:
            name = str(pre.get("name") or "")
            lv = str(pre.get("level") or "").lower()
            if classify_name(name) == "defect":
                # 缺陷前件：路由层已按 (name, level) 精确筛选 → 完全匹配
                if name in defects and str(pre.get("level") or "").lower() == defect_level:
                    acts.append(1.0)
                continue
            if not is_level_word(lv) or name not in feats:
                continue
            kw = keywords[name]
            if hard:
                bw = bucket_word(x[name], kw)
                if bw is None:
                    acts.append(0.0)          # 论域外 → 不命中
                    detail.append((name, float(x[name]), False, 0.0))
                else:
                    w = "mid" if lv == "medium" else lv
                    if w == bw:
                        acts.append(1.0)
                    else:
                        acts.append(0.0)
                continue
            bucket = level_to_bucket(lv, int(kw.fuzzy_level or 3))
            if bucket is None or bucket >= len(feats[name][0]):
                continue
            means, sigma = feats[name]
            a = float(gauss_mf(x[name], means[bucket], sigma))
            acts.append(a)
            lo, hi = float(kw.range_min), float(kw.range_max)
            detail.append((name, float(x[name]), (lo <= x[name] <= hi), a))

        if not acts:
            continue
        activation = float(min(acts))          # 弱连接
        if activation <= 0.0:
            continue

        for sol in parsed.get("solutions", []) or []:
            name = str(sol.get("name") or "")
            action = sol.get("action")
            raw = str(sol.get("value") or "")
            if action not in ("add", "reduce"):
                continue
            try:
                value = float(raw.rstrip("%"))
            except ValueError:
                continue
            delta = value if action == "add" else -value
            if "%" in raw:
                delta = delta / 100.0 * float(x.get(name, 0) or 0)
            per_param[name].append((delta, activation, float(pri or 1.0)))

    return per_param, detail


def aggregate(per_param):
    """按参数分组：组内 priority×激活度 加权平均（权重和为 1）。"""
    out = {}
    for name, items in per_param.items():
        ws = [a * p for _, a, p in items]
        s = sum(ws)
        if s <= 0:
            continue
        out[name] = sum(d * w for (d, _, _), w in zip(items, ws)) / s
    return out


def main():
    from process.models import ProcessParameter
    from process.services.parameter_optimize import (
        _normalize_field_name_by_spec,
        _to_full_dict,
    )
    from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine

    # ---------------------------------------------------------- 数据准备
    hr("0. 数据准备")
    all_rules = [(rm.rule_description or "", float(rm.priority or 1.0))
                 for rm in RuleMethod.objects.filter(is_active=True).all()]

    kw_all = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}

    # 规则里出现过的缺陷名
    defect_names = set()
    for desc, _ in all_rules:
        for pre in parse_rule(desc).get("preconditions", []) or []:
            nm = str(pre.get("name") or "")
            if classify_name(nm) == "defect":
                defect_names.add(nm)
    print(f"规则里出现过的缺陷名 = {len(defect_names)} 个")

    # 参数现场快照
    snaps = list(ProcessParameter.objects.exclude(inj_spd_1=None)[:MAX_SNAPSHOTS])
    print(f"工艺参数快照 = {len(snaps)} 条")

    if not snaps:
        print("!! 没有可用快照")
        return 1

    algo_snapshots = []
    for p in snaps:
        business = {k: v for k, v in _to_full_dict(p).items()
                    if isinstance(v, (int, float))}
        algo = _normalize_field_name_by_spec(
            business,
            FuzzyEngine.FIELD_NAME_ALIAS,
            FuzzyEngine.FIELD_INDEX_OFFSET,
            FuzzyEngine.FAMILY_FIELD_ALIAS,
        )
        if algo:
            algo_snapshots.append(algo)
    print(f"可用快照 = {len(algo_snapshots)} 条")

    # 规则里用到的参数
    used = set()
    for desc, _ in all_rules:
        for pre in parse_rule(desc).get("preconditions", []) or []:
            used.add(str(pre.get("name") or ""))
        for sol in parse_rule(desc).get("solutions", []) or []:
            used.add(str(sol.get("name") or ""))
    keywords = {n: kw_all[n] for n in used if n in kw_all}
    print(f"涉及 RuleKeyword = {len(keywords)} 个")

    # 去重后的规则集（推理层去重，跨库副本不重复计入）
    seen = set()
    rules = []
    for desc, pri in all_rules:
        if desc in seen:
            continue
        seen.add(desc)
        rules.append((desc, pri))
    print(f"去重后规则 = {len(rules)} 条（原 {len(all_rules)} 条）")

    # ---------------------------------------------------------- 扫场景
    hr("1. 扫描推理场景")
    hit_counts = Counter()          # M1
    act_buckets = Counter()         # M2
    concur_counts = Counter()       # M3
    single_hit_scenes = 0           # M5
    total_scenes = 0
    diffs = []                      # M4
    changed = []                    # M4
    cont_vals = []                  # M6
    rule_vals = []                  # M6
    per_param_rule_n = Counter()    # 每个参数在一次场景里命中几条
    near_zero_out_of_range = 0      # M7
    near_zero_in_range = 0          # M7
    all_detail_out_of_range = 0     # M7
    all_detail_total = 0            # M7

    levels = ["low", "medium", "high"]
    for defect in sorted(defect_names):
        # 该缺陷相关规则
        d_rules = []
        for desc, pri in rules:
            parsed = parse_rule(desc)
            names = [str(p.get("name") or "") for p in
                     parsed.get("preconditions", []) or []]
            if defect in names:
                d_rules.append((desc, pri))
        if not d_rules:
            continue
        for level in levels:
            # 缺陷档位精确匹配（路由层语义）
            lvl_rules = []
            for desc, pri in d_rules:
                parsed = parse_rule(desc)
                ok = False
                for p in parsed.get("preconditions", []) or []:
                    nm = str(p.get("name") or "")
                    if nm == defect:
                        if str(p.get("level") or "").lower() == level:
                            ok = True
                        else:
                            ok = False
                            break
                if ok:
                    lvl_rules.append((desc, pri))
            if not lvl_rules:
                continue

            for algo in algo_snapshots:
                kws = {n: kw for n, kw in keywords.items() if n in algo}
                if not kws:
                    continue
                per_param, detail = infer_detail(lvl_rules, kws, algo,
                                                {defect}, level)
                if not per_param:
                    continue
                total_scenes += 1

                # M1 命中规则数
                cnt = sum(len(v) for v in per_param.values())
                hit_counts[cnt] += 1

                # M2 激活度分布
                for name, items in per_param.items():
                    for d, a, p in items:
                        if a >= BINARY_THRESHOLD:
                            act_buckets["满激活 (>=0.9)"] += 1
                        elif a > PARTIAL_LO:
                            act_buckets["部分激活 (0.05,0.9)"] += 1
                        else:
                            act_buckets["近零 (<=0.05)"] += 1

                # M3 同参数并发命中数
                for name, items in per_param.items():
                    concur_counts[len(items)] += 1
                    per_param_rule_n[(name, len(items))] += 1

                # M5 单命中
                if cnt == 1:
                    single_hit_scenes += 1

                # M7 近零激活度的归因：论域外 vs 论域内
                for name, xv, in_range, a in detail:
                    if a <= PARTIAL_LO:
                        if not in_range:
                            near_zero_out_of_range += 1
                        else:
                            near_zero_in_range += 1
                    all_detail_out_of_range += 0 if in_range else 1
                    all_detail_total += 1

                # M4 模糊版 vs 硬分桶版（真正的「模糊推理 vs 离散查表」对照）
                per_param_h, _ = infer_detail(lvl_rules, kws, algo,
                                              {defect}, level, hard=True)
                c = aggregate(per_param)
                b = aggregate(per_param_h)
                for name in set(c) | set(b):
                    cv = c.get(name) or 0.0
                    bv = b.get(name) or 0.0
                    denom = max(abs(cv), 1e-9)
                    diffs.append(abs(cv - bv) / denom)
                    if abs(cv - bv) > 1e-6:
                        changed.append((name, cv, bv))
                    cont_vals.append(cv)

                # M6 规则写的调整量
                for name, items in per_param.items():
                    for d, a, p in items:
                        rule_vals.append(d)

    # ---------------------------------------------------------- 报告
    hr("M1  每次推理命中的规则条数")
    if total_scenes:
        for k, v in sorted(hit_counts.items()):
            print(f"  {k:>3} 条: {v:>6} 场景 ({v / total_scenes * 100:5.1f}%)  "
                  + "#" * int(v / total_scenes * 50))
    print(f"  总场景数 = {total_scenes}")

    hr("M2  命中规则的激活度分布（模糊性是否真的在起作用）")
    tot_act = sum(act_buckets.values()) or 1
    for k, v in act_buckets.most_common():
        print(f"  {k:<24} {v:>7} 次 ({v / tot_act * 100:5.1f}%)  "
              + "#" * int(v / tot_act * 50))

    hr("M3  同一参数上并发命中的规则数（融合是否有意义）")
    tot_cc = sum(concur_counts.values()) or 1
    for k, v in sorted(concur_counts.items()):
        print(f"  {k:>3} 条: {v:>7} ({v / tot_cc * 100:5.1f}%)  "
              + "#" * int(v / tot_cc * 50))

    hr("M4  模糊推理 vs 离散查表（硬分桶）：输出差异多大")
    print("  对照组定义：高斯隶属度加权平均  vs  按分位点硬分桶 + 完全匹配")
    if diffs:
        arr = np.array(diffs)
        print(f"  样本 = {len(diffs)} 个（参数 × 场景）")
        print(f"  相对差异  中位数 = {np.median(arr) * 100:.2f}%")
        print(f"            90 分位 = {np.percentile(arr, 90) * 100:.2f}%")
        print(f"            最大   = {arr.max() * 100:.2f}%")
        for thr in (0.01, 0.05, 0.10, 0.20):
            print(f"  差异 > {thr * 100:>5.0f}% 的占比 = {(arr > thr).mean() * 100:5.1f}%")
        print(f"  两者输出**完全一致**的占比 = {(arr <= 1e-6).mean() * 100:.1f}%")
        print()
        print("  解读：差异 ≈ 0 ⇒ 把模糊推理换成硬阈值查表，输出基本不变")
        print("        差异大 ⇒ 软性折中是真实需求，不能退化成查表")
        if changed:
            print(f"\n  差异样本（前 10 个）：")
            for name, cv, bv in changed[:10]:
                print(f"    {name:<8} 模糊版={cv:+.4f}   查表版={bv:+.4f}")

    hr("M7  近零激活度从哪来？——论域失真的归因")
    nz = near_zero_out_of_range + near_zero_in_range
    if nz:
        print(f"  近零激活度(<=0.05) 共 {nz} 次")
        print(f"    其中 当前值在论域外   = {near_zero_out_of_range} "
              f"({near_zero_out_of_range / nz * 100:.1f}%)  ← 论域失真")
        print(f"    其中 当前值在论域内   = {near_zero_in_range} "
              f"({near_zero_in_range / nz * 100:.1f}%)  ← 正常（离桶中心远）")
    if all_detail_total:
        print(f"\n  全部前件求值 {all_detail_total} 次，"
              f"论域外 = {all_detail_out_of_range} "
              f"({all_detail_out_of_range / all_detail_total * 100:.1f}%)")
    print()
    print("  ⇒ 论域（『低/高』的基准）没定义，会让大量规则**直接失效**，")
    print("    而不只是『精度不够』。这比档位映射与聚合都更靠前。")

    hr("M5  只命中 1 条规则的场景占比（此时模糊推理完全无作用）")
    if total_scenes:
        print(f"  {single_hit_scenes} / {total_scenes} = "
              f"{single_hit_scenes / total_scenes * 100:.1f}%")

    hr("M6  建议值 vs 规则写的调整量（是不是就是个查表系统）")
    if cont_vals and rule_vals:
        cv = np.array(cont_vals)
        rv = np.array(rule_vals)
        print(f"  规则写的调整量：n={len(rv)}  均值={rv.mean():+.4f}  "
              f"标准差={rv.std():.4f}")
        print(f"  输出的建议值  ：n={len(cv)}  均值={cv.mean():+.4f}  "
              f"标准差={cv.std():.4f}")
        exact = np.isclose(cv[:, None], rv[None, :], atol=1e-6).any(axis=1).mean()
        print(f"  输出**恰好等于**某条规则写的调整量 = {exact * 100:.1f}%")

    print()
    print("=" * 78)
    print("度量结束")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
