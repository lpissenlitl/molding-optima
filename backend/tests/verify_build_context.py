"""Step 2 边界验证：_build_algorithm_context 按 condition 提取算法入参

设计意图：
- 工艺优化算法与工艺初始化算法对 context 的需求不同：
  - 初始化：mold_info + polymer_info + machine_info 完整 → 推导初始工艺
  - 优化：machine（HMI 设定范围）+ baseline + defect → 缺陷修正
- 故 parameter_optimize 的 _build_algorithm_context：
  - 不传 process_condition / mold / polymer 完整 dict
  - machine 按 condition.injection_index 选 InjectionUnit（全字段透传）
  - 传 polymer_abbreviation / product_category（仅用于 FuzzyEngine 规则查询）

覆盖：
- context 含 7 个关键字段（不含 process_condition / mold / polymer）
- machine 按 injection_index 选 InjectionUnit（HMI 范围字段保留）
- injection_index 越界 → {} + warning
- condition.injection_machine=None → machine={}
- polymer_abbreviation / product_category 单字段提取（含 None 安全）
- process_parameter / feedback 透传
- _build_condition_data 已删除（保留回归检查）
"""

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from process.services.parameter_optimize import (
    ParameterOptimizeService,
    _to_full_dict,
    _normalize_field_name_by_spec,
    AlgorithmContext,
    _REQUIRED_CONTEXT_KEYS,
)
from process.algorithms.fuzzy import FuzzyEngine


print("=" * 70)
print("Step 2 边界验证：_build_algorithm_context 按 condition 提取算法入参")
print("=" * 70)


def make_field(name, is_relation):
    return SimpleNamespace(name=name, is_relation=is_relation)


def make_orm_mock(fields):
    """构造 ORM mock（_meta.fields 限定 + getattr 返回 mock 自动属性）"""
    mock = MagicMock()
    mock._meta.fields = fields
    return mock


# ---------- Step 2 自负责 build condition ----------
condition_fields = [
    make_field("id", False),
    make_field("injection_index", False),  # 决定 InjectionUnit 选择
    make_field("injection_machine", True),
    make_field("polymer", True),
    make_field("mold", True),
]

# InjectionUnit 关键字段（覆盖：HMI 范围 + 设备极限 + 喷嘴/螺杆）
injection_unit_fields = [
    make_field("id", False),
    make_field("unit_code", False),
    make_field("screw_diameter", False),
    make_field("nozzle_type", False),
    make_field("max_injection_pressure", False),       # 设备极限
    make_field("max_set_injection_pressure", False),   # HMI 范围（优化核心约束）
    make_field("max_set_injection_speed", False),        # HMI 范围
    make_field("max_set_holding_pressure", False),
    make_field("max_set_holding_speed", False),
    make_field("max_set_screw_rotation_speed", False),
]

# Polymer 主表字段
polymer_fields = [
    make_field("id", False),
    make_field("abbreviation", False),
    make_field("recommended_melt_temp", False),
]

# Mold 主表字段
mold_fields = [
    make_field("id", False),
    make_field("product_category", False),
    make_field("cavity_count", False),
]


def make_injection_unit_mock(idx):
    """构造第 idx 个 InjectionUnit 的 mock"""
    m = make_orm_mock(injection_unit_fields)
    m.id = idx
    m.unit_code = f"S000{idx:03d}"
    m.screw_diameter = 55.0 + idx
    m.nozzle_type = "直通式"
    m.max_injection_pressure = 200.0
    m.max_set_injection_pressure = 180.0
    m.max_set_injection_speed = 100.0
    m.max_set_holding_pressure = 120.0
    m.max_set_holding_speed = 30.0
    m.max_set_screw_rotation_speed = 200.0
    return m


# ---------- Step 2 自负责 build condition（基础场景：injection_index=0） ----------
injection_unit_0 = make_injection_unit_mock(0)
injection_unit_1 = make_injection_unit_mock(1)
injection_unit_2 = make_injection_unit_mock(2)

machine_mock = MagicMock()
machine_mock.id = 100
machine_mock.injection_units.all.return_value = [
    injection_unit_0,
    injection_unit_1,
    injection_unit_2,
]

