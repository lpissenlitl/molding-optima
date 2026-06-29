"""
通用 Schema 定义 - Pydantic 版本

本文件为所有模块提供基础 Schema 定义，作为序列化库统一的核心。
迁移自 marshmallow，所有字段注释和类型定义保持不变。

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
import re
from datetime import datetime
from typing import Optional, List, Any, TypeVar, Generic
from pydantic import BaseModel, Field, field_validator, ConfigDict


T = TypeVar('T')


# ==================== 基础 Schema ====================

class AbstractBaseSchema(BaseModel):
    """替代 marshmallow Schema 基类"""
    
    model_config = ConfigDict(populate_by_name=True)


class TracedSchema(AbstractBaseSchema):
    """跟踪字段 Schema 基类"""
    
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class BaseSchema(TracedSchema):
    """通用 Schema 基类"""
    
    is_deleted: Optional[bool] = Field(None, description="是否删除")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"  # 相当于 marshmallow 的 unknown = EXCLUDE
    )


# ==================== 分页 Schema ====================

class PaginationBaseSchema(AbstractBaseSchema):
    """分页接口参数基类检查器"""
    
    page_no: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=30, ge=1, le=1000, description="每页数量")
    sort: Optional[str] = Field(
        None,
        description="排序规则。格式：'+字段' 升序，'-字段' 降序。"
                   "多字段用逗号分隔，如 '+username,-age'。"
                   "传 null 或空字符串表示不排序。"
                   "不传此参数则默认按 id 倒序。"
    )
    
    @field_validator('sort')
    @classmethod
    def validate_sort(cls, v: Optional[str]) -> Optional[str]:
        """验证排序参数，支持 null/空字符串（不排序）和格式化字符串"""
        if v is None or v == "":
            return v
        
        if not isinstance(v, str):
            raise ValueError("排序参数必须是字符串或 null")
        
        pattern = r'^[+-]?[\w]+(,\s*[+-]?[\w]+)*$'
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "排序参数格式无效。示例：'+username' 或 '+username,-age'。"
                "字段名仅含字母、数字、下划线，不可用逗号结尾或开头。"
            )
        
        return v


# ==================== 批量操作 Schema ====================

class BatchIdsSchema(AbstractBaseSchema):
    """通用批量操作 Schema：仅包含 ID 列表"""
    
    ids: List[int] = Field(min_length=1, max_length=1000, description="ID 列表")


class BatchDeleteSchema(BatchIdsSchema):
    """通用批量删除 Schema：仅包含 ID 列表"""
    pass


# ==================== 字符串处理字段 ====================

class StripStr(str):
    """去除字符串首尾空字符"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            v = str(v)
        stripped = v.strip()
        if stripped == "":
            raise ValueError("不能为空字符串")
        return stripped