"""
molding-optima 仪表板统计 Schema

对应接口：
- GET /api/processes/statistics/dashboard/
"""
from typing import List, Optional

from pydantic import Field

from extensions.schemas import BaseSchema


class DashboardTrendSchema(BaseSchema):
    """近 N 天工艺创建趋势"""

    dates: List[str] = Field(..., description="日期序列（MM-DD 格式）")
    counts: List[int] = Field(..., description="每日新增工艺数（与 dates 一一对应）")


class DashboardOriginItemSchema(BaseSchema):
    """起源类型分布项（饼图用）"""

    name: str = Field(..., description="中文名（用于饼图展示）")
    value: int = Field(..., description="工艺数")
    origin_type: Optional[str] = Field(None, description="origin_type 标识（用于前端联动）")


class DashboardStatisticsSchema(BaseSchema):
    """仪表板统计聚合响应"""

    trend: DashboardTrendSchema = Field(..., description="近 30 天创建趋势")
    origin_distribution: List[DashboardOriginItemSchema] = Field(
        ..., description="起源类型分布（饼图）",
    )


__all__ = [
    "DashboardTrendSchema",
    "DashboardOriginItemSchema",
    "DashboardStatisticsSchema",
]