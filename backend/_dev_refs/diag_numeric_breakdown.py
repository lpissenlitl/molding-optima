"""拆解：数值层每一层贡献了多少（2026-10-22）

目的：规则写 `IP0_add_3.8`，实际只推出 +0.006。逐层拆开看：
  隶属度 → 规则激活度 → 归一化 → priority 加权 → delta 贡献

运行：cd backend; $env:PYTHONPATH="."; ../.venv/Scripts/python.exe _dev_refs/diag_numeric_breakdown.py
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

import numpy as np

from process.models import ProcessCondition, ProcessParameter
from process.models.rules import RuleKeyword
from process.services.parameter_optimize import (
    _compose_algorithm_context,
    _extract_machine_info,
    _extract_mold_info,
    _extract_polymer_info,
    _snapshot_parameter,
)
from process.algorithms.fuzzy.services.rule_query_service import (
    RuleQueryContext,
    RuleQueryService,
)
from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet
from process.algorithms.fuzzy.fuzzy_core.parsing import is_level_word


def hr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


cond = None
param = None
for c in (ProcessCondition.objects
          .select_related("polymer", "mold", "injection_machine")
          .order_by("id")):
    if not c.polymer or not c.mold:
        continue
    p = (ProcessParameter.objects
         .filter(process_condition=c).order_by("-seq_idx").first())
    if p:
        cond, param = c, p
        break

machine_info = _extract_machine_info(cond)
polymer_info = _extract_polymer_info(cond)
mold_info = _extract_mold_info(cond)
baseline = _snapshot_parameter(param)

poly_abbr = getattr(cond.polymer, "abbreviation", None)
prod_cat = getattr(cond.mold, "product_category", None)
defect_kw = RuleKeyword.objects.filter(category="defect").exclude(
    keyword_name="DEFECTFREE").first()
defect_name = defect_kw.keyword_name

feedback = {"defect": [{"keyword_id": None, "keyword_name": defect_name,
                        "level": "low", "position": "DL1"}],
            "observations": [], "tuning_result": None}

ctx = _compose_algorithm_context(
    machine_info=machine_info, polymer_info=polymer_info,
    mold_info=mold_info, parameter=baseline, feedback=feedback,
)
x = ctx["process_parameter"]

hr("[1] 规则与论域")
rules = RuleQueryService.get_rules(RuleQueryContext(
    defect_name=defect_name, defect_level="low", defect_position=None,
    polymer_abbreviation=poly_abbr, product_category=prod_cat,
    rule_library_code=None,
))
split = RuleQueryService.split_by_conclusion_kind(rules)
numeric = split["numeric"]
print(f"命中 {len(rules)} 条，numeric={len(numeric)} advisory={len(split['advisory'])}")

engine = FuzzyEngine()
param_names = engine._collect_keyword_names(numeric)
keyword_dicts = engine._load_keyword_dicts(param_names, x)
print(f"\nkeyword 论域（keyword, lvl, min, max, step）与当前值:")
for kd in keyword_dicts:
    k = kd["keyword"]
    print(f"   {k:<10} lvl={kd['lvl']} range=[{kd['min_val']}, {kd['max_val']}] "
          f"step={kd['step']:.3f}  当前值={x.get(k)}")

rule_array = RuleQueryService.to_rule_array(numeric)
priority_array = RuleQueryService.get_priority_array(numeric)
net = NumTskRuleNet(rule_array, keyword_dicts, priority_array)

hr("[2] 逐层拆解")
# --- 隶属度层 ---
num_degrees = net.connected_matrix.shape[1]
membership_degrees = np.zeros(shape=(num_degrees,)) + 0.01
for k in x:
    if not net.pre_dict.get(k):
        continue
    idx, f_k = net.pre_dict[k]["index"], net.pre_dict[k]["memberships"]
    for i in range(f_k.f_level):
        membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)

print("\n[2.1] 各参数的 5 档隶属度（当前值落在哪档一目了然）:")
for kd in keyword_dicts:
    k = kd["keyword"]
    if not net.pre_dict.get(k):
        continue
    idx = net.pre_dict[k]["index"]
    vals = membership_degrees[idx: idx + kd["lvl"]]
    print(f"   {k:<10} 当前值={x.get(k)!s:<8} 隶属度={np.round(vals, 5).tolist()}")

# --- 规则层 ---
rule_matrix = net.connected_matrix * membership_degrees
rule_activations = np.zeros(shape=(rule_matrix.shape[0],))
for i in range(net.rule_nums):
    conditions = rule_matrix[i, rule_matrix[i] != 0]
    if conditions.size != 0:
        rule_activations[i] = np.prod(conditions)

# --- 归一化 + priority ---
activations_sum = np.sum(rule_activations)
new_activations = rule_activations / max(activations_sum, 1e-10)
activations_with_priority = new_activations * np.asarray(priority_array)

print(f"\n[2.2] 规则激活度（原始 / 归一化 / priority加权 / 结论delta / 贡献）:")
print(f"   归一化分母 Σ激活度 = {activations_sum:.8f}")
print()
print(f"   {'规则':<52} {'原始激活':>10} {'归一化':>10} {'加权':>10} {'delta':>8} {'贡献':>10}")
total_contrib = {}
for i in range(net.rule_nums):
    rule_str = net.rule_dict[i].r_rule
    darray = net.solution_matrix[i, :]
    sol = {}
    for j in range(len(darray)):
        if darray[j] != 0:
            for k, v in net.sol_dict.items():
                if j == v["index"]:
                    sol[k] = darray[j]
    delta_txt = ",".join(f"{k}:{v:+.2f}" for k, v in sol.items())
    contrib = {k: v * activations_with_priority[i] for k, v in sol.items()}
    for k, v in contrib.items():
        total_contrib[k] = total_contrib.get(k, 0.0) + v
    print(f"   {rule_str[:50]:<52} {rule_activations[i]:>10.6f} "
          f"{new_activations[i]:>10.6f} {activations_with_priority[i]:>10.6f} "
          f"{delta_txt:>8} {str({k: round(v, 4) for k, v in contrib.items()}):>10}")

hr("[3] 每个参数的最终 delta（= 引擎实际推出的调整量）")
for k, v in sorted(total_contrib.items(), key=lambda kv: -abs(kv[1])):
    cur = x.get(k)
    print(f"   {k:<10} 规则原始delta合计={v:+.6f}   当前值={cur}   → {cur + v if cur is not None else '?'}")

print()
print("=" * 78)
print("诊断结束")
print("=" * 78)
