r"""算法入参契约 —— **名字对齐 ORM + 对外接口能承载必填项** 护栏。

【护的是什么】
算法线（expert / fuzzy）各自持有自己的字段字典（各自的 ``specs.py``），
**互不约束字段集合** —— 两边要的东西本来就不同（expert 要设备规格推初值，
fuzzy 只要 HMI 上限当判级论域上界）。本护栏只约束**三件与算法无关、
各自独立成立**的事：

  1. **一份 spec 内部不分裂**：契约 key == attr_name
     （同一项设备能力，在一条 spec 里只能有一个名字）；
  2. **名字是 ORM 真名**：attr_name 必须是 ORM 模型的**真实属性**
     —— 真相源是 ORM，不是任何一份「字段清单」；
  3. **对外接口能承载算法必填项**：对外 schema 的字段集 ⊇ 对应算法契约的必填集
     （否则 pydantic 的 ``extra="ignore"`` 会把多传的字段**静默丢弃**
     ⇒ 调用方传不进去 ⇒ 报「缺失」，且错误信息指不出是哪一层吃掉的）。

【刻意不护什么】
- ❌ **不约束 expert 与 fuzzy 的字段集合相同** —— 那是两条算法线各自的取舍，
  拉平就等于把它们焊在一起：公共清单会变成两条线的最大公约数，
  任何一方多要一个字段都得改公共件 ⇒ 违背「算法是独立单元」。
- ❌ **不设「一份共享字段清单」当基准** —— 字段真名的真相源是 ORM；
  多维护一张表只会多一个可能漂移的地方。

【挂账机制】已知待拍板项列在下方两张清单里，并配对断言（清单 ↔ 实际状态锁死）：
拍板后从清单移除即可，护栏随即收紧。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_spec_contract_alignment.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from masterdata.models.injection import (  # noqa: E402
    InjectionMoldingMachine,
    InjectionUnit,
)
from process.algorithms.common.field_contract import derive_required_fields  # noqa: E402
from process.algorithms.expert.specs import MACHINE_INFO_FIELDS  # noqa: E402
from process.algorithms.fuzzy.specs import OPTIMIZE_MACHINE_INFO_FIELDS  # noqa: E402
from process.schemas.initialization import MachineInfoSchema  # noqa: E402
from process.schemas.optimization import OptimizeMachineInfoSchema  # noqa: E402


# 契约里写的 ``source_model``（模型名字符串）→ 真实 ORM 类
ORM_MODELS = {
    'InjectionMoldingMachine': InjectionMoldingMachine,
    'InjectionUnit': InjectionUnit,
}


# ---- 已知待拍板项（挂账：拍板后从这里移除，护栏随即收紧）------------------
# 设备极限组的 3 个别名 key：算法**不消费**（引擎 0 引用）、ORM 用 ``_speed``。
# 取舍待拍板：① 统一改成 ORM 真名 ② 直接从 spec 删除。
KNOWN_PENDING_ALIASES = {
    'max_injection_velocity',
    'max_holding_velocity',
    'max_decompression_velocity',
}

# 对外初始化接口缺 expert 契约的必填项 ``drive_system``
# （它属 InjectionMoldingMachine 主表、不是注射单元字段）——
# 要不要把它暴露到对外契约上，待拍板。
KNOWN_PENDING_SCHEMA_GAPS = {
    'drive_system',
}


def _alias_offenders(spec):
    """spec 内「契约名 != ORM 属性名」的字段（同一能力两个名字）。"""
    return {
        key: entry['attr_name']
        for key, entry in spec.items()
        if entry.get('attr_name') and key != entry['attr_name']
    }


def test_expert_spec_key_matches_attr_name():
    """expert 契约：一份 spec 内部契约名 == ORM 属性名。"""
    offenders = _alias_offenders(MACHINE_INFO_FIELDS)
    assert set(offenders) <= KNOWN_PENDING_ALIASES, offenders


def test_fuzzy_spec_key_matches_attr_name():
    """fuzzy 契约：同上（当前无待拍板项 ⇒ 必须完全干净）。"""
    offenders = _alias_offenders(OPTIMIZE_MACHINE_INFO_FIELDS)
    assert not offenders, offenders


def test_pending_aliases_still_pending():
    """挂账清单与 spec 实际状态锁死（防止清单与代码各说各话）。"""
    actual = set(_alias_offenders(MACHINE_INFO_FIELDS))
    assert actual == KNOWN_PENDING_ALIASES, sorted(actual)


def test_attr_name_is_real_orm_field():
    """真相源 = ORM：契约里的 attr_name 必须是 ORM 模型的真实属性。"""
    for label, spec in (
        ('expert', MACHINE_INFO_FIELDS),
        ('fuzzy', OPTIMIZE_MACHINE_INFO_FIELDS),
    ):
        for key, entry in spec.items():
            attr_name = entry.get('attr_name')
            if not attr_name:
                continue  # 计算字段（attr_name=None）由 service 层特殊处理
            model = ORM_MODELS[entry['source_model']]
            assert hasattr(model, attr_name), (label, key, attr_name)


def test_initialize_schema_carries_required_limit_fields():
    """对外初始化接口必须能承载算法契约的**必填上限字段**（否则被静默丢弃）。"""
    required = {
        field for field in derive_required_fields(MACHINE_INFO_FIELDS)
        if field.startswith('max_set_')
    }
    missing = required - set(MachineInfoSchema.model_fields)
    assert not missing, sorted(missing)


def test_initialize_schema_gap_is_only_drive_system():
    """挂账：对外初始化接口目前只缺 expert 必填的 drive_system（待拍板）。"""
    required = set(derive_required_fields(MACHINE_INFO_FIELDS))
    gap = required - set(MachineInfoSchema.model_fields)
    assert gap == KNOWN_PENDING_SCHEMA_GAPS, sorted(gap)


def test_optimize_schema_carries_required_fields():
    """对外调优接口必须能承载 fuzzy 契约的**全部必填项**（单向包含，不要求相等）。"""
    required = set(derive_required_fields(OPTIMIZE_MACHINE_INFO_FIELDS))
    missing = required - set(OptimizeMachineInfoSchema.model_fields)
    assert not missing, sorted(missing)


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_spec_contract_alignment``。"""
    cases = [
        test_expert_spec_key_matches_attr_name,
        test_fuzzy_spec_key_matches_attr_name,
        test_pending_aliases_still_pending,
        test_attr_name_is_real_orm_field,
        test_initialize_schema_carries_required_limit_fields,
        test_initialize_schema_gap_is_only_drive_system,
        test_optimize_schema_carries_required_fields,
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
