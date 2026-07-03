"""
RuleQueryService - 模糊推理规则路由层

按"上下文（产品/材料/缺陷）"解析出真正要使用的规则库和规则集合。

设计原则（见 fuzzy-engine-reference.md §6）：
- RuleLibrary 顶层隔离（library_code）
- library 库内三级特异性匹配：polymer_category × product_category
- parent_library 支持跨层复用
- 双层分流：rule_level = factory / fallback

注意：本模块只负责 DB 查询与路由，不执行任何模糊推理。
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

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
        缺陷名称，如 'SHORTSHOT'
    polymer_category : Optional[str]
        当前聚合物的类别名（精确路径，如 'PE'）。None 表示不指定
    product_category : Optional[str]
        当前产品的类别名（精确路径，如 '酒瓶'）。None 表示不指定
    rule_library_code : Optional[str]
        用户指定的规则库编码。None 表示按上下文自动解析
    """
    defect_name: str
    polymer_category: Optional[str] = None
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
        通过 RuleMethodAdapter 生成的 fuzzykit 风格规则字符串
    specificity : int
        1=精确（polymer+product 都指定）, 2=部分polymer, 3=部分product, 4=默认
    rule_level : str
        'factory' / 'fallback'
    priority : float
        priority 字段（默认 1.0）
    """
    method: RuleMethod
    rule_str: str
    specificity: int
    rule_level: str
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
        general = RuleLibrary.objects.filter(
            library_code='general',
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
        """按三级特异性匹配拉出 RuleMethod。

        返回按 (specificity 升序, priority 降序) 排序，便于上层加权推理。
        """
        libraries = cls.get_libraries(context)
        if not libraries:
            logger.warning('[RuleQueryService] 未找到任何可用规则库: %s', context)
            return []

        # 三级特异性匹配
        # L1 精确：polymer 匹配 + product 匹配
        # L2 部分-polymer：polymer 匹配 + product=None
        # L3 部分-product：polymer=None + product 匹配
        # L4 默认：polymer=None + product=None
        specificity_filters = [
            (1, context.polymer_category, context.product_category),
            (2, context.polymer_category, None),
            (3, None, context.product_category),
            (4, None, None),
        ]

        all_rules: List[ResolvedRule] = []
        seen_ids = set()

        for lib in libraries:
            for specificity, polymer, product in specificity_filters:
                qs = RuleMethod.objects.filter(
                    rule_library=lib,
                    polymer_category=polymer,
                    product_category=product,
                    defect_name=context.defect_name,
                    enable=True,
                    is_deleted=False,
                ).order_by('-priority', 'id')
                for rm in qs:
                    if rm.id in seen_ids:
                        continue
                    seen_ids.add(rm.id)
                    from process.engines.fuzzy.adapters import RuleMethodAdapter
                    rule_str = RuleMethodAdapter.to_rule_string(rm)
                    all_rules.append(ResolvedRule(
                        method=rm,
                        rule_str=rule_str,
                        specificity=specificity,
                        rule_level=rm.rule_level or 'factory',
                        priority=float(rm.priority or 1.0),
                    ))

        # 排序：specificity 升序优先（同特异性 priority 降序）
        all_rules.sort(key=lambda r: (r.specificity, -r.priority))
        return all_rules

    @classmethod
    def split_by_level(cls, rules: List[ResolvedRule]) -> Dict[str, List[ResolvedRule]]:
        """按 rule_level 分流，返回 {'factory': [...], 'fallback': [...]}。"""
        result = {'factory': [], 'fallback': []}
        for r in rules:
            if r.rule_level in ('factory', 'fallback'):
                result[r.rule_level].append(r)
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
