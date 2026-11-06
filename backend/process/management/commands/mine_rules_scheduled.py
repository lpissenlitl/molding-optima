"""规则挖掘定时调度命令 —— 攒够最小样本数才挖一次。

用法：
    python manage.py mine_rules_scheduled                     # 全部可访问公司
    python manage.py mine_rules_scheduled --company-id 11      # 指定公司（可重复）
    python manage.py mine_rules_scheduled --min-samples 20     # 提高触发门槛
    python manage.py mine_rules_scheduled --force              # 忽略水位强制挖一次
    python manage.py mine_rules_scheduled --dry-run            # 只判定不挖

链路（与 `mine_rules` 同一条）：
    TuningRecord（DB） -> collect -> MiningSample（JSONL 语料）
        -> mine -> MiningRule（DB，pending 待审核）

⚠️ **为什么要有这个命令（而 `mine_rules` 不够用）**
    `mine_rules` 是「无条件跑一遍」的命令，适合手工排查与首次灌库；
    定时调度需要的是「**攒够最小样本数再挖**」—— 样本不足时 Apriori
    挖不出东西，反复空跑纯属浪费；而没有新经验进来时指标不会变，
    重算也是白算。

⚠️ **调度由运维侧 cron 拉起**（本项目无任务队列基础设施）：
    ```cron
    0 * * * * cd /path/to/backend && python manage.py mine_rules_scheduled
    ```
"""

from django.core.management.base import BaseCommand

from process.services import mining as mining_service


class Command(BaseCommand):
    help = '规则挖掘定时调度：逐公司采集样本，攒够最小样本数才挖一次'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id', type=int, action='append', dest='company_ids',
            help='目标公司 id（可重复指定；缺省 = 全部可访问公司）',
        )
        parser.add_argument(
            '--min-samples', type=int, default=10,
            help='触发挖掘所需的最小语料样本数（同时也是挖掘内核的最小样本数）',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='忽略触发条件强制挖一次（首次上线 / 手工补挖）',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='只判定不挖（不写候选规则表）',
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
            '--corpus-dir', default=None,
            help='显式指定语料目录（默认按租户解析）',
        )

    def handle(self, *args, **options):
        result = mining_service.run_scheduled_mining(
            company_ids=options.get('company_ids') or None,
            min_samples=options['min_samples'],
            force=options['force'],
            dry_run=options['dry_run'],
            corpus_dir=options['corpus_dir'],
            min_support=options['min_support'],
            min_confidence=options['min_confidence'],
            min_lift=options['min_lift'],
        )

        for detail in result['details']:
            self.stdout.write(
                f"[{detail['status']}] 公司 {detail['company_id']} "
                f"({detail['company_name']}): {detail['reason']} | "
                f"新增样本 {detail['collected']} | 语料 {detail['samples']} 条"
            )
            if detail['status'] == 'mined':
                self.stdout.write(
                    f"    -> 挖出规则 {detail['rules']} 条"
                    f"（新增 {detail['created']} / 更新 {detail['updated']}）"
                )

        self.stdout.write(
            f"[汇总] 公司 {result['companies']} 个 | "
            f"挖掘 {result['mined']} | 跳过 {result['skipped']} | "
            f"失败 {result['failed']}"
        )
        if result['failed']:
            # ⚠️ 有公司失败时以非零退出码结束 —— 让 cron / 监控能发现
            self.stderr.write('存在挖掘失败的公司，请检查日志')
            raise SystemExit(1)