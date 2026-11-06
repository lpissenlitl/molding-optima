# -*- coding: utf-8 -*-
"""一次性验收：调机轮次回显链路（参数与反馈配对语义）

背景：界面语义「第 N 轮 = 参数(N) + 反馈(N)」—— 反馈是该轮参数自身的试模结果。

覆盖：
1. tuning_result_from_record：库内状态 → 前端评价枚举的反映射
2. _build_tuning_payload：单轮反馈的回显结构
3. get_condition_history：每轮 history item 携带【自己那一份】tuning（不串轮）
4. _create_new_tuning_record：新轮次不预置父轮缺陷（改动前会把父轮缺陷复制过来）
5. 回归：_update_previous_tuning_record 把缺陷与标签写到被评价的那一轮
6. build_recommendation_suggestion：Recommendation → 前端 Suggestion（算法建议同样按轮锚定）
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
from process.services import condition as cond
from process.services import parameter_optimize as po
from process.services.tuning import tuning_result_from_record

print("=== 调机轮次回显链路验收 ===")

# ---------- 1. 反映射（库内存储词 → 前端三档）----------
CASES = [
    ("improved", "effective"),
    ("worse", "ineffective"),
    ("unchanged", "unchanged"),
    ("pending", None),            # 未试模 ⇒ 未评价
    ("qualified", "qualified"),   # 合格/不合格直通
    ("unqualified", "unqualified"),
    (None, None),
]
for src, expected in CASES:
    got = tuning_result_from_record(src)
    assert got == expected, f"{src!r} -> {got!r}，期望 {expected!r}"
print("[1/6] tuning_result_from_record: improved/worse/unchanged -> 三档；qualified/unqualified 直通；pending -> None  OK")

# ---------- 2. _build_tuning_payload ----------
empty = cond._build_tuning_payload(None)
assert empty == {
    "tuning_result": None,
    "result": None,
    "defect_feedbacks": [],
    "result_detail": None,
}, empty

fake_record = MagicMock(
    result="worse",
    defect_feedbacks=[{"keyword_name": "飞边", "level": "medium"}],
    result_detail="飞边加重",
)
payload = cond._build_tuning_payload(fake_record)
assert payload["tuning_result"] == "ineffective", payload
assert payload["result"] == "worse", payload
assert payload["defect_feedbacks"] == [{"keyword_name": "飞边", "level": "medium"}], payload
assert payload["result_detail"] == "飞边加重", payload
print("[2/6] _build_tuning_payload: 无记录回空；result=worst -> tuning_result=ineffective  OK")

# ---------- 3. get_condition_history：每轮携带自己的 tuning ----------
class _FakeField:
    def __init__(self, name):
        self.name = name
        self.is_relation = False


def _make_param(pid, seq, field_names=("inj_pres_1", "inj_pres_2")):
    p = MagicMock(id=pid)
    p.to_dict.return_value = {"id": pid, "seq_idx": seq, "inj_pres_1": 50 + seq}
    p._meta = MagicMock(fields=[_FakeField(n) for n in field_names])
    return p


def _make_record(pid, result, defects):
    r = MagicMock()
    r.process_parameter_id = pid
    r.result = result
    r.defect_feedbacks = defects
    r.result_detail = None
    return r


def _make_recommendation(pid, recommendations, is_adopted=True):
    r = MagicMock()
    r.process_parameter_id = pid
    r.source_type = "fuzzy_rule"
    r.is_adopted = is_adopted
    r.recommendations = recommendations
    return r


params = [_make_param(101, 1), _make_param(102, 2)]
records = [
    _make_record(101, "improved", [{"keyword_name": "短射", "level": "high"}]),
    _make_record(102, "pending", []),
]
recommendations = [
    _make_recommendation(101, [{
        "param": "inj_pres_1",
        "current_value": 70,
        "recommended_value": 60,
        "reason": "降低一段注射压力",
    }], is_adopted=False),
]
fake_condition = MagicMock()
fake_condition.to_dict.return_value = {"id": 7, "condition_no": "COND-7"}

param_qs = MagicMock()
param_qs.order_by.return_value = params
rec_qs = MagicMock()
rec_qs.order_by.return_value = records
reco_qs = MagicMock()
reco_qs.order_by.return_value = recommendations

with patch.object(cond, "_get_process_condition_by_id", return_value=fake_condition), \
        patch.object(cond.ProcessParameter.objects, "filter", return_value=param_qs), \
        patch.object(cond.TuningRecord.objects, "filter", return_value=rec_qs), \
        patch.object(cond.Recommendation.objects, "filter", return_value=reco_qs):
    hist = cond.get_condition_history(7)

history = hist["history"]
assert len(history) == 2, history
# 第 1 轮：带自己的缺陷与评价
assert history[0]["tuning"]["tuning_result"] == "effective", history[0]
assert history[0]["tuning"]["defect_feedbacks"] == [{"keyword_name": "短射", "level": "high"}], history[0]
# 第 2 轮：未试模 ⇒ 未评价、无缺陷（不串第 1 轮的缺陷）
assert history[1]["tuning"]["tuning_result"] is None, history[1]
assert history[1]["tuning"]["defect_feedbacks"] == [], history[1]
assert hist["condition"]["condition_no"] == "COND-7", hist["condition"]
# 算法建议同样锚在本轮：第 1 轮有，第 2 轮无
assert history[0]["tuning"]["suggestion"]["groups"][0]["items"][0]["param"] == "inj_pres_1", history[0]
assert history[0]["tuning"]["suggestion"]["adopted"] is False, history[0]
assert "suggestion" not in history[1]["tuning"], history[1]
print("[3/6] get_condition_history: 每轮携带自己的 tuning + suggestion，未试模轮不串前轮数据  OK")

# ---------- 4. _create_new_tuning_record：新轮次不预置父轮缺陷 ----------
parent = MagicMock(id=1)
parent._meta = MagicMock(fields=[_FakeField("inj_pres_1")])
new_param = MagicMock(id=2)

with patch.object(TuningRecord.objects, "create") as mc:
    po._create_new_tuning_record(new_param=new_param, parent_param=parent)

kwargs = mc.call_args.kwargs
assert kwargs["defect_feedbacks"] == [], f"新轮次不应预置缺陷，实际 {kwargs['defect_feedbacks']!r}"
assert kwargs["result"] == "pending", kwargs
assert kwargs["process_parameter"] is new_param, kwargs
print("[4/6] _create_new_tuning_record: 新轮次 defect_feedbacks=[] / result=pending（不复制父轮缺陷）  OK")

# ---------- 5. 回归：缺陷与标签写到被评价的那一轮 ----------
fake_rec = MagicMock(result="pending")
with patch.object(TuningRecord.objects, "filter") as mf:
    mf.return_value.order_by.return_value.first.return_value = fake_rec
    po._update_previous_tuning_record(
        parent_param=MagicMock(id=1),
        defect_feedbacks=[{"keyword_name": "气纹", "level": "low"}],
        tuning_result="unchanged",
    )
assert fake_rec.result == "unchanged", fake_rec.result
assert fake_rec.defect_feedbacks == [{"keyword_name": "气纹", "level": "low"}], fake_rec.defect_feedbacks
print("[5/6] _update_previous_tuning_record: 缺陷 + unchanged 标签写到被评价轮  OK")

# ---------- 6. 算法建议锚定：Recommendation → 前端 Suggestion ----------
fake_rec_full = _make_recommendation(101, [{
    "param": "inj_pres_1",
    "current_value": 70,
    "recommended_value": 60,
    "reason": "降低一段注射压力",
}], is_adopted=False)
sug = po.build_recommendation_suggestion(fake_rec_full, params[0])
assert sug["source_type"] == "fuzzy_rule", sug
assert sug["adopted"] is False, sug
assert len(sug["groups"]) == 1, sug
item = sug["groups"][0]["items"][0]
assert item["param"] == "inj_pres_1", item
assert item["description"] == "降低一段注射压力", item
assert item["direction"] == "decrease", item

# 空建议 => groups 空（但保留 is_adopted）
empty_sug = po.build_recommendation_suggestion(
    _make_recommendation(101, [], is_adopted=True), params[0]
)
assert empty_sug["groups"] == [], empty_sug
assert empty_sug["adopted"] is True, empty_sug

# baseline 里没有该字段 => 过滤掉（与落库时 _build_suggestion_payload 口径一致）
no_field_param = _make_param(103, 3, field_names=("cool_t",))
filtered = po.build_recommendation_suggestion(fake_rec_full, no_field_param)
assert filtered["groups"] == [], filtered
print("[6/6] build_recommendation_suggestion: Recommendation -> groups/adopted，baseline 过滤口径一致  OK")

print("\n=== 全部通过 ===")
