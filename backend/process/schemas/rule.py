"""规则中心列表查询条件 Schema

背景：规则库 / 规则关键字 / 规则方法 / 专家规则列表接口原先复用通用
`PaginationBaseSchema`，而它只声明 `page_no / page_size / sort` ⇒ 前端传的
筛选参数（`owner_type` / `library_type` / `library_name` / `is_active` /
`keyword_type` / `rule_code` …）在校验阶段被**直接丢弃**，导致列表页筛选框
全部失效（个别接口靠 view 里手工 `request.GET.get` 兜住了部分参数，
漏掉的那些则静默失效）。

本文件为规则中心补齐列表专用 Schema，字段名与
`process.services.rule` 对应 service 的形参**一一对应**（view 层用
`**cleaned_data` 透传 ⇒ 名字必须严格对齐，否则会 TypeError）。
"""
from typing import Optional

from pydantic import Field

from extensions.schemas import PaginationBaseSchema


class RuleLibraryListSchema(PaginationBaseSchema):
    """规则库列表查询条件（对应 service `get_list_of_rule_library` 形参）"""

    library_name: Optional[str] = Field(
        None, description="库名称（模糊匹配）",
    )
    library_code: Optional[str] = Field(
        None, description="库编码（模糊匹配）",
    )
    owner_type: Optional[str] = Field(
        None, description="归属类型：system（系统级）/ tenant（租户级）",
    )
    library_type: Optional[str] = Field(
        None, description="库类型：expert（专家规则库）/ fuzzy（模糊规则库）",
    )
    is_active: Optional[bool] = Field(
        None, description="是否启用（true/false）",
    )


class RuleKeywordListSchema(PaginationBaseSchema):
    """规则关键字列表查询条件（对应 service `get_list_of_rule_keyword` 形参）"""

    name: Optional[str] = Field(
        None, description="关键词名称 / 别名（模糊匹配）",
    )
    keyword_type: Optional[str] = Field(
        None,
        description=(
            "参数类型：pressure / speed / time / temperature / "
            "position / force / length / weight"
        ),
    )


class RuleMethodListSchema(PaginationBaseSchema):
    """规则方法列表查询条件（对应 service `get_list_of_rule_method` 形参）"""

    defect_label: Optional[str] = Field(
        None, description="缺陷标签（模糊匹配）",
    )
    defect_code: Optional[str] = Field(
        None, description="缺陷编码（按缺陷查规则的业务入口）",
    )
    is_active: Optional[bool] = Field(
        None, description="是否启用（true/false）",
    )
    rule_library_id: Optional[int] = Field(
        None, description="所属规则库 ID",
    )


class ExpertRuleListSchema(PaginationBaseSchema):
    """专家规则列表查询条件（对应 service `get_list_of_expert_rule` 形参）"""

    rule_code: Optional[str] = Field(
        None, description="规则编码（模糊匹配）",
    )
    is_active: Optional[bool] = Field(
        None, description="是否启用（true/false）",
    )
    rule_library_id: Optional[int] = Field(
        None, description="所属规则库 ID",
    )
