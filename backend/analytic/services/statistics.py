"""
molding-optima analytic 聚合分析服务（按业务域拆分）

业务域：
- statistics: 工艺统计聚合（trend + origin）

迁移记录：
- 2026-10-08 从 process.services.statistics 迁出
  原路径：process/services/statistics.py
  原函数：get_dashboard_statistics
  新函数：get_process_statistics（命名更明确"工艺"维度）

- 2026-10-08 同步重命名 app：dashboard → analytic
  原因：避免与前端 UI 视图（views/dashboard）混淆；无 -s 后缀符合命名习惯
"""
from datetime import date, timedelta
from typing import Any, Dict

from django.db.models import Count
from django.db.models.functions import TruncDate

from process.models import ProcessCondition


# 从 model choices 动态获取（避免与 model 定义重复/不一致）
ORIGIN_LABELS: Dict[str, str] = dict(
    ProcessCondition.PROCESS_CONDITION_ORIGIN_CHOICES,
)


def get_process_statistics(company_id: int, days: int = 30) -> Dict[str, Any]:
    """
    获取工艺统计聚合数据

    Args:
        company_id: 公司 ID（多租户隔离）
        days: 趋势天数（默认 30）

    Returns:
        {
            'trend': {
                'dates':  ['08-25', '08-26', ..., '09-23'],
                'counts': [3, 0, 5, ..., 2],
            },
            'origin_distribution': [
                {'name': '手工新建', 'value': 12, 'origin_type': 'manual_creation'},
                ...
            ],
        }
    """
    return {
        'trend': _get_trend(company_id, days),
        'origin_distribution': _get_origin_distribution(company_id),
    }


def _get_trend(company_id: int, days: int) -> Dict[str, Any]:
    """近 N 天每日新增工艺数（0 时补齐）"""
    start_date = date.today() - timedelta(days=days - 1)

    # 按日期分组聚合（数据库侧 group by）
    rows = (
        ProcessCondition.objects
        .filter(company_id=company_id, created_at__date__gte=start_date)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    trend_dict = {row['date']: row['count'] for row in rows}

    # 补齐日期序列（缺失日期补 0）
    dates: list = []
    counts: list = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        dates.append(f"{d.month:02d}-{d.day:02d}")
        counts.append(trend_dict.get(d, 0))

    return {'dates': dates, 'counts': counts}


def _get_origin_distribution(company_id: int) -> list:
    """按 origin_type 分组聚合（count 数降序）"""
    rows = (
        ProcessCondition.objects
        .filter(company_id=company_id)
        .values('origin_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    items = []
    for row in rows:
        origin_type = row['origin_type'] or 'unknown'
        items.append({
            'name': ORIGIN_LABELS.get(origin_type, origin_type),
            'value': row['count'],
            'origin_type': origin_type,
        })
    return items