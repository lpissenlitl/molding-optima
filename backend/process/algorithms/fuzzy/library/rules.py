"""规则资源 —— 规则的取数与语义判定。

规则分两层：library（规则库分组 `RuleLibrary`）、method（挂在库下的规则条目 `RuleMethod`）。

- `RuleQueryService`：查库（依赖 ORM）
- `RuleService`：规则串语义判定（不查库），文件来源可复用同一份
- `ResourceRepository`（`library/repository.py`）负责把规则组织成算法要用的资源
"""

from typing import List, Optional

from process.algorithms.fuzzy.fuzzy_core.parsing import (
    normalize_level_word,
    parse_rule,
)
from process.algorithms.fuzzy.fuzzy_core.profiles import RuleProfile
from process.algorithms.fuzzy.library.contracts import RuleQueryContext
from process.models.rules import RuleLibrary, RuleMethod


# --- RuleQueryService: 查询侧（只访问数据库，不含业务判断） ---

class RuleQueryService:
    """规则查询服务 —— 只把数据从库里取出来，不做业务判断。

    「哪条规则适用」由 `RuleService` 判断。

    规则库以 ORM 实例在内部传递（而非 `library_code` 字符串）：同一
    `library_code` 可能对应多条库记录（不同 company），改用字符串会改变
    SQL 语义与命中条数。
    """

    @staticmethod
    def get_libraries_by_codes(
        codes: List[str],
        library_type: Optional[str] = None,
    ) -> List[RuleLibrary]:
        """按候选编码逐个查库，返回命中的规则库（保持候选顺序）。

        逐个查（而非 `library_code__in` 一次查完）是有意为之：命中结果最终按
        `priority` 降序稳定排序，同 priority 时候选顺序决定先后。改成批量查询
        会改变同 priority 库的相对顺序，进而改变下游规则遍历顺序。

        Args:
            codes: 候选规则库编码（按优先级从高到低）。
            library_type: 可选的库类型过滤（兜底库用 `'fuzzy'`）。

        Returns:
            命中的 `RuleLibrary` 列表（去重，顺序 = 候选顺序）。
        """
        libraries: List[RuleLibrary] = []
        for code in codes:
            qs = RuleLibrary.objects.filter(
                library_code=code,
                is_active=True,
                is_deleted=False,
            )
            if library_type:
                qs = qs.filter(library_type=library_type)
            lib = qs.first()
            if lib and lib not in libraries:
                libraries.append(lib)
        return libraries

    @staticmethod
    def get_methods(
        rule_library: RuleLibrary,
        polymer_abbreviation: Optional[str],
        product_category: Optional[str],
        defect_code: str,
    ) -> List[RuleMethod]:
        """按「规则库 + 聚合物 + 产品 + 缺陷」取规则方法。

        排序：``priority`` 降序、``id`` 升序。
        """
        return list(
            RuleMethod.objects.filter(
                rule_library=rule_library,
                polymer_abbreviation=polymer_abbreviation,
                product_category=product_category,
                defect_code=defect_code,
                is_active=True,
                is_deleted=False,
            ).order_by('-priority', 'id')
        )


# --- RuleService: 规则语义（不访问数据库） ---

