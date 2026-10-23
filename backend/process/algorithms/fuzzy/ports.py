"""端口契约（Ports）—— 编排层与数据源之间的唯一接口定义。

**零外部依赖**：本模块不 import Django、不 import ORM。
因此 `fuzzy_algorithm.py` 只依赖本模块，就能被 import 和调用（无需数据库环境）——
这是"编排层可脱离 DB 验证"的前提。

内容：
- `RuleQueryContext`：规则查询的输入
- `ResolvedRule`：规则查询的输出
- `RuleRepository`：规则与字段元数据的读取端口（Protocol）

默认实现：`services/rule_query_service.py` 的 `RuleQueryService`
（它 import ORM，**必须由调用方在真正需要访问数据时才导入**）。

⚠️ 为什么不用 `ABC` 而用 `Protocol`：
   `Protocol` 是结构化子类型——只要 `RuleQueryService` 的方法签名对得上，
   它就自动满足本协议，无需显式继承，也不会引入 import 环。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


# ============================================================================
# 数据类型
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
    method : Any
        规则来源的 ORM 实例（`RuleMethod`）。
        ⚠️ 端口层不能 import ORM（否则又拖回数据库依赖），
        故此处用 `Any`，实际类型由实现方保证。
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
    method: Any
    rule_str: str
    specificity: int
    conclusion_kind: str
    priority: float


# ============================================================================
# 端口
# ============================================================================

class RuleRepository(Protocol):
    """规则与字段元数据的读取端口。

    编排层（`FuzzyEngine`）**只依赖这个协议**，不依赖任何具体实现，
    更不依赖 Django ORM。默认实现是 `RuleQueryService`。
    """

    def get_rules(self, context: RuleQueryContext) -> List[ResolvedRule]:
        """按上下文查出适用的规则列表（已按特异级/优先级排序）。"""

    def split_by_conclusion_kind(
        self,
        rules: List[ResolvedRule],
    ) -> Dict[str, List[ResolvedRule]]:
        """按结论形态分流，返回 ``{'numeric': [...], 'advisory': [...]}``。"""

    def to_rule_array(self, rules: List[ResolvedRule]) -> List[Dict[str, Any]]:
        """转成推理层期望的 rule_array 结构。"""

    def get_priority_array(self, rules: List[ResolvedRule]) -> List[float]:
        """转成与 rule_array 等长的 priority 数组。"""

    def get_keywords_by_names(self, names) -> List[Dict[str, Any]]:
        """按参数名批量取论域元数据。

        返回的 dict 结构：
        ``{'keyword', 'lvl', 'min_val', 'max_val', 'step'}``
        （可含可选的 ``'source'`` 标记元数据来源）。
        """
