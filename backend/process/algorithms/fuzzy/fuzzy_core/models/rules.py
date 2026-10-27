"""规则对象 —— FuzzyRule / NumTskRule / ParticularRules。

**层定位**：模糊推理五层流程的第 4 层（filter 分类建对象）的**产物类型**。

五层流程：

    ① 读取(ORM) → ② 契约化(RuleProfile) → ③ 适用性筛选
    → ④ **filter：拆一次 → 分类 → 建对象**（本模块的类在这里被创建）
    → ⑤ 推理（Mamdani / 0 阶 TSK）

第 4 层的**唯一入口**是 `fuzzy_core.rules_filter.build_rule_objects`：
它负责拆解规则串（每条规则只拆一次），并把拆解产物交给本模块的类。
⇒ 本模块的类**不再自己拆规则串**，只做「拆解产物 → 策略化结构」的组装。

三个类 = **三种结论取舍策略**，共用同一份拆解产物：

- `FuzzyRule`       提示层（Mamdani）：结论**全收**（等级词结论）
- `NumTskRule`     数值层（0 阶 TSK）：结论**三路分流**（popup 隔离 / 数值 / 代数）
- `ParticularRules` 异类：不做推理，只抽「缺陷名 + 提示语」

⚠️ 三者**不做继承**：`RuleProfile` 不是基类。规则档案与解析产物是**组合**
   关系（规则对象持有 profile 引用），契约层不被内核反向污染。

⚠️ 词法底座统一在 `fuzzy_core.parsing`（`parse_rule` / `classify_name`），
   本模块不重复实现切词逻辑。
"""

from typing import Dict, List

import numpy as np

from ..macros import ACTION_MAP, DEFECT_CONST
from ..parsing import classify_name as _classify_name
from ..profiles import RuleProfile


__all__ = ['FuzzyRule', 'NumTskRule', 'ParticularRules']


# ============================================================================
# 共用：拆解产物 → 前件结构（两种策略的前件完全相同）
# ============================================================================

def _build_preconditions(preconditions: List[Dict]) -> Dict[str, Dict]:
    """拆解产物的前件段 → 内核现行 dict 形态。

    Parameters
    ----------
    preconditions : list
        `parsing.parse_rule` 的 ``preconditions`` 段。

    Returns
    -------
    dict
        ``{param_name: {name, level, p_type}}``
    """
    result: Dict[str, Dict] = {}
    for info in preconditions:
        name = info['name']
        result[name] = {
            'name': name,
            'level': info.get('level', ''),
            'p_type': _classify_name(name),
        }
    return result


# ============================================================================
# FuzzyRule: Mamdani 规则（提示层用）
# ============================================================================

class FuzzyRule:
    """提示层（Mamdani）规则对象。

    输入
    ----
    profile : RuleProfile
        规则档案（契约层产物）：规则串 + 优先级 + 特异级 + 溯源。
    parsed : dict
        词法拆解产物（`parsing.parse_rule` 的返回值），由第 4 层 filter 拆一次后传入。

    输出（内核现行形态）
    --------------------
    r_preconditions : {param_name: {name, level, p_type}}
    r_solutions     : {param_name: {name, action, level, s_type}}

    结论策略：**全收** —— 等级词结论（`X_add_low`）与提示类结论都进
    `r_solutions`（提示层只按档位查隶属度，不需要区分结论形态）。
    """

    def __init__(self, profile: RuleProfile, parsed: Dict[str, List[Dict]]):
        self.profile = profile
        self.r_rule = profile.rule_description
        self.r_preconditions = _build_preconditions(parsed['preconditions'])
        self.r_solutions = self._build_solutions(parsed['solutions'])

    @staticmethod
    def _build_solutions(solutions: List[Dict]) -> Dict[str, Dict]:
        """拆解产物的结论段 → 全收策略的 dict 形态。"""
        result: Dict[str, Dict] = {}
        for info in solutions:
            name = info['name']
            action = info.get('action', '')
            # 结论值存于 'level' 字段（内核现行形态）
            result[name] = {
                'name': name,
                'action': ACTION_MAP.get(action, 0),
                'level': info.get('value', ''),
                's_type': 'process',
            }
        return result

    def __repr__(self):
        return self.r_rule


# ============================================================================
# NumTskRule: 数值结论规则（数值层用）
# ============================================================================

