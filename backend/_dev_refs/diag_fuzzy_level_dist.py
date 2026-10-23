"""档位（fuzzy_level）分布诊断 —— 量化「多档语义词表」这个抽象层有没有用武之地。

回答四个问题：
1. RuleKeyword 表里 fuzzy_level 的分布
2. 规则里真实出现的字段 → 它们的 fuzzy_level 分布
3. 5/7/9 档字段在规则里到底被引用了多少次（关键）
4. 规则串里真实出现的档位词有哪些（`very_*` / `levelN` 到底有没有人用）

只读脚本，不改任何数据。
"""
import collections
import os
import re
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from django.db.models import Count  # noqa: E402

from process.models import RuleKeyword, RuleMethod  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import collect_param_names  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.macros import ALL_LEVEL_WORDS  # noqa: E402


def main():
    print("=" * 74)
    print("1. RuleKeyword 表 fuzzy_level 分布")
    print("=" * 74)
    for row in (RuleKeyword.objects.values("fuzzy_level")
                .annotate(n=Count("id")).order_by("fuzzy_level")):
        print(f"  fuzzy_level={row['fuzzy_level']}: {row['n']} 条")

    rules = list(RuleMethod.objects.filter(is_active=True, is_deleted=False)
                 .values_list("rule_description", flat=True))
    print(f"\n活跃规则数: {len(rules)}")

    fields = collect_param_names(rules)
    kw_lvl = dict(RuleKeyword.objects.values_list("keyword_name", "fuzzy_level"))

    print("=" * 74)
    print("2. 规则里前件字段的 fuzzy_level 分布")
    print("=" * 74)
    dist = collections.Counter()
    missing = []
    for f in fields:
        lvl = kw_lvl.get(f)
        if lvl is None:
            missing.append(f)
        else:
            dist[lvl] += 1
    for lvl, n in sorted(dist.items()):
        print(f"  lvl={lvl}: {n} 个字段")
    print(f"  RuleKeyword 里查不到: {sorted(missing)}")

    high = sorted(f for f in fields if (kw_lvl.get(f) or 3) > 3)
    print(f"\n  >> 5/7/9 档字段共 {len(high)} 个: {high}")

    print("=" *74)
    print("3. 高档位字段的规则引用次数")
    print("=" * 74)
    for f in high:
        cnt = sum(1 for r in rules if f in r)
        print(f"  {f} (lvl={kw_lvl.get(f)}): 出现在 {cnt} 条规则里")

    print("=" * 74)
    print("4. 规则串里真实出现的档位词")
    print("=" * 74)
    words = collections.Counter()
    for r in rules:
        for w in r.replace("IF", " ").replace("AND", " ").replace("THEN", " ").split():
            m = re.match(r"^[A-Za-z0-9]+_(level\d+|[a-z_]+)$", w)
            if m and m.group(1) in ALL_LEVEL_WORDS:
                words[m.group(1)] += 1
    for w, n in words.most_common():
        print(f"  {w:<18} {n:>5} 次")

    semantic = [w for w in words if not w.startswith("level")]
    numbered = [w for w in words if w.startswith("level")]
    print(f"\n  语义词 {len(semantic)} 种: {sorted(semantic)}")
    print(f"  编号词 {len(numbered)} 种: {sorted(numbered)}")
    print(f"  >> very_*/extremely_*/ultra_* 使用次数: "
          f"{sum(n for w, n in words.items() if w.startswith(('very_', 'extremely_', 'ultra_', 'slightly_')))}")


if __name__ == "__main__":
    main()
