"""组装层 —— **来源无关**的规则编排（零 ORM）。

数据库来源（`library/repository.py`）与文件来源（`library/files/`）的差别
只有两步：**选库**与**取方法**。从「取回的方法」到「交给内核的规则档案」
这段逻辑（特异级计算 / 契约构造 / 校验 / 缺陷名匹配 / 跨库去重 / 排序）
**完全来源无关** ⇒ 全部收在这里，两个来源共用。

⚠️ **为什么必须共用**：去重键（业务内容）、特异级（相对当前上下文算出的标签）、
去重时的胜负判据 —— 任何一条在两条路径下写法不同，同一条建议就会被算两遍
或被漏掉，而且**不报错**，只是结果悄悄不同。这类分叉最难查。

⚠️ **本模块零 ORM**：只依赖 `library/contracts.py`（契约）、
`library/semantics.py`（语义）、`library/adapters.py`（转换）与
`fuzzy_core/profiles.py`（内核契约校验）。
"""

import logging
from typing import Dict, List, Optional

from process.algorithms.fuzzy.fuzzy_core.profiles import (
    KeywordProfile,
    RuleProfile,
    keyword_profile_issues,
    rule_profile_issues,
)
from process.algorithms.fuzzy.library.adapters import RuleAdapter
from process.algorithms.fuzzy.library.contracts import (
    LibraryRecord,
    RuleQueryContext,
    RuleRecord,
)
from process.algorithms.fuzzy.library.semantics import RuleService


logger = logging.getLogger(__name__)


