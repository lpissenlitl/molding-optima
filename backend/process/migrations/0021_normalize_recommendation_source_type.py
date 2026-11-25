"""把 Recommendation.source_type 的旧码 'fuzzy_rule' 刷成引擎 subtype 'fuzzy'。

背景（2026-11-24）：`0020` 把 ORM choices 改成容纳引擎 subtype
（`fuzzy_rule` → `fuzzy`，并补 `'empirical'`）⇒ 存量行里带的旧码
`'fuzzy_rule'` 在新 choices 下成了非法值，需一次性刷齐。

【注意】**不改 DB schema** —— 本迁移只改行数据。
"""

from django.db import migrations


def _upgrade(apps, schema_editor):
    """旧码 'fuzzy_rule' → 'fuzzy'（幂等：已刷过的行不再命中）。"""
    Recommendation = apps.get_model('process', 'Recommendation')
    Recommendation.objects.filter(source_type='fuzzy_rule').update(source_type='fuzzy')


class Migration(migrations.Migration):

    dependencies = [
        ('process', '0020_alter_recommendation_source_type'),
    ]

    operations = [
        # 【注意】**不做反向**：改回旧码会把「本来就是 'fuzzy'」的行一并改错
        #   （旧世界的真实落库值本就是 'fuzzy'）⇒ 反向无意义，保持现状。
        migrations.RunPython(_upgrade, migrations.RunPython.noop),
    ]
