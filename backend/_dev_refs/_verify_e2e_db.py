"""端到端真实 DB 复验。

生产链路的四件事必须成立：
1. 规则查询命中真实数据；
2. 返回对象类型是 fuzzy_core.profiles.RuleProfile；
3. 溯源字段是字符串 source_ref，无 ORM 实例泄漏；
4. 契约层校验（validate_rule_profiles）对真实数据通过。

另验证第 4 层（build_rule_objects）的分流与建对象结果。

运行：../.venv/Scripts/python.exe _dev_refs/_verify_e2e_db.py
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.algorithms.fuzzy.library.contracts import RuleQueryContext  # noqa: E402
from process.algorithms.fuzzy.library.repository import (  # noqa: E402
    ResourceRepository,
)
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    RuleProfile,
    validate_rule_profiles,
)
from process.algorithms.fuzzy.fuzzy_core.rules_filter import (  # noqa: E402
    build_rule_objects,
)

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
print('端到端复验完成')
