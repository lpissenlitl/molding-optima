"""字段体检（_build_field_context）测试

覆盖 2026-10-22 引入的字段三态分类：
  - authority : 有 RuleKeyword 权威元数据
  - guessed   : 无权威元数据，按实时值推测了一个论域（带 meta_source='guessed' 标记）
  - unknown   : 既无权威元数据也无实时值 ⇒ 规则少了一个门控条件，激活度偏高

不依赖规则库数据：mock 掉 _load_keyword_dicts，只测分类与报告逻辑。

运行：
  cd backend
  python -m tests.test_fuzzy_field_report
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.algorithms.fuzzy.fuzzy_algorithm import (  # noqa: E402
    FIELD_SOURCE_GUESSED,
    FuzzyEngine,
)


RULES = [
    'IF SHORTSHOT_low AND MEL_high THEN MEL_add_3.8',
    'IF FLASH_high AND HOLDEXIST_high AND PP0_high THEN PP0_reduce_10',
]

# 模拟 _load_keyword_dicts 的返回：
#   MEL        -> 权威元数据
#   HOLDEXIST  -> 推测论域（带 meta_source 标记）
#   PP0        -> 没有（既不在清单里，也拿不到实时值）
KEYWORD_DICTS = [
    {'keyword': 'MEL', 'lvl': 5, 'min_val': 0.0, 'max_val': 100.0, 'step': 1.0},
    {
        'keyword': 'HOLDEXIST', 'lvl': 3, 'min_val': 0.0, 'max_val': 2.0,
        'step': 0.1, 'meta_source': FIELD_SOURCE_GUESSED,
    },
]


class _FakeRule:
    """最小 ResolvedRule 替身（只需 rule_str）。"""

    def __init__(self, s):
        self.rule_str = s


def _build_engine():
    engine = FuzzyEngine()

    def _fake_load(param_names, process_parameter):
        # 真实实现只返回查到的字段
        names = set(param_names)
        return [dict(kw) for kw in KEYWORD_DICTS if kw['keyword'] in names]

    engine._load_keyword_dicts = _fake_load
    return engine


def test_field_classification():
    """字段三态分类正确。"""
    engine = _build_engine()
    rules = [_FakeRule(r) for r in RULES]
    _kws, classification = engine._build_field_context(rules, {}, 'numeric')

    assert classification['authority'] == ['MEL'], classification
    assert classification['guessed'] == ['HOLDEXIST'], classification
    assert classification['unknown'] == ['PP0'], classification
    print("[PASS] 字段三态分类正确")


def test_defect_names_not_in_report():
    """缺陷名在 collect_param_names 阶段已被剔除，不应出现在 unknown 里。"""
    engine = _build_engine()
    rules = [_FakeRule(r) for r in RULES]
    _kws, classification = engine._build_field_context(rules, {}, 'numeric')

    all_names = (classification['authority'] + classification['guessed']
                 + classification['unknown'])
    assert 'SHORTSHOT' not in all_names, all_names
    assert 'FLASH' not in all_names, all_names
    print("[PASS] 缺陷名不进入字段分类")


def test_report_accumulated():
    """每次调用都会往 _field_reports 里追加一份分类结果。"""
    engine = _build_engine()
    rules = [_FakeRule(r) for r in RULES]
    engine._build_field_context(rules, {}, 'numeric')
    engine._build_field_context(rules, {}, 'advisory')

    assert len(engine._field_reports) == 2, engine._field_reports
    assert engine._field_reports[0]['layer'] == 'numeric'
    assert engine._field_reports[1]['layer'] == 'advisory'
    assert engine._field_reports[0]['classification']['unknown'] == ['PP0']
    print("[PASS] 降级清单累积到 _field_reports")


def test_keyword_dicts_unchanged():
    """送引擎的元数据清单原样透传（不做任何增删改）。"""
    engine = _build_engine()
    rules = [_FakeRule(r) for r in RULES]
    kws, _cls = engine._build_field_context(rules, {}, 'numeric')

    assert len(kws) == len(KEYWORD_DICTS), kws
    assert {k['keyword'] for k in kws} == {'MEL', 'HOLDEXIST'}
    # 权威项不带 meta_source，猜测项带 meta_source
    by_name = {k['keyword']: k for k in kws}
    assert 'meta_source' not in by_name['MEL']
    assert by_name['HOLDEXIST']['meta_source'] == FIELD_SOURCE_GUESSED
    print("[PASS] 元数据清单原样透传")


def test_empty_input():
    """没有规则时不报错，分类结果为空。"""
    engine = _build_engine()
    kws, classification = engine._build_field_context([], {}, 'numeric')
    assert kws == []
    assert classification['authority'] == []
    assert classification['guessed'] == []
    assert classification['unknown'] == []
    print("[PASS] 空输入不报错")


def main():
    test_field_classification()
    test_defect_names_not_in_report()
    test_report_accumulated()
    test_keyword_dicts_unchanged()
    test_empty_input()
    print("\nALL PASS  (5/5 组通过)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
