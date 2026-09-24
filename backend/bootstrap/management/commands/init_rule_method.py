"""
Django management command: 导入规则方法（RuleMethod / 模糊规则）到数据库

数据源：process/refs/rule_method_by_library.json（旧系统导出的按库分组的模糊规则清单）

策略：
- 基础库（JSON 中 rule_type='基础库'）→ DB library_code='base'，主基础库，priority=100
- 子规则库（JSON 中 rule_type='子规则库'）→ DB library_code 与 JSON key 保持一致，priority=10

字段映射（JSON → Model.RuleMethod）：
  rule_description     →  rule_description   (去尾空格)
  rule_explanation     →  rule_explanation
  defect_label         →  defect_label
  defect_code          →  defect_code
  polymer_abbreviation →  polymer_abbreviation
  product_type         →  product_category   ← 字段名修正（旧系统命名不一致）
  is_active (1/0)      →  is_active (bool)
  priority             →  priority            (默认 1)
  source               →  'expert'            ← 统一记为专家经验（旧数据未区分）

库归属：
  - 所有库 owner_type='system'，归属 system_demo 公司
  - library_type='fuzzy'（与 service.add_rule_method 校验一致）

使用方法：
  python manage.py init_rule_method                          # 默认 JSON
  python manage.py init_rule_method --json /path/to/file     # 自定义 JSON
  python manage.py init_rule_method --dry-run                # 只打印不入库
  python manage.py init_rule_method --force                  # 覆盖已存在规则
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from identity.const import SYSTEM_DEMO_COMPANY_CODE
from identity.models.company import Company
from process.models.rules import RuleLibrary, RuleMethod


# 默认 JSON 路径
DEFAULT_JSON_PATH = 'process/refs/rule_method_by_library.json'

# 基础库优先级（最高，定义为系统默认基础库）
BASE_LIBRARY_PRIORITY = 100

# 补充库优先级（低于基础库，作为可选补充）
SUPPLEMENT_LIBRARY_PRIORITY = 10

# 规则默认 priority（旧 JSON 字段全部为 null）
DEFAULT_RULE_PRIORITY = 1

# 规则默认来源（旧数据未区分，统一记为专家经验）
DEFAULT_RULE_SOURCE = 'expert'


def build_library_def(json_key: str, json_libraries: dict) -> dict:
    """
    根据 JSON 的 library key 生成 RuleLibrary 的定义参数

    主库识别规则：JSON 库下所有规则 rule_type 都是 '基础库'
    补充库识别规则：其他（含全部为 '子规则库' 或 混合类型）

    判定逻辑采用"主库优先"：只要存在任何一条 rule_type='基础库'
    的规则，即识别为主库（避免数据混入导致误判为补充库）。

    Args:
        json_key: JSON 中 libraries 的 key（如 '基础库' / 'R20230825161658'）
        json_libraries: JSON 完整 libraries 字典（用于遍历 rules 探测 rule_type）

    Returns:
        dict: {library_code, library_name, priority, library_type, owner_type, is_active, description}
    """
    items = json_libraries.get(json_key, [])

    # 扫描所有规则的 rule_type，决定主/补充库
    rule_types = {r.get('rule_type') for r in items if r.get('rule_type')}
    is_base_library = '基础库' in rule_types

    if is_base_library:
        # 主库：标准化 library_code，priority=100
        return {
            'library_code': 'base',
            'library_name': '基础模糊规则库',
            'priority': BASE_LIBRARY_PRIORITY,
            'library_type': 'fuzzy',
            'owner_type': 'system',
            'is_active': True,
            'description': (
                f'系统默认基础模糊规则库（来源 JSON key={json_key!r}，'
                f'{len(items)} 条规则）'
            ),
        }

    # 补充库：library_code 沿用 JSON key（已经是 R+时间戳 格式，保留可读性）
    return {
        'library_code': json_key,
        'library_name': f'补充规则库 - {json_key}',
        'priority': SUPPLEMENT_LIBRARY_PRIORITY,
        'library_type': 'fuzzy',
        'owner_type': 'system',
        'is_active': True,
        'description': (
            f'按产品/场景补充的模糊规则库（JSON key={json_key!r}，'
            f'{len(items)} 条规则）'
        ),
    }


def normalize_is_active(value) -> bool:
    """
    JSON 的 is_active 字段兼容多种类型：1/0、true/false、True/False
    缺失时默认为 True（启用）
    """
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'y', 't')
    return False


class Command(BaseCommand):
    help = '从 process/refs/rule_method_by_library.json 导入 RuleMethod 模糊规则'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            type=str,
            default=DEFAULT_JSON_PATH,
            help=f'JSON 路径（默认: {DEFAULT_JSON_PATH}）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只打印计划，不写库',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='覆盖已存在的规则（更新字段而非跳过）',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        json_path = Path(options['json'])
        dry_run = options['dry_run']
        force_update = options['force']

        self.stdout.write(self.style.NOTICE('=== 导入 RuleMethod 模糊规则 ===\n'))

        # 1) 校验 JSON 文件
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f'JSON 文件不存在: {json_path}'))
            return
        try:
            with json_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'JSON 解析失败: {e}'))
            return

        json_libraries = data.get('libraries', {})
        meta = data.get('_meta', {})
        self.stdout.write(f'JSON 文件: {json_path}')
        if meta:
            self.stdout.write(
                f'_meta: total_records={meta.get("total_records")}, '
                f'library_count={meta.get("library_count")}'
            )
        self.stdout.write(f'读取到 {len(json_libraries)} 个规则库\n')

        # 2) 反查 system_demo 公司
        system_company = Company.objects.filter(code=SYSTEM_DEMO_COMPANY_CODE).first()
        if not system_company:
            self.stdout.write(self.style.ERROR(
                f'系统演示公司（code={SYSTEM_DEMO_COMPANY_CODE}）不存在，'
                f'请先执行 init_platform'
            ))
            return

        # 3) 统计
        lib_imported = 0  # 新建的库数
        lib_reused = 0    # 复用已有库数
        rule_imported = 0
        rule_updated = 0
        rule_skipped = 0
        errors = []

        # 4) 遍历每个库
        for json_key, items in json_libraries.items():
            lib_def = build_library_def(json_key, json_libraries)

            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO(
                f'[{lib_def["library_code"]}] {lib_def["library_name"]} '
                f'({len(items)} 条规则, priority={lib_def["priority"]})'
            ))

            # 4.1) 创建 / 复用 RuleLibrary
            library = None
            if not dry_run:
                library, created = RuleLibrary.objects.get_or_create(
                    library_code=lib_def['library_code'],
                    company_id=system_company.id,
                    is_deleted=False,
                    defaults={
                        'library_name': lib_def['library_name'],
                        'description': lib_def['description'],
                        'owner_type': lib_def['owner_type'],
                        'library_type': lib_def['library_type'],
                        'priority': lib_def['priority'],
                        'is_active': lib_def['is_active'],
                    },
                )
                # 修复历史数据：company_id 为 None 时补齐
                if not created and library.company_id is None:
                    library.company_id = system_company.id
                    library.save(update_fields=['company_id'])
                    self.stdout.write(self.style.WARNING(
                        '  修复库归属: company_id → '
                        f'{system_company.id}'
                    ))

            if dry_run:
                self.stdout.write(f'  [DRY-RUN] 将创建/复用: {lib_def["library_code"]}')
            elif created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建规则库'))
                lib_imported += 1
            else:
                self.stdout.write(f'  → 使用已有规则库')
                lib_reused += 1

            # 4.2) 遍历规则
            for idx, rule_data in enumerate(items, start=1):
                try:
                    rule_desc = (rule_data.get('rule_description') or '').strip()
                    defect_code = (rule_data.get('defect_code') or '').strip()
                    defect_label = (rule_data.get('defect_label') or '').strip()

                    # 必填校验：rule_description + defect_code 至少有一个
                    if not rule_desc:
                        errors.append(
                            f'{lib_def["library_code"]}[{idx}]: '
                            f'rule_description 为空'
                        )
                        continue

                    if not dry_run:
                        # 去重查询：同库内 (defect_code + rule_description) 唯一
                        existing = RuleMethod.objects.filter(
                            rule_library=library,
                            defect_code=defect_code or None,
                            rule_description=rule_desc,
                            is_deleted=False,
                        ).first()

                        # 字段值映射
                        polymer = rule_data.get('polymer_abbreviation') or None
                        # 旧系统字段名 product_type → 新模型 product_category
                        product_cat = rule_data.get('product_type') or None
                        is_active = normalize_is_active(rule_data.get('is_active'))
                        priority = rule_data.get('priority') or DEFAULT_RULE_PRIORITY
                        explanation = rule_data.get('rule_explanation') or ''

                        if existing:
                            if not force_update:
                                rule_skipped += 1
                                continue
                            # --force 模式：更新已有规则
                            existing.rule_explanation = explanation
                            existing.polymer_abbreviation = polymer
                            existing.product_category = product_cat
                            existing.defect_label = defect_label
                            existing.is_active = is_active
                            existing.priority = priority
                            existing.source = DEFAULT_RULE_SOURCE
                            existing.confidence = 1.0
                            existing.save()
                            rule_updated += 1
                        else:
                            # 新建
                            RuleMethod.objects.create(
                                rule_library=library,
                                rule_description=rule_desc,
                                rule_explanation=explanation,
                                defect_label=defect_label,
                                defect_code=defect_code,
                                polymer_abbreviation=polymer,
                                product_category=product_cat,
                                is_active=is_active,
                                priority=priority,
                                confidence=1.0,
                                source=DEFAULT_RULE_SOURCE,
                                company_id=system_company.id,
                            )
                            rule_imported += 1
                    else:
                        # dry-run 模式：模拟判断（库还没建，但可以演示数量）
                        rule_imported += 1  # 仅作计数用

                except Exception as e:
                    errors.append(
                        f'{lib_def["library_code"]}[{idx}] '
                        f'(id={rule_data.get("id")}): {e}'
                    )

        # 5) 汇总
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== 导入完成 ==='))
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '  [DRY-RUN] 以下为模拟统计（未实际写入数据库）：'
            ))
        self.stdout.write(f'  规则库：新建 {lib_imported} 个 / 复用 {lib_reused} 个')
        self.stdout.write(f'  规则：  新增 {rule_imported} 条 / 更新 {rule_updated} 条 / 跳过 {rule_skipped} 条')
        self.stdout.write(f'  错误：  {len(errors)} 条')

        if errors:
            self.stdout.write(self.style.WARNING('\n=== 错误详情（前 20 条）==='))
            for err in errors[:20]:
                self.stdout.write(f'  {err}')

        # 6) 验证入库结果（dry-run 模式跳过）
        if not dry_run:
            self.stdout.write('\n=== 验证入库结果 ===')
            from django.db.models import Count
            by_library = (
                RuleLibrary.objects
                .filter(library_type='fuzzy', is_deleted=False)
                .annotate(rule_count=Count('rule_methods'))
                .values('library_code', 'library_name', 'priority', 'rule_count')
                .order_by('-priority', 'library_code')
            )
            for item in by_library:
                self.stdout.write(
                    f"  [{item['library_code']}] {item['library_name']} "
                    f"(priority={item['priority']}): {item['rule_count']} 条"
                )
            total = RuleMethod.objects.filter(is_deleted=False).count()
            self.stdout.write(f'\nRuleMethod 总数: {total}')
        else:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN 模式，未写库]'))