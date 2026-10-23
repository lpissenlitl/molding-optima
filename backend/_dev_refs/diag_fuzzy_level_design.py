"""档位映射的正确解法：全局静态表 vs per-parameter 词表

2026-10-22

回应一个设计判断：
「算法不会因为 3/5 级模糊等级就不能用，这肯定是算法设计的问题」

本脚本要证明三件事：
  1. 规则串（知识层）不需要改，**改的是引擎的解释器**
  2. 把全局表从 3 档改成 5 档，是「用一个 bug 换另一个 bug」
     —— 只要库里同时存在 3 档与 5 档参数，就必然有一边错
  3. 唯一正解是：档位→桶索引的映射，由**该参数自己的档位词表**决定

判据（语义正确性）：
  取 x = 论域正中。
  - 5 档参数：x 落在「中间档」，此时 low 与 high 的激活度应当**对称且都偏低**
  - 若 high 激活度 ≈ 1.0，说明「高」被当成了「中间档」→ 档位错位

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_level_design.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
FUZZY_DIR = os.path.join(BACKEND, "process", "algorithms", "fuzzy")
sys.path.insert(0, FUZZY_DIR)

import numpy as np

from fuzzy_core.functional import gauss_mf
from fuzzy_core.macros import HS_MAPPING_DICT


def hr(t):
    print()
    print("=" * 78)
    print(t)
    print("=" * 78)


# 各档位数的词表（引擎应当按参数自己的档位数取用）
LEVEL_WORDS_BY_LVL = {
    3: ["low", "mid", "high"],
    5: ["very_low", "low", "mid", "high", "very_high"],
    7: ["extremely_low", "very_low", "low", "mid", "medium", "high", "very_high"],
    9: ["extremely_low", "very_low", "low", "low_mid", "mid", "mid_high", "high",
        "very_high", "extremely_high"],
}

# 现状：全局静态表（3 档语义）
GLOBAL_3 = {"low": 0, "mid": 1, "medium": 1, "high": 2}
# 另一种「改法」：把全局表改成 5 档语义
GLOBAL_5 = {"very_low": 0, "low": 1, "mid": 2, "medium": 2, "high": 3, "very_high": 4}


def feature(lvl, lo, hi):
    """按档位数建高斯隶属度参数（与 FuzzyFeature 同构）。"""
    sigma = (hi - lo) / (2 * (lvl - 1))
    means = np.r_[lo, np.quantile([lo, hi], np.arange(1, lvl - 1) / (lvl - 1)), hi]
    return [float(m) for m in means], float(sigma)


def bucket_global(word, table):
    return table.get(word)


def bucket_per_param(word, lvl):
    """per-parameter 词表定位：词表由参数自己的档位数决定。"""
    words = LEVEL_WORDS_BY_LVL.get(lvl) or LEVEL_WORDS_BY_LVL[3]
    w = "mid" if word == "medium" else word
    if w in words:
        return words.index(w)
    return None


def mu(lvl, lo, hi, x, bucket):
    means, sigma = feature(lvl, lo, hi)
    if bucket is None or bucket >= len(means):
        return None
    return float(gauss_mf(x, means[bucket], sigma))


# 实验用的论域与观测点（模块级，供 _row 引用）
LO, HI = 0.0, 100.0
X = 50.0


def _fmt(m):
    return f"{m:>12.4f}" if m is not None else f"{'越界!!':>12}"


def _row(name, lvl, word, b, verdict_extra=""):
    words = LEVEL_WORDS_BY_LVL[lvl]
    semantic = words[b] if (b is not None and b < len(words)) else "越界"
    m = mu(lvl, LO, HI, X, b)
    ok = (semantic == word) or (word == "medium" and semantic == "mid")
    verdict = "OK" if ok else "!! 错位"
    if b is not None and b >= len(words):
        verdict = "!! 桶越界"
    verdict += verdict_extra
    print(f"  {name:<6}{word:<10}{b:>4}{semantic:>12}{_fmt(m)}   {verdict}")


def main():
    hr("实验设置")
    print("  两个参数，同一个论域 [0, 100]：")
    print("    KA: fuzzy_level=3  → 桶序 [low, mid, high]")
    print("    KB: fuzzy_level=5  → 桶序 [very_low, low, mid, high, very_high]")
    print("  规则串（知识层，**不需要改**）：")
    print("    IF KA_low THEN ...      IF KB_low THEN ...")
    print("    IF KA_high THEN ...     IF KB_high THEN ...")
    print("  取 x = 50（各参数论域的正中）")
    print()

    hr("方案 1：全局表按 3 档语义（= 现状 HS_MAPPING_DICT）")
    print(f"  {'参数':<6}{'规则词':<10}{'桶':>4}{'该桶语义':>12}{'激活度':>12}   判定")
    print("  " + "-" * 72)
    for lvl, name in ((3, "KA"), (5, "KB")):
        for word in ("low", "high"):
            extra = "  ← x 在正中却判为『高』" if (word == "high" and lvl == 5) else ""
            _row(name, lvl, word, bucket_global(word, GLOBAL_3), extra)

    hr("方案 2：把全局表改成 5 档语义（『修一下 HS_MAPPING_DICT 就完事』）")
    print(f"  {'参数':<6}{'规则词':<10}{'桶':>4}{'该桶语义':>12}{'激活度':>12}   判定")
    print("  " + "-" * 72)
    for lvl, name in ((3, "KA"), (5, "KB")):
        for word in ("low", "high"):
            extra = "  ← 3 档参数被反向弄错" if (word == "low" and lvl == 3) else ""
            _row(name, lvl, word, bucket_global(word, GLOBAL_5), extra)

    hr("方案 3：per-parameter 词表（档位→桶由参数自己的 fuzzy_level 决定）")
    print(f"  {'参数':<6}{'规则词':<10}{'桶':>4}{'该桶语义':>12}{'激活度':>12}   判定")
    print("  " + "-" * 72)
    for lvl, name in ((3, "KA"), (5, "KB")):
        for word in ("low", "high"):
            _row(name, lvl, word, bucket_per_param(word, lvl))

    hr("结论")
    print("  方案 1（现状）：5 档参数全错 —— low 落到 very_low 桶，high 落到 mid 桶")
    print("  方案 2（改全局表）：5 档对了，3 档反了 —— **用一个 bug 换另一个 bug**")
    print("  方案 3（per-parameter）：3 档 / 5 档同时正确")
    print()
    print("  关键判据（x=50，各参数论域正中）：")
    for lvl, name in ((3, "KA"), (5, "KB")):
        m_low_g3 = mu(lvl, LO, HI, X, bucket_global("low", GLOBAL_3))
        m_high_g3 = mu(lvl, LO, HI, X, bucket_global("high", GLOBAL_3))
        m_low_pp = mu(lvl, LO, HI, X, bucket_per_param("low", lvl))
        m_high_pp = mu(lvl, LO, HI, X, bucket_per_param("high", lvl))
        print(f"    {name} (lvl={lvl})  现状: low={m_low_g3:.4f} high={m_high_g3:.4f}"
              f"   per-param: low={m_low_pp:.4f} high={m_high_pp:.4f}")
    print()
    print("  x 在正中时，low 与 high 的激活度应当**对称且都偏低**（x 确实不在两端）。")
    print("  现状下 KB 的 high=1.0000 —— 说明『高』被当成了『中间档』，")
    print("  规则写 high 时其实在判 x 处于中间，命中逻辑整体平移了一档。")
    print()
    print("  ⇒ 正确修法：档位→桶索引的映射必须随参数而变，")
    print("     而不是把某一张全局字典从 3 档改成 5 档。")
    print("  ⇒ 规则库（知识层）一个字都不用改；改的是引擎的解释器。")

    print()
    print("=" * 78)
    print("实验结束")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
