"""诊断：模糊推理链路在哪一环断掉（2026-10-22）

目的：用户反馈"算法部分还没跑通"。本脚本用**真实 DB 数据**逐环节走一遍
模糊推理链路，定位断点，而不是靠静态阅读猜。

检查项：
  1. 规则库数据量（RuleMethod / RuleKeyword）
  2. 规则前件形态抽样（前件里有哪些 keyword、哪些 level）
  3. RuleKeyword 论域完整性（min_val/max_val 是否齐）
  4. 真实 condition 抽样（polymer / mold 是否能拿到 abbreviation / product_category）
  5. RuleQueryService 能否查到规则
  6. 论域能否建起来（_load_keyword_dicts）
  7. NumTskRuleNet 能否算出结果

运行：cd backend; $env:PYTHONPATH="."; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_pipeline.py
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from collections import Counter

from process.models.rules import RuleKeyword, RuleMethod
from process.models import ProcessCondition, ProcessParameter
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule
from process.algorithms.fuzzy.services.rule_query_service import (
    RuleQueryContext,
    RuleQueryService,
)
from process.algorithms.fuzzy.fuzzy_core.macros import HS_MAPPING_DICT, DEFECT_CONST


def hr(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ---------------------------------------------------------------- 1. 数据量
hr("[1] 规则库数据量")
print(f"RuleMethod   total = {RuleMethod.objects.count()}")
print(f"RuleKeyword  total = {RuleKeyword.objects.count()}")
by_cat = Counter(RuleKeyword.objects.values_list("category", flat=True))
print(f"RuleKeyword  by category = {dict(by_cat)}")
by_src = Counter(RuleMethod.objects.values_list("source", flat=True))
print(f"RuleMethod   by source = {dict(by_src)}")
active = RuleMethod.objects.filter(is_active=True).count()
print(f"RuleMethod   is_active=True = {active}")
print("RuleMethod 字段 = " + ", ".join(
    f.name for f in RuleMethod._meta.fields
))
print("RuleKeyword 字段 = " + ", ".join(
    f.name for f in RuleKeyword._meta.fields
))

# ------------------------------------------------------- 2. 规则前件形态抽样
hr("[2] 规则前件形态抽样（前 5 条）")
sample = list(RuleMethod.objects.all()[:5])
for rm in sample:
    desc = rm.rule_description or ""
    print(f"  - id={rm.id} src={rm.source} defect={rm.defect_code} "
          f"poly={rm.polymer_abbreviation} cat={rm.product_category} desc={desc[:80]!r}")

# 统计全部规则的前件 keyword / level 用法
pre_keywords = Counter()
pre_levels = Counter()
conclusion_actions = Counter()
pos_pre_count = 0
parse_fail = 0
for rm in RuleMethod.objects.all().iterator():
    desc = rm.rule_description or ""
    try:
        parsed = parse_rule(desc)
    except Exception:
        parse_fail += 1
        continue
    for pre in parsed.get("preconditions", []) or []:
        name = pre.get("name")
        pre_keywords[name] += 1
        pre_levels[pre.get("level")] += 1
        if name and str(name).upper().startswith("DL"):
            pos_pre_count += 1
    for sol in parsed.get("solutions", []) or []:
        conclusion_actions[sol.get("action")] += 1

print(f"\nparse 失败条数 = {parse_fail}")
print(f"前件含 DL*（缺陷位置）的规则数 = {pos_pre_count}")
print(f"\n前件 level 取值分布（top 20）:")
for lv, n in pre_levels.most_common(20):
    in_map = "OK(在HS_MAPPING_DICT)" if lv in HS_MAPPING_DICT else "MISS(->KeyError)"
    print(f"   {str(lv):<16} {n:>6}   {in_map}")
print(f"\n结论 action 分布 = {dict(conclusion_actions)}")
print(f"\n前件 keyword top 15 = {dict(pre_keywords.most_common(15))}")

# --------------------------------------------------- 3. RuleKeyword 论域完整性
hr("[3] RuleKeyword 论域完整性")
total = RuleKeyword.objects.count()
no_min = RuleKeyword.objects.filter(range_min__isnull=True).count()
no_max = RuleKeyword.objects.filter(range_max__isnull=True).count()
print(f"range_min 为空 = {no_min}/{total}")
print(f"range_max 为空 = {no_max}/{total}")
print("\n样例（defect 类）:")
for kw in RuleKeyword.objects.filter(category="defect")[:5]:
    print(f"   {kw.keyword_name:<20} lvl={kw.fuzzy_level} "
          f"range=[{kw.range_min}, {kw.range_max}] step={kw.step} type={kw.keyword_type}")

# ------------------------------------------------- 4. 真实 condition 抽样
hr("[4] 真实 condition 抽样")
conds = (
    ProcessCondition.objects
    .select_related("polymer", "mold", "injection_machine")
    .all()[:5]
)
for c in conds:
    poly = c.polymer
    mold = c.mold
    print(f"  - condition id={c.id}")
    print(f"      polymer={getattr(poly, 'abbreviation', None)!r} mold={getattr(mold, 'product_category', None)!r}"
          f" machine={c.injection_machine_id}")
params = ProcessParameter.objects.count()
print(f"\nProcessParameter total = {params}")

# --------------------------------------------- 5. RuleQueryService 查规则
hr("[5] RuleQueryService 查规则（逐条件放宽）")
# 取一个真实存在的缺陷 keyword
defect_kw = RuleKeyword.objects.filter(category="defect").exclude(
    keyword_name="DEFECTFREE"
).first()
if defect_kw is None:
    print("!! 没有 defect 类 keyword，无法继续")
    sys.exit(1)
print(f"用 defect keyword: {defect_kw.keyword_name}")

# 取真实 polymer / mold
real_poly = None
real_cat = None
for c in ProcessCondition.objects.select_related("polymer", "mold").all():
    if c.polymer and getattr(c.polymer, "abbreviation", None):
        real_poly = c.polymer.abbreviation
    if c.mold and getattr(c.mold, "product_category", None):
        real_cat = c.mold.product_category
    if real_poly and real_cat:
        break
print(f"真实 polymer.abbreviation = {real_poly!r}")
print(f"真实 mold.product_category = {real_cat!r}")

levels = [None, "low", "medium", "high"]
for lv in levels:
    qc = RuleQueryContext(
        defect_name=defect_kw.keyword_name,
        defect_level=lv,
        defect_position=None,
        polymer_abbreviation=real_poly,
        product_category=real_cat,
        rule_library_code=None,
    )
    try:
        rules = RuleQueryService.get_rules(qc)
        print(f"  defect_level={str(lv):<8} → {len(rules)} 条")
    except Exception as e:
        print(f"  defect_level={str(lv):<8} → 异常 {type(e).__name__}: {e}")

# 再看纯 defect 过滤（不带 polymer/category）
for lv in levels:
    qc = RuleQueryContext(
        defect_name=defect_kw.keyword_name,
        defect_level=lv,
        defect_position=None,
        polymer_abbreviation=None,
        product_category=None,
        rule_library_code=None,
    )
    try:
        rules = RuleQueryService.get_rules(qc)
        print(f"  [仅 defect] level={str(lv):<8} → {len(rules)} 条")
    except Exception as e:
        print(f"  [仅 defect] level={str(lv):<8} → 异常 {type(e).__name__}: {e}")

# --------------------------------------------- 6/7. 论域 + NumTskRuleNet
hr("[6/7] 论域构建 + NumTskRuleNet 推理")
qc = RuleQueryContext(
    defect_name=defect_kw.keyword_name,
    defect_level="high",
    defect_position=None,
    polymer_abbreviation=None,
    product_category=None,
    rule_library_code=None,
)
rules = RuleQueryService.get_rules(qc)
print(f"命中规则 {len(rules)} 条")
if rules:
    split = RuleQueryService.split_by_conclusion_kind(rules)
    print(f"  numeric={len(split['numeric'])}  advisory={len(split['advisory'])}")
    for r in split["numeric"][:3]:
        print(f"    numeric rule: {getattr(r, 'rule_description', r)!r}")

    from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine
    from process.algorithms.fuzzy.fuzzy_core.parsing import (
        classify_name, is_level_word, parse_rule,
    )
    engine = FuzzyEngine()
    param_names = engine._collect_keyword_names(split["numeric"])
    print(f"\n  涉及 keyword {len(param_names)} 个: {sorted(param_names)[:10]}")

    # ---- 每个前件的门控状态 ----
    print("\n  === 前件门控分析（每条规则的前件能不能当门控）===")
    gate_summary = Counter()
    for r in split["numeric"]:
        parsed = parse_rule(r.rule_str)
        for pre in parsed.get("preconditions", []) or []:
            name, lv = pre.get("name"), pre.get("level")
            in_pre_dict = name in param_names
            judgable = is_level_word(lv)
            if not judgable:
                status = "SKIP(level非档位词)"
            elif not in_pre_dict:
                status = "SKIP(非参数名/无论域)"
            else:
                status = "GATE(有效门控)"
            gate_summary[status] += 1
            print(f"    {r.rule_str[:62]:<62} | {name}_{lv} -> {status}")

    print(f"\n  门控状态汇总: {dict(gate_summary)}")

    # 取一条真实 parameter 当 process_parameter
    real_param = ProcessParameter.objects.exclude(inj_spd_1=None).first()
    if real_param is None:
        print("  !! 没有可用 parameter")
        sys.exit(0)
    from process.services.parameter_optimize import _to_full_dict
    process_parameter = {
        k: v for k, v in _to_full_dict(real_param).items()
        if v is not None and isinstance(v, (int, float))
    }
    print(f"  process_parameter 数值项 {len(process_parameter)} 个")

    try:
        keyword_dicts = engine._load_keyword_dicts(param_names, process_parameter)
        print(f"  论域构建成功：{len(keyword_dicts)} 个")
        for kd in keyword_dicts[:5]:
            print(f"     {kd}")
    except Exception as e:
        import traceback
        print(f"  !! 论域构建异常: {type(e).__name__}: {e}")
        traceback.print_exc()

    try:
        rule_array = RuleQueryService.to_rule_array(split["numeric"])
        priority_array = RuleQueryService.get_priority_array(split["numeric"])
        print(f"  rule_array={len(rule_array)} priority_array={len(priority_array)}")
    except Exception as e:
        import traceback
        print(f"  !! to_rule_array 异常: {type(e).__name__}: {e}")
        traceback.print_exc()
        rule_array = None

    # ---- 真实跑一次 NumTskRuleNet.predict ----
    if rule_array:
        from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet
        try:
            net = NumTskRuleNet(rule_array, keyword_dicts, priority_array)
            results, extra = net.predict(process_parameter, top_k=len(split["numeric"]))
            print(f"\n  === predict 结果：{len(results)} 条 ===")
            for rule_str, act, adjustments in results[:12]:
                print(f"    activation={act:.6f}  {rule_str[:60]:<60} -> {adjustments}")
            if not results:
                print("    (空)")
        except Exception as e:
            import traceback
            print(f"  !! NumTskRuleNet.predict 异常: {type(e).__name__}: {e}")
            traceback.print_exc()

    # ---- 走引擎的完整 recommend（看最终产出） ----
    print("\n  === FuzzyEngine.recommend 端到端 ===")
    try:
        ctx = {
            "feedback": {"defect": [{"keyword_name": defect_kw.keyword_name, "level": "high", "position": "DL1"}]},
            "process_parameter": process_parameter,
            "machine_info": {},
            "polymer_info": {},
            "mold_info": {},
        }
        recs = engine.recommend(ctx)
        print(f"    产出 {len(recs)} 条推荐:")
        for r in recs[:10]:
            print(f"      {r}")
    except Exception as e:
        import traceback
        print(f"  !! recommend 异常: {type(e).__name__}: {e}")
        traceback.print_exc()

print()
print("=" * 72)
print("诊断结束")
print("=" * 72)
