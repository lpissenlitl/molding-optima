"""
文件中心相关 Schema 定义 - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Optional
from pydantic import Field

from extensions.schemas import AbstractBaseSchema, BaseSchema


class FileSchema(BaseSchema):
    """文件内容 Schema 基类"""
    
    uuid: Optional[str] = Field(None, description="文件唯一标识（UUID）")
    filename: str = Field(..., description="文件名")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    type: str = Field(..., description="文件类别")
    size: Optional[int] = Field(None, description="文件大小（字节）")
    md5: Optional[str] = Field(None, description="文件MD5")
    storage_path: str = Field(..., description="存储路径")
    uploaded_by: Optional[str] = Field(None, description="上传者")


class FileListSchema(AbstractBaseSchema):
    """根据业务信息获取文件列表"""
    
    business_id: int = Field(..., description="业务ID")
    business_type: str = Field(..., description="业务类型")
    usage_type: str = Field(..., description="使用类型")