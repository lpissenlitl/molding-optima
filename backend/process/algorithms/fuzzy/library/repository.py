"""资源仓库 —— **数据库来源**的资源取用入口。

编排四步：
1. 选库：用户显式指定（只用它）→ **未指定则全量模糊库**（适用性交由
   规则级判定：聚合物 / 产品两维的匹配谓词 + 特异级）；
2. 收集：按**匹配谓词**（规则该维为通用或等于上下文值；上下文该维未知 ⇒
   该维不设限）从各库收集 method，每个库**只查一次**；
3. 组装：过滤 + 判定结论形态 → `List[RuleProfile]`（内核输入契约）；
4. 组合：把 rule 资源与 keyword 资源组合给编排层。

编排层只认 `library/contracts.py` 的 `AlgorithmResourceRepository` 协议。

⚠️ **本模块只做「取数」，不做「编排」**：

选库、去重、特异级计算这些**来源无关**的逻辑已抽到 `library/assembly.py`
的 `RuleAssembler` —— 文件来源（`library/files/`）与数据库来源共用同一份，
否则同一批规则在两条路径下的命中集合会悄悄分叉（不报错，只是结果不同）。

本模块与文件来源的差异只剩两步：**选库**（本模块查库）与**取方法**（本模块查库）。
"""

import logging
from typing import Dict, List

from process.algorithms.fuzzy.fuzzy_core.profiles import (
    KeywordProfile,
    RuleProfile,
    keyword_profile_issues,
)
from process.algorithms.fuzzy.library.assembly import RuleAssembler
from process.algorithms.fuzzy.library.contracts import (
    LibraryRecord,
    RuleQueryContext,
    RuleRecord,
)
from process.algorithms.fuzzy.library.keywords import KeywordQueryService
from process.algorithms.fuzzy.library.rules import RuleQueryService


logger = logging.getLogger(__name__)


# --- ResourceRepository ---

class ResourceRepository:
    """规则 + 关键字的取用入口（**数据库来源**）。

    是 `library/contracts.py::AlgorithmResourceRepository` 协议的默认实现。
    只负责路由与组织，不执行任何模糊推理。

    兄弟实现：`library/files/repository.py::FileResourceRepository`
    （文件来源）—— 两者对外契约完全一致，编排层可互换。
    """

    # —— 编排：把规则库组织成算法要用的规则 ——————————————————

    @classmethod
    def select_libraries(cls, context: RuleQueryContext) -> List[LibraryRecord]:
        """根据上下文解析目标规则库（按优先级排序）。

        两种口径（与文件来源**对称**）：

        1. **用户显式指定**（`context.rule_library_code`）⇒ 只用它；
        2. **未指定** ⇒ **全部模糊规则库**（专家库不算模糊规则库）——
           「哪条规则适用于当前产品/材料」交给**规则级**判定
           （`RuleService.matches_context` + `resolve_specificity`）。

        ⚠️ **为什么不按产品类别挑库**：「产品类别 → 库编码」映射表指向的 code
          （`packaging` / `auto_parts` / `medical`）在库里**根本不存在**
          （实际库码是 `base` 与 `R2023*`/`R2024*` 这类编号）⇒ 候选必然落空
          ⇒ 未显式指定时**永远只加载 base 库**，其余库（占全库 64%）从不参与推理。
          用一张写死的映射表把「规则是否适用于本产品」提前做掉，既是逻辑写死，
          也让规则库无法按产品灵活增删 —— 适用性本来就该由规则自身的标注决定。

        返回**来源无关记录** `LibraryRecord`（不是 ORM 实例）——
        编排层只认这一种形态，数据库来源与文件来源在此汇流。

        ⚠️ **为什么不返回 ORM 实例**：ORM 实例会把数据库绑进编排层的
          类型契约里，文件来源就没有对应的形态可用。返回记录后，
          `RuleAssembler.select_libraries` 才能被两个来源共用。
        """
        codes = RuleAssembler.library_code_candidates(context)
        index = RuleQueryService.get_library_index(codes)
        return RuleAssembler.select_libraries(codes, index, context)

    @classmethod
    def get_rules(cls, context: RuleQueryContext) -> List[RuleProfile]:
        """按上下文匹配拉出 RuleMethod，组装成内核输入契约。

        规则串直接取 `RuleMethod.rule_description`（格式：
        `IF SHORTSHOT_low AND IV0_low THEN IV0_add_2`）。

        「特异级」在这里有**两个角色**，本方法把它们分开：
        - **取数判据**：`RuleService.matches_context` 的**匹配谓词** ——
          规则该维为通用（NULL 或字面值「通用」）或等于上下文值；
          上下文该维未知（None / 「通用」）⇒ 该维不设限
          （「未指明」≠「不适用」），已知但不等 ⇒ 排除（冲突排除）；
        - **规则档案上的标签**：由 `RuleService.resolve_specificity` 按规则
          实际命中了上下文的哪些维度算出，**与取数顺序无关**。

        返回按 (specificity 升序, priority 降序) 排序，便于上层加权推理。
        """
        codes = RuleAssembler.library_code_candidates(context)
        index = RuleQueryService.get_library_index(codes)
        libraries = RuleAssembler.select_libraries(codes, index, context)
        if not libraries:
            logger.warning('[ResourceRepository] 未找到任何可用规则库: %s', context)
            return []

        # 每个库只查一次：「规则该维为 NULL 或等于上下文值」这个集合
        #   按特异级拆成 4 段查，与一次查询取全**等价** ⇒ 无需再拆。
        # ⚠️ **按库主键归档**（不按库编码）：库编码跨租户可重复 ⇒ 同码两库
        #   按编码归档会互相覆盖（后取的那库顶掉前一个），
        #   别家的规则被**静默张冠李戴**（不报错，只是结果不同）。
        methods_by_library: Dict[int, List[RuleRecord]] = {}
        for lib in libraries:
            methods_by_library[lib.library_id] = RuleQueryService.get_methods(
                lib.library_id,
                context.defect_name,
            )

        return RuleAssembler.assemble(libraries, context, methods_by_library)

    # —— 组合：把 keyword 资源并进来 ——————————————————————————

    @classmethod
    def get_keywords_by_names(cls, names) -> List[KeywordProfile]:
        """按参数名批量取论域元数据（`RuleKeyword`）。

        编排层访问字段元数据的唯一入口，不需要知道 `RuleKeyword` 这个 ORM 模型。

        查库在 `KeywordQueryService`，此处**原样转发**内核契约
        `KeywordProfile`（不转成内核 `keyword_array` 元素 dict ——
        net 现在直接吃契约对象，多这一层转换只会把契约掐断）。
        排序在这里做（ORM 的 `__in` 查询与顺序无关，但调用方要稳定序）。

        ⚠️ **内核契约校验关口**（`fuzzy_core/profiles.py`）：档案不合格的
        关键字**跳过并留痕**，不整批抛 —— 理由同 `get_rules`。
        """
        if not names:
            return []
        profiles = KeywordQueryService.get_keywords_by_names(sorted(names))
        valid: List[KeywordProfile] = []
        for p in profiles:
            issues = keyword_profile_issues(p)
            if issues:
                logger.warning(
                    '[ResourceRepository] 关键字档案校验未通过，已跳过: %s（%s）',
                    p.keyword, '; '.join(issues))
                continue
            valid.append(p)
        return valid


__all__ = ['ResourceRepository']