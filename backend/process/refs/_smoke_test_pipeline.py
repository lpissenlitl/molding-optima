"""
Smoke test: 验证 RuleKeyword → FuzzyEngine 数据通路

步骤：
1. 从 DB 读取 RuleKeyword
2. 通过 RuleKeywordAdapter 转 fuzzy dict
3. 简单验证字段映射正确
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
django.setup()

from process.engines.fuzzy.adapters import RuleKeywordAdapter
from process.models.rules import RuleKeyword
from identity.models.company import Company
from identity.const import SYSTEM_DEMO_COMPANY_CODE


def main():
    c = Company.objects.filter(code=SYSTEM_DEMO_COMPANY_CODE).first()
    print(f'Company: {c.code} (id={c.id})')
    print()

    # 1. 测试 RuleKeywordAdapter（单条）
    print('=== 测试 1: 单条 RuleKeyword → fuzzy dict ===')
    sample_names = ['BT1', 'IP0', 'PT0', 'CLAMP', 'SHORTSHOT', 'DLSHORTSHOT1']
    for name in sample_names:
        kw = RuleKeyword.objects.filter(
            keyword_name=name, company_id=c.id, is_deleted=False,
        ).first()
        if not kw:
            print(f'  {name}: ❌ 不存在')
            continue
        fuzzy_dict = RuleKeywordAdapter.to_fuzzy_dict(kw)
        print(f'  {name:<15}  category={kw.category:<15}  '
              f'kw_type={kw.keyword_type:<12}  '
              f'fuzzy_level={kw.fuzzy_level}  '
              f'step={fuzzy_dict["step"]:.2f}  '
              f'range=[{fuzzy_dict["min_val"]}, {fuzzy_dict["max_val"]}]')

    # 2. 批量查询
    print()
    print('=== 测试 2: 批量查询 → fuzzy dict 列表 ===')
    names = ['BT1', 'PT0', 'IP0']
    fuzzy_list = RuleKeywordAdapter.get_keywords_by_names(names)
    print(f'查询 {len(names)} 个 → 返回 {len(fuzzy_list)} 个 fuzzy dict')
    for fd in fuzzy_list:
        print(f'  {fd}')

    # 3. 按 category 统计
    print()
    print('=== 测试 3: 按 category 分布 ===')
    from django.db.models import Count
    by_category = RuleKeyword.objects.filter(
        company_id=c.id, is_deleted=False,
    ).values('category').annotate(count=Count('id')).order_by('-count')
    for item in by_category:
        print(f'  {item["category"]}: {item["count"]} 条')

    # 4. 字段验证
    print()
    print('=== 测试 4: 关键字段验证 ===')
    bt1 = RuleKeyword.objects.filter(keyword_name='BT1', company_id=c.id).first()
    checks = [
        ('category', bt1.category == 'parameter'),
        ('parameter_kind', bt1.parameter_kind == 'setpoint'),
        ('keyword_type', bt1.keyword_type == 'temperature'),
        ('unit', bt1.unit == '℃'),
        ('fuzzy_level', bt1.fuzzy_level == 5),
        ('keyword_alias', bool(bt1.keyword_alias)),
        ('description', bool(bt1.description)),
    ]
    all_pass = True
    for field, ok in checks:
        status = '[OK]' if ok else '[FAIL]'
        all_pass = all_pass and ok
        print(f'  {status} BT1.{field} = {getattr(bt1, field)!r}')

    print()
    print('=' * 60)
    if all_pass:
        print('[ALL PASS] RuleKeyword -> FuzzyEngine pipeline OK')
    else:
        print('[SOME FAIL] Please check fields')
    print('=' * 60)


if __name__ == '__main__':
    main()