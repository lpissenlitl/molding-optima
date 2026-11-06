"""
Django management command: 导入专家规则（ExpertRule）到数据库

铺两层专家规则：
- **平台层**（公共大库，owner_type='system'）：从内置 JSON 导入，规则库编码 `expert_rules`
- **租户层**（租户私库，owner_type='tenant'）：内置少量 demo 规则，演示「叶子级覆盖」

使用方法：
    python manage.py init_expert_rules
    python manage.py init_expert_rules --tenant-company-code hai_xin_mold_co
    python manage.py init_expert_rules --tenant-company-code ''   # 只铺平台层
"""
import json

from django.core.management.base import BaseCommand

from identity.const import SYSTEM_DEMO_COMPANY_CODE
from identity.models.company import Company
from process.models.rules import RuleLibrary, ExpertRule
from process.services import rule as rule_service
from utils.console import configure_console_encoding
from utils.data_paths import EXPERT_RULES_JSON, resolve_data_path


# ---- 租户私库 demo（分层叠加的租户层示例）----
# ⚠️ 引擎按 (layer, priority) 排序合并，租户层**后加载** ⇒ **叶子级 key 覆盖**平台层
#   （租户只写要改的那个值，平台同组其它值全部保留）。下面三条分别演示：
#   ① 覆盖平台 MATERIAL_PC_ABS 的注射速度比（同组其它 key 保留）；
#   ② 覆盖平台 MOLD_TEMP_DEFAULTS 的模温兜底（仅全局兜底，不影响材料推荐值）；
#   ③ 覆盖平台 GATE_DIRECT 的保压公式（同条件）。
TENANT_DEMO_COMPANY_CODE = 'hai_xin_mold_co'
TENANT_DEMO_LIBRARY_CODE = 'tenant_expert_rules'
TENANT_DEMO_RULES = [
    {
        'rule_code': 'TENANT_PC_ABS',
        'rule_name': '租户 PC+ABS 注射速度（私库覆盖）',
        'priority': 100,
        'is_active': True,
        'conditions': [
            {'field': 'polymer.abbreviation', 'operator': 'exact', 'value': 'PC+ABS'},
        ],
        # 只写要改的两个 key：inj_ratio_threshold / inj_ratio_coef 保留平台层
        'coefficients': {
            'injection': {'inj_velo_ratio_thin': 0.19, 'inj_velo_ratio_thick': 0.30},
        },
    },
    {
        'rule_code': 'TENANT_MOLD_TEMP',
        'rule_name': '租户模温默认值（私库覆盖）',
        'priority': 100,
        'is_active': True,
        'conditions': [],
        'coefficients': {'mold_temp': {'default': 58}},
    },
    {
        'rule_code': 'TENANT_GATE_DIRECT',
        'rule_name': '租户直浇口保压公式（私库覆盖）',
        'priority': 100,
        'is_active': True,
        'conditions': [
            {
                'field': 'product.gate_type',
                'operator': 'in',
                'value': ['直浇口', '护耳式浇口', '点浇口'],
            },
        ],
        'coefficients': {'holding': {'hold_time_formula': '0.45 + 0.09 * avg_thickness'}},
    },
]


