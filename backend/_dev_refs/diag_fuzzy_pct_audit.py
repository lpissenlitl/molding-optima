"""百分比结论规则的形态统计（决定 A5/A5b bug 是否已在触发）

2026-10-22

背景：tsk_inference 第四层里 `cur_params[i] = x[rule_solution[i]]`，
      rule_solution[i] 是**该规则第一个结论参数**，
      而 `sol_matrix = solution_matrix.T * cur_params` 会把**整行所有结论**
      都乘上同一个当前值。
      => 一条规则里只要有 2 个百分比结论，第二个就会乘错对象。

统计项：
  B1  含 % 的规则数
  B2  按「结论个数 × 是否含 %」交叉分布
  B3  含 % 且结论个数 > 1 的规则（bug 触发条件）—— 逐条列出
  B4  纯绝对值多结论规则（对照组，应正确）
  B5  单结论规则占比

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_pct_audit.py
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
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule


def classify_solution(sol):
    action = sol.get("action")
    value = str(sol.get("value", ""))
    if action in ("add", "reduce"):
        if value.endswith("%"):
            return "pct"
        try:
            float(value)
            return "abs"
        except ValueError:
            return "other"
    if action in ("adjust", "popup"):
        return "check"
    return "other"


def main():
    rules = list(
        RuleMethod.objects.filter(is_deleted=False).values_list("id", "rule_description")
    )
    print(f"规则总数（未删除）: {len(rules)}")

    cross = Counter()
    pct_multi = []
    abs_multi = []
    single = 0

    for rid, desc in rules:
        if not desc:
            continue
        sols = parse_rule(desc)["solutions"]
        numeric = [s for s in sols if classify_solution(s) in ("pct", "abs")]
        if not numeric:
            continue
        kinds = Counter(classify_solution(s) for s in numeric)
        has_pct = kinds.get("pct", 0) > 0
        has_abs = kinds.get("abs", 0) > 0
        n = len(numeric)
        if n == 1:
            single += 1
        cross[(n, has_pct, has_abs)] += 1

        if has_pct and n > 1:
            pct_multi.append((rid, desc, numeric))
        elif has_abs and n > 1:
            abs_multi.append((rid, desc, numeric))

    print()
    print("=" * 78)
    print("[B1] 含 % 的规则数")
    print("=" * 78)
    n_pct = sum(v for (n, p, a), v in cross.items() if p)
    n_abs = sum(v for (n, p, a), v in cross.items() if a)
    print(f"  含百分比结论的规则: {n_pct} 条")
    print(f"  含绝对值结论的规则: {n_abs} 条")
    print(f"  只有 1 个数值结论的规则: {single} 条")

    print()
    print("=" * 78)
    print("[B2] 交叉分布（结论个数 x 含% x 含绝对值）")
    print("=" * 78)
    for (n, p, a), v in sorted(cross.items()):
        tag = []
        if p:
            tag.append("含%")
        if a:
            tag.append("含绝对值")
        print(f"  结论数={n}  [{','.join(tag) or '其他':12s}] -> {v} 条")

    print()
    print("=" * 78)
    print("[B3] 含 % 且结论个数 > 1 —— 第二个百分比结论会乘错对象")
    print("=" * 78)
    print(f"命中: {len(pct_multi)} 条")
    for rid, desc, numeric in pct_multi[:15]:
        detail = ", ".join(
            f"{s.get('name')}_{s.get('action')}_{s.get('value')}" for s in numeric
        )
        print(f"  #{rid}  {detail}")
        print(f"        {desc}")
    if len(pct_multi) > 15:
        print(f"  ... 另有 {len(pct_multi) - 15} 条")

    print()
    print("=" * 78)
    print("[B4] 纯绝对值多结论（对照组，行为正确）")
    print("=" * 78)
    print(f"命中: {len(abs_multi)} 条")
    for rid, desc, numeric in abs_multi[:6]:
        detail = ", ".join(
            f"{s.get('name')}_{s.get('action')}_{s.get('value')}" for s in numeric
        )
        print(f"  #{rid}  {detail}")
        print(f"        {desc}")
    if len(abs_multi) > 6:
        print(f"  ... 另有 {len(abs_multi) - 6} 条")


if __name__ == "__main__":
    main()