polymer_mock = make_orm_mock(polymer_fields)
polymer_mock.abbreviation = "ABS"
polymer_mock.recommended_melt_temp = 230.0

mold_mock = make_orm_mock(mold_fields)
mold_mock.product_category = "酒瓶"
mold_mock.cavity_count = 8

condition_mock = make_orm_mock(condition_fields)
condition_mock.injection_index = 0  # 选第一台 InjectionUnit
condition_mock.injection_machine = machine_mock
condition_mock.polymer = polymer_mock
condition_mock.mold = mold_mock

parameter_data = {"inj_stg": 2, "inj_spd_1": 50.0, "noz_temp": 220.0}
feedback = {
    "defect": [{"keyword_id": 1, "keyword_name": "短射", "level": "high", "position": "DL1"}],
    "observations": [],
    "tuning_result": "improved",
}

service = ParameterOptimizeService()
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)


# ---------- [1] context 含关键字段（不含 process_condition / mold / polymer） ----------
required_keys = {
    "machine",
    "process_parameter",
    "feedback",
    "polymer_abbreviation",
    "product_category",
}
assert required_keys.issubset(set(context.keys())), (
    f"context keys 缺关键字段: {required_keys - set(context.keys())}"
)
# 关键反向断言：优化算法不关心 mold/polymer 完整 dict 也不该有 process_condition
# 也不应有拆分后的 defect_feedbacks / observations / tuning_result（整体 feedback 透传）
forbidden_keys = {"process_condition", "mold", "polymer",
                  "defect_feedbacks", "observations", "tuning_result"}
assert not (forbidden_keys & set(context.keys())), (
    f"context 不应含这些字段: {forbidden_keys & set(context.keys())}"
)
print(f"\n[1] context 含 5 关键字段 + feedback 整体透传: OK")


# ---------- [2] machine 按 injection_index 选 InjectionUnit ----------
assert isinstance(context["machine"], dict), f"machine 应是 dict，实际 {type(context['machine'])}"
assert context["machine"]["unit_code"] == "S000000", (
    f"injection_index=0 应选第一台 (S000000)，实际 {context['machine'].get('unit_code')}"
)
# 关键 HMI 范围字段保留
critical_hmi_fields = {
    "max_set_injection_pressure",
    "max_set_injection_speed",
    "max_set_holding_pressure",
    "max_set_holding_speed",
    "max_set_screw_rotation_speed",
}
assert critical_hmi_fields.issubset(set(context["machine"].keys())), (
    f"machine 缺 HMI 范围字段: {critical_hmi_fields - set(context['machine'].keys())}"
)
print(f"[2] machine 按 injection_index=0 选 InjectionUnit（含 HMI 范围字段）: OK")


# ---------- [3] injection_index=1 → 选第二台 ----------
condition_mock.injection_index = 1
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)
assert context["machine"]["unit_code"] == "S000001", (
    f"injection_index=1 应选第二台 (S000001)，实际 {context['machine'].get('unit_code')}"
)
print(f"[3] injection_index=1 → 选第二台 InjectionUnit: OK")


# ---------- [4] injection_index 越界 → {} ----------
condition_mock.injection_index = 99
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)
assert context["machine"] == {}, f"injection_index=99 越界应得 {{}}，得 {context['machine']}"
print(f"[4] injection_index 越界（99 > 3）→ {{}} + warning: OK")


# ---------- [5] injection_index=None → 默认选第一台 ----------
condition_mock.injection_index = None
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)
assert context["machine"]["unit_code"] == "S000000", (
    f"injection_index=None 应默认选第一台，实际 {context['machine'].get('unit_code')}"
)
print(f"[5] injection_index=None → 默认选第一台 InjectionUnit: OK")


# ---------- [6] injection_machine=None → machine={} ----------
condition_mock.injection_machine = None
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)
assert context["machine"] == {}, f"None machine 应得 {{}}，得 {context['machine']}"
print(f"[6] injection_machine=None → machine={{}}: OK")


# ---------- [7] polymer_abbreviation / product_category 单字段提取 ----------
condition_mock.injection_machine = machine_mock
condition_mock.polymer = None
condition_mock.mold = None
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)
assert context["polymer_abbreviation"] is None, (
    f"polymer=None 应得 None，得 {context['polymer_abbreviation']}"
)
assert context["product_category"] is None, (
    f"mold=None 应得 None，得 {context['product_category']}"
)

