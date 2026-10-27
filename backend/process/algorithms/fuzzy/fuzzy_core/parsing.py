"""规则词法解析（公开 API）

供**算法层**与**规则层**共用的词法工具：

- `split_phase()`  把一个规则词法单元解析为结构化字段
- `classify_name()`  判定名字是"缺陷"还是"工艺参数"
- `is_param_name()`  判定名字是否是"工艺参数名"（唯一判定口径）

为什么要统一口径：算法层与规则层都要按规则串反推"这条规则涉及哪些参数"、
按"结论形态"分流规则，两处各自解析会让 `X_add_2` / `X_adjust_提示语`
的理解出现分叉。

命名空间说明：
- 规则库段号以 0-based 为主（IV0/MBP0/BT/...），与 RuleKeyword 的
  `IV0~IV5` / `PP0~PP4` 完全吻合，不要在这里做 0/1-based 转换。
"""

from typing import Dict, List

from .macros import ALL_LEVEL_WORDS, DEFECT_CONST, LEVEL_WORD_ALIASES


# 规则关键字（IF / AND / THEN）——不是词法单元，跳过
RULE_KEYWORDS = frozenset({'IF', 'AND', 'THEN', 'Then', 'then'})


def split_phase(phase: str) -> Dict[str, str]:
    """将规则词法单元（已按空格 split 后的一项）解析为结构化字段。

    支持以下三种形式：

    1. 前提词（条件）  `<param_name>_<level>`
       例： ``MEL_low``           → name='MEL',     level='low'
            ``inj_pres_1_low``    → name='inj_pres_1', level='low'
            ``SHORTSHOT_high``    → name='SHORTSHOT', level='high'

    2. 结论词（修正）  `<param_name>_<action>_<value>`
       例： ``MEL_add_low``       → name='MEL',     action='add',    value='low'
            ``inj_pres_1_add_10`` → name='inj_pres_1', action='add', value='10'
            ``hold_time_reduce_5%`` → name='hold_time', action='reduce', value='5%'
            ``alert_popup_sugg``  → name='alert',   action='popup', value='sugg'

    3. 代数结论词      ``<name>=a*X+b*Y+...``（极少见，预留）

    Parameters
    ----------
    phase : str
        词法单元（不包含 IF / AND / THEN 等关键字）

    Returns
    -------
    dict
        至少包含 ``name``；若是结论词则还含 ``action``、``value``；
        若是前提词则还含 ``level``。
    """
    if not phase:
        return {'name': '', 'level': '', 'kind': 'precondition'}

    if '=' in phase:
        # 代数式结论（预留接口，由 NumTskRule._rule_process 内部进一步处理）
        return {'name': phase.split('=', 1)[0], 'kind': 'algebra'}

    parts = phase.split('_')
    # ---- 情形 1: 弹窗结论  `<name>_popup_<text>` ---------------------------
    #   形式：弹窗词总是以 `_popup_` 标识（特例：`_popup_xxx` 整体作 r_extra）
    for i in range(1, len(parts) - 1):
        if parts[i] == 'popup':
            name = '_'.join(parts[:i])
            value = '_'.join(parts[i + 1:]) or parts[-1]
            return {'name': name, 'action': 'popup', 'value': value, 'kind': 'solution'}

    # ---- 情形 2: 标准结论  `<name>_<action>_<value>` -----------------------
    #   action 必为 add/reduce/adjust 之一
    for i in range(1, len(parts) - 1):
        if parts[i] in {'add', 'reduce', 'adjust'}:
            name = '_'.join(parts[:i])
            action = parts[i]
            value = '_'.join(parts[i + 1:])
            return {'name': name, 'action': action, 'value': value, 'kind': 'solution'}

    # ---- 情形 3: 前提词  `<name>_<level>` ----------------------------------
    #   档位词可能是多段的（very_low / extremely_low / slightly_low ...），
    #   必须按“最长后缀”匹配：'IV0_very_low' 应拆成 name='IV0' + level='very_low'，
    #   而不是 name='IV0_very' + level='low'（那样档位会错一档）。
    for seg_count in range(min(3, len(parts) - 1), 0, -1):
        suffix = '_'.join(parts[-seg_count:])
        if suffix in ALL_LEVEL_WORDS:
            name = '_'.join(parts[:-seg_count])
            return {'name': name, 'level': suffix, 'kind': 'precondition'}

    # ---- 兜底：按空格 + 第一段下划线拆分 -----------------------------------
    #   注：兜底结果的 level 未必是合法等级词（如 'worse'），调用方必须
    #   用 is_level_word() 复核后再查档位映射。
    return {'name': parts[0], 'level': parts[1] if len(parts) > 1 else '', 'kind': 'precondition'}


