"""
molding-optima 报表导出 Schema 定义（Pydantic 版本）
精简引入：仅保留与工艺相关的导出参数。
"""
from typing import Optional, List, Literal
from pydantic import Field

from extensions.schemas import BaseSchema


class ProcessExportSchema(BaseSchema):
    """工艺参数导出"""

    process_condition_ids: List[int] = Field(..., min_length=1, description="工艺条件 ID 列表")
    template: Literal["compact", "default", "detail"] = Field(
        "default",
        description="导出模板：compact=精简总览 / default=标准工艺卡 / detail=追溯（含工艺上下文）",
    )
    include_snapshots: bool = Field(False, description="是否包含 process_context_snapshot")


class ProcessReportGenerateSchema(BaseSchema):
    """工艺报告生成（PDF/DOCX）"""

    process_condition_id: int = Field(..., description="工艺条件 ID")
    format: Literal["pdf", "docx"] = Field("pdf", description="输出格式：pdf 或 docx")
    template: Optional[str] = Field(None, description="报告模板")


class ExportListSchema(BaseSchema):
    """列表导出（Excel）"""

    resource: str = Field(
        ...,
        min_length=1,
        description="导出资源（白名单 key：auxiliary_list / filler_list / injection_list / polymer_list）",
    )
    ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="待导出的数据 ID 列表",
    )