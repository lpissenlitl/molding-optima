"""确认 Mamdani 引擎在生产里是真在跑还是空跑。

背景：
  - fuzzy_algorithm.py:491 在 `_infer_advisory_layer` 里构造 FuzzyRuleNet（Mamdani）
  - 但它只处理「模糊等级结论」这类规则（如 X_add_low，兼容 Rule.dat 风格）
  - 检查/弹窗类结论（X_adjust_提示语）走的是 ParticularRules，不经 Mamdani

本脚本统计：
  Q1 规则库里有多少条规则是「模糊等级结论」？（决定 Mamdani 是否空跑）
  Q2 Mamdani 结论侧用 HS_MAPPING_DICT 定位桶 => P1 是否也影响它？
  Q3 若有模糊等级结论，列出样例

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_mamdani_liveness.py
"""

import os
import re
import sys
from collections import Counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.models.rules import RuleMethod  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import split_phase  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.macros import ALL_LEVEL_WORDS  # noqa: E402


def main():
    print("=" * 72)
    print("Mamdani 引擎生产活性核实")
    print("=" * 72)

    rules = list(
        RuleMethod.objects.filter(is_deleted=False).values_list("rule_description", flat=True)
    )
    print(f"\n有效规则总数: {len(rules)}")

    level_words = set(ALL_LEVEL_WORDS)
    mamdani_like = []      # 结论是模糊等级（low/medium/high/...）=> 走 Mamdani
    popup_like = []        # 结论是 adjust/popup 提示语 => 走 ParticularRules
    numeric_like = []      # 结论是数值/百分比 => 走 NumTskRuleNet

    for desc in rules:
        text = str(desc)
        if " THEN " not in text.upper():
            continue
        then_part = re.split(r"\s+THEN\s+", text, flags=re.I)[-1]
        is_level = False
        is_popup = False
        for token in then_part.replace(",", " ").split():
            info = split_phase(token)
            action = info.get("action", "")
            value = str(info.get("value", ""))
            level = str(info.get("level", ""))
            # 注意：split_phase 对 `X_adjust_提示语` 把 'adjust' 放在 level 字段，
            # 而非 action 字段 —— 两种判定都要覆盖
            if action in ("popup", "adjust") or "adjust" in level or "popup" in level:
                is_popup = True
            elif value.lower() in level_words:
                is_level = True
            elif action in ("add", "reduce"):
                pass
        if is_level:
            mamdani_like.append(desc)
        elif is_popup:
            popup_like.append(desc)
        else:
            numeric_like.append(desc)

    print(f"\nQ1 结论形态分布：")
    print(f"    模糊等级结论 (走 Mamdani FuzzyRuleNet) : {len(mamdani_like)} 条")
    print(f"    检查/弹窗结论 (走 ParticularRules)     : {len(popup_like)} 条")
    print(f"    数值/百分比结论 (走 NumTskRuleNet)      : {len(numeric_like)} 条")

    # 原始 token 形态分布（用于校验上面的判定是否可靠）
    raw = Counter()
    for desc in rules:
        text = str(desc)
        # 注意：不能对规则串做 upper() —— split_phase 的动作词匹配是大小写敏感的，
        # 大写后会被误判成「前件」形态（level=ADD/REDUCE, kind=precondition）
        if " THEN " not in text.upper():
            continue
        then_part = re.split(r"\s+THEN\s+", text, flags=re.I)[-1]
        for token in then_part.replace(",", " ").split():
            info = split_phase(token)
            raw[(
                info.get("action", ""),
                str(info.get("value", ""))[:16],
                str(info.get("level", ""))[:16],
                info.get("kind", ""),
            )] += 1
    print(f"\nQ1b 结论 token 的 split_phase 原始形态（前 25）:")
    for k, v in raw.most_common(25):
        print(f"        action={k[0]!r:<8} value={k[1]!r:<20} level={k[2]!r:<18} kind={k[3]!r:<12} x{v}")

    if mamdani_like:
        print(f"\nQ3 Mamdani 规则样例（前 5 条）:")
        for d in mamdani_like[:5]:
            print(f"    {d}")
        # 结论字段分布
        concl = Counter()
        for d in mamdani_like:
            then = str(d).upper().split(" THEN ", 1)[1]
            for token in then.replace(",", " ").split():
                info = split_phase(token)
                if str(info.get("value", "")).lower() in level_words:
                    concl[(info["name"], info.get("action"), info.get("value"))] += 1
        print(f"\n    Mamdani 结论 (参数, 动作, 档位) 分布：")
        for k, v in concl.most_common(20):
            print(f"        {k}  x{v}")
    else:
        print("\nQ3 [!] 规则库中【没有任何模糊等级结论】")
        print("    => FuzzyRuleNet 虽然代码路径已接线，但实际【空跑】")
        print("    => P1（桶贴错标签）对 Mamdani 只是潜在风险，不是现实故障")

    print("\nQ2 Mamdani 的桶定位点：")
    print("    nets.py L271  前件:  pre_dict[name]['index'] + HS_MAPPING_DICT[level]")
    print("    nets.py L281  结论:  sol_dict[name]['index'] + HS_MAPPING_DICT[level]")
    print("    => 与 NumTskRuleNet L634 同源，P1 对两者【同时成立】")

    return 0


if __name__ == "__main__":
    sys.exit(main())
