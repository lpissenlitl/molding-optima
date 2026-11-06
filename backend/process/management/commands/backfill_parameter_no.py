"""工艺参数编号（parameter_no）存量回填命令

背景：
    `parameter_no` 是面向用户的业务编号（格式 PP-{YYYYMMDD}-{HHMMSS}-{NNN}），
    但生成逻辑落地前，历史轮次该字段全为空 ⇒ 调机历史里看不到工艺编号。
    本命令按记录创建时刻回填，使历史轮次与新建轮次口径一致。

用法：
    python manage.py backfill_parameter_no                # 预览（默认不写库）
    python manage.py backfill_parameter_no --apply         # 实际回填
    python manage.py backfill_parameter_no --company-id 11 --apply
    python manage.py backfill_parameter_no --limit 10 --apply

分配规则：
    - 时间基准：记录的 `created_at`（轮次创建时刻）⇒ 编号能读出创建时间
    - 排序：同租户内按 (created_at, id) 升序 ⇒ 同秒内序号顺序稳定且可重跑
    - NNN：同一租户同一秒内从已占用序号之后递增 ⇒ 租户内唯一
    - 已有编号的记录不覆盖（demo 种子数据等保持原样）
    - 含软删记录（编号不回收，避免同号指向两条历史数据）

幂等：只处理编号为空的记录 ⇒ 可重复执行。
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from process.models import ProcessParameter


class Command(BaseCommand):
    help = '回填存量工艺参数编号（parameter_no）；默认预览，加 --apply 才写库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id', type=int, default=None,
            help='只回填指定公司的记录（默认全部）',
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
        company_id = options['company_id']
        apply_changes = options['apply']
        limit = options['limit']

        # 待回填：编号为空的全部记录（含软删 —— 编号不回收）
        qs = ProcessParameter.all_objects.filter(
            Q(parameter_no__isnull=True) | Q(parameter_no='')
        )
        if company_id is not None:
            qs = qs.filter(company_id=company_id)
        # 排序决定同秒内的序号顺序：同租户内按创建时刻，再按自增 id
        qs = qs.order_by('company_id', 'created_at', 'id')
        total = qs.count()
        if limit is not None:
            qs = qs[:limit]

        if total == 0:
            self.stdout.write(self.style.SUCCESS('没有需要回填的记录（编号已全部就绪）'))
            return

        self.stdout.write(f'待回填记录：{total} 条')
        if not apply_changes:
            self.stdout.write(self.style.WARNING('当前为预览模式（未写库），加 --apply 执行回填'))
        self.stdout.write('')

        # 按 (租户, 秒) 分组：同组内共享编号前缀，序号依次递增
        groups = {}
        for param in qs:
            prefix = ProcessParameter.parameter_no_prefix(param.created_at)
            groups.setdefault((param.company_id, prefix), []).append(param)

        plan = []  # [(parameter, 编号)]
        for (cid, prefix), params in groups.items():
            # 已占用的序号（含同租户同前缀的既有编号）⇒ 从其后开始
            used = ProcessParameter.used_parameter_seqs(cid, prefix)
            next_seq = (max(used) + 1) if used else 1
            for param in params:
                plan.append((param, ProcessParameter.build_parameter_no(param.created_at, next_seq)))
                next_seq += 1

        # 预览输出（前 20 条）
        for param, no in plan[:20]:
            self.stdout.write(
                f'  id={param.id:<6} company={str(param.company_id):<6} '
                f'created_at={param.created_at:%Y-%m-%d %H:%M:%S} → {no}'
            )
        if len(plan) > 20:
            self.stdout.write(f'  ... 其余 {len(plan) - 20} 条省略')

        # 冲突自检：同租户内不得出现重复编号
        seen = {}
        for param, no in plan:
            key = (param.company_id, no)
            if key in seen:
                self.stderr.write(
                    self.style.ERROR(
                        f'编号冲突：company={param.company_id} {no} '
                        f'（id={seen[key]} 与 id={param.id}）'
                    )
                )
                return
            seen[key] = param.id

        self.stdout.write('')
        if not apply_changes:
            self.stdout.write(self.style.SUCCESS(f'预览完成：{len(plan)} 条待回填（未写库）'))
            return

        # 写库：用 update 绕过 save()（save() 不会覆盖已有编号，但逐条 save 触发额外逻辑）
        with transaction.atomic():
            updated = 0
            for param, no in plan:
                count = ProcessParameter.all_objects.filter(id=param.id).update(parameter_no=no)
                updated += count
            self.stdout.write(self.style.SUCCESS(f'回填完成：更新 {updated} 条'))
