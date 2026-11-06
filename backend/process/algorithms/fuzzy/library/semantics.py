"""语义层 —— 规则语义的**唯一判定口径**（零 ORM）。

`RuleService` 只回答「这条规则是什么 / 适不适用 / 谁更该被采信」，
**不取数、不碰数据库**。数据库来源与文件来源**共用同一份** ⇒ 两条路径的
判定结果不可能分叉。

⚠️ **为什么独立成文件**：它必须能被**零 ORM** 地引入 —— 文件来源
（`library/files/`）不能因为要一个语义判定就把 Django ORM 拖进来
（依赖倒置的实质检验 = 「高层不被低层实现拖住」）。
它与 `RuleQueryService`（查询线，必然碰 ORM）分离，文件来源可直接复用。

`library/rules.py` 保留 `from .semantics import RuleService` 的兼容导出，
既有引用路径不变。
"""

from typing import Dict, List, Optional

from process.algorithms.fuzzy.fuzzy_core.parsing import (
    classify_conclusion_kind as classify_kind,
    parse_rule,
)
from process.algorithms.fuzzy.library.contracts import RuleQueryContext


class RuleService:
    """规则语义服务 —— 判断规则「是什么」，不取数。

    不 import ORM，也不接受 ORM 实例；「取哪条规则」由来源侧负责
    （数据库来源见 `library/rules.py::RuleQueryService`，
    文件来源见 `library/files/`）。
    """

    # —— 「通用」标签（该维无具体信息）———————————————————————————

    #: 「通用」标签集合 —— 该维**没有具体信息**的字面值。
    #:
    #: ⚠️ **为什么除 NULL 外还要认字面值**：
    #:   规则标注里的「通用」不是「NULL 没填」，而是**明确写了"适用于所有
    #:   产品/材料"** —— 业务含义与 NULL 相同（该维不设限），但取值不同。
    #:   如 `R20240702164137` 的 155 条规则 `product_category`
    #:   **全部是字面值「通用」（非 NULL）** ⇒ 若只认 NULL，这批规则
    #:   **在任何上下文下都会被判为"产品类别冲突"而永不生效**。
    #:
    #: ⚠️ **规则侧与上下文侧同义**：规则侧「通用」= 该规则不针对具体产品；
    #:   上下文侧「通用」= 当前模具没有明确产品大类 ⇒ 两边都按
    #:   「该维无具体信息」处理：不冲突、不计匹配。
    GENERIC_LABELS = frozenset({'通用'})

    @staticmethod
    def is_generic_label(value: Optional[str]) -> bool:
        """该维是否**没有具体信息**（NULL 或「通用」字面值）。

        Args:
            value: 规则标注值或上下文值（`None` = NULL）。

        Returns:
            该维是否为通用（不设限、不计匹配）。
        """
        if value is None:
            return True
        return value.strip() in RuleService.GENERIC_LABELS

    # —— 规则串拆解（**唯一解析入口**）———————————————————————————————

    @staticmethod
    def parse_rule(rule_str: str) -> Dict[str, List[Dict[str, str]]]:
        """规则串 → 拆解产物（**全链路唯一解析入口**）。

        ⚠️ **为什么收拢到语义层**：规则串的拆解是纯函数，但调用点曾散在
        三处（来源适配层判结论形态 / 编排层判缺陷名 / 内核第 4 层建对象），
        同一条规则串被拆三次（1646 条 ⇒ 约 5000 次）。

        ⚠️ **正确用法**：拆一次，把产物放进 `RuleProfile.parsed`，
        下游一律**复用**它（`parsed=None` 时才各自兜底拆解）。
        """
        return parse_rule(rule_str)

    # —— 适用性判定 ————————————————————————————————————————

    @staticmethod
    def matches_context(
        rule_polymer: Optional[str],
        rule_product: Optional[str],
        ctx_polymer: Optional[str],
        ctx_product: Optional[str],
    ) -> bool:
        """规则的聚合物 / 产品两维是否适用于当前上下文（**匹配谓词的唯一口径**）。

        语义：

        - 上下文该维**已知**（有具体值）⇒ 规则该维必须为「通用」或**等于**上下文值；
        - 上下文该维**未知**（None 或「通用」字面值）⇒ 该维**不加任何限制**
          ——「未指明」≠「不适用」；
        - 上下文已知、规则该维有值但**不等** ⇒ **冲突排除**（该规则不参与）。

        ⚠️ **为什么要有这个纯函数**：两条来源（数据库 / 文件）都只负责
          「取回候选」，适用性判定统一走这里 —— 两份实现一旦分叉，同一批规则
          在两条路径下的命中集合就会不同，而且**极难察觉**（不报错，只是结果
          悄悄不同）。本函数是**唯一真相源**：两条来源都调它。

        Args:
            rule_polymer: 规则标注的聚合物缩写（NULL / 「通用」= 通用）。
            rule_product: 规则标注的产品类别（NULL / 「通用」= 通用）。
            ctx_polymer: 上下文聚合物缩写（None / 「通用」= 未指明）。
            ctx_product: 上下文产品类别（None / 「通用」= 未指明）。

        Returns:
            该规则是否适用于当前上下文。
        """
        if (not RuleService.is_generic_label(ctx_polymer)
                and not RuleService.is_generic_label(rule_polymer)
                and rule_polymer != ctx_polymer):
            return False
        if (not RuleService.is_generic_label(ctx_product)
                and not RuleService.is_generic_label(rule_product)
                and rule_product != ctx_product):
            return False
        return True

    @staticmethod
    def match_defect_name(
        rule_str: str,
        context: RuleQueryContext,
        parsed: Optional[Dict[str, List[Dict[str, str]]]] = None,
    ) -> bool:
        """规则前件的缺陷是否与反馈缺陷一致（**只比缺陷名，不比档位**）。

        规则库约定：缺陷一定是第一个前件（1646 条规则实测 100% 一致），格式
        `IF {defect}_{level} AND ...`。

        ⚠️ 档位（缺陷程度）**不在这里过滤**：程度已作为**算法输入**进推理网络
        （见 ``engine._build_defect_inputs``），由隶属度表达「越严重越激进」。
        若此处仍按档位硬切，有两个问题：

        1. **重复表达**：档位被表达了两次（选规则一次、激活度一次），
           且两处口径本就不同（这里是字符串相等，激活度是论域上的桶中心距离）。
        2. **砍掉合法输入**：缺陷关键词是 5 档（very_low ~ very_high），
           而规则库只写了 low/medium/high 三档 ⇒ 用户选「极轻微 / 极严重」时
           规则被**全部切光** ⇒ 对外报「无可用规则」。

        ⇒ 本闸门只守「确定不该参与」的边界：缺陷名对不上 ⇒ 拒绝。

        Args:
            rule_str: 规则串（仅在 `parsed` 未给出时用于拆解）。
            context: 查询上下文。
            parsed: 已拆解的产物（**优先使用**）。给出它就不重复拆解 ——
                这是「规则串只拆一次」在编排层的落点。
        """
        if not context.defect_name:
            return True
        if parsed is None:
            parsed = parse_rule(rule_str)
        preconditions = parsed['preconditions']
        if not preconditions:
            return True
        first = preconditions[0]
        return first.get('name') == context.defect_name

    @staticmethod
    def resolve_specificity(
        rule_polymer: Optional[str],
        rule_product: Optional[str],
        ctx_polymer: Optional[str],
        ctx_product: Optional[str],
    ) -> int:
        """规则相对当前上下文的真实特异级（1=精确 / 2=部分polymer / 3=部分product / 4=默认）。

        「上下文为 None / 「通用」」表示该维度**未指定** ⇒ 不算匹配。

        例：规则 poly=None/prod='碗'、上下文 poly=None/prod='碗'
        ⇒ 只有产品维度匹配 ⇒ 3（部分-product），而不是「精确级」。

        ⚠️ **规则侧写「通用」也不算匹配**：规则标注「通用」= 该规则**没有**
          针对某个具体产品/材料 ⇒ 不能因为上下文里恰好也写了「通用」就说它
          命中了产品维度（那会让 155 条「通用」规则被误标成产品专用规则）。
          同理，规则写「通用」而上下文写了具体产品（如 '酒瓶'）⇒ 也不算匹配
          —— 规则没有针对酒瓶，只是**不冲突**。

        ⚠️ 特异级是**相对当前上下文**的概念：同一条规则在不同上下文下取值不同。
        这也是它不能由「规则落在哪次查询里」反推的原因 —— 取数已改成**单次
        匹配谓词查询**（不分四级过滤器），上下文缺维度时也没有「先到的那一级」
        可言 ⇒ 只能由规则标签与上下文逐维比对算出。
        """
        polymer_match = (
            not RuleService.is_generic_label(ctx_polymer)
            and not RuleService.is_generic_label(rule_polymer)
            and rule_polymer == ctx_polymer
        )
        product_match = (
            not RuleService.is_generic_label(ctx_product)
            and not RuleService.is_generic_label(rule_product)
            and rule_product == ctx_product
        )
        if polymer_match and product_match:
            return 1
        if polymer_match:
            return 2
        if product_match:
            return 3
        return 4

    @staticmethod
    def dedupe_key(defect_code: Optional[str], rule_description: Optional[str]):
        """业务内容去重键：``(defect_code, 归一化后的规则串)``。

        ⚠️ **为什么不用规则主键**：同一业务规则常同时存在于多个库
        （`base` 通用库 + 产品专用库），用主键去重会把它们当成不同的规则，
        同一建议就会被算两遍。业务内容相同 ⇒ 视为同一条规则。

        规则串只做 ``strip()`` 归一（实测 1646 条中 0 条带首尾空白，
        归一不引入额外合并）；中间内容一字不改。
        """
        return (defect_code or '', (rule_description or '').strip())

    @staticmethod
    def prefer_candidate(
        new_specificity: int,
        new_priority: float,
        old_specificity: int,
        old_priority: float,
    ) -> bool:
        """去重时新候选是否应该顶替旧候选。

        判据（**真实特异级优先**）：
        1. 特异级更高者胜（数值更小 = 更特异）：产品库的规则针对当前产品，
           通用库的规则只是兜底 —— 业务上前者才是当前情境下该用的那条。
        2. 特异级相同时，``priority`` 更高者胜。
        3. 仍相同则保留先到的那条（由调用方保证顺序稳定）。
        """
        if new_specificity != old_specificity:
            return new_specificity < old_specificity
        return new_priority > old_priority

    @staticmethod
    def classify_conclusion_kind(
        rule_str: str,
        parsed: Optional[Dict[str, List[Dict[str, str]]]] = None,
    ) -> str:
        """按结论形态判定规则所属推理层。

        这里的「层」指结论能不能算出数值，与规则库的组织维度（base 库 / 产品库 /
        特异级）无关。

        - 'numeric'：数值结论（`X_add_2` / `X_reduce_3` / `X_reduce_30%`）
          → 数值层零阶 TSK 推理（NumTskRuleNet）
        - 'advisory'：提示类结论（`X_adjust_请检查锁模力是否不合理。`）
          或模糊等级结论（`X_add_low`）
          → 提示层（文本建议 / Mamdani 全模糊推理）

        ⚠️ 判定口径**不在本层**：统一走 `fuzzy_core.parsing.classify_conclusion_kind`
        （与 `is_numeric_value` 同一份真相源）⇒ 规则层与第 4 层 filter
        不会把同一批规则分流到不同的推理层。

        Args:
            rule_str: 规则串（仅在 `parsed` 未给出时用于拆解）。
            parsed: 已拆解的产物（**优先使用**）⇒ 不重复拆解。
        """
        if parsed is None:
            parsed = parse_rule(rule_str)
        return classify_kind(parsed['solutions'])
