"""元数据过滤链的【逐层真相】。

追一条规则从原始文本到最终矩阵的完整路径，统计每一层过滤掉了什么：

  L0  RuleKeyword 表（全量）
  L1  collect_param_names()   词法层：剔除缺陷名 / DL* 位置名
  L2  _load_keyword_dicts()  DB 层：查不到的用实时值【猜】一个伪元数据（兜底）
  L3  nets.py pre_set        规则层：规则里出现过的前件字段
  L4  nets.py pre_dict       引擎层：有元数据的字段（= L2 结果）
  L5  nets.py L630 跳过      最终被静默跳过的前件 + 受影响规则

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_filter_chain.py
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
from process.algorithms.fuzzy.fuzzy_core.parsing import (  # noqa: E402
    classify_name,
    collect_param_names,
    is_position_name,
    parse_rule,
)
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet  # noqa: E402


def main():
    print("=" * 74)
    print("元数据过滤链：逐层真相")
    print("=" * 74)

    rules = list(
        RuleMethod.objects.filter(is_deleted=False).values_list("rule_description", flat=True)
    )
    all_kw = {
        r["keyword_name"]: r
        for r in RuleKeyword.objects.filter(is_deleted=False).values(
            "keyword_name", "fuzzy_level", "range_min", "range_max"
        )
    }

    # ---- L0 全量
    print(f"\nL0 RuleKeyword 全量            : {len(all_kw)} 个")

    # ---- 规则里出现的字段全集
    pre_all, sol_all = Counter(), Counter()
    for desc in rules:
        p = parse_rule(desc)
        for x in p["preconditions"]:
            if x.get("name"):
                pre_all[x["name"]] += 1
        for x in p["solutions"]:
            if x.get("name"):
                sol_all[x["name"]] += 1
    used = set(pre_all) | set(sol_all)
    print(f"L1a 规则里出现的字段全集       : {len(used)} 个"
          f"  (前件 {len(pre_all)} / 结论 {len(sol_all)})")

    # ---- L1 词法层过滤
    collected = collect_param_names([str(r) for r in rules])
    print(f"L1b collect_param_names() 结果  : {len(collected)} 个")

    dropped_defect = sorted(k for k in used if classify_name(k) == "defect")
    dropped_pos = sorted(k for k in used if is_position_name(k))
    print(f"     其中被剔除: 缺陷名 {len(dropped_defect)} / 位置名 {len(dropped_pos)}")
    lost = sorted(used - collected)
    print(f"     used - collected = {len(lost)} 个 -> {lost}")

    # ---- L2 DB 层
    in_db = sorted(k for k in collected if k in all_kw)
    not_in_db = sorted(k for k in collected if k not in all_kw)
    print(f"\nL2a collect 里 DB 查得到的      : {len(in_db)} 个")
    print(f"L2b collect 里 DB 查不到的      : {len(not_in_db)} 个 -> {not_in_db}")
    print("     -> 这些走 _load_keyword_dicts 的兜底（用实时值猜论域）")

    # ---- L3/L4/L5 引擎层
    numeric_rules = [str(r) for r in rules if "THEN" in str(r) and "_add_" in str(r) or
                     "THEN" in str(r) and "_reduce_" in str(r)]
    kw_dicts = []
    for k in in_db:
        r = all_kw[k]
        kw_dicts.append({
            "keyword": k,
            "min_val": r["range_min"],
            "max_val": r["range_max"],
            "step": 0.1,
            "lvl": r["fuzzy_level"],
        })

    print(f"\nL3 送入引擎的 keyword_dicts     : {len(kw_dicts)} 个")
    print(f"     其中带 fuzzy_level 的       : {len([d for d in kw_dicts if d.get('lvl')])} 个")

    rule_array = [{'rule_description': r} for r in numeric_rules]
    net = NumTskRuleNet(rule_array, kw_dicts, [1] * len(rule_array))
    print(f"\nL4a net.pre_set (规则出现过)    : {len(net.pre_set)} 个")
    print(f"L4b net.pre_dict (有元数据)     : {len(net.pre_dict)} 个")
    print(f"L4c net.sol_dict (有元数据)     : {len(net.sol_dict)} 个")

    missing = sorted(set(net.pre_set) - set(net.pre_dict))
    print(f"\nL5  静默跳过的前件字段          : {len(missing)} 个 -> {missing}")

    # 受影响规则
    affected = []
    for desc in numeric_rules:
        p = parse_rule(desc)
        names = [x.get("name") for x in p["preconditions"] if x.get("name")]
        hit = [n for n in names if n in missing]
        if hit:
            affected.append((desc, hit))
    print(f"    受影响规则数                : {len(affected)}")
    for d, h in affected[:10]:
        print(f"      - 缺 {h}: {d}")

    # 结论侧缺元数据
    sol_missing = sorted(set(net.sol_set) - set(net.sol_dict))
    print(f"\nL5b 结论侧缺元数据的字段       : {len(sol_missing)} 个 -> {sol_missing}")

    print("\n" + "=" * 74)
    print("总结：各层过滤量")
    print("=" * 74)
    print(f"  规则里出现字段            {len(used)}")
    print(f"  - 词法层剔除(缺陷/位置)   {len(dropped_defect) + len(dropped_pos)}"
          f"  -> collect {len(collected)}")
    print(f"  - DB 查不到(走兜底猜论域) {len(not_in_db)}  -> 实际有元数据 {len(in_db)}")
    print(f"  - 引擎侧仍缺(静默跳过)    {len(missing)}")
    print(f"  - 规则侧完全不用(闲置)    {len(all_kw) - len(used)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
