"""工艺优化 —— 跨职责簇共用的字段命名翻译。

职责边界：只做业务字段名 ↔ 算法字段名的翻译与中文标签，不取数、不推理。
"""
from process.algorithms.fuzzy import (
    field_names,  # 命名契约：业务字段名 ↔ 算法字段名（双向映射，契约层唯一真相源）
)
from process.models import ProcessParameter


def to_business_param_name(param_name: str) -> str:
    """算法字段名 → 业务字段名（无法翻译时原样返回）。

    算法侧返回的 ``param`` 是算法命名空间（``IV0`` / ``BT1`` / ...），
    业务侧字段名是 ``inj_spd_1`` / ``brl_temp_1`` / ...。
    两者不在同一命名空间：不翻译就永远匹配不上 baseline，
    推荐值会被静默丢弃（表现为“算法有推荐，但参数没变”）。
    """
    if not param_name or not isinstance(param_name, str):
        return param_name
    return field_names.to_business_name(param_name) or param_name


def param_label(business_name: str) -> str:
    """业务字段名 → 中文标签（取 ProcessParameter 字段的 verbose_name）。

    例：``inj_pres_1`` → ``一段注射压力``。

    建议文案面向的是工艺员，必须用中文标签而不是 ``inj_pres_1`` / ``IP0``。
    参数不在 ProcessParameter 里时（规则库专用参数如 ``IPOS`` / ``CUSION``）
    回落到业务字段名本身。
    """
    if not business_name:
        return business_name
    try:
        return ProcessParameter._meta.get_field(business_name).verbose_name
    except Exception:  # noqa: BLE001 —— 字段不存在 / 非模型字段
        return business_name


__all__ = ["param_label", "to_business_param_name"]
