"""E2 步骤1 回归验证：新版词法解析对现有规则库的影响面。

做法：用 git HEAD 里的旧版 parsing.py / macros.py 与工作区新版做**逐条对照**，
确认本次改动（词表派生 + 多段后缀匹配）对现有 1646 条规则**零行为变化**。

本脚本只读，不修改任何文件、不执行任何回退操作。

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_e2_step1_regression.py
"""

import os
import subprocess
import sys
import types
from collections import Counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# git 仓库根（git show 的路径以仓库根为基准）
_REPO = os.path.dirname(_BACKEND)

import django

django.setup()

from process.models.rules import RuleMethod  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core import parsing as new_parsing  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core import macros as new_macros  # noqa: E402

RULE_PATH = "backend/process/algorithms/fuzzy/fuzzy_core/parsing.py"
MACROS_PATH = "backend/process/algorithms/fuzzy/fuzzy_core/macros.py"


def _load_old_module(git_path, name, fix_import=True):
    """从 git HEAD 载入旧版模块（只读，不动工作区）。"""
    src = subprocess.check_output(
        ["git", "show", f"HEAD:{git_path}"], cwd=_REPO
    ).decode("utf-8")
    # 仓库文件带 UTF-8 BOM，必须去掉才能编译
    src = src.lstrip("\ufeff")
    if fix_import:
        src = src.replace(
            "from .macros import",
            "from process.algorithms.fuzzy.fuzzy_core.macros import",
        )
    mod = types.ModuleType(name)
    mod.__dict__["__file__"] = f"<git HEAD:{git_path}>"
    exec(compile(src, f"<git HEAD:{git_path}>", "exec"), mod.__dict__)
    return mod


def main():
    print("=" * 72)
    print("E2 步骤1 回归验证：新版词法 vs 旧版词法")
    print("=" * 72)

    old_macros = _load_old_module(MACROS_PATH, "old_macros")
    old_parsing = _load_old_module(RULE_PATH, "old_parsing")

    # ---- M1: 等级词全集差异 ----
    old_words = set(old_macros.ALL_LEVEL_WORDS)
    new_words = set(new_macros.ALL_LEVEL_WORDS)
    print("\n[M1] ALL_LEVEL_WORDS 差异")
    print(f"  旧: {len(old_words)} 个   新: {len(new_words)} 个")
    print(f"  新增: {sorted(new_words - old_words)}")
    print(f"  移除: {sorted(old_words - new_words)}")

    # ---- 取全量规则 ----
    rules = list(
        RuleMethod.objects.filter(is_deleted=False).values_list("rule_description", flat=True)
    )
    print(f"\n[M0] 规则库条数（is_deleted=False）: {len(rules)}")

    # ---- M2: 每个词法单元的 split_phase 对照 ----
    diff_counter = Counter()
    diff_samples = []
    level_counter = Counter()
    token_count = 0
    for rule in rules:
        for word in (rule or "").split():
            if word in ("IF", "AND", "THEN", "Then", "then"):
                continue
            token_count += 1
            old_info = old_parsing.split_phase(word)
            new_info = new_parsing.split_phase(word)
            if old_info != new_info:
                key = (old_info.get("name"), old_info.get("level"),
                       new_info.get("name"), new_info.get("level"))
                diff_counter[key] += 1
                if len(diff_samples) < 10:
                    diff_samples.append((word, old_info, new_info))
            level_counter[str(new_info.get("level"))] += 1

    print(f"\n[M2] split_phase 对照（{token_count} 个词法单元）")
    print(f"  结果不同的单元: {sum(diff_counter.values())}")
    if diff_counter:
        for (on, ol, nn, nl), cnt in diff_counter.most_common(20):
            print(f"    {cnt:5d} x  旧(name={on!r}, level={ol!r})"
                  f"  ->  新(name={nn!r}, level={nl!r})")
        for word, oi, ni in diff_samples:
            print(f"    样例: {word!r}\n      旧 {oi}\n      新 {ni}")
    else:
        print("  [OK] 全部一致")

    print("\n[M2b] 新版 level 词分布（前 12）")
    for word, cnt in level_counter.most_common(12):
        print(f"    {word:<16} {cnt}")

    # ---- M3: is_level_word 对照 ----
    is_diff = Counter()
    for rule in rules:
        for word in (rule or "").split():
            if word in ("IF", "AND", "THEN", "Then", "then"):
                continue
            info = old_parsing.split_phase(word)
            lvl = info.get("level", "")
            if lvl is None:
                continue
            o = old_parsing.is_level_word(lvl)
            n = new_parsing.is_level_word(lvl)
            if o != n:
                is_diff[(lvl, o, n)] += 1
    print(f"\n[M3] is_level_word 对照：差异 {sum(is_diff.values())} 处")
    for (lvl, o, n), cnt in is_diff.most_common(10):
        print(f"    {cnt:5d} x  {lvl!r}: 旧={o} -> 新={n}")
    if not is_diff:
        print("  [OK] 全部一致")

    # ---- M4: collect_param_names 对照 ----
    rule_list = list(rules)
    old_params = old_parsing.collect_param_names(rule_list)
    new_params = new_parsing.collect_param_names(rule_list)
    print(f"\n[M4] collect_param_names 对照")
    print(f"  旧: {len(old_params)} 个   新: {len(new_params)} 个")
    print(f"  新增: {sorted(new_params - old_params)}")
    print(f"  移除: {sorted(old_params - new_params)}")

    # ---- M5: resolve_bucket 对现有词形是否可解析 ----
    print("\n[M5] resolve_bucket(5, <现有档位词>) 自检")
    for w in ("low", "medium", "high"):
        try:
            b = new_macros.resolve_bucket(5, w)
            print(f"    {w!r} -> 桶{b}")
        except ValueError as e:
            print(f"    {w!r} -> 报错: {e}")

    print("\n" + "=" * 72)
    total_diff = sum(diff_counter.values()) + sum(is_diff.values())
    if total_diff == 0 and old_params == new_params:
        print("结论：本次改动对现有规则库【零行为变化】")
    else:
        print(f"结论：存在 {total_diff} 处行为差异 + "
              f"{len(old_params ^ new_params)} 个参数名差异（需评估）")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
