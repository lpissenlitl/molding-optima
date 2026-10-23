"""全库体检：档位词表在「前端 / 后端 / 引擎」三方的分叉情况

2026-10-22

背景（回应「这肯定是算法设计的问题」）：
  - 前端 `LEVEL_WORDS` 已经**按 keyword.fuzzy_level 动态取词表**（per-parameter）
  - 后端 `macros.FUZZY_LEVELS` 只有 3/5 档，且用 'mid'
  - 引擎 `LEGACY_HS_MAPPING_DICT` 是**全局静态表**，只有 3 档语义
  ⇒ 前端已经 per-parameter 了，引擎还停在全局表 —— 这不是设计选择，是内部不自洽

本脚本用**最长后缀匹配**还原「真参数名 + 档位词」（这是 E1 的正确解法，
比现状 `split_phase` 的「从右往左取第一个 level 词」更正确），
然后体检全库规则串与各参数 fuzzy_level 的兼容性。

统计项：
  C1  RuleKeyword 全表 fuzzy_level 分布
  C2  前件参数 / 结论参数 的 fuzzy_level 分布
  C3  档位词兼容性体检（前件侧 + 结论侧）
  C4  三种修法各自会命中多少条不兼容规则
  C5  三方词表分叉汇总

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_level_audit.py
"""

import os
import re
import sys
from collections import Counter, defaultdict

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
    FUZZY_LEVELS,
)


def hr(title):
    print()
    print("=" * 76)
    print(title)
    print("=" * 76)


# ---------------------------------------------------------------------------
# 前端权威词表（frontend/src/constants/rule-const.ts LEVEL_WORDS）
# 注意：前端 3 档用 'medium'，7 档 'medium' 在正中；**前端没有 9 档**
# ---------------------------------------------------------------------------
FRONTEND_LEVEL_WORDS = {
    3: ["low", "medium", "high"],
    5: ["very_low", "low", "medium", "high", "very_high"],
    7: ["extremely_low", "very_low", "low", "medium", "high", "very_high",
        "extremely_high"],
}

# 词法切分用的档位词全集（后端 ALL_LEVEL_WORDS ∪ 前端词表）
_ALL_LEVEL_TOKENS = set(ALL_LEVEL_WORDS)
for _w in FRONTEND_LEVEL_WORDS.values():
    _ALL_LEVEL_TOKENS.update(_w)
_ALL_LEVEL_TOKENS = frozenset(_ALL_LEVEL_TOKENS)

# 按长度降序，保证「最长后缀匹配」正确（very_low 优先于 low）
_LEVEL_TOKENS_BY_LEN = sorted(_ALL_LEVEL_TOKENS, key=len, reverse=True)

# 老 fuzzykit 遗留：'mid' 与 'medium' 同义
_MID_ALIASES = {"mid": "medium"}


def split_longest(token):
    """最长后缀匹配：'<name>_<level>' → (name, level)；失败返回 (token, None)"""
    for w in _LEVEL_TOKENS_BY_LEN:
        if token.endswith("_" + w):
            return token[: -len(w) - 1], w
    return token, None


RULE_RE = re.compile(r"^\s*IF\s+(.*?)\s+THEN\s+(.*?)\s*$", re.IGNORECASE | re.DOTALL)


def split_parts(text):
    if not text:
        return []
    return [t for t in re.split(r"\s+AND\s+|\s+and\s+", text.strip()) if t]


def parse_desc(desc):
    """→ (pre_tokens, sol_tokens)"""
    m = RULE_RE.match(desc or "")
    if not m:
        return [], []
    return split_parts(m.group(1)), split_parts(m.group(2))


def normalize(word):
    return _MID_ALIASES.get(str(word).lower(), str(word).lower())


def words_for(lvl):
    """某档位数对应的词表（前端权威；9 档前端缺失 → 兜底 3 档）"""
    return FRONTEND_LEVEL_WORDS.get(lvl) or FRONTEND_LEVEL_WORDS[3]


def compatible(word, lvl):
    """档位词是否在该参数的档位词表内"""
    w = normalize(word)
    return w in words_for(lvl)


