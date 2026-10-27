"""
verify_provided_smoke.py
验证 parameter_optimize.infer_from_provided 的成功路径：
- 输入完整三维（mold_info / machine_info / polymer_info）+ parameter + feedback
- 算法能给出推荐时，输出 new_parameter + suggestion 两个 key
- new_parameter 无 parameter_id / seq_idx（不落库语义）
- suggestion 无 recommendation_id
- suggestion.source_type 取最高优先级引擎

策略：patch _call_algorithms 走通整条链路（不调真实算法 / 不查 DB），
再调一次 infer_from_provided，断言返回结构正确。
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch
from process.services import parameter_optimize as _opt_mod  # 模块顶层 helper（整改后从类内移出）
from process.services.parameter_optimize import ParameterOptimizeService
from process.algorithms.base import AlgorithmRecommendation


def _make_rec(param, current, recommended, source="fuzzy"):
    return AlgorithmRecommendation(
        param_name=param,
        current_value=current,
        recommended_value=recommended,
        confidence=0.85,
        reason="短射 → 提高一段注射压力",
        source=source,
    )


def main():
    print("=" * 70)
    print("parameter_optimize.infer_from_provided 成功路径测试")
    print("=" * 70)

    baseline = {
        "inj_pres_1": 60.0,
        "inj_pres_2": 55.0,
        "brl_temp_3": 220.0,
    }
    feedback = {
        "defect": [{"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL1"}],
    }
    mold_info = {"product_category": "空调"}
    machine_info = {
        "drive_system": "hydraulic",
        "max_set_injection_pressure": 180.0,
    }
    polymer_info = {"abbreviation": "PP"}

    # 实例化 service（保持与 view 层调用形式一致）
    service = ParameterOptimizeService()

    # 让 _call_algorithms 返回 2 条推荐：1 条匹配 baseline（会被覆盖）+ 1 条不匹配（被丢弃）
    algorithm_result = {
        "recommendations": [
            _make_rec("inj_pres_1", 60.0, 75.0).to_dict(),
            _make_rec("inj_pres_2", 55.0, 70.0).to_dict(),
            _make_rec("not_in_baseline", 0.0, 99.0).to_dict(),    # 不应进 new_parameter
        ],
        "algorithm_sources": {
            "fuzzy": [
                _make_rec("inj_pres_1", 60.0, 75.0).to_dict(),
                _make_rec("inj_pres_2", 55.0, 70.0).to_dict(),
                _make_rec("not_in_baseline", 0.0, 99.0).to_dict(),
            ],
        },
        "best_recommendation": _make_rec("inj_pres_1", 60.0, 75.0).to_dict(),
    }

    with patch.object(
        _opt_mod,
        "_call_algorithms",
        return_value=algorithm_result,
    ):
        result = service.infer_from_provided(
            parameter=baseline,
            feedback=feedback,
            mold_info=mold_info,
            machine_info=machine_info,
            polymer_info=polymer_info,
        )

    # ---- 1. 顶层结构 ----
    assert isinstance(result, dict), f"result 应为 dict, got {type(result)}"
    assert "new_parameter" in result, f"missing new_parameter: {list(result.keys())}"
    assert "suggestion" in result, f"missing suggestion: {list(result.keys())}"
    print("[1/6] 顶层结构 new_parameter + suggestion OK")

    # ---- 2. new_parameter 不含落库 ID ----
    np = result["new_parameter"]
    assert "parameter_id" not in np, "new_parameter 不应含 parameter_id（不落库）"
    assert "seq_idx" not in np, "new_parameter 不应含 seq_idx（不落库）"
    print("[2/6] new_parameter 无 parameter_id / seq_idx OK")

    # ---- 3. baseline 字段被覆盖为推荐值 ----
    assert np.get("inj_pres_1") == 75.0, f"inj_pres_1 应被覆盖为 75.0, got {np.get('inj_pres_1')}"
    assert np.get("inj_pres_2") == 70.0, f"inj_pres_2 应被覆盖为 70.0, got {np.get('inj_pres_2')}"
    # 未被推荐的 baseline 字段保留
    assert np.get("brl_temp_3") == 220.0, f"brl_temp_3 baseline 应保留 220.0, got {np.get('brl_temp_3')}"
    # 不在 baseline 的推荐值被丢弃（无 key，无 None）
    assert "not_in_baseline" not in np, "推荐字段不在 baseline 时应被丢弃"
    print("[3/6] new_parameter 推荐覆盖 + baseline 保留 + 越界字段丢弃 OK")

    # ---- 4. suggestion 结构 ----
    sg = result["suggestion"]
    assert "recommendation_id" not in sg, "suggestion 不应含 recommendation_id（不落库）"
    assert "source_type" in sg, f"suggestion 缺 source_type: {list(sg.keys())}"
    assert "groups" in sg, f"suggestion 缺 groups: {list(sg.keys())}"
    print(f"[4/6] suggestion.source_type={sg['source_type']} + 无 recommendation_id OK")

    # ---- 5. groups 含分类后的 items（2 条 in-baseline 推荐） ----
    groups = sg["groups"]
    assert isinstance(groups, list) and len(groups) > 0, f"groups 应非空, got {groups}"
    # 累加所有 group.items，确认每条都有 description / direction / rule_refs
    all_items = [it for g in groups for it in g["items"]]
    assert len(all_items) == 2, f"in-baseline 推荐应产生 2 个 items, got {len(all_items)}"
    for it in all_items:
        assert "description" in it
        assert "direction" in it
        assert "rule_refs" in it
    print(f"[5/6] groups={len(groups)} groups, items={len(all_items)} 全部含 3 字段 OK")

    # ---- 6. 实例方法形态（保持与 view 层调用一致） ----
    # 重调一次，直接通过 service 实例调（2026-10-15 二次调整后回归实例方法）
    with patch.object(
        _opt_mod,
        "_call_algorithms",
        return_value=algorithm_result,
    ):
        result2 = service.infer_from_provided(
            parameter=baseline,
            feedback=feedback,
            mold_info=mold_info,
            machine_info=machine_info,
            polymer_info=polymer_info,
        )
    assert "new_parameter" in result2
    assert "suggestion" in result2
    print("[6/6] 实例方法保持与 view 层一致 OK")

    print("\n=== verify_provided_smoke PASSED ===")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
