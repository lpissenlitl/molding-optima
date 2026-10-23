"""统计 levelN 编号形式在当前规则库/算法链路里的真实使用情况。

回答三个问题：
  Q1  有效规则（is_deleted=False）里，levelN 出现多少次？
  Q2  已删除规则（is_deleted=True）里有没有 levelN？—— 判断"历史上用过后来废弃"还是"从未用过"
  Q3  前端 LEVEL_WORDS 里有没有 levelN？—— 判断前端能否产出这种形态

另附：split_phase 对 `X_levelN` 的解析行为（词法层已认，但有没有数据走这条路）。
"""

import os
import re
import sys
from collections import Counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

from process.models.rules import RuleMethod  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import (  # noqa: E402
    parse_rule, split_phase, is_level_word,
)

LEVEL_NUM_RE = re.compile(r'\blevel(\d+)\b')


def scan(rules, label):
    pre_hits = Counter()
    sol_hits = Counter()
    token_hits = Counter()
    total = 0
    for desc in rules:
        if not desc:
            continue
        total += 1
        # 原始文本里出现 levelN 的次数
        for m in LEVEL_NUM_RE.finditer(desc):
            token_hits[m.group(0)] += 1
        info = parse_rule(desc)
        for p in info.get('preconditions', []):
            lvl = str(p.get('level', ''))
            if LEVEL_NUM_RE.fullmatch(lvl):
                pre_hits[lvl] += 1
        for s in info.get('solutions', []):
            for key in ('level', 'value'):
                v = str(s.get(key, ''))
                if LEVEL_NUM_RE.fullmatch(v):
                    sol_hits[v] += 1
    print(f"\n--- {label}（{total} 条）---")
    print(f"  原始文本含 levelN 的规则数: {sum(token_hits.values())} 次"
          f"  明细: {dict(token_hits) or '无'}")
    print(f"  解析后【前件】level 命中 levelN: {sum(pre_hits.values())} 次"
          f"  明细: {dict(pre_hits) or '无'}")
    print(f"  解析后【结论】命中 levelN: {sum(sol_hits.values())} 次"
          f"  明细: {dict(sol_hits) or '无'}")
    return pre_hits, sol_hits, token_hits


def main():
    print("=" * 72)
    print("levelN 编号形式使用情况统计")
    print("=" * 72)

    active = list(
        RuleMethod.objects.filter(is_deleted=False)
        .values_list("rule_description", flat=True)
    )
    deleted = list(
        RuleMethod.objects.filter(is_deleted=True)
        .values_list("rule_description", flat=True)
    )

    scan(active, "Q1 有效规则 is_deleted=False")
    scan(deleted, "Q2 已删除规则 is_deleted=True")

    # ---- Q3 前端 ----
    print("\n--- Q3 前端 LEVEL_WORDS ---")
    front = os.path.join(os.path.dirname(_BACKEND), "frontend", "src")
    found = []
    if os.path.isdir(front):
        for root, _dirs, files in os.walk(front):
            for fn in files:
                if not fn.endswith((".ts", ".vue", ".js")):
                    continue
                path = os.path.join(root, fn)
                try:
                    with open(path, encoding="utf-8", errors="ignore") as fh:
                        for lineno, line in enumerate(fh, 1):
                            if "LEVEL_WORDS" in line:
                                found.append((os.path.relpath(path, front), lineno,
                                              line.strip()[:120]))
                except OSError:
                    pass
    if found:
        for rel, lineno, line in found[:12]:
            print(f"  {rel}:{lineno}  {line}")
        print(f"  共 {len(found)} 处引用")
    else:
        print("  未在前端 src 找到 LEVEL_WORDS 定义")

    # ---- 附：词法层对 X_levelN 的解析行为 ----
    print("\n--- 附：split_phase 对 `X_levelN` 的解析 ---")
    for phrase in ("IV0_level3", "IV0_level1", "SHORTSHOT_level5", "IV0_low"):
        info = split_phase(phrase)
        print(f"  {phrase!r:<20} -> name={info.get('name')!r:<14}"
              f" level={info.get('level')!r:<12}"
              f" is_level_word={is_level_word(str(info.get('level', '')))}")

    # ---- 附：当前全局表对 levelN 的处理 ----
    print("\n--- 附：现行 LEGACY_HS_MAPPING_DICT 对 levelN 的取值 ---")
    from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT
    for w in ("level1", "level3", "level5", "level9"):
        print(f"  {w} -> {LEGACY_HS_MAPPING_DICT.get(w)}")
    print("  -> 5 档字段上 level3 会指向桶2（该字段的 medium 位），而非编号语义期望的桶2")
    print("    —— 巧合一致；但 level1 在 5 档上会指向桶0（very_low），编号语义期望的也是桶0。")
    print("    -> 编号形式在全局表下【恰好】与 per-field 语义一致（因为编号就是相对位置）。")

    print("\n" + "=" * 72)
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
