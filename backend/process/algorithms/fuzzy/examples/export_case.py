# -*- coding: utf-8 -*-
"""案例导出工具（开发期）—— 从生产库抽一个业务案例，固化成可离线复现的 JSON。

⚠️ **这是开发期工具，不是运行时组件**：
   它 import 了 service 层（`process.services.parameter_optimize`）来还原
   「机台 / 材料 / 模具 / 工艺参数」的真实抽取口径 ——
   算法包内的**运行时**代码不依赖 service 层（依赖方向：service → algorithm）。
   本脚本只是站在 service 那一侧取数，产出数据后即可删掉。

用法：
    cd backend
    ..\\.venv\\Scripts\\python.exe process\\algorithms\\fuzzy\\examples\\export_case.py

产出：
    process/algorithms/fuzzy/examples/cases/fuzzy_shortshot_low.json

⚠️ 导出的 rules / keywords 是**数据源原始形态**（RuleProfile 字段 / RuleKeyword
   原始元数据），**不是**裁剪后的中间态 ——
   裁剪（论域上界按设备实测值替换）发生在引擎里，离线复现时走同一条路径。
"""
import json
import os
import sys

BACKEND = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))))
sys.path.insert(0, BACKEND)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')

import django  # noqa: E402

django.setup()

from process.models.tuning_record import TuningRecord  # noqa: E402
from process.models.rules import RuleKeyword  # noqa: E402
from process.services import parameter_optimize as po  # noqa: E402
from process.algorithms.fuzzy import field_names  # noqa: E402
from process.algorithms.defect_selection import select_defect  # noqa: E402
from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.rules_filter import (  # noqa: E402
    build_rule_objects,
)
from process.algorithms.fuzzy.library.contracts import RuleQueryContext  # noqa: E402
from process.algorithms.fuzzy.library.repository import (  # noqa: E402
    ResourceRepository,
)

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_ID = 'fuzzy_shortshot_low'
OUT = os.path.join(HERE, 'cases', '%s.json' % CASE_ID)

# ProcessParameter 上不参与算法推理的字段
EXCLUDE = {
    'id', 'created_at', 'updated_at', 'is_deleted', 'deleted_at',
    'company', 'organization', 'process_condition', 'parent_param',
    'seq_idx', 'parameter_no', 'param_source',
}


def main():
    # ---------------- 1) 取真实记录 ----------------
    rec = (TuningRecord.objects.filter(is_deleted=False)
           .order_by('-id').first())
    if rec is None:
        raise SystemExit('库里没有 TuningRecord，先跑一次调优')

    out_pp = rec.process_parameter
    base_pp = out_pp.parent_param or out_pp
    cond = base_pp.process_condition

    baseline = {}
    for f in base_pp._meta.fields:
        if f.name in EXCLUDE:
            continue
        v = getattr(base_pp, f.name, None)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        baseline[f.name] = v

    machine_info = po._extract_machine_info(cond)
    polymer_info = po._extract_polymer_info(cond)
    mold_info = po._extract_mold_info(cond)

    # ---------------- 2) 组上下文 ----------------
    feedback = {'defect': rec.defect_feedbacks}
    biz_context = {
        'feedback': feedback,
        'polymer_info': polymer_info,
        'mold_info': mold_info,
        'machine_info': machine_info,
        'process_parameter': baseline,
    }
    algo_context = dict(biz_context)
    algo_context['process_parameter'] = field_names.to_algo_params(baseline)

    # ---------------- 3) 规则（生产路径取出） ----------------
    selection = select_defect(algo_context)
    query_ctx = RuleQueryContext(
        defect_name=selection.keyword_name,
        defect_level=selection.level,
        defect_position=selection.position,
        polymer_abbreviation=(polymer_info or {}).get('abbreviation'),
        product_category=(mold_info or {}).get('product_category'),
        rule_library_code=None,
    )
    profiles = ResourceRepository.get_rules(query_ctx)
    if not profiles:
        raise SystemExit('该上下文没取到规则')

    # ---------------- 4) 关键词原始元数据 ----------------
    filtered = build_rule_objects(profiles)
    kw_names = set(filtered.numeric_param_names) | set(
        filtered.defect_param_names)
    kw_rows = list(
        RuleKeyword.objects.filter(keyword_name__in=sorted(kw_names))
        .order_by('keyword_name')
    )

    # ---------------- 5) 期望输出（真跑一次生产路径） ----------------
    engine = FuzzyEngine()
    recs = engine.recommend(algo_context)

    expected_recs = []
    for r in recs:
        expected_recs.append({
            'param_name': r.param_name,
            'business_param_name': field_names.to_business_name(r.param_name),
            'current_value': r.current_value,
            'recommended_value': r.recommended_value,
            'confidence': r.confidence,
            'direction': r.direction,
            'source': r.source,
        })

    case = {
        'case_id': CASE_ID,
        'title': 'PP 包装件 · 短射(低档) · 注射/保压参数调优',
        'description': (
            '真实调优记录原样抽出的输入数据集：'
            '缺陷 SHORTSHOT/low（位置 DLSHORTSHOT1），'
            '基线工艺参数取自该轮调优的父版本。'
            '规则池是导出时刻的快照：当时未指定规则库，'
            '按当时口径只取到 base 通用库中该缺陷的规则；'
            '选库口径为「未指定 ⇒ 全量模糊库」，'
            '本案例的 rules 快照未回改（见 README「已知边界」）。'
        ),
        'source': {
            'tuning_record_id': rec.id,
            'baseline_process_parameter_id': base_pp.id,
            'optimized_process_parameter_id': out_pp.id,
            'captured_at': rec.created_at.isoformat() if rec.created_at else None,
            'note': '由 export_case.py 从生产库导出；导出后本案例可完全离线复现',
        },
        'context': biz_context,
        'rules': [
            {
                'rule_description': p.rule_description,
                'priority': p.priority,
                'conclusion_kind': p.conclusion_kind,
                'specificity': p.specificity,
                'source_ref': p.source_ref,
            }
            for p in profiles
        ],
        'keywords': [
            {
                'keyword_name': kw.keyword_name,
                'fuzzy_level': kw.fuzzy_level,
                'range_min': kw.range_min,
                'range_max': kw.range_max,
                'step': kw.step,
                'description': kw.description,
            }
            for kw in kw_rows
        ],
        'expected': {
            'recommendations': expected_recs,
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(case, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write('\n')

    print('案例已导出: %s' % OUT)
    print('  规则 %d 条 / 关键词 %d 条 / 期望建议 %d 条'
          % (len(profiles), len(kw_rows), len(expected_recs)))
    for r in expected_recs:
        print('    %-12s %s → %s  (conf=%.6f)'
              % (r['param_name'], r['current_value'],
                 r['recommended_value'], r['confidence']))


if __name__ == '__main__':
    main()
