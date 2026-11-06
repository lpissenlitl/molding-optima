# -*- coding: utf-8 -*-
"""一次性验收：tuning_result → TuningRecord.result 映射链路（含 unchanged）

覆盖：
1. TUNING_RESULT_MAP 映射（含 qualified/unqualified 直通）
2. _update_previous_tuning_record：unchanged 能落库（改动前被 if 守卫丢弃）
3. TuningService.upsert_tuning_record：unchanged 原样落库
4. _update_previous_recommendation_is_adopted：仅 ineffective 置 False（训练标签）
5. FeedbackSchema 接受 unchanged
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch, MagicMock

from process.models import TuningRecord
from process.schemas.optimization import FeedbackSchema
from process.services import parameter_optimize as po
from process.services.tuning import TUNING_RESULT_MAP, TuningService

print("=== tuning_result 映射链路验收 ===")

# ---------- 1. 映射表 ----------
assert TUNING_RESULT_MAP["effective"] == "improved", TUNING_RESULT_MAP
assert TUNING_RESULT_MAP["ineffective"] == "worse", TUNING_RESULT_MAP
assert TUNING_RESULT_MAP["unchanged"] == "unchanged", TUNING_RESULT_MAP
assert TUNING_RESULT_MAP["qualified"] == "qualified", TUNING_RESULT_MAP
assert TUNING_RESULT_MAP["unqualified"] == "unqualified", TUNING_RESULT_MAP
print("[1/5] TUNING_RESULT_MAP: effective→improved, ineffective→worse, unchanged→unchanged, qualified/unqualified 直通  OK")

# ---------- 2. _update_previous_tuning_record ----------
CASES = [
    ("effective", "improved"),
    ("ineffective", "worse"),
    ("unchanged", "unchanged"),
    ("qualified", "qualified"),
    ("unqualified", "unqualified"),
    (None, "pending"),  # 未评价 ⇒ 保持原值不动
]
for tuning_result, expected in CASES:
    fake_record = MagicMock(result="pending")
    with patch.object(TuningRecord.objects, "filter") as mf:
        mf.return_value.order_by.return_value.first.return_value = fake_record
        po._update_previous_tuning_record(
            parent_param=MagicMock(id=1),
            defect_feedbacks=[{"keyword_name": "短射", "level": "high"}],
            tuning_result=tuning_result,
        )
    assert fake_record.result == expected, f"{tuning_result!r} ⇒ {fake_record.result!r}，期望 {expected!r}"
    print(f"[2/5] _update_previous_tuning_record({tuning_result!r}) -> result={expected!r}  OK")

# ---------- 3. upsert_tuning_record ----------
fake_record = MagicMock(result="pending")
with patch.object(TuningRecord.objects, "filter") as mf:
    mf.return_value.order_by.return_value.first.return_value = fake_record
    TuningService.upsert_tuning_record(
        parameter=MagicMock(id=1),
        defect_feedbacks=[],
        tuning_result="unchanged",
    )
assert fake_record.result == "unchanged", fake_record.result
print("[3/5] upsert_tuning_record('unchanged') ⇒ result='unchanged'  OK")

# ---------- 4. Recommendation.is_adopted（训练标签）----------
for tuning_result, expect_adopted in [("ineffective", False), ("unchanged", True), ("effective", True)]:
    fake_rec = MagicMock(is_adopted=True)
    with patch.object(po.Recommendation.objects, "filter") as mf:
        mf.return_value.order_by.return_value.first.return_value = fake_rec
        po._update_previous_recommendation_is_adopted(MagicMock(id=1), tuning_result)
    assert fake_rec.is_adopted is expect_adopted, f"{tuning_result} ⇒ is_adopted={fake_rec.is_adopted}"
    print(f"[4/5] is_adopted({tuning_result!r}) ⇒ {expect_adopted}  OK")

# ---------- 5. Schema ----------
fb = FeedbackSchema(defect=[], tuning_result="unchanged")
assert fb.tuning_result == "unchanged", fb.tuning_result
assert FeedbackSchema(defect=[], tuning_result="qualified").tuning_result == "qualified"
assert FeedbackSchema(defect=[], tuning_result=None).tuning_result is None
print("[5/5] FeedbackSchema 接受 unchanged / qualified / null  OK")

print("\n=== 全部通过 ===")
