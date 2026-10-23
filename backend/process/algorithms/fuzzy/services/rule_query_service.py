"""
RuleQueryService - 模糊推理规则路由层

按"上下文（产品/材料/缺陷）"解析出真正要使用的规则库和规则集合。

设计原则（见 fuzzy-engine-reference.md §6）：
- RuleLibrary 顶层隔离（library_code）
- library 库内四级特异级匹配：polymer_abbreviation × product_category
- parent_library 支持跨层复用
- 双层分流：按**结论形态**分流（数值结论 → NumTskRuleNet；检查/弹窗结论 → FuzzyRuleNet）

注意：本模块只负责 DB 查询与路由，不执行任何模糊推理。
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from process.algorithms.fuzzy.fuzzy_core.parsing import (
    normalize_level_word,
    parse_rule,
)
from process.models.rules import RuleLibrary, RuleMethod


logger = logging.getLogger(__name__)


# ============================================================================
# 数据类
# ============================================================================

@dataclass
class RuleQueryContext:
    """规则查询上下文。

    Attributes
    ----------
    defect_name : str
        缺陷名称（英文 keyword_name，如 'SHORTSHOT'），与
        `RuleMethod.defect_code` 对齐。
    defect_level : Optional[str]
        缺陷严重程度（low / medium / high）。
        规则库里每个缺陷都有三档规则，档位写在规则串的**第一个前件**里
        （`IF SHORTSHOT_low AND ...`）—— 1646 条规则实测全部如此。
        None 表示不按档位过滤。
    defect_position : Optional[str]
        缺陷位置（`DL` + 缺陷名 + 段号，如 'DLOVERSIZE1'）。
        本期不参与规则筛选，仅作为上下文透传。
    polymer_abbreviation : Optional[str]
        当前聚合物的缩写（如 'PE'）。None 表示不指定
    product_category : Optional[str]
        当前产品的类别名（精确路径，如 '酒瓶'）。None 表示不指定
    rule_library_code : Optional[str]
        用户指定的规则库编码。None 表示按上下文自动解析
    """
    defect_name: str
    defect_level: Optional[str] = None
    defect_position: Optional[str] = None
    polymer_abbreviation: Optional[str] = None
    product_category: Optional[str] = None
    rule_library_code: Optional[str] = None


@dataclass
class ResolvedRule:
    """路由后的一条规则 + 元数据。

    Attributes
    ----------
    method : RuleMethod
        ORM 实例
    rule_str : str
        fuzzykit 风格规则字符串（直接取 `RuleMethod.rule_description`）
    specificity : int
        1=精确（polymer+product 都指定）, 2=部分polymer, 3=部分product, 4=默认
    conclusion_kind : str
        'numeric'（数值结论：``X_add_3.8`` / ``X_reduce_30%``）
        / 'advisory'（提示类结论：``X_adjust_请检查锁模力是否不合理。``）
        —— 按**结论形态**判定（能不能算出数值），不是规则库的组织维度。
        历史上这个字段叫 ``rule_level``，但与「档位（level）」语义冲突，
        已改名为 ``conclusion_kind``；也不再读已删除的 `RuleMethod.rule_level`。
    priority : float
        priority 字段（默认 1.0）
    """
    method: RuleMethod
    rule_str: str
    specificity: int
    conclusion_kind: str
    priority: float


# ============================================================================
# RuleQueryService
# ============================================================================

class RuleQueryService:
    """规则查询与路由服务。"""

    @staticmethod
    def get_libraries(context: RuleQueryContext) -> List[RuleLibrary]:
        """根据上下文解析目标规则库（按优先级排序）。"""
        libraries = []

        # 1) 用户显式指定
        if context.rule_library_code:
            lib = RuleLibrary.objects.filter(
                library_code=context.rule_library_code,
                is_active=True,
                is_deleted=False,
            ).first()
            if lib:
                libraries.append(lib)

        # 2) 按上下文产品/聚合物找匹配的库（业务约定映射）
        if context.product_category:
            candidate_codes = RuleQueryService._product_to_library_codes(context.product_category)
            for code in candidate_codes:
                lib = RuleLibrary.objects.filter(
                    library_code=code,
                    is_active=True,
                    is_deleted=False,
                ).first()
                if lib and lib not in libraries:
                    libraries.append(lib)

        # 3) 通用兜底库（必须存在）
        #    主基础模糊规则库：library_code='base'（library_type='fuzzy'，priority=100）
        #    历史实现找的是 'general'，该 library_code 在库里并不存在 → 兜底库
        #    永远找不到 → get_libraries 返回空 → 整条链路拿不到规则。
        general = RuleLibrary.objects.filter(
            library_code='base',
            library_type='fuzzy',
            is_active=True,
            is_deleted=False,
        ).first()
        if general and general not in libraries:
            libraries.append(general)

        # 按 priority 降序
        return sorted(libraries, key=lambda l: -l.priority)

    @staticmethod
    def _product_to_library_codes(product_category: str) -> List[str]:
        """产品类别 → 规则库编码候选列表。

        按"精确产品类 + 大类"两级尝试；留 extension 接口。
        默认实现简单。
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

    @classmethod
    def get_rules(cls, context: RuleQueryContext) -> List[ResolvedRule]:
        """按四级特异级匹配拉出 RuleMethod。

        规则串直接取 `RuleMethod.rule_description`（规则库的唯一权威来源，
        格式：`IF SHORTSHOT_low AND IV0_low THEN IV0_add_2`）。

        历史实现调 `RuleMethodAdapter.to_rule_string(rm)`，而那个适配器读的是
        0005 迁移已删除的 `rule_content` 字段 → 必然 AttributeError。

        返回按 (specificity 升序, priority 降序) 排序，便于上层加权推理。
        """
        libraries = cls.get_libraries(context)
        if not libraries:
            logger.warning('[RuleQueryService] 未找到任何可用规则库: %s', context)
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

        all_rules: List[ResolvedRule] = []
        seen_ids = set()

        for lib in libraries:
            for specificity, polymer, product in specificity_filters:
                qs = RuleMethod.objects.filter(
                    rule_library=lib,
                    polymer_abbreviation=polymer,
                    product_category=product,
                    defect_code=context.defect_name,
                    is_active=True,
                    is_deleted=False,
                ).order_by('-priority', 'id')
                for rm in qs:
                    if rm.id in seen_ids:
                        continue
                    rule_str = (rm.rule_description or '').strip()
                    if not rule_str:
                        continue
                    if not cls._match_defect_level(rule_str, context):
                        continue
                    seen_ids.add(rm.id)
                    all_rules.append(ResolvedRule(
                        method=rm,
                        rule_str=rule_str,
                        specificity=specificity,
                        conclusion_kind=cls.classify_conclusion_kind(rule_str),
                        priority=float(rm.priority or 1.0),
                    ))

        # 排序：specificity 升序优先（同特异性 priority 降序）
        all_rules.sort(key=lambda r: (r.specificity, -r.priority))
        return all_rules

    @staticmethod
    def _match_defect_level(rule_str: str, context: RuleQueryContext) -> bool:
        """规则前件的缺陷档位是否与反馈档位一致。

        规则库约定：缺陷一定是**第一个前件**（1646 条规则实测 100% 一致），
        格式 `IF {defect}_{level} AND ...`。反馈档位（low/medium/high）决定
        命中哪一档规则——三档规则是三套完全不同的调整方案，不能混用。
        """
        if not context.defect_level:
            return True
        preconditions = parse_rule(rule_str)['preconditions']
        if not preconditions:
            return True
        first = preconditions[0]
        if first.get('name') != context.defect_name:
            return True
        # 局部变量叫 defect_level 而不是 rule_level：
        # 本模块内 level 统一指「档位」，而结论形态已改名为 conclusion_kind。
        defect_level = normalize_level_word(first.get('level'))
        return defect_level == normalize_level_word(context.defect_level)

    @staticmethod
    def classify_conclusion_kind(rule_str: str) -> str:
        """按**结论形态**判定规则所属推理层。
    
        ⚠️ 这里的「层」指**结论能不能算出数值**，与规则库的**组织维度**
        （base 库 / 产品库 / 特异级）**完全无关**。
    
        - 'numeric'：数值结论（`X_add_2` / `X_reduce_3` / `X_reduce_30%`）
          → 数值层零阶 TSK 推理（NumTskRuleNet）
        - 'advisory'：提示类结论（`X_adjust_请检查锁模力是否不合理。`）
          或模糊等级结论（`X_add_low`）
          → 提示层（文本建议 / Mamdani 全模糊推理）
    
        历史实现读 `RuleMethod.rule_level` 字段，但该字段已被 0005 迁移删除，
        访问必然 AttributeError；旧名 'factory' / 'fallback' 也早已与实际语义脱节
        （字面像库层级，实际是结论形态），现已改为 numeric / advisory。
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

    @classmethod
    def split_by_conclusion_kind(cls, rules: List[ResolvedRule]) -> Dict[str, List[ResolvedRule]]:
        """按结论形态分流，返回 ``{'numeric': [...], 'advisory': [...]}``。
    
        分流依据是规则的**结论形态**（见 `classify_conclusion_kind`），
        不是已删除的 `RuleMethod.rule_level` 字段，也不是规则库的组织维度。
        """
        result: Dict[str, List[ResolvedRule]] = {'numeric': [], 'advisory': []}
        for r in rules:
            kind = r.conclusion_kind or cls.classify_conclusion_kind(r.rule_str)
            if kind in result:
                result[kind].append(r)
        return result

    @classmethod
    def get_priority_array(cls, rules: List[ResolvedRule]) -> List[float]:
        """由规则列表生成 priority_array（与 rule_array 等长）。"""
        return [r.priority for r in rules]

    @classmethod
    def to_rule_array(cls, rules: List[ResolvedRule]) -> List[Dict[str, Any]]:
        """由 ResolvedRule 列表生成 fuzzykit 期望的 rule_array 结构。"""
        return [{'rule_description': r.rule_str} for r in rules]


# ============================================================================
# 模块自检
# ============================================================================

if __name__ == '__main__':
    print('RuleQueryService 模块结构正常加载')
    print('  RuleQueryContext 字段:', RuleQueryContext.__dataclass_fields__.keys())
    print('  ResolvedRule 字段:    ', ResolvedRule.__dataclass_fields__.keys())
    print('  RuleQueryService 静态方法:', [
        m for m in dir(RuleQueryService)
        if not m.startswith('_') and callable(getattr(RuleQueryService, m))
    ])
