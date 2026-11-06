# -*- coding: utf-8 -*-
"""文件来源的单元测试（**不碰数据库**）。

守住的性质：

1. **零 ORM**：文件通道的模块不许 import Django / `process.models`；
2. **取数口径**：过滤（缺陷码 / 启用）与排序（priority 降、id 升）
   与数据库来源逐条一致；
3. **适用性闸门**：聚合物 / 产品两维由共用的 `matches_context` 判定；
4. **选库**：**未指定 ⇒ 全量模糊库**（停用库 / 专家库不选）、显式指定 ⇒ 只用它、
   按优先级降序；
5. **自动重载**：改了 JSON 立即生效（mtime 缓存）；
6. **同码多库**：库编码跨租户可重复 ⇒ 同码多库是合法状态，
   两个库各读各的规则文件（按库主键分文件）。
"""

import json
import os

import pytest

from process.algorithms.fuzzy.library.contracts import RuleQueryContext
from process.algorithms.fuzzy.library.files.loader import FileLibraryLoader
from process.algorithms.fuzzy.library.files.repository import FileResourceRepository


# —— 合成数据集 ————————————————————————————————————————————

LIBRARIES = {
    'schema_version': 1,
    'libraries': [
        {'library_id': 1, 'library_code': 'base', 'library_name': '基础库',
         'library_type': 'fuzzy', 'priority': 100, 'is_active': True},
        {'library_id': 2, 'library_code': 'prod_lib', 'library_name': '产品库',
         'library_type': 'fuzzy', 'priority': 10, 'is_active': True},
        {'library_id': 3, 'library_code': 'off_lib', 'library_name': '停用库',
         'library_type': 'fuzzy', 'priority': 50, 'is_active': False},
        {'library_id': 4, 'library_code': 'expert_lib', 'library_name': '专家库',
         'library_type': 'expert', 'priority': 100, 'is_active': True},
    ],
}

KEYWORDS = {
    'schema_version': 1,
    'keywords': [
        {'id': 1, 'keyword_name': 'SHORTSHOT', 'fuzzy_level': 5,
         'range_min': 0.0, 'range_max': 1.0, 'step': None},
        {'id': 2, 'keyword_name': 'IV0', 'fuzzy_level': 5,
         'range_min': 0.0, 'range_max': 120.0, 'step': 40.0},
        # 论域非法（min >= max）⇒ 应被跳过并留痕
        {'id': 3, 'keyword_name': 'BROKEN', 'fuzzy_level': 5,
         'range_min': 5.0, 'range_max': 5.0, 'step': None},
    ],
}

RULES_BASE = {
    'schema_version': 1,
    'library_code': 'base',
    'rules': [
        {'id': 30, 'defect_code': 'SHORTSHOT',
         'rule_description': 'IF SHORTSHOT_low AND IV0_low THEN IV0_add_2',
         'priority': 1, 'polymer_abbreviation': None,
         'product_category': None, 'is_active': True},
        {'id': 20, 'defect_code': 'SHORTSHOT',
         'rule_description': 'IF SHORTSHOT_high AND IV0_high THEN IV0_add_5',
         'priority': 5, 'polymer_abbreviation': None,
         'product_category': None, 'is_active': True},
        # priority=0 ⇒ 必须排在 priority=1 之后（按**原始值**排）
        {'id': 10, 'defect_code': 'SHORTSHOT',
         'rule_description': 'IF SHORTSHOT_medium THEN IV0_add_1',
         'priority': 0, 'polymer_abbreviation': None,
         'product_category': None, 'is_active': True},
        # 停用规则 ⇒ 不进候选
        {'id': 40, 'defect_code': 'SHORTSHOT',
         'rule_description': 'IF SHORTSHOT_low THEN IV0_add_9',
         'priority': 9, 'polymer_abbreviation': None,
         'product_category': None, 'is_active': False},
        # 别的缺陷 ⇒ 不进候选
        {'id': 50, 'defect_code': 'BURN',
         'rule_description': 'IF BURN_low THEN IV0_add_7',
         'priority': 9, 'polymer_abbreviation': None,
         'product_category': None, 'is_active': True},
    ],
}

