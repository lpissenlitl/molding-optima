"""
verify_initialize_flat.py

验证 initialize 响应的 flat 契约（D1 决策 2026-10-22，见
backend/_refs/system/algorithm/2026-10-22-optimize-contract-and-fuzzy-engine-review.md）：

- initialize 的 result['process'] 与 optimize 的 new_parameter **同为 flat**
- flat ↔ nested 的形态转换只在后端边界发生一次（process_params_to_flat），
  落库与 HTTP 响应共用同一份 flat，不会各拍一次导致语义漂移
- 温度段位语义不漂移：喷嘴（noz_temp）与料筒 1..9（brl_temp_1..9）是独立字段

不查 DB、不调真实算法：mock _infer_kernel 走通响应边界。
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import MagicMock, patch  # noqa: E402

from process.services import parameter_initialize as _init_mod  # noqa: E402
from process.services.parameter_initialize import (  # noqa: E402
    ParameterInitializeService,
    process_params_to_flat,
)

# 算法侧的 nested 工艺参数（ProcessParams.to_dict 形态）
NESTED_PROCESS = {
    "inj_stg": 1,
    "inj_spd_steps": [50.0],
    "inj_pres_steps": [80.0, 75.0],
    "inj_pos_steps": [10.0],
    "inj_t": 1.5,
    "inj_dly_t": 0.2,
    "cool_t": 10.0,
    "vps_mode": 0,
    "hold_stg": 1,
    "hold_pres_steps": [60.0],
    "hold_spd_steps": [10.0],
    "hold_time_steps": [1.0],
    "met_stg": 1,
    "met_pres_steps": [90.0],
    "met_rot_spd_steps": [50.0],
    "met_back_pres_steps": [5.0],
    "met_pos_steps": [20.0],
    "pre_met_decomp_mode": 0,
    "pre_met_decomp_pres": 3.0,
    "pre_met_decomp_spd": 5.0,
    "pre_met_decomp_t": 1.0,
    "pre_met_decomp_dist": 2.0,
    "pst_met_decomp_mode": 1,
    "pst_met_decomp_pres": 3.0,
    "pst_met_decomp_spd": 5.0,
    "pst_met_decomp_t": 1.0,
    "pst_met_decomp_dist": 2.0,
    "met_lim_t": 3.0,
    "met_end_pos": 15.0,
    "brl_temp_stg": 5,
    "noz_temp": 230.0,
    "brl_temp_steps": [200.0, 210.0],
}


def main():
    print("=" * 70)
    print("initialize flat 契约验证（D1 决策）")
    print("=" * 70)

    # ---- A. process_params_to_flat 映射正确性 ----
    flat = process_params_to_flat(NESTED_PROCESS)

    # A1 单值字段直传
    assert flat.get("inj_t") == 1.5, f"inj_t 应为 1.5, got {flat.get('inj_t')}"
    assert flat.get("inj_stg") == 1, f"inj_stg 应为 1, got {flat.get('inj_stg')}"
    print("[A1] 单值字段直传 OK")

    # A2 单值字段为 None 时不输出该 key（与历史落库行为一致）
    flat_none = process_params_to_flat({"inj_t": None, "inj_stg": 2})
    assert "inj_t" not in flat_none, f"None 单值不应输出 key, got {flat_none.get('inj_t')}"
    assert flat_none.get("inj_stg") == 2
    print("[A2] None 单值不输出 key OK")

    # A3 数组段展开 + 缺位补 None（恒输出全部段位）
    assert flat.get("inj_pres_1") == 80.0, f"inj_pres_1 应为 80.0, got {flat.get('inj_pres_1')}"
    assert flat.get("inj_pres_2") == 75.0, f"inj_pres_2 应为 75.0, got {flat.get('inj_pres_2')}"
    for i in range(3, 7):
        key = f"inj_pres_{i}"
        assert key in flat and flat[key] is None, f"{key} 应存在且为 None"
    print("[A3] 数组段展开 + 缺位补 None OK")

    # A4 温度段位：喷嘴与料筒 1..9 是独立字段，**不错位**
    assert flat.get("noz_temp") == 230.0, f"noz_temp 应为 230.0, got {flat.get('noz_temp')}"
    assert flat.get("brl_temp_1") == 200.0, f"brl_temp_1 应为 200.0, got {flat.get('brl_temp_1')}"
    assert flat.get("brl_temp_2") == 210.0, f"brl_temp_2 应为 210.0, got {flat.get('brl_temp_2')}"
    for i in range(3, 10):
        key = f"brl_temp_{i}"
        assert key in flat and flat[key] is None, f"{key} 应存在且为 None"
    print("[A4] 温度段位 noz_temp / brl_temp_1..9 不错位 OK")

    # A5 nested 数组字段不出现在 flat 里
    for nested_key in ("inj_pres_steps", "brl_temp_steps", "hold_time_steps"):
        assert nested_key not in flat, f"flat 不应含 nested 数组字段 {nested_key}"
    print("[A5] flat 不含 nested 数组字段 OK")

    # ---- B. infer_from_provided 响应是 flat ----
    kernel_result = {
        "param_source": "ai_recommendation",
        "matched_rules": ["DEFAULT"],
        "process": dict(NESTED_PROCESS),
        "mold_temp": {"mold_temp": 50.0},
        "hot_runner": {"valve_num": 0, "valve_time_steps": []},
    }
    with patch.object(ParameterInitializeService, "_infer_kernel", return_value=kernel_result):
        result = ParameterInitializeService.infer_from_provided(
            mold_info={}, machine_info={}, polymer_info={}
        )

    resp_process = result.get("process")
    assert isinstance(resp_process, dict), f"process 应为 dict, got {type(resp_process)}"
    assert "inj_pres_steps" not in resp_process, "响应 process 不应是 nested"
    assert resp_process.get("inj_pres_1") == 80.0, f"响应 inj_pres_1 应为 80.0, got {resp_process.get('inj_pres_1')}"
    assert resp_process.get("noz_temp") == 230.0, "响应 noz_temp 应为 230.0"
    assert resp_process.get("brl_temp_1") == 200.0, "响应 brl_temp_1 应为 200.0"
    print("[B1] infer_from_provided 响应 process 为 flat OK")

    # B2 响应 flat 与纯函数输出完全一致（单一事实来源）
    assert resp_process == flat, "响应 flat 与 process_params_to_flat 输出不一致"
    print("[B2] 响应 flat == process_params_to_flat 输出 OK")

    # B3 非工艺字段不受影响（mold_temp / hot_runner 仍是独立顶层 key）
    assert result.get("mold_temp") == {"mold_temp": 50.0}, "mold_temp 应保持独立顶层 key"
    assert "hot_runner" in result, "hot_runner 应保持独立顶层 key"
    print("[B3] mold_temp / hot_runner 保持独立顶层 key OK")

    # ---- C. 落库与响应同源 ----
    captured = {}

    def _capture_create(**kwargs):
        captured.update(kwargs)
        return MagicMock(id=999, seq_idx=1)

    with patch(
        "process.models.parameter.ProcessParameter.objects.create",
        side_effect=_capture_create,
    ), patch("process.models.tuning_record.TuningRecord.objects.create"):
        _init_mod._create_process_parameter(
            MagicMock(id=14),
            {"process": dict(NESTED_PROCESS)},
        )

    created = captured.get("process_condition")
    assert created is not None, "ProcessParameter.objects.create 未被调用"
    for key, value in flat.items():
        assert captured.get(key) == value, (
            f"落库值与响应 flat 不一致: {key} 落库={captured.get(key)} 响应={value}"
        )
    assert captured.get("param_source"), "落库应带 param_source"
    print(f"[C1] 落库 {len(flat)} 个工艺字段与响应 flat 完全一致 OK")

    print("\n=== verify_initialize_flat PASSED ===")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
