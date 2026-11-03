"""
远程搜索建议相关 Schema 定义 - Pydantic 版本
"""
from typing import Optional
from pydantic import Field

from extensions.schemas import AbstractBaseSchema


class SelectionOptionsSchema(AbstractBaseSchema):
    """远程搜索建议查询参数（GET /api/selection-options/）"""

    table: str = Field(..., min_length=1, description="目标表（白名单 key，如 mold / polymer）")
    column: str = Field(..., min_length=1, description="搜索列（目标表的文本字段名）")
    input: str = Field("", description="搜索关键词（对 column 做 icontains 匹配）")
    limit: Optional[int] = Field(None, ge=1, le=100, description="返回条数上限")
