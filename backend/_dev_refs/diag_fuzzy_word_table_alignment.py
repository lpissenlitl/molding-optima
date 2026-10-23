"""校验：后端 LEVEL_WORDS_BY_LVL 与前端 LEVEL_WORDS 是否逐档一致。

E2 要求「三方词表收敛到后端一处权威定义」。前端 `frontend/src/constants/rule-const.ts`
里的 `LEVEL_WORDS: Record<FuzzyLevel, string[]>` 是另一个来源，本脚本比对两者，
防止任何一侧改动后另一侧悄悄漂移。

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_word_table_alignment.py
"""

import os
import re
import sys

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

sys.path.insert(0, os.path.join(_BACKEND, "process", "algorithms", "fuzzy"))

from fuzzy_core.macros import LEVEL_WORDS_BY_LVL  # noqa: E402

FRONT_FILE = os.path.join(
    os.path.dirname(_BACKEND), "frontend", "src", "constants", "rule-const.ts"
)


def parse_front_level_words(path):
    """从前端 rule-const.ts 里抠出 LEVEL_WORDS 的字面量。"""
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(
        r"export const LEVEL_WORDS[^=]*=\s*\{(.*?)\n\}", src, re.S
    )
    if not m:
        return None
    body = m.group(1)
    table = {}
    for lvl_m in re.finditer(r"(\d+)\s*:\s*\[(.*?)\]", body, re.S):
        lvl = int(lvl_m.group(1))
        words = re.findall(r"'([a-z_]+)'", lvl_m.group(2))
        table[lvl] = words
    return table


def main():
    print("=" * 72)
    print("词表一致性校验：后端 LEVEL_WORDS_BY_LVL  vs  前端 LEVEL_WORDS")
    print("=" * 72)

    if not os.path.isfile(FRONT_FILE):
        print(f"[SKIP] 未找到前端文件: {FRONT_FILE}")
        return 0

    front = parse_front_level_words(FRONT_FILE)
    if front is None:
        print("[FAIL] 无法从前端文件解析出 LEVEL_WORDS")
        return 1

    print(f"\n前端文件: {os.path.relpath(FRONT_FILE, os.path.dirname(_BACKEND))}")
    print(f"前端档位: {sorted(front)}")
    print(f"后端档位: {sorted(LEVEL_WORDS_BY_LVL)}")

    all_lvls = sorted(set(front) | set(LEVEL_WORDS_BY_LVL))
    problems = []
    print()
    for lvl in all_lvls:
        f_words = front.get(lvl)
        b_words = list(LEVEL_WORDS_BY_LVL.get(lvl, ()))
        if f_words is None:
            print(f"  [DIFF] {lvl} 档: 前端缺失，后端 = {b_words}")
            problems.append((lvl, "前端缺失"))
            continue
        if b_words is None:
            print(f"  [DIFF] {lvl} 档: 后端缺失，前端 = {f_words}")
            problems.append((lvl, "后端缺失"))
            continue
        if f_words == b_words:
            print(f"  [OK]   {lvl} 档一致: {b_words}")
        else:
            print(f"  [DIFF] {lvl} 档不一致")
            print(f"           前端: {f_words}")
            print(f"           后端: {b_words}")
            problems.append((lvl, "词表不一致"))

    print()
    if problems:
        print(f"结论：{len(problems)} 处不一致 —— 需要收敛")
        return 1
    print("结论：前后端词表【完全一致】")
    return 0


if __name__ == "__main__":
    sys.exit(main())
