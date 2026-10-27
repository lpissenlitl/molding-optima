r"""推荐结果层（`fuzzy/recommendations.py`）合并逻辑测试

由 `process/algorithms/fuzzy/sanity_check.py` CASE 3 迁移而来（E19；**该文件已删除**）。
迁移原因同 `fuzzy_core/tests/test_inference_gates.py`：sanity_check 是与 pytest
并行的第二套测试体系，而 `recommendations` / `engine` 正在重构中。

覆盖「方案 B：同层聚合 + 跨层覆盖」的全部规则：
  1. 数值层的调整量裸累加到同参数上（不做折算）
  2. 提示层的数值结论：若该参数数值层已命中 ⇒ 只记为 `advisory_reference`
  3. 提示层的**文本建议**（`advice` 非空）不参与数值聚合，单独返回
  4. `to_recommendations()` 的对外字段（recommended_value / confidence /
     direction / source / reason）

⚠️ 本模块**零 Django 依赖**（已实测：import 后 `django` 与 `process.models`
均未进 `sys.modules`），因此不需要 `django.setup()`。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_fuzzy_aggregation.py -q
"""

from process.algorithms.fuzzy.recommendations import (
    RuleAdjustment,
    aggregate,
    to_recommendations,
)


NUMERIC_RESULTS = [
    RuleAdjustment(param_name='inj_pres_1', delta=10.0, activation=0.9,
                   layer='numeric', rule_str='r1'),
    RuleAdjustment(param_name='inj_pres_2', delta=5.0, activation=0.7,
                   layer='numeric', rule_str='r2'),
    # 同参数多条规则 → 同层聚合
    RuleAdjustment(param_name='inj_pres_1', delta=5.0, activation=0.6,
                   layer='numeric', rule_str='r3'),
]

ADVISORY_RESULTS = [
    RuleAdjustment(param_name='hold_time', delta=1.5, activation=0.5,
                   layer='advisory', rule_str='r4'),
    # inj_pres_1 已被数值层覆盖 → 应作为 advisory_reference，不覆盖
    RuleAdjustment(param_name='inj_pres_1', delta=999, activation=0.4,
                   layer='advisory', rule_str='r5'),
    # 文本建议（检查/弹窗类）→ 必须单独输出，不进数值聚合
    RuleAdjustment(param_name='MEL', delta=0.0, activation=0.0,
                   layer='advisory', rule_str='r6', advice='请检查计量终点位置'),
]

CURRENT_PARAMS = {'inj_pres_1': 50, 'inj_pres_2': 80, 'hold_time': 3, 'MEL': 10}
FACTOR = 1.2


def test_aggregate_same_layer_sum():
    """同参数多条数值规则 ⇒ 裸累加（不折算）。"""
    aggregated, _ = aggregate(NUMERIC_RESULTS, ADVISORY_RESULTS)
    by_name = {a.param_name: a for a in aggregated}

    inj1 = by_name['inj_pres_1']
    assert abs(inj1.delta - 15.0) < 1e-6, f'aggregated delta={inj1.delta}'
    assert inj1.rule_count == 2, inj1.rule_count
    assert abs(inj1.activation_sum - 1.5) < 1e-6, f'activation_sum={inj1.activation_sum}'


def test_aggregate_cross_layer_becomes_reference():
    """数值层已覆盖的参数 ⇒ 提示层只作 `advisory_reference`，不覆盖数值。"""
    aggregated, _ = aggregate(NUMERIC_RESULTS, ADVISORY_RESULTS)
    by_name = {a.param_name: a for a in aggregated}

    inj1 = by_name['inj_pres_1']
    assert inj1.sources == ['numeric', 'advisory'], f'sources={inj1.sources}'
    assert inj1.advisory_reference == 999, f'advisory_reference={inj1.advisory_reference}'
    # 提示层的 999 没有被折算进 delta
    assert abs(inj1.delta - 15.0) < 1e-6, f'aggregated delta={inj1.delta}'


def test_aggregate_layer_only_params():
    """仅数值层命中的参数 sources 只含 numeric；仅提示层的只含 advisory。"""
    aggregated, _ = aggregate(NUMERIC_RESULTS, ADVISORY_RESULTS)
    by_name = {a.param_name: a for a in aggregated}

    assert by_name['inj_pres_2'].sources == ['numeric'], by_name['inj_pres_2'].sources
    assert by_name['hold_time'].sources == ['advisory'], by_name['hold_time'].sources


def test_text_advice_separated():
    """文本建议被单独分离 —— 不进数值聚合，也不进参数汇总。"""
    aggregated, advice_items = aggregate(NUMERIC_RESULTS, ADVISORY_RESULTS)
    by_name = {a.param_name: a for a in aggregated}

    assert len(advice_items) == 1, f'advice_items={advice_items}'
    assert advice_items[0].advice == '请检查计量终点位置'
    assert 'MEL' not in by_name, '文本建议不应进入数值聚合'


def test_to_recommendations_numeric_fields():
    """数值推荐的对外字段：recommended_value / confidence / direction / source / reason。"""
    aggregated, advice_items = aggregate(NUMERIC_RESULTS, ADVISORY_RESULTS)
    recs = to_recommendations(aggregated, advice_items, FACTOR, CURRENT_PARAMS)
    rec_by_name = {r.param_name: r for r in recs}

    # recommended = current + delta * factor；confidence = activation_sum / rule_count
    inj1_rec = rec_by_name['inj_pres_1']
    assert abs(inj1_rec.recommended_value - (50 + 15.0 * 1.2)) < 1e-6, inj1_rec.recommended_value
    assert abs(inj1_rec.confidence - (1.5 / 2)) < 1e-6, inj1_rec.confidence
    assert inj1_rec.direction == 'increase', inj1_rec.direction
    assert inj1_rec.source == 'fuzzy.numeric', inj1_rec.source
    assert inj1_rec.reason == "模糊推理 (sources=['numeric', 'advisory'])", inj1_rec.reason


def test_to_recommendations_advice_fields():
    """文本建议：recommended_value=None / confidence=None / direction='check' / source='fuzzy.check'。"""
    aggregated, advice_items = aggregate(NUMERIC_RESULTS, ADVISORY_RESULTS)
    recs = to_recommendations(aggregated, advice_items, FACTOR, CURRENT_PARAMS)
    rec_by_name = {r.param_name: r for r in recs}

    mel_rec = rec_by_name['MEL']
    assert mel_rec.recommended_value is None, mel_rec.recommended_value
    assert mel_rec.confidence is None, mel_rec.confidence
    assert mel_rec.direction == 'check', mel_rec.direction
    assert mel_rec.source == 'fuzzy.check', mel_rec.source


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_fuzzy_aggregation``。"""
    cases = [
        test_aggregate_same_layer_sum,
        test_aggregate_cross_layer_becomes_reference,
        test_aggregate_layer_only_params,
        test_text_advice_separated,
        test_to_recommendations_numeric_fields,
        test_to_recommendations_advice_fields,
    ]
    failed = []
    for fn in cases:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - 独立跑法需要汇总全部失败
            print(f'[FAIL] {fn.__name__}: {exc}')
            failed.append(fn.__name__)
    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] {len(failed)}/{len(cases)} 个用例失败：{failed}')
        return 1
    print(f'[PASS] {len(cases)}/{len(cases)} 个用例通过')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
