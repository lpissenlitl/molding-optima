"""端到端诊断：走真实 service 路径跑一次 infer（2026-10-22）

与 diag_fuzzy_pipeline.py 的区别：
- diag_fuzzy_pipeline 直接调引擎，且用**业务命名**传 process_parameter（错了）
- 本脚本走 `ParameterOptimizeService.infer_from_provided` 完整链路：
  _compose_algorithm_context（命名翻译）→ _call_algorithms → 引擎
  → _normalize_recommendations → _apply_recommendations_to_baseline → suggestion

运行：cd backend; $env:PYTHONPATH="."; ../.venv/Scripts/python.exe _dev_refs/diag_infer_e2e.py
"""
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from process.models import ProcessCondition, ProcessParameter
from process.models.rules import RuleKeyword
from process.services.parameter_optimize import (
    ParameterOptimizeService,
    _extract_machine_info,
    _extract_mold_info,
    _extract_polymer_info,
    _snapshot_parameter,
)


def hr(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# --------------------------------------------------- 1. 找一个可用的 condition
hr("[1] 真实 condition + parameter")
cond = None
param = None
for c in (
    ProcessCondition.objects
    .select_related("polymer", "mold", "injection_machine")
    .order_by("id")
):
    if not c.polymer or not c.mold:
        continue
    p = (
        ProcessParameter.objects
        .filter(process_condition=c)
        .order_by("-seq_idx")
        .first()
    )
    if p is None:
        continue
    cond = c
    param = p
    break

if cond is None or param is None:
    print("!! 找不到带 parameter 的 condition")
    raise SystemExit(1)

print(f"condition id={cond.id}  parameter id={param.id} seq_idx={param.seq_idx}")
print(f"polymer={getattr(cond.polymer, 'abbreviation', None)!r} "
      f"mold.product_category={getattr(cond.mold, 'product_category', None)!r}")
print(f"machine={cond.injection_machine_id}")

machine_info = _extract_machine_info(cond)
polymer_info = _extract_polymer_info(cond)
mold_info = _extract_mold_info(cond)
print(f"\nmachine_info  ({len(machine_info)} 项): {machine_info}")
print(f"polymer_info ({len(polymer_info)} 项): {polymer_info}")
print(f"mold_info    ({len(mold_info)} 项): {mold_info}")

baseline = _snapshot_parameter(param)
print(f"\nbaseline 字段数 = {len(baseline)}")
print("  抽样:", {k: baseline[k] for k in list(baseline)[:10]})

# ------------------------------------------------- 2. 选一个真有规则的缺陷
hr("[2] 选缺陷关键词（按规则命中数排序）")
from process.algorithms.fuzzy.services.rule_query_service import (
    RuleQueryContext,
    RuleQueryService,
)

poly_abbr = getattr(cond.polymer, "abbreviation", None)
prod_cat = getattr(cond.mold, "product_category", None)

best = None
for kw in RuleKeyword.objects.filter(category="defect").exclude(
    keyword_name="DEFECTFREE"
):
    for lv in ("low", "medium", "high"):
        try:
            rules = RuleQueryService.get_rules(RuleQueryContext(
                defect_name=kw.keyword_name,
                defect_level=lv,
                defect_position=None,
                polymer_abbreviation=poly_abbr,
                product_category=prod_cat,
                rule_library_code=None,
            ))
        except Exception:
            continue
        if rules:
            best = (kw.keyword_name, lv, len(rules))
            break
    if best:
        break

if best is None:
    print("!! 该 polymer/category 下没有任何规则，退回不带过滤")
    kw0 = RuleKeyword.objects.filter(category="defect").exclude(
        keyword_name="DEFECTFREE"
    ).first()
    defect_name = kw0.keyword_name
    defect_level = "high"
    print(f"  使用 defect={defect_name} level={defect_level}")
else:
    defect_name, defect_level, n = best
    print(f"  defect={defect_name} level={defect_level} 命中 {n} 条规则")

# ------------------------------------------------------- 3. 跑真实 infer
hr("[3] ParameterOptimizeService.infer_from_provided")
feedback = {
    "defect": [
        {"keyword_id": None, "keyword_name": defect_name,
         "level": defect_level, "position": "DL1"},
    ],
    "observations": [],
    "tuning_result": None,
}

svc = ParameterOptimizeService()
try:
    result = svc.infer_from_provided(
        parameter=baseline,
        feedback=feedback,
        mold_info=mold_info,
        machine_info=machine_info,
        polymer_info=polymer_info,
    )
except Exception as e:
    print(f"!! infer_from_provided 异常: {type(e).__name__}: {e}")
    traceback.print_exc()
    raise SystemExit(2)

print("\ninfer 返回顶层键:", list(result.keys()))

new_param = result.get("new_parameter") or {}
print(f"\nnew_parameter 字段数 = {len(new_param)}")
changed = {k: (baseline.get(k), v) for k, v in new_param.items()
           if baseline.get(k) != v}
print(f"与 baseline 不同的字段 {len(changed)} 个:")
for k, (old, new) in changed.items():
    print(f"   {k:<22} {old} -> {new}")

sug = result.get("suggestion") or {}
print(f"\nsuggestion.source_type = {sug.get('source_type')}")
groups = sug.get("groups") or []
print(f"suggestion.groups = {len(groups)} 组")
for g in groups:
    print(f"  - 组 {g.get('title')!r} / {g.get('name')!r} "
          f"items={len(g.get('items') or [])}")
    for it in (g.get("items") or [])[:6]:
        print(f"      {it}")

# ------------------------------------------- 4. 直接看引擎原始推荐（未过滤）
hr("[4] 引擎原始推荐（绕过 _normalize_recommendations 的过滤）")
from process.services.parameter_optimize import (
    _compose_algorithm_context,
    _call_algorithms,
)

ctx = _compose_algorithm_context(
    machine_info=machine_info,
    polymer_info=polymer_info,
    mold_info=mold_info,
    parameter=baseline,
    feedback=feedback,
)
print("context keys =", list(ctx.keys()))
print("process_parameter 抽样 =", dict(list(ctx["process_parameter"].items())[:8]))
raw = _call_algorithms(ctx)
print(f"\nalgorithm_sources = {raw.get('algorithm_sources')}")
recs = raw.get("recommendations") or []
print(f"原始推荐 {len(recs)} 条:")
for r in recs[:15]:
    print(f"   {r}")

print()
print("=" * 72)
print("诊断结束")
print("=" * 72)
