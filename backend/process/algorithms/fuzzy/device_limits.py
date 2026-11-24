"""设备限值表 —— 区间类型 + 查表 + 跨命名空间翻译（纯函数，不碰 ORM）。

**算法层不知道参数的上下限**：
算法层只做**字段映射**（业务字段名 ↔ 算法字段名，见 ``field_names.py``），
**不持有任何「上限来源」声明** —— 哪个族配哪个上限字段、限值多大、
哪些参数参与校验，一律由 service 层决定：

  - **取值 + 组装** ⇒ ``services/shared/param_limits.py``
    （从 ``machine_info`` 解析出各设定工艺参数的允许区间，产出**业务键区间表**）；
  - **比对 + 按严格度处理** ⇒ ``services/shared/param_limits.py``（同文件，
    「准备 + 校验」两个功能）。

【注意】**本模块只处理「限值表」**（纯函数，不碰 ORM）：
  - 允许区间的类型（:data:`Limit`）；
  - 「算法参数名 → 参数族前缀」的解析（:func:`param_family`）—— 命名规则
    （字母前缀 + 数字段号）的**单一真相源**；
  - 「参数名 → 该参数适用的上限」的两级匹配（:func:`lookup_limit`）；
  - 「业务键区间表 → 算法族上界表」的跨命名空间翻译（:func:`to_family_limits`）。

【注意】**只依赖同包的 ``field_names``**（不 import Django、不 import ORM）⇒
  依赖方向恒为「调用方 → fuzzy」，本包内不成环。

设备侧两套权威源（语义不同，不可混用；组装规则在 service 层）：
  ====================  ==========================  =========================
  权威源                字段                         回答的问题
  ====================  ==========================  =========================
  设备**可设定**上限    ``max_set_*``                「这个参数最多能设多少」
  设备**实测**行程      ``max_injection_stroke``      「设备能走多远」
  ====================  ==========================  =========================
"""
import re
from typing import Dict, Mapping, Optional, Tuple

from .field_names import to_algo_family

#: 允许区间：``(下限, 上限)``；``None`` 表示该侧不限。
Limit = Tuple[Optional[float], Optional[float]]

__all__ = [
    # 限值表（纯函数，不碰 ORM）
    'Limit',
    'param_family',
    'lookup_limit',
    'to_family_limits',
]

# 算法参数名 = 字母前缀 + 数字段号（IP0 / IV1 / MSR2）。
# 必须带数字后缀：整段参数（IPOS 注射位置 / NT 喷嘴温度 / MT 模温）没有机台上限，
# 也不能被当成某个分段参数的上限。
_ALGO_PARAM_PATTERN = re.compile(r'^([A-Za-z]+)(\d+)$')


def param_family(param_name: str) -> Optional[str]:
    """算法参数名 → 参数族前缀（无族前缀返回 None）。

    上限是**按族**给的（``{'IP': 100.0, 'IV': 80.0}``），所以任何要按上限
    判断参数的代码都需要「参数名 → 族」这一步。原先只有查表函数内部用正则取族，
    **族知识被封在函数里** —— 需要「只要族、不要上限」时（越限识别）就无从下手。

    暴露这个函数 ⇒ 正则（``^([A-Za-z]+)(\\d+)$``）仍是**单一真相源**：
    修改命名规则只改这一处。

    Args:
        param_name: 算法侧参数名（如 'IP0' / 'IV1' / 'MSR2'）

    Returns:
        族前缀（如 'IP' / 'IV' / 'MSR'）；
        整段参数（'IPOS' / 'NT' / 'MT'，没有数字后缀）没有族 ⇒ 返回 None
    """
    if not param_name:
        return None
    matched = _ALGO_PARAM_PATTERN.match(param_name)
    if not matched:
        return None
    return matched.group(1)


def lookup_limit(
    param_name: str,
    limits: Dict[str, float],
) -> Optional[float]:
    """算法参数名 → 该参数适用的上限（无上限返回 None）。

    **两级匹配**（上限表的键 = 族前缀 **或** 整段参数名）：

    1. **精确匹配** —— 整段参数（``MEL`` / ``VPTL``）在表里就是键本身；
    2. **族前缀匹配** —— 分段参数（``IL0``~``IL5`` / ``IP0``）取族前缀
       （族前缀由 :func:`param_family` 的正则取 ⇒ 命名规则仍是**单一真相源**）。

    【注意】**表里只有族键也能命中**：分段参数（``IP0``）的精确匹配必然落空
    ⇒ 自动落到族匹配；整段参数（``MEL`` / ``VPTL``）在表里就是键本身
    ⇒ 精确命中。

    Args:
        param_name: 算法侧参数名（如 'IP0' / 'IL2' / 'MEL' / 'VPTL'）
        limits: 上限表（键 = 族前缀或整段参数名 → 上限值）。

    Returns:
        上限值；该参数没有对应上限时返回 None
    """
    if not param_name or not limits:
        return None
    if param_name in limits:
        return limits[param_name]
    family = param_family(param_name)
    if family is None:
        return None
    return limits.get(family)


def to_family_limits(business_limits: Mapping[str, Limit]) -> Dict[str, float]:
    """业务键限值表 → 算法族上界表。

    **取区间上界**：限值表是区间 ``(下限, 上界)``，而算法层消费的是
    **上界标量**（论域上界 / 推荐值天花板）⇒ 只取高位。

    **跳过映射不到的键**：业务键在命名契约里没有对应族 ⇒ 不进表（不臆造族）。

    【注意】**整段参数也认**：``met_end_pos`` / ``vps_pos`` 没有段号，
    但族是确定的（``MEL`` / ``VPTL``）⇒ 照常翻译。

    Args:
        business_limits: 业务键 → 允许区间（service 层产出的成品表）。

    Returns:
        算法族 → 上界值；缺上限（``None``）或映射不到族的业务键不出现。
    """
    if not business_limits:
        return {}

    family_limits: Dict[str, float] = {}
    for business_key, interval in business_limits.items():
        family = to_algo_family(business_key)
        if not family:
            continue
        if not interval:
            continue
        high = interval[1]
        if high is None:
            continue
        try:
            family_limits[family] = float(high)
        except (TypeError, ValueError):
            continue
    return family_limits


# ============================================================================
# 判级论域口径（消费侧口径；组装规则在 service 层）
# ============================================================================
# 每个设定工艺参数的判级上界，取 **service 层 ``LIMIT_SOURCES`` 声明的**
# 那台机器的**能力项**（``max_set_injection_pressure`` /
# ``max_injection_stroke`` / …）—— **所有参数一视同仁**，唯一差别是「上限
# 取自哪个设备字段」。
#
# 【注意】**判级区间 = [0, 声明上限]**：
#   经验下界是**档位语义**、不是物理下限 ⇒ 真实值低于它时判不出档、规则恒
#   失活；设备设不出不存在的值 ⇒ 物理上 0 总是可设定的 ⇒ 下界必须取 0。
#   经验档位表本身**保留**（`RuleKeyword.range_min/max` 不动）⇒
#   回落经验论域时仍是原口径。
#
# 【注意】**真实值可能远超经验域**（行程类参数的真实值域远大于 RuleKeyword
#   种子默认域）⇒ 用经验域会越界 ⇒ 「充填量第一优先」那组规则会失活。
#
# 【注意】族前缀靠正则 `^([A-Za-z]+)(\d+)$` 取 ⇒ **整段参数取不到族**
#   （`MEL` / `VPTL` 没有数字后缀）⇒ 上限表额外收录整段参数名，
#   由 :func:`lookup_limit` 的两级匹配消化。


