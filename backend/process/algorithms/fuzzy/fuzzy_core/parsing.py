"""规则词法解析（公开 API）

从 `fuzzy_core/models/nets.py` 抽出的词法工具，供**算法层**与**规则层**共用：

- `split_phase()`  把一个规则词法单元解析为结构化字段
- `classify_name()`  判定名字是"缺陷"还是"工艺参数"
- `collect_param_names()`  从规则串中收集"工艺参数名"

为什么公开化（2026-10-20）：
- 算法层（`fuzzy_algorithm.py`）需要按规则串反推"这条规则涉及哪些参数"，
  以便按需拉取 RuleKeyword 元数据。它过去自己写了一套粗糙的字符串切分
  （只收"首字母非大写"的词），而规则库里的参数名全是大写（IV0/MBP0/...），
  结果恒定收集到 0 个参数 → 工厂级永远拿不到论域 → 整层被跳过。
- 规则层（`rule_query_service.py`）需要按"结论形态"分流规则，同样要复用
  同一套词法语义，避免两处对 `X_add_2` / `X_adjust_提示语` 的理解不一致。

原位置（`models/nets.py`）保留 `_split_phase` / `_classify_name` 别名，
避免历史 import 断裂。

命名空间说明：
- 规则库段号以 0-based 为主（IV0/MBP0/BT/...），与 RuleKeyword 的
  `IV0~IV5` / `PP0~PP4` 完全吻合，不要在这里做 0/1-based 转换。
"""

from typing import Dict, Iterable, List, Set

from .macros import ALL_LEVEL_WORDS, DEFECT_CONST


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
    #   从右往左找到第一个已知 level 词，剩下的 prefix 全部是 name
    for i in range(len(parts) - 1, 0, -1):
        if parts[i] in ALL_LEVEL_WORDS:
            name = '_'.join(parts[:i])
            level = parts[i]
            return {'name': name, 'level': level, 'kind': 'precondition'}

    # ---- 兜底：老 fuzzykit 风格（按空格 + 第一段下划线拆分）---------------
    #   注：兜底结果的 level 未必是合法等级词（如 'worse'），调用方必须
    #   用 is_level_word() 复核后再查 HS_MAPPING_DICT。
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

    老 fuzzykit 写 'mid'，前端 LEVEL_WORDS 与规则库 rule_description 写
    'medium'，两者同义（都是第 2 档）。比较前必须先归一，否则同一个档位
    会被当成两档。
    """
    w = str(word or '').lower()
    return {'mid': 'medium'}.get(w, w)


def is_position_name(name: str) -> bool:
    """是否缺陷位置名（`DL` + 缺陷名 + 段号，如 `DLOVERSIZE1`）。"""
    return bool(name) and name.upper().startswith('DL')


def collect_param_names(rule_strings: Iterable[str]) -> Set[str]:
    """从规则串中收集"工艺参数名"（剔除缺陷名与缺陷位置名）。

    前件与结论的参数都要收：模糊推理需要两侧都有 RuleKeyword 元数据，
    缺结论侧元数据会让该条规则的调整量整体丢失。

    Args:
        rule_strings: 规则字符串列表

    Returns:
        参数名集合
    """
    names: Set[str] = set()
    for rule_str in rule_strings:
        for word in (rule_str or '').split():
            if word in RULE_KEYWORDS:
                continue
            name = split_phase(word).get('name')
            if not name:
                continue
            if is_position_name(name):
                continue
            if classify_name(name) == 'defect':
                continue
            names.add(name)
    return names


def parse_rule_words(rule_str: str) -> List[Dict[str, str]]:
    """把一条规则串拆成有序的词法单元列表（跳过 IF / AND / THEN）。"""
    return [
        split_phase(word)
        for word in (rule_str or '').split()
        if word not in RULE_KEYWORDS
    ]


def parse_rule(rule_str: str) -> Dict[str, List[Dict[str, str]]]:
    """把一条规则串拆成前件 / 结论两部分。

    Returns:
        {'preconditions': [...], 'solutions': [...]}
        每个元素是 `split_phase()` 的结果 dict。
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
        if is_pre:
            preconditions.append(info)
        else:
            solutions.append(info)
    return {'preconditions': preconditions, 'solutions': solutions}


__all__ = [
    'ALL_LEVEL_WORDS',
    'RULE_KEYWORDS',
    'classify_name',
    'collect_param_names',
    'is_level_word',
    'is_position_name',
    'normalize_level_word',
    'parse_rule',
    'parse_rule_words',
    'split_phase',
]
