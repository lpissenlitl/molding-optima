"""算法内核专项审计（只审 fuzzy 包内部，不涉及上下游链路）

2026-10-22

目的：把「算法部分」的问题收敛成一张确切清单，而不是泛泛地说设计混乱。
只做两件事：
  1) 静态统计：规则库层面各问题模式各有多少条
  2) 动态实证：构造最小用例，调用生产代码 NumTskRuleNet，验证算出来对不对

审计项：
  A1 混合结论规则：同一条规则既有绝对值结论又有百分比结论
     —— 疑点：`rule_classify[i] = 1 if '%' in desc else 0` 是整条规则一个标志，
        而第四层 `cur_params[i] = x[第一个结论参数]` 会把**整行所有结论**乘上
        同一个当前值 ⇒ 绝对值结论被误乘、百分比结论乘错对象
  A2 同参数多桶前件：一条规则的两个前件指向同一参数的不同桶
     —— 疑点：connected_matrix 那一行会出现两个 1 ⇒ 连乘语义失真
  A3 同名前件覆盖：一条规则里同一参数出现两次（前件 dict 赋值覆盖）
  A4 兜底论域：缺 RuleKeyword 时自造 lvl=3 的异构论域
  A5 激活度阈值：MIN_ACTIVATION_THRESHOLD 在 TSK 路径是否被使用

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_algo_audit.py
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

from process.models.rules import RuleKeyword, RuleMethod
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRule, NumTskRuleNet
from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT


def hr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def classify_solution(sol):
    """把一个结论单元归类。"""
    action = sol.get("action")
    value = str(sol.get("value", ""))
    if action in ("add", "reduce"):
        if value.endswith("%"):
            return "pct"
        try:
            float(value)
            return "abs"
        except ValueError:
            return "other"
    if action in ("adjust", "popup"):
        return "check"
    return "other"


def main():
    rules = list(RuleMethod.objects.filter(is_deleted=False).values_list("id", "rule_description"))
    print(f"规则总数（未删除）: {len(rules)}")

    a1_hits = []
    a2_hits = []
    a3_hits = []
    a4_hits = []

    for rid, desc in rules:
        if not desc:
            continue
        parsed = parse_rule(desc)
        sols = parsed["preconditions"] and parsed["solutions"] or parsed["solutions"]
        sols = parsed["solutions"]
        pres = parsed["preconditions"]

        # ---- A1 混合结论 ----
        kinds = Counter(classify_solution(s) for s in sols)
        if kinds.get("pct", 0) and kinds.get("abs", 0):
            a1_hits.append((rid, desc, dict(kinds)))

        # ---- A2 同参数多桶前件 ----
        by_name = {}
        for p in pres:
            by_name.setdefault(p.get("name"), []).append(p.get("level"))
        for nm, lvs in by_name.items():
            if len(lvs) > 1:
                same = len(set(lvs)) == 1
                a2_hits.append((rid, desc, nm, lvs, same))
                break

        # ---- A3 同名前件（NumTskRule 的 dict 覆盖）----
        nr = NumTskRule(desc)
        pre_names = [w for w in desc.split() if w not in ("IF", "AND", "THEN", "Then", "then")]
        seen = set()
        for w in pre_names:
            info = None
            for p in pres:
                pass
            break
        # 直接用 NumTskRule 的解析结果长度与词法解析结果长度比较
        if len(nr.r_preconditions) < len(pres):
            a3_hits.append((rid, desc, len(pres), len(nr.r_preconditions)))

    # ---- A4 兜底论域 ----
    kw_names = set(RuleKeyword.objects.filter(is_deleted=False).values_list("keyword_name", flat=True))
    all_param_names = set()
    for rid, desc in rules:
        if not desc:
            continue
        for s in parse_rule(desc)["solutions"]:
            n = s.get("name")
            if n:
                all_param_names.add(n)
    missing = sorted(n for n in all_param_names if n not in kw_names)

    # ======================================================================
    hr("[A1] 混合结论规则（绝对值 + 百分比同条）")
    print(f"命中: {len(a1_hits)} 条")
    for rid, desc, kinds in a1_hits[:8]:
        print(f"  #{rid} {desc}")
        print(f"        结论形态分布: {kinds}")
    if len(a1_hits) > 8:
        print(f"  ... 另有 {len(a1_hits) - 8} 条")

    # ======================================================================
    hr("[A2] 同参数多桶前件（一条规则里同一参数出现多次）")
    same_lv = [h for h in a2_hits if h[4]]
    diff_lv = [h for h in a2_hits if not h[4]]
    print(f"命中: {len(a2_hits)} 条")
    print(f"  其中 同参数同档位重复（如 IV0_high AND IV0_high）: {len(same_lv)} 条")
    print(f"  其中 同参数不同档位（如 IV0_low AND IV0_high）  : {len(diff_lv)} 条  <-- 语义会被 dict 覆盖改变")
    for rid, desc, nm, lvs, same in diff_lv[:10]:
        print(f"  #{rid} 参数 {nm} 出现档位 {lvs}")
        print(f"        {desc}")

    # ======================================================================
    hr("[A3] 同名前件被 dict 覆盖（NumTskRule 丢失前件）")
    print(f"命中: {len(a3_hits)} 条")
    for rid, desc, n_parse, n_numtsk in a3_hits[:8]:
        print(f"  #{rid} 词法解析 {n_parse} 个前件 → NumTskRule 只剩 {n_numtsk} 个")
        print(f"        {desc}")

    # ======================================================================
    hr("[A4] 结论参数缺 RuleKeyword（会走兜底论域 lvl=3）")
    print(f"结论侧参数总数: {len(all_param_names)}")
    print(f"RuleKeyword 覆盖: {len(all_param_names & kw_names)}")
    print(f"缺失（走兜底）: {len(missing)}")
    for n in missing[:25]:
        cnt = sum(1 for _, d in rules if d and n in d)
        print(f"  {n:20s}  出现在 {cnt} 条规则中")

    # ======================================================================
    hr("[A5] 动态实证：混合结论规则算出来对不对")
    print("构造一条混合规则 + 实际调用生产代码 NumTskRuleNet.predict\n")

    mixed = "IF IV0_low THEN IP0_add_5 AND IV0_reduce_30%"
    kws = [
        {"keyword": "IV0", "lvl": 5, "min_val": 0.0, "max_val": 120.0, "step": 10.0},
        {"keyword": "IP0", "lvl": 5, "min_val": 0.0, "max_val": 200.0, "step": 10.0},
    ]
    net = NumTskRuleNet([{"rule_description": mixed}], kws, [1.0])
    res, _ = net.predict({"IV0": 30.0, "IP0": 100.0}, top_k=5)
    print(f"规则: {mixed}")
    print(f"输入: IV0=30, IP0=100")
    print(f"rule_classify = {net.rule_classify}   （1=百分比规则）")
    print(f"solution_matrix = {net.solution_matrix.tolist()}")
    print(f"rule_solution  = {net.rule_solution}")
    print("输出:")
    for rule_str, act, adj in res:
        print(f"  activation={act!r}")
        print(f"  adjustments = {adj}")
    print()
    print("人工推演（期望）：")
    print("  IP0_add_5      -> 绝对值 +5          -> IP0 建议 = 100 + 5   = 105")
    print("  IV0_reduce_30% -> 相对 IV0 当前值 -30% -> IV0 建议 = 30 * 0.7 = 21")
    print("实际产出见上 -- 若 IP0 是 500 而非 105、或 IV0 不是 21，即为 bug")

    # ======================================================================
    hr("[A5b] 纯百分比多结论：两个百分比结论各自乘谁？")
    mixed2 = "IF IV0_low THEN IV0_reduce_30% AND IP0_reduce_20%"
    net_b = NumTskRuleNet([{"rule_description": mixed2}], kws, [1.0])
    res_b, _ = net_b.predict({"IV0": 30.0, "IP0": 100.0}, top_k=5)
    print(f"规则: {mixed2}")
    print(f"输入: IV0=30, IP0=100")
    print(f"rule_solution = {net_b.rule_solution}  (只有第一个结论参数)")
    for rule_str, act, adj in res_b:
        print(f"  adjustments = {adj}")
    print("人工推演（期望）：IV0 = 30*0.7 = 21 ; IP0 = 100*0.8 = 80")
    print("实际产出见上 -- 若 IV0/IP0 都是乘 30 或都乘 100，即为 bug")

    # ======================================================================
    hr("[A5c] 纯绝对值多结论（对照组，应正确）")
    absrule = "IF IV0_low THEN IV0_add_5 AND IP0_add_3"
    net_c = NumTskRuleNet([{"rule_description": absrule}], kws, [1.0])
    res_c, _ = net_c.predict({"IV0": 30.0, "IP0": 100.0}, top_k=5)
    print(f"规则: {absrule}")
    for rule_str, act, adj in res_c:
        print(f"  adjustments = {adj}")
    print("人工推演（期望）：IV0 = +5 ; IP0 = +3  （无当前值参与）")

    # ======================================================================
    hr("[A6] 动态实证：同参数多桶前件的门控表现")
    multi = "IF IV0_low AND IV0_high THEN IP0_add_5"
    net2 = NumTskRuleNet([{"rule_description": multi}], kws, [1.0])
    print(f"规则: {multi}")
    print(f"connected_matrix = {net2.connected_matrix.tolist()}")
    print("（一行里出现两个 1 -> 连乘会把同一参数的两个桶相乘）")
    res2, _ = net2.predict({"IV0": 30.0, "IP0": 100.0}, top_k=5)
    for rule_str, act, adj in res2:
        print(f"  activation={act!r}  adjustments={adj}")


if __name__ == "__main__":
    main()
