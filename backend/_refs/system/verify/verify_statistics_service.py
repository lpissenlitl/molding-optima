"""
statistics_service 单元测试（不依赖数据库）

验证：
- 函数签名正确
- 趋势日期序列生成正确（30 天，无 0 截断）
- 起源分布 dict 结构正确
- 中文标签从 ProcessCondition choices 动态获取（DRY 验证）
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')

import django
django.setup()

from datetime import date, timedelta
from process.services import statistics_service
from process.models import ProcessCondition


# ===== 1. ORIGIN_LABELS 动态加载验证 =====
print('=== ORIGIN_LABELS ===')
print(f'Loaded {len(statistics_service.ORIGIN_LABELS)} labels from ProcessCondition.PROCESS_CONDITION_ORIGIN_CHOICES')
for k, v in statistics_service.ORIGIN_LABELS.items():
    print(f'  {k}: {v}')
assert 'manual_creation' in statistics_service.ORIGIN_LABELS
assert 'ai_recommendation' in statistics_service.ORIGIN_LABELS
assert statistics_service.ORIGIN_LABELS['manual_creation'] == '手工新建'
print('PASS')


# ===== 2. 趋势日期序列长度验证 =====
print('\n=== trend series length ===')
from unittest.mock import patch, MagicMock

# Mock QuerySet：返回空结果
with patch.object(statistics_service, 'ProcessCondition') as MockModel:
    mock_qs = MagicMock()
    mock_qs.filter.return_value.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = []
    MockModel.objects = mock_qs

    trend = statistics_service._get_trend(company_id=1, days=30)
    print(f'dates len: {len(trend["dates"])}')
    print(f'counts len: {len(trend["counts"])}')
    print(f'first 3 dates: {trend["dates"][:3]}')
    print(f'last 3 dates: {trend["dates"][-3:]}')
    print(f'first 3 counts: {trend["counts"][:3]}')
    print(f'last 3 counts: {trend["counts"][-3:]}')

    assert len(trend['dates']) == 30
    assert len(trend['counts']) == 30
    assert all(c == 0 for c in trend['counts']), '空数据应全为 0'

    # 验证最后一个日期是今天
    today = date.today()
    expected_last = f'{today.strftime("%m")}-{today.strftime("%d")}'
    assert trend['dates'][-1] == expected_last, f"last date should be today, got {trend['dates'][-1]}"
    print('PASS: dates length=30, all 0, last is today')


# ===== 3. 起源分布 dict 结构 =====
print('\n=== origin distribution structure ===')
with patch.object(statistics_service, 'ProcessCondition') as MockModel:
    mock_qs = MagicMock()
    mock_qs.filter.return_value.values.return_value.annotate.return_value.order_by.return_value = [
        {'origin_type': 'manual_creation', 'count': 10},
        {'origin_type': 'ai_recommendation', 'count': 5},
        {'origin_type': None, 'count': 2},  # 测试 None 处理
    ]
    MockModel.objects = mock_qs

    items = statistics_service._get_origin_distribution(company_id=1)
    print(f'items: {items}')
    assert len(items) == 3
    assert items[0]['name'] == '手工新建'
    assert items[0]['value'] == 10
    assert items[0]['origin_type'] == 'manual_creation'
    assert items[2]['name'] == 'unknown'
    assert items[2]['origin_type'] == 'unknown'
    print('PASS: name/value/origin_type structure OK, None handled')


# ===== 4. 顶层函数整合 =====
print('\n=== get_dashboard_statistics ===')
with patch.object(statistics_service, 'ProcessCondition') as MockModel:
    mock_qs = MagicMock()
    mock_qs.filter.return_value.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = []
    mock_qs.filter.return_value.values.return_value.annotate.return_value.order_by.return_value = []
    MockModel.objects = mock_qs

    result = statistics_service.get_dashboard_statistics(company_id=1, days=30)
    assert 'trend' in result
    assert 'origin_distribution' in result
    assert 'dates' in result['trend']
    assert 'counts' in result['trend']
    assert isinstance(result['origin_distribution'], list)
    print('PASS: top-level structure OK')

print('\n=== ALL TESTS PASSED ===')