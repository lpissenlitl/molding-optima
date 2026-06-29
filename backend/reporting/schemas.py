"""
molding-optima 报表导出 Schema 定义（Pydantic 版本）
精简引入：仅保留与工艺相关的导出参数。
"""
from typing import Optional, List
from pydantic import Field

from extensions.schemas import BaseSchema


class ProcessExportSchema(BaseSchema):
    """工艺参数导出"""

    process_condition_ids: List[int] = Field(..., min_length=1, description="工艺条件 ID 列表")
    template: Optional[str] = Field("default", description="导出模板（default/detail/compact）")
    include_snapshots: bool = Field(False, description="是否包含 process_context_snapshot")


class ProcessReportGenerateSchema(BaseSchema):
    """工艺报告生成（PDF/DOCX）"""

    process_condition_id: int = Field(..., description="工艺条件 ID")
    format: str = Field("pdf", description="输出格式：pdf 或 docx")
    template: Optional[str] = Field(None, description="报告模板")