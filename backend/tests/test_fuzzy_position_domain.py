r"""位置类判级论域（设备实测最大注射行程）测试。

口径（**3 条，各自都有独立参照系**）：

  1. **业务口径 —— 权威源与匹配方式**
     位置类参数（注射位置 `IL` / 计量位置 `ML` / 储料终止位置 `MEL` /
     VP 切换位置 `VPTL`）的判级论域取 `InjectionUnit.max_injection_stroke`
     （最大注射行程）。
     匹配是**两级**：整段参数（`MEL`/`VPTL`）走精确匹配，分段参数
     （`IL0`~`IL5` / `ML0`~`ML3`）走族前缀匹配 —— `param_family()` 的
     `^([A-Za-z]+)(\d+)$` 正则取不到整段参数 ⇒ 必须另立名单。

  2. **数值锚点 —— 判级区间是 [0, 行程]**
     经验下界（如 `VPTL` 的 30mm）是**档位语义**、不是物理下限；真实值
     低于它时（VPTL 13.92）判不出档、规则恒失活 ⇒ 判级区间必须覆盖
     [0, 行程]（用户口径：「我们不可能设定一个机器不存在的值」）。
     step 按跨度等比缩放；**不改传入档案**（行程逐请求不同 ⇒ 就地改会
     跨请求污染）。

  3. **回落口径 —— 缺权威源 / 当前值超行程 ⇒ 回落经验论域**
     `max_injection_stroke` 的 condition 是「可选」（行程是设备能力参数，
     业务侧未必录入）⇒ 缺失不报错、不阻塞；当前值超出设备行程 = 这个产品
     在这台设备上做不出来 ⇒ 视同缺权威源，回落经验论域（判档结果不变）。

运行：
  cd backend
  python -m tests.test_fuzzy_position_domain
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
    OPTIMIZE_MACHINE_INFO_FIELDS,
    POSITION_DOMAIN_FIELDS,
    lookup_position_limit,
    resolve_position_limits,
)


def test_position_domain_authority_and_matching():
    """【业务口径】权威源 = 设备实测行程；两级匹配；不误伤无关参数。"""
    limits = resolve_position_limits({'max_injection_stroke': 200.0})

    # 权威源名单：4 个族，同指最大注射行程
    assert set(POSITION_DOMAIN_FIELDS) == {'IL', 'ML', 'MEL', 'VPTL'}, \
        POSITION_DOMAIN_FIELDS
    assert set(POSITION_DOMAIN_FIELDS.values()) == {'max_injection_stroke'}, \
        POSITION_DOMAIN_FIELDS
    assert limits == {'IL': 200.0, 'ML': 200.0, 'MEL': 200.0, 'VPTL': 200.0}, \
        limits

    # 两级匹配：整段精确 / 分段族前缀
    assert lookup_position_limit('MEL', limits) == 200.0
    assert lookup_position_limit('VPTL', limits) == 200.0
    assert lookup_position_limit('IL0', limits) == 200.0
    assert lookup_position_limit('ML3', limits) == 200.0
    # 无关参数取不到（不误伤）：非位置类 / 无字段映射 / 形近但不同族
    assert lookup_position_limit('IP0', limits) is None
    assert lookup_position_limit('NT', limits) is None
    assert lookup_position_limit('IPOS', limits) is None
    assert lookup_position_limit('VPTM', limits) is None
    print("[PASS] 权威源与两级匹配正确")


def test_position_domain_bounds_and_step():
    """【数值锚点】判级论域 = [0, 行程]；step 等比缩放；不改传入档案。"""
    profile = KeywordProfile(keyword='VPTL', lvl=3, min_val=30.0, max_val=60.0,
                              step=10.0)
    limits = resolve_position_limits({'max_injection_stroke': 200.0})

    bounded = FuzzyEngine._apply_position_bound(profile, limits)

    # 下界统一 0（经验下界 30 是档位语义、不是物理下限）
    assert bounded.min_val == 0.0, bounded
    assert bounded.max_val == 200.0, bounded
    # step 按跨度等比缩放（经验跨度 30 → 新跨度 200）
    assert abs(bounded.step - 10.0 * 200.0 / 30.0) < 1e-9, bounded
    assert bounded.lvl == 3, bounded
    # 不改传入档案（行程逐请求不同 ⇒ 就地改会跨请求污染）
    assert bounded is not profile, '必须返回新档案'
    assert (profile.min_val, profile.max_val, profile.step) == (30.0, 60.0, 10.0), \
        profile
    print("[PASS] 判级区间 [0, 行程]、step 等比缩放、不改入参")


def test_position_domain_fallback_and_gate():
    """【回落口径】缺权威源 / 当前值超行程 ⇒ 回落经验论域；行程字段是「可选」。"""
    # 缺行程 ⇒ 不产出（调用方回落经验域）；非正数同理
    assert resolve_position_limits({}) == {}
    assert resolve_position_limits({'max_injection_stroke': None}) == {}
    assert resolve_position_limits({'max_injection_stroke': 0}) == {}

    profile = KeywordProfile(keyword='VPTL', lvl=3, min_val=30.0, max_val=60.0,
                              step=10.0)
    limits = resolve_position_limits({'max_injection_stroke': 200.0})
    # 当前值超行程 ⇒ 回落经验论域（视同缺权威源，判档结果不变）
    over = FuzzyEngine._apply_position_bound(profile, limits, 491.04)
    assert over is profile
    assert (over.min_val, over.max_val) == (30.0, 60.0), over

    # 权威源入口：机器维度字段字典已声明最大注射行程，且条件是「可选」（缺不阻塞）
    spec = OPTIMIZE_MACHINE_INFO_FIELDS['max_injection_stroke']
    assert spec['source_model'] == 'InjectionUnit', spec
    assert spec['attr_name'] == 'max_injection_stroke', spec
    assert spec['condition'] == '可选', spec
    print("[PASS] 缺权威源 / 超行程 ⇒ 回落经验论域，行程字段为可选")


def main():
    test_position_domain_authority_and_matching()
    test_position_domain_bounds_and_step()
    test_position_domain_fallback_and_gate()
    print("\nALL PASS  (3/3 组通过)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
