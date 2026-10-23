"""临时验证：规则里出现 very_low（前端下拉可选词）时，后端会发生什么。只读。"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT
from process.algorithms.fuzzy.fuzzy_core.macros import (  # noqa: E402
    ALL_LEVEL_WORDS,
)
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import is_level_word  # noqa: E402

print("ALL_LEVEL_WORDS =", sorted(ALL_LEVEL_WORDS))
print()
for w in ('low', 'medium', 'high', 'very_low', 'very_high', 'extremely_low', 'level3'):
    in_words = is_level_word(w)
    in_map = w in LEGACY_HS_MAPPING_DICT
    flag = '' if in_map else '  <== 词表里有但映射表没有！'
    print(f"  {w:<15} is_level_word={in_words!s:<5} LEGACY_HS_MAPPING_DICT 有={in_map!s:<5}{flag}")

print("\n--- 用一条含 very_low 的规则建网 ---")
rule_array = [{'rule_description': 'IF SHORTSHOT_low AND IV0_very_low THEN IV0_add_2'}]
keyword_array = [{'keyword': 'IV0', 'lvl': 5, 'min_val': 0.0, 'max_val': 120.0, 'step': 40.0}]
try:
    net = NumTskRuleNet(rule_array, keyword_array, [1.0])
    print("建网成功")
    print("  connected_matrix 非零列:", net.connected_matrix.nonzero())
    res, _ = net.predict({'IV0': 30.0}, top_k=1)
    print("  推理结果:", res)
except Exception as e:
    print(f"  [建网即抛异常] {type(e).__name__}: {e}")

print("\n--- 经编排层 FuzzyEngine（看 except Exception 是否吞掉）---")
from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine  # noqa: E402
import process.algorithms.fuzzy.services.rule_query_service as rqs

# 伪造一条含 very_low 的 ResolvedRule
fake = rqs.ResolvedRule(
    method=None,
    rule_str='IF SHORTSHOT_low AND IV0_very_low THEN IV0_add_2',
    specificity=1, conclusion_kind='numeric', priority=1.0,
)
orig = rqs.RuleQueryService.get_rules
rqs.RuleQueryService.get_rules = staticmethod(lambda ctx: [fake])
try:
    engine = FuzzyEngine()
    recs = engine.recommend({
        'feedback': {'defect': [{'keyword_name': 'SHORTSHOT', 'level': 'low'}]},
        'process_parameter': {'IV0': 30.0},
        'iteration_trend': {'trend': 'stable'},
        'machine_info': {},
        'polymer_info': {'abbreviation': 'PP'},
        'mold_info': {'product_category': '酒瓶'},
    })
    print(f"  FuzzyEngine.recommend 返回 {len(recs)} 条 Recommendation")
    if not recs:
        print("  [静默降级] 异常被吞掉，返回空推荐，调用方无从知晓")
finally:
    rqs.RuleQueryService.get_rules = orig