"""
Django management command: 导入初始化规则到数据库

使用方法：
    python manage.py import_init_rules
"""
import json

from django.core.management.base import BaseCommand

from process.models.rules import RuleLibrary, ExpertRule


class Command(BaseCommand):
    help = '导入初始化规则到数据库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            type=str,
            help='规则JSON文件路径（可选，默认使用内置路径）',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制覆盖现有规则',
        )

    def handle(self, *args, **options):
        json_path = options.get('json')
        force_update = options.get('force', False)

        self.stdout.write(self.style.NOTICE('=== 导入初始化规则 ===\n'))

        # 默认 JSON 路径
        if json_path is None:
            json_path = 'process/engines/expert/expert_rules/init_rules.json'

        # 读取 JSON 文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'文件不存在: {json_path}'))
            return

        rules = data.get('rules', [])
        self.stdout.write(f'读取到 {len(rules)} 条规则')

        # 创建或获取规则库
        library, created = RuleLibrary.objects.get_or_create(
            library_code='init_rules',
            defaults={
                'library_name': '工艺初始化规则库',
                'description': '工艺参数初始化专家规则库',
                'owner_type': 'system',
                'priority': 100,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'创建规则库: {library.library_name}'))
        else:
            self.stdout.write(f'使用已有规则库: {library.library_name}')

        # 统计
        imported = 0
        updated = 0
        skipped = 0

        for rule_data in rules:
            rule_code = rule_data['rule_code']
            rule_name = rule_data.get('rule_name', rule_code)

            # 检查是否存在
            exists = ExpertRule.objects.filter(
                rule_library=library,
                rule_code=rule_code
            ).exists()

            if exists:
                if force_update:
                    # 更新已有规则
                    rule = ExpertRule.objects.get(rule_library=library, rule_code=rule_code)
                    rule.rule_name = rule_name
                    rule.description = rule_data.get('description', '')
                    rule.priority = rule_data.get('priority', 100)
                    rule.is_active = rule_data.get('is_active', True)
                    rule.conditions = rule_data.get('conditions', [])
                    rule.coefficients = rule_data.get('coefficients', {})
                    rule.source = 'expert'
                    rule.save()
                    updated += 1
                    self.stdout.write(f'  更新: {rule_code}')
                else:
                    skipped += 1
                    self.stdout.write(f'  跳过(已存在): {rule_code}')
            else:
                # 创建新规则
                ExpertRule.objects.create(
                    rule_library=library,
                    rule_code=rule_code,
                    rule_name=rule_name,
                    description=rule_data.get('description', ''),
                    priority=rule_data.get('priority', 100),
                    is_active=rule_data.get('is_active', True),
                    conditions=rule_data.get('conditions', []),
                    coefficients=rule_data.get('coefficients', {}),
                    source='expert',
                )
                imported += 1
                self.stdout.write(self.style.SUCCESS(f'  导入: {rule_code}'))

        # 输出统计
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== 导入完成 ==='))
        self.stdout.write(f'  新增: {imported} 条')
        self.stdout.write(f'  更新: {updated} 条')
        self.stdout.write(f'  跳过: {skipped} 条')

        # 验证
        self.stdout.write('')
        self.stdout.write('=== 验证规则 ===')
        count = ExpertRule.objects.filter(rule_library=library).count()
        self.stdout.write(f'数据库中规则总数: {count}')
