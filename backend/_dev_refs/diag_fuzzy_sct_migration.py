"""查旧版 levelN 结论规则（SCT*_add_levelN）在当前规则库里的去向。

背景：旧版 fuzzykit 的 Rule.dat 里有 24 条形如
    IF WELDLINE_low AND DLWELDLINE7_high THEN SCT1_add_level1
的规则，用 `levelN` 表达“把 SCT1 调到第 N 档”。
当前规则库实测 levelN 命中 0 次 —— 这批规则要么没迁过来，
要么被改写成了语义词。本脚本查清是哪一种。

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_sct_migration.py
"""

import os
import sys
from collections import Counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.models.rules import RuleKeyword, RuleMethod  # noqa: E402


def main():
    print("=" * 72)
    print("旧版 levelN 结论规则的迁移去向")
    print("=" * 72)

    qs = RuleMethod.objects.filter(is_deleted=False)
    all_rules = list(qs.values_list("rule_description", flat=True))
    print(f"\n当前有效规则总数: {len(all_rules)}")

    # 1) SCT 开头（可能是参数名）
    sct = [r for r in all_rules if "SCT" in str(r).upper()]
    print(f"含 'SCT' 的规则: {len(sct)} 条")
    for r in sct[:8]:
        print(f"    {r}")

    # 2) 旧版那批规则的精确形态
    old_patterns = ["add_level", "reduce_level", "level1", "level5", "level9"]
    for pat in old_patterns:
        hit = [r for r in all_rules if pat in str(r)]
        print(f"  含 '{pat}': {len(hit)} 条")

    # 3) 结论里出现 add/reduce 的规则（看结论词形态）
    concl_words = Counter()
    for r in all_rules:
        text = str(r)
        if " THEN " not in text:
            continue
        then = text.split(" THEN ")[-1]
        for token in then.replace(",", " ").split():
            if "_" not in token:
                continue
            parts = token.split("_")
            if len(parts) >= 2:
                concl_words[parts[-1]] += 1
    print("\n结论侧最后一个 token 的分布（前 20）:")
    for word, cnt in concl_words.most_common(20):
        print(f"    {word:<20} {cnt}")

    # 4) RuleKeyword 里有没有 SCT 字段
    kw_names = list(
        RuleKeyword.objects.filter(is_deleted=False).values_list("keyword_name", flat=True)
    )
    sct_kw = [k for k in kw_names if "SCT" in str(k).upper()]
    print(f"\nRuleKeyword 中含 'SCT' 的字段: {len(sct_kw)} 个 -> {sct_kw[:10]}")
    print(f"RuleKeyword 总数: {len(kw_names)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
