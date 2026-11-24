r"""判级论域 = **[0, 机台对每个参数的可设定上限]**（所有参数一视同仁）。

口径（**4 条，各自都有独立参照系**）：

  1. **业务口径 —— 权威源与匹配方式**
     每个设定工艺参数的判级论域上界，取自 service 层 ``LIMIT_SOURCES``
     声明的那台机器的**能力项**（``max_set_injection_pressure`` /
     ``max_injection_stroke`` / …）。
     匹配是**两级**：整段参数（`MEL`/`VPTL`）走精确匹配，分段参数
     （`IL0`~`IL5` / `ML0`~`ML3`）走族前缀匹配 —— `param_family()` 的
     `^([A-Za-z]+)(\d+)$` 正则取不到整段参数 ⇒ 必须另立名单。

  2. **数值锚点 —— 判级区间是 [0, 上限]**
     经验下界（如 `VPTL` 的 30mm）是**档位语义**、不是物理下限；真实值
     低于它时（VPTL 13.92）判不出档、规则恒失活 ⇒ 判级区间必须覆盖
     [0, 上限]（设备设不出不存在的值）。
     step 按跨度等比缩放；**不改传入档案**（上限逐请求不同 ⇒ 就地改会
     跨请求污染）。

  3. **必填口径 —— 行程是位置类论域上界的唯一权威源**
     `max_injection_stroke` 的 condition 是「**必填**」⇒ 调优链路上缺失
     **报错**（契约层 → 400），不回落经验论域（论域无上界 ⇒ 位置类规则失活）。

  4. **回落口径 —— 当前值超上限 ⇒ 回落经验论域**（**防御性**分支）
     当前值超出机台可设定上限 ⇒ 视同缺权威源，回落经验论域（判档结果不变）。

【注意】**位置参数与压力 / 速度参数同构**：本文件不再有「位置类专项」口径 ——
      位置参数（IL / ML / MEL / VPTL）与压力 / 速度参数走**同一条**判定路径，
      唯一差别是「上限取自哪个设备字段」。

运行：
  cd backend
  python -m tests.test_fuzzy_declared_domain
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.algorithms.fuzzy.device_limits import lookup_limit  # noqa: E402
from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
)
from process.algorithms.fuzzy.specs import (  # noqa: E402
    OPTIMIZE_MACHINE_INFO_FIELDS,
)
from process.algorithms.fuzzy.device_limits import to_family_limits  # noqa: E402
from process.services.shared.param_limits import (  # noqa: E402
    LIMIT_SOURCES,
    build_limits,
)


def test_declared_domain_authority_and_matching():
    """【业务口径】权威源 = service 层声明的能力项；两级匹配；不误伤无关参数。"""
    limits = to_family_limits(build_limits({'max_injection_stroke': 200.0}))

    # 权威源声明在 **service 层**（业务键 → 上限来源字段）⇒
    # 算法层不持有上限来源声明，也不自己判「哪些族是位置类」。
    stroke_sources = {
        key: spec.high for key, spec in LIMIT_SOURCES.items()
        if spec.high == 'max_injection_stroke'
    }
    assert set(stroke_sources) == {'inj_pos', 'met_pos', 'met_end_pos', 'vps_pos'}, \
        stroke_sources
    assert set(stroke_sources.values()) == {'max_injection_stroke'}, stroke_sources
    # 翻译后的族表：4 个族，同指最大注射行程
    assert set(limits) == {'IL', 'ML', 'MEL', 'VPTL'}, limits
    assert limits == {'IL': 200.0, 'ML': 200.0, 'MEL': 200.0, 'VPTL': 200.0}, \
        limits

    # 两级匹配：整段精确 / 分段族前缀
    assert lookup_limit('MEL', limits) == 200.0
    assert lookup_limit('VPTL', limits) == 200.0
    assert lookup_limit('IL0', limits) == 200.0
    assert lookup_limit('ML3', limits) == 200.0
    # 无关参数取不到（不误伤）：非该能力项 / 无字段映射 / 形近但不同族
    assert lookup_limit('IP0', limits) is None
    assert lookup_limit('NT', limits) is None
    assert lookup_limit('IPOS', limits) is None
    assert lookup_limit('VPTM', limits) is None
    print("[PASS] 权威源与两级匹配正确")


def test_declared_domain_bounds_and_step():
    """【数值锚点】判级论域 = [0, 上限]；step 等比缩放；不改传入档案。"""
    profile = KeywordProfile(keyword='VPTL', lvl=3, min_val=30.0, max_val=60.0,
                              step=10.0)
    limits = to_family_limits(build_limits({'max_injection_stroke': 200.0}))

    bounded, declared_max, guarded = FuzzyEngine._apply_declared_bound(
        profile, limits)

    # 下界统一 0（经验下界 30 是档位语义、不是物理下限）
    assert bounded.min_val == 0.0, bounded
    assert bounded.max_val == 200.0, bounded
    assert declared_max == 200.0, declared_max
    assert guarded is False
    # step 按跨度等比缩放（经验跨度 30 → 新跨度 200）
    assert abs(bounded.step - 10.0 * 200.0 / 30.0) < 1e-9, bounded
    assert bounded.lvl == 3, bounded
    # 不改传入档案（上限逐请求不同 ⇒ 就地改会跨请求污染）
    assert bounded is not profile, '必须返回新档案'
    assert (profile.min_val, profile.max_val, profile.step) == (30.0, 60.0, 10.0), \
        profile
    print("[PASS] 判级区间 [0, 上限]、step 等比缩放、不改入参")


def test_position_and_setting_params_share_one_path():
    """【同构口径】位置参数与压力 / 速度参数走**同一条**判定路径。"""
    machine = {
        'max_injection_stroke': 200.0,
        'max_set_injection_pressure': 100.0,
    }
    limits = to_family_limits(build_limits(machine))
    # 同一张表里，位置族与压力族同构（都是「族 → 上限」）
    assert limits == {'IL': 200.0, 'ML': 200.0, 'MEL': 200.0, 'VPTL': 200.0,
                      'IP': 100.0}, limits

    # 同一个方法、同一个判据：下界归 0、只换上界
    profile = KeywordProfile(keyword='IP0', lvl=3, min_val=10.0, max_val=200.0,
                              step=50.0)
    bounded, declared_max, guarded = FuzzyEngine._apply_declared_bound(
        profile, limits)
    assert bounded.min_val == 0.0, bounded
    assert bounded.max_val == 100.0, bounded
    assert declared_max == 100.0, declared_max
    assert guarded is False
    print("[PASS] 位置参数与压力参数同构：一张表、一个方法、一条判据")


def test_declared_domain_fallback_and_gate():
    """【必填 + 回落口径】缺源不产出；当前值超上限 ⇒ 回落经验论域。"""
    # 缺源 ⇒ 取值函数不产出限值（**函数级**行为：不臆造限值；必填校验在
    # 上游契约层完成，见 OPTIMIZE_MACHINE_INFO_FIELDS）；非正数同理
    assert to_family_limits(build_limits({})) == {}
    assert to_family_limits(build_limits({'max_injection_stroke': None})) == {}
    assert to_family_limits(build_limits({'max_injection_stroke': 0})) == {}

    profile = KeywordProfile(keyword='VPTL', lvl=3, min_val=30.0, max_val=60.0,
                              step=10.0)
    limits = to_family_limits(build_limits({'max_injection_stroke': 200.0}))
    # 当前值超上限 ⇒ 回落经验论域（视同缺权威源，判档结果不变）
    over, declared_max, guarded = FuzzyEngine._apply_declared_bound(
        profile, limits, 491.04)
    assert over is profile
    assert guarded is True
    assert declared_max == 200.0, declared_max
    assert (over.min_val, over.max_val) == (30.0, 60.0), over

    # 权威源入口：机器维度字段字典已声明最大注射行程，且条件是「必填」
    # （缺 ⇒ 契约层报错 400，不回落经验论域）
    spec = OPTIMIZE_MACHINE_INFO_FIELDS['max_injection_stroke']
    assert spec['source_model'] == 'InjectionUnit', spec
    assert spec['attr_name'] == 'max_injection_stroke', spec
    assert spec['condition'] == '必填', spec
    print("[PASS] 论域上界 = 声明的能力项上限；行程字段为必填；当前值超上限 ⇒ 回落经验论域")


def main():
    test_declared_domain_authority_and_matching()
    test_declared_domain_bounds_and_step()
    test_position_and_setting_params_share_one_path()
    test_declared_domain_fallback_and_gate()
    print("\nALL PASS  (4/4 组通过)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
