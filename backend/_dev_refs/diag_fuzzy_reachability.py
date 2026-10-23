"""档位可达性体检：在真实工艺数据下，各参数的哪些档位永远不会被命中

2026-10-22

前置发现（diag_fuzzy_domain.py）：
  - RuleKeyword.range 是**种子默认值**，不是标定过的工艺窗口
    BT/NT 论域 [0,50]，真实值 [230,250] / [123,255] → 整体在论域外
  - inj_spd_1 真实值 [30,38]，论域 [0,120] → 只占论域 25%~32%
  - 5 档分桶下 means = [0,30,60,90,120]，σ=15
    ⇒ inj_spd_1 的真实值全部落在 low 桶（mean=30）附近
    ⇒ `IV0_mid` / `IV0_high` / `IV0_very_high` 的隶属度恒接近 0

本脚本量化：**规则库里有多少条规则，其前件档位在真实数据下永远不可达。**

判据：
  桶 b 的有效区间 = 与相邻桶中心的中点之间
  真实值区间 [mn, mx] 与之有交集 → 该档位「可达」
  否则 → 「不可达」（该档位的规则在真实工况下永不生效）

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_reachability.py
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
from django.db.models import Avg, Max, Min

from process.models import ProcessParameter
from process.models.rules import RuleKeyword, RuleMethod
from process.algorithms.fuzzy.fuzzy_core.parsing import (
    classify_name,
    is_level_word,
    parse_rule,
)

ALGO_TO_BIZ = {
    "IV0": "inj_spd_1", "IV1": "inj_spd_2", "IV2": "inj_spd_3",
    "IP0": "hold_pres_1", "PP0": "hold_pres_2",
    "PV0": "hold_pres_3", "PV1": "hold_pres_4",
    "BT": "brl_temp_1", "NT": "noz_temp", "CT": "mold_temp",
    "MEL": "melt_temp", "MSR0": "mold_screw_sp",
    "MP0": "mold_press", "MBP0": "mold_back_press",
}

LEVEL_WORDS_BY_LVL = {
    3: ["low", "mid", "high"],
    5: ["very_low", "low", "mid", "high", "very_high"],
    7: ["extremely_low", "very_low", "low", "mid", "medium", "high",
        "very_high", "extremely_high"],
}


def hr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def bucket_bounds(lo, hi, lvl):
    """返回 [(中心, 下界, 上界)]，按档位顺序。"""
    means = np.r_[lo, np.quantile([lo, hi], np.arange(1, lvl - 1) / (lvl - 1)), hi]
    out = []
    for i, m in enumerate(means):
        lower = lo if i == 0 else (means[i - 1] + m) / 2
        upper = hi if i == len(means) - 1 else (m + means[i + 1]) / 2
        out.append((float(m), float(lower), float(upper)))
    return out


def main():
    qs = ProcessParameter.objects.all()
    total = qs.count()
    kw_all = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}

    # ---------------------------------------------------------- 统计
    hr("1. 各参数：真实值区间 vs 5 档可达性")
    print(f"  {'参数':<8}{'业务字段':<16}{'论域':>14}{'真实[min,max]':>20}"
          f"{'可达档位':>26}{'不可达':>8}")
    print("  " + "-" * 96)

    reachable = {}     # (param, level_word) → bool
    param_report = {}
    for algo, biz in sorted(ALGO_TO_BIZ.items()):
        kw = kw_all.get(algo)
        if kw is None:
            continue
        try:
            agg = qs.aggregate(mn=Min(biz), mx=Max(biz), av=Avg(biz))
        except Exception:
            continue
        if agg["mn"] is None:
            continue
        lo, hi = float(kw.range_min), float(kw.range_max)
        lvl = int(kw.fuzzy_level or 3)
        if hi <= lo:
            continue
        mn, mx = float(agg["mn"]), float(agg["mx"])
        words = LEVEL_WORDS_BY_LVL.get(lvl) or LEVEL_WORDS_BY_LVL[3]
        bounds = bucket_bounds(lo, hi, lvl)

        ok_list, bad_list = [], []
        for i, w in enumerate(words):
            _c, bl, bu = bounds[i]
            hit = not (mx < bl or mn > bu)     # 区间有交集 → 可达
            reachable[(algo, w)] = hit
            (ok_list if hit else bad_list).append(w)
        param_report[algo] = (biz, lo, hi, mn, mx, lvl, words, ok_list, bad_list)

        rng = f"[{lo:g},{hi:g}]"
        real = f"[{mn:g},{mx:g}]"
        ok_s = ",".join(ok_list) or "—"
        print(f"  {algo:<8}{biz:<16}{rng:>14}{real:>20}{ok_s:>26}"
              f"{len(bad_list):>8}")

    # ---------------------------------------------------------- 规则扫描
    hr("2. 规则前件的档位可达性（真实数据下）")
    rules = list(RuleMethod.objects.filter(is_active=True).all())

    level_reach = Counter()        # (level_word) → 不可达次数
    pair_stat = Counter()          # (param, level) → (可达次数, 不可达次数)
    dead_rules = []                # 至少有一个前件不可达的规则
    dead_by_cause = Counter()

    for rm in rules:
        desc = rm.rule_description or ""
        parsed = parse_rule(desc)
        pres = parsed.get("preconditions", []) or []
        rule_dead = False
        for pre in pres:
            name = str(pre.get("name") or "")
            lv = str(pre.get("level") or "").lower()
            if classify_name(name) == "defect":
                continue
            if not is_level_word(lv):
                continue
            key = (name, lv)
            if key not in reachable:
                continue
            hit = reachable[key]
            pair_stat[(name, lv, "total")] += 1
            if not hit:
                pair_stat[(name, lv)] += 1
                rule_dead = True
                level_reach[lv] += 1
                dead_by_cause[name] += 1
        if rule_dead:
            dead_rules.append((rm, desc))

    print(f"  参与统计的规则 = {len(rules)} 条")
    print(f"  **至少有一个前件档位在真实数据下不可达** = {len(dead_rules)} 条 "
          f"({len(dead_rules) / max(len(rules), 1) * 100:.1f}%)")
    print()
    print("  不可达前件按档位词分布：")
    for w, n in level_reach.most_common():
        print(f"    {w:<16} {n:>6} 次")
    print()
    print("  不可达前件按参数分布（top 12）：")
    for p, n in dead_by_cause.most_common(12):
        print(f"    {p:<14} {n:>6} 次")

    # ---------------------------------------------------------- 组合表
    hr("3. 参数 × 档位 的可达性明细（只看规则里用到的组合）")
    used_pairs = sorted({(k[0], k[1]) for k in pair_stat if len(k) == 3})
    print(f"  {'参数':<8}{'档位词':<12}{'不可达/总次数':>16}{'占比':>10}"
          f"{'判定':>12}")
    print("  " + "-" * 60)
    for name, w in used_pairs:
        bad = pair_stat.get((name, w), 0)
        tot = pair_stat.get((name, w, "total"), 0)
        if not tot:
            continue
        pct = bad / tot * 100
        verdict = "!! 不可达" if bad == tot else ("部分" if bad else "OK")
        print(f"  {name:<8}{w:<12}{f'{bad}/{tot}':>16}{pct:>9.0f}%{verdict:>12}")

    # ---------------------------------------------------------- 结论
    hr("4. 结论")
    only_low = [p for p, v in param_report.items()
                if v[7] and set(v[7]) <= {"low", "mid"}
                and "high" not in v[7]]
    print(f"  真实数据下只能落在 low/mid 档（永远到不了 high）的参数 = {len(only_low)}")
    for p in only_low[:10]:
        biz, lo, hi, mn, mx, lvl, words, ok, bad = param_report[p]
        print(f"    {p:<8}({biz:<14}) 真实[{mn:g},{mx:g}]  论域[{lo:g},{hi:g}]"
              f"  可达={','.join(ok)}  不可达={','.join(bad)}")
    print()
    print("  ⇒ 若结论成立，则：")
    print("     1) 5 档划分对当前工艺窗口**过于细分**，大部分档位永远用不上；")
    print("     2) 规则库里写 `X_high` / `X_very_high` 的规则在真实工况下")
    print("        **永远不会生效**（不是『精度不够』，是根本触发不了）；")
    print("     3) 这与「论域用种子默认值」是**同一个病根**：")
    print("        论域没标定 → 真实值只占论域一角 → 档位全部挤在一端。")
    print("     ⇒ 也就是说：档位映射错位（E2）是表层，")
    print("        **论域未标定（E5）才是让整套档位体系失效的根因**。")

    print()
    print("=" * 78)
    print("可达性体检结束")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
