"""Quantify the impact of the level->bucket mapping (P1) with real rules.

A) current mapping : low->0, medium->1, high->2   (what the code does today)
B) fixed mapping   : low->1, medium->2, high->3   (5-bucket semantics:
                     very_low, low, medium, high, very_high)

Both runs use the SAME rules and the SAME input values; only the bucket index
changes. Also measures the impact of dropping 'DL*' position preconditions.

ASCII-only output (Windows GBK console).
Run from backend: ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_bucket_impact.py
"""

import os
import sys
from collections import Counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

from process.models.rules import RuleMethod, RuleKeyword
from process.algorithms.fuzzy.fuzzy_core.models import nets
from process.algorithms.fuzzy.fuzzy_core.parsing import (
    parse_rule,
    is_position_name,
    collect_param_names,
    classify_name,
)


def build_keywords(include_defects=False, include_positions=False):
    kws = []
    for k in RuleKeyword.objects.all().filter(is_deleted=False):
        name = getattr(k, "keyword_name", None)
        if name is None:
            continue
        if not include_defects and classify_name(name) == "defect":
            continue
        if not include_positions and is_position_name(name):
            continue
        kws.append(
            {
                "keyword": name,
                "lvl": int(k.fuzzy_level or 3),
                "min_val": float(k.range_min or 0.0),
                "max_val": float(k.range_max or 1.0),
                "step": float(k.action_max_val or 1.0),
            }
        )
    return kws


def build_x(kws):
    """Give every non-defect, non-position param a value at 40% of its range
    (a 'slightly low' operating point, the most common rule-triggering case)."""
    x = {}
    for k in kws:
        lo, hi = k["min_val"], k["max_val"]
        x[k["keyword"]] = lo + (hi - lo) * 0.40
    return x


def run(rules, kws, x, top_k=10):
    net = nets.NumTskRuleNet(rules, kws, [1.0] * len(rules))
    res, _ = net.predict(x, top_k=top_k)
    return res


def show(title, res):
    print(f"\n-- {title} --")
    for i, (rule, act, concl) in enumerate(res[:10]):
        concl_txt = ", ".join(f"{k}={v}" for k, v in concl.items())
        print(f"  {i + 1:>2}. act={act:.6f}  {rule[:74]}")
        print(f"        -> {concl_txt}")


def main():
    rules = [
        {"rule_description": getattr(r, "rule_description", "") or ""}
        for r in RuleMethod.objects.all().filter(is_deleted=False)
    ]
    rules = [r for r in rules if r["rule_description"].strip()]
    print("rules:", len(rules))

    # ---- how many rules carry DL* / injectstage / HOLDEXIST preconditions ----
    pos_rules = 0
    missing_kw = Counter()
    kwnames = {k["keyword"] for k in build_keywords(include_defects=True, include_positions=True)}
    for r in rules:
        parsed = parse_rule(r["rule_description"])
        hit = False
        for pc in parsed["preconditions"]:
            nm = pc.get("name")
            if is_position_name(nm):
                hit = True
            if nm not in kwnames and classify_name(nm) != "defect":
                missing_kw[nm] += 1
        if hit:
            pos_rules += 1
    print("rules carrying a DL* position precondition:", pos_rules)
    print("precondition params missing from RuleKeyword:", dict(missing_kw))

    # ---- scenario setup: params only (no defect, no position) ----------------
    kws_params = build_keywords(include_defects=False, include_positions=False)
    x = build_x(kws_params)
    print("input params:", len(x))

    # ---- A: current mapping -------------------------------------------------
    saved = dict(nets.HS_MAPPING_DICT)
    nets.HS_MAPPING_DICT = {
        "low": 0, "mid": 1, "medium": 1, "high": 2,
        "add": 1, "reduce": -1, "adjust": -2,
    }
    res_a = run(rules, kws_params, x)
    show("A) CURRENT mapping  low->0 medium->1 high->2", res_a)

    # ---- B: fixed mapping (5-bucket semantics) ------------------------------
    nets.HS_MAPPING_DICT = {
        "low": 1, "mid": 2, "medium": 2, "high": 3,
        "add": 1, "reduce": -1, "adjust": -2,
    }
    res_b = run(rules, kws_params, x)
    show("B) FIXED mapping    low->1 medium->2 high->3", res_b)

    nets.HS_MAPPING_DICT = saved

    act_a = {r[0]: r[1] for r in res_a}
    act_b = {r[0]: r[1] for r in res_b}
    common = set(act_a) & set(act_b)
    print("\n-- activation comparison on common top rules --")
    for rule in sorted(common, key=lambda k: -act_a[k])[:10]:
        print(f"  A={act_a[rule]:.6f}  B={act_b[rule]:.6f}  ratio={act_b[rule] / act_a[rule] if act_a[rule] else float('nan'):.3f}  {rule[:60]}")

    # ---- C: does the defect dimension work if defect keywords are supplied? --
    kws_def = build_keywords(include_defects=True, include_positions=False)
    x_def = dict(x)
    x_def["SHORTSHOT"] = 0.0     # defect value injected like the legacy code
    res_c = run(rules, kws_def, x_def)
    show("C) CURRENT mapping + defect keywords present in pre_dict", res_c)

    # ---- D: with position keywords present ---------------------------------
    kws_pos = build_keywords(include_defects=True, include_positions=True)
    x_pos = dict(x_def)
    for k in kws_pos:
        if is_position_name(k["keyword"]):
            x_pos[k["keyword"]] = 0.99      # legacy injected position value
    res_d = run(rules, kws_pos, x_pos)
    show("D) CURRENT mapping + defect + DL* position keywords present (x=0.99)", res_d)

    # ---- E: the 20 rules that carry a DL* precondition ----------------------
    print("\n== E: rules whose DL* precondition is silently dropped today ==")
    dl_rules = []
    for r in rules:
        parsed = parse_rule(r["rule_description"])
        for pc in parsed["preconditions"]:
            if is_position_name(pc.get("name")):
                dl_rules.append(r["rule_description"])
                break
    print("  count:", len(dl_rules))
    for d in dl_rules:
        print("   ", d[:110])

    # activate them with and without the position dimension
    def act_of(res):
        return {r[0]: r[1] for r in res}

    a_d = act_of(res_c)     # defect present, DL* dropped
    a_e = act_of(res_d)     # defect present, DL* active
    print("\n  activation of those rules (C = dropped, D = active):")
    for d in dl_rules:
        print(f"    C={a_d.get(d, 0.0):.6f}   D={a_e.get(d, 0.0):.6f}   {d[:74]}")


if __name__ == "__main__":
    main()
