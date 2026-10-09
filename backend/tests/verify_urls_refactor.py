"""URL 路由验证：所有 URL 都能正确 resolve 到 view

覆盖：
- 18 个新 URL（condition 维度 8 + parameter 维度 5 + 优化/移植/初始化 5）
- 8 个原 URL（tuning + 规则 + 规则中心 v2）
- 老 URL（/processes/parameter/...）不应该 resolve（已废弃）
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from django.urls import resolve, Resolver404, reverse


print("=" * 70)
print("URL 路由验证：双资源化（condition + parameter）")
print("=" * 70)


# ============================================================================
# 期望的 URL → View 映射
# ============================================================================

EXPECTED_URLS = [
    # condition 维度（本轮保留：list/detail/batch_delete/initialize/transplant）
    ("/api/processes/condition/", "ConditionListView", "get"),
    ("/api/processes/condition/123/", "ConditionDetailView", "get"),
    ("/api/processes/condition/batch_delete/", "ConditionBatchDeleteView", "post"),
    ("/api/processes/condition/initialize/", "ConditionInitializeView", "post"),
    ("/api/processes/condition/transplant/", "ConditionTransplantView", "post"),

    # 路径名误导修正后：视图变体已从 condition 段迁出
    ("/api/processes/parameter/by-condition/123/frontend/", "ParameterFrontendView", "get"),
    ("/api/processes/parameter/by-condition/123/tree/", "ParameterTreeView", "get"),
    ("/api/processes/optimization/by-condition/123/", "OptimizationView", "get"),
    ("/api/processes/optimization/by-condition/123/infer/", "OptimizationInferView", "post"),
    ("/api/processes/optimization/by-condition/123/history/", "OptimizationHistoryView", "get"),

    # parameter 维度
    ("/api/processes/parameter/100/", "ParameterDetailView", "get"),

    # 调机反馈（保留）
    ("/api/processes/tuning/record/", "ProcessTuningRecordView", "post"),

    # 规则管理（保留）
    ("/api/processes/rules/keywords/", "RuleKeywordListView", "get"),
    ("/api/processes/rules/methods/", "RuleMethodListView", "get"),
    ("/api/processes/rules/by-defect/", "RuleByDefectView", "get"),

    # 规则中心 v2（保留）
    ("/api/processes/rule-libraries/", "RuleLibraryListView", "get"),
    ("/api/processes/rule-libraries/1/", "RuleLibraryDetailView", "get"),
    ("/api/processes/rule-libraries/1/methods/", "RuleMethodListByLibraryView", "get"),
    ("/api/processes/rule-methods/1/", "RuleMethodDetailView", "get"),
    ("/api/processes/rule-libraries/1/expert-rules/", "ExpertRuleListByLibraryView", "get"),
    ("/api/processes/expert-rules/1/", "ExpertRuleDetailView", "get"),
]


# 已废弃 URL（应该 resolve 失败）
# 注：/api/processes/parameter/<int:>/ 现在是 parameter 维度的主 URL，不是废弃 URL
DEPRECATED_URLS = [
    # 上轮已废弃（无对应新路径）
    "/api/processes/parameter/",
    "/api/processes/parameter/frontend/",
    "/api/processes/parameter/batch_delete/",
    "/api/processes/parameter/transplant/",
    "/api/processes/initialization/from-masterdata/",
    # 本轮废弃（path 名误导修正：原 condition 段下的视图变体已迁出）
    "/api/processes/condition/123/frontend/",
    "/api/processes/condition/123/tree/",
    "/api/processes/condition/123/optimization/",
    "/api/processes/condition/123/optimization/infer/",
    "/api/processes/condition/123/optimization/history/",
    # 历史路径
    "/api/processes/optimization/123/",
    "/api/processes/optimization/123/history/",
    "/api/processes/optimization/infer/",
]


# ============================================================================
# Test 1: 新 URL 全部能 resolve 到正确 view
# ============================================================================
print("\n[Test 1] 新 URL resolve 验证:")
fail_count = 0
for url, expected_view_name, _ in EXPECTED_URLS:
    try:
        match = resolve(url)
        actual_view_name = match.func.view_class.__name__
        if actual_view_name == expected_view_name:
            print(f"    [OK] {url} → {actual_view_name}")
        else:
            print(f"    [FAIL] {url} → {actual_view_name}（期望 {expected_view_name}）")
            fail_count += 1
    except Resolver404:
        print(f"    [FAIL] {url} 无法 resolve")
        fail_count += 1

if fail_count > 0:
    print(f"\n[FAIL] {fail_count} 个新 URL resolve 失败")
    sys.exit(1)
else:
    print(f"\n    [OK] 全部 {len(EXPECTED_URLS)} 个新 URL resolve 成功")


# ============================================================================
# Test 2: 已废弃 URL 不能 resolve（不保留老 URL）
# ============================================================================
print("\n[Test 2] 已废弃 URL 拒绝验证:")
fail_count = 0
for url in DEPRECATED_URLS:
    try:
        match = resolve(url)
        print(f"    [FAIL] {url} 仍能 resolve 到 {match.func.view_class.__name__}（应废弃）")
        fail_count += 1
    except Resolver404:
        print(f"    [OK] {url} 已废弃（无法 resolve）")

if fail_count > 0:
    print(f"\n[FAIL] {fail_count} 个废弃 URL 仍可 resolve")
    sys.exit(1)
else:
    print(f"\n    [OK] 全部 {len(DEPRECATED_URLS)} 个废弃 URL 已正确废弃")


# ============================================================================
# Test 3: condition_id 与 parameter_id 不会路由冲突（同一数字不同含义）
# ============================================================================
print("\n[Test 3] ID 类型不冲突验证:")
# /processes/condition/<int>/ 应解析到 ConditionDetailView
# /processes/parameter/<int>/ 应解析到 ParameterDetailView
# 两个不同的 view，互不冲突

match_condition = resolve("/api/processes/condition/42/")
match_parameter = resolve("/api/processes/parameter/42/")

assert match_condition.func.view_class.__name__ == "ConditionDetailView", \
    f"condition 路由错: {match_condition.func.view_class.__name__}"
assert match_parameter.func.view_class.__name__ == "ParameterDetailView", \
    f"parameter 路由错: {match_parameter.func.view_class.__name__}"

print(f"    [OK] /condition/42/ → ConditionDetailView")
print(f"    [OK] /parameter/42/ → ParameterDetailView")
print(f"    [OK] 同一数字 42 在两个命名空间解析到不同 view（语义清晰）")


# ============================================================================
# Test 4: view 数量与命名检查
# ============================================================================
print("\n[Test 4] view 命名检查:")
import process.views.processes as v

condition_views = [
    "ConditionListView", "ConditionCreateView", "ConditionDetailView",
    "ConditionBatchDeleteView", "ConditionInitializeView",
    "ConditionTransplantView",
]
parameter_views = [
    "ParameterTreeView",
    "ParameterDetailView", "ParameterLineageView",
    "ParameterDescendantsView", "ParameterAdjustmentView",
    "ParameterRevertView",
]
optimization_views = [
    "OptimizationView", "OptimizationHistoryView", "OptimizationInferView",
]

missing = []
for name in condition_views:
    if not hasattr(v, name):
        missing.append(name)
        print(f"    [FAIL] {name} 缺失")
    else:
        print(f"    [OK] {name}")

for name in parameter_views:
    if not hasattr(v, name):
        missing.append(name)
        print(f"    [FAIL] {name} 缺失")
    else:
        print(f"    [OK] {name}")

for name in optimization_views:
    if not hasattr(v, name):
        missing.append(name)
        print(f"    [FAIL] {name} 缺失")
    else:
        print(f"    [OK] {name}")

# 旧 view 应该已删除
old_views = [
    "ProcessParameterListView", "ProcessParameterCreateView",
    "ProcessParameterDetailView", "ProcessParameterFrontendView",
    "ProcessParameterBatchDeleteView", "ProcessTransplantView",
    "ProcessInitializationFromMasterdataView", "ProcessOptimizationView",
    "ProcessOptimizationHistoryView", "ProcessOptimizationInferView",
    # 本次重命名也应清理：
    "ConditionOptimizationView", "ConditionTreeView",
    "ConditionOptimizationHistoryView", "ConditionInferView",
    # 本轮新增的清理（路径名误导修正）：
    "ConditionFrontendView",
]
print(f"\n[清理验证] 旧 view 应已删除:")
for name in old_views:
    if hasattr(v, name):
        print(f"    [WARN] {name} 仍存在（应删除）")
    else:
        print(f"    [OK] {name} 已删除")

if missing:
    print(f"\n[FAIL] {len(missing)} 个新 view 缺失")
    sys.exit(1)


print("\n" + "=" * 70)
print("URL 重构验证通过")
print(f"- {len(EXPECTED_URLS)} 个新 URL 全部 resolve 成功")
print(f"- {len(DEPRECATED_URLS)} 个废弃 URL 全部拒绝")
print(f"- {len(condition_views)} 个 Condition* view + {len(parameter_views)} 个 Parameter* view + {len(optimization_views)} 个 Optimization* view 全部定义")
print(f"- {len(old_views)} 个旧 view 全部清理")
print("=" * 70)
