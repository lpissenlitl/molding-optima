"""资源仓库 —— 算法实际要用的资源（规则 + 关键字）的取用入口。

编排四步：
1. 选库：用户显式指定 → 按产品/聚合物展开的候选 → 通用兜底库；
2. 收集：按四级特异级（精确 / 部分polymer / 部分product / 默认）从各库收集 method；
3. 组装：过滤 + 判定结论形态 → `List[RuleProfile]`（内核输入契约）；
4. 组合：把 rule 资源与 keyword 资源组合给编排层。

编排层只认 `library/contracts.py` 的 `AlgorithmResourceRepository` 协议。
"""

import logging
from typing import List

from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile, RuleProfile
from process.algorithms.fuzzy.library.keywords import KeywordQueryService
from process.algorithms.fuzzy.library.contracts import RuleQueryContext
from process.algorithms.fuzzy.library.rules import (
    RuleAdapter,
    RuleQueryService,
    RuleService,
)
from process.models.rules import RuleLibrary


logger = logging.getLogger(__name__)


# --- ResourceRepository ---

class ResourceRepository:
    """规则 + 关键字的取用入口。

    是 `library/contracts.py::AlgorithmResourceRepository` 协议的默认实现。
    只负责路由与组织，不执行任何模糊推理。
    """

    # —— 编排：把规则库组织成算法要用的规则 ——————————————————

    @classmethod
    def select_libraries(cls, context: RuleQueryContext) -> List[RuleLibrary]:
        """根据上下文解析目标规则库（按优先级排序）。

        三步：用户显式指定 → 按产品/聚合物展开的候选 → 通用兜底库。
        """
        codes = []

        # 1) 用户显式指定
        if context.rule_library_code:
            codes.append(context.rule_library_code)

        # 2) 按上下文产品/聚合物找匹配的库
        if context.product_category:
            codes.extend(RuleService.product_to_library_codes(context.product_category))

        libraries = RuleQueryService.get_libraries_by_codes(codes)

        # 3) 通用兜底库（必须存在）
        #    library_code='base'（library_type='fuzzy'，priority=100）
        #    库里没有 'general' 这个 library_code → 兜底库永远找不到
        for lib in RuleQueryService.get_libraries_by_codes(['base'], library_type='fuzzy'):
            if lib not in libraries:
                libraries.append(lib)

        # 按 priority 降序
        return sorted(libraries, key=lambda l: -l.priority)

    @classmethod
    def get_rules(cls, context: RuleQueryContext) -> List[RuleProfile]:
        """按四级特异级匹配拉出 RuleMethod，组装成内核输入契约。

        规则串直接取 `RuleMethod.rule_description`（格式：
        `IF SHORTSHOT_low AND IV0_low THEN IV0_add_2`）。

        返回按 (specificity 升序, priority 降序) 排序，便于上层加权推理。
        """
        libraries = cls.select_libraries(context)
        if not libraries:
            logger.warning('[ResourceRepository] 未找到任何可用规则库: %s', context)
            return []

        # 四级特异级匹配
        # L1 精确：polymer 匹配 + product 匹配
        # L2 部分-polymer：polymer 匹配 + product=None
        # L3 部分-product：polymer=None + product 匹配
        # L4 默认：polymer=None + product=None
        specificity_filters = [
            (1, context.polymer_abbreviation, context.product_category),
            (2, context.polymer_abbreviation, None),
            (3, None, context.product_category),
            (4, None, None),
        ]

        all_rules: List[RuleProfile] = []
        seen_ids = set()

        for lib in libraries:
            for specificity, polymer, product in specificity_filters:
                methods = RuleQueryService.get_methods(
                    lib, polymer, product, context.defect_name,
                )
                for rm in methods:
                    if rm.id in seen_ids:
                        continue
                    # 契约构造归 RuleAdapter（来源适配层），编排层只做过滤
                    profile = RuleAdapter.to_rule_profile(rm, specificity)
                    if profile is None:      # 规则串为空
                        continue
                    if not RuleService.match_defect_level(
                        profile.rule_description, context,
                    ):
                        continue
                    seen_ids.add(rm.id)
                    all_rules.append(profile)

        # 排序：specificity 升序优先（同特异性 priority 降序）
        all_rules.sort(key=lambda r: (r.specificity, -r.priority))
        return all_rules

    # —— 组合：把 keyword 资源并进来 ——————————————————————————

    @classmethod
    def get_keywords_by_names(cls, names) -> List[KeywordProfile]:
        """按参数名批量取论域元数据（`RuleKeyword`）。

        编排层访问字段元数据的唯一入口，不需要知道 `RuleKeyword` 这个 ORM 模型。

        查库在 `KeywordQueryService`，此处**原样转发**内核契约
        `KeywordProfile`（不再转成内核 `keyword_array` 元素 dict ——
        net 现在直接吃契约对象，多这一层转换只会把契约掐断）。
        排序在这里做（ORM 的 `__in` 查询与顺序无关，但调用方要稳定序）。
        """
        if not names:
            return []
        return KeywordQueryService.get_keywords_by_names(sorted(names))