class RuleAssembler:
    """来源无关的规则组装。"""

    # —— 选库 ————————————————————————————————————————————————

    @staticmethod
    def library_code_candidates(
        context: RuleQueryContext,
    ) -> Optional[List[str]]:
        """候选规则库编码候选列表。

        1. 用户显式指定（`context.rule_library_code`）⇒ **只用它**
           （用户已经明确圈定了范围，尊重用户的指定）；
        2. 未指定 ⇒ 返回 `None` ⇒ **全部模糊规则库都加载**，
           「哪条规则适用于当前产品/材料」交给**规则级**判定：
           `RuleService.matches_context`（冲突硬排除）
           + `RuleService.resolve_specificity`（特异级打分）。

        ⚠️ **为什么不再按产品类别挑库**（2026-10-29 改造）：
           旧实现用 `RuleService.product_to_library_codes` 把产品类别映射成
           库编码候选，但那张映射表指向的编码（`packaging` / `auto_parts` /
           `medical`）**在库里根本不存在**（实际库码是 `base` 与
           `R2023*`/`R2024*` 这类编号）⇒ 候选必然落空 ⇒ 未显式指定库时
           **永远只加载 base 库**，其余库（占全库 64%）从不参与推理。

           更根本的问题是**职责错位**：产品类别与规则是否匹配，本来就是
           **规则与上下文的关系**，应当由算法按规则自身的材料/产品标注判断
           （这正是 `specs.py` 对 `product_category` 的原始定义：
           「规则库精确筛选键（specificity 1/3）… 填了能命中高特异级规则，
           不填退到默认规则」）。用一张写死的映射表把判断提前做掉，
           既是「逻辑写死」，又让规则库无法按产品灵活增删。

        ⚠️ **不查库**，只产出编码候选 —— 由来源侧拿候选去取库；
           `None` 表示「未指定 ⇒ 全量」，由来源侧取全部模糊库索引。
        """
        if context.rule_library_code:
            return [context.rule_library_code]
        return None

    @staticmethod
    def select_libraries(
        candidates: Optional[List[str]],
        index: Dict[str, LibraryRecord],
    ) -> List[LibraryRecord]:
        """选库（**未指定 ⇒ 全量模糊库**；指定 ⇒ 按候选 + 通用兜底库）。

        两种口径：

        - `candidates is None`（未指定库）⇒ **全量**：取索引里全部
          `is_active` 且 `library_type == 'fuzzy'` 的库
          （专家库不是模糊规则库，不参与）；
        - `candidates` 有值 ⇒ 沿用原口径：
          - 候选编码按顺序取库，**重复的编码只取一次**；
          - 停用的库（`is_active=False`）不取；
          - 候选库**不按库类型过滤**（用户可能显式指定任意库）；
          - 通用兜底库 `base` 追加在最后，且**要求 `library_type == 'fuzzy'`**
            —— 专家库不能当模糊规则库兜底。

        两种口径最后都按 `priority` **降序**稳定排序（同 priority 时候选顺序
        决定先后）。

        Args:
            candidates: 候选库编码（`library_code_candidates` 产出；
                `None` = 未指定 ⇒ 全量）。
            index: `library_code` → `LibraryRecord` 的索引（由来源侧提供）。

        Returns:
            选中的库（按 priority 降序）。
        """
        libraries: List[LibraryRecord] = []
        if candidates is None:
            # 未指定 ⇒ 全量模糊库（适用性交由规则级判定，见上）
            for lib in index.values():
                if not lib.is_active or lib.library_type != 'fuzzy':
                    continue
                if lib not in libraries:
                    libraries.append(lib)
        else:
            for code in candidates:
                lib = index.get(code)
                if lib is None or not lib.is_active:
                    continue
                if lib not in libraries:
                    libraries.append(lib)

            # 通用兜底库（必须存在）
            base = index.get('base')
            if (base is not None and base.is_active
                    and base.library_type == 'fuzzy' and base not in libraries):
                libraries.append(base)

        return sorted(libraries, key=lambda l: -l.priority)

    # —— 组装 ————————————————————————————————————————————————

    @staticmethod
    def assemble(
        libraries: List[LibraryRecord],
        context: RuleQueryContext,
        methods_by_library: Dict[str, List[RuleRecord]],
    ) -> List[RuleProfile]:
        """把各库取回的方法组装成内核规则档案。

        流程（**来源无关**）：

        0. **适用性闸门**：`RuleService.matches_context` —— 聚合物 / 产品两维
           （**匹配谓词的唯一口径**，两条来源共用）;
        1. 特异级：由 `RuleService.resolve_specificity` 按「规则标签 × 当前上下文」
           逐维比对算出 —— 它是**相对当前上下文**的量，不是规则自身的属性；
        2. 契约构造：`RuleAdapter.to_rule_profile`（规则串为空 ⇒ 跳过）；
        3. 契约校验：`rule_profile_issues` —— 不合格的**跳过并留痕**，
           不整批抛（一条脏规则只废掉自己，不能让整次调优塌成空推荐）；
        4. 缺陷名匹配：`RuleService.match_defect_name`（只比缺陷名，不比档位）——
           **复用档案里的拆解产物**（`profile.parsed`），不重新拆规则串；
        5. 跨库副本去重：键 = `(defect_code, 规则串)`，胜出判据 = 真实特异级优先；
        6. 排序：`specificity` 升序、同特异性 `priority` 降序。

        ⚠️ **为什么适用性闸门放在编排层而不是来源侧**：数据库来源原先在
          SQL 里用 ``Q(...)`` 表达谓词，文件来源只能用 Python 表达。
          若各自实现，两份逻辑一旦分叉，同一批规则在两条路径下的命中集合
          就会不同，而且**极难察觉**（不报错，只是结果悄悄不同）。
          ⇒ 谓词只在 `RuleService.matches_context` 实现一次，
          **两个来源都只负责「取回候选」，由编排层统一筛**。

        Args:
            libraries: 选中的库（`select_libraries` 产出，已按优先级降序）。
            context: 查询上下文。
            methods_by_library: `library_code` → 该库的规则记录列表。

        Returns:
            内核规则档案列表。
        """
        best_by_key: dict = {}
        dropped = 0

        for lib in libraries:
            for record in methods_by_library.get(lib.library_code, []):
                # 适用性闸门（匹配谓词的唯一口径）
                if not RuleService.matches_context(
                    record.polymer_abbreviation, record.product_category,
                    context.polymer_abbreviation, context.product_category,
                ):
                    continue
                # 特异级由「规则实际命中了上下文的哪些维度」决定，
                # 而不是它碰巧落在哪次查询里
                specificity = RuleService.resolve_specificity(
                    record.polymer_abbreviation, record.product_category,
                    context.polymer_abbreviation, context.product_category,
                )
                # 契约构造归 RuleAdapter（来源适配层），编排层只做过滤
                profile = RuleAdapter.to_rule_profile(record, specificity)
                if profile is None:      # 规则串为空
                    continue
                issues = rule_profile_issues(profile)
                if issues:
                    logger.warning(
                        '[RuleAssembler] 规则档案校验未通过，已跳过: %s（%s）',
                        profile.source_ref or profile.rule_description,
                        '; '.join(issues))
                    continue
                if not RuleService.match_defect_name(
                    profile.rule_description, context, profile.parsed,
                ):
                    continue

                key = RuleService.dedupe_key(
                    record.defect_code, profile.rule_description,
                )
                held = best_by_key.get(key)
                if held is None:
                    best_by_key[key] = profile
                    continue
                dropped += 1
                if RuleService.prefer_candidate(
                    specificity, profile.priority,
                    held.specificity, held.priority,
                ):
                    best_by_key[key] = profile

        all_rules: List[RuleProfile] = list(best_by_key.values())

        if dropped:
            logger.info(
                '[RuleAssembler] 跨库副本去重：%d 条 → %d 条（合并 %d 条重复业务内容）',
                len(all_rules) + dropped, len(all_rules), dropped)

        # 排序：specificity 升序优先（同特异性 priority 降序）
        all_rules.sort(key=lambda r: (r.specificity, -r.priority))
        return all_rules


class KeywordAssembler:
    """来源无关的关键字编排（**契约校验关口**）。"""

    @staticmethod
    def filter_valid(
        profiles: List[KeywordProfile],
        source_label: str = '未知来源',
    ) -> List[KeywordProfile]:
        """内核契约校验关口 —— 不合格的**跳过并留痕**，不整批抛。

        ⚠️ **为什么放到共用层**：数据库来源与文件来源各自实现一遍校验，
          两份口径一旦分叉，同一个关键字在两条路径下的去留就会不同
          （不报错，只是结果悄悄不同）⇒ 只在这里实现一次。

        Args:
            profiles: 待校验的关键字档案。
            source_label: 日志前缀（标识是哪个来源触发的）。

        Returns:
            通过校验的关键字档案。
        """
        valid: List[KeywordProfile] = []
        for p in profiles:
            issues = keyword_profile_issues(p)
            if issues:
                logger.warning(
                    '[%s] 关键字档案校验未通过，已跳过: %s（%s）',
                    source_label, p.keyword, '; '.join(issues))
                continue
            valid.append(p)
        return valid


__all__ = ['RuleAssembler', 'KeywordAssembler']
