# -*- coding: utf-8 -*-
r"""合格态（qualified）流程护栏。

背景：合格态产品**没有缺陷** ⇒
- 界面不要求填缺陷（前端隐藏并清空缺陷区）
- 后端照常落库（result=qualified），但提交的缺陷信息一律丢弃。

覆盖：
1. is_qualified_result：合格判定
2. upsert_tuning_record：qualified ⇒ 丢弃缺陷（即使传了）；其余档位缺陷保留
3. _record_tuning_round：qualified ⇒ 显式清空缺陷（含历史遗留，不靠 if 守卫跳过）
4. _to_algorithm_feedback：仅 qualified 允许空缺陷
5. TuningRecordRequestSchema：接受 parameter（flat 工艺字段），未传字段不落库

【注意】**不覆盖「合格态短路跳过推理」**：生产实现 ``optimize_from_condition``
的返回键里**没有** ``skipped`` / ``skip_reason`` ⇒ 「合格态不跑 fuzzy、
不建新轮次」这条语义当前**不存在于生产代码**。本文件不对它立契约
（若那是个漏掉的功能，应先确认口径再单独补契约，不在此处凭空固化）。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_qualified_flow.py -q
"""
import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch, MagicMock  # noqa: E402

from extensions.exceptions import BizException  # noqa: E402
from process.models import TuningRecord  # noqa: E402
from process.schemas.tuning import TuningRecordRequestSchema  # noqa: E402
from process.services import parameter_optimize as po  # noqa: E402
from process.services.tuning import TuningService, is_qualified_result  # noqa: E402

DEFECT = [{"keyword_name": "短射", "level": "high", "position": "DL短射1"}]
OBS = [{"param_key": "actual_product_weight", "value": 85.0}]


def test_is_qualified_result_only_accepts_qualified():
    """参照系（业务口径）：只有 'qualified' 这一档算合格。"""
    assert is_qualified_result("qualified") is True
    assert is_qualified_result("unqualified") is False
    assert is_qualified_result("effective") is False
    assert is_qualified_result(None) is False


def test_upsert_tuning_record_drops_defects_on_qualified():
    """参照系（业务口径）：合格态产品没有缺陷 ⇒ 提交的缺陷一律丢弃。"""
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


def test_upsert_tuning_record_keeps_defects_on_other_results():
    """参照系（业务口径）：非合格档位的缺陷照常写入（回归）。"""
    fake_record2 = MagicMock(result="pending", defect_feedbacks=[])
    with patch.object(TuningRecord.objects, "filter") as mf:
        mf.return_value.order_by.return_value.first.return_value = fake_record2
        TuningService.upsert_tuning_record(
            parameter=MagicMock(id=1),
            defect_feedbacks=DEFECT,
            tuning_result="unchanged",
        )

    assert fake_record2.defect_feedbacks == DEFECT, fake_record2.defect_feedbacks


def test_record_tuning_round_clears_legacy_defects_on_qualified():
    """参照系（业务口径）：先填过缺陷、后改判合格 ⇒ 历史缺陷必须被清掉。

    【注意】**必须显式置空**，不能靠 ``if defect_feedbacks:`` 守卫跳过 ——
    守卫会让空数组不写入，于是「先填过缺陷、后改判合格」时历史缺陷会残留。
    """
    fake_rec = MagicMock(result="pending", defect_feedbacks=[{"keyword_name": "气纹", "level": "low"}])
    with patch.object(TuningRecord.objects, "filter") as mf, \
            patch.object(po.Recommendation.objects, "create"):
        mf.return_value.order_by.return_value.first.return_value = fake_rec
        po._record_tuning_round(
            parent_param=MagicMock(id=1),
            changed_fields={},
            defect_feedbacks=DEFECT,
            observations=OBS,
            tuning_result="qualified",
            algorithm_recommendations=[],
            source_type="fuzzy_rule",
        )

    assert fake_rec.result == "qualified", fake_rec.result
    assert fake_rec.defect_feedbacks == [], f"合格态应清空历史缺陷，实际 {fake_rec.defect_feedbacks!r}"
    # 合格态只清缺陷，**实测观察保留**（合格与否与实测值无关）
    assert fake_rec.observations == OBS, f"合格态应保留实测观察，实际 {fake_rec.observations!r}"


