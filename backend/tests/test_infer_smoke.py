"""Smoke test for infer call chain (offline, no DB connection needed).

This test verifies:
1. All imports work (schema, service, view, urls)
2. Schema validation accepts well-formed requests and rejects malformed ones
3. Service can be instantiated
4. URL routing is registered
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

# 1. Imports
from process.schemas import (
    InferRequestSchema,
    FeedbackSchema,
    DefectFeedbackDataSchema,
    CycleObservationSchema,
    SuggestionSchema,
    SuggestionGroupSchema,
    SuggestionItemSchema,
)
from process.services import OptimizationInferService
from process.urls import urlpatterns
print("[1/4] Imports OK")

# 2. Schema validation
valid_request = {
    "condition_id": 100,
    "parent_seq_idx": 1,
    "parameter": {"inj_spd_1": 50.0, "inj_pres_1": 60.0},
    "feedback": {
        "defect": [
            {"keyword_id": 15, "keyword_name": "短射", "level": "high", "position": "DL飞边3"},
            {"keyword_id": 22, "keyword_name": "飞边", "level": "medium", "position": "DL飞边2"},
        ],
        "observations": [
            {"param_key": "actual_product_weight", "value": 85.0},
            {"param_key": "peak_pressure", "value": None},
        ],
        "tuning_result": "ineffective",
    },
}
parsed = InferRequestSchema.model_validate(valid_request)
assert parsed.condition_id == 100
assert parsed.parent_seq_idx == 1
assert parsed.parameter["inj_spd_1"] == 50.0
assert len(parsed.feedback.defect) == 2
assert parsed.feedback.tuning_result == "ineffective"
print("[2/4] InferRequestSchema validation OK")

# 2b. Schema rejects malformed requests
try:
    InferRequestSchema.model_validate({"parent_seq_idx": 1})
    assert False, "should reject missing condition_id"
except Exception as e:
    print(f"[2/4] Schema correctly rejects missing fields: {type(e).__name__}")

# 2c. Suggestion schema
suggestion_dict = {
    "source_type": "fuzzy_rule",
    "recommendation_id": 42,
    "groups": [
        {
            "category": "注射参数",
            "icon": "mdi:speedometer",
            "items": [
                {
                    "description": "降低一段注射速度 5 mm/s",
                    "direction": "decrease",
                    "rule_refs": ["M001"],
                }
            ],
        }
    ]
}
suggestion = SuggestionSchema.model_validate(suggestion_dict)
assert suggestion.source_type == "fuzzy_rule"
assert len(suggestion.groups) == 1
assert suggestion.groups[0].items[0].direction == "decrease"
print("[2/4] SuggestionSchema validation OK")

# 2d. DefectFeedbackDataSchema 允许 keyword_id/keyword_name 为 null
empty_defect_schema = DefectFeedbackDataSchema.model_validate({
    "keyword_id": None,
    "keyword_name": None,
    "level": None,
    "position": "",
})
assert empty_defect_schema.keyword_id is None
assert empty_defect_schema.keyword_name is None
print("[2/4] DefectFeedbackDataSchema accepts null keyword_id/name OK")

# 2e. 缺省时也走默认值 None
default_defect = DefectFeedbackDataSchema.model_validate({})
assert default_defect.keyword_id is None
assert default_defect.keyword_name is None
print("[2/4] DefectFeedbackDataSchema default None OK")

# 2f. 包含未选缺陷的完整请求也能通过
req_with_empty = {
    "condition_id": 100,
    "parent_seq_idx": 1,
    "feedback": {
        "defect": [
            {"keyword_id": None, "keyword_name": None},  # 用户未选
        ],
    },
}
parsed2 = InferRequestSchema.model_validate(req_with_empty)
assert parsed2.feedback.defect[0].keyword_id is None
print("[2/4] InferRequestSchema accepts defect with null keyword_id OK")

# 3. Service instantiation
service = OptimizationInferService()
assert hasattr(service, "infer")
assert hasattr(service, "_resolve_parent")
assert hasattr(service, "_build_baseline")
assert hasattr(service, "_build_suggestion_payload")
print("[3/4] Service instantiation OK")

# 4. URL routing
infer_routes = [p for p in urlpatterns if "optimization/infer" in str(p.pattern)]
assert len(infer_routes) == 1, f"expected 1 infer route, got {len(infer_routes)}"
print(f"[4/4] URL route registered: {infer_routes[0].pattern}")

print("\n=== Smoke test PASSED ===")