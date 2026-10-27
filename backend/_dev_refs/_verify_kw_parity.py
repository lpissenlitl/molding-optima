"""关键字路径的**新旧对拍**（E12 验收）。

背景
----
E12 把关键字的「查库」从 `RuleKeywordAdapter` 剥离到 `KeywordQueryService`，
并让 `ResourceRepository.get_keywords_by_names` 走
「查库 → 内核契约 `KeywordProfile` → 内核 `keyword_array` 元素（dict）」。

改动前 `ResourceRepository.get_keywords_by_names` 的实现是：
    RuleKeywordAdapter.get_keywords_by_names(sorted(names))
        = [RuleKeywordAdapter.to_fuzzy_dict(kw)
           for kw in RuleKeyword.objects.filter(keyword_name__in=names)]

本脚本用**真实 DB** 数据，把「旧实现（内联复刻）」与「新实现（现网门面）」
的输出**逐元素、逐键、含键序、含类型**对拍，证明行为零变化。

⚠️ E20 之后：`RuleKeywordAdapter.to_fuzzy_dict` 这个出口已被删除（契约构造
归位到 `KeywordProfile`，不再经 dict 中转），旧基线因此**冻结在本脚本内**
（`_legacy_to_fuzzy_dict`），不再依赖生产代码的历史出口 —— 对拍关系不变。
同理，`KeywordProfile.to_net_dict` 也已删除（内核 net 直接吃契约对象），
对拍所需的 dict 形态在本脚本内就地重建。

同时校验新链路的中间产物确实是内核契约 `KeywordProfile`
（而不是又退回裸 dict / ORM 实例）。

运行：../.venv/Scripts/python.exe _dev_refs/_verify_kw_parity.py
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
    validate_keyword_profiles,
)
from process.algorithms.fuzzy.library.keywords import (  # noqa: E402
    KeywordQueryService,
)
from process.algorithms.fuzzy.library.repository import (  # noqa: E402
    ResourceRepository,
)
from process.models.rules import RuleKeyword  # noqa: E402

NAMES = ['IV0', 'IV1', 'MEL', 'NT', 'SHORTSHOT', 'inj_pres_1', 'ZZZ_NOT_EXIST']


def _legacy_to_fuzzy_dict(keyword):
    """E12 之前的 `RuleKeywordAdapter.to_fuzzy_dict`（冻结副本）。

    E20 把该出口删除（契约构造归位到 `KeywordProfile`，不再经 dict 中转），
    旧基线因此冻结在本脚本内，不再依赖生产代码的历史出口。
    """
    step = getattr(keyword, 'step', None)
    if step is None:
        # 兜底：step 字段为空时使用区间范围的 1/3
        try:
            span = float(keyword.range_max) - float(keyword.range_min)
            step = max(span / 3.0, 0.01)
        except Exception:
            step = 1.0
    return {
        'keyword': keyword.keyword_name,
        'lvl': int(keyword.fuzzy_level or 3),
        'min_val': float(keyword.range_min),
        'max_val': float(keyword.range_max),
        'step': float(step),
    }


def _profile_to_net_dict(profile):
    """`KeywordProfile` → 内核 `keyword_array` 元素（键名与数量固定）。

    ⚠️ `meta_source` 内核不读，仅在非空时附带；ORM 路径恒为空串，
    故实际只出 5 个键，键序与 `_legacy_to_fuzzy_dict` 一致。
    """
    data = {
        'keyword': profile.keyword,
        'lvl': profile.lvl,
        'min_val': profile.min_val,
        'max_val': profile.max_val,
        'step': profile.step,
    }
    if profile.meta_source:
        data['meta_source'] = profile.meta_source
    return data


print('=' * 68)
print('1) 新链路中间产物：必须是内核契约 KeywordProfile')
profiles = KeywordQueryService.get_keywords_by_names(NAMES)
print('   命中条数 =', len(profiles))
print('   类型集合 =', sorted({type(p).__name__ for p in profiles}))
print('   全部是 KeywordProfile =', all(isinstance(p, KeywordProfile) for p in profiles))
print('   契约校验 validate_keyword_profiles =', end=' ')
try:
    validate_keyword_profiles(profiles)
    print('通过')
except ValueError as e:
    print('失败 ->', e)

print()
print('2) 新旧对拍（旧实现内联复刻 vs 现网门面）')
old = [
    _legacy_to_fuzzy_dict(kw)
    for kw in RuleKeyword.objects.filter(keyword_name__in=sorted(NAMES))
]
new = ResourceRepository.get_keywords_by_names(NAMES)
# 门面现在**直接返回内核契约 KeywordProfile**（不再转 dict）；
# 对拍仍按「键 / 值 / 键序 / 类型」逐项比 ⇒ 先归一成同形态再比。
new = [_profile_to_net_dict(p) for p in new]
print('   旧实现条数 =', len(old), '| 新实现条数 =', len(new))
print('   条数相同 =', len(old) == len(new))

same_value = old == new
same_order = all(list(a.keys()) == list(b.keys()) for a, b in zip(old, new))
same_type = all(
    type(a[k]) is type(b[k]) for a, b in zip(old, new) for k in a
)
print('   逐元素逐键**值**全等 =', same_value)
print('   逐元素**键序**全等 =', same_order)
print('   逐键**类型**全等 =', same_type)

if not (same_value and same_order and same_type):
    for i, (a, b) in enumerate(zip(old, new)):
        if a != b or list(a.keys()) != list(b.keys()):
            print('   [DIFF]', i, '旧 =', a, '新 =', b)

print()
print('3) 空入参 / 不存在名字（边界）')
print('   门面空入参 =', ResourceRepository.get_keywords_by_names([]))
print('   服务空入参 =', KeywordQueryService.get_keywords_by_names([]))
missing = ResourceRepository.get_keywords_by_names(['ZZZ_NOT_EXIST'])
print('   不存在的名字 =', missing)

print()
print('4) ORM 泄漏检查：新链路不得把 ORM 实例带出')
leaked = [p for p in profiles if hasattr(p, '_state')]
print('   带 ORM 属性的对象数 =', len(leaked))
print('   字段集合 =', sorted({k for p in profiles for k in p.__dataclass_fields__}))

ok = (
    all(isinstance(p, KeywordProfile) for p in profiles)
    and same_value and same_order and same_type
    and len(leaked) == 0
)
print()
print('=' * 68)
print('[%s] 关键字路径新旧对拍' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
