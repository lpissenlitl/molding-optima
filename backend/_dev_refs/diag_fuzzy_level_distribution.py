"""统计 RuleKeyword.fuzzy_level 的实际分布（确认哪些档数真的有字段在用）。"""

import os
import sys
from collections import Counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

from process.models.rules import RuleKeyword  # noqa: E402


def main():
    qs = RuleKeyword.objects.filter(is_deleted=False)
    c = Counter(qs.values_list("fuzzy_level", flat=True))
    print("RuleKeyword.fuzzy_level 分布（is_deleted=False）:")
    for lvl in sorted(c):
        print(f"  {lvl} 档: {c[lvl]} 个字段")
    print(f"  合计: {sum(c.values())} 个")
    for lvl in (3, 5, 7, 9):
        if not c.get(lvl):
            print(f"  [!] {lvl} 档当前无任何字段在用")
    # 看 3 档的是谁
    for lvl in sorted(c):
        names = list(
            qs.filter(fuzzy_level=lvl).values_list("keyword_name", flat=True)[:12]
        )
        print(f"  {lvl} 档样例: {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
