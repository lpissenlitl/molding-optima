"""FieldRegistry 改造的零行为变化回归。

对比【改造前】与【改造后】两条路径：

  旧：_collect_keyword_names -> _load_keyword_dicts              -> 送引擎
  新：_build_field_registry -> registry.keyword_dicts             -> 送引擎

检查三件事：
  M1  论域清单内容是否逐项一致（忽略新增的 source 标记）
  M2  论域清单顺序是否一致（权威项应完全一致；兜底项旧路径是 set 顺序，可能不同）
  M3  NumTskRuleNet.predict 的推理结果是否一致

运行：../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_field_registry_regression.py
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.models import ProcessCondition, ProcessParameter  # noqa: E402
from process.models.rules import RuleKeyword, RuleMethod  # noqa: E402
from process.services.parameter_optimize import _to_full_dict  # noqa: E402
from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet  # noqa: E402
from process.algorithms.fuzzy.services.rule_query_service import (  # noqa: E402
    RuleQueryContext,
    RuleQueryService,
)


def _norm(items):
    """去掉 source 标记（它是本次新增的），其余逐字保留。"""
    return [{k: v for k, v in d.items() if k != 'source'} for d in items]


def _by_name(items):
    return {d['keyword']: d for d in items}


def main():
    print("=" * 74)
    print("FieldRegistry 零行为变化回归")
    print("=" *74)

    defect_kw = RuleKeyword.objects.filter(category="defect").exclude(
        keyword_name="DEFECTFREE"
    ).first()
    if defect_kw is None:
        print("!! 没有 defect 类 keyword")
        return 1
    real_poly = real_cat = None
    for c in ProcessCondition.objects.select_related("polymer", "mold").all():
        if c.polymer and getattr(c.polymer, "abbreviation", None):
            real_poly = c.polymer.abbreviation
        if c.mold and getattr(c.mold, "product_category", None):
            real_cat = c.mold.product_category
        if real_poly and real_cat:
            break

    qc = RuleQueryContext(
        defect_name=defect_kw.keyword_name,
        defect_level="high",
        defect_position=None,
        polymer_abbreviation=real_poly,
        product_category=real_cat,
        rule_library_code=None,
    )
    rules = RuleQueryService.get_rules(qc)
    if not rules:
        print("!! 没有命中规则")
        return 1
    split = RuleQueryService.split_by_conclusion_kind(rules)
    numeric = split['numeric']
    print(f"\n规则 {len(rules)} 条 -> numeric {len(numeric)} / advisory {len(split['advisory'])}")

    real_param = ProcessParameter.objects.exclude(inj_spd_1=None).first()
    if real_param is None:
        print("!! 没有可用 parameter")
        return 1
    process_parameter = {
        k: v for k, v in _to_full_dict(real_param).items()
        if v is not None and isinstance(v, (int, float))
    }
    print(f"process_parameter 数值项 {len(process_parameter)} 个")

    engine = FuzzyEngine()

    # ---- 旧路径 ----
    param_names = engine._collect_keyword_names(numeric)
    old_kw = engine._load_keyword_dicts(param_names, process_parameter)

    # ---- 新路径 ----
    registry_kw, _cls = engine._build_field_context(
        numeric, process_parameter, 'numeric')
    new_kw = registry_kw

    print(f"\n旧路径论域清单: {len(old_kw)} 个")
    print(f"新路径论域清单: {len(new_kw)} 个")

    # ---- M1 内容逐项一致 ----
    old_map = _by_name(_norm(old_kw))
    new_map = _by_name(_norm(new_kw))
    only_old = sorted(set(old_map) - set(new_map))
    only_new = sorted(set(new_map) - set(old_map))
    diff = {
        k: (old_map[k], new_map[k]) for k in set(old_map) & set(new_map)
        if old_map[k] != new_map[k]
    }
    print("\n[M1] 论域清单内容对照")
    print(f"  仅旧路径有: {only_old}")
    print(f"  仅新路径有: {only_new}")
    print(f"  内容不同  : {len(diff)} 个 -> {list(diff)[:5]}")
    m1_ok = not only_old and not only_new and not diff

    # ---- M2 顺序 ----
    old_names = [d['keyword'] for d in old_kw]
    new_names = [d['keyword'] for d in new_kw]
    same_order = old_names == new_names
    print("\n[M2] 论域清单顺序对照")
    print(f"  完全一致  : {same_order}")
    if not same_order:
        first_diff = next(
            (i for i, (a, b) in enumerate(zip(old_names, new_names)) if a != b), None
        )
        print(f"  首个差异位: {first_diff}")
        print(f"    旧: {old_names[max(0, (first_diff or 0) - 2):(first_diff or 0) + 3]}")
        print(f"    新: {new_names[max(0, (first_diff or 0) - 2):(first_diff or 0) + 3]}")
        # 权威项顺序是否一致（权威项在前，顺序应完全相同）
        auth_old = [n for n in old_names if n in {d['keyword'] for d in old_kw
                                                 if d.get('source') != 'guessed'}]
        auth_new = [n for n in new_names if n in {d['keyword'] for d in new_kw
                                                 if d.get('source') != 'guessed'}]
        print(f"  权威项顺序一致: {auth_old == auth_new}")

    # ---- M3 推理结果 ----
    print("\n[M3] NumTskRuleNet.predict 结果对照")
    rule_array = RuleQueryService.to_rule_array(numeric)
    priority_array = RuleQueryService.get_priority_array(numeric)

    def run(kw):
        net = NumTskRuleNet(rule_array, kw, priority_array)
        # predict 返回 (results, extra)
        res, extra = net.predict(process_parameter, top_k=len(numeric))
        return res

    try:
        old_res = run(old_kw)
    except Exception as e:
        print(f"  旧路径推理异常: {type(e).__name__}: {e}")
        old_res = None
    try:
        new_res = run(new_kw)
    except Exception as e:
        print(f"  新路径推理异常: {type(e).__name__}: {e}")
        new_res = None

    m3_ok = False
    if old_res is not None and new_res is not None:
        print(f"  旧结果条数: {len(old_res)}    新结果条数: {len(new_res)}")
        if old_res:
            print(f"  结果样例结构: {old_res[0]!r}"[:200])
        # 直接比对完整结构（不假设元组布局）
        old_map_r = {r[0]: r[1:] for r in old_res}
        new_map_r = {r[0]: r[1:] for r in new_res}
        only_o = sorted(set(old_map_r) - set(new_map_r))
        only_n = sorted(set(new_map_r) - set(old_map_r))
        rdiff = {
            k: (old_map_r[k], new_map_r[k]) for k in set(old_map_r) & set(new_map_r)
            if old_map_r[k] != new_map_r[k]
        }
        print(f"  仅旧路径有: {len(only_o)} 条")
        print(f"  仅新路径有: {len(only_n)} 条")
        print(f"  内容不同  : {len(rdiff)} 条")
        for k in list(rdiff)[:3]:
            print(f"    {k}:\n      旧={rdiff[k][0]}\n      新={rdiff[k][1]}")
        m3_ok = not only_o and not only_n and not rdiff

    # ---- 定性分布 ----
    report = registry.report()
    print("\n[定性分布]")
    for status in ('authority', 'excluded', 'guessed', 'unknown'):
        names = [x['name'] for x in report[status]]
        print(f"  {status:<10} {len(names):>3} 个  {names[:8]}")

    print("\n" + "=" * 74)
    print(f"M1 论域内容一致 : {'PASS' if m1_ok else 'FAIL'}")
    print(f"M2 清单顺序一致 : {'PASS' if same_order else 'DIFF (仅兜底项顺序可能不同)'}")
    print(f"M3 推理结果一致 : {'PASS' if m3_ok else 'FAIL'}")
    print("=" * 74)

    # ================= 场景 B：全量规则 =================
    print("\n" + "=" * 74)
    print("场景 B：全量规则（覆盖更多字段，能看到 guessed / unknown）")
    print("=" * 74)

    class _FakeRule:
        """最小 ResolvedRule 替身（只需 rule_str）。"""

        def __init__(self, s):
            self.rule_str = s

    all_desc = list(RuleMethod.objects.filter(is_deleted=False)
                    .values_list('rule_description', flat=True))
    num_desc = [d for d in all_desc if '_add_' in d or '_reduce_' in d]
    print(f"全量规则 {len(all_desc)} 条 -> 含数值结论 {len(num_desc)} 条")

    fake_rules = [_FakeRule(d) for d in num_desc]

    old_b = engine._load_keyword_dicts(
        engine._collect_keyword_names(fake_rules), process_parameter)
    new_b, cls_b = engine._build_field_context(
        fake_rules, process_parameter, 'numeric')

    old_map_b = _by_name(_norm(old_b))
    new_map_b = _by_name(_norm(new_b))
    only_o = sorted(set(old_map_b) - set(new_map_b))
    only_n = sorted(set(new_map_b) - set(old_map_b))
    diff_b = {k: (old_map_b[k], new_map_b[k]) for k in set(old_map_b) & set(new_map_b)
              if old_map_b[k] != new_map_b[k]}
    print(f"\n论域清单  旧 {len(old_b)} / 新 {len(new_b)}")
    print(f"  仅旧有  : {only_o}")
    print(f"  仅新有  : {only_n}")
    print(f"  内容不同: {len(diff_b)}")
    b_m1 = not only_o and not only_n and not diff_b
    b_order = [d['keyword'] for d in old_b] == [d['keyword'] for d in new_b]
    print(f"  顺序一致: {b_order}")

    rb = [{'rule_description': d} for d in num_desc]
    pb = [1.0] * len(num_desc)

    def run_b(kw):
        net = NumTskRuleNet(rb, kw, pb)
        res, _extra = net.predict(process_parameter, top_k=len(num_desc))
        return res

    o_res, n_res = run_b(old_b), run_b(new_b)
    o_m = {r[0]: r[1:] for r in o_res}
    n_m = {r[0]: r[1:] for r in n_res}
    rdiff_b = {k: (o_m[k], n_m[k]) for k in set(o_m) & set(n_m) if o_m[k] != n_m[k]}
    print(f"\n推理结果  旧 {len(o_res)} 条 / 新 {len(n_res)} 条")
    print(f"  仅旧有  : {len(set(o_m) - set(n_m))} 条")
    print(f"  仅新有  : {len(set(n_m) - set(o_m))} 条")
    print(f"  内容不同: {len(rdiff_b)} 条")
    b_m3 = not (set(o_m) ^ set(n_m)) and not rdiff_b

    rep_b = cls_b
    print("\n[定性分布 - 全量]")
    for status in ('authority', 'guessed', 'unknown'):
        names = rep_b[status]
        print(f"  {status:<10} {len(names):>3} 个  {names[:10]}")

    print("\n" + "=" * 74)
    print(f"场景 B  M1 论域内容一致: {'PASS' if b_m1 else 'FAIL'}")
    print(f"场景 B  M2 清单顺序一致: {'PASS' if b_order else 'DIFF'}")
    print(f"场景 B  M3 推理结果一致: {'PASS' if b_m3 else 'FAIL'}")
    print("=" * 74)
    return 0 if (m1_ok and m3_ok and b_m1 and b_m3) else 1


if __name__ == '__main__':
    sys.exit(main())
