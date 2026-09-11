"""
Django management command: 初始化 FuzzyEngine 规则库 + 演示规则

初始化内容：
  1) general 通用规则库（priority=0）
  2) packaging 包装容器规则库（priority=10，作为示例）
  3) RuleMethod 演示规则（覆盖 PE 酒瓶短射场景，验证双层并行 + 优先级协议）

使用方法：
    python manage.py init_fuzzy_demo
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from process.models.rules import RuleLibrary, RuleMethod, RuleKeyword


# 演示规则
DEFAULT_LIBS = [
    {
        'library_code': 'general',
        'library_name': '通用规则库',
        'description': '跨产品/材料生效的兜底规则库（兜底层规则来源）',
        'owner_type': 'system',
        'priority': 0,
    },
    {
        'library_code': 'packaging',
        'library_name': '包装容器规则库',
        'description': '包装容器大类通用规则（按 polymer_category 区分）',
        'owner_type': 'system',
        'priority': 10,
    },
]


# 演示规则数据（覆盖 PE 酒瓶短射场景的双层并行）
DEMO_RULES = [
    # --- 工厂级：PE 酒瓶精确规则 ---
    {
        'library_code': 'packaging',
        'rule_no': 'RM-DEMO-001',
        'priority': 10.0,    # L1 精确协议
        'rule_level': 'factory',
        'defect_name': 'SHORTSHOT',
        'polymer_category': 'PE',
        'product_category': '酒瓶',
        'rule_type': 'shortshot_adjust',
        'rule_description': 'PE 酒瓶短射 → 显著延长保压时间',
        'rule_explanation': 'PE 酒瓶短射时保压时间从 3.5s 延长到 7.5s 以充分补料',
        'rule_content': {
            'conditions': [
                {'param': 'hold_time', 'fuzzy_level': 'low'},
            ],
            'adjustments': [
                {
                    'type': 'param',
                    'param': 'hold_time',
                    'action': 'add',
                    'value': 4,
                    'value_type': 'absolute',
                },
            ],
        },
        'source': 'expert',
    },

    # --- 工厂级：PE 通用（不限定产品）的短射规则 ---
    {
        'library_code': 'packaging',
        'rule_no': 'RM-DEMO-002',
        'priority': 5.0,    # L2 部分-polymer 协议
        'rule_level': 'factory',
        'defect_name': 'SHORTSHOT',
        'polymer_category': 'PE',
        'product_category': None,
        'rule_type': 'shortshot_adjust',
        'rule_description': 'PE 通用短射 → 适度延长保压时间',
        'rule_explanation': 'PE 材料制品短射时保压时间延长 2s',
        'rule_content': {
            'conditions': [
                {'param': 'hold_time', 'fuzzy_level': 'low'},
            ],
            'adjustments': [
                {
                    'type': 'param',
                    'param': 'hold_time',
                    'action': 'add',
                    'value': 2,
                    'value_type': 'absolute',
                },
            ],
        },
        'source': 'expert',
    },

    # --- 兜底层：跨产品通用兜底规则 ---
    {
        'library_code': 'general',
        'rule_no': 'RM-DEMO-003',
        'priority': 1.0,    # L4 默认协议
        'rule_level': 'fallback',
        'defect_name': 'SHORTSHOT',
        'polymer_category': None,
        'product_category': None,
        'rule_type': 'shortshot_adjust',
        'rule_description': '通用兜底短射规则（模糊级调整）',
        'rule_explanation': '新机型无特定规则时，按模糊级给予保守调整',
        'rule_content': {
            'conditions': [
                {'param': 'hold_time', 'fuzzy_level': 'low'},
            ],
            'adjustments': [
                {
                    'type': 'param',
                    'param': 'hold_time',
                    'action': 'add',
                    'level': 'low',
                },
            ],
        },
        'source': 'expert',
    },

    # --- 工厂级：飞边通用规则 ---
    {
        'library_code': 'general',
        'rule_no': 'RM-DEMO-004',
        'priority': 10.0,
        'rule_level': 'factory',
        'defect_name': 'FLASH',
        'polymer_category': None,
        'product_category': None,
        'rule_type': 'flash_adjust',
        'rule_description': '飞边通用规则 → 降低保压压力',
        'rule_explanation': '保压压力过高引起飞边时降低 10MPa',
        'rule_content': {
            'conditions': [
                {'param': 'hold_pres', 'fuzzy_level': 'high'},
            ],
            'adjustments': [
                {
                    'type': 'param',
                    'param': 'hold_pres',
                    'action': 'reduce',
                    'value': 10,
                    'value_type': 'absolute',
                },
            ],
        },
        'source': 'expert',
    },
]


class Command(BaseCommand):
    help = '初始化 FuzzyEngine 规则库与演示规则'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制覆盖已存在的演示规则',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force_update = options.get('force', False)

        self.stdout.write(self.style.NOTICE('=== 初始化 FuzzyEngine 规则库 ===\n'))

        # 1) 创建默认规则库
        for lib_data in DEFAULT_LIBS:
            lib, created = RuleLibrary.objects.get_or_create(
                library_code=lib_data['library_code'],
                defaults=lib_data,
            )
            status = self.style.SUCCESS('创建') if created else '使用'
            self.stdout.write(
                f"  {status}: {lib.library_code} ({lib.library_name}) priority={lib.priority}"
            )

        # 2) 创建演示规则
        self.stdout.write('\n=== 导入演示规则 ===')
        imported = 0
        updated = 0
        skipped = 0

        for rule_data in DEMO_RULES:
            library_code = rule_data.pop('library_code')
            library = RuleLibrary.objects.get(library_code=library_code)

            rule_no = rule_data['rule_no']
            exists = RuleMethod.objects.filter(
                rule_library=library,
                rule_no=rule_no,
            ).exists()

            if exists:
                if force_update:
                    rm = RuleMethod.objects.get(rule_library=library, rule_no=rule_no)
                    for k, v in rule_data.items():
                        setattr(rm, k, v)
                    rm.save()
                    updated += 1
                    self.stdout.write(self.style.WARNING(f'  更新: {rule_no}'))
                else:
                    skipped += 1
                    self.stdout.write(f'  跳过(已存在): {rule_no}')
                continue

            RuleMethod.objects.create(rule_library=library, **rule_data)
            imported += 1
            self.stdout.write(self.style.SUCCESS(f'  新增: {rule_no}'))

        # 3) 提示用户配置 RuleKeyword.step
        self.stdout.write('\n=== 后续操作提示 ===')
        self.stdout.write(
            '请确认 RuleKeyword.step 字段已填充（如未填充，运行：）\n'
            '  python manage.py init_fuzzy_ranges  # 从 range_test.csv 迁移\n'
        )

        # 4) 输出统计
        self.stdout.write(self.style.SUCCESS('=== 初始化完成 ==='))
        self.stdout.write(f'  新增规则: {imported}')
        self.stdout.write(f'  更新规则: {updated}')
        self.stdout.write(f'  跳过规则: {skipped}')

        # 5) 验证加载路径
        self.stdout.write('\n=== 验证规则加载（验证三级特异性匹配）===')
        for specificity_filter in [
            ('L1 精确 PE+酒瓶', 'SHORTSHOT', 'PE', '酒瓶'),
            ('L2 部分-polymer (PE)', 'SHORTSHOT', 'PE', None),
            ('L4 默认', 'SHORTSHOT', None, None),
            ('FLASH 默认', 'FLASH', None, None),
        ]:
            label, defect, polymer, product = specificity_filter
            qs = RuleMethod.objects.filter(
                defect_name=defect,
                polymer_category=polymer,
                product_category=product,
                is_active=True,
            )
            self.stdout.write(f'  {label}: 命中 {qs.count()} 条')