condition_mock.polymer = polymer_mock
condition_mock.mold = mold_mock
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)
assert context["polymer_abbreviation"] == "ABS", (
    f"polymer.abbreviation=ABS，应得 ABS，得 {context['polymer_abbreviation']}"
)
assert context["product_category"] == "酒瓶", (
    f"mold.product_category=酒瓶，应得 酒瓶，得 {context['product_category']}"
)
print(f"[7] polymer_abbreviation / product_category 单字段提取（含 None 安全）: OK")


# ---------- [8] feedback 整体透传（process_parameter 翻译效果在 [14] 验证） ----------
condition_mock.injection_index = 0
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=parameter_data,
    feedback=feedback,
)
# feedback 整体透传（不拆分）
assert context["feedback"] == feedback, "feedback 应整体透传（不拆分为 defect_feedbacks/observations/tuning_result）"
# process_parameter 被翻译为算法侧命名（详细验证见 [14]）
expected_translated = {
    "inj_stg": 2,        # 未在 spec，原样保留
    "IV1": 50.0,         # inj_spd_1 → IV1
    "NT": 220.0,         # noz_temp → NT
}
assert context["process_parameter"] == expected_translated, (
    f"process_parameter 应被翻译为算法侧命名\n"
    f"期望 {expected_translated}\n得 {context['process_parameter']}"
)
print(f"[8] feedback 整体透传 + process_parameter 翻译生效: OK")


# ---------- [9] _build_condition_data 已删除（保留回归检查）----------
from process.services import parameter_optimize as service_module

assert not hasattr(service_module.ParameterOptimizeService, "_build_condition_data"), (
    "_build_condition_data 应已删除（build condition 移到 Step 2 _build_algorithm_context）"
)
print(f"\n[9] _build_condition_data 已删除（Step 1 不该有这个方法）: OK")


# ============================================================================
# 字段名翻译（Port-Adapter 模式）：_normalize_field_name_by_spec
# ============================================================================
# 验证：
# - [10] 空 FIELD_NAME_ALIAS → 快路径，原样输出
# - [11] 非空 FIELD_NAME_ALIAS → 按 prefix 映射正确重命名
# - [12] 无映射的字段原样保留
# - [13] 辅助过程：原对象不被修改（防御性拷贝）


# ---------- [10] 空 spec → 快路径原样输出 ----------
sample_params = {"inj_stg": 2, "inj_spd_1": 50.0, "noz_temp": 220.0}
result = _normalize_field_name_by_spec(sample_params, {})
assert result == sample_params, (
    f"空 spec 应原样输出，期望 {sample_params}，得 {result}"
)
print(f"\n[10] 空 FIELD_NAME_ALIAS → 快路径（无映射原样输出）: OK")


# ---------- [11] 非空 spec → 按 prefix 映射重命名 ----------
# 假设算法侧（fuzzy rule）使用 IL/IV/IP 缩写（HsMoldingService 场景）
spec = {"inj_pos": "IL", "inj_spd": "IV", "inj_pres": "IP"}
business_params = {
    "inj_pos_1": 25.0,
    "inj_spd_1": 50.0,
    "inj_pres_1": 80.0,
    "inj_pos_2": 35.0,
    "inj_spd_2": 30.0,
}
result = _normalize_field_name_by_spec(business_params, spec)
expected = {
    "IL1": 25.0,
    "IV1": 50.0,
    "IP1": 80.0,
    "IL2": 35.0,
    "IV2": 30.0,
}
assert result == expected, (
    f"期望 {expected}\n得 {result}"
)
print(f"[11] 非空 spec → 按 prefix 映射重命名（inj_pos_1 → IL1 等）: OK")


