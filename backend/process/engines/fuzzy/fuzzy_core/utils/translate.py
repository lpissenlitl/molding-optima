"""
模糊规则翻译工具集

从 `old/mdprocess/utils/fuzzykit/fuzzy_core/utils/translate.py` 迁移。
原文件依赖 Django settings.RANGES_PATH 与 numpy 读取旧 fuzzykit 的 csv；
本次迁移改为从 RuleKeyword 模型动态获取取值范围。
"""

import numpy as np

from ..models.nets import DEFECT_CONST  # noqa: F401  保留兼容旧规则


def defect_translate(defect: dict) -> list:
    """缺陷数值 → 模糊级别字符串。

    Parameters
    ----------
    defect : dict
        {defect_name: degree_value}，degree_value 范围 [-1, 0]
        （负值表示严重程度，0 表示正常）

    Returns
    -------
    list[str]
        [{defect_name}_low / _mid / _high, ...]
    """
    defect_output = []
    for index, value in defect.items():
        label = index
        if value >= -0.3:
            label += '_low'
        elif -0.6 <= value < -0.3:
            label += '_mid'
        else:
            label += '_high'
        defect_output.append(label)
    return defect_output


def _value_to_fuzzy_level(value: float, value_min: float, value_max: float, f_level: int = 3) -> str:
    """根据取值范围把精确值划分为模糊级别（low/mid/high 等）。"""
    if value_max <= value_min:
        # 退化情况：区间为零，强行给 mid
        return {3: 'mid', 5: 'mid'}.get(f_level, 'mid')

    span = value_max - value_min
    if f_level == 3:
        if value <= value_min + span / 3:
            return 'low'
        if value <= value_min + 2 * span / 3:
            return 'mid'
        return 'high'
    if f_level == 5:
        boundaries = [value_min + i * span / 5 for i in range(1, 5)]
        if value <= boundaries[0]:
            return 'very_low'
        if value <= boundaries[1]:
            return 'low'
        if value <= boundaries[2]:
            return 'mid'
        if value <= boundaries[3]:
            return 'high'
        return 'very_high'
    raise ValueError(f'不支持的 f_level: {f_level}')


def rule_standard(
    label: str,
    rules,
    defect,
    ranges_provider=None,
):
    """将单变量阈值规则标准化为 fuzzykit 格式的规则字符串。

    Parameters
    ----------
    label : str
        结论标签，如 'inj_pres_1_add_5'
    rules : list
        规则条件列表（字符串如 'inj_pres_1=60'，或 'True' 表示无条件）
    defect : list
        缺陷标签列表，如 ['SHORTSHOT_low']
    ranges_provider : callable, optional
        参数取值范围提供器，签名 `get_range(param_name: str) -> (min, max)`
        缺省时使用 RuleKeyword 模型查表。

    Returns
    -------
    list[str]
        标准化规则字符串列表
    """
    cond_split_words = '^'

    def trans_func(rule):
        if not isinstance(rule, str):
            raise TypeError('rules must contain rule in string！')

        rule = rule.lstrip('[').rstrip(']')
        conds = rule.split(cond_split_words)

        if conds[0] == 'True':
            a_rule = ' '.join(['IF', ' AND '.join(defect), 'THEN', label])
            return [a_rule]

        output_dict = {}
        for k in conds:
            name, value_str = k.split('=')
            value = float(value_str)

            if ranges_provider is not None:
                value_min, value_max = ranges_provider(name)
            else:
                # 兜底：从 RuleKeyword 模型查（避免此处 DB 连接带来副作用，使用 import 延迟加载）
                try:
                    from process.models.rules import RuleKeyword
                    kw = RuleKeyword.objects.filter(keyword_name=name).first()
                    if not kw:
                        value_min, value_max = 0.0, 1.0
                    else:
                        value_min = float(kw.range_min)
                        value_max = float(kw.range_max)
                except Exception:
                    value_min, value_max = 0.0, 1.0

            v_degree = _value_to_fuzzy_level(value, value_min, value_max, f_level=3)
            output_dict[k] = f'{name}_{v_degree}'

        standard_rules = []
        output = list(output_dict.values())
        for word in defect:
            words = [word] + output
            a_rule = ' '.join(['IF', ' AND '.join(words), 'THEN', label])
            standard_rules.append(a_rule)
        return standard_rules

    st_rules = []
    for i in rules:
        st_rules += trans_func(i)
    return st_rules


# ============================================================================
# 模块自检
# ============================================================================

if __name__ == '__main__':
    # defect_translate demo
    defects = {'SHORTSHOT': -0.7, 'FLASH': -0.2}
    print('== defect_translate ==:')
    print(defect_translate(defects))

    # rule_standard demo
    print('== rule_standard ==:')
    rules = rule_standard(
        label='inj_pres_1_add_5',
        rules=['inj_pres_1=60'],
        defect=['SHORTSHOT_low'],
    )
    for r in rules:
        print(' -', r)
