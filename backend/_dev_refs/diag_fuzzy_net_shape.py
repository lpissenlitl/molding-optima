"""统计 NumTskRuleNet 两个矩阵的真实规模与结构。

回答「nets.py 在构建什么」：
  - connected_matrix 的形状（规则数 x 前件桶列数）
  - solution_matrix 的形状（规则数 x 结论参数列数）
  - 前件字段清单、每个字段占几列
  - 矩阵稀疏度（这决定了「矩阵运算」到底是不是在干实事）

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_net_shape.py
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
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRule  # noqa: E402


def main():
    print("=" * 72)
    print("NumTskRuleNet 矩阵规模实测")
    print("=" * 72)

    rules = list(
        RuleMethod.objects.filter(is_deleted=False).values_list("rule_description", flat=True)
    )
    kw_rows = list(
        RuleKeyword.objects.filter(is_deleted=False).values(
            "keyword_name", "fuzzy_level", "range_min", "range_max"
        )
    )
    kw = {r["keyword_name"]: r for r in kw_rows}

    print(f"\n规则库: {len(rules)} 条")
    print(f"RuleKeyword: {len(kw)} 个字段")

    # 按生产侧同样的规则筛选逻辑统计
    pre_fields = Counter()
    sol_fields = Counter()
    kept = 0
    for desc in rules:
        num_rule = NumTskRule(desc)
        if num_rule.r_extra:
            continue
        if any(sol.get("action") == -2 for sol in num_rule.r_solutions.values()):
            continue
        kept += 1
        pre_fields.update(num_rule.r_preconditions.keys())
        sol_fields.update(num_rule.r_solutions.keys())

    print(f"进入数值推理层的规则: {kept} 条")
    print(f"前件字段数: {len(pre_fields)}   结论参数数: {len(sol_fields)}")

    # 列宽 = sum(lvl of pre fields that have RuleKeyword metadata)
    cols = 0
    no_meta = []
    lvl_hist = Counter()
    for name in pre_fields:
        meta = kw.get(name)
        if not meta:
            no_meta.append(name)
            continue
        lvl = meta["fuzzy_level"]
        lvl_hist[lvl] += 1
        cols += lvl

    print(f"\n前件总列数（= Σ 各字段 fuzzy_level）: {cols}")
    print(f"各字段级数分布: {dict(lvl_hist)}")
    print(f"无 RuleKeyword 元数据、无法建论域的前件: {len(no_meta)} 个 -> {no_meta[:10]}")

    print("\n结论参数清单:")
    for name, cnt in sol_fields.most_common():
        meta = kw.get(name)
        lvl = meta["fuzzy_level"] if meta else "-"
        print(f"    {name:<16} 被 {cnt:>5} 条规则作为结论   fuzzy_level={lvl}")

    print("\n矩阵形状:")
    print(f"    connected_matrix : ({kept}, {cols})")
    print(f"    solution_matrix  : ({kept}, {len(sol_fields)})")

    # 稀疏度：每行平均有多少个 1
    ones_per_row = sum(pre_fields.values())
    print(f"\nconnected_matrix 理论非零数: {ones_per_row} "
          f"(每条规则前件数之和)")
    print(f"    占总格子比: {ones_per_row / (kept * cols) * 100:.4f}%")
    print("    => 矩阵本身极度稀疏，它不是在做稠密线性代数，")
    print("       而是把「规则前件命中哪个桶」摊平成一维向量，")
    print("       好让「所有规则同时算激活度」变成一次矩阵-向量乘。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
