"""规则对象 —— FuzzyRule / NumTskRule。

**层定位**：模糊推理五层流程的第 4 层（filter 分类建对象）的**产物类型**。

五层流程：

    ① 读取(ORM) → ② 契约化(RuleProfile) → ③ 适用性筛选
    → ④ **filter：拆一次 → 分类 → 建对象**（本模块的类在这里被创建）
    → ⑤ 推理（Mamdani / 0 阶 TSK）

第 4 层的**唯一入口**是 `fuzzy_core.rules_filter.build_rule_objects`：
它负责拆解规则串（每条规则只拆一次），并把拆解产物交给本模块的类。
⇒ 本模块的类**不再自己拆规则串**，只做「拆解产物 → 策略化结构」的组装。

两个类 = **两种结论取舍策略**，共用同一份拆解产物：

- `FuzzyRule`   提示层（Mamdani）：结论**全收**（等级词结论）
- `NumTskRule` 数值层（0 阶 TSK）：结论**两路分流**（popup 隔离 / 数值）

⚠️ **代数式结论（`X=a*Y+b*Z`）已从内核移除**（2026-10-27）：它在第 4 层
filter 就被判为 advisory（无 action）⇒ 永远不会进 `NumTskRule`，
原 `parameter_vector` 分支是**永不执行的死代码**；且它恒为全零向量
（`np.zeros`），即便执行也只会算出 0。现改为在 filter 层**显式跳过并留痕**
（见 `rules_filter.build_rule_objects`）。

⚠️ 二者**不做继承**：`RuleProfile` 不是基类。规则档案与解析产物是**组合**
   关系（规则对象持有 profile 引用），契约层不被内核反向污染。

⚠️ 词法底座统一在 `fuzzy_core.parsing`（`parse_rule` / `classify_name`），
   本模块不重复实现切词逻辑。
"""

from typing import Dict, List

from ..macros import ACTION_MAP
from ..parsing import classify_name as _classify_name
from ..profiles import RuleProfile


__all__ = ['FuzzyRule', 'NumTskRule']


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
    r_extra         : {原始结论词: value}（弹窗规则）

    结论策略：**两路分流** ——
      1. ``_popup_xxx``              → r_extra（只作提示，不进数值矩阵）
      2. ``_add_10`` / ``_reduce_5%`` → r_solutions（数值结论）

    ⚠️ 代数式结论（``X=a*Y+b*Z``）**不在此处理** —— 它在第 4 层 filter
       就被判为 advisory 并跳过（内核不支持该形态），不会走到这里。
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
        return r_solutions, r_extra

    def __repr__(self):
        return self.r_rule