def classify_name(name: str) -> str:
    """根据名称区分是工艺参数还是缺陷。

    Returns:
        'defect' —— 缺陷名（在前 DEFECT_CONST 中）
        'process' —— 工艺参数名
    """
    if name in DEFECT_CONST:
        return 'defect'
    return 'process'


def is_level_word(word: str) -> bool:
    """词是否是可判级的等级词（low / medium / high / ...）。

    'worse' 这类人工判断词返回 False——它无法映射到隶属度等级索引，
    遇到时只能跳过，不能查表。
    """
    return str(word or '').lower() in ALL_LEVEL_WORDS


def normalize_level_word(word: str) -> str:
    """等级词归一（'mid' → 'medium'，其余原样返回）。

    兼容写法 'mid' 与前端 LEVEL_WORDS / 规则库 rule_description 写的
    'medium' 同义（都是第 2 档）。比较前必须先归一，否则同一个档位
    会被当成两档。
    """
    w = str(word or '').lower()
    return LEVEL_WORD_ALIASES.get(w, w)


def is_position_name(name: str) -> bool:
    """是否缺陷位置名（`DL` + 缺陷名 + 段号，如 `DLOVERSIZE1`）。"""
    return bool(name) and name.upper().startswith('DL')


def is_param_name(name: str) -> bool:
    """是否是「工艺参数名」（不是缺陷名、不是缺陷位置名）。

    参数名集合的**唯一判定口径**：缺陷名（`DEFECT_CONST` 内）不参与论域，
    缺陷位置名（`DL` 前缀）同理。
    第 4 层 filter 按已拆解产物收参数名时也走本函数 ⇒ 口径永远一致。
    """
    if not name:
        return False
    if is_position_name(name):
        return False
    return classify_name(name) != 'defect'


def parse_rule(rule_str: str) -> Dict[str, List[Dict[str, str]]]:
    """把一条规则串拆成前件 / 结论两部分。

    Returns:
        {'preconditions': [...], 'solutions': [...]}
        每个元素是 `split_phase()` 的结果 dict，另附 ``'phase'`` = 原始词。

    ⚠️ `phase`（原始词）不是冗余：弹窗结论的 `r_extra` 键、代数结论的等式串
    都只能从原文取（`split_phase` 只给拆解后的字段，拆不回原文）。
    """
    preconditions: List[Dict[str, str]] = []
    solutions: List[Dict[str, str]] = []
    is_pre = False
    for word in (rule_str or '').split():
        if word == 'IF':
            is_pre = True
            continue
        if word in ('THEN', 'Then', 'then'):
            is_pre = False
            continue
        if word == 'AND':
            continue
        info = split_phase(word)
        info['phase'] = word
        if is_pre:
            preconditions.append(info)
        else:
            solutions.append(info)
    return {'preconditions': preconditions, 'solutions': solutions}


__all__ = [
    'ALL_LEVEL_WORDS',
    'RULE_KEYWORDS',
    'classify_name',
    'is_level_word',
    'is_param_name',
    'is_position_name',
    'normalize_level_word',
    'parse_rule',
    'split_phase',
]
