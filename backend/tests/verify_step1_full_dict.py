"""Step 1 边界验证：_to_full_dict（ORM → 完整 dict，不裁剪字段）

覆盖：
- _to_full_dict(None) → {}
- _to_full_dict(ORM 实例) → 含全部非关系字段（含 ORM 元数据 / 业务字段）
- _to_full_dict 排除 ORM 关系字段（避免对象嵌套 / FK _id 冲突）
- _build_condition_data 已删除（build condition 移到 Step 2 _build_engine_context）
- _serialize_parameter 已删除（Step 1 直接用 _to_full_dict）
"""

import os
import sys
from unittest.mock import MagicMock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from process.models import ProcessParameter, ProcessCondition
from process.services.parameter_optimize import (
    ParameterOptimizeService,
    _to_full_dict,
)


print("=" * 70)
print("Step 1 边界验证：_to_full_dict（ORM → 完整 dict）")
print("=" * 70)


# ---------- _to_full_dict(None) → {} ----------
result = _to_full_dict(None)
assert result == {}, f"None 应得 {{}}，得 {result}"
print(f"\n[1] _to_full_dict(None) → {{}}: OK")


# ---------- _to_full_dict(ORM 实例) → 完整字段（含元数据 / 业务字段）----------
from types import SimpleNamespace

def make_field(name, is_relation):
    return SimpleNamespace(name=name, is_relation=is_relation)

mock_param_fields = [
    make_field("id", False),
    make_field("created_at", False),
    make_field("updated_at", False),
    make_field("is_deleted", False),
    make_field("deleted_at", False),
    make_field("process_condition", True),  # FK 应被排除
    make_field("parent_param", True),  # FK 应被排除
    make_field("parameter_no", False),
    make_field("param_source", False),
    make_field("seq_idx", False),
    make_field("inj_stg", False),
    make_field("inj_spd_1", False),
]
mock_param = MagicMock()
mock_param._meta.fields = mock_param_fields
# getattr(mock_param, f.name) → mock 自动属性
result = _to_full_dict(mock_param)
# 关键验证：FK 字段（is_relation=True）被排除
expected_excluded = {"process_condition", "parent_param"}
assert not (expected_excluded & set(result.keys())), (
    f"FK 字段未排除: {result.keys() & expected_excluded}"
)
print(f"[2] FK 字段被排除: OK ({expected_excluded} 不在结果中)")

# 关键验证：非关系字段都在（含元数据 / 业务字段 / 工艺字段）
expected_included = {"id", "created_at", "is_deleted", "parameter_no", "param_source", "seq_idx", "inj_stg", "inj_spd_1"}
assert expected_included.issubset(set(result.keys())), (
    f"非关系字段缺失: {expected_included - set(result.keys())}"
)
print(f"[3] ORM 元数据 / 业务字段 / 工艺字段都保留: OK ({len(expected_included)} 项都在)")


# ---------- _serialize_parameter 已删除（Step 1 直接用 _to_full_dict）----------
from process.services import parameter_optimize as service_module

assert not hasattr(service_module.ParameterOptimizeService, "_serialize_parameter"), (
    "_serialize_parameter 应已删除（Step 1 直接用 _to_full_dict）"
)
print(f"[4] _serialize_parameter 已删除（Step 1 直接用 _to_full_dict）: OK")


# ---------- _build_condition_data 已删除（build condition 职责移到 Step 2）----------
assert not hasattr(service_module.ParameterOptimizeService, "_build_condition_data"), (
    "_build_condition_data 应已删除（build condition 移到 Step 2 _build_engine_context）"
)
assert not hasattr(service_module.ParameterOptimizeService, "_serialize_condition"), (
    "_serialize_condition 应已删除"
)
assert not hasattr(service_module.ParameterOptimizeService, "_serialize_machine"), (
    "_serialize_machine 应已删除"
)
assert not hasattr(service_module.ParameterOptimizeService, "_serialize_polymer"), (
    "_serialize_polymer 应已删除"
)
assert not hasattr(service_module.ParameterOptimizeService, "_serialize_mold"), (
    "_serialize_mold 应已删除"
)
print(f"\n[5] _build_condition_data + 4 个 _serialize_* 已删除: OK")


print()
print("=" * 70)
print("ALL PASSED")
