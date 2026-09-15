"""
Django management command: 校验并修正已有 RuleLibrary 的 library_type

业务背景：
- library_type 是 RuleLibrary 的新字段
- Django migration 0008 已为所有记录设置 default='expert'
- 本脚本提供手动校验入口，确保已知编码的库类型正确

执行：
python manage.py migrate_library_type
"""
from django.core.management.base import BaseCommand

from process.models.rules import RuleLibrary


class Command(BaseCommand):
    help = '校验并修正已有 RuleLibrary 的 library_type'

    # 已知的专家规则库编码（与 init_expert_rules.py 同步）
    EXPERT_CODES = ['expert_rules', 'init_rules']

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只打印不实际修改',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = 0

        for lib in RuleLibrary.objects.filter(is_deleted=False):
            old_type = lib.library_type
            # 推断规则：
            # - library_code 在已知专家规则库列表中 → expert
            # - 否则保持现有值（默认 'expert'）
            target = 'expert' if lib.library_code in self.EXPERT_CODES else lib.library_type
            if old_type != target:
                if dry_run:
                    self.stdout.write(self.style.WARNING(
                        f'  [dry-run] {lib.library_code}: {old_type} → {target}',
                    ))
                else:
                    lib.library_type = target
                    lib.save(update_fields=['library_type'])
                    self.stdout.write(self.style.SUCCESS(
                        f'  [update] {lib.library_code}: {old_type} → {target}',
                    ))
                updated += 1
            else:
                self.stdout.write(f'  [skip]   {lib.library_code}: {old_type}（无需修改）')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ library_type 校验完成，共需更新 {updated} 条记录'
            + ('（dry-run 模式未实际修改）' if dry_run else ''),
        ))