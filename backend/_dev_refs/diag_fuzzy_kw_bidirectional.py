"""规则字段 与 RuleKeyword 元数据的【双向差异】精确统计。

回答四个分类问题：
  ① 正常      : 元数据有 + 规则用
  ② 规则引用了未知字段 : 元数据无 + 规则用   ← 当前被静默跳过，最危险
  ③ 闲置字段  : 元数据有 + 规则不用          ← 正常，不用管
  ④ 备而不用  : 元数据有 + 规则用，但被 collect_param_names 主动排除
                  （缺陷名 / DL* 位置维度）—— E4 待定

同时给出被跳过前件影响的【具体规则】清单。

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_kw_bidirectional.py
"""

import os
import sys
from collections import Counter, defaultdict

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.models.rules import RuleKeyword, RuleMethod  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import (  # noqa: E402
    classify_name,
    collect_param_names,
    is_position_name,
    parse_rule,
)


def main():
    print("=" * 72)
    print("规则字段 vs RuleKeyword 元数据：双向差异")
    print("=" * 72)

    rules = list(
        RuleMethod.objects.filter(is_deleted=False).values_list("rule_description", flat=True)
    )
    kw_rows = list(
        RuleKeyword.objects.filter(is_deleted=False).values(
            "keyword_name", "fuzzy_level", "parameter_kind", "category", "keyword_type"
        )
    )
    kw = {r["keyword_name"]: r for r in kw_rows}

    print(f"\n规则: {len(rules)} 条    RuleKeyword: {len(kw)} 个字段")

    # 规则里出现的全部字段（不排除缺陷/位置）
    pre_fields = Counter()   # 前件
    sol_fields = Counter()   # 结论
    missing_pre_rules = defaultdict(list)   # 缺失前件 -> 受影响规则
    missing_sol_rules = defaultdict(list)

    for desc in rules:
        parsed = parse_rule(desc)
        for pre in parsed.get("preconditions", []):
            name = pre.get("name")
            if not name:
                continue
            pre_fields[name] += 1
            if name not in kw:
                missing_pre_rules[name].append(desc)
        for sol in parsed.get("solutions", []):
            name = sol.get("name")
            if not name:
                continue
            sol_fields[name] += 1
            if name not in kw:
                missing_sol_rules[name].append(desc)

    used = set(pre_fields) | set(sol_fields)
    in_kw_used = sorted(k for k in used if k in kw)
    not_in_kw = sorted(k for k in used if k not in kw)
    idle = sorted(k for k in kw if k not in used)

    print("\n" + "=" * 72)
    print("① 正常（元数据有 + 规则用）")
    print("=" * 72)
    print(f"    {len(in_kw_used)} 个字段")
    print(f"    前件 {len([k for k in in_kw_used if k in pre_fields])} 个 / "
          f"结论 {len([k for k in in_kw_used if k in sol_fields])} 个")

    print("\n" + "=" * 72)
    print("② 规则引用了【元数据中没有】的字段  ← 当前被静默跳过")
    print("=" * 72)
    if not not_in_kw:
        print("    （无）")
    else:
        total_rules = set()
        for name in not_in_kw:
            kind = "前件" if name in pre_fields else "结论"
            cnt = pre_fields.get(name, 0) + sol_fields.get(name, 0)
            print(f"    {name:<20} {kind}  出现 {cnt} 次   "
                  f"classify={classify_name(name)}  pos={is_position_name(name)}")
            total_rules.update(missing_pre_rules.get(name, []))
            total_rules.update(missing_sol_rules.get(name, []))
        print(f"\n    受影响规则数: {len(total_rules)}")
        for r in list(total_rules)[:6]:
            print(f"      - {r}")

    print("\n" + "=" * 72)
    print("③ 闲置字段（元数据有 + 规则不用）")
    print("=" * 72)
    by_kind = Counter()
    by_cat = Counter()
    for k in idle:
        by_kind[kw[k].get("parameter_kind") or "(空)"] += 1
        by_cat[kw[k].get("category") or "(空)"] += 1
    print(f"    共 {len(idle)} 个（占 {len(idle)/len(kw)*100:.1f}%）")
    print(f"    parameter_kind 分布: {dict(by_kind)}")
    print(f"    category 分布      : {dict(by_cat)}")
    # 抽样
    print(f"    样例: {idle[:20]}")

    print("\n" + "=" * 72)
    print("④ 备而不用（元数据有 + 规则用 + 但被 collect_param_names 排除）")
    print("=" * 72)
    collected = collect_param_names([str(r) for r in rules])
    excluded = sorted(k for k in used if k in kw and k not in collected)
    defect_like = [k for k in excluded if classify_name(k) == "defect"]
    pos_like = [k for k in excluded if is_position_name(k)]
    other = [k for k in excluded if k not in defect_like and k not in pos_like]
    print(f"    被 collect_param_names 排除但规则里出现的字段: {len(excluded)} 个")
    print(f"      缺陷名   ({len(defect_like)}): {defect_like}")
    print(f"      位置维度 ({len(pos_like)}): {pos_like}")
    print(f"      其他     ({len(other)}): {other}")
    print("    -> 这些字段的元数据在库里，但元数据查询层不查它们 -> 引擎侧当作『无元数据』跳过")

    # 引擎实际用的元数据集合 = collect_param_names 的结果
    print("\n" + "=" * 72)
    print("引擎侧实际视角")
    print("=" * 72)
    eng_has = sorted(k for k in collected if k in kw)
    eng_missing = sorted(k for k in collected if k not in kw)
    print(f"    collect_param_names 返回: {len(collected)} 个")
    print(f"    其中有元数据: {len(eng_has)}    缺元数据: {len(eng_missing)} -> {eng_missing}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
