# -*- coding: utf-8 -*-
"""规则库可见性的护栏用例（**零 ORM**）。

守住的业务规则（**参照系 = 这条业务规则本身**，不是被改代码的自我复述）：

> 系统库 = 所有租户公用；每个租户有自己的私库，私库只对归属租户可见。

⚠️ **为什么输入是独立构造的**：这里手写三个 `LibraryRecord`
  （系统库 + 两个租户私库），断言的是**选库结果里的可见集合**，
  而不是某个中间计算值 ⇒ 判据一旦写反（例如把系统库按私库处理、
  或把归属租户比错），断言立刻失败。

⚠️ **零 ORM**：本模块不 import Django / `process.models` —— 可见性判据
  落在零 ORM 的共用编排层（`library/assembly.py`），因此可以在没有数据库的
  环境里断言。
"""

from process.algorithms.fuzzy.library.assembly import RuleAssembler
from process.algorithms.fuzzy.library.contracts import (
    LibraryRecord,
    RuleQueryContext,
)


def _index():
    """三个独立构造的库：系统库 + 公司 1 私库 + 公司 9 私库。"""
    return {
        'sys': [LibraryRecord(
            library_code='sys', library_name='系统库', library_type='fuzzy',
            priority=100, owner_type='system', company_id=11, library_id=1)],
        'c1': [LibraryRecord(
            library_code='c1', library_name='公司1私库', library_type='fuzzy',
            priority=200, owner_type='tenant', company_id=1, library_id=2)],
        'c9': [LibraryRecord(
            library_code='c9', library_name='公司9私库', library_type='fuzzy',
            priority=200, owner_type='tenant', company_id=9, library_id=3)],
    }


def _dup_code_index():
    """**同码两库**：公司 1 与公司 9 各有一个 `rule_miner` 挖掘私库。

    ⚠️ 库编码是业务分类编码，**跨租户可重复** ⇒ 同码多库是合法状态
      （典型场景：各租户各有一个挖掘规则私库）。
    """
    return {
        'rule_miner': [
            LibraryRecord(
                library_code='rule_miner', library_name='公司1挖掘库',
                library_type='fuzzy', priority=0, owner_type='tenant',
                company_id=1, library_id=101),
            LibraryRecord(
                library_code='rule_miner', library_name='公司9挖掘库',
                library_type='fuzzy', priority=0, owner_type='tenant',
                company_id=9, library_id=102),
        ],
    }


def _visible_codes(company_id, index=None):
    """某租户可见的库编码集合（`company_id=None` = 无租户上下文）。"""
    context = RuleQueryContext(defect_name='SHORTSHOT', company_id=company_id)
    return {lib.library_code
            for lib in RuleAssembler.select_libraries(
                None, index if index is not None else _index(), context)}


def _visible_keys(company_id, index):
    """某租户可见的**库身份**集合（`(库编码, 库主键)`）—— 同码时可区分。"""
    context = RuleQueryContext(defect_name='SHORTSHOT', company_id=company_id)
    return {(lib.library_code, lib.library_id)
            for lib in RuleAssembler.select_libraries(None, index, context)}


def test_private_library_visible_only_to_owning_tenant():
    """系统库人人可见；租户私库只对归属租户可见。

    ⚠️ **业务规则**：系统库是全平台公用资产；租户私库（含从私库晋升
      之前的挖掘经验）只对归属租户生效 ⇒ 别家租户不能吃到。
    """
    # 公司 1：看得到系统库 + 自己的私库，看不到公司 9 的私库
    assert _visible_codes(1) == {'sys', 'c1'}
    # 公司 9：看得到系统库 + 自己的私库，看不到公司 1 的私库
    assert _visible_codes(9) == {'sys', 'c9'}
    # 系统演示公司：只有系统库（系统库里没有它的私库）
    assert _visible_codes(11) == {'sys'}
    # ⚠️ **无租户上下文 ⇒ 不过滤**（第三方集成 / 离线 runner / examples 导出）
    #    ⇒ 保持现状全量，不改变既有行为
    assert _visible_codes(None) == {'sys', 'c1', 'c9'}


def test_same_code_libraries_are_kept_and_split_by_owner():
    """同码两库（各归各租户）**都要留下，且各看各的**。

    ⚠️ **业务规则**：库编码是业务分类编码，跨租户可重复 ⇒ 同码多库是合法状态。
      若索引按编码去重（只留第一条），别家的库会**静默消失** ——
      它库里的规则不报错、只是不参与推理 ⇒ 租户看不到自己的挖掘经验。

    ⚠️ 判据是**库身份**（编码 + 主键）：同码时只看编码无法区分谁是谁。
    """
    index = _dup_code_index()
    # 公司 1 看得到自己的挖掘库，看不到公司 9 的
    assert _visible_keys(1, index) == {('rule_miner', 101)}
    # 公司 9 同理
    assert _visible_keys(9, index) == {('rule_miner', 102)}
    # ⚠️ **无租户上下文 ⇒ 不过滤** ⇒ 两个同码库都在（保持现状全量）
    assert _visible_keys(None, index) == {
        ('rule_miner', 101), ('rule_miner', 102)}
