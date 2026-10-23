"""fuzzy 模块算法实现 vs 设计规格 对照审计（2026-10-23 第 12 轮；接线前快照）

只读脚本：不写库、不改代码。目的：量化『档位→桶语义』的实现偏差影响面。

⚠️ 本脚本是**接线前的历史对照快照**。背景：`nets.py` 曾用静态 `HS_MAPPING_DICT[level]`
取桶索引，而该表是全局 3 档口径；`macros.resolve_bucket(lvl, word)` 才是按字段级数
定位的正确实现。2026-10-23 已完成接线（`nets.py` 三处改用 `resolve_bucket`）并
**整表删除** `HS_MAPPING_DICT` ⇒ 本脚本自带旧表快照 `LEGACY_HS_MAPPING_DICT`
复现旧口径做 A/B 对照，保证仍可复现历史结论。

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_bucket_mapping.py
"""

import collections
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="gbk", errors="replace")
except Exception:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

from process.algorithms.fuzzy.fuzzy_core.macros import (
    LEVEL_WORDS_BY_LVL,
    resolve_bucket,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import (
    is_level_word,
    split_phase,
)
from process.models.rules import RuleKeyword, RuleMethod

# 旧版全局静态档位表快照（2026-10-23 已从 macros.py 整表删除）：
# 见 `_dev_refs/_legacy_bucket_map.py` —— 本脚本做 A/B 对照需要**旧口径**。
from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT


def hr(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def main():
    kws = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}
    rules = list(
        RuleMethod.objects.filter(is_deleted=False).filter(is_active=True)
        .values_list("rule_description", flat=True)
    )

    hr("1. RuleKeyword.fuzzy_level 分布（字段的桶数）")
    lvl_cnt = collections.Counter(
        int(kw.fuzzy_level or 3) for kw in kws.values())
    print(f"  RuleKeyword 总数: {len(kws)}")
    for lvl, c in sorted(lvl_cnt.items()):
        words = LEVEL_WORDS_BY_LVL.get(lvl)
        print(f"  lvl={lvl}: {c:>4} 个字段   词表={words}")

    hr("2. 前件档位词 → 桶索引：静态表 vs 按字段级数解析")
    print("  『静态』= 旧版静态表 LEGACY_HS_MAPPING_DICT[word]（接线前实际走的路）")
    print("  『正确』= resolve_bucket(该字段的 lvl, word)（现已接线）")
    print()
    print(f"  {'字段':<10}{'lvl':>5}{'档位词':>12}{'静态桶':>8}{'正确桶':>8}"
          f"{'错位':>6}  说明")
    print("  " + "-" * 84)

    # 统计每条规则的前件（参数名, 档位词）
    pre_pairs = []          # (param, word)
    for desc in rules:
        m = re.match(r"^IF\s+(.+?)\s+THEN\s+(.+)$", desc.strip(), re.S)
        if not m:
            continue
        for part in m.group(1).split(" AND "):
            info = split_phase(part)
            name = info.get("name", "")
            level = str(info.get("level", "")).lower()
            if not name or not level:
                continue
            pre_pairs.append((name, level))

    pair_stat = collections.Counter(pre_pairs)
    # nets.py 接线前的实际守卫顺序：先 is_level_word() 放行，再查静态表
    #   ⇒ 只有「是合法等级词、但静态表里没有」的词才会真的 KeyError
    resolvable = [(n, w) for (n, w) in pair_stat if w in LEGACY_HS_MAPPING_DICT]
    guarded_out = [(n, w) for (n, w) in pair_stat
                   if w not in LEGACY_HS_MAPPING_DICT and not is_level_word(w)]
    real_crash = [(n, w) for (n, w) in pair_stat
                  if w not in LEGACY_HS_MAPPING_DICT and is_level_word(w)]

    shown = 0
    mismatch_pairs = []
    for name, word in sorted(resolvable, key=lambda x: -pair_stat[x]):
        kw = kws.get(name)
        if kw is None:
            continue
        lvl = int(kw.fuzzy_level or 3)
        static_bucket = LEGACY_HS_MAPPING_DICT[word]
        try:
            correct_bucket = resolve_bucket(lvl, word)
        except ValueError as e:
            print(f"  {name:<10}{lvl:>5}{word:>12}{static_bucket:>8}"
                  f"{'ERR':>8}{'':>6}  {e}")
            continue
        delta = static_bucket - correct_bucket
        if delta != 0:
            mismatch_pairs.append((name, word, lvl, static_bucket,
                                   correct_bucket, delta, pair_stat[(name, word)]))
        if shown < 24 and delta != 0:
            shown += 1
            words = LEVEL_WORDS_BY_LVL.get(lvl, ())
            correct_word = words[correct_bucket] if correct_bucket < len(words) else "?"
            print(f"  {name:<10}{lvl:>5}{word:>12}{static_bucket:>8}"
                  f"{correct_bucket:>8}{delta:>+6}  正确档位词={correct_word}")
    print("  " + "-" * 84)

    # 汇总
    bad_rules = set()
    total_refs = 0
    bad_refs = 0
    for name, word in resolvable:
        kw = kws.get(name)
        if kw is None:
            continue
        lvl = int(kw.fuzzy_level or 3)
        try:
            correct_bucket = resolve_bucket(lvl, word)
        except ValueError:
            continue
        total_refs += pair_stat[(name, word)]
        if LEGACY_HS_MAPPING_DICT[word] != correct_bucket:
            bad_refs += pair_stat[(name, word)]

    print(f"  桶索引错位的 (参数,档位词) 组合: {len(mismatch_pairs)} 个")
    print(f"  受影响的前件引用次数: {bad_refs} / {total_refs} "
          f"({bad_refs * 100 // max(total_refs, 1)}%)")
    by_lvl = collections.Counter(p[2] for p in mismatch_pairs)
    print(f"  按字段级数分布: {dict(sorted(by_lvl.items()))}")
    off = collections.Counter(p[5] for p in mismatch_pairs)
    print(f"  错位档数分布: {dict(sorted(off.items()))}（正=静态表偏低）")

    hr("3. ★ 崩溃风险：静态表里没有的档位词")
    print("  nets.py 接线前的守卫顺序：先 is_level_word() 放行 → 再查静态表")
    print("  ⇒ 只有「合法等级词、但静态表里没有」的词才会真的 KeyError")
    print(f"  旧静态表的词表键: "
          f"{sorted(k for k in LEGACY_HS_MAPPING_DICT if not k.startswith('level'))}")
    print()
    if guarded_out:
        print(f"  ℹ️ 被 is_level_word() 拦下（不查表 ⇒ 不崩）："
              f"{len(guarded_out)} 个组合，"
              f"{sum(pair_stat[x] for x in guarded_out)} 次引用")
        for name, word in sorted(guarded_out, key=lambda x: -pair_stat[x])[:8]:
            print(f"    · {name:<10} 词={word:<14} 引用 {pair_stat[(name, word)]} 次")
        print()
    if not real_crash:
        print("  ✅ 当前规则库未出现「合法等级词但静态表没有」的词 ⇒ 暂无 KeyError 风险")
        crash_refs = 0
    else:
        print(f"  ⚠️ 出现 {len(real_crash)} 个组合会导致 KeyError：")
        crash_refs = 0
        for name, word in sorted(real_crash, key=lambda x: -pair_stat[x]):
            kw = kws.get(name)
            lvl = int(kw.fuzzy_level or 3) if kw else 0
            crash_refs += pair_stat[(name, word)]
            print(f"    · {name:<10} lvl={lvl} 词={word:<14} "
                  f"引用 {pair_stat[(name, word)]} 次")
        print(f"  合计 {crash_refs} 次引用会触发 KeyError ⇒ 整层推理崩溃")

    hr("4. 结论")
    print(f"  启用规则数            : {len(rules)}")
    print(f"  前件引用总数          : {total_refs}")
    print(f"  桶索引错位的前件引用  : {bad_refs} "
          f"({bad_refs * 100 // max(total_refs, 1)}%)")
    print(f"  可能 KeyError 的引用  : {crash_refs}")
    print()
    print("  ⇒ 旧版静态表是全局 3 档口径，字段级数 >3 时全部错位；")
    print("    正确实现 resolve_bucket(lvl, word) 已于 2026-10-23 接线并删除旧表。")

    print()
    print("=" * 100)
    print("对照审计结束（只读，未写库、未改代码）")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
