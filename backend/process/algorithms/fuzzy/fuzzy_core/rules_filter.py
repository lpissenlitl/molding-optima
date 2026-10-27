"""第 4 层：filter —— 规则分类与对象构建（**内核唯一入口**）。

**层定位**：模糊推理五层流程的第 4 层。

    ① 读取(ORM) → ② 契约化(RuleProfile) → ③ 适用性筛选
    → ④ **本模块：拆一次 → 分类 → 建对象** → ⑤ 推理（Mamdani / 0 阶 TSK）

**输入**
    ``List[RuleProfile]`` —— 第 2 层契约化、第 3 层适用性筛选之后的规则档案。

**输出**
    ``FilteredRules`` —— 三类归属的规则对象 + 提示文本 + 各自的参数名集合。

**为什么在这一层**
- 规则串**只拆一次**：拆解产物同时供「分类」「建对象」「收参数名」三处使用
- 分类与建对象**同处一处**：编排层不再持有分流逻辑，也不再碰规则串
- 编排层因此**零解析**：它只负责把 Profile 列表交给本模块，再把产物交给 net

**三段判定**（口径固定，不做"优化"）：

1. **结论形态** —— 与 `library/rules.py::classify_conclusion_kind` 同口径：
   只要有一个结论的动作不是 add/reduce ⇒ advisory；
   全是 add/reduce 时，至少一个结论值是数字 ⇒ numeric。
2. **数值可推理性** —— 数值类规则的所有结论值都必须是数字，
   否则送进数值层会 ``float('low')`` 抛 ValueError ⇒ **一条脏规则拖垮整层**
   ⇒ 这类规则整条跳过。
3. **检查类识别** —— 提示类规则里只要有 adjust/popup 结论 ⇒
   整条按"检查类"处理（出提示文本）。

⚠️ 第 1 段比第 2 段**松**（第 1 段"至少一个数字"、第 2 段"全部数字"）⇒
   混合规则（``THEN IV0_add_2 AND IV0_add_low``）会被第 1 段判为 numeric、
   再被第 2 段挡下 ⇒ **不进任何一层**。本模块保留这一行为（进 ``skipped``）。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .models.rules import FuzzyRule, NumTskRule
from .parsing import is_param_name, parse_rule
from .profiles import RuleProfile


__all__ = ['AdviceItem', 'FilteredRules', 'build_rule_objects']


# ============================================================================
# 产物类型
# ============================================================================

@dataclass
class AdviceItem:
    """一条文本建议（检查/弹窗类结论）。

    ⚠️ 不含数值：这类结论给的是提示语，不是调整量。
    """

    param_name: str
    advice: str
    rule_description: str


@dataclass
class FilteredRules:
    """第 4 层产物：已分类、已建对象、已收参数名。

    Attributes
    ----------
    numeric_rules : list[NumTskRule]
        数值层（0 阶 TSK）的规则对象 —— 结论是数值/百分比。
    mamdani_rules : list[FuzzyRule]
        提示层（Mamdani）的规则对象 —— 结论是模糊等级词。
    advice_items : list[AdviceItem]
        检查/弹窗类规则的提示文本（不进任何推理网络）。
    numeric_param_names : set[str]
        数值层用到的工艺参数名（决定要拉哪些 RuleKeyword 论域元数据）。
    mamdani_param_names : set[str]
        提示层用到的工艺参数名。
    skipped : list[dict]
        被跳过的规则及原因（诊断信息，不参与推理）。
    """

    numeric_rules: List[NumTskRule] = field(default_factory=list)
    mamdani_rules: List[FuzzyRule] = field(default_factory=list)
    advice_items: List[AdviceItem] = field(default_factory=list)
    numeric_param_names: Set[str] = field(default_factory=set)
    mamdani_param_names: Set[str] = field(default_factory=set)
    skipped: List[Dict[str, str]] = field(default_factory=list)


# ============================================================================
# 判定（口径固定，见文件头说明）
# ============================================================================

def _is_numeric_value(value) -> bool:
    """结论值是否是数值。

    口径与 `library/rules.py::classify_conclusion_kind` **完全一致**
    （同一套 isdigit 判定），保证"判为数值类"⇒"一定可安全推理"。
    """
    text = '' if value is None else str(value)
    return text.rstrip('%').lstrip('-').replace('.', '', 1).isdigit()


def _conclusion_kind(solutions: List[Dict]) -> str:
    """结论形态：'numeric' / 'advisory'。

    复刻 `library/rules.py::classify_conclusion_kind` 的判定口径，
    但输入是**已拆解的结论段**（不再重新拆规则串）。
    """
    has_numeric = False
    for sol in solutions:
        action = sol.get('action')
        if action in ('add', 'reduce'):
            if _is_numeric_value(sol.get('value', '')):
                has_numeric = True
        else:
            return 'advisory'
    return 'numeric' if has_numeric else 'advisory'


def _first_non_numeric_value(solutions: List[Dict]):
    """数值类规则里**第一个**不能安全 float 的结论值（None = 全部安全）。

    adjust / popup 结论不做预检（它们在 net 走特殊分支，不做 float 转换）。
    """
    for sol in solutions:
        action = sol.get('action')
        if action not in ('add', 'reduce'):
            continue
        value = sol.get('value', '')
        if not _is_numeric_value(value):
            return str(value)
    return None


def _has_check_conclusion(solutions: List[Dict]) -> bool:
    """结论里是否有检查/弹窗类（adjust / popup）。

    命中即整条按"检查类"处理（出提示文本，不进推理网络）。
    """
    for sol in solutions:
        if sol.get('action') in ('adjust', 'popup'):
            return True
    return False


def _collect_param_names(parsed: Dict[str, List[Dict]], into: Set[str]) -> None:
    """把一条规则的参数名并进集合（与 `parsing.is_param_name` 同口径）。

    ⚠️ 走的是**已拆解产物**，不再重新拆规则串 ⇒ 第 4 层只拆一次。
    """
    for info in parsed['preconditions'] + parsed['solutions']:
        name = info.get('name')
        if is_param_name(name):
            into.add(name)


# ============================================================================
# 第 4 层入口
# ============================================================================

def build_rule_objects(profiles: List[RuleProfile]) -> FilteredRules:
    """把规则档案分类并建出规则对象（第 4 层唯一入口）。

    Parameters
    ----------
    profiles : list[RuleProfile]
        第 2 层契约化、第 3 层筛选后的规则档案。

    Returns
    -------
    FilteredRules
        三类归属的规则对象 + 提示文本 + 各自的参数名集合 + 跳过明细。

    Notes
    -----
    - 每条规则串**只拆一次**（``parse_rule``），拆解产物同时供
      「分类」「建对象」「收参数名」三处使用
    - 保持输入顺序（各组内部顺序与 ``profiles`` 一致）⇒ 推理结果的排序稳定
    """
    result = FilteredRules()

    for profile in profiles:
        parsed = parse_rule(profile.rule_description)
        solutions = parsed['solutions']

        # ---- 判定 1：结论形态 -------------------------------------------
        if _conclusion_kind(solutions) == 'numeric':
            # ---- 判定 2：数值可推理性 ----------------------------------
            bad_value = _first_non_numeric_value(solutions)
            if bad_value is None:
                result.numeric_rules.append(NumTskRule(profile, parsed))
                _collect_param_names(parsed, result.numeric_param_names)
                continue
            result.skipped.append({
                'rule': profile.rule_description,
                'reason': f'结论值 {bad_value!r} 不是数值，送进数值层会抛 ValueError',
            })
            continue

        # ---- 判定 3：检查/弹窗类 → 提示文本（不进推理网络）--------------
        if _has_check_conclusion(solutions):
            for sol in solutions:
                if sol.get('action') not in ('adjust', 'popup'):
                    continue
                advice = sol.get('value')
                if not advice:
                    continue
                result.advice_items.append(AdviceItem(
                    param_name=sol.get('name', ''),
                    advice=advice,
                    rule_description=profile.rule_description,
                ))
            continue

        # ---- 提示层（Mamdani）：结论是模糊等级词 -------------------------
        result.mamdani_rules.append(FuzzyRule(profile, parsed))
        _collect_param_names(parsed, result.mamdani_param_names)

    return result