class RuleService:
    """规则语义服务 —— 判断规则「是什么」，不取数。

    不 import ORM，也不接受 ORM 实例；「取哪条规则」由来源侧负责
    （数据库来源见 `RuleQueryService`）。
    """

    # —— 选库策略（业务约定映射）——————————————————————————————

    @staticmethod
    def product_to_library_codes(product_category: str) -> List[str]:
        """产品类别 → 规则库编码候选列表。

        按「精确产品类 + 大类」两级尝试。只产出编码候选，不查库。
        """
        candidates = []
        # 1) 精确产品类（如 product_category='PE酒瓶' → library_code='PE_bottle'）
        candidates.append(product_category.replace(' ', '_'))

        # 2) 大类约定（product_category '酒瓶' → library_code 'packaging'）
        # 实际项目里这里应通过业务配置表/查找表展开，这里用启发式映射
        major_category_map = {
            '酒瓶': 'packaging',
            '食品包装': 'packaging',
            '化妆品容器': 'packaging',
            '通用包装': 'packaging',
            '汽车件': 'auto_parts',
            '医疗器械': 'medical',
        }
        for keyword, lib_code in major_category_map.items():
            if keyword in product_category and lib_code not in candidates:
                candidates.append(lib_code)

        return candidates

    # —— 适用性判定 ————————————————————————————————————————

    @staticmethod
    def match_defect_level(rule_str: str, context: RuleQueryContext) -> bool:
        """规则前件的缺陷档位是否与反馈档位一致。

        规则库约定：缺陷一定是第一个前件（1646 条规则实测 100% 一致），格式
        `IF {defect}_{level} AND ...`。反馈档位（low/medium/high）决定命中哪一档
        规则 —— 三档规则是三套完全不同的调整方案，不能混用。
        """
        if not context.defect_level:
            return True
        preconditions = parse_rule(rule_str)['preconditions']
        if not preconditions:
            return True
        first = preconditions[0]
        if first.get('name') != context.defect_name:
            return True
        # 本模块内 level 统一指「档位」，结论形态用 conclusion_kind
        defect_level = normalize_level_word(first.get('level'))
        return defect_level == normalize_level_word(context.defect_level)

    @staticmethod
    def classify_conclusion_kind(rule_str: str) -> str:
        """按结论形态判定规则所属推理层。

        这里的「层」指结论能不能算出数值，与规则库的组织维度（base 库 / 产品库 /
        特异级）无关。

        - 'numeric'：数值结论（`X_add_2` / `X_reduce_3` / `X_reduce_30%`）
          → 数值层零阶 TSK 推理（NumTskRuleNet）
        - 'advisory'：提示类结论（`X_adjust_请检查锁模力是否不合理。`）
          或模糊等级结论（`X_add_low`）
          → 提示层（文本建议 / Mamdani 全模糊推理）
        """
        solutions = parse_rule(rule_str)['solutions']
        has_numeric = False
        for sol in solutions:
            action = sol.get('action')
            if action in ('add', 'reduce'):
                value = str(sol.get('value', ''))
                if value.rstrip('%').lstrip('-').replace('.', '', 1).isdigit():
                    has_numeric = True
            else:
                # adjust / popup：检查类结论，不进数值推理层
                return 'advisory'
        return 'numeric' if has_numeric else 'advisory'


# --- RuleAdapter: RuleMethod → RuleProfile ---

class RuleAdapter:
    """`RuleMethod` → `RuleProfile`（内核输入契约）。纯转换器，不访问数据库。

    与 `RuleKeywordAdapter`（`library/keywords.py`）成对：那边管关键字侧，
    这边管规则侧。

    规则串取 `RuleMethod.rule_description`（权威来源）；结论形态由
    `RuleService.classify_conclusion_kind` 判定 —— 语义判定归 `RuleService`，
    本类只负责把来源侧字段搬进契约档案。
    """

    @staticmethod
    def to_rule_profile(
        rule_method: RuleMethod,
        specificity: int,
    ) -> Optional[RuleProfile]:
        """`RuleMethod` 实例 → `RuleProfile`；规则串为空返回 `None`。

        Args:
            rule_method: `RuleMethod` ORM 实例。
            specificity: 特异级 1~4（由取数时的匹配层级决定，不在规则记录里）。
        """
        rule_description = (rule_method.rule_description or '').strip()
        if not rule_description:
            return None
        return RuleProfile(
            rule_description=rule_description,
            priority=float(rule_method.priority or 1.0),
            conclusion_kind=RuleService.classify_conclusion_kind(rule_description),
            specificity=specificity,
            # 溯源标识（字符串，不携带 ORM 对象）
            source_ref=f'RuleMethod:{rule_method.id}',
        )
