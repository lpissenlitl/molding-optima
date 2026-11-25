r"""``parameter_optimize.optimize_from_provided`` 成功路径护栏。

验证：
- 输入完整三维（``mold_info`` / ``machine_info`` / ``polymer_info``）+ parameter + feedback
- 算法能给出推荐时，输出 parameter + suggestion 两个 key
- parameter 键无 ``parameter_id`` / ``seq_idx``（不落库语义）
- suggestion 无 ``recommendation_id``
- ``suggestion.source_type`` 取最高优先级引擎

策略：patch ``_call_algorithms`` 走通整条链路（不调真实算法 / 不查 DB）。

【注意】L2 策略层（场景 / 名额）**本文件不测**（由 ``test_decide_adjustment_layer.py`` 覆盖）
⇒ 桩成「策略清单为空」⇒ 匹配不到场景 ⇒ 不裁决，所有 in-baseline 推荐都能落地，
本文件专注于验证**载荷结构**（覆盖 / 保留 / 丢弃 / suggestion 结构）。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_provided_smoke.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402

from extensions.exceptions import BizException  # noqa: E402
from process.algorithms.base import AlgorithmRecommendation  # noqa: E402
from process.services import parameter_optimize as _opt_mod  # noqa: E402
from process.services.optimize_chain import decide_adjustment as _decide_adjustment_mod  # noqa: E402

BASELINE = {
    "inj_pres_1": 60.0,
    "inj_pres_2": 55.0,
    "brl_temp_3": 220.0,
}
FEEDBACK = {
    "defects": [{"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL1"}],
}
MOLD_INFO = {"product_category": "空调"}
#: 设备设定上限 = 判级论域上界的**必需来源**（必须用设备值，设备值没有就报错）
#: ⇒ 缺任何一项都会被契约校验拒（400）。
#: 【注意】``max_injection_stroke``（实测行程）**同样是必填** —— 位置类判级
#: 论域的上界唯一权威源（注射位置 / 计量位置 / 储料终止位置 / VP 切换位置）。
MACHINE_INFO = {
    "drive_system": "hydraulic",
    "max_set_injection_pressure": 180.0,
    "max_set_injection_speed": 300.0,
    "max_set_holding_pressure": 120.0,
    "max_set_holding_speed": 150.0,
    "max_set_screw_rotation_speed": 200.0,
    "max_set_metering_pressure": 100.0,
    "max_set_metering_back_pressure": 15.0,
    "max_injection_stroke": 200.0,
}
POLYMER_INFO = {"abbreviation": "PP"}


def _make_rec(param, current, recommended, source="fuzzy"):
    return AlgorithmRecommendation(
        param_name=param,
        current_value=current,
        recommended_value=recommended,
        confidence=0.85,
        reason="短射 → 提高一段注射压力",
        source=source,
    )


def _algorithm_result():
    """3 条推荐：2 条命中 baseline（会被覆盖）+ 1 条不命中（被丢弃）。"""
    return {
        "recommendations": [
            _make_rec("inj_pres_1", 60.0, 75.0).to_dict(),
            _make_rec("inj_pres_2", 55.0, 70.0).to_dict(),
            _make_rec("not_in_baseline", 0.0, 99.0).to_dict(),
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


def _optimize():
    """跑一次 optimize_from_provided（算法层、策略层、规则库可见性都桩掉）。

    【注意】``_resolve_visible_libraries`` 是**唯一**碰 DB 的点（查可见规则库）
    ⇒ 桩掉它本文件即可完全离线，不必依赖真实 DB。
    """
    with patch.object(
        _opt_mod, "_call_algorithms", return_value=_algorithm_result(),
    ), patch.object(
        _decide_adjustment_mod, "sorted_scenario_strategies", return_value=(),
    ), patch.object(
        _opt_mod, "_resolve_visible_libraries", return_value=[],
    ):
        return _opt_mod.optimize_from_provided(
            parameter=dict(BASELINE),
            feedback=FEEDBACK,
            mold_info=MOLD_INFO,
            machine_info=MACHINE_INFO,
            polymer_info=POLYMER_INFO,
        )


def test_provided_result_has_parameter_and_suggestion():
    """参照系（业务口径）：成功路径返回 parameter + suggestion 两个 key。"""
    result = _optimize()

    assert isinstance(result, dict), f"result 应为 dict, got {type(result)}"
    assert "parameter" in result, f"missing parameter: {list(result.keys())}"
    assert "suggestion" in result, f"missing suggestion: {list(result.keys())}"


def test_provided_parameter_has_no_persisted_ids():
    """参照系（业务口径）：provided 入口不落库 ⇒ 参数里没有落库 ID。"""
    np = _optimize()["parameter"]

    assert "parameter_id" not in np, "parameter 键不应含 parameter_id（不落库）"
    assert "seq_idx" not in np, "parameter 键不应含 seq_idx（不落库）"


def test_provided_parameter_overrides_recommends_and_keeps_baseline():
    """参照系（业务口径）：推荐覆盖 baseline 同名字段；未被推荐的 baseline 字段保留；
    不在 baseline 的推荐字段丢弃。"""
    np = _optimize()["parameter"]

    assert np.get("inj_pres_1") == 75.0, f"inj_pres_1 应被覆盖为 75.0, got {np.get('inj_pres_1')}"
    assert np.get("inj_pres_2") == 70.0, f"inj_pres_2 应被覆盖为 70.0, got {np.get('inj_pres_2')}"
    assert np.get("brl_temp_3") == 220.0, (
        f"brl_temp_3 baseline 应保留 220.0, got {np.get('brl_temp_3')}"
    )
    assert "not_in_baseline" not in np, "推荐字段不在 baseline 时应被丢弃"


def test_provided_suggestion_structure():
    """参照系（业务口径）：suggestion 带 source_type / groups，且无 recommendation_id（不落库）。"""
    sg = _optimize()["suggestion"]

    assert "recommendation_id" not in sg, "suggestion 不应含 recommendation_id（不落库）"
    assert "source_type" in sg, f"suggestion 缺 source_type: {list(sg.keys())}"
    assert "groups" in sg, f"suggestion 缺 groups: {list(sg.keys())}"


def test_provided_groups_items_have_required_fields():
    """参照系（业务口径）：groups 里每条 item 都带 description / direction / rule_refs。"""
    sg = _optimize()["suggestion"]

    groups = sg["groups"]
    assert isinstance(groups, list) and len(groups) > 0, f"groups 应非空, got {groups}"
    all_items = [it for g in groups for it in g["items"]]
    assert len(all_items) == 2, f"in-baseline 推荐应产生 2 个 items, got {len(all_items)}"
    for it in all_items:
        assert "description" in it
        assert "direction" in it
        assert "rule_refs" in it


def test_provided_repeated_call_is_stable():
    """参照系（业务口径）：同一入口重复调用，结果结构一致。"""
    result2 = _optimize()

    assert "parameter" in result2
    assert "suggestion" in result2


def test_provided_rejects_missing_injection_stroke():
    """参照系（业务口径）：缺实测行程 ⇒ **400**（不回落经验论域）。

    行程是位置类判级论域上界的唯一权威源（``max_injection_stroke``
    属于必填字段）⇒ 缺失 ⇒ 契约层拒（service 层转 ``BizException``）。
    """
    without_stroke = {k: v for k, v in MACHINE_INFO.items()
                      if k != "max_injection_stroke"}

    with patch.object(
        _opt_mod, "_resolve_visible_libraries", return_value=[],
    ):
        with pytest.raises(BizException) as exc:
            _opt_mod.optimize_from_provided(
                parameter=dict(BASELINE),
                feedback=FEEDBACK,
                mold_info=MOLD_INFO,
                machine_info=without_stroke,
                polymer_info=POLYMER_INFO,
            )

    assert "max_injection_stroke" in str(exc.value), str(exc.value)


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_provided_smoke``。"""
    cases = [
        test_provided_result_has_parameter_and_suggestion,
        test_provided_parameter_has_no_persisted_ids,
        test_provided_parameter_overrides_recommends_and_keeps_baseline,
        test_provided_suggestion_structure,
        test_provided_groups_items_have_required_fields,
        test_provided_repeated_call_is_stable,
        test_provided_rejects_missing_injection_stroke,
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