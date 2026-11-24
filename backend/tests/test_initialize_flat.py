r"""initialize 响应的 flat 契约护栏。

验证 initialize 响应的 flat 契约：

- initialize 的 ``result['parameter']`` 与 optimize 的 parameter **同为 flat**
- flat ↔ nested 的形态转换只在后端边界发生一次（``process_params_to_flat``），
  落库与 HTTP 响应共用同一份 flat，不会各拍一次导致语义漂移
- 温度段位语义不漂移：喷嘴（``noz_temp``）与料筒 1..9（``brl_temp_1..9``）是独立字段

不查 DB、不调真实算法：mock ``_infer_kernel`` 走通响应边界。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_initialize_flat.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import MagicMock, patch  # noqa: E402

from process.services import parameter_initialize as _init_mod  # noqa: E402
from process.services.parameter_initialize import (  # noqa: E402
    ParameterInitializeService,
    process_params_to_flat,
)

#: 算法侧的 nested 工艺参数（``ProcessParams.to_dict`` 形态）
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


def _kernel_result():
    return {
        "param_source": "ai_recommendation",
        "matched_rules": ["DEFAULT"],
        "process": dict(NESTED_PROCESS),
        "mold_temp": {"mold_temp": 50.0},
        "hot_runner": {"valve_num": 0, "valve_time_steps": []},
    }


def test_flat_maps_single_value_fields():
    """参照系（业务口径）：单值工艺字段直传到 flat。"""
    flat = process_params_to_flat(NESTED_PROCESS)

    assert flat.get("inj_t") == 1.5, f"inj_t 应为 1.5, got {flat.get('inj_t')}"
    assert flat.get("inj_stg") == 1, f"inj_stg 应为 1, got {flat.get('inj_stg')}"


def test_flat_skips_none_single_values():
    """参照系（业务口径）：单值字段为 None 时不输出该 key（与历史落库行为一致）。"""
    flat_none = process_params_to_flat({"inj_t": None, "inj_stg": 2})

    assert "inj_t" not in flat_none, f"None 单值不应输出 key, got {flat_none.get('inj_t')}"
    assert flat_none.get("inj_stg") == 2


def test_flat_expands_array_segments_with_none_padding():
    """参照系（业务口径）：数组段展开成 ``<field>_<n>``，缺位补 None（恒输出全部段位）。"""
    flat = process_params_to_flat(NESTED_PROCESS)

    assert flat.get("inj_pres_1") == 80.0, f"inj_pres_1 应为 80.0, got {flat.get('inj_pres_1')}"
    assert flat.get("inj_pres_2") == 75.0, f"inj_pres_2 应为 75.0, got {flat.get('inj_pres_2')}"
    for i in range(3, 7):
        key = f"inj_pres_{i}"
        assert key in flat and flat[key] is None, f"{key} 应存在且为 None"


def test_flat_keeps_nozzle_and_barrel_temperatures_separate():
    """参照系（业务口径）：喷嘴温度与料筒温度是独立字段，**不错位**。"""
    flat = process_params_to_flat(NESTED_PROCESS)

    assert flat.get("noz_temp") == 230.0, f"noz_temp 应为 230.0, got {flat.get('noz_temp')}"
    assert flat.get("brl_temp_1") == 200.0, f"brl_temp_1 应为 200.0, got {flat.get('brl_temp_1')}"
    assert flat.get("brl_temp_2") == 210.0, f"brl_temp_2 应为 210.0, got {flat.get('brl_temp_2')}"
    for i in range(3, 10):
        key = f"brl_temp_{i}"
        assert key in flat and flat[key] is None, f"{key} 应存在且为 None"


def test_flat_excludes_nested_array_fields():
    """参照系（业务口径）：flat 里不保留 nested 数组字段（边界只展开一次）。"""
    flat = process_params_to_flat(NESTED_PROCESS)

    for nested_key in ("inj_pres_steps", "brl_temp_steps", "hold_time_steps"):
        assert nested_key not in flat, f"flat 不应含 nested 数组字段 {nested_key}"


def test_initialize_response_parameter_is_flat():
    """参照系（业务口径）：initialize_from_provided 的响应 parameter 是 flat。"""
    with patch.object(ParameterInitializeService, "_infer_kernel", return_value=_kernel_result()):
        result = ParameterInitializeService.initialize_from_provided(
            mold_info={}, machine_info={}, polymer_info={}
        )

    resp_parameter = result.get("parameter")
    assert isinstance(resp_parameter, dict), f"parameter 应为 dict, got {type(resp_parameter)}"
    assert "inj_pres_steps" not in resp_parameter, "响应 parameter 不应是 nested"
    assert resp_parameter.get("inj_pres_1") == 80.0, (
        f"响应 inj_pres_1 应为 80.0, got {resp_parameter.get('inj_pres_1')}"
    )
    assert resp_parameter.get("noz_temp") == 230.0, "响应 noz_temp 应为 230.0"
    assert resp_parameter.get("brl_temp_1") == 200.0, "响应 brl_temp_1 应为 200.0"


def test_initialize_response_matches_flat_helper():
    """参照系（业务口径）：响应 flat 与纯函数输出完全一致（单一事实来源）。"""
    flat = process_params_to_flat(NESTED_PROCESS)

    with patch.object(ParameterInitializeService, "_infer_kernel", return_value=_kernel_result()):
        result = ParameterInitializeService.initialize_from_provided(
            mold_info={}, machine_info={}, polymer_info={}
        )

    assert result.get("parameter") == flat, "响应 flat 与 process_params_to_flat 输出不一致"


def test_initialize_keeps_non_process_top_level_keys():
    """参照系（业务口径）：非工艺字段（mold_temp / hot_runner）保持独立顶层 key。"""
    with patch.object(ParameterInitializeService, "_infer_kernel", return_value=_kernel_result()):
        result = ParameterInitializeService.initialize_from_provided(
            mold_info={}, machine_info={}, polymer_info={}
        )

    assert result.get("mold_temp") == {"mold_temp": 50.0}, "mold_temp 应保持独立顶层 key"
    assert "hot_runner" in result, "hot_runner 应保持独立顶层 key"


def test_persisted_values_match_response_flat():
    """参照系（业务口径）：落库值与响应 flat 同源 —— 不会各拍一次导致语义漂移。"""
    flat = process_params_to_flat(NESTED_PROCESS)
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


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_initialize_flat``。"""
    cases = [
        test_flat_maps_single_value_fields,
        test_flat_skips_none_single_values,
        test_flat_expands_array_segments_with_none_padding,
        test_flat_keeps_nozzle_and_barrel_temperatures_separate,
        test_flat_excludes_nested_array_fields,
        test_initialize_response_parameter_is_flat,
        test_initialize_response_matches_flat_helper,
        test_initialize_keeps_non_process_top_level_keys,
        test_persisted_values_match_response_flat,
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