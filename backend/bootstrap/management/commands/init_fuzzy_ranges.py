"""
Django management command: 从老 fuzzykit 迁移 RuleKeyword.step

老 fuzzykit 的 process_ranges.csv 列说明：
  col1: param_name (变量名)
  col2: fuzzy_level (模糊分级)
  col3: all_range_min (参数取值范围最小值)
  col4: all_range_max (参数取值范围最大值)
  col5: action_range_min (调整区间最小值)
  col6: action_range_max (调整区间最大值)
  col7: action_maxVal  (单次最大调整量, fuzzykit nets.py 第1137、1160行用作 step)

迁移逻辑：
  - 按 col1 (param_name) 与 RuleKeyword.keyword_name 匹配
  - 把 col7 写入 RuleKeyword.step
  - 缺省时用 (col4-col3) / fuzzy_level 作为兜底

使用方法：
  python manage.py init_fuzzy_ranges  # 从默认路径
  python manage.py init_fuzzy_ranges --csv /custom/path.csv
  python manage.py init_fuzzy_ranges --dry-run
"""

import csv
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from process.models.rules import RuleKeyword


DEFAULT_CSV_PATH = 'old/mdprocess/utils/fuzzykit/fuzzy_core/dataset/process_ranges.csv'


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '从老 fuzzykit 的 process_ranges.csv 迁移 RuleKeyword.step'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default=DEFAULT_CSV_PATH,
            help=f'CSV 路径（默认: {DEFAULT_CSV_PATH}）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只打印计划，不写库',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='覆盖已有 step 值',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv'])
        dry_run = options['dry_run']
        force_update = options['force']

        self.stdout.write(self.style.NOTICE('=== 迁移 RuleKeyword.step ===\n'))

        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f'CSV 文件不存在: {csv_path}'))
            self.stdout.write(
                self.style.WARNING(
                    f'提示：请将 process_ranges.csv 拷贝到指定路径，'
                    f'或使用 --csv 指定其他路径'
                )
            )
            return

        # 读取 CSV
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for line_no, row in enumerate(reader, 1):
                if not row or row[0].startswith('#'):
                    continue
                if len(row) < 7:
                    continue
                rows.append({
                    'param_name': row[0].strip(),
                    'fuzzy_level': int(row[1]) if row[1].isdigit() else 3,
                    'range_min': float(row[2]),
                    'range_max': float(row[3]),
                    'action_range_min': float(row[4]),
                    'action_range_max': float(row[5]),
                    'action_max_val': float(row[6]),
                })

        self.stdout.write(f'CSV 文件: {csv_path}')
        self.stdout.write(f'读取到 {len(rows)} 个工艺参数（含缺陷行）')
        self.stdout.write('')

        matched = 0
        updated = 0
        skipped = 0
        not_found = 0

        for row in rows:
            param_name = row['param_name']
            step = row['action_max_val']

            # 跳过缺省值（-1 表示未配置）
            if step < 0:
                # 用 fallback: (range_max - range_min) / fuzzy_level
                span = row['range_max'] - row['range_min']
                if span > 0 and row['fuzzy_level'] > 0:
                    step = span / row['fuzzy_level']

            try:
                kw = RuleKeyword.objects.filter(
                    keyword_name=param_name,
                    is_deleted=False,
                ).first()
            except Exception as e:
                logger.warning(f'查询失败 {param_name}: {e}')
                not_found += 1
                continue

            if not kw:
                not_found += 1
                continue

            matched += 1

            # 是否更新
            if kw.step is not None and not force_update:
                skipped += 1
                self.stdout.write(f'  跳过(已有 step={kw.step}): {param_name}')
                continue

            step_value = round(step, 4) if step else None
            if dry_run:
                self.stdout.write(f'  [DRY-RUN] 将 {param_name}.step 设为 {step_value}')
            else:
                kw.step = step_value
                kw.save(update_fields=['step'])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f'  更新: {param_name}.step = {step_value}'))

        # 输出统计
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== 迁移完成 ==='))
        self.stdout.write(f'  匹配关键字: {matched}')
        self.stdout.write(f'  更新 step:  {updated}')
        self.stdout.write(f'  跳过(已有): {skipped}')
        self.stdout.write(f'  未匹配:     {not_found}')
        if dry_run:
            self.stdout.write(self.style.WARNING('  [DRY-RUN 模式，未写库]'))
