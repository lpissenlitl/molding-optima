# Generated for FuzzyEngine 迁移新增字段

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """FuzzyEngine 迁移所需的新增字段

    - RuleKeyword.step          → 用于模糊推理的调整步长
    - RuleMethod.rule_level     → 工厂级 (NumTskRuleNet) / 兜底层 (FuzzyRuleNet)
    """

    dependencies = [
        ('process', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rulekeyword',
            name='step',
            field=models.FloatField(blank=True, null=True, verbose_name='模糊步长'),
        ),
        migrations.AddField(
            model_name='rulemethod',
            name='rule_level',
            field=models.CharField(
                choices=[('factory', '工厂级'), ('fallback', '兜底层')],
                default='factory',
                max_length=20,
                verbose_name='规则层级',
            ),
        ),
    ]