def test_record_tuning_round_writes_defects_on_other_results():
    """参照系（业务口径）：非合格档位写入缺陷与实测观察（回归）。"""
    fake_rec2 = MagicMock(result="pending", defect_feedbacks=[])
    with patch.object(TuningRecord.objects, "filter") as mf, \
            patch.object(po.Recommendation.objects, "create"):
        mf.return_value.order_by.return_value.first.return_value = fake_rec2
        po._record_tuning_round(
            parent_param=MagicMock(id=1),
            changed_fields={},
            defect_feedbacks=DEFECT,
            observations=OBS,
            tuning_result="unchanged",
            algorithm_recommendations=[],
            source_type="fuzzy_rule",
        )

    assert fake_rec2.defect_feedbacks == DEFECT, fake_rec2.defect_feedbacks
    assert fake_rec2.observations == OBS, fake_rec2.observations


def test_to_algorithm_feedback_allows_empty_defects_only_on_qualified():
    """参照系（业务口径）：只有合格态允许空缺陷 —— 其余档位空缺陷一律拒。"""
    po._to_algorithm_feedback({"tuning_result": "qualified", "defects": []})   # 放行
    po._to_algorithm_feedback({"tuning_result": "qualified", "defects": DEFECT})  # 也放行

    for bad in (
        {"tuning_result": "unchanged", "defects": []},
        {"tuning_result": "unqualified", "defects": []},
        {},
    ):
        with pytest.raises(BizException):
            po._to_algorithm_feedback(bad)


def test_schema_accepts_flat_parameter():
    """参照系（业务口径）：评价接口收 flat 工艺字段（未传字段不落库）。"""
    schema = TuningRecordRequestSchema(**{
        "tuning_result": "qualified",
        "defect_feedbacks": [],
        "parameter": {"inj_pres_1": 55, "hold_t_1": 12},
    })

    dumped = schema.model_dump(exclude_none=True, by_alias=True)

    assert dumped["parameter"] == {"inj_pres_1": 55, "hold_t_1": 12}, dumped["parameter"]
    assert dumped["tuning_result"] == "qualified", dumped


def test_schema_without_parameter_only_writes_evaluation():
    """参照系（业务口径）：不传 parameter ⇒ 只写评价（向后兼容）。"""
    no_param = TuningRecordRequestSchema(**{"tuning_result": "unchanged", "defect_feedbacks": DEFECT})

    dumped = no_param.model_dump(exclude_none=True, by_alias=True)

    assert "parameter" not in dumped, dumped


def test_schema_accepts_empty_parameter_dict():
    """参照系（业务口径）：传空 dict ⇒ 不报错（语义 = 没改参数，只写评价）。"""
    empty_param = TuningRecordRequestSchema(**{"tuning_result": "qualified", "parameter": {}})

    dumped = empty_param.model_dump(exclude_none=True, by_alias=True)

    assert dumped.get("parameter", {}) == {}, dumped


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_qualified_flow``。"""
    cases = [
        test_is_qualified_result_only_accepts_qualified,
        test_upsert_tuning_record_drops_defects_on_qualified,
        test_upsert_tuning_record_keeps_defects_on_other_results,
        test_record_tuning_round_clears_legacy_defects_on_qualified,
        test_record_tuning_round_writes_defects_on_other_results,
        test_to_algorithm_feedback_allows_empty_defects_only_on_qualified,
        test_schema_accepts_flat_parameter,
        test_schema_without_parameter_only_writes_evaluation,
        test_schema_accepts_empty_parameter_dict,
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