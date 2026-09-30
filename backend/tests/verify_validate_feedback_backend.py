"""Bug 1 扩展验证：_validate_feedback 单元测试（后端）

覆盖：
- defect 缺失 / 空数组 / 非 list → ERROR_REQUIRED_FIELD
- 缺 keyword_id → ERROR_REQUIRED_FIELD
- 非 DEFECTFREE：缺 level / position → ERROR_REQUIRED_FIELD
- DEFECTFREE 缺 level/position → OK
- 多项混合校验
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from extensions.exceptions import BizException, ERROR_REQUIRED_FIELD
from process.services.optimization_infer import (
    OptimizationInferService,
    _DEFECTFREE_KEYWORD_NAME,
)


print("=" * 70)
print("_validate_feedback 单元测试（后端）")
print("=" * 70)


def expect_fail(feedback: dict, expected_substr: str, case_name: str):
    try:
        OptimizationInferService._validate_feedback(feedback)
    except BizException as e:
        assert e.error_code == ERROR_REQUIRED_FIELD, (
            f"[{case_name}] expected ERROR_REQUIRED_FIELD, got {e.error_code}"
        )
        assert expected_substr in str(e), (
            f"[{case_name}] expected error contains '{expected_substr}', got '{e}'"
        )
        print(f"[PASS] {case_name}: {e}")
        return
    print(f"[FAIL] {case_name}: 应抛出 BizException 但通过了")
    sys.exit(1)


def expect_ok(feedback: dict, case_name: str):
    try:
        OptimizationInferService._validate_feedback(feedback)
        print(f"[PASS] {case_name}: 合法")
    except Exception as e:
        print(f"[FAIL] {case_name}: 不应抛错但抛了: {e}")
        sys.exit(1)


# ---------- 必填：defect 列表 ----------
expect_fail({}, "请填写缺陷反馈信息", "空 feedback")
expect_fail({"defect": None}, "请填写缺陷反馈信息", "defect 缺失")
expect_fail({"defect": []}, "请填写缺陷反馈信息", "defect 空数组")
expect_fail({"defect": "not_a_list"}, "请填写缺陷反馈信息", "defect 非 list")

# ---------- 每项格式 ----------
expect_fail({"defect": ["not_a_dict"]}, "格式错误", "defect 项非 dict")

# ---------- keyword_name 必填（后端匹配走 name，id 是冗余存） ----------
expect_fail(
    {"defect": [{"keyword_id": 15, "keyword_name": None, "level": "high", "position": "DL1"}]},
    "未选择缺陷类型",
    "缺 keyword_name",
)

# ---------- DEFECTFREE：level/position 可空 ----------
expect_ok(
    {"defect": [{"keyword_id": 999, "keyword_name": _DEFECTFREE_KEYWORD_NAME, "level": None, "position": ""}]},
    "DEFECTFREE 缺 level+position",
)
expect_ok(
    {"defect": [{"keyword_id": 999, "keyword_name": _DEFECTFREE_KEYWORD_NAME}]},
    "DEFECTFREE 完全无 level/position",
)

# ---------- 非 DEFECTFREE：level + position 必填 ----------
expect_fail(
    {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": None, "position": "DL1"}]},
    "未选择缺陷程度",
    "非 DEFECTFREE 缺 level",
)
expect_fail(
    {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": ""}]},
    "未填写缺陷位置",
    "非 DEFECTFREE 缺 position",
)
expect_fail(
    {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": "high"}]},
    "未填写缺陷位置",
    "非 DEFECTFREE 完全无 position",
)

# ---------- 多项混合校验 ----------
expect_fail(
    {
        "defect": [
            {"keyword_id": 999, "keyword_name": _DEFECTFREE_KEYWORD_NAME, "level": None, "position": ""},
            {"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": ""},  # ← 第 2 项缺 position
        ],
    },
    "第 2 项",
    "多项：第 2 项缺 position",
)
expect_fail(
    {
        "defect": [
            {"keyword_id": 999, "keyword_name": _DEFECTFREE_KEYWORD_NAME, "level": None, "position": ""},
            {"keyword_id": 15, "keyword_name": "短射", "level": None, "position": "DL1"},  # ← 第 2 项缺 level
        ],
    },
    "第 2 项",
    "多项：第 2 项缺 level",
)

# ---------- 完全合法 ----------
expect_ok(
    {
        "defect": [
            {"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL1"},
        ],
    },
    "完整合法",
)
expect_ok(
    {
        "defect": [
            {"keyword_id": 999, "keyword_name": _DEFECTFREE_KEYWORD_NAME, "level": None, "position": ""},
            {"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL1"},
        ],
    },
    "DEFECTFREE + 具体缺陷 合法",
)

print()
print("=" * 70)
print("ALL PASSED (13 个用例)")