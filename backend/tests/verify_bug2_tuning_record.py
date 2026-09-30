"""Bug 2 修复验证：_create_process_parameter / _copy_process_parameter 同步创建 TuningRecord"""
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch, MagicMock
from process.services.parameter_init import ParameterInitService

print("=== Bug 2 修复验证 ===")

# ---------- 1. _create_process_parameter ----------
print("\n[1] _create_process_parameter 验证:")
fake_param = MagicMock(id=999)

with patch("process.models.parameter.ProcessParameter.objects.create", return_value=fake_param) as mock_param_create, \
     patch("process.models.tuning_record.TuningRecord.objects.create") as mock_tr_create:
    fake_condition = MagicMock(id=14)
    fake_result = {"process": {"inj_stg": 3, "inj_pres_steps": [80, 90, None, None, None, None]}}

    new_param = ParameterInitService._create_process_parameter(fake_condition, fake_result)

    assert mock_param_create.called, "BUG: ProcessParameter 未创建"
    print("    [OK] ProcessParameter.objects.create 被调用")
    assert mock_tr_create.called, "BUG: TuningRecord 未创建"
    print("    [OK] TuningRecord.objects.create 被调用 (业务契约 1:1)")

    call_kwargs = mock_tr_create.call_args.kwargs
    assert call_kwargs["process_parameter"] == fake_param
    assert call_kwargs["result"] == "pending"
    assert call_kwargs["defect_feedbacks"] == []
    print("    [OK] TuningRecord 入参正确: process_parameter=id999, result=pending, defect_feedbacks=[]")

# ---------- 2. _copy_process_parameter ----------
print("\n[2] _copy_process_parameter 验证:")
fake_source_param = MagicMock()
fake_source_param.inj_stg = 3
fake_source_param.inj_pres_1 = 80.5

with patch("process.models.parameter.ProcessParameter.objects.create", return_value=fake_param) as mock_param_create, \
     patch("process.models.tuning_record.TuningRecord.objects.create") as mock_tr_create:
    fake_target_cond = MagicMock(id=15)

    new_param = ParameterInitService._copy_process_parameter(fake_source_param, fake_target_cond)

    assert mock_param_create.called, "BUG: ProcessParameter 未创建"
    print("    [OK] ProcessParameter.objects.create 被调用")
    assert mock_tr_create.called, "BUG: TuningRecord 未创建"
    print("    [OK] TuningRecord.objects.create 被调用 (业务契约 1:1)")

    call_kwargs = mock_tr_create.call_args.kwargs
    assert call_kwargs["process_parameter"] == fake_param
    assert call_kwargs["result"] == "pending"
    print("    [OK] TuningRecord 入参正确: process_parameter=id999, result=pending")

print("\n" + "=" * 50)
print("Bug 2 验证通过")
print("ProcessParameter <-> TuningRecord 1:1 业务契约已建立")
print("后续 optimization/infer/ 调 _update_previous_tuning_record 不再 WARNING")