class NumTskRule:
    """数值层（0 阶 TSK）规则对象。

    输入
    ----
    profile : RuleProfile
        规则档案（契约层产物）。
    parsed : dict
        `parsing.parse_rule` 的返回值。

    输出（内核现行形态）
    --------------------
    r_preconditions : {param_name: {name, level, p_type}}
    r_solutions     : {param_name: {name, action, level, s_type}}
                       或 {param_name: {name, parameter_vector, ratio_vector, s_type}}
    r_extra         : {原始结论词: value}（弹窗规则）

    结论策略：**三路分流** ——
      1. ``_popup_xxx``              → r_extra（只作提示，不进数值矩阵）
      2. ``_add_10`` / ``_reduce_5%`` → r_solutions（数值结论）
      3. 代数式 ``X=a*Y+b*Z``         → r_solutions（向量形态，预留接口）
    """

    def __init__(self, profile: RuleProfile, parsed: Dict[str, List[Dict]]):
        self.profile = profile
        self.r_rule = profile.rule_description
        self.r_preconditions = _build_preconditions(parsed['preconditions'])
        self.r_solutions, self.r_extra = self._build_conclusions(parsed['solutions'])

    @staticmethod
    def _build_conclusions(solutions: List[Dict]):
        """拆解产物的结论段 → 三路分流策略。

        Returns
        -------
        (dict, dict)
            ``(r_solutions, r_extra)``
        """
        r_solutions: Dict[str, Dict] = {}
        r_extra: Dict[str, str] = {}
        for info in solutions:
            action = info.get('action', '')
            name = info['name']
            value = info.get('value', '')
            phase = info.get('phase', '')

            if action == 'popup':
                # 弹窗规则结论：仅作 r_extra 提示，不进数值矩阵
                r_extra[phase] = value
            elif action in ('add', 'reduce', 'adjust'):
                r_solutions[name] = {
                    'name': name,
                    'action': ACTION_MAP.get(action, 0),
                    'level': value,
                    's_type': 'process',
                }
            elif info.get('kind') == 'algebra':
                # 代数式结论（极少见，预留接口）
                expressions = phase.split('=')
                items = expressions[1].split('+')
                parameter_vector = np.zeros(len(items))
                ratio_vector = np.zeros(len(items))
                for i, item_str in enumerate(items):
                    item = item_str.split('*')
                    ratio = item[0]
                    if '(' in ratio or ')' in ratio:
                        ratio_vector[i] = float(ratio[1:-1])
                    else:
                        ratio_vector[i] = float(ratio)
                r_solutions[expressions[0]] = {
                    'name': expressions[0],
                    'parameter_vector': parameter_vector,
                    'ratio_vector': ratio_vector,
                    's_type': 'process',
                }
        return r_solutions, r_extra

    def __repr__(self):
        return self.r_rule


# ============================================================================
# ParticularRules: 弹窗/提示规则
# ============================================================================

class ParticularRules:
    """弹窗/提示规则抽取器（**异类**：不做推理，只抽缺陷名与提示语）。

    与前两个类的区别：它**不产 preconditions / solutions**，而是产出
    ``{'rule_description', 'rule_defect'?, 'rule_output'?}``。

    输入
    ----
    profiles : list[RuleProfile]
        规则档案列表。
    parsed_list : list[dict]
        与 ``profiles`` **等长同序**的 `parsing.parse_rule` 返回值。

    输出
    ----
    adjust_rule_list : list[dict]
        每条 ``{'rule_description', 'rule_defect'?, 'rule_output'?}``
    """

    def __init__(self, profiles: List[RuleProfile],
                 parsed_list: List[Dict[str, List[Dict]]]):
        self.adjust_rule_list = self._rule_process(profiles, parsed_list)

    @staticmethod
    def _rule_process(profiles: List[RuleProfile],
                      parsed_list: List[Dict[str, List[Dict]]]):
        """从规则档案 + 拆解产物中抽出关联缺陷与输出文本。"""
        output_list = []
        for profile, parsed in zip(profiles, parsed_list):
            item = {'rule_description': profile.rule_description}
            for info in parsed['preconditions']:
                # ⚠️ 已知缺陷：这里按 `split('_')[0]` 取缺陷名，
                #    `GLOSS_VARIATION` 这类含下划线的缺陷名会被截断成 'GLOSS'
                #    ⇒ 查不到 DEFECT_CONST ⇒ rule_defect 漏判。
                #    正确做法是用 `split_phase` 拆出的 `info['name']`。
                #    该类生产零调用，暂不混入行为变化。
                words = info.get('phase', '').split('_')
                if words[0] not in DEFECT_CONST:
                    continue  # 工艺参数条件，跳过
                item['rule_defect'] = words[0]
            for info in parsed['solutions']:
                # 弹窗/检查类结论：用词法解析取完整提示语
                # （提示语本身可能含下划线，不能按 split('_')[2] 截断）
                if info.get('action') in ('adjust', 'popup') and info.get('value'):
                    item['rule_output'] = info['value']
            output_list.append(item)
        return output_list