# ---------- [12] 完整字段名映射 + 前缀映射 + 边界 case（原样保留）----------
# 设计原则（2026-09-30）：ProcessParameter 中每个工艺字段都应在 FIELD_NAME_ALIAS 中有映射
# 本例使用“完整 spec” 模拟真实环境（包含完整映射表）。met_lim_t 是唯一边界 case。
spec = {
    # 注射
    "inj_pos":   "IL",  "inj_spd":   "IV",  "inj_pres": "IP",
    "inj_t":     "IT",  "inj_dly_t": "ID",
    # 保压
    "hold_pres": "PP",  "hold_spd": "PV",  "hold_t":   "PT",
    # 嫧胶
    "met_pos": "ML", "met_pres": "MP", "met_back_pres": "MBP",
    "met_rot_spd": "MSR", "met_end_pos": "MEL",
    # 温度
    "noz_temp": "NT", "cool_t": "CT", "brl_temp": "BT",
    # 松退
    "pre_met_decomp_dist": "DDBM", "pst_met_decomp_dist": "DDAM",
    # VP 切换
    "vps_mode": "VPTM", "vps_pos": "VPTL", "vps_pres": "VPTP",
    "vps_spd": "VPTV", "vps_t": "VPTT",
}
business_params = {
    # 完整工艺字段集（涵盖注射/保压/嫧胶/温度/松退/VP）
    "inj_pos_1": 25.0,    "inj_spd_1": 50.0,    "inj_pres_1": 80.0,
    "inj_t": 300.0,       "inj_dly_t": 0.5,
    "hold_pres_1": 50.0,  "hold_spd_1": 20.0,   "hold_t_1": 5.0,
    "met_pos_1": 40.0,    "met_pres_1": 60.0,
    "met_back_pres_1": 5.0, "met_rot_spd_1": 80.0,
    "met_end_pos": 50.0,
    "noz_temp": 220.0,    "cool_t": 15.0,
    "brl_temp_1": 230.0,
    "pre_met_decomp_dist": 5.0, "pst_met_decomp_dist": 3.0,
    "vps_pos": 5.0,       "vps_pres": 80.0,
    "met_lim_t": 8.0,     # 边界 case：算法侧未启用嫧胶延时 → 原样保留
}
result = _normalize_field_name_by_spec(business_params, spec)
expected = {
    # 完整字段名映射
    "IT": 300.0, "ID": 0.5, "MEL": 50.0,
    "NT": 220.0, "CT": 15.0,
    "DDBM": 5.0, "DDAM": 3.0,
    "VPTL": 5.0, "VPTP": 80.0,
    # 前缀 + 数字后缀映射
    "IL1": 25.0, "IV1": 50.0, "IP1": 80.0,
    "PP1": 50.0, "PV1": 20.0, "PT1": 5.0,
    "ML1": 40.0, "MP1": 60.0,
    "MBP1": 5.0, "MSR1": 80.0,
    "BT1": 230.0,
    # 边界 case（原样保留）
    "met_lim_t": 8.0,
}
assert result == expected, (
    f"完整映射表下所有工艺字段都应被翻译\n"
    f"仅 met_lim_t 为边界 case\n"
    f"期望 {expected}\n得 {result}"
)
print(f"[12] 完整映射下翻译生效 + met_lim_t 边界 case 原样保留: OK")


# ---------- [13] 原对象不被修改（防御性拷贝） ----------
original = {"inj_pos_1": 25.0, "noz_temp": 220.0}
snapshot = dict(original)
_normalize_field_name_by_spec(original, {"inj_pos": "IL", "noz_temp": "NT"})
assert original == snapshot, (
    f"原 dict 不应被修改\n期望 {snapshot}\n得 {original}"
)
print(f"[13] 原 dict 不被修改（防御性拷贝）: OK")


