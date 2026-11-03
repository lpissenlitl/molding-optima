"""端到端真实 DB 复验。

生产链路的四件事必须成立：
1. 规则查询命中真实数据；
2. 返回对象类型是 fuzzy_core.profiles.RuleProfile；
3. 溯源字段是字符串 source_ref，无 ORM 实例泄漏；
4. 契约层校验（validate_rule_profiles）对真实数据通过。

另验证第 4 层（build_rule_objects）的分流与建对象结果。

运行：../.venv/Scripts/python.exe tests/_verify_e2e_db.py
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

# 本脚本位于 backend/tests/ ⇒ 向上两级 = backend 根目录
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.algorithms.fuzzy.library.contracts import RuleQueryContext  # noqa: E402
from process.algorithms.fuzzy.library.repository import (  # noqa: E402
    ResourceRepository,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    RuleProfile,
    validate_rule_profiles,
)
from process.algorithms.fuzzy.fuzzy_core.rules_filter import (  # noqa: E402
    build_rule_objects,
)
from process.models.rules import RuleMethod  # noqa: E402

ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low')
rules = ResourceRepository.get_rules(ctx)

print('=' * 68)
print('1) 命中条数 =', len(rules))
print('   类型集合 =', sorted({type(r).__name__ for r in rules}))
print('   全部是 RuleProfile =', all(isinstance(r, RuleProfile) for r in rules))

print('=' * 68)
print('2) 溯源字段 source_ref（字符串，非 ORM 实例）')
print('   样例 =', [r.source_ref for r in rules[:5]])
print('   含 RuleMethod:20 =', any(r.source_ref == 'RuleMethod:20' for r in rules))

print('=' * 68)
print('3) ORM 泄漏检查（应全为 False）')
for attr in ('method', 'id', 'rule_content', '_state'):
    leaks = [r for r in rules if hasattr(r, attr)]
    print('   hasattr(%-12s) 命中数 = %d' % (attr + ')', len(leaks)))

print('=' * 68)
print('4) 第 4 层产物（拆一次 → 分类 → 建对象）')
filtered = build_rule_objects(rules)
built = filtered.numeric_rules + filtered.mamdani_rules
print('   建出的规则对象数 =', len(built), '| 跳过 =', len(filtered.skipped))
print('   建出 + 跳过 <= 档案数 =', len(built) + len(filtered.skipped) <= len(rules))
print('   每个规则对象都带 priority（唯一来源 profile.priority）=',
      all(hasattr(r, 'profile') and hasattr(r.profile, 'priority') for r in built))
print('   priority 前 5 =', [r.profile.priority for r in built[:5]])

print('=' * 68)
print('5) 契约层校验 validate_rule_profiles（真实数据）')
try:
    validate_rule_profiles(rules)
    print('   结果 = 通过（真实 DB 数据符合内核输入契约）')
except Exception as exc:  # noqa: BLE001
    print('   结果 = 失败:', exc)

print('=' * 68)
print('6) 按结论形态分流（第 4 层唯一入口 build_rule_objects）')
print('   分流结果 =', {
    'numeric': len(filtered.numeric_rules),
    'mamdani': len(filtered.mamdani_rules),
    'advice_items': len(filtered.advice_items),
    'skipped': len(filtered.skipped),
})

print('=' * 68)
print('7) 特异级（specificity）标注自检')
print('   参照系：脚本内独立实现一遍判定（不复用 RuleService.resolve_specificity）')

import re  # noqa: E402

from django.db.models import Q  # noqa: E402


def _expected_spec(rm, ctx):
    """独立实现的特异级判定（参照系）。上下文为 None ⇒ 该维度不算匹配。"""
    poly_m = (ctx.polymer_abbreviation is not None
              and rm.polymer_abbreviation == ctx.polymer_abbreviation)
    prod_m = (ctx.product_category is not None
              and rm.product_category == ctx.product_category)
    if poly_m and prod_m:
        return 1
    if poly_m:
        return 2
    if prod_m:
        return 3
    return 4


def _rm_by_profile(profile):
    """从 source_ref（'RuleMethod:{id}'）反查 ORM 行。"""
    m = re.match(r'^RuleMethod:(\d+)$', profile.source_ref or '')
    if not m:
        return None
    return RuleMethod.objects.filter(id=int(m.group(1))).first()


CASES = [
    ('裸（poly/prod 都无）',
     dict(defect_name='SHORTSHOT', defect_level='low')),
    ('prod=碗',
     dict(defect_name='SHORTSHOT', defect_level='low', product_category='碗')),
    ('poly=PP',
     dict(defect_name='SHORTSHOT', defect_level='low',
          polymer_abbreviation='PP')),
    ('prod=碗 + poly=PP',
     dict(defect_name='SHORTSHOT', defect_level='low', product_category='碗',
          polymer_abbreviation='PP')),
    ('显式补充库 R20240516093115 + prod=碗',
     dict(defect_name='SHORTSHOT', defect_level='low',
          rule_library_code='R20240516093115', product_category='碗')),
    # ⚠️ 缺维场景：上下文没给 polymer / product ⇒ 这两维**不设限**
    #    （「未指明」≠「不适用」）⇒ 该库里的带标签规则也会进来。
    ('显式补充库 R20240516093115（无维度）',
     dict(defect_name='SHORTSHOT', defect_level='low',
          rule_library_code='R20240516093115')),
    ('显式补充库 R20240702164137（无维度）',
     dict(defect_name='SHORTSHOT', defect_level='low',
          rule_library_code='R20240702164137')),
]

spec_failures = []
for label, kw in CASES:
    c = RuleQueryContext(**kw)
    ps = ResourceRepository.get_rules(c)
    dist = {}
    for p in ps:
        dist[p.specificity] = dist.get(p.specificity, 0) + 1
    print('   %-34s 命中=%-4s spec 分布=%s'
          % (label, len(ps), dict(sorted(dist.items()))))
    for p in ps:
        rm = _rm_by_profile(p)
        if rm is None:
            spec_failures.append('%s: %s 无法反查 ORM 行' % (label, p.source_ref))
            continue
        want = _expected_spec(rm, c)
        if p.specificity != want:
            spec_failures.append(
                '%s: %s spec=%s 应为 %s（poly=%r prod=%r）'
                % (label, p.source_ref, p.specificity, want,
                   rm.polymer_abbreviation, rm.product_category))

# 业务语义硬断言：没有任何维度可匹配时，全部命中规则都只能是默认级
bare = ResourceRepository.get_rules(RuleQueryContext(
    defect_name='SHORTSHOT', defect_level='low'))
if bare and any(p.specificity != 4 for p in bare):
    spec_failures.append('裸上下文下存在非默认级（spec != 4）')

print('   标注与参照系一致 =', not spec_failures)
for msg in spec_failures[:10]:
    print('     [FAIL]', msg)

print('=' * 68)
print('8) 跨库副本去重自检')
print('   参照系：脚本内独立实现一遍选库后的取数 + 去重键 + 判优')
print('   （不复用 RuleService.dedupe_key / prefer_candidate）')


def _expected_dedup(context):
    """独立实现一遍去重，返回 {内容键: (特异级, priority, 规则串)}。

    参照系只复用一处**非本次改动**的逻辑：
    - `ResourceRepository.select_libraries`（选库）
    取数谓词、去重键、判优、编排、缺陷名闸门全部自己写一遍。

    ⚠️ **取数口径（匹配谓词）**：规则该维为 NULL（通用）或等于上下文值；
       上下文该维未知（None）⇒ 该维**不设限**；已知但不等 ⇒ **排除**（冲突排除）。
    ⚠️ 缺陷名闸门**不复用**生产代码（`RuleService.match_defect_name`）：
       它是改造落点之一，复用会让参照系与生产同源、失去校验意义。
    """

    libs = ResourceRepository.select_libraries(context)

    groups = {}
    for lib in libs:
        rows = RuleMethod.objects.filter(
            rule_library_id=lib.library_id,
            defect_code=context.defect_name,
            is_active=True,
            is_deleted=False,
        )
        if context.polymer_abbreviation is not None:
            rows = rows.filter(
                Q(polymer_abbreviation__isnull=True)
                | Q(polymer_abbreviation=context.polymer_abbreviation))
        if context.product_category is not None:
            rows = rows.filter(
                Q(product_category__isnull=True)
                | Q(product_category=context.product_category))
        for rm in rows.order_by('-priority', 'id'):
            rule_str = (rm.rule_description or '').strip()
            if not rule_str:
                continue
            # 缺陷名闸门：自己写一遍（不调生产代码，保持参照系独立）
            pre = parse_rule(rule_str)['preconditions']
            if pre and pre[0].get('name') != context.defect_name:
                continue
            spec = _expected_spec(rm, context)
            # 独立写的去重键：内容键 = (缺陷码, 规则串)
            key = (rm.defect_code, rule_str)
            groups.setdefault(key, []).append(
                (spec, float(rm.priority or 1.0), rm.id, rule_str))

    # 独立写的判优：特异级升（同特异级则 priority 降、同 priority 则 id 升）
    expected = {}
    for key, items in groups.items():
        best = min(items, key=lambda t: (t[0], -t[1], t[2]))
        expected[key] = best
    return expected, len(groups), sum(len(v) for v in groups.values())


DEDUP_CASES = CASES + [
    ('显式补充库 R20240702164137(通用) + prod=通用',
     dict(defect_name='SHORTSHOT', defect_level='low',
          rule_library_code='R20240702164137', product_category='通用')),
    ('显式补充库 R20231129160052(手机外壳) + prod=手机外壳',
     dict(defect_name='SHORTSHOT', defect_level='low',
          rule_library_code='R20231129160052', product_category='手机外壳')),
]

dedup_failures = []
for label, kw in DEDUP_CASES:
    c = RuleQueryContext(**kw)
    ps = ResourceRepository.get_rules(c)
    expected, exp_unique, exp_total = _expected_dedup(c)

    # 断言 1：生产结果里同一内容最多出现 1 次
    prod_keys = []
    for p in ps:
        rm = _rm_by_profile(p)
        if rm is None:
            dedup_failures.append('%s: %s 无法反查 ORM 行' % (label, p.source_ref))
            continue
        prod_keys.append((rm.defect_code, (rm.rule_description or '').strip()))
    dup_left = len(prod_keys) - len(set(prod_keys))
    if dup_left:
        dedup_failures.append('%s: 生产结果仍有 %d 条重复内容' % (label, dup_left))

    # 断言 2：内容集合与参照系一致
    if set(prod_keys) != set(expected.keys()):
        missing = set(expected.keys()) - set(prod_keys)
        extra = set(prod_keys) - set(expected.keys())
        dedup_failures.append('%s: 内容集合与参照系不符（缺 %d / 多 %d）'
                              % (label, len(missing), len(extra)))

    # 断言 3：每组保留的那条就是参照系算出的最特异者
    for p in ps:
        rm = _rm_by_profile(p)
        if rm is None:
            continue
        key = (rm.defect_code, (rm.rule_description or '').strip())
        want = expected.get(key)
        if want is None:
            continue
        if p.specificity != want[0]:
            dedup_failures.append(
                '%s: %s 保留的特异级=%s，参照系最特异=%s'
                % (label, p.source_ref, p.specificity, want[0]))

    print('   %-42s 命中=%-4s 去重前=%-4s 唯一=%-4s 残留重复=%s'
          % (label, len(ps), exp_total, exp_unique, dup_left))

# 业务语义硬断言：裸上下文不加载任何补充库 ⇒ 库内无副本 ⇒ 条数不受去重影响。
# ⚠️ 不写死条数（规则库在变）⇒ 与参照系对拍。
bare_ctx = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low')
bare_dedup = ResourceRepository.get_rules(bare_ctx)
_bare_exp, _bare_uniq, _bare_total = _expected_dedup(bare_ctx)
if len(bare_dedup) != _bare_uniq:
    dedup_failures.append('裸上下文命中条数应与参照系一致（%d），实为 %d'
                          % (_bare_uniq, len(bare_dedup)))
if any(p.specificity != 4 for p in bare_dedup):
    dedup_failures.append('裸上下文下存在非默认级（spec != 4）')

print('   去重断言全部通过 =', not dedup_failures)
for msg in dedup_failures[:10]:
    print('     [FAIL]', msg)

# ============================================================================
# 9) optimize 链的「显式指定规则库」通道（2026-10-27 新增）
# ============================================================================
print('=' * 68)
print('9) optimize 链 rule_library_code 通道')
print('=' * 68)

from process.services.parameter_optimize import (  # noqa: E402
    _compose_algorithm_context,
    _extract_context_overrides,
)

lib_failures = []

# 断言 1：compose 把 rule_library_code 放进 context
_ctx = _compose_algorithm_context(
    machine_info={}, polymer_info={}, mold_info={},
    parameter={}, feedback={'defect': []},
    rule_library_code='R20240516093115',
)
if _ctx.get('rule_library_code') != 'R20240516093115':
    lib_failures.append('compose 未把 rule_library_code 放进 context')

# 断言 2：未指定时为 None（与现状完全等价）
_ctx_none = _compose_algorithm_context(
    machine_info={}, polymer_info={}, mold_info={},
    parameter={}, feedback={'defect': []},
)
if _ctx_none.get('rule_library_code') is not None:
    lib_failures.append('未指定时 rule_library_code 应为 None')


class _FakeCond:
    """只带 process_context_snapshot 的最小替身（不碰 DB）。"""

    def __init__(self, snapshot):
        self.process_context_snapshot = snapshot


# 断言 3：overrides 读取的四种情形
if _extract_context_overrides(_FakeCond(None)) != {}:
    lib_failures.append('空 snapshot 应返回 {}')
if _extract_context_overrides(_FakeCond({})) != {}:
    lib_failures.append('无 overrides 应返回 {}')
if _extract_context_overrides(
        _FakeCond({'overrides': {'rule_library_code': 'X'}})) != {'rule_library_code': 'X'}:
    lib_failures.append('有 overrides 应原样返回')
if _extract_context_overrides(_FakeCond({'overrides': 'not-a-dict'})) != {}:
    lib_failures.append('overrides 非 dict 应返回 {}')

# 断言 4：端到端 —— 指定补充库后，命中里真的出现该库的规则
_lib_code = 'R20240516093115'
_ctx_q = RuleQueryContext(defect_name='SHORTSHOT', defect_level='low',
                           rule_library_code=_lib_code)
_hits = ResourceRepository.get_rules(_ctx_q)
_lib_rm_ids = set(
    RuleMethod.objects.filter(rule_library__library_code=_lib_code)
    .values_list('id', flat=True)
)
_hit_rm_ids = set()
for _p in _hits:
    _rm = _rm_by_profile(_p)
    if _rm is not None:
        _hit_rm_ids.add(_rm.id)
_overlap = _lib_rm_ids & _hit_rm_ids
if not _overlap:
    lib_failures.append('指定补充库后，命中里没有该库的规则')
else:
    print('   指定 %s ⇒ 命中 %d 条，其中该库规则 %d 条'
          % (_lib_code, len(_hits), len(_overlap)))

# 断言 5：不指定时不加载任何补充库（保证新通道不改变现状）
_bare_hits = ResourceRepository.get_rules(
    RuleQueryContext(defect_name='SHORTSHOT', defect_level='low'))
_bare_hit_ids = set()
for _p in _bare_hits:
    _rm = _rm_by_profile(_p)
    if _rm is not None:
        _bare_hit_ids.add(_rm.id)
if _bare_hit_ids & _lib_rm_ids:
    lib_failures.append('未指定库时却加载了补充库规则')
else:
    print('   未指定 ⇒ 只命中 base 库规则（%d 条）' % len(_bare_hit_ids))

print('   选库通道断言全部通过 =', not lib_failures)
for _m in lib_failures[:10]:
    print('     [FAIL]', _m)

print('=' * 68)
print('端到端复验完成')