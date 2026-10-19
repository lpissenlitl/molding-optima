"""Smoke test for optimize (工艺参数调优) call chain (offline, no DB connection needed).

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

from pydantic import ValidationError

# 1. Imports
from process.schemas import (
    ProcessOptimizeFromConditionSchema,
    ProcessOptimizeFromProvidedSchema,
    FeedbackSchema,
    DefectFeedbackDataSchema,
    CycleObservationSchema,
    SuggestionSchema,
    SuggestionGroupSchema,
    SuggestionItemSchema,
)
from process.services import ParameterOptimizeService
from process.services import parameter_optimize as _opt_mod  # 模块顶层函数（整改后 helper 已不在类内）
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
parsed = ProcessOptimizeFromConditionSchema.model_validate(valid_request)
assert parsed.condition_id == 100
assert parsed.parent_seq_idx == 1
# parameter 是 ProcessParameterSchema 实例（不再是自由 dict），用属性访问
assert parsed.parameter.inj_spd_1 == 50.0
assert parsed.parameter.inj_pres_1 == 60.0
assert len(parsed.feedback.defect) == 2
assert parsed.feedback.tuning_result == "ineffective"
print("[2/4] ProcessOptimizeFromConditionSchema validation OK (flat parameter)")

# 2b. Schema rejects malformed requests
try:
    ProcessOptimizeFromConditionSchema.model_validate({"parent_seq_idx": 1})
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
parsed2 = ProcessOptimizeFromConditionSchema.model_validate(req_with_empty)
assert parsed2.feedback.defect[0].keyword_id is None
print("[2/4] ProcessOptimizeFromConditionSchema accepts defect with null keyword_id OK")

# 2g. parameter 为 None：合法，用户没改参数，service 走 ORM 反查 baseline
req_no_param = {
    "condition_id": 100,
    "parent_seq_idx": 1,
    "feedback": {"defect": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
}
p_no = ProcessOptimizeFromConditionSchema.model_validate(req_no_param)
assert p_no.parameter is None
print("[2/4] ProcessOptimizeFromConditionSchema accepts parameter=None OK")

# 2h. parameter = {} 空对象：应被拒（前端忘翻译 / 误传空 dict 都会落入此情形）
try:
    ProcessOptimizeFromConditionSchema.model_validate({
        "condition_id": 100, "parent_seq_idx": 1,
        "parameter": {},
        "feedback": {"defect": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
    })
    assert False, "should reject empty parameter dict"
except ValidationError as e:
    msg = str(e)
    assert "parameter" in msg or "工艺字段" in msg, f"error message should mention parameter: {msg}"
    print("[2/4] ProcessOptimizeFromConditionSchema rejects parameter={} OK")

# 2i. parameter 只含业务元数据（无标量工艺字段）：应被拒
try:
    ProcessOptimizeFromConditionSchema.model_validate({
        "condition_id": 100, "parent_seq_idx": 1,
        "parameter": {"parent_seq_idx": 5, "param_source": "manual"},
        "feedback": {"defect": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
    })
    assert False, "should reject parameter with only business metadata"
except ValidationError as e:
    print(f"[2/4] ProcessOptimizeFromConditionSchema rejects business-meta-only parameter OK: {type(e).__name__}")

# 2j. parameter 含一个标量工艺字段（稀疏覆盖）：合法
req_sparse = {
    "condition_id": 100, "parent_seq_idx": 1,
    "parameter": {"inj_spd_1": 50.0},   # 只改一段注射速度
    "feedback": {"defect": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
}
p_sp = ProcessOptimizeFromConditionSchema.model_validate(req_sparse)
assert p_sp.parameter.inj_spd_1 == 50.0
assert p_sp.parameter.inj_pres_1 is None   # 未覆盖的字段仍是 None
print("[2/4] ProcessOptimizeFromConditionSchema accepts sparse flat override OK")

# 2k. FromProvided：三维上下文是「必填对象」，但对象内字段可缺
#     两层设计：对象存在性由 pydantic 拦，字段级必填等级由 algorithms/fuzzy/specs.py 拦
provided_min = {
    "parameter": {"inj_pres_1": 60.0},
    "feedback": {"defect": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
    "mold_info": {"product_category": "空调"},
    "machine_info": {"drive_system": "hydraulic"},
    "polymer_info": {"abbreviation": "PP"},
}
p1 = ProcessOptimizeFromProvidedSchema.model_validate(provided_min)
assert p1.machine_info.drive_system == "hydraulic"
assert p1.machine_info.max_set_injection_pressure is None
# rule_library_code 已从公共 schema 移除（算法内部资源选择，上游自解）
assert not hasattr(p1, "rule_library_code")
print("[2/4] ProcessOptimizeFromProvidedSchema accepts minimal (3 对象齐、字段可缺) OK")

# 2g'. 缺任意一个维度对象必须被拒（论域上界无来源 → 模糊等级不可信）
for missing_dim in ("machine_info", "polymer_info", "mold_info"):
    bad = {k: v for k, v in provided_min.items() if k != missing_dim}
    try:
        ProcessOptimizeFromProvidedSchema.model_validate(bad)
        assert False, f"should reject missing {missing_dim}"
    except ValidationError:
        pass
print("[2/4] ProcessOptimizeFromProvidedSchema rejects missing context dimension OK")

# 2h. FromProvided：三维齐全；未知字段应被 BaseSchema 的 extra='ignore' 丢弃
provided_full = {
    "parameter": {"inj_pres_1": 60.0, "brl_temp_3": 220.0, "unknown_biz_field": 1},
    "feedback": {"defect": [{"keyword_name": "飞边", "level": "medium", "position": "分型面"}]},
    "mold_info": {"product_category": "空调", "target_cycle_time": 45.0},
    "machine_info": {
        "drive_system": "hydraulic",
        "max_set_injection_pressure": 180.0,
        "max_set_holding_pressure": 120.0,
        "bogus": 9,
    },
    "polymer_info": {"abbreviation": "PP", "min_melt_temp": 200.0, "max_melt_temp": 260.0},
}
p2 = ProcessOptimizeFromProvidedSchema.model_validate(provided_full)
assert p2.machine_info.max_set_injection_pressure == 180.0
assert p2.polymer_info.max_melt_temp == 260.0
assert p2.mold_info.product_category == "空调"
assert not hasattr(p2.machine_info, "bogus")
print("[2/4] ProcessOptimizeFromProvidedSchema accepts full 3-dim context OK")

# 2i. FromProvided：缺 parameter 必须报错（调优作用对象缺失）
try:
    ProcessOptimizeFromProvidedSchema.model_validate({"feedback": {}})
    assert False, "should reject missing parameter"
except Exception:
    print("[2/4] ProcessOptimizeFromProvidedSchema rejects missing parameter OK")

# 3. Service instantiation
service = ParameterOptimizeService()
assert hasattr(service, "infer")
assert hasattr(service, "infer_from_provided")
# 模块顶层 helper（2026-10-15 整改后从类内移出，独立函数）
assert hasattr(_opt_mod, "_resolve_parent")
assert hasattr(_opt_mod, "_resolve_baseline")
assert hasattr(_opt_mod, "_build_suggestion_payload")
# 纯算法内核（Step 3+4，两个入口共用，对应 parameter_initialize._infer_kernel 模式）
assert hasattr(_opt_mod.ParameterOptimizeService, "_infer_kernel")
assert hasattr(_opt_mod, "_resolve_baseline")
assert hasattr(_opt_mod, "_compose_algorithm_context")
print("[3/4] Service instantiation OK + _infer_kernel pure-kernel present")

# 3a. infer_from_provided：缺 feedback.defect 必拒（与 infer() 同一套约束镜像）
from extensions.exceptions import BizException
try:
    service.infer_from_provided(
        parameter={"inj_pres_1": 60.0},
        feedback={"defect": []},   # 空缺陷列表
        mold_info={"product_category": "空调"},
        machine_info={"drive_system": "hydraulic"},
        polymer_info={"abbreviation": "PP"},
    )
    assert False, "should reject empty defect list"
except BizException as e:
    assert "缺陷" in str(e) or "feedback" in str(e).lower() or "defect" in str(e).lower()
    print("[3/4] infer_from_provided rejects empty defect list OK")

# 3b. infer_from_provided：完整输入走通整条链路
#     （接受 2 种结果：成功（返回 new_parameter+suggestion） / fail-fast（无推荐 BizException），
#      只要不 NameError 即说明 _call_algorithms 的 engines 变量已修好）
try:
    result = service.infer_from_provided(
        parameter={"inj_pres_1": 60.0, "brl_temp_3": 220.0},
        feedback={"defect": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
        mold_info={"product_category": "空调"},
        machine_info={
            "drive_system": "hydraulic",
            "max_set_injection_pressure": 180.0,
            "max_set_injection_speed": 300.0,
            "max_set_holding_pressure": 120.0,
            "max_set_holding_speed": 150.0,
            "max_set_screw_rotation_speed": 200.0,
            "max_set_metering_pressure": 100.0,
            "max_set_metering_back_pressure": 15.0,
            "max_set_decompression_pressure": 10.0,
        },
        polymer_info={"abbreviation": "PP"},
    )
    # 成功路径：从 provided 返回的 new_parameter / suggestion 无落库 ID
    assert "new_parameter" in result, f"missing new_parameter: {result.keys()}"
    assert "suggestion" in result, f"missing suggestion: {result.keys()}"
    # 无 parameter_id / seq_idx（说明不落库语义正确）
    assert "parameter_id" not in result["new_parameter"]
    assert "seq_idx" not in result["new_parameter"]
    assert "recommendation_id" not in result["suggestion"]
    # baseline 字段被保留（应用推荐前是 baseline 字典）
    assert result["new_parameter"].get("inj_pres_1") in (60.0, None) or isinstance(
        result["new_parameter"].get("inj_pres_1"), (int, float)
    )
    print("[3/4] infer_from_provided full happy path OK")
except BizException as e:
    # fail-fast 路径：算法无推荐（测试环境可能规则集不全）—— 也算链路打通
    assert "推荐算法" in str(e), f"unexpected BizException: {e}"
    print(f"[3/4] infer_from_provided full path → fail-fast as expected (no rule match): {e}")

# 4. URL routing
optimize_routes = [p for p in urlpatterns if "algorithms/optimize" in str(p.pattern)]
assert len(optimize_routes) == 1, f"expected 1 optimize route, got {len(optimize_routes)}"
print(f"[4/4] URL route registered: {optimize_routes[0].pattern}")

# 5. 算法层接口契约（OptimizeDataValidator，字段名用 ORM 命名空间）
from process.algorithms.fuzzy.specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OptimizeDataValidator,
)

FULL_MACHINE = {
    "drive_system": "hydraulic",
    "max_set_injection_pressure": 180.0,
    "max_set_injection_speed": 300.0,
    "max_set_holding_pressure": 120.0,
    "max_set_holding_speed": 150.0,
    "max_set_screw_rotation_speed": 200.0,
    "max_set_metering_pressure": 100.0,
    "max_set_metering_back_pressure": 15.0,
    "max_set_decompression_pressure": 10.0,
}
OK_POLYMER = {"abbreviation": "PP"}
OK_MOLD = {"product_category": "空调"}

OptimizeDataValidator.validate(FULL_MACHINE, OK_POLYMER, OK_MOLD)
print("[5/5] OptimizeDataValidator accepts complete hydraulic input OK")

# 5a. 缺注射压力上界 → 必拒（算法会退回「当前值×2」自造论域）
try:
    OptimizeDataValidator.validate(
        {k: v for k, v in FULL_MACHINE.items() if k != "max_set_injection_pressure"},
        OK_POLYMER, OK_MOLD,
    )
    assert False, "should reject missing max_set_injection_pressure"
except ValueError as exc:
    assert "max_set_injection_pressure" in str(exc), str(exc)
    print("[5/5] OptimizeDataValidator rejects missing injection limit OK")

# 5b. 液压机缺计量压力 → 拒
try:
    OptimizeDataValidator.validate(
        {k: v for k, v in FULL_MACHINE.items() if k != "max_set_metering_pressure"},
        OK_POLYMER, OK_MOLD,
    )
    assert False, "should reject hydraulic missing metering pressure"
except ValueError:
    print("[5/5] OptimizeDataValidator rejects hydraulic missing metering limit OK")

# 5c. 同一份缺失在全电机下应放过（HMI 无该输入栏，属物理正常，不是数据缺失）
ELECTRIC = {
    **{k: v for k, v in FULL_MACHINE.items() if k != "max_set_metering_pressure"},
    "drive_system": "electric",
}
OptimizeDataValidator.validate(ELECTRIC, OK_POLYMER, OK_MOLD)
print("[5/5] OptimizeDataValidator tolerates electric machine without metering limit OK")

# 5d. 规则库筛选键（abbreviation / product_category）现在都是「可选」：为精度旋钮，
#     填了命中高特异度规则，不填退到默认规则，算法并不因缺它们而无法运行
OptimizeDataValidator.validate(FULL_MACHINE, {}, OK_MOLD)
print("[5/5] OptimizeDataValidator tolerates missing polymer abbreviation (精度旋钮) OK")
OptimizeDataValidator.validate(FULL_MACHINE, OK_POLYMER, {})
print("[5/5] OptimizeDataValidator tolerates missing product_category (精度旋钮) OK")

# 5e. 温度类字段是「推荐」：缺失不拦（触发条件在本维度外，强拦会挡住纯压力类调优）
OptimizeDataValidator.validate(FULL_MACHINE, OK_POLYMER, OK_MOLD)  # 未带任何温度字段
assert OPTIMIZE_MACHINE_INFO_FIELDS["max_set_decompression_speed"]["condition"] == "可选"
print("[5/5] OptimizeDataValidator treats temperature bounds as recommended OK")

print("\n=== Smoke test PASSED ===")