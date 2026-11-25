# -*- coding: utf-8 -*-
r"""合格态走 **optimize 接口** 的链路护栏。

契约来源：``docs/optimize-api-contract.md`` §5.2 ——
「**合格态不短路** —— 与其它评价档位走同一条链路（推理 → 落库 → 建新轮次），
响应形状与 §5.1 完全相同」。

覆盖：
1. 合格态（``feedback.tuning_result == 'qualified'``，无缺陷）+ **引擎零产出**
   ⇒ **不 fail-fast**，产出真实的工艺变更（省能耗：递减步进下调注射压力）；
2. 响应里**没有** ``skipped`` 字段（短路方案的产物，已否决）；
3. 对照：非合格态 + 引擎零产出 ⇒ 仍报「推荐算法暂不可用」
   （移位 fail-fast **不误伤**非合格态）；
4. ⚠️ **已知缺口**（``docs/qualified-tuning-boundary.md`` §6 R5）：引擎零产出
   ⇒ ``suggestion.groups`` 为空 ⇒ **场景自带候选产生的变更没有建议条目**
   ⇒ 前端硬校验会弹「推荐算法暂不可用」。此处**如实钉住现状**。

策略：桩 ``_call_algorithms`` 为**零产出**（模拟合格态下缺陷驱动引擎全沉默）；
**不桩** ``sorted_scenario_strategies``（要真实命中 ``qualified_efficiency``）。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_qualified_optimize_path.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402

from extensions.exceptions import BizException  # noqa: E402
from process.services import parameter_optimize as _opt_mod  # noqa: E402
from process.services.optimize_chain.anchors import STEP_DOWN_RATIO  # noqa: E402

#: 基线：一段注射压力 60（合格态省能耗的调机对象）
BASELINE = {
    "inj_pres_1": 60.0,
    "inj_pres_2": 55.0,
    "brl_temp_3": 220.0,
}
#: 合格态反馈：**无缺陷** + 明确说合格（判据源 = ``feedback.tuning_result``）
QUALIFIED_FEEDBACK = {
    "defects": [],
    "tuning_result": "qualified",
}
#: 对照用反馈：有缺陷 + **非合格** ⇒ 引擎零产出时应当被拒（不误伤非合格态）
DEFECT_FEEDBACK = {
    "defects": [{"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL1"}],
    "tuning_result": "unqualified",
}
MOLD_INFO = {"product_category": "空调"}
#: 设备设定上限 = 判级论域上界的**必需来源**（缺任何一项都会被契约校验拒）
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

#: 引擎零产出（合格态下缺陷驱动引擎全沉默的真实形态）
_SILENT_ALGORITHM_RESULT = {
    "recommendations": [],
    "algorithm_sources": {},
    "best_recommendation": None,
}


def _optimize(feedback):
    """跑一次 ``optimize_from_provided``（引擎桩成零产出，规则库可见性离线）。"""
    with patch.object(
        _opt_mod, "_call_algorithms", return_value=dict(_SILENT_ALGORITHM_RESULT),
    ), patch.object(
        _opt_mod, "_resolve_visible_libraries", return_value=[],
    ):
        return _opt_mod.optimize_from_provided(
            parameter=dict(BASELINE),
            feedback=dict(feedback),
            mold_info=MOLD_INFO,
            machine_info=MACHINE_INFO,
            polymer_info=POLYMER_INFO,
        )


def test_qualified_does_not_fail_fast_when_engines_are_silent():
    """合格态 + 引擎零产出 ⇒ **不 fail-fast**，仍能产出工艺变更。

    【注意】这是「合格态不短路」契约的**核心守卫** —— 移位 fail-fast 之后，
    合格态的产出**不再依赖 L1 有没有出声**：候选由场景自带（``candidate_params``），
    目标值由口径解算（``step_down``）。
    """
    result = _optimize(QUALIFIED_FEEDBACK)

    # 有真实的工艺变更：注射压力按递减步进下调（省能耗）
    assert result["parameter"]["inj_pres_1"] == pytest.approx(
        60.0 * (1 - STEP_DOWN_RATIO)
    ), result["parameter"].get("inj_pres_1")
    # 方向是「降」—— 合格态省能耗，不是加压
    assert result["parameter"]["inj_pres_1"] < BASELINE["inj_pres_1"]
    # 别的参数不动（合格态只降压力）
    assert result["parameter"]["inj_pres_2"] == pytest.approx(55.0)
    assert result["parameter"]["brl_temp_3"] == pytest.approx(220.0)


def test_qualified_response_has_no_skipped_field():
    """响应里**没有** ``skipped`` —— 合格态短路方案（已否决）的产物不得复现。

    参照系：``docs/optimize-api-contract.md`` §5.2「合格态不短路」。
    """
    result = _optimize(QUALIFIED_FEEDBACK)

    assert "skipped" not in result, list(result.keys())
    assert "skip_reason" not in result, list(result.keys())
    # 响应形状与其它档位一致（§5.1）：parameter + suggestion
    assert set(result.keys()) == {"parameter", "suggestion"}, list(result.keys())


def test_qualified_suggestion_groups_are_empty_known_gap():
    """⚠️ **已知缺口（R5）**：引擎零产出 ⇒ 没有建议条目 ⇒ ``groups`` 为空。

    【注意】**场景自带候选产生的变更没有对应的建议条目**（``Recommendation``
    挂的是 L1 的建议；场景候选不带建议值 ⇒ 没有条目）
    ⇒ 前端硬校验 ``suggestion.groups`` 非空 ⇒ 会弹「推荐算法暂不可用」。
    ⇒ 此处**如实钉住现状**；修好 R5 后本断言会失败，提醒同步更新。
    """
    result = _optimize(QUALIFIED_FEEDBACK)

    assert result["suggestion"]["groups"] == [], (
        "引擎零产出 ⇒ 无建议条目（R5 已知缺口，修好后请同步改此断言）"
    )


def test_non_qualified_with_silent_engines_is_still_rejected():
    """对照：非合格态 + 引擎零产出 ⇒ 仍报「推荐算法暂不可用」。

    【注意】守卫「移位 fail-fast **不误伤**非合格态」—— 拒绝判据是
    **L2 零保留项**（这一轮确实没有可落地的调整），与合格态无关。
    """
    with pytest.raises(BizException) as exc:
        _optimize(DEFECT_FEEDBACK)

    assert "推荐算法暂不可用" in str(exc.value), str(exc.value)
