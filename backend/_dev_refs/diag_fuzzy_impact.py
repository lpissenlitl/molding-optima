"""诊断：模糊推理设计缺陷的**影响面**（真实 DB 数据）

2026-10-22

配合 `_dev_refs/diag_fuzzy_design.py`（设计层实证）使用：
- 那份脚本回答「机制错在哪」
- 这份脚本回答「错的东西影响多少条规则 / 多少参数」

统计项：
  B1  规则前件个数分布
  B2  门控可行性：每条规则有几个前件真能当门控
  B3  失活规则（零门控）占比 + 典型形态
  B4  前件 level 词分布 + 带 very_/extremely_ 前缀的污染名统计
  B5  结论参数的 RuleKeyword.fuzzy_level 分布（决定档位是否错位）
  B6  结论参数名被污染（name 含 _very/_extremely）的规则数
  B7  同一规则串跨库重复度

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_impact.py
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

from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT
from process.models.rules import RuleKeyword, RuleMethod
from process.algorithms.fuzzy.fuzzy_core.macros import (
    ALL_LEVEL_WORDS,
    DEFECT_CONST,
    FUZZY_LEVELS,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import (
    classify_name,
    is_level_word,
    parse_rule,
    split_phase,
)


def hr(title):
    print()
    print("=" * 74)
    print(title)
    print("=" * 74)


# 规则里出现的、会被词法层污染的参数名后缀
POLLUTION_PREFIX = ("very_", "extremely_")


def is_polluted(name):
    n = str(name or "").lower()
    return any(p in n for p in POLLUTION_PREFIX)


def main():
    rules = list(RuleMethod.objects.filter(is_active=True).all())
    total = len(rules)
    hr(f"B0  活跃规则总数 = {total}")

    keywords = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}

    pre_count_dist = Counter()
    gate_count_dist = Counter()
    dead_rules = []
    level_word_dist = Counter()
    polluted_pre = Counter()
    conclusion_params = Counter()
    conclusion_fuzzy_lvl = Counter()
    rule_str_count = Counter()

    for rm in rules:
        desc = (rm.rule_description or "").strip()
        rule_str_count[desc] += 1
        if not desc:
            continue

        parsed = parse_rule(desc)
        pres = parsed.get("preconditions", []) or []
        sols = parsed.get("solutions", []) or []

        pre_count_dist[len(pres)] += 1

        # ---- B2 门控可行性 ----
        gates = 0
        for pre in pres:
            name = pre.get("name")
            lv = pre.get("level")
            level_word_dist[str(lv)] += 1
            if is_polluted(name):
                polluted_pre[str(name)] += 1
            if not is_level_word(lv):
                continue
            if classify_name(str(name)) == "defect":
                continue          # 缺陷：路由层已保证，网络层被丢弃
            if str(name) not in keywords:
                continue          # 无 RuleKeyword → 建不了论域
            if str(lv) not in LEGACY_HS_MAPPING_DICT:
                continue
            gates += 1
        gate_count_dist[gates] += 1
        if gates == 0:
            dead_rules.append((rm, desc, pres, sols))

        # ---- B5/B6 结论参数 ----
        for sol in sols:
            name = sol.get("name")
            if not name:
                continue
            conclusion_params[str(name)] += 1
            if is_polluted(name):
                continue
            kw = keywords.get(str(name))
            if kw is not None:
                conclusion_fuzzy_lvl[int(kw.fuzzy_level)] += 1

    # ---------------------------------------------------------------- B1
    hr("B1  规则前件个数分布")
    for k, v in sorted(pre_count_dist.items()):
        bar = "#" * max(1, int(v / max(total, 1) * 60))
        print(f"  {k} 个前件: {v:>5} 条  {bar}")

    # ---------------------------------------------------------------- B2
    hr("B2  每条规则『真正能当门控』的前件个数")
    print("  门控 = 前件是工艺参数 + level 是档位词 + 该参数有 RuleKeyword + level 在 LEGACY_HS_MAPPING_DICT")
    for k, v in sorted(gate_count_dist.items()):
        pct = v / max(total, 1) * 100
        bar = "#" * max(1, int(pct))
        print(f"  {k} 个有效门控: {v:>5} 条 ({pct:5.1f}%)  {bar}")

    # ---------------------------------------------------------------- B3
    hr("B3  零门控规则（= 静默失活，永远不会产生建议）")
    print(f"  失活规则 = {len(dead_rules)} 条 ({len(dead_rules) / max(total, 1) * 100:.1f}%)")
    if dead_rules:
        print("\n  失活原因分类：")
        cause = Counter()
        for rm, desc, pres, sols in dead_rules:
            names = [str(p.get("name")) for p in pres]
            if not names:
                cause["无前件（解析失败/规则串为空）"] += 1
            elif all(n in DEFECT_CONST for n in names):
                cause["前件只有缺陷名（无参数门控）"] += 1
            elif any(is_polluted(n) for n in names):
                cause["前件参数名被 very_/extremely_ 污染"] += 1
            elif all(not is_level_word(str(p.get("level"))) for p in pres):
                cause["前件 level 不是档位词（如 worse）"] += 1
            else:
                cause["前件参数查不到 RuleKeyword"] += 1
        for k, v in cause.most_common():
            print(f"    {k:<42} {v:>5} 条")

        print("\n  典型样本（前 8 条）：")
        for rm, desc, pres, sols in dead_rules[:8]:
            print(f"    id={rm.id:<6} {desc[:88]}")

    # ---------------------------------------------------------------- B4
    hr("B4  前件 level 词分布")
    print(f"  ALL_LEVEL_WORDS = {sorted(ALL_LEVEL_WORDS)}")
    print(f"  LEGACY_HS_MAPPING_DICT 里的档位词 = "
          f"{[k for k in LEGACY_HS_MAPPING_DICT if k not in ('add', 'reduce', 'adjust')]}")
    print()
    for lv, n in level_word_dist.most_common(20):
        in_all = "OK" if lv in ALL_LEVEL_WORDS else "非档位词"
        in_map = "OK" if lv in LEGACY_HS_MAPPING_DICT else "!! 不在LEGACY_HS_MAPPING_DICT"
        note = ""
        if lv in ALL_LEVEL_WORDS and lv not in LEGACY_HS_MAPPING_DICT:
            note = "  ← is_level_word 放行，但查表会 KeyError"
        print(f"    {str(lv):<16} {n:>6}  {in_all:<8} {in_map:<24}{note}")

    print(f"\n  被污染的参数名 top 10：")
    if polluted_pre:
        for k, v in polluted_pre.most_common(10):
            print(f"    {k:<28} {v:>6} 次")
    else:
        print("    (无)")

    # ---------------------------------------------------------------- B5
    hr("B5  结论参数的 RuleKeyword.fuzzy_level 分布")
    print("  引擎的档位→桶映射是**全局静态表** LEGACY_HS_MAPPING_DICT（只有 3 档语义：low/mid/high）")
    print("  而桶数由每个参数自己的 fuzzy_level 决定 → 5/7/9 档必然错位")
    print()
    for lvl, n in sorted(conclusion_fuzzy_lvl.items()):
        words = FUZZY_LEVELS.get(lvl)
        if lvl == 3:
            verdict = "OK（3 档语义与 LEGACY_HS_MAPPING_DICT 完全对齐）"
        elif lvl == 5:
            verdict = "!! 错位一档：low→very_low桶, mid→low桶, high→mid桶"
        else:
            verdict = f"!! 完全脱节：档位词表 {words} 不存在，只落在最左 3 桶"
        pct = n / max(sum(conclusion_fuzzy_lvl.values()), 1) * 100
        print(f"  fuzzy_level={lvl}: {n:>6} 次 ({pct:5.1f}%)  {verdict}")

    # ---------------------------------------------------------------- B6
    hr("B6  结论参数名被污染的规则数")
    polluted_sol = 0
    for rm in rules:
        parsed = parse_rule(rm.rule_description or "")
        for sol in parsed.get("solutions", []) or []:
            if is_polluted(sol.get("name")):
                polluted_sol += 1
                break
    print(f"  结论参数名含 very_/extremely_ 的规则 = {polluted_sol} 条")
    print("  → 这些规则的结论参数查不到 RuleKeyword → 调整量无处安放 → **结论被丢弃**")

    # ---------------------------------------------------------------- B7
    hr("B7  同一规则串跨库重复度")
    dup_groups = {k: v for k, v in rule_str_count.items() if v > 1}
    dup_records = sum(dup_groups.values())
    print(f"  规则串去重后 = {len(rule_str_count)} 条，实际记录 = {total} 条")
    print(f"  重复组 = {len(dup_groups)} 组，涉及记录 {dup_records} 条"
          f"（占 {dup_records / max(total, 1) * 100:.1f}%）")
    print("\n  重复最多的 10 条规则串：")
    for k, v in Counter(rule_str_count).most_common(10):
        print(f"    x{v:<4} {k[:76]}")
    print("\n  >>> 跨库副本全部参与推理 → 同一工艺知识被重复计入激活度分母，")
    print("  >>> 进一步摊薄单条规则的调整量。")

    print()
    print("=" * 74)
    print("诊断结束")
    print("=" * 74)


if __name__ == "__main__":
    main()