RULES_PROD = {
    'schema_version': 1,
    'library_code': 'prod_lib',
    'rules': [
        {'id': 60, 'defect_code': 'SHORTSHOT',
         'rule_description': 'IF SHORTSHOT_low AND IV0_low THEN IV0_add_3',
         'priority': 1, 'polymer_abbreviation': None,
         'product_category': '碗', 'is_active': True},
        {'id': 61, 'defect_code': 'SHORTSHOT',
         'rule_description': 'IF SHORTSHOT_low AND IV0_low THEN IV0_add_4',
         'priority': 1, 'polymer_abbreviation': 'PP',
         'product_category': '碗', 'is_active': True},
    ],
}


@pytest.fixture()
def data_dir(tmp_path):
    """构造一份合成数据目录。"""
    (tmp_path / 'rules').mkdir()
    (tmp_path / 'libraries.json').write_text(
        json.dumps(LIBRARIES, ensure_ascii=False), encoding='utf-8')
    (tmp_path / 'keywords.json').write_text(
        json.dumps(KEYWORDS, ensure_ascii=False), encoding='utf-8')
    (tmp_path / 'rules' / 'base.json').write_text(
        json.dumps(RULES_BASE, ensure_ascii=False), encoding='utf-8')
    (tmp_path / 'rules' / 'prod_lib.json').write_text(
        json.dumps(RULES_PROD, ensure_ascii=False), encoding='utf-8')
    return tmp_path


@pytest.fixture()
def repo(data_dir):
    return FileResourceRepository(root_dir=str(data_dir))


# —— 1) 零 ORM ————————————————————————————————————————————————

def test_file_channel_has_no_orm_dependency():
    """文件通道的模块**不许** import Django / ORM 模型。

    ⚠️ 这是「文件来源能脱离数据库跑」的**前提** —— 一旦有人在
      `loader.py` / `repository.py` 里 import 了 ORM，文件通道就会
      把 Django 拖进依赖链，脱离数据库运行的能力就没了。
    """
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ('loader.py', 'repository.py'):
        src = open(os.path.join(here, name), encoding='utf-8').read()
        assert 'process.models' not in src, '%s 引入了 ORM 模型' % name
        assert 'from django' not in src, '%s 引入了 Django' % name
        assert 'import django' not in src, '%s 引入了 Django' % name


# —— 2) 取数口径 ————————————————————————————————————————————

def test_candidate_methods_filters_and_sorts(data_dir):
    loader = FileLibraryLoader(root_dir=str(data_dir))
    records = loader.get_candidate_methods('base', 'SHORTSHOT')

    # 停用规则与别的缺陷都不进候选
    descs = [r.rule_description for r in records]
    assert 'IF SHORTSHOT_low THEN IV0_add_9' not in descs
    assert 'IF BURN_low THEN IV0_add_7' not in descs

    # 排序：priority 降序（原始值）、id 升序
    # 期望顺序：id=20(priority5) → id=30(priority1) → id=10(priority0)
    assert [r.source_ref for r in records] == [
        'file:base#20', 'file:base#30', 'file:base#10']


def test_priority_zero_sorts_last(data_dir):
    """``priority=0`` 必须排在最后 —— 排序用的是**原始值**。

    ⚠️ 若用转换后的 ``or 1.0`` 归一值排序，priority=0 会与 priority=1
      并列 ⇒ 顺序与数据库侧分叉。
    """
    loader = FileLibraryLoader(root_dir=str(data_dir))
    records = loader.get_candidate_methods('base', 'SHORTSHOT')
    assert records[-1].source_ref == 'file:base#10'
    assert records[-1].priority == 1.0   # 契约里归一为 1.0（与数据库侧一致）


def test_missing_library_file_is_empty(data_dir):
    loader = FileLibraryLoader(root_dir=str(data_dir))
    assert loader.get_candidate_methods('no_such_lib', 'SHORTSHOT') == []


# —— 3) 选库 ————————————————————————————————————————————————