# ---------- [14] FuzzyEngine.FIELD_NAME_ALIAS 实际生效（验证业务→算法 真实转换） ----------
# 验证完整性：表中每个 mapping 都对应实际存在的算法 keyword（以 RuleKeyword 主数据为准则）
# 调 _build_algorithm_context 看业务字典中所有工艺字段都被翻译（仅 met_lim_t 为边界 case）
condition_mock.injection_index = 0
# 业务字段全集（涵盖注射/保压/嫧胶/温度/松退/VP）
business_params = {
    # 注射
    "inj_pos_1": 25.0, "inj_pos_2": 35.0,
    "inj_spd_1": 50.0, "inj_spd_2": 60.0,
    "inj_pres_1": 80.0, "inj_pres_2": 90.0,
    "inj_t": 300.0, "inj_dly_t": 0.5,
    # 保压
    "hold_pres_1": 50.0, "hold_spd_1": 20.0, "hold_t_1": 5.0,
    # 嫧胶
    "met_pos_1": 40.0, "met_pres_1": 60.0,
    "met_back_pres_1": 5.0, "met_rot_spd_1": 80.0,
    "met_end_pos": 50.0,
    # 温度
    "noz_temp": 220.0, "cool_t": 15.0, "brl_temp_1": 230.0,
    # 松退
    "pre_met_decomp_dist": 5.0, "pst_met_decomp_dist": 3.0,
    # VP 切换
    "vps_pos": 5.0, "vps_pres": 80.0,
    # 边界 case
    "met_lim_t": 8.0,
}
context = service._build_algorithm_context(
    condition=condition_mock,
    parameter=business_params,
    feedback=feedback,
)
expected_params = {
    # 注射
    "IL1": 25.0, "IL2": 35.0,
    "IV1": 50.0, "IV2": 60.0,
    "IP1": 80.0, "IP2": 90.0,
    "IT": 300.0, "ID": 0.5,
    # 保压
    "PP1": 50.0, "PV1": 20.0, "PT1": 5.0,
    # 嫧胶
    "ML1": 40.0, "MP1": 60.0,
    "MBP1": 5.0, "MSR1": 80.0, "MEL": 50.0,
    # 温度
    "NT": 220.0, "CT": 15.0, "BT1": 230.0,
    # 松退
    "DDBM": 5.0, "DDAM": 3.0,
    # VP 切换
    "VPTL": 5.0, "VPTP": 80.0,
    # 边界 case（原样保留）
    "met_lim_t": 8.0,
}
assert context["process_parameter"] == expected_params, (
    f"FuzzyEngine.FIELD_NAME_ALIAS 应按映射表翻译\n"
    f"期望 {expected_params}\n得 {context['process_parameter']}"
)
assert FuzzyEngine.FIELD_NAME_ALIAS, "FuzzyEngine.FIELD_NAME_ALIAS 应非空"
print(f"[14] FuzzyEngine.FIELD_NAME_ALIAS 实际生效（业务→算法 真实转换）: OK")


# ============================================================================
# Step 3 边界验证：_call_algorithms 入口验证（AlgorithmContext schema 完整性）
# ============================================================================

# ---------- [15] AlgorithmContext schema 定义验证 ----------
expected_keys = {"machine", "polymer_abbreviation", "product_category", "process_parameter", "feedback"}
assert set(AlgorithmContext.__annotations__.keys()) == expected_keys, (
    f"AlgorithmContext schema 应为 5 字段 {expected_keys}，实际 {set(AlgorithmContext.__annotations__.keys())}"
)
assert _REQUIRED_CONTEXT_KEYS == frozenset(expected_keys), (
    f"_REQUIRED_CONTEXT_KEYS 应与 AlgorithmContext schema 一致"
)
print(f"[15] AlgorithmContext schema 定义（5 字段） + _REQUIRED_CONTEXT_KEYS 同步: OK")


# ---------- [16] _call_algorithms 空 context → 返回空结构 ----------
service = ParameterOptimizeService()
result = service._call_algorithms({})  # type: ignore[arg-type]
assert result == {
    "recommendations": [],
    "algorithm_sources": {},
    "best_recommendation": None,
}, f"空 context 应返回 _empty_algorithm_result()，实际 {result}"
print(f"[16] _call_algorithms 空 context → 返回空结果（_empty_algorithm_result）: OK")


# ---------- [17] _call_algorithms 缺字段 context → 返回空结构 + warning ----------
incomplete_context = {
    "machine": {},
    "polymer_abbreviation": "ABS",
    # 缺少: product_category, process_parameter, feedback
}
result = service._call_algorithms(incomplete_context)  # type: ignore[arg-type]
expected_empty = {
    "recommendations": [],
    "algorithm_sources": {},
    "best_recommendation": None,
}
assert result == expected_empty, (
    f"缺字段 context 应返回空结构，实际 {result}"
)
# 缺哪几个字段：product_category, process_parameter, feedback
print(f"[17] _call_algorithms 缺字段 context → 返回空结构 + warning 日志: OK")


print()
print("=" * 70)
print("ALL PASSED")