def main():
    rules = list(RuleMethod.objects.filter(is_active=True).all())
    keywords = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}

    hr(f"C0  活跃规则 = {len(rules)} 条；RuleKeyword = {len(keywords)} 个")

    # ---------------------------------------------------------------- C1
    hr("C1  RuleKeyword.fuzzy_level 全表分布")
    lvl_dist = Counter()
    lvl_by_cat = defaultdict(Counter)
    for kw in keywords.values():
        lvl_dist[int(kw.fuzzy_level)] += 1
        lvl_by_cat[str(getattr(kw, "category", "") or "?")][int(kw.fuzzy_level)] += 1
    for lvl, n in sorted(lvl_dist.items()):
        print(f"  fuzzy_level={lvl}: {n:>5} 个 ({n / max(len(keywords), 1) * 100:5.1f}%)")
    print("\n  按 category 拆分：")
    for cat, c in lvl_by_cat.items():
        detail = "  ".join(f"{k}档:{v}" for k, v in sorted(c.items()))
        print(f"    {cat:<16} {detail}")

    # ---------------------------------------------------------------- 扫描
    pre_lvl_dist = Counter()
    sol_lvl_dist = Counter()
    pre_incompat = Counter()      # (lvl, word) → 次数
    sol_incompat = Counter()
    pre_total = 0
    sol_numeric = 0               # 数值结论：X_add_2 / X_reduce_30%
    sol_level = 0                 # 档位结论：X_add_low
    sol_advisory = 0              # 提示文本结论：X_adjust_请检查...
    unknown_param_pre = Counter()

    for rm in rules:
        pre_tokens, sol_tokens = parse_desc(rm.rule_description or "")
        for tok in pre_tokens:
            name, level = split_longest(tok)
            if level is None:
                continue
            pre_total += 1
            kw = keywords.get(name)
            if kw is None:
                unknown_param_pre[name] += 1
                continue
            lvl = int(kw.fuzzy_level)
            pre_lvl_dist[lvl] += 1
            if not compatible(level, lvl):
                pre_incompat[(lvl, normalize(level))] += 1
        for tok in sol_tokens:
            # 结论 token 形如 X_add_2 / X_reduce_30% / X_adjust_文本 / X_add_low
            m = re.match(r"^(.+?)_(add|reduce|adjust)_(.+)$", tok)
            if not m:
                continue
            name, act, val = m.groups()
            if act == "adjust":
                # 提示文本结论：引擎本来就不给数值（走文本建议通道）
                sol_advisory += 1
                continue
            kw = keywords.get(name)
            if kw is None:
                continue
            lvl = int(kw.fuzzy_level)
            sol_lvl_dist[lvl] += 1
            if re.match(r"^-?[\d.]+%?$", val):
                sol_numeric += 1
            else:
                sol_level += 1
                if not compatible(val, lvl):
                    sol_incompat[(lvl, normalize(val))] += 1

    # ---------------------------------------------------------------- C2
    hr("C2  规则里出现的参数，其 fuzzy_level 分布")
    print("  【前件参数】")
    for lvl, n in sorted(pre_lvl_dist.items()):
        note = "" if lvl in FRONTEND_LEVEL_WORDS else "  ← 前端 LEVEL_WORDS 无此档（表单会兜底成 3 档）"
        print(f"    fuzzy_level={lvl}: {n:>6} 次{note}")
    print("  【结论参数】")
    for lvl, n in sorted(sol_lvl_dist.items()):
        note = "" if lvl in FRONTEND_LEVEL_WORDS else "  ← 前端 LEVEL_WORDS 无此档"
        print(f"    fuzzy_level={lvl}: {n:>6} 次{note}")
    print(f"\n  前件里查不到 RuleKeyword 的参数名 top 10：")
    for k, v in unknown_param_pre.most_common(10):
        print(f"    {k:<30} {v:>6} 次")

    # ---------------------------------------------------------------- C3
    hr("C3  档位词兼容性体检")
    print("  判据：档位词是否 ∈ 该参数自己档位数对应的词表")
    print(f"  前件侧：{pre_total} 个可判级前件")
    if pre_incompat:
        bad = sum(pre_incompat.values())
        print(f"  !! 不兼容 {bad} 个 ({bad / max(pre_total, 1) * 100:.1f}%)：")
        for (lvl, word), n in pre_incompat.most_common(20):
            print(f"     lvl={lvl}  档位词={word:<16} {n:>6} 次")
    else:
        print("  前件侧全部兼容")
    print(f"\n  结论侧：数值 {sol_numeric} 条 / 档位 {sol_level} 条 / 提示文本 {sol_advisory} 条")
    print("  （提示文本结论走文本建议通道，不参与数值推理，不计入兼容性）")
    if sol_incompat:
        bad = sum(sol_incompat.values())
        print(f"  !! 档位结论不兼容 {bad} 个 ({bad / max(sol_level, 1) * 100:.1f}%)：")
        for (lvl, word), n in sol_incompat.most_common(20):
            print(f"     lvl={lvl}  档位词={word:<16} {n:>6} 次")
    else:
        print("  结论侧全部兼容")

    # ---------------------------------------------------------------- C4
    hr("C4  三种修法各自会踩到什么")
    n3 = lvl_dist.get(3, 0)
    n5 = lvl_dist.get(5, 0)
    n7 = lvl_dist.get(7, 0)
    n9 = lvl_dist.get(9, 0)
    print(f"  库里档位数分布：3档={n3}  5档={n5}  7档={n7}  9档={n9}")
    print()
    print("  方案 A：保持全局表不动（现状）")
    print(f"     后果：5/7/9 档参数全部错位；7档的 'medium' 应在索引 3，引擎给 1（差 2 档）")
    print(f"     受影响前件次数：{pre_lvl_dist.get(5, 0) + pre_lvl_dist.get(7, 0) + pre_lvl_dist.get(9, 0)}")
    print()
    print("  方案 B：把全局表改成 5 档语义")
    print(f"     后果：3 档参数的 'high' → 索引 3，**桶越界**（3 档只有 0/1/2）")
    print(f"     受影响参数：{n3} 个 3 档参数")
    if n3 == 0:
        print("     ⚠ 当前数据下 3 档参数为 0 → 方案 B 表面上『能跑』，")
        print("       但那是**当前数据的侥幸**，一旦有 3 档参数立刻越界崩溃。")
        print("       且 7/9 档参数仍然错位（全局表里没有它们的词）。")
    print()
    print("  方案 C：per-parameter 词表（按参数自己的 fuzzy_level 定位桶）")
    print(f"     后果：3/5/7 档同时正确；9 档需先补前端词表")
    print(f"     需处理的不兼容前件：{sum(pre_incompat.values())} 个（应显式报错，而非静默失活）")

    # ---------------------------------------------------------------- C5
    hr("C5  三方词表分叉汇总")
    print("  【前端】frontend/src/constants/rule-const.ts LEVEL_WORDS（按 fuzzy_level 取）")
    for lvl, ws in FRONTEND_LEVEL_WORDS.items():
        print(f"     {lvl}档: {ws}")
    print(f"     9档: **前端 LEVEL_WORDS 无 9 档** → levelOptionsFor() 兜底返回 3 档词表")
    print("  【后端】backend/.../fuzzy_core/macros.py FUZZY_LEVELS")
    for lvl, ws in FUZZY_LEVELS.items():
        print(f"     {lvl}档: {ws}")
    print("     7/9档: **缺失**")
    print("  【引擎】backend/.../fuzzy_core/macros.py LEGACY_HS_MAPPING_DICT")
    print(f"     {LEGACY_HS_MAPPING_DICT}")
    print()
    print("  ⇒ 三处词表三套内容，且**只有前端是 per-parameter 的**。")
    print("  ⇒ 前端按 keyword.fuzzy_level 给用户选词（= 按参数语义），")
    print("    引擎却用全局表读词（= 按全局假设）—— 这就是『算法设计问题』的直接证据：")
    print("    规则编写侧已经是 per-parameter，推理侧没跟上。")

    print()
    print("=" * 76)
    print("体检结束")
    print("=" * 76)


if __name__ == "__main__":
    main()
