# -*- coding: utf-8 -*-
"""一次性验收：合格态（qualified）流程

背景：合格态产品**没有缺陷** ⇒
- 界面不要求填缺陷（前端隐藏并清空缺陷区）
- 后端照常落库（result=qualified），但提交的缺陷信息一律丢弃
- 不进入缺陷驱动的优化流程（infer 短路：不跑 fuzzy、不建新轮次）

覆盖：
1. is_qualified_result：合格判定
2. upsert_tuning_record：qualified ⇒ 丢弃缺陷（即使传了）；其余档位缺陷保留
3. _update_previous_tuning_record：qualified ⇒ 显式清空缺陷（含历史遗留，不靠 if 守卫跳过）
4. _validate_feedback：仅 qualified 允许空缺陷
5. infer：qualified ⇒ 不跑 fuzzy、不建新轮次，但参数与评价照常落库
6. TuningRecordRequestSchema：接受 parameter（flat 工艺字段），未传字段不落库
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch, MagicMock

from extensions.exceptions import BizException
from process.models import TuningRecord
from process.schemas.tuning import TuningRecordRequestSchema
from process.services import parameter_optimize as po
from process.services.tuning import TuningService, is_qualified_result

print("=== 合格态（qualified）流程验收 ===")

DEFECT = [{"keyword_name": "短射", "level": "high", "position": "DL短射1"}]

# ---------- 1. 合格判定 ----------
assert is_qualified_result("qualified") is True
assert is_qualified_result("unqualified") is False
assert is_qualified_result("effective") is False
assert is_qualified_result(None) is False
print("[1/6] is_qualified_result: 仅 'qualified' 为真  OK")

# ---------- 2. upsert_tuning_record：qualified 丢弃缺陷 ----------
fake_record = MagicMock(result="pending", defect_feedbacks=[{"keyword_name": "气纹"}])
with patch.object(TuningRecord.objects, "filter") as mf:
    mf.return_value.order_by.return_value.first.return_value = fake_record
    TuningService.upsert_tuning_record(
        parameter=MagicMock(id=1),
        defect_feedbacks=DEFECT,
        tuning_result="qualified",
    )
assert fake_record.result == "qualified", fake_record.result
assert fake_record.defect_feedbacks == [], f"合格态应丢弃缺陷，实际 {fake_record.defect_feedbacks!r}"

# 非合格档位：缺陷照常写入（回归）
fake_record2 = MagicMock(result="pending", defect_feedbacks=[])
with patch.object(TuningRecord.objects, "filter") as mf:
    mf.return_value.order_by.return_value.first.return_value = fake_record2
    TuningService.upsert_tuning_record(
        parameter=MagicMock(id=1),
        defect_feedbacks=DEFECT,
        tuning_result="unchanged",
    )
assert fake_record2.defect_feedbacks == DEFECT, fake_record2.defect_feedbacks
print("[2/6] upsert_tuning_record: qualified ⇒ 缺陷丢弃；unchanged ⇒ 缺陷保留  OK")

# ---------- 3. _update_previous_tuning_record：qualified 显式清空 ----------
# 场景：先填过缺陷，后改判合格 —— 历史缺陷必须被清掉（不能靠 `if defect_feedbacks:` 守卫跳过）
fake_rec = MagicMock(result="pending", defect_feedbacks=[{"keyword_name": "气纹", "level": "low"}])
with patch.object(TuningRecord.objects, "filter") as mf:
    mf.return_value.order_by.return_value.first.return_value = fake_rec
    po._update_previous_tuning_record(
        parent_param=MagicMock(id=1),
        defect_feedbacks=DEFECT,
        tuning_result="qualified",
    )
assert fake_rec.result == "qualified", fake_rec.result
assert fake_rec.defect_feedbacks == [], f"合格态应清空历史缺陷，实际 {fake_rec.defect_feedbacks!r}"

# 非合格档位：缺陷写入（回归）
fake_rec2 = MagicMock(result="pending", defect_feedbacks=[])
with patch.object(TuningRecord.objects, "filter") as mf:
    mf.return_value.order_by.return_value.first.return_value = fake_rec2
    po._update_previous_tuning_record(
        parent_param=MagicMock(id=1),
        defect_feedbacks=DEFECT,
        tuning_result="unchanged",
    )
assert fake_rec2.defect_feedbacks == DEFECT, fake_rec2.defect_feedbacks
print("[3/6] _update_previous_tuning_record: qualified ⇒ 显式清空（含历史遗留）；其余 ⇒ 写入  OK")

# ---------- 4. _validate_feedback：仅 qualified 允许空缺陷 ----------
po._validate_feedback({"tuning_result": "qualified", "defect": []})  # 放行
po._validate_feedback({"tuning_result": "qualified", "defect": DEFECT})  # 也放行
for bad in (
    {"tuning_result": "unchanged", "defect": []},
    {"tuning_result": "unqualified", "defect": []},
    {},
):
    try:
        po._validate_feedback(bad)
    except BizException:
        pass
    else:
        raise AssertionError(f"空缺陷应当被拒：{bad!r}")
print("[4/6] _validate_feedback: 仅 qualified 允许空缺陷，其余一律拒  OK")

# ---------- 5. infer：qualified 短路（不跑 fuzzy、不建新轮次，但照常落库）----------
fake_ctx = {
    "condition": MagicMock(),
    "parent_param": MagicMock(id=1),
    "baseline": {},
    "machine_info": {},
    "polymer_info": {},
    "mold_info": {},
    "user_changed_fields": {"inj_pres_1": 55},
}
with patch.object(po, "_assemble_context", return_value=fake_ctx), \
        patch.object(po, "_sync_user_modified_parameter") as msync, \
        patch.object(po, "_update_previous_tuning_record") as mupd, \
        patch.object(po.ParameterOptimizeService, "_infer_kernel") as mkernel, \
        patch.object(po.db_transaction, "atomic") as matomic:
    result = po.ParameterOptimizeService().infer(
        condition_id=1,
        parent_seq_idx=1,
        parameter=None,
        feedback={"tuning_result": "qualified", "defect": []},
    )
assert mkernel.call_count == 0, "合格态不应调用模糊推理"
assert msync.call_count == 1, "合格态仍应写回用户手改的参数"
assert mupd.call_count == 1, "合格态仍应写入本轮评价"
assert result["skipped"] is True, result
assert result["skip_reason"] == "qualified", result
assert result["new_parameter"] is None, result
assert result["suggestion"] is None, result
print("[5/6] infer(qualified): 不跑 fuzzy、不建新轮次；参数与评价照常落库  OK")

# ---------- 6. Schema：接受 parameter（flat 工艺字段）----------
schema = TuningRecordRequestSchema(**{
    "tuning_result": "qualified",
    "defect_feedbacks": [],
    "parameter": {"inj_pres_1": 55, "hold_t_1": 12},
})
dumped = schema.model_dump(exclude_none=True, by_alias=True)
assert dumped["parameter"] == {"inj_pres_1": 55, "hold_t_1": 12}, dumped["parameter"]
assert dumped["tuning_result"] == "qualified", dumped

# 不传 parameter ⇒ 只写评价（向后兼容）
no_param = TuningRecordRequestSchema(**{"tuning_result": "unchanged", "defect_feedbacks": DEFECT})
dumped2 = no_param.model_dump(exclude_none=True, by_alias=True)
assert "parameter" not in dumped2, dumped2

# 传空 dict ⇒ 不报错（语义 = 没改参数，只写评价）
empty_param = TuningRecordRequestSchema(**{"tuning_result": "qualified", "parameter": {}})
dumped3 = empty_param.model_dump(exclude_none=True, by_alias=True)
assert dumped3.get("parameter", {}) == {}, dumped3
print("[6/6] TuningRecordRequestSchema: 接受 parameter(flat)；未传/空 dict 均不报错  OK")

print("\n=== 全部通过 ===")
