"""温度类判级论域（材料温度区间）测试

覆盖 B1-1 的三条口径：

  1. **权威源 = 材料维度**：温度类参数（NT/BT/ET/MT）的判级论域取
     `Polymer.min/max_melt_temp`（熔体侧）/ `min/max_mold_temp`（模温侧），
     不再取 RuleKeyword 的经验域。
  2. **缺权威源不阻塞**：材料区间缺失 / 区间倒挂 ⇒ 该参数**回落经验域**，
     不报错、不阻塞（温度类字段的 condition 是「推荐」不是「必填」）。
  3. **只换「整段」温度参数**：`BT1..BT9` / `MT0..MT19` / `HRT0..HRT49`
     是**分段加热器设定值**（沿轴向递减），材料熔体区间不是它们的权威源
     ⇒ 本步**不动**它们。

⚠️ 为什么还要单独测「不改传入对象」：材料区间**逐请求不同**，而档案可能来自
   仓库缓存 / 共享对象 ⇒ 就地改会把 A 材料的区间泄漏到 B 材料的请求里。

运行：
  cd backend
  python -m tests.test_fuzzy_temperature_domain
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
)
from process.algorithms.fuzzy.specs import (  # noqa: E402
    TEMPERATURE_DOMAIN_FIELDS,
    resolve_temperature_limits,
)


# PP 的材料区间（实测库内值）
PP_POLYMER = {
    'min_melt_temp': 200.0,
    'max_melt_temp': 280.0,
    'min_mold_temp': 20.0,
    'max_mold_temp': 80.0,
}


def test_resolve_temperature_limits():
    """材料区间 → 温度类论域（熔体侧 / 模温侧分开）。"""
    limits = resolve_temperature_limits(PP_POLYMER)

    assert limits['NT'] == (200.0, 280.0), limits
    assert limits['BT'] == (200.0, 280.0), limits
    assert limits['ET'] == (200.0, 280.0), limits
    assert limits['MT'] == (20.0, 80.0), limits
    # 分段温度参数**不在**权威源名单里
    assert 'BT1' not in limits, limits
    assert 'MT0' not in limits, limits
    assert 'HRT0' not in limits, limits
    print("[PASS] 温度类论域按熔体侧/模温侧分别取材料区间")


def test_resolve_temperature_limits_missing():
    """缺权威源 ⇒ 不产出（调用方回落经验域），不报错。"""
    assert resolve_temperature_limits({}) == {}
    assert resolve_temperature_limits(None) == {}
    # 只有熔体区间 ⇒ 模温侧不产出
    limits = resolve_temperature_limits({'min_melt_temp': 200.0,
                                         'max_melt_temp': 280.0})
    assert 'NT' in limits and 'MT' not in limits, limits
    print("[PASS] 缺材料区间不产出、不报错")


def test_resolve_temperature_limits_inverted():
    """区间倒挂 ⇒ 不产出（倒挂会让档位语义整体翻转）。"""
    limits = resolve_temperature_limits({'min_melt_temp': 280.0,
                                         'max_melt_temp': 200.0})
    assert 'NT' not in limits, limits
    print("[PASS] 倒挂区间不产出")


def test_apply_temperature_bound_replaces_domain():
    """论域被**整体**换成材料区间（上下界一起换）。"""
    profile = KeywordProfile(keyword='NT', lvl=5, min_val=0.0, max_val=50.0,
                              step=16.666666666666668)
    limits = resolve_temperature_limits(PP_POLYMER)

    bounded = FuzzyEngine._apply_temperature_bound(profile, limits)

    assert bounded.min_val == 200.0, bounded
    assert bounded.max_val == 280.0, bounded
    # step 按跨度等比缩放（跨度 50 → 80 ⇒ step × 1.6）
    assert abs(bounded.step - 16.666666666666668 * 80.0 / 50.0) < 1e-9, bounded
    assert bounded.lvl == 5, bounded
    print("[PASS] 温度类论域整体换成材料区间")


def test_apply_temperature_bound_not_mutate_input():
    """不改传入对象（材料区间逐请求不同 ⇒ 就地改会跨请求污染）。"""
    profile = KeywordProfile(keyword='NT', lvl=5, min_val=0.0, max_val=50.0,
                              step=16.0)
    limits = resolve_temperature_limits(PP_POLYMER)

    bounded = FuzzyEngine._apply_temperature_bound(profile, limits)

    assert bounded is not profile, '必须返回新档案'
    assert profile.min_val == 0.0 and profile.max_val == 50.0, profile
    assert profile.step == 16.0, profile
    print("[PASS] 论域替换不改传入档案（无跨请求污染）")


def test_apply_temperature_bound_non_temperature():
    """非温度类参数 / 无权威源 ⇒ 原样返回（不误伤其它族）。"""
    profile = KeywordProfile(keyword='IV0', lvl=5, min_val=0.0, max_val=120.0,
                              step=40.0)
    limits = resolve_temperature_limits(PP_POLYMER)

    assert FuzzyEngine._apply_temperature_bound(profile, limits) is profile
    assert FuzzyEngine._apply_temperature_bound(profile, None) is profile
    assert FuzzyEngine._apply_temperature_bound(profile, {}) is profile
    print("[PASS] 非温度类参数不受影响")


def test_apply_temperature_bound_inverted_kept():
    """倒挂区间 ⇒ 保留经验论域（不让档位语义翻转）。"""
    profile = KeywordProfile(keyword='NT', lvl=5, min_val=0.0, max_val=50.0,
                              step=16.0)
    bounded = FuzzyEngine._apply_temperature_bound(
        profile, {'NT': (280.0, 200.0)})

    assert bounded is profile
    assert bounded.min_val == 0.0 and bounded.max_val == 50.0, bounded
    print("[PASS] 倒挂区间保留经验论域")


def test_load_keyword_profiles_dispatch():
    """装配层分流：整段温度参数换材料区间，分段温度参数保持经验域。"""
    engine = FuzzyEngine()

    def _fake_repo(names):
        # 只返回查到的字段（真实实现只返回查到的）
        table = {
            'NT': KeywordProfile(keyword='NT', lvl=5, min_val=0.0, max_val=50.0,
                                 step=16.0),
            'BT1': KeywordProfile(keyword='BT1', lvl=5, min_val=150.0,
                                  max_val=350.0, step=66.0),
            'IV0': KeywordProfile(keyword='IV0', lvl=5, min_val=0.0, max_val=120.0,
                                  step=40.0),
        }
        return [table[n] for n in names if n in table]

    class _Repo:
        def get_keywords_by_names(self, names):
            return _fake_repo(names)

    engine._repo = _Repo()
    limits = resolve_temperature_limits(PP_POLYMER)

    profiles = engine._load_keyword_profiles(
        ['NT', 'BT1', 'IV0'], {}, None, limits)
    by_name = {kp.keyword: kp for kp in profiles}

    # 整段温度参数 ⇒ 材料区间
    assert by_name['NT'].min_val == 200.0, by_name['NT']
    assert by_name['NT'].max_val == 280.0, by_name['NT']
    # 分段温度参数 ⇒ 保持经验域（材料熔体区间不是它的权威源）
    assert by_name['BT1'].min_val == 150.0, by_name['BT1']
    assert by_name['BT1'].max_val == 350.0, by_name['BT1']
    # 非温度类 ⇒ 不受影响
    assert by_name['IV0'].min_val == 0.0, by_name['IV0']
    assert by_name['IV0'].max_val == 120.0, by_name['IV0']
    print("[PASS] 装配层按参数族分流（整段换 / 分段不动 / 其它不动）")


def test_load_keyword_profiles_fallback():
    """缺材料区间 ⇒ 回落经验域（不报错、不阻塞）。"""
    engine = FuzzyEngine()

    class _Repo:
        def get_keywords_by_names(self, names):
            return [KeywordProfile(keyword='NT', lvl=5, min_val=0.0,
                                   max_val=50.0, step=16.0)]

    engine._repo = _Repo()

    profiles = engine._load_keyword_profiles(['NT'], {}, None, None)
    assert len(profiles) == 1, profiles
    assert profiles[0].min_val == 0.0 and profiles[0].max_val == 50.0, profiles
    print("[PASS] 缺材料区间回落经验域")


def test_temperature_domain_fields_list():
    """权威源名单的形状：4 个整段参数，熔体侧 3 / 模温侧 1。"""
    assert set(TEMPERATURE_DOMAIN_FIELDS) == {'NT', 'BT', 'ET', 'MT'}, \
        TEMPERATURE_DOMAIN_FIELDS
    melt = [k for k, v in TEMPERATURE_DOMAIN_FIELDS.items()
            if v == ('min_melt_temp', 'max_melt_temp')]
    mold = [k for k, v in TEMPERATURE_DOMAIN_FIELDS.items()
            if v == ('min_mold_temp', 'max_mold_temp')]
    assert sorted(melt) == ['BT', 'ET', 'NT'], melt
    assert mold == ['MT'], mold
    print("[PASS] 权威源名单形状正确（整段 4 个）")


def main():
    test_resolve_temperature_limits()
    test_resolve_temperature_limits_missing()
    test_resolve_temperature_limits_inverted()
    test_apply_temperature_bound_replaces_domain()
    test_apply_temperature_bound_not_mutate_input()
    test_apply_temperature_bound_non_temperature()
    test_apply_temperature_bound_inverted_kept()
    test_load_keyword_profiles_dispatch()
    test_load_keyword_profiles_fallback()
    test_temperature_domain_fields_list()
    print("\nALL PASS  (10/10 组通过)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
