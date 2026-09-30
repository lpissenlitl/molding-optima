"""Bug 1 修复验证：validateFeedback 纯函数单元测试

注意：validateFeedback 是 .vue 文件 <script setup> 内的局部函数，无法直接 import。
这里复刻其逻辑到独立测试脚本，覆盖关键 case。
"""

import sys
from typing import Any, Dict, List, Optional

# 复刻 constant
DEFECTFREE_KEYWORD_NAME = "DEFECTFREE"


# 复刻 validateFeedback pure 函数（与 .vue 文件内逻辑完全一致）
def validateFeedback(feedback: Any) -> Dict[str, Any]:
    defects = feedback.get("defect") if feedback else None
    if not isinstance(defects, list) or len(defects) == 0:
        return {"ok": False, "error": "请填写缺陷反馈（至少 1 项；可选择\u201c无缺陷\u201d作为合法反馈）"}

    for i, d in enumerate(defects):
        if d is None or d.get("keyword_name") is None:
            return {"ok": False, "error": f"第 {i + 1} 项缺陷未选择缺陷类型"}

        is_defect_free = d.get("keyword_name") == DEFECTFREE_KEYWORD_NAME
        if not is_defect_free:
            level = d.get("level")
            if level is None or level == "":
                return {"ok": False, "error": f"第 {i + 1} 项缺陷未选择缺陷程度（\u201c无缺陷\u201d除外）"}
            position = d.get("position")
            if not position:  # None / 空串都视为未填
                return {"ok": False, "error": f"第 {i + 1} 项缺陷未填写缺陷位置（\u201c无缺陷\u201d除外）"}

    return {"ok": True}


# ---------- 测试用例 ----------
test_cases = [
    # (name, feedback, expect_ok, expect_error_substr)
    ("空 feedback", {}, False, "请填写缺陷反馈"),
    ("defect 缺失", {"defect": None}, False, "请填写缺陷反馈"),
    ("defect 空数组", {"defect": []}, False, "请填写缺陷反馈"),

    ("缺陷项缺 keyword_name", {"defect": [{"keyword_id": 15, "keyword_name": None, "level": "high", "position": "DL1"}]}, False, "未选择缺陷类型"),
    ("缺陷项缺 keyword_id 但有 name（id 是元数据冗余存）", {"defect": [{"keyword_id": None, "keyword_name": "短射", "level": "high", "position": "DL1"}]}, True, None),
    ("缺陷项缺 level（非 DEFECTFREE）", {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": None}]}, False, "未选择缺陷程度"),
    ("缺陷项 level 空字符串", {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": ""}]}, False, "未选择缺陷程度"),

    # DEFECTFREE 特殊项
    ("DEFECTFREE 项，level 为 null（合法）", {"defect": [{"keyword_id": 999, "keyword_name": "DEFECTFREE", "level": None}]}, True, None),
    ("DEFECTFREE 项，level 为空串（合法）", {"defect": [{"keyword_id": 999, "keyword_name": "DEFECTFREE", "level": ""}]}, True, None),

    # 多项混合
    ("多项：DEFECTFREE + 缺陷（有 level + position）", {
        "defect": [
            {"keyword_id": 999, "keyword_name": "DEFECTFREE", "level": None},
            {"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL1"},
        ],
    }, True, None),
    ("多项：第 2 项缺 level", {
        "defect": [
            {"keyword_id": 999, "keyword_name": "DEFECTFREE", "level": None},
            {"keyword_id": 15, "keyword_name": "短射", "level": None},
        ],
    }, False, "第 2 项"),
    ("多项：第 1 项缺 keyword_name", {
        "defect": [
            {"keyword_id": 15, "keyword_name": None, "level": "high", "position": "DL1"},
            {"keyword_id": 16, "keyword_name": "飞边", "level": "low"},
        ],
    }, False, "第 1 项"),

    # 完全合法：完整反馈
    ("完整合法", {
        "defect": [
            {"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL1"},
        ],
    }, True, None),

    # ---------- position 校验（新增）----------
    ("非 DEFECTFREE 缺 position", {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": "high"}]}, False, "未填写缺陷位置"),
    ("非 DEFECTFREE position 为空串", {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": ""}]}, False, "未填写缺陷位置"),
    ("非 DEFECTFREE position 为 null", {"defect": [{"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": None}]}, False, "未填写缺陷位置"),
    ("DEFECTFREE 缺 position（合法）", {"defect": [{"keyword_id": 999, "keyword_name": "DEFECTFREE", "level": None}]}, True, None),
    ("DEFECTFREE position 空串（合法）", {"defect": [{"keyword_id": 999, "keyword_name": "DEFECTFREE", "level": None, "position": ""}]}, True, None),
    ("多项：第 2 项缺 position", {
        "defect": [
            {"keyword_id": 999, "keyword_name": "DEFECTFREE", "level": None},
            {"keyword_id": 15, "keyword_name": "短射", "level": "high"},
        ],
    }, False, "第 2 项"),
]

print("=" * 70)
print("validateFeedback 单元测试")
print("=" * 70)

failed = 0
for name, feedback, expect_ok, expect_error in test_cases:
    result = validateFeedback(feedback)
    actual_ok = result["ok"]
    actual_error = result.get("error", "")

    ok_match = actual_ok == expect_ok
    error_match = True
    if expect_error and actual_ok is False:
        error_match = expect_error in actual_error

    if ok_match and error_match:
        status = "PASS"
    else:
        status = "FAIL"
        failed += 1

    print(f"[{status}] {name}")
    print(f"       expect ok={expect_ok}, actual ok={actual_ok}")
    if expect_error and not error_match:
        print(f"       expect error contains: {expect_error!r}")
        print(f"       actual error: {actual_error!r}")

print()
print("=" * 70)
print(f"通过 {len(test_cases) - failed}/{len(test_cases)}")
if failed:
    print("FAIL")
    sys.exit(1)
else:
    print("ALL PASSED")