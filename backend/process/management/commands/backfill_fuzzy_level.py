"""规则关键字模糊档位（fuzzy_level）存量统一命令。

背景：存量 `fuzzy_level` 需与现行 3 档词表对齐（分析见 docs/fuzzy-algorithm-diagnosis.md）。

用法：
    python manage.py backfill_fuzzy_level                # 预览（默认不写库）
    python manage.py backfill_fuzzy_level --apply         # 实际写库
    python manage.py backfill_fuzzy_level --to-level 5 --apply   # 回滚到 5 档

说明：
    - 含软删记录（软删记录恢复后仍应与现网口径一致）
    - 幂等：只处理 `fuzzy_level != 目标值` 的记录 ⇒ 可重复执行
    - 数据源 `_data/rule_keyword_curated.json` 为 3 档，本命令负责把**存量库**对齐到源；
      重建库时由 init_rule_keyword 直接落 3 档
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from process.models import RuleKeyword


class Command(BaseCommand):
    help = '统一规则关键字的模糊档位（fuzzy_level）；默认预览，加 --apply 才写库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to-level', type=int, default=3,
            help='目标模糊档位（默认 3；回滚可传 5）',
        )
        parser.add_argument(
            '--apply', action='store_true',
            help='实际写库（不加此参数只打印预览）',
        )
        parser.add_argument(
            '--limit', type=int, default=None,
            help='最多处理多少条（调试用）',
        )

    def handle(self, *args, **options):
        to_level = options['to_level']
        apply_changes = options['apply']
        limit = options['limit']

        valid_levels = tuple(lvl for lvl, _label in RuleKeyword.FUZZY_LEVELS)
        if to_level not in valid_levels:
            self.stderr.write(self.style.ERROR(
                '不支持的目标档位: %s（可选 %s）'
                % (to_level, ', '.join(str(i) for i in valid_levels))
            ))
            return

        # 待改：档位不等于目标值的全部记录（含软删 —— 恢复后仍应口径一致）
        qs = RuleKeyword.all_objects.exclude(fuzzy_level=to_level)
        total = qs.count()
        if limit is not None:
            qs = qs[:limit]

        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                '没有需要调整的记录（fuzzy_level 已全部为 %d）' % to_level))
            return

        self.stdout.write('待调整记录：%d 条（目标档位 %d）' % (total, to_level))
        if not apply_changes:
            self.stdout.write(self.style.WARNING('当前为预览模式（未写库），加 --apply 执行'))
        self.stdout.write('')

        # 按 (原档位, category) 汇总，方便一眼看清影响面
        summary = {}
        for kw in qs:
            key = (kw.fuzzy_level, kw.category)
            summary[key] = summary.get(key, 0) + 1
        for (old, cat), cnt in sorted(summary.items()):
            self.stdout.write('  %d 档 → %d 档  [%s]  %d 条' % (old, to_level, cat, cnt))

        self.stdout.write('')
        if not apply_changes:
            self.stdout.write(self.style.SUCCESS(
                '预览完成：%d 条待调整（未写库）' % total))
            return

        # 写库：用 update 绕过 save()（逐条 save 会触发额外逻辑，且无需重算派生字段）
        with transaction.atomic():
            updated = RuleKeyword.all_objects.exclude(fuzzy_level=to_level).update(
                fuzzy_level=to_level)
        self.stdout.write(self.style.SUCCESS(
            '调整完成：更新 %d 条（fuzzy_level → %d）' % (updated, to_level)))
