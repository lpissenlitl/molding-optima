"""契约 —— `library` 层对外的能力契约。

- `RuleQueryContext`：查询上下文（缺陷名 / 档位 / 缺陷位置 / 聚合物 / 产品类别 / 规则库编码）。
- `AlgorithmResourceRepository`：取规则（`get_rules`）与取论域元数据
  （`get_keywords_by_names`）的取用契约。

用 `Protocol`（结构化子类型）表达，实现方无需显式继承，也不会引入 import 环。
本模块零 ORM 依赖，不得 import `library.rules` / `library.keywords` /
`library.repository`（那三者依赖 ORM，会形成环并把数据库拖进编排层）。
"""

from dataclasses import dataclass
from typing import List, Optional, Protocol

from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile, RuleProfile


# --- 数据类型 ---

@dataclass
class RuleQueryContext:
    """规则查询上下文。

    defect_name: 缺陷名称（英文 keyword_name，如 'SHORTSHOT'），与
        `RuleMethod.defect_code` 对齐。
    defect_level: 缺陷严重程度（low / medium / high）。档位写在规则串的第一个
        前件里（`IF SHORTSHOT_low AND ...`）—— 1646 条规则实测全部如此。
        None 表示不按档位过滤。
    defect_position: 缺陷位置（`DL` + 缺陷名 + 段号）。本期不参与规则筛选，仅透传。
    polymer_abbreviation: 当前聚合物的缩写（如 'PE'）。None 表示不指定
    product_category: 当前产品的类别名（精确路径，如 '酒瓶'）。None 表示不指定
    rule_library_code: 用户指定的规则库编码。None 表示按上下文自动解析
    """
    defect_name: str
    defect_level: Optional[str] = None
    defect_position: Optional[str] = None
    polymer_abbreviation: Optional[str] = None
    product_category: Optional[str] = None
    rule_library_code: Optional[str] = None


# --- 契约 ---

class AlgorithmResourceRepository(Protocol):
    """规则 + 关键字的取用契约。

    `get_rules` 取规则（methods），`get_keywords_by_names` 取关键字元数据
    （keywords）—— 二者都是算法的必需输入（规则给推理逻辑、关键字给论域定义），
    故合并为一个契约。

    只管「取资源」，不管「加工」：按结论形态分流与契约构造是对已取回档案的加工，
    住在 `fuzzy_core/profiles.py`，编排层直接调用。

    编排层只依赖本协议，默认实现是 `library.repository.ResourceRepository`。
    """

    def get_rules(self, context: RuleQueryContext) -> List[RuleProfile]:
        """按上下文查出适用的规则列表（已按特异级/优先级排序）。"""

    def get_keywords_by_names(self, names) -> List[KeywordProfile]:
        """按参数名批量取论域元数据。

        返回 ``List[KeywordProfile]`` —— **内核输入契约对象**，
        不退回裸 dict：内核 net 吃的就是契约对象，来源层若在门口把它降级成
        dict，契约就断在门口了。
        """
