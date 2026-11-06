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
    LibraryIndex,
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

        ⚠️ **为什么不按产品类别挑库**：
           产品类别与规则是否匹配，本来就是**规则与上下文的关系**，应当由算法
           按规则自身的材料/产品标注判断（这正是 `specs.py` 对
           `product_category` 的原始定义：「规则库精确筛选键
           （specificity 1/3）… 填了能命中高特异级规则，不填退到默认规则」）。
           用一张写死的「产品类别 → 库编码」映射表把判断提前做掉，
           既是「逻辑写死」，又让规则库无法按产品灵活增删。

        ⚠️ **不查库**，只产出编码候选 —— 由来源侧拿候选去取库；
           `None` 表示「未指定 ⇒ 全量」，由来源侧取全部模糊库索引。
        """
        if context.rule_library_code:
            return [context.rule_library_code]
        return None

    @staticmethod
    def is_library_visible(
        lib: LibraryRecord,
        company_id: Optional[int],
    ) -> bool:
        """库可见性判据（**唯一定义处** —— 数据库来源与文件来源共用）。

        业务策略：**系统库全平台公用；租户私库只对归属租户可见**。

        ```
        库可见 ⟺ owner_type == 'system'
               OR (owner_type == 'tenant' AND company_id == 当前租户)
        ```

        ⚠️ **`company_id` 取不到 ⇒ 不过滤**（返回 True）：第三方集成
          （`infer_from_provided`）、离线 runner、examples 导出脚本都
          **没有租户上下文** ⇒ 缺上下文时**不改变行为**（保持现状全量）。

        ⚠️ **按「库归属」判定，不按「规则归属」**：规则的 `company_id`
          保留原租户值作溯源（晋升后仍记着来自哪家租户的经验），
          **不影响可见性** ⇒ 隔离只看库归属。

        ⚠️ **归属类型缺失 ⇒ 按系统库处理**（`or 'system'`）：不因字段缺失
          而静默踢掉整库规则（那会直接让某个租户的推荐全空）。

        Args:
            lib: 库档案（`LibraryRecord`）。
            company_id: 当前租户公司主键（None = 无租户上下文）。

        Returns:
            该库对当前租户是否可见。
        """
        if company_id is None:
            # 无租户上下文 ⇒ 不过滤（保持现状）
            return True
        if (lib.owner_type or 'system') == 'system':
            # 系统库：全平台公用
            return True
        # 租户私库：只有归属租户可见
        return lib.company_id is not None and lib.company_id == company_id

    @staticmethod
    def select_libraries(
        candidates: Optional[List[str]],
        index: LibraryIndex,
        context: Optional[RuleQueryContext] = None,
    ) -> List[LibraryRecord]:
        """选库（**未指定 ⇒ 全量模糊库**；指定 ⇒ 按候选 + 通用兜底库）。

        两种口径：

        - `candidates is None`（未指定库）⇒ **全量**：取索引里全部
          `is_active` 且 `library_type == 'fuzzy'` 的库
          （专家库不是模糊规则库，不参与）；
        - `candidates` 有值 ⇒ 沿用原口径：
          - 候选编码按顺序取库，**同一编码的多条记录全取**
            （同码多库是合法状态：库编码跨租户可重复）；
          - 停用的库（`is_active=False`）不取；
          - 候选库**不按库类型过滤**（用户可能显式指定任意库）；
          - 通用兜底库 `base` 追加在最后，且**要求 `library_type == 'fuzzy'`**
            —— 专家库不能当模糊规则库兜底。

        两种口径最后都按 `priority` **降序**稳定排序（同 priority 时候选顺序
        决定先后）。

        ⚠️ **可见性过滤在本方法收口**（`is_library_visible`）：谓词只在
          这里实现一次，两条来源共用 ⇒ 不会出现「数据库来源过滤了、文件来源
          没过滤」的分叉（那会让同一批规则在两条路径下的命中集合不同，
          而且**不报错**，只是结果悄悄不同）。

        ⚠️ **同码多库靠可见性裁决**：索引里同码的多个库（各租户的同名私库）
          不会被丢掉 —— 谁该被看到由 `is_library_visible` 判（租户私库只对
          归属租户可见）⇒ 不会串库，也不会让别家的库静默消失。

        Args:
            candidates: 候选库编码（`library_code_candidates` 产出；
                `None` = 未指定 ⇒ 全量）。
            index: `library_code` → **同码全部** `LibraryRecord` 的索引
                （由来源侧提供）。
            context: 查询上下文（提供 `company_id` = 当前租户；
                None = 无租户上下文 ⇒ 不过滤）。

        Returns:
            选中的库（按 priority 降序）。
        """
        libraries: List[LibraryRecord] = []
        if candidates is None:
            # 未指定 ⇒ 全量模糊库（适用性交由规则级判定，见上）
            for records in index.values():
                for lib in records:
                    if not lib.is_active or lib.library_type != 'fuzzy':
                        continue
                    if lib not in libraries:
                        libraries.append(lib)
        else:
            for code in candidates:
                for lib in index.get(code, []):
                    if not lib.is_active:
                        continue
                    if lib not in libraries:
                        libraries.append(lib)

            # 通用兜底库（必须存在）
            for lib in index.get('base', []):
                if (lib.is_active and lib.library_type == 'fuzzy'
                        and lib not in libraries):
                    libraries.append(lib)

        # 可见性过滤（**唯一定义处**：RuleAssembler.is_library_visible）
        tenant_id = context.company_id if context is not None else None
        visible = [lib for lib in libraries
                   if RuleAssembler.is_library_visible(lib, tenant_id)]
        hidden = len(libraries) - len(visible)
        if hidden:
            logger.info(
                '[RuleAssembler] 租户隔离：%d 个库对当前租户不可见（可见 %d 个）',
                hidden, len(visible))

        return sorted(visible, key=lambda l: -l.priority)

    # —— 组装 ————————————————————————————————————————————————

    @staticmethod
    def assemble(
        libraries: List[LibraryRecord],
        context: RuleQueryContext,
        methods_by_library: Dict[int, List[RuleRecord]],
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
            methods_by_library: **库主键** → 该库的规则记录列表。
                ⚠️ **按主键归档，不按库编码归档**：库编码跨租户可重复
                  （同码多库是合法状态）⇒ 按编码归档会让同码两库互相覆盖
                  （后取的那库顶掉前一个），别家的规则被静默张冠李戴。

        Returns:
            内核规则档案列表。
        """
        best_by_key: dict = {}
        dropped = 0

        for lib in libraries:
            for record in methods_by_library.get(lib.library_id, []):
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
