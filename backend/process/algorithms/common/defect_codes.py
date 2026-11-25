"""缺陷码词表 —— 中文缺陷名 → 英文缺陷码。

缺陷码是算法层的命名空间：``RuleMethod.defect_code`` 与
``RuleKeyword.keyword_name`` 用同一套码，算法层按它查规则库。

【注意】**权威源 = ``RuleKeyword.keyword_name``**（规则库 17 类缺陷码），本表是它的
离线副本（中文名取自规则库条目的 ``description``）⇒ 规则库扩缺陷类型时本表要同改，
否则中文名查不到规则（表现为无推荐，不报错）。
"""

from typing import Dict, Optional


# 中文缺陷名 → 英文缺陷码（与 RuleKeyword.keyword_name 同码）
DEFECT_CODE_ALIAS: Dict[str, str] = {
    "短射": "SHORTSHOT",
    "缩水": "SHRINKAGE",
    "飞边": "FLASH",
    "熔接痕": "WELDLINE",
    "困气": "AIRTRAP",
    "气纹": "GASVEINS",
    "烧焦": "BURN",
    "料花": "MATERIALFLOWER",
    "水波纹": "WATERRIPPLE",
    "脱模不良": "HARDDEMOLDING",
    "顶白": "TOPWHITE",
    "变形": "WARPING",
    "尺寸偏大": "OVERSIZE",
    "尺寸偏小": "UNDERSIZE",
    "浇口印": "GATEMARK",
    "阴阳面": "SHADING",
    # 规则库无「色差」这一类缺陷 ⇒ 保留原名（查不到规则 ⇒ 无推荐）
    "色差": "COLOR_SHIFT",
}


def to_defect_code(name: Optional[str]) -> str:
    """中文缺陷名 → 英文缺陷码。

    Args:
        name: 缺陷名，中文名（``短射``）或英文码（``SHORTSHOT``）皆可。

    Returns:
        str: 英文缺陷码；入参为空时返回空串，非中文名则原样返回。
    """
    if not name:
        return ""
    return DEFECT_CODE_ALIAS.get(name, name)


__all__ = [
    'DEFECT_CODE_ALIAS',
    'to_defect_code',
]