class Command(BaseCommand):
    help = '导入专家规则（ExpertRule）到数据库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            type=str,
            help='专家规则 JSON 文件路径（可选，默认使用内置路径）',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制覆盖已有规则',
        )
        parser.add_argument(
            '--tenant-company-code',
            type=str,
            default=TENANT_DEMO_COMPANY_CODE,
            help=(
                '租户私库 demo 所属租户的公司编码（默认 %s）；'
                '传空字符串则只铺平台层' % TENANT_DEMO_COMPANY_CODE
            ),
        )

    def handle(self, *args, **options):
        configure_console_encoding()

        json_path = options.get('json')
        force_update = options.get('force', False)

        self.stdout.write(self.style.NOTICE('=== 导入专家规则（ExpertRule） ===\n'))

        # 默认 JSON 路径（专家规则数据文件，与 rule_loader.py 共享）
        if json_path is None:
            json_path = EXPERT_RULES_JSON
        json_path = resolve_data_path(json_path)

        # 读取 JSON 文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'文件不存在: {json_path}'))
            return

        rules = data.get('rules', [])
        self.stdout.write(f'读取到 {len(rules)} 条规则')

        # 系统库归属到 system_demo 公司（通过 code 反查 id，不能硬编码）
        system_company = Company.objects.filter(code=SYSTEM_DEMO_COMPANY_CODE).first()
        if not system_company:
            self.stdout.write(self.style.ERROR(
                f'系统演示公司（code={SYSTEM_DEMO_COMPANY_CODE}）不存在，请先执行 init_platform'
            ))
            return

        # 创建或获取规则库（专家规则库标识，语义清晰，避免与其他类型规则混淆）
        library, created = RuleLibrary.objects.get_or_create(
            library_code='expert_rules',
            defaults={
                'library_name': '工艺初始化规则库',
                'description': '工艺参数初始化专家规则库',
                'owner_type': 'system',
                'priority': 100,
                'is_active': True,
                'company_id': system_company.id,
            }
        )
        # 修复历史数据：如果库已存在但 company_id 为 None，补齐到 system_demo
        if not created and library.company_id is None:
            library.company_id = system_company.id
            library.save(update_fields=['company_id'])
            self.stdout.write(self.style.WARNING(
                f'修复库归属: {library.library_name} → company_id={system_company.id}'
            ))
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
                    rule.priority = rule_data.get('priority', 100)
                    rule.is_active = rule_data.get('is_active', True)
                    rule.conditions = rule_data.get('conditions', [])
                    rule.coefficients = rule_data.get('coefficients', {})
                    rule.save()
                    updated += 1
                    self.stdout.write(f'  更新: {rule_code}')
                else:
                    skipped += 1
                    self.stdout.write(f'  跳过(已存在): {rule_code}')
            else:
                # 创建新规则
                # 注意：ExpertRule 无 description / source 字段（已在 0005 迁移中移除）
                ExpertRule.objects.create(
                    rule_library=library,
                    rule_code=rule_code,
                    rule_name=rule_name,
                    priority=rule_data.get('priority', 100),
                    is_active=rule_data.get('is_active', True),
                    conditions=rule_data.get('conditions', []),
                    coefficients=rule_data.get('coefficients', {}),
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

        # ---- 租户层（租户私库 demo）----
        tenant_code = options.get('tenant_company_code') or ''
        if tenant_code:
            self.stdout.write('')
            self._import_tenant_demo_rules(tenant_code, force_update)

    def _import_tenant_demo_rules(self, company_code, force_update=False):
        """导入**租户私库** demo 专家规则（分层叠加的租户层示例）。

        ⚠️ 租户层与平台层的关系：引擎按 (layer, priority) 排序合并、租户层后加载
        ⇒ **叶子级 key 覆盖**平台层（租户只写要改的那个值，平台同组其它值保留）。
        """
        self.stdout.write(self.style.NOTICE('=== 导入租户私库 demo 专家规则 ===\n'))

        tenant = Company.objects.filter(code=company_code).first()
        if tenant is None:
            self.stdout.write(self.style.WARNING(
                f'租户公司（code={company_code}）不存在，跳过租户私库 demo'
            ))
            return

        # 租户私库：同一租户内 library_code 唯一
        library = RuleLibrary.objects.filter(
            company_id=tenant.id,
            library_code=TENANT_DEMO_LIBRARY_CODE,
            library_type='expert',
            is_deleted=False,
        ).first()
        if library is None:
            library = RuleLibrary.create_with_check(
                library_code=TENANT_DEMO_LIBRARY_CODE,
                library_name='租户私有专家规则库',
                description=(
                    '租户级专家规则私库（demo）：与平台公共大库分层叠加，'
                    '租户层叶子级覆盖平台层'
                ),
                owner_type='tenant',
                library_type='expert',
                priority=100,
                is_active=True,
                company_id=tenant.id,
            )
            self.stdout.write(self.style.SUCCESS(f'创建租户私库: {library.library_name}'))
        else:
            self.stdout.write(f'使用已有租户私库: {library.library_name}')

        imported = 0
        updated = 0
        skipped = 0

        for rule_data in TENANT_DEMO_RULES:
            rule_code = rule_data['rule_code']
            exists = ExpertRule.objects.filter(
                rule_library=library,
                rule_code=rule_code,
                is_deleted=False,
            ).first()

            if exists is None:
                rule_service.add_expert_rule(
                    company_id=tenant.id,
                    organization_id=None,
                    rule_library_id=library.id,
                    is_superuser=False,
                    **rule_data,
                )
                imported += 1
                self.stdout.write(self.style.SUCCESS(f'  导入: {rule_code}'))
            elif force_update:
                exists.rule_name = rule_data['rule_name']
                exists.priority = rule_data['priority']
                exists.is_active = rule_data['is_active']
                exists.conditions = rule_data['conditions']
                exists.coefficients = rule_data['coefficients']
                exists.save()
                updated += 1
                self.stdout.write(f'  更新: {rule_code}')
            else:
                skipped += 1
                self.stdout.write(f'  跳过(已存在): {rule_code}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== 租户私库导入完成 ==='))
        self.stdout.write(f'  新增: {imported} 条')
        self.stdout.write(f'  更新: {updated} 条')
        self.stdout.write(f'  跳过: {skipped} 条')
        self.stdout.write(
            f'  租户私库规则总数: '
            f'{ExpertRule.objects.filter(rule_library=library, is_deleted=False).count()}'
        )