"""规则挖掘 demo 数据播种命令。

用法：
    python manage.py seed_mining_demo --company-id 11
    python manage.py seed_mining_demo --company-id 11 --reset

功能：
    在指定公司下造一批「带 adjustments 的调机记录」⇒ 规则挖掘链路可闭环。

⚠️ **为什么要 demo 数据**
    存量调机记录的 `adjustments` **全为空**（规范化训练样本是后加的字段，
    历史流水没有回填）⇒ 提炼器当场跑只能得到 0 条样本、0 条规则。
    本命令补一批**结构真实**的调机记录，让「采集 → 挖掘 → 候选规则入库」
    全链路先跑通；真实数据到位后把 demo 数据清掉即可。

⚠️ **数据结构与系统产出完全同构**
    `adjustments` 正常由 `tuning.build_adjustments` 自动生成（用户不可定义）；
    本命令按**同一结构**手写，字段与取值口径完全一致
    （见 `TuningRecord` 模型注释与 `build_adjustments`）。

⚠️ **必须遵守的业务约束：合格态无缺陷**
    `tuning.TuningService.upsert_tuning_record` 有一条规定：
    **合格态（qualified）的缺陷反馈一律丢弃** ⇒ 合格样本的 `defects` 恒为空。
    demo 数据若给合格样本塞缺陷，就与系统真实产出**不同构**
    （后果：语料里出现现实中不存在的样本，挖出的规则无法在真实数据上复现）。
    ⇒ 本命令的 A 组（qualified）**故意不带缺陷**。

⚠️ **demo 数据用英文缺陷名**
    缺陷名取算法命名空间（`SHORTSHOT` / `FLASH`），与 `RuleKeyword.keyword_name`
    同构；中文名在 `RuleKeyword.keyword_alias` 里。

⚠️ **预期产出（默认阈值 min_support=0.05 / min_confidence=0.7 / min_lift=1.0）**
    18 条样本分四组：
      A 组 6 条：无缺陷 + inj_pres_1:increase            → qualified
      B 组 5 条：SHORTSHOT + inj_pres_1:increase         → improved
      C 组 4 条：SHORTSHOT + hold_pres_1:decrease        → unqualified
      D 组 3 条：FLASH     + hold_pres_1:decrease        → improved
    ⇒ 应挖出 **4 条**候选规则：
      1. {SHORTSHOT, inj_pres_1:increase}  ⇒ improved    sup=0.278 conf=1.0 lift=2.25  【可落地】
      2. {SHORTSHOT, hold_pres_1:decrease} ⇒ unqualified sup=0.222 conf=1.0 lift=4.5   （负向）
      3. {FLASH}                           ⇒ improved    sup=0.167 conf=1.0 lift=2.25  （无变更）
      4. {FLASH, hold_pres_1:decrease}     ⇒ improved    sup=0.167 conf=1.0 lift=2.25  【可落地】
    （1 与 4 含变更动作且后件为正向 ⇒ 能落地成 RuleMethod；
      2 是负向经验（不改）；3 没有可建议的动作 ⇒ 同样不落地）
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from process.models import ProcessCondition, ProcessParameter, TuningRecord


#: demo 工艺条件编号（幂等键）
DEMO_CONDITION_NO = 'DEMO-MINING-001'

#: demo 参数编号前缀
DEMO_PARAMETER_PREFIX = 'DEMO-MINING-P'

#: demo 缺陷元数据（keyword_name 取算法命名空间英文名）
DEMO_DEFECTS = {
    'SHORTSHOT': {'keyword_id': 1228, 'position': 'DLSHORTSHOT2', 'label': '短射'},
    'FLASH': {'keyword_id': 1078, 'position': 'DLFLASH2', 'label': '飞边'},
}

#: demo 样本分组（组内多条同构）
#:
#: ⚠️ **qualified 组必须无缺陷**（业务规则会清空合格态的缺陷反馈）
#: ⚠️ `level` 取值与现网一致（medium / very_low / low）
DEMO_GROUPS = [
    {
        'code': 'A',
        'count': 6,
        'defects': [],
        'param': 'inj_pres_1',
        'before': 50,
        'after': 60,
        'result': 'qualified',
        'level': None,
    },
    {
        'code': 'B',
        'count': 5,
        'defects': ['SHORTSHOT'],
        'param': 'inj_pres_1',
        'before': 50,
        'after': 60,
        'result': 'improved',
        'level': 'medium',
    },
    {
        'code': 'C',
        'count': 4,
        'defects': ['SHORTSHOT'],
        'param': 'hold_pres_1',
        'before': 40,
        'after': 35,
        'result': 'unqualified',
        'level': 'very_low',
    },
    {
        'code': 'D',
        'count': 3,
        'defects': ['FLASH'],
        'param': 'hold_pres_1',
        'before': 40,
        'after': 35,
        'result': 'improved',
        'level': 'medium',
    },
]

#: 各结果对应的「上一轮结果」（写进 `tuning_context.previous_result`）
#:
#: ⚠️ 这是**相对评价**的语义来源：`improved` 表示比上一轮好，
#: 所以上一轮必然是 `worse` / `unchanged`。
_PREVIOUS_RESULT = {
    'qualified': 'worse',
    'improved': 'worse',
    'unqualified': 'unchanged',
    'worse': 'improved',
}


def _direction(before, after) -> str:
    """变更方向（口径与 `tuning._diff_snapshots` 一致）。"""
    if after > before:
        return 'increase'
    if after < before:
        return 'decrease'
    return 'hold'


class Command(BaseCommand):
    help = '播种规则挖掘用的 demo 调机记录（带 adjustments）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id', type=int, required=True,
            help='目标公司 id（demo 数据归属于该公司）',
        )
        parser.add_argument(
            '--reset', action='store_true',
            help='先软删除既有 demo 数据再重建',
        )

    def handle(self, *args, **options):
        from identity.models import Company

        company_id = options['company_id']
        company = Company.objects.filter(id=company_id).first()
        if company is None:
            raise CommandError(f'公司不存在：id={company_id}')

        if options['reset']:
            removed = self._reset(company)
            self.stdout.write(f'已软删除既有 demo 数据：{removed} 条')

        created = updated = 0
        with transaction.atomic():
            condition = self._get_or_create_condition(company)
            for index, group in enumerate(DEMO_GROUPS):
                for offset in range(group['count']):
                    seq = index * 10 + offset + 1
                    parameter_no = f'{DEMO_PARAMETER_PREFIX}{seq:03d}'
                    parameter = self._get_or_create_parameter(
                        condition, company, parameter_no, group,
                    )
                    is_new = self._upsert_record(
                        parameter, company, group, seq,
                    )
                    if is_new:
                        created += 1
                    else:
                        updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'demo 调机记录：新建 {created} 条，复用 {updated} 条，'
            f'公司={company.name}({company_id})，工艺条件={DEMO_CONDITION_NO}'
        ))
        self.stdout.write(
            '下一步：python manage.py mine_rules --company-id '
            f'{company_id}'
        )

    # --- 内部 ---

    def _reset(self, company) -> int:
        """软删除既有 demo 数据（调机记录 + 参数）。"""
        parameters = ProcessParameter.objects.filter(
            process_condition__condition_no=DEMO_CONDITION_NO,
            company_id=company.id,
        )
        removed = 0
        for parameter in parameters:
            for record in TuningRecord.objects.filter(
                process_parameter=parameter,
            ):
                record.soft_delete()
                removed += 1
            parameter.soft_delete()
        return removed

    def _get_or_create_condition(self, company) -> ProcessCondition:
        """取（或建）demo 工艺条件。"""
        condition = ProcessCondition.objects.filter(
            company_id=company.id, condition_no=DEMO_CONDITION_NO,
        ).first()
        if condition is not None:
            return condition
        return ProcessCondition.objects.create(
            company=company,
            status='draft',
            condition_no=DEMO_CONDITION_NO,
            origin_type='manual_creation',
        )

    def _get_or_create_parameter(
        self,
        condition: ProcessCondition,
        company,
        parameter_no: str,
        group: dict,
    ) -> ProcessParameter:
        """取（或建）demo 工艺参数（把变更后的值写进对应字段）。"""
        # 用 all_objects 查找（含软删）：命中被软删的上一代时应恢复它，
        # 否则会新建同 parameter_no 的第二条 ⇒ 同一编号两条并存。
        parameter = ProcessParameter.all_objects.filter(
            process_condition=condition, parameter_no=parameter_no,
        ).first()
        if parameter is None:
            parameter = ProcessParameter(
                process_condition=condition,
                company=company,
                parameter_no=parameter_no,
                param_source='manual_adjusted',
            )
        elif parameter.is_deleted:
            parameter.restore()
        # 把变更后的值写进对应字段（快照里才看得到这次调整）
        setattr(parameter, group['param'], group['after'])
        parameter.save()
        return parameter

    def _upsert_record(
        self,
        parameter: ProcessParameter,
        company,
        group: dict,
        seq: int,
    ) -> bool:
        """写（或更新）调机记录。

        Returns:
            True = 新建；False = 复用并更新。
        """
        defect_feedbacks = []
        for defect in group['defects']:
            meta = DEMO_DEFECTS.get(defect, {})
            defect_feedbacks.append({
                'keyword_id': meta.get('keyword_id'),
                'keyword_name': defect,
                'level': group.get('level') or 'medium',
                'position': meta.get('position'),
                'position_3d': None,
            })

        changes = [{
            'param': group['param'],
            'before': group['before'],
            'after': group['after'],
            'direction': _direction(group['before'], group['after']),
            'rule_ref': None,
        }]
        adjustments = {
            'defects': list(group['defects']),
            'changes': changes,
            'tuning_context': {
                'iteration': seq,
                'previous_result': _PREVIOUS_RESULT.get(
                    group['result'], 'unchanged',
                ),
            },
        }

        record = TuningRecord.all_objects.filter(
            process_parameter=parameter,
        ).first()
        if record is None:
            TuningRecord.objects.create(
                process_parameter=parameter,
                company=company,
                defect_feedbacks=defect_feedbacks,
                adjustments=adjustments,
                result=group['result'],
                result_detail='规则挖掘 demo 数据',
                previous_parameter={group['param']: group['before']},
            )
            return True

        if record.is_deleted:
            record.restore()
        record.defect_feedbacks = defect_feedbacks
        record.adjustments = adjustments
        record.result = group['result']
        record.previous_parameter = {group['param']: group['before']}
        record.save()
        return False