def test_select_libraries_without_code_loads_all_fuzzy_libraries(repo):
    """**未指定库 ⇒ 全量模糊库**。

    ⚠️ **不按「产品类别 → 库编码」映射表选库**：该映射表指向的 code
      库里根本不存在 ⇒ 候选必然落空 ⇒ 只会加载 base 通用库。
      口径是**全部加载**，适用性交由规则级判定
      （`matches_context` / `resolve_specificity`）。

    停用库（`off_lib`）与专家库（`expert_lib`）**不在**全量口径内。
    """
    ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low')
    codes = [l.library_code for l in repo.select_libraries(ctx)]
    assert codes == ['base', 'prod_lib']      # 按 priority 降序（100 → 10）
    assert 'off_lib' not in codes             # 停用库不选
    assert 'expert_lib' not in codes          # 专家库不是模糊规则库


def test_select_libraries_explicit_code_uses_only_that_library(repo):
    """**显式指定 ⇒ 只用它**（不连带其它库）。"""
    ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low',
                           rule_library_code='base')
    codes = [l.library_code for l in repo.select_libraries(ctx)]
    assert codes == ['base']


def test_select_libraries_respects_explicit_code(repo):
    ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low',
                           rule_library_code='prod_lib')
    codes = [l.library_code for l in repo.select_libraries(ctx)]
    # 停用库不会被选中；base 作为兜底追加；按 priority 降序
    assert codes == ['base', 'prod_lib']


def test_select_libraries_excludes_inactive_lib(repo):
    ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low',
                           rule_library_code='off_lib')
    codes = [l.library_code for l in repo.select_libraries(ctx)]
    assert 'off_lib' not in codes


# —— 4) 适用性闸门 ——————————————————————————————————————————

def test_rules_apply_context_predicate(repo):
    """产品维度冲突 ⇒ 规则被排除（共用 `matches_context`）。"""
    ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low',
                           rule_library_code='prod_lib',
                           product_category='瓶')
    descs = [p.rule_description for p in repo.get_rules(ctx)]
    # 规则标了 prod='碗'，上下文 prod='瓶' ⇒ 冲突排除
    assert not any('add_3' in d or 'add_4' in d for d in descs)


def test_rules_include_matching_context(repo):
    ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low',
                           rule_library_code='prod_lib',
                           product_category='碗')
    descs = [p.rule_description for p in repo.get_rules(ctx)]
    assert any('add_3' in d for d in descs)


def test_specificity_is_relative_to_context(repo):
    """特异级是**相对当前上下文**算的，不是规则自身的属性。"""
    bare = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low')
    bare_specs = {p.specificity for p in repo.get_rules(bare)}
    assert bare_specs == {4}

    with_prod = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low',
                                 rule_library_code='prod_lib',
                                 product_category='碗')
    specs = {p.specificity for p in repo.get_rules(with_prod)}
    assert 3 in specs       # 只命中产品维 ⇒ 部分-product
    assert 4 in specs       # 通用规则 ⇒ 默认级


# —— 5) 关键字 ——————————————————————————————————————————————

def test_keywords_skip_invalid_domain(repo):
    profiles = repo.get_keywords_by_names(['SHORTSHOT', 'IV0', 'BROKEN'])
    names = [p.keyword for p in profiles]
    assert 'SHORTSHOT' in names
    assert 'IV0' in names
    assert 'BROKEN' not in names      # 论域非法 ⇒ 跳过并留痕


def test_keywords_missing_names(repo):
    assert repo.get_keywords_by_names(['__NOPE__']) == []
    assert repo.get_keywords_by_names([]) == []


# —— 6) 自动重载 ————————————————————————————————————————————

def test_auto_reload_picks_up_changes(data_dir):
    """改了 JSON 立即生效（mtime 缓存失效）。"""
    loader = FileLibraryLoader(root_dir=str(data_dir), auto_reload=True)
    before = len(loader.get_candidate_methods('base', 'SHORTSHOT'))

    payload = json.loads((data_dir / 'rules' / 'base.json').read_text(
        encoding='utf-8'))
    payload['rules'].append({
        'id': 70, 'defect_code': 'SHORTSHOT',
        'rule_description': 'IF SHORTSHOT_low THEN IV0_add_11',
        'priority': 2, 'polymer_abbreviation': None,
        'product_category': None, 'is_active': True,
    })
    (data_dir / 'rules' / 'base.json').write_text(
        json.dumps(payload, ensure_ascii=False), encoding='utf-8')

    after = len(loader.get_candidate_methods('base', 'SHORTSHOT'))
    assert after == before + 1


