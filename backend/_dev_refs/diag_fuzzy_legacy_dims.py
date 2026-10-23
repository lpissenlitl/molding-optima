"""Verify whether legacy dimensions (DL position / stage modes) still appear
in the current rule library. ASCII-only output (Windows GBK console).

Run from backend: ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_legacy_dims.py
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

from process.models.rules import RuleMethod

LEGACY_TOKENS = [
    "DL",
    "injectstage",
    "holdingstage",
    "meteringstage",
    "DMAM",
    "MEL",
    "VPTL",
]


def main():
    rules = list(RuleMethod.objects.all().filter(is_deleted=False))
    print("total rules (is_deleted=False):", len(rules))

    enabled = [r for r in rules if getattr(r, "is_active", True)]
    print("active rules:", len(enabled))

    print("\n-- defect_code / defect_label fields --")
    dc = Counter()
    dl = Counter()
    for r in rules:
        dc[str(getattr(r, "defect_code", None))] += 1
        dl[str(getattr(r, "defect_label", None))] += 1
    print("  defect_code:")
    for k, v in dc.most_common(30):
        print(f"    {k:<24} {v}")
    print("  defect_label:")
    for k, v in dl.most_common(30):
        print(f"    {k:<24} {v}")

    descriptions = [getattr(r, "rule_description", "") or "" for r in rules]

    print("\n-- legacy token occurrences in rule_description --")
    for token in LEGACY_TOKENS:
        hits = [d for d in descriptions if token in d]
        print(f"{token:<16} rules_containing={len(hits)}")
        for h in hits[:3]:
            print("    ", h[:110])

    print("\n-- defect-style precondition tokens (all caps words) --")
    from process.algorithms.fuzzy.fuzzy_core.macros import DEFECT_CONST

    defect_hits = Counter()
    for d in descriptions:
        for w in d.split():
            token = w.split("_")[0]
            if token in DEFECT_CONST:
                defect_hits[token] += 1
    for k, v in defect_hits.most_common():
        print(f"  {k:<16} {v}")

    print("\n-- distinct level words used in preconditions --")
    levels = Counter()
    for d in descriptions:
        head = d.upper()
        if " THEN " in head:
            head = head.split(" THEN ")[0]
        for w in head.split():
            if "_" in w:
                levels[w.rsplit("_", 1)[-1]] += 1
    for k, v in levels.most_common():
        print(f"  {k:<16} {v}")

    print("\n-- conclusion tokens --")
    concl = Counter()
    for d in descriptions:
        if " THEN " in d.upper():
            tail = d.upper().split(" THEN ")[1]
            for w in tail.split():
                concl[w.rsplit("_", 1)[-1]] += 1
    for k, v in concl.most_common(30):
        print(f"  {k:<16} {v}")


if __name__ == "__main__":
    main()
