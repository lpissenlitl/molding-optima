"""接线前 vs 接线后：真实引擎跑两遍的推荐差异（2026-10-23）

只读脚本：不写库、不改产品代码。

背景：
    第一刀把 `nets.py` 的档位取桶从全局静态 3 档表 `HS_MAPPING_DICT[level]`
    换成 `resolve_bucket(lvl, word)`（按字段自己的档位词表定位）。
    之前的量化（`diag_fuzzy_bucket_shift_impact.py`）是**复刻激活度公式**算的，
    属于推算；本脚本用**真实引擎跑两遍**，给出业务口径的权威对比。

做法：
    1. 走真实 service 路径构造 `AlgorithmContext`（命名翻译 / 规则查询 / 缺陷筛选）
    2. monkeypatch `nets.resolve_bucket` 为旧口径 → 跑 `_call_algorithms` = 接线前
    3. 恢复真实 `resolve_bucket` → 再跑一次 = 接线后
       （`_resolve_bucket_safe` 在 nets 模块内按全局名查 `resolve_bucket`，替换即生效）
    4. 逐样本对比：推荐条数 / 参数集合 / 每个参数的 delta / 排序

运行：
    cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_bucket_before_after.py
    cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_bucket_before_after.py --limit 5
"""

import argparse
import collections
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='gbk', errors='replace')
except Exception:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

