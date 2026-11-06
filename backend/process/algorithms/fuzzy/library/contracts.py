"""契约 —— `library` 层对外的能力契约。

- `RuleQueryContext`：查询上下文（缺陷名 / 档位 / 缺陷位置 / 聚合物 / 产品类别 / 规则库编码）。
- `AlgorithmResourceRepository`：取规则（`get_rules`）与取论域元数据
  （`get_keywords_by_names`）的取用契约。
- `LibraryRecord` / `RuleRecord`：**来源无关**的记录契约 —— 数据库来源与
  文件来源都先把自己那一侧的数据规约成这两种记录，再由共用编排层组装。

用 `Protocol`（结构化子类型）表达，实现方无需显式继承，也不会引入 import 环。
本模块零 ORM 依赖，不得 import `library.rules` / `library.keywords` /
`library.repository` / `library.semantics`（那三者会形成环或把数据库拖进编排层）。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, runtime_checkable

from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile, RuleProfile


# --- 数据类型 ---

@dataclass
class LibraryRecord:
    """规则库档案（**来源无关**）。

    数据库来源由 ORM `RuleLibrary` 规约而来，文件来源由 JSON 规约而来；
    编排层只认这一种形态 ⇒ 选库 / 排序逻辑两边完全一致。

    Attributes
    ----------
    library_code : str
        库编码（如 'base' / 'R20240516093115'）。候选码匹配与兜底库都按它。
    library_name : str
        库名称（仅展示 / 排查用，不参与算法）。
    library_type : str
        库类型（'fuzzy' / 'expert'）。**只有兜底库要求 'fuzzy'**。
    priority : int
        库优先级（越大越优先）。选库后按它降序。
    is_active : bool
        是否启用。
    library_id : Optional[int]
        来源侧主键（数据库来源为 ORM 主键；文件来源为导出时记录的原主键，
        便于回溯）。
        ⚠️ **不是「库身份」的判据，但它是「按库归档规则」的键** ——
          同一编码下可能有多条库记录（跨租户可重复），取规则必须按主键
          分库取，否则同码两库会互相覆盖（张冠李戴）。
    source_ref : str
        溯源标识（字符串）。
    owner_type : str
        归属类型（'system' 系统级 / 'tenant' 租户级）。
        **可见性判据**：系统库全平台公用；租户私库只对归属租户可见。
        ⚠️ **缺失归属信息 ⇒ 按 'system' 处理**（保持既有可见行为，
        不因字段缺失而静默踢掉整库规则）。
    company_id : Optional[int]
        归属公司主键（租户私库的归属租户）。
        **不参与算法**，只用于可见性判定（与 `RuleQueryContext.company_id` 对齐）。
    """

    library_code: str
    library_name: str = ''
    library_type: str = 'fuzzy'
    priority: int = 0
    is_active: bool = True
    library_id: Optional[int] = None
    source_ref: str = ''
    owner_type: str = 'system'
    company_id: Optional[int] = None


#: 规则库索引：**库编码 → 同码的全部库记录**（保持来源顺序）。
#:
#: ⚠️ **不是「编码 → 一条记录」**：`library_code` 是业务分类编码，
#:   **跨租户可重复**（模型注释 + `add_rule_library` 只校验「同公司内不重复」）
#:   ⇒ 同码多记录是**合法状态**，索引必须全部装下。
#:   若按编码去重（只留第一条），别家的库会被**静默丢掉** ——
#:   不报错，只是它库里的规则不参与推理。
#:
#: ⚠️ **谁该被看到由可见性判据裁决**（`assembly.RuleAssembler.is_library_visible`），
#:   取数层不做取舍 —— 否则「取舍」会在两个来源各写一遍，必然分叉。
LibraryIndex = Dict[str, List[LibraryRecord]]


@dataclass
class RuleRecord:
    """规则条目档案（**来源无关**）。

    数据库来源由 ORM `RuleMethod` 规约而来，文件来源由 JSON 规约而来。
    携带**匹配维度**（聚合物 / 产品）与**溯源标识** —— 这两个字段在
    内核契约 `RuleProfile` 里不存在（内核不需要），但选库 / 去重 / 特异级
    计算都要用 ⇒ 必须一路带到组装环节。

    Attributes
    ----------
    defect_code : str
        缺陷标识（与 `RuleQueryContext.defect_name` 对齐）。
    rule_description : str
        规则串（`IF {defect}_{level} AND ... THEN {param}_{action}_{value}`）。
    priority : float
        规则优先级（数值越大越优先）。
    polymer_abbreviation : Optional[str]
        规则标注的聚合物缩写（None 或字面值「通用」= 该维通用）。
    product_category : Optional[str]
        规则标注的产品类别（None 或字面值「通用」= 该维通用）。
    source_ref : str
        溯源标识（数据库来源 `RuleMethod:<id>`；文件来源 `file:<code>#<id>`）。
    """

    defect_code: str = ''
    rule_description: str = ''
    priority: float = 1.0
    polymer_abbreviation: Optional[str] = None
    product_category: Optional[str] = None
    source_ref: str = ''

@dataclass
class RuleQueryContext:
    """规则查询上下文。

    defect_name: 缺陷名称（英文 keyword_name，如 'SHORTSHOT'），与
        `RuleMethod.defect_code` 对齐。
    defect_level: 缺陷严重程度（low / medium / high）。档位写在规则串的第一个
        前件里（`IF SHORTSHOT_low AND ...`）—— 1646 条规则实测全部如此。
        None 表示不按档位过滤。
    defect_position: 缺陷位置（`DL` + 缺陷名 + 段号）。本期不参与规则筛选，仅透传。
    polymer_abbreviation: 当前聚合物的缩写（如 'PE'）。None 或「通用」表示不指定
    product_category: 当前产品的类别名（精确路径，如 '酒瓶'）。None 或「通用」表示不指定
    rule_library_code: 用户指定的规则库编码。None = **全部模糊规则库** ——
        「哪条规则适用于当前产品/材料」由**规则级**判定决定
        （`RuleService.matches_context` + `resolve_specificity`），
        而不是靠一张写死的「产品 → 库」映射表提前做掉。
    company_id: 当前租户公司主键（**可见性上下文**）—— 系统库对所有租户
        公用，租户私库只对归属租户可见（判据在 `assembly.RuleAssembler`，
        两条来源共用一处）。
        None = **无租户上下文**（第三方集成 / 离线 runner / examples 导出）
        ⇒ **不过滤**（保持现状全量），不改变既有行为。
    """
    defect_name: str
    defect_level: Optional[str] = None
    defect_position: Optional[str] = None
    polymer_abbreviation: Optional[str] = None
    product_category: Optional[str] = None
    rule_library_code: Optional[str] = None
    company_id: Optional[int] = None


# --- 契约 ---

@runtime_checkable
class AlgorithmResourceRepository(Protocol):
    """规则 + 关键字的取用契约。

    `get_rules` 取规则（methods），`get_keywords_by_names` 取关键字元数据
    （keywords）—— 二者都是算法的必需输入（规则给推理逻辑、关键字给论域定义），
    故合并为一个契约。

    只管「取资源」，不管「加工」：按结论形态分流与契约构造是对已取回档案的加工，
    住在 `fuzzy_core/profiles.py`，编排层直接调用。

    编排层只依赖本协议，默认实现是 `library.repository.ResourceRepository`
    （数据库来源）；第二个实现是 `library/files/repository.py`
    （文件来源）—— 两者可互换。

    ⚠️ **标了 `@runtime_checkable`**：允许用 `isinstance` 校验实现方
      （只校验方法是否存在，不校验签名）⇒ 两条来源的「契约满足」可被自动断言。
    """

    def get_rules(self, context: RuleQueryContext) -> List[RuleProfile]:
        """按上下文查出适用的规则列表（已按特异级/优先级排序）。"""

    def get_keywords_by_names(self, names) -> List[KeywordProfile]:
        """按参数名批量取论域元数据。

        返回 ``List[KeywordProfile]`` —— **内核输入契约对象**，
        不退回裸 dict：内核 net 吃的就是契约对象，来源层若在门口把它降级成
        dict，契约就断在门口了。
        """
