r"""tuning_result → TuningRecord.result 映射链路护栏。

覆盖：
1. TUNING_RESULT_MAP 映射（含 qualified/unqualified 直通）
2. _record_tuning_round：unchanged 能落库（改动前被 if 守卫丢弃）
3. TuningService.upsert_tuning_record：unchanged 原样落库
4. _settle_recommendation_adoption：仅 ineffective 置 False（训练标签）
5. FeedbackSchema 接受 unchanged

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_tuning_result_map.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch, MagicMock  # noqa: E402

from process.models import TuningRecord  # noqa: E402
from process.schemas.optimization import FeedbackSchema  # noqa: E402
from process.services import parameter_optimize as po  # noqa: E402
from process.services.tuning import TUNING_RESULT_MAP, TuningService  # noqa: E402

#: tuning_result → 落库 result 的期望映射（None = 未评价 ⇒ 保持原值不动）
CASES = [
    ("effective", "improved"),
    ("ineffective", "worse"),
    ("unchanged", "unchanged"),
    ("qualified", "qualified"),
    ("unqualified", "unqualified"),
    (None, "pending"),
]


def test_result_map_maps_every_tuning_result():
    """参照系（业务口径）：effective→improved、ineffective→worse，
    unchanged/qualified/unqualified 直通。"""
    assert TUNING_RESULT_MAP["effective"] == "improved", TUNING_RESULT_MAP
    assert TUNING_RESULT_MAP["ineffective"] == "worse", TUNING_RESULT_MAP
    assert TUNING_RESULT_MAP["unchanged"] == "unchanged", TUNING_RESULT_MAP
    assert TUNING_RESULT_MAP["qualified"] == "qualified", TUNING_RESULT_MAP
    assert TUNING_RESULT_MAP["unqualified"] == "unqualified", TUNING_RESULT_MAP


def test_record_tuning_round_writes_mapped_result():
    """参照系（业务口径）：本轮评价按映射表落库；未评价（None）保持 pending。"""
    for tuning_result, expected in CASES:
        fake_record = MagicMock(result="pending")
        with patch.object(TuningRecord.objects, "filter") as mf, \
                patch.object(po.Recommendation.objects, "create") as mrec:
            mf.return_value.order_by.return_value.first.return_value = fake_record
            po._record_tuning_round(
                parent_param=MagicMock(id=1),
                changed_fields={},
                defect_feedbacks=[{"keyword_name": "短射", "level": "high"}],
                observations=[{"param_key": "actual_product_weight", "value": 85.0}],
                tuning_result=tuning_result,
                algorithm_recommendations=[],
                source_type="fuzzy_rule",
            )
        assert mrec.called, "记录本轮时应同时挂上算法推荐"
        assert fake_record.result == expected, (
            f"{tuning_result!r} ⇒ {fake_record.result!r}，期望 {expected!r}"
        )


def test_upsert_tuning_record_keeps_unchanged():
    """参照系（业务口径）：unchanged 原样落库（不被守卫丢弃）。"""
    fake_record = MagicMock(result="pending")
    with patch.object(TuningRecord.objects, "filter") as mf:
        mf.return_value.order_by.return_value.first.return_value = fake_record
        TuningService.upsert_tuning_record(
            parameter=MagicMock(id=1),
            defect_feedbacks=[],
            tuning_result="unchanged",
        )

    assert fake_record.result == "unchanged", fake_record.result


def test_settle_recommendation_adoption_only_ineffective_is_false():
    """参照系（业务口径）：训练标签只有 ineffective 置未采纳，其余照旧。"""
    for tuning_result, expect_adopted in [("ineffective", False), ("unchanged", True), ("effective", True)]:
        fake_rec = MagicMock(is_adopted=True)
        with patch.object(po.Recommendation.objects, "filter") as mf:
            mf.return_value.order_by.return_value.first.return_value = fake_rec
            po._settle_recommendation_adoption(MagicMock(id=1), tuning_result)
        assert fake_rec.is_adopted is expect_adopted, (
            f"{tuning_result} ⇒ is_adopted={fake_rec.is_adopted}"
        )


def test_feedback_schema_accepts_all_result_values():
    """参照系（业务口径）：评价入参接受 unchanged / qualified / null。"""
    fb = FeedbackSchema(defect=[], tuning_result="unchanged")
    assert fb.tuning_result == "unchanged", fb.tuning_result
    assert FeedbackSchema(defect=[], tuning_result="qualified").tuning_result == "qualified"
    assert FeedbackSchema(defect=[], tuning_result=None).tuning_result is None


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_tuning_result_map``。"""
    cases = [
        test_result_map_maps_every_tuning_result,
        test_record_tuning_round_writes_mapped_result,
        test_upsert_tuning_record_keeps_unchanged,
        test_settle_recommendation_adoption_only_ineffective_is_false,
        test_feedback_schema_accepts_all_result_values,
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