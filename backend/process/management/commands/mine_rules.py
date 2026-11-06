"""规则挖掘闭环命令 —— 采集样本 → 挖掘规则 → 候选规则入库。

用法：
    python manage.py mine_rules --company-id 11
    python manage.py mine_rules --company-id 11 --skip-collect   # 只挖不采集
    python manage.py mine_rules --company-id 11 --dry-run        # 只算不落库

链路：
    TuningRecord（DB）
        ↓ collect      → MiningSample（JSONL 文件语料）
        ↓ mine         → MiningRule（DB，状态 pending 待审核）

⚠️ **语料落盘位置**
    `{STORE_PATH}/{tenant_slug}/mining/samples/company_{company_id}.jsonl`
    —— 运行时数据目录，不在代码仓库内（见 `mining.provider`）。
"""

import json

from django.core.management.base import BaseCommand, CommandError

from process.services import mining as mining_service


class Command(BaseCommand):
    help = '规则挖掘闭环：采集样本 → 挖掘规则 → 候选规则入库（待审核）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id', type=int, required=True,
            help='目标公司 id',
        )
        parser.add_argument(
            '--skip-collect', action='store_true',
            help='跳过采集（只用已有语料挖掘）',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='只算不落库（不写候选规则表）',
        )
        parser.add_argument(
            '--min-support', type=float, default=0.05, help='最小支持度',
        )
        parser.add_argument(
            '--min-confidence', type=float, default=0.7, help='最小置信度',
        )
        parser.add_argument(
            '--min-lift', type=float, default=1.0, help='最小提升度',
        )
        parser.add_argument(
            '--min-samples', type=int, default=10, help='最少样本数',
        )
        parser.add_argument(
            '--corpus-dir', default=None,
            help='显式指定语料目录（默认按租户解析）',
        )

    def handle(self, *args, **options):
        from identity.models import Company

        company_id = options['company_id']
        company = Company.objects.filter(id=company_id).first()
        if company is None:
            raise CommandError(f'公司不存在：id={company_id}')

        tenant_slug = company.tenant_slug
        corpus_dir = options['corpus_dir']

        collect_result = None
        if not options['skip_collect']:
            collect_result = mining_service.collect_samples(
                company_id=company_id,
                tenant_slug=tenant_slug,
                corpus_dir=corpus_dir,
            )
            self.stdout.write(
                f'[采集] 扫描 {collect_result["scanned"]} 条样本，'
                f'新增/修订 {collect_result["appended"]} 条 → '
                f'{collect_result["corpus_path"]}'
            )
        else:
            self.stdout.write('[采集] 已跳过（--skip-collect）')

        mine_result = mining_service.mine_rules(
            company_id=company_id,
            tenant_slug=tenant_slug,
            min_support=options['min_support'],
            min_confidence=options['min_confidence'],
            min_lift=options['min_lift'],
            min_samples=options['min_samples'],
            corpus_dir=corpus_dir,
            persist=not options['dry_run'],
        )

        self.stdout.write(
            f'[挖掘] 语料 {mine_result["samples"]} 条样本 → '
            f'{mine_result["rules"]} 条规则'
        )
        if not options['dry_run']:
            self.stdout.write(
                f'[入库] 候选规则：新增 {mine_result["created"]} 条，'
                f'更新 {mine_result["updated"]} 条（状态 pending 待审核）'
            )
        else:
            self.stdout.write('[入库] --dry-run => 未写入候选规则表')

        for rule in mine_result['rules_detail']:
            defects = '+'.join(
                f"{d.get('name')}({d.get('level')})" if d.get('level')
                else str(d.get('name'))
                for d in rule['defects']
            ) or '-'
            changes = '+'.join(
                f"{c.get('param')}:{c.get('direction')}" for c in rule['changes']
            ) or '-'
            self.stdout.write(
                f'  · [{defects}] + [{changes}] -> {rule["consequent"]}  '
                f'support={rule["support"]:.3f} '
                f'confidence={rule["confidence"]:.3f} '
                f'lift={rule["lift"]:.3f} '
                f'evidence={len(rule["evidence"])}'
            )

        if options['dry_run']:
            self.stdout.write(json.dumps(
                {'collect': collect_result, 'mine': mine_result},
                ensure_ascii=False, indent=2,
            ))