def test_auto_reload_disabled_keeps_cache(data_dir):
    loader = FileLibraryLoader(root_dir=str(data_dir), auto_reload=False)
    before = len(loader.get_candidate_methods('base', 'SHORTSHOT'))
    payload = json.loads((data_dir / 'rules' / 'base.json').read_text(
        encoding='utf-8'))
    payload['rules'].append({
        'id': 71, 'defect_code': 'SHORTSHOT',
        'rule_description': 'IF SHORTSHOT_low THEN IV0_add_12',
        'priority': 2, 'polymer_abbreviation': None,
        'product_category': None, 'is_active': True,
    })
    (data_dir / 'rules' / 'base.json').write_text(
        json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    after = len(loader.get_candidate_methods('base', 'SHORTSHOT'))
    assert after == before      # 关掉自动重载 ⇒ 仍是缓存内容


# —— 7) 契约 ————————————————————————————————————————————————

def test_repository_satisfies_protocol(repo):
    """文件仓库满足 `AlgorithmResourceRepository` 协议的结构。"""
    from process.algorithms.fuzzy.library.contracts import (
        AlgorithmResourceRepository,
    )
    assert isinstance(repo, AlgorithmResourceRepository)


def test_missing_data_dir_raises(data_dir):
    """数据目录缺失 ⇒ 明确报错，而不是静默返回空结果。"""
    loader = FileLibraryLoader(root_dir=str(data_dir / 'nope'))
    with pytest.raises(FileNotFoundError):
        loader.load_libraries()


# —— 8) 同码多库 ————————————————————————————————————————————

def test_same_code_libraries_read_their_own_rule_file(tmp_path):
    """**同码两库各读各的规则文件**（按库主键分文件）。

    ⚠️ **业务规则**：库编码是业务分类编码，跨租户可重复 ⇒ 同码多库是合法状态。
      若两个库读同一个 `<库码>.json` ⇒ 后写的覆盖先写的，
      文件侧只剩一个库的规则（不报错，只是结果悄悄不同）。
    """
    (tmp_path / 'rules').mkdir()
    (tmp_path / 'libraries.json').write_text(json.dumps({
        'schema_version': 1,
        'libraries': [
            {'library_id': 11, 'library_code': 'rule_miner',
             'library_name': '公司1挖掘库', 'library_type': 'fuzzy',
             'priority': 0, 'is_active': True,
             'owner_type': 'tenant', 'company_id': 1},
            {'library_id': 12, 'library_code': 'rule_miner',
             'library_name': '公司9挖掘库', 'library_type': 'fuzzy',
             'priority': 0, 'is_active': True,
             'owner_type': 'tenant', 'company_id': 9},
        ],
    }, ensure_ascii=False), encoding='utf-8')
    for lib_id, action in ((11, 'add_1'), (12, 'add_2')):
        (tmp_path / 'rules' / ('rule_miner__%s.json' % lib_id)).write_text(
            json.dumps({
                'schema_version': 1, 'library_code': 'rule_miner',
                'library_id': lib_id,
                'rules': [{'id': lib_id, 'defect_code': 'SHORTSHOT',
                           'rule_description': 'IF SHORTSHOT_low THEN IV0_%s'
                                               % action,
                           'priority': 1, 'is_active': True}],
            }, ensure_ascii=False), encoding='utf-8')

    repo = FileResourceRepository(root_dir=str(tmp_path))
    # ⚠️ 两个同码库都在索引里（不被去重掉）
    libs = repo.select_libraries(RuleQueryContext(defect_name='SHORTSHOT'))
    assert {(l.library_code, l.library_id) for l in libs} == {
        ('rule_miner', 11), ('rule_miner', 12)}

    # 各自只拿到自己那份规则（不串库）
    d1 = {p.rule_description for p in repo.get_rules(
        RuleQueryContext(defect_name='SHORTSHOT', company_id=1))}
    d9 = {p.rule_description for p in repo.get_rules(
        RuleQueryContext(defect_name='SHORTSHOT', company_id=9))}
    assert d1 == {'IF SHORTSHOT_low THEN IV0_add_1'}
    assert d9 == {'IF SHORTSHOT_low THEN IV0_add_2'}