"""
Django management command: 为 RuleKeyword 迁移 step（推理步长）

数据源（二选一）：
  1. 默认：_refs/module/process/data/rule_keyword_curated.json
     该文件是从老 fuzzykit process_ranges.csv 提炼出的关键词清单，
     其 action_max_val 即老 CSV 的 col7（单次最大调整量，fuzzykit 用作 step）。
  2. --csv：直接指定老 fuzzykit 的 process_ranges.csv（该文件不在本仓库，需手动提供）

老 fuzzykit 的 process_ranges.csv 列说明：
  col1: param_name (变量名)
  col2: fuzzy_level (模糊分级)
  col3: all_range_min (参数取值范围最小值)
  col4: all_range_max (参数取值范围最大值)
  col5: action_range_min (调整区间最小值)
  col6: action_range_max (调整区间最大值)
  col7: action_maxVal  (单次最大调整量, fuzzykit nets.py 第1137、1160行用作 step)

迁移逻辑：
  - 按 param_name 与 RuleKeyword.keyword_name 匹配
  - 把 action_max_val 写入 RuleKeyword.step
  - 缺省时用 (range_max-range_min) / fuzzy_level 作为兜底

使用方法：
  python manage.py init_rule_keyword_steps                # 默认读 curated JSON
  python manage.py init_rule_keyword_steps --json /path   # 自定义 JSON
  python manage.py init_rule_keyword_steps --csv /path    # 老 fuzzykit CSV
  python manage.py init_rule_keyword_steps --dry-run
"""

import csv
import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from process.models.rules import RuleKeyword
from utils.console import configure_console_encoding
from utils.refs import RULE_KEYWORD_JSON, resolve_data_path


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '迁移 RuleKeyword.step（每个参数的推理步长）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            type=str,
            default=RULE_KEYWORD_JSON,
            help=f'JSON 路径（默认: {RULE_KEYWORD_JSON}）',
        )
        parser.add_argument(
            '--csv',
            type=str,
            default=None,
            help='老 fuzzykit process_ranges.csv 路径（可选，指定后优先于 --json）',
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

    @staticmethod
    def _load_rows_from_json(json_path: Path) -> list:
        """从 curated JSON 读取 step 来源

        JSON 的 action_max_val 即老 CSV 的 col7（单次最大调整量 = step）。
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rows = []
        for record in data:
            name = (record.get('keyword_name') or '').strip()
            if not name:
                continue
            action_max_val = record.get('action_max_val')
            rows.append({
                'param_name': name,
                'fuzzy_level': record.get('fuzzy_level') or 3,
                'range_min': record.get('range_min') or 0,
                'range_max': record.get('range_max') or 0,
                'action_range_min': record.get('action_range_min'),
                'action_range_max': record.get('action_range_max'),
                # None 与 -1 同义：未配置
                'action_max_val': action_max_val if action_max_val is not None else -1,
            })
        return rows

    @staticmethod
    def _load_rows_from_csv(csv_path: Path) -> list:
        """从老 fuzzykit 的 process_ranges.csv 读取 step 来源"""
        rows = []
        # utf-8-sig：兼容 Excel 导出的带 BOM 的 CSV
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
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
        return rows

    def handle(self, *args, **options):
        configure_console_encoding()

        dry_run = options['dry_run']
        force_update = options['force']

        self.stdout.write(self.style.NOTICE('=== 迁移 RuleKeyword.step ===\n'))

        # 数据源：--csv 优先，其次 --json
        csv_path = options.get('csv')
        if csv_path:
            csv_path = resolve_data_path(csv_path)
            if not csv_path.exists():
                self.stdout.write(self.style.ERROR(f'CSV 文件不存在: {csv_path}'))
                self.stdout.write(self.style.WARNING(
                    '提示：请将 process_ranges.csv 拷贝到指定路径，'
                    '或使用 --json 指定其他路径'
                ))
                return
            rows = self._load_rows_from_csv(csv_path)
            source_desc = f'CSV 文件: {csv_path}'
        else:
            json_path = resolve_data_path(options['json'])
            if not json_path.exists():
                self.stdout.write(self.style.ERROR(f'JSON 文件不存在: {json_path}'))
                self.stdout.write(self.style.WARNING(
                    '提示：可用 --csv 指定老 fuzzykit 的 process_ranges.csv'
                ))
                return
            rows = self._load_rows_from_json(json_path)
            source_desc = f'JSON 文件: {json_path}'

        self.stdout.write(source_desc)
        self.stdout.write(f'读取到 {len(rows)} 个工艺参数（含缺陷行）')
        self.stdout.write('')

        matched = 0
        updated = 0
        skipped = 0
        not_found = 0

        for row in rows:
            param_name = row['param_name']
            step = row['action_max_val']

            # 跳过缺省值（-1 或 None 表示未配置）
            if step is None or step < 0:
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
