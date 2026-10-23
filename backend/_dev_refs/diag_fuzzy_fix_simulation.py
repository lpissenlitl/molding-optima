"""对照实验：模糊推理「现状」vs「修正后」的输出量级对比

2026-10-22

目的：把设计修正的**方向**用真实数据验证出来，而不是停留在"感觉不对"。

对比 4 组：
  S0  现状（生产代码原样跑）
  S1  只修档位映射（level → 桶 按参数自己的 fuzzy_level 动态定位）
  S2  只修聚合（跨参数全局归一化 → 按参数分组归一化 + priority 加权平均）
  S3  两个都修（+ 缺陷前件不再静默丢弃）

参考实现写在脚本内（不污染生产代码），逐组与现状对比每个参数的输出量级。

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_fix_simulation.py
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
from process.algorithms.fuzzy.fuzzy_core.macros import HS_MAPPING_DICT
from process.algorithms.fuzzy.fuzzy_core.parsing import (
    classify_name,
    is_level_word,
    parse_rule,
)
from process.algorithms.fuzzy.services.rule_query_service import (
    RuleQueryContext,
    RuleQueryService,
)


def hr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# 档位词表：按参数自己的 fuzzy_level 定位桶
LEVEL_WORDS_BY_LVL = {
    3: ["low", "mid", "high"],
    5: ["very_low", "low", "mid", "high", "very_high"],
    7: ["extremely_low", "very_low", "low", "mid", "medium", "high", "very_high"],
}


def level_to_bucket(level_word, f_level):
    """档位词 → 桶索引（按参数自己的档位数定位）。"""
    words = LEVEL_WORDS_BY_LVL.get(f_level) or LEVEL_WORDS_BY_LVL[3]
    w = str(level_word or "").lower()
    if w == "medium":
        w = "mid"
    if w in words:
        return words.index(w)
    # 退化：词不在该档位表里 → 落到最接近的语义档
    order = ["very_low", "low", "mid", "high", "very_high"]
    if w in order and "mid" in words:
        return order.index(w) if order.index(w) < len(words) else len(words) - 1
    return None


def build_feature(kw):
    """按 RuleKeyword 的 fuzzy_level 建高斯隶属度参数。"""
    lo, hi = float(kw.range_min), float(kw.range_max)
    lvl = int(kw.fuzzy_level or 3)
    if hi <= lo:
        hi = lo + 1.0
    sigma = (hi - lo) / (2 * (lvl - 1))
    means = np.r_[lo, np.quantile([lo, hi], np.arange(1, lvl - 1) / (lvl - 1)), hi]
    return [float(m) for m in means], float(sigma)


def reference_infer(rules, keywords, x, use_fixed_level=True, use_group_norm=True,
                     keep_defect_pre=True):
    """参考实现：档位动态定位 + 按参数分组归一化 + 缺陷前件不当门控。

    返回 {param: delta}
    """
    feats = {}
    for name, kw in keywords.items():
        if name in x:
            feats[name] = build_feature(kw)

    # 逐规则算激活度
    per_param = defaultdict(list)
    for rm, desc in rules:
        parsed = parse_rule(desc)
        acts = []
        for pre in parsed.get("preconditions", []) or []:
            name = str(pre.get("name") or "")
            lv = str(pre.get("level") or "").lower()
            is_defect = classify_name(name) == "defect"
            if is_defect:
                # 缺陷档位由路由层精确保证 → 视为完全匹配
                if keep_defect_pre:
                    acts.append(1.0)
                continue
            if not is_level_word(lv):
                continue
            if name not in feats:
                continue
            kw = keywords[name]
            if use_fixed_level:
                bucket = HS_MAPPING_DICT.get(lv)
            else:
                bucket = level_to_bucket(lv, int(kw.fuzzy_level or 3))
            if bucket is None or bucket >= len(feats[name][0]):
                continue
            means, sigma = feats[name]
            mu = float(gauss_mf(x[name], means[bucket], sigma))
            acts.append(mu)

        if not acts:
            continue
        activation = float(min(acts))          # 弱连接

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
            per_param[name].append((delta, activation, float(rm.priority or 1.0)))

    out = {}
    for name, items in per_param.items():
        if use_group_norm:
            # 按参数分组：组内 priority×激活度 加权平均（权重和为 1）
            ws = [act * pri for _, act, pri in items]
            s = sum(ws)
            if s <= 0:
                continue
            out[name] = sum(d * w for (d, _, _), w in zip(items, ws)) / s
        else:
            # 现状语义：跨参数全局归一化 + 直接累加
            tot = sum(act for _, act, _ in items) or 1e-7
            out[name] = sum(d * act / tot * pri for d, act, pri in items)
    return out


def run_now(rules, keywords, x):
    """现状：直接调生产代码 NumTskRuleNet。"""
    from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet
    from process.algorithms.fuzzy.adapters import RuleKeywordAdapter

    kw_dicts = []
    for name, kw in keywords.items():
        if name in x:
            kw_dicts.append(RuleKeywordAdapter.to_fuzzy_dict(kw))
    rule_array = [{"rule_description": d} for _, d in rules]
    prio = [float(r.priority or 1.0) for r, _ in rules]
    net = NumTskRuleNet(rule_array, kw_dicts, prio)
    results, _ = net.predict(x, top_k=len(rules))
    out = defaultdict(float)
    for rule_str, activation, adjustments in results:
        for p, v in adjustments.items():
            out[p] += float(v) * float(activation)
    return dict(out)


def expected_delta(rules):
    """规则里写的调整量（工艺知识本身），按参数聚合。"""
    agg = defaultdict(list)
    for rm, desc in rules:
        parsed = parse_rule(desc)
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
            d = value if action == "add" else -value
            agg[name].append(d)
    return {k: (min(v), max(v), len(v)) for k, v in agg.items()}


def main():
    # -------------------------------------------------- 取真实规则
    hr("0. 取真实规则（defect=ABERRATION, level=low，全库）")
    ctx = RuleQueryContext(
        defect_name="ABERRATION",
        defect_level="low",
        defect_position=None,
        polymer_abbreviation=None,
        product_category=None,
        rule_library_code=None,
    )
    resolved = RuleQueryService.get_rules(ctx)
    print(f"命中规则 {len(resolved)} 条")
    if not resolved:
        print("!! 没有命中规则")
        return 1

    # 跨库去重（现状不做去重，先量化其影响）
    dedup = {}
    for r in resolved:
        dedup.setdefault(r.rule_str, r)
    print(f"去重后唯一规则串 {len(dedup)} 条（重复 {len(resolved) - len(dedup)} 条）")

    rules = [(r.method, r.rule_str) for r in resolved]
    rules_dedup = [(r.method, r.rule_str) for r in dedup.values()]

    # -------------------------------------------------- 取真实参数
    hr("1. 取真实工艺参数")
    from process.models import ProcessParameter
    from process.services.parameter_optimize import (
        _normalize_field_name_by_spec,
        _to_full_dict,
    )
    from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine

    real = ProcessParameter.objects.exclude(inj_spd_1=None).first()
    if real is None:
        print("!! 没有可用 parameter")
        return 1
    business = {k: v for k, v in _to_full_dict(real).items()
                if isinstance(v, (int, float))}
    # 翻译成算法命名（与生产链路的 _normalize_field_name_by_spec 完全一致）
    algo = _normalize_field_name_by_spec(
        business,
        FuzzyEngine.FIELD_NAME_ALIAS,
        FuzzyEngine.FIELD_INDEX_OFFSET,
        FuzzyEngine.FAMILY_FIELD_ALIAS,
    )
    print(f"process_parameter: 业务字段 {len(business)} 个 → 算法命名 {len(algo)} 个")
    print(f"  样例: {dict(list(algo.items())[:8])}")

    # -------------------------------------------------- 取 keyword
    kw_all = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}
    used = set()
    for _, desc in rules:
        for pre in parse_rule(desc).get("preconditions", []) or []:
            used.add(str(pre.get("name") or ""))
        for sol in parse_rule(desc).get("solutions", []) or []:
            used.add(str(sol.get("name") or ""))
    keywords = {n: kw_all[n] for n in used if n in kw_all and n in algo}
    print(f"涉及 keyword {len(used)} 个，其中在算法参数里能取到值的 {len(keywords)} 个")

    # -------------------------------------------------- 对照实验
    hr("2. 对照实验：现状 vs 修正后")

    s0 = run_now(rules, keywords, algo)
    s1 = reference_infer(rules, keywords, algo,
                          use_fixed_level=False, use_group_norm=False,
                          keep_defect_pre=False)
    s2 = reference_infer(rules, keywords, algo,
                          use_fixed_level=True, use_group_norm=True,
                          keep_defect_pre=False)
    s3 = reference_infer(rules_dedup, keywords, algo,
                          use_fixed_level=False, use_group_norm=True,
                          keep_defect_pre=True)

    exp = expected_delta(rules_dedup)

    rows = []
    for p in sorted(set(list(s0.keys()) + list(s3.keys()))):
        lo, hi, n = exp.get(p, (None, None, 0))
        rows.append((
            p,
            n,
            f"{lo:+.2f}~{hi:+.2f}" if lo is not None else "-",
            s0.get(p),
            s2.get(p),
            s3.get(p),
        ))

    print(f"{'参数':<8}{'规则数':>6}{'规则写的调整量':>16}"
          f"{'S0 现状':>12}{'S2 只修聚合':>12}{'S3 全修':>12}")
    print("-" * 78)
    for p, n, e, a, b, c in rows:
        fa = f"{a:+.4f}" if a is not None else "-"
        fb = f"{b:+.4f}" if b is not None else "-"
        fc = f"{c:+.4f}" if c is not None else "-"
        print(f"{p:<8}{n:>6}{e:>16}{fa:>12}{fb:>12}{fc:>12}")
    print("-" * 78)
    print("  S0 = 现状（生产代码）")
    print("  S2 = 只修聚合（按参数分组归一化），档位映射仍是旧的")
    print("  S3 = 修档位映射 + 修聚合 + 跨库去重 + 缺陷前件不当门控")

    # -------------------------------------------------- 量级对比
    hr("3. 量级对比：产出 / 规则写的调整量")
    print(f"{'参数':<8}{'规则写的':>10}{'S0 现状':>12}{'S0 倍数':>10}"
          f"{'S3 修正':>12}{'S3 倍数':>10}")
    print("-" * 78)
    for p, n, e, a, b, c in rows:
        lo, hi, n2 = exp.get(p, (None, None, 0))
        if lo is None or hi is None:
            continue
        target = (lo + hi) / 2
        if abs(target) < 1e-9:
            continue
        ra = abs(a / target) if (a is not None and target) else None
        rc = abs(c / target) if (c is not None and target) else None
        print(f"{p:<8}{target:>+10.2f}"
              f"{(f'{a:+.4f}' if a is not None else '-'):>12}"
              f"{(f'{ra:.3f}' if ra else '-'):>10}"
              f"{(f'{c:+.4f}' if c is not None else '-'):>12}"
              f"{(f'{rc:.3f}' if rc else '-'):>10}")
    print()
    print("  倍数 = |产出 / 规则写的调整量|。1.0 表示量级正确。")
    print("  （只列『规则写了单一调整量』的参数；同参反向的会互相抵消，不列入）")

    # -------------------------------------------------- 论域体检
    hr("5. 论域体检：RuleKeyword 的 range 与真实值对不对得上")
    print("  RuleKeyword.range_min/max 的模型注释自己写着：")
    print("    『取值范围是通用默认值/模拟推荐值，非设备物理极限』")
    print("    『实际推理时：设备真实范围 > RuleKeyword 默认值』")
    print("  但引擎一直直接用它当论域。\n")
    print(f"{'参数':<8}{'fuzzy_lvl':>10}{'range_min':>11}{'range_max':>11}"
          f"{'真实值':>10}{'相对位置':>10}{'判定':>14}")
    print("-" * 78)
    out_of_range = 0
    for p in sorted(keywords):
        kw = keywords[p]
        lo, hi = float(kw.range_min), float(kw.range_max)
        v = float(algo.get(p, 0) or 0)
        if hi > lo:
            pos = (v - lo) / (hi - lo)
            pos_s = f"{pos * 100:.0f}%"
        else:
            pos_s = "-"
        if v < lo or v > hi:
            verdict = "!! 论域外"
            out_of_range += 1
        elif hi > lo and (v - lo) / (hi - lo) > 0.9:
            verdict = "!! 贴上界"
            out_of_range += 1
        else:
            verdict = ""
        print(f"{p:<8}{int(kw.fuzzy_level or 3):>10}{lo:>11.1f}{hi:>11.1f}"
              f"{v:>10.1f}{pos_s:>10}{verdict:>14}")
    print("-" * 78)
    print(f"  论域失真（值在论域外 / 贴上界）的参数 = {out_of_range} / {len(keywords)}")

    # -------------------------------------------------- 失活规则统计
    hr("4. 失活规则里有多少是『数值结论』（真正该给建议却给不出）")
    dead_numeric = 0
    dead_advisory = 0
    for r in resolved:
        parsed = parse_rule(r.rule_str)
        pres = parsed.get("preconditions", []) or []
        sols = parsed.get("solutions", []) or []
        gates = 0
        for pre in pres:
            name = str(pre.get("name") or "")
            lv = str(pre.get("level") or "").lower()
            if classify_name(name) == "defect":
                continue
            if not is_level_word(lv) or name not in keywords:
                continue
            gates += 1
        if gates:
            continue
        numeric = any(s.get("action") in ("add", "reduce") for s in sols)
        if numeric:
            dead_numeric += 1
        else:
            dead_advisory += 1
    print(f"  零门控规则 = {dead_numeric + dead_advisory} 条")
    print(f"    其中结论是数值（真失活，该给建议给不出）= {dead_numeric} 条")
    print(f"    其中结论是提示文本（走 check 分支，仍能出文本建议）= {dead_advisory} 条")

    print()
    print("=" * 78)
    print("对照实验结束")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
