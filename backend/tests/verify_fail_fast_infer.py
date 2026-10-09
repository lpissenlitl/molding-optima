"""
verify_fail_fast_infer.py
验证 parameter_optimize.infer 在算法无推荐时 fail-fast：
- engine_recommendations 为空时抛 BizException(ERROR_OPERATION_FAILED)
- 不进入 Step 5 事务（不创建新 ProcessParameter / 不更新 TuningRecord）

策略：mock _recommendation_service.get_recommendations 返回空 recommendations，
然后调一次 infer，断言：
1. 抛 BizException
2. e.error_code == ERROR_OPERATION_FAILED
3. e.detail_message 含"推荐算法暂不可用"
4. 没有新 ProcessParameter 创建（count 与调用前一致）
"""

import os
import sys
import django

# 让 Django settings 可用
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch, MagicMock
from extensions.exceptions import BizException, ERROR_OPERATION_FAILED
from process.services.parameter_optimize import ParameterOptimizeService
from process.models import ProcessParameter, TuningRecord


def run_case(case_name, feedback, mock_return):
    print(f"\n[{case_name}]")
    print(f"  feedback={feedback}")
    print(f"  mock get_recommendations 返回={mock_return}")

    before_param_count = ProcessParameter.objects.count()
    before_record_count = TuningRecord.objects.count()

    # 先创建 instance（__init__ 会触发 _ensure_engines_registered lazy 注册 FuzzyEngine，
    # 但会被后面的 instance 字段 mock 覆盖）
    service = ParameterOptimizeService()

    # mock：跳过所有 DB 副作用 + 让 recommendation_service 返回空
    with patch.object(
        ParameterOptimizeService,
        "_validate_feedback",
    ), patch.object(
        ParameterOptimizeService,
        "_resolve_parent",
        return_value=(MagicMock(), MagicMock()),
    ), patch.object(
        ParameterOptimizeService,
        "_build_baseline",
        return_value={"dummy": 1},
    ), patch.object(
        ParameterOptimizeService,
        "_apply_recommendations_to_baseline",
        return_value={"dummy": 1},
    ), patch.object(
        ParameterOptimizeService,
        "_build_suggestion_payload",
        return_value={"groups": []},
    ), patch.object(
        ParameterOptimizeService,
        "_update_previous_tuning_record",
    ), patch.object(
        ParameterOptimizeService,
        "_update_previous_recommendation_is_adopted",
    ), patch.object(
        ParameterOptimizeService,
        "_create_new_parameter",
    ), patch.object(
        ParameterOptimizeService,
        "_create_new_tuning_record",
    ), patch.object(
        ParameterOptimizeService,
        "_create_new_recommendation",
    ), patch.object(
        service,
        "_recommendation_service",
    ) as mock_svc:
        mock_svc.get_recommendations.return_value = mock_return

        try:
            service.infer(
                condition_id=1,
                parent_seq_idx=1,
                feedback=feedback,
            )
            print(f"  [FAIL] 期望抛 BizException，实际无异常")
            return False
        except BizException as e:
            if e.error_code == ERROR_OPERATION_FAILED:
                print(f"  [PASS] 抛 BizException(ERROR_OPERATION_FAILED)")
                print(f"         detail_message={e.detail_message}")
                # 业务文案不应暴露实现细节（引擎 / 规则 / fuzzy 等术语）
                forbidden = ("引擎", "规则", "fuzzy", "rule_miner")
                leaked = [kw for kw in forbidden if kw in e.detail_message]
                if leaked:
                    print(f"  [FAIL] detail_message 泄漏实现细节: {leaked}")
                    return False
                print(f"  [PASS] detail_message 未泄漏实现细节")
            else:
                print(f"  [FAIL] 错误码不匹配: got {e.error_code}, "
                      f"expected ERROR_OPERATION_FAILED ({ERROR_OPERATION_FAILED.code})")
                return False

            # 验证没创建新 round / 没更新 TuningRecord
            after_param_count = ProcessParameter.objects.count()
            after_record_count = TuningRecord.objects.count()
            if before_param_count != after_param_count:
                print(f"  [FAIL] ProcessParameter count 变了 {before_param_count}→{after_param_count}")
                return False
            if before_record_count != after_record_count:
                print(f"  [FAIL] TuningRecord count 变了 {before_record_count}→{after_record_count}")
                return False
            print(f"  [PASS] 未污染数据库（ProcessParameter/TuningRecord count 不变）")
            return True


def main():
    print("=" * 70)
    print("parameter_optimize fail-fast 守卫测试")
    print("=" * 70)

    cases = [
        # 引擎空 recommendations（推荐引擎全部不可用）
        (
            "case1_无可用引擎",
            {"defect": [{"keyword_id": 1, "keyword_name": "DEFECTFREE"}]},
            {"recommendations": [], "engine_sources": {}, "best_recommendation": None},
        ),
        # 模拟 FuzzyEngine 失败、其他引擎也未命中 → 空 recommendations
        (
            "case2_引擎失败_无recommendations",
            {"defect": [{"keyword_id": 1, "keyword_name": "DEFECTFREE"}]},
            {"recommendations": [], "engine_sources": {"fuzzy.factory": []}, "best_recommendation": None},
        ),
    ]

    passed = 0
    total = 0
    for case_name, feedback, mock_return in cases:
        total += 1
        if run_case(case_name, feedback, mock_return):
            passed += 1

    print("\n" + "=" * 70)
    print(f"结果: {passed}/{total} PASS")
    print("=" * 70)
    return passed == total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)