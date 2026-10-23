"""Verify the decisive facts for P1/P6 and for the legacy 'worse' handling.

Q1: RuleKeyword.fuzzy_level distribution (decides whether P1 fires at all)
Q2: which parameter names appear in rule preconditions, and their fuzzy_level
Q3: 'worse' precondition rules: count + conclusion kind (numeric vs adjust)
Q4: are defect names present in RuleKeyword (can they become pre_dict entries?)
Q5: are legacy stage/position params present in RuleKeyword?

ASCII-only output (Windows GBK console).
Run from backend: ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_fuzzy_level.py
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

from process.models.rules import RuleMethod

from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule
from process.algorithms.fuzzy.fuzzy_core.macros import DEFECT_CONST


def main():
    rules = [r for r in RuleMethod.objects.all().filter(is_deleted=False)]
    descriptions = [getattr(r, "rule_description", "") or "" for r in rules]

    # ---- locate RuleKeyword model ----
    from process.models.rules import RuleKeyword

    kws = list(RuleKeyword.objects.all().filter(is_deleted=False))
    print("RuleKeyword rows:", len(kws))
    lvl_by_name = {}
    for k in kws:
        nm = getattr(k, "keyword_name", None) or getattr(k, "name", None)
        lvl_by_name[nm] = (
            getattr(k, "fuzzy_level", None),
            getattr(k, "range_min", None),
            getattr(k, "range_max", None),
        )

    # ---- Q1: fuzzy_level distribution ----
    print("\n== Q1: fuzzy_level distribution over RuleKeyword ==")
    lv = Counter(v[0] for v in lvl_by_name.values())
    for k, v in lv.most_common():
        print(f"  fuzzy_level={k!s:<6} count={v}")
    print("  names by fuzzy_level:")
    by_lvl = defaultdict(list)
    for nm, v in lvl_by_name.items():
        by_lvl[v[0]].append(nm)
    for k in sorted(by_lvl, key=lambda x: (x is None, x)):
        names = sorted(by_lvl[k])
        print(f"    lvl={k!s:<4} ({len(names)}): {names}")

    # ---- Q2: params used in rule preconditions ----
    pre_names = Counter()
    sol_names = Counter()
    level_words = Counter()
    worse_rules = []
    for d in descriptions:
        try:
            parsed = parse_rule(d)
        except Exception as exc:
            print("  parse fail:", repr(d)[:80], exc)
            continue
        for name, val in zip(
            [v.get("name") for v in (parsed.get("preconditions") or [])],
            (parsed.get("preconditions") or []),
        ):
            pre_names[name] += 1
            level_words[str(val.get("level", "")).lower()] += 1
            if str(val.get("level", "")).lower() == "worse":
                worse_rules.append((d, parsed))
        for val in parsed.get("solutions") or []:
            sol_names[val.get("name")] += 1

    print("\n== Q2: precondition names -> fuzzy_level ==")
    for nm, c in pre_names.most_common():
        if nm in DEFECT_CONST:
            print(f"  {nm:<14} used={c:<5} [DEFECT] in RuleKeyword={nm in lvl_by_name}")
            continue
        info = lvl_by_name.get(nm)
        print(f"  {nm:<14} used={c:<5} fuzzy_level={info[0] if info else 'MISSING'!s}")

    print("\n== level words in preconditions ==")
    for k, v in level_words.most_common():
        print(f"  {k:<14} {v}")

    # ---- Q3: worse rules ----
    print("\n== Q3: rules with a 'worse' precondition ==")
    print("  count:", len(worse_rules))
    kinds = Counter()
    samples = []
    for d, parsed in worse_rules:
        sols = parsed.get("solutions") or []
        is_adjust = any(
            str(v.get("level", "")).strip().startswith("\u8bf7\u68c0\u67e5")
            or "adjust" in str(v.get("level", ""))
            for v in sols
        )
        kinds["adjust_or_text" if is_adjust else "numeric"] += 1
        if len(samples) < 6:
            samples.append(d)
    for k, v in kinds.items():
        print(f"  {k:<18} {v}")
    for s in samples:
        print("    sample:", s[:110])

    # ---- Q4/Q5 ----
    print("\n== Q4: defect names in RuleKeyword ==")
    present = [n for n in DEFECT_CONST if n in lvl_by_name]
    print("  count:", len(present))
    print("  ", sorted(present))

    print("\n== Q5: legacy dimension params in RuleKeyword ==")
    for probe in ["DL", "IPOS", "MEL", "VPTL", "injectstage1", "holdingstage1", "DMAM0"]:
        print(f"  {probe:<16} in RuleKeyword = {probe in lvl_by_name}")

    print("\n== solution params -> fuzzy_level ==")
    for nm, c in sol_names.most_common():
        info = lvl_by_name.get(nm)
        print(f"  {nm:<14} used={c:<5} fuzzy_level={info[0] if info else 'MISSING'!s}")


if __name__ == "__main__":
    main()