# ⚠️ sys.path 必须在 django.setup() 之前就位（否则 `_moldx` / `process` 找不到）
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
for _p in (_BACKEND, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import django  # noqa: E402

django.setup()

from process.algorithms.fuzzy.fuzzy_core.models import nets  # noqa: E402
from process.algorithms.fuzzy.services.rule_query_service import (  # noqa: E402
    RuleQueryContext,
    RuleQueryService,
)
from process.models import ProcessCondition, ProcessParameter  # noqa: E402
from process.models.rules import RuleKeyword  # noqa: E402
from process.services.parameter_optimize import (  # noqa: E402
    _call_algorithms,
    _compose_algorithm_context,
    _extract_machine_info,
    _extract_mold_info,
    _extract_polymer_info,
    _snapshot_parameter,
)

from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT  # noqa: E402


# 真实实现（接线后），monkeypatch 时暂存、恢复
REAL_RESOLVE = nets.resolve_bucket


def legacy_resolve(lvl, word, field_words=None):
    """旧口径：全局静态 3 档表（接线前 `nets.py` 实际走的路）。

    表里没有的词（旧表不含 very_low 等多段词）走真实实现兜底，
    保证对照实验不会因 KeyError 中断；统计里单独计数。
    """
    w = str(word or '').strip().lower()
    if w in LEGACY_HS_MAPPING_DICT:
        return LEGACY_HS_MAPPING_DICT[w]
    return REAL_RESOLVE(lvl, word, field_words)


def hr(title):
    print()
    print('=' * 100)
    print(title)
    print('=' * 100)


# ---------------------------------------------------------------- 样本准备

def pick_condition():
    """找一个带 polymer / mold / parameter 的真实 condition。"""
    for c in (
        ProcessCondition.objects
        .select_related('polymer', 'mold', 'injection_machine')
        .order_by('id')
    ):
        if not c.polymer or not c.mold:
            continue
        p = (
            ProcessParameter.objects
            .filter(process_condition=c)
            .order_by('-seq_idx')
            .first()
        )
        if p is None:
            continue
        return c, p
    return None, None


def pick_defect(cond):
    """选一个在该 polymer / product_category 下真有规则的缺陷词。"""
    poly_abbr = getattr(cond.polymer, 'abbreviation', None)
    prod_cat = getattr(cond.mold, 'product_category', None)

    for kw in RuleKeyword.objects.filter(category='defect').exclude(
        keyword_name='DEFECTFREE'
    ):
        for lv in ('high', 'medium', 'low'):
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
                return kw.keyword_name, lv, len(rules)
    return None, None, 0


# ---------------------------------------------------------------- 对比主体

def run_both(ctx):
    """同一 context 跑两遍：接线前（legacy 映射）/ 接线后（真实映射）。"""
    nets.resolve_bucket = legacy_resolve
    try:
        before = _call_algorithms(ctx)
    finally:
        nets.resolve_bucket = REAL_RESOLVE
    after = _call_algorithms(ctx)
    return before, after


def rec_map(result):
    """推荐列表 → {参数名: Recommendation dict}。

    ⚠️ Recommendation 的字段是 param_name / current_value / recommended_value /
    confidence / reason / source / direction —— **没有 delta 字段**，
    调整量体现在 recommended_value = current_value + 累加后的 delta。
    """
    out = {}
    for r in result.get('recommendations') or []:
        out[r.get('param')] = r
    return out


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='限制样本数（0=全部）')
    ap.add_argument('--json', default='', help='把逐样本明细写到该 JSON 文件')
    args = ap.parse_args()

    hr('0. 接线前后对照：真实引擎跑两遍')
    cond, param = pick_condition()
    if cond is None:
        print('!! 找不到带 parameter 的 condition')
        return 1
    defect_name, defect_level, n_rules = pick_defect(cond)
    if defect_name is None:
        print('!! 找不到可用缺陷词')
        return 1

    print(f'condition id={cond.id}  parameter id={param.id}')
    print(f'defect={defect_name} level={defect_level}（该组合命中 {n_rules} 条规则）')

    machine_info = _extract_machine_info(cond)
    polymer_info = _extract_polymer_info(cond)
    mold_info = _extract_mold_info(cond)

    params = list(
        ProcessParameter.objects.all().order_by('id')
    )
    if args.limit:
        params = params[:args.limit]
    print(f'样本（ProcessParameter）数 = {len(params)}')

    feedback = {
        'defect': [
            {'keyword_id': None, 'keyword_name': defect_name,
             'level': defect_level, 'position': 'DL1'},
        ],
        'observations': [],
        'tuning_result': None,
    }

    # ---------------------------------------------------------- 逐样本跑两遍
    details = []
    stat = collections.Counter()
    param_appear = collections.Counter()     # 参数：接线前命中数 / 接线后命中数
    delta_rows = []
    errors = 0

    for i, pp in enumerate(params, 1):
        baseline = _snapshot_parameter(pp)
        if not baseline:
            continue
        ctx = _compose_algorithm_context(
            machine_info=machine_info,
            polymer_info=polymer_info,
            mold_info=mold_info,
            parameter=baseline,
            feedback=feedback,
        )
        try:
            before, after = run_both(ctx)
        except Exception as e:  # noqa: BLE001
            errors += 1
            print(f'  [样本 {i}] 异常：{type(e).__name__}: {e}')
            continue

        b_recs = before.get('recommendations') or []
        a_recs = after.get('recommendations') or []
        b_map, a_map = rec_map(before), rec_map(after)

        b_params = [r.get('param') for r in b_recs]
        a_params = [r.get('param') for r in a_recs]

        only_before = [p for p in b_params if p not in a_map]
        only_after = [p for p in a_params if p not in b_map]
        both = [p for p in b_params if p in a_map]
        changed_delta = []
        for p in both:
            bv = _num(a_map[p].get('recommended_value'))
            av = _num(b_map[p].get('recommended_value'))
            bc = _num(a_map[p].get('confidence'))
            ac = _num(b_map[p].get('confidence'))
            if (bv is not None and av is not None
                    and abs(bv - av) > 1e-9) or (bc is not None and ac is not None
                                                 and abs(bc - ac) > 1e-9):
                changed_delta.append(p)

        stat['samples'] += 1
        stat['err'] += errors
        if len(b_recs) != len(a_recs):
            stat['count_changed'] += 1
        if set(b_params) != set(a_params):
            stat['set_changed'] += 1
        if b_params != a_params:
            stat['order_changed'] += 1
        if changed_delta:
            stat['delta_changed'] += 1
        if not b_recs and not a_recs:
            stat['both_empty'] += 1
        if b_recs and not a_recs:
            stat['lost_all'] += 1
        if not b_recs and a_recs:
            stat['gained_all'] += 1

        for p in b_params:
            param_appear[(p, 'before')] += 1
        for p in a_params:
            param_appear[(p, 'after')] += 1

        for p in changed_delta:
            delta_rows.append({
                'param': p,
                'before': b_map[p],
                'after': a_map[p],
            })

        details.append({
            'parameter_id': pp.id,
            'before_count': len(b_recs),
            'after_count': len(a_recs),
            'before_params': b_params,
            'after_params': a_params,
            'only_before': only_before,
            'only_after': only_after,
            'before_head': b_recs[:8],
            'after_head': a_recs[:8],
            'changed_delta': {
                p: {
                    'before_value': b_map[p].get('recommended_value'),
                    'after_value': a_map[p].get('recommended_value'),
                    'before_conf': b_map[p].get('confidence'),
                    'after_conf': a_map[p].get('confidence'),
                } for p in changed_delta
            },
        })

    # ---------------------------------------------------------- 聚合输出
    hr('1. 聚合结果（接线前 = 旧静态表 / 接线后 = resolve_bucket）')
    print(f'  成功样本数              : {stat["samples"]}')
    print(f'  异常样本数              : {errors}')
    print(f'  两边都无推荐            : {stat["both_empty"]}')
    print(f'  推荐条数变化            : {stat["count_changed"]} '
          f'({stat["count_changed"] * 100 // max(stat["samples"], 1)}%)')
    print(f'  推荐参数集合变化        : {stat["set_changed"]} '
          f'({stat["set_changed"] * 100 // max(stat["samples"], 1)}%)')
    print(f'  推荐排序变化            : {stat["order_changed"]} '
          f'({stat["order_changed"] * 100 // max(stat["samples"], 1)}%)')
    print(f'  同一参数推荐值/置信度变化: {stat["delta_changed"]} '
          f'({stat["delta_changed"] * 100 // max(stat["samples"], 1)}%)')
    print(f'  接线前有、接线后全没了  : {stat["lost_all"]}')
    print(f'  接线前没有、接线后有    : {stat["gained_all"]}')

    hr('2. 参数级：只在一侧出现的参数（按出现次数）')
    only_b = collections.Counter()
    only_a = collections.Counter()
    for d in details:
        for p in d['only_before']:
            only_b[p] += 1
        for p in d['only_after']:
            only_a[p] += 1
    print('  【仅接线前出现】(旧口径多推的，5 档字段上 high 被当成 medium ⇒ 门槛偏松)')
    for p, c in only_b.most_common(15):
        print(f'    {p:<22} {c} 个样本')
    print()
    print('  【仅接线后出现】(正确口径多推的)')
    for p, c in only_a.most_common(15):
        print(f'    {p:<22} {c} 个样本')

    hr('3. 参数级：推荐值 / 置信度发生变化的样本数')
    delta_cnt = collections.Counter()
    for r in delta_rows:
        delta_cnt[r['param']] += 1
    for p, c in delta_cnt.most_common(15):
        print(f'    {p:<22} {c} 个样本 推荐值/置信度变了')

    hr('4. 逐样本明细（前 12 个有差异的样本）')
    shown = 0
    for d in details:
        if not (d['only_before'] or d['only_after'] or d['changed_delta']):
            continue
        shown += 1
        if shown > 12:
            break
        print(f'  parameter_id={d["parameter_id"]}  '
              f'条数 {d["before_count"]} → {d["after_count"]}')
        if d['only_before']:
            print(f'    仅接线前: {d["only_before"]}')
        if d['only_after']:
            print(f'    仅接线后: {d["only_after"]}')
        for p, v in list(d['changed_delta'].items())[:6]:
            print(f'    值变化 {p}: 推荐值 {v["before_value"]} → {v["after_value"]}'
                  f'  置信 {v["before_conf"]} → {v["after_conf"]}')

    # --------------------------------------------- 原始推荐逐条对照（看激活度）
    hr('5. 原始推荐逐条对照（第一个样本，含推荐值/置信度）')
    first = details[0] if details else None
    if first:
        print(f'  parameter_id={first["parameter_id"]}')
        print('  --- 接线前（旧静态表）---')
        for r in first['before_head']:
            print(f'    cur={r.get("current_value")} rec={r.get("recommended_value")} '
                  f'conf={r.get("confidence")} dir={r.get("direction")} '
                  f'param={r.get("param")}')
            print(f'        reason={str(r.get("reason"))[:90]}')
        print('  --- 接线后（resolve_bucket）---')
        for r in first['after_head']:
            print(f'    cur={r.get("current_value")} rec={r.get("recommended_value")} '
                  f'conf={r.get("confidence")} dir={r.get("direction")} '
                  f'param={r.get("param")}')
            print(f'        reason={str(r.get("reason"))[:90]}')

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': dict(stat),
                'details': details,
            }, f, ensure_ascii=False, indent=2)
        print()
        print(f'逐样本明细已写入 {args.json}')

    print()
    print('=' * 100)
    print('对照结束（只读，未写库、未改产品代码）')
    print('=' * 100)
    return 0


if __name__ == '__main__':
    sys.exit(main())
