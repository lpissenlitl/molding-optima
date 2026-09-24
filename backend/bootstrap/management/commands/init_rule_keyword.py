"""
Django management command: 导入 RuleKeyword 主数据

数据源：process/refs/rule_keyword_curated.json（旧系统导出的关键词清单，已人工审校）

字段映射（按 2026-09-15 设计文档）：
  JSON.keyword_type (中文)  →  Model.category (3 类业务角色)
  JSON.description            →  Model.keyword_alias (中文别名)
  JSON.fuzzy_level            →  Model.fuzzy_level
  JSON.range_min/_max         →  Model.range_min/_max
  JSON.action_range_min/_max  →  Model.action_range_min/_max
  JSON.action_max_val         →  Model.action_max_val
  Model.keyword_type          ←  按关键词名前缀 + description 推断（物理量）
  Model.unit                  ←  按 keyword_type 给标准单位
  Model.parameter_kind        ←  默认 'setpoint'（本次不导入 actual）

不导入的数据（19 条）：
  - injectstage1-6（8）：fuzzy 引擎内部 one-hot 预处理中间变量
  - holdingstage1-5（5）：同上
  - meteringstage1-4（4）：同上
  - HOLDEXIST（1）：业务控制位（保压启用）
  - VALVEEXIST（1）：业务控制位（热流道启用）

去重策略：按 keyword_name 去重保留首条（327 条入库）

特殊 keyword：
  - 导入完 JSON 后，会额外确保 DEFECTFREE（无缺陷）存在
  - 业务场景：产品本轮试模无缺陷，但工艺仍可优化（减少周期时间、提产能、降能耗）
  - 排序：前端按 keyword_name='DEFECTFREE' 识别后排到第一，后端不需特殊排序
  - 命名选择：DEFECTFREE 而非 NONE（None 容易产生"无关键字"的歧义）

使用方法：
  python manage.py init_rule_keyword                          # 默认 JSON
  python manage.py init_rule_keyword --json /path/to/file     # 自定义 JSON
  python manage.py init_rule_keyword --dry-run                # 只打印不入库
  python manage.py init_rule_keyword --force                  # 覆盖已存在
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from identity.const import SYSTEM_DEMO_COMPANY_CODE
from identity.models.company import Company
from process.models.rules import RuleKeyword


DEFAULT_JSON_PATH = 'process/refs/rule_keyword_curated.json'

# ============================================================================
# JSON.keyword_type (中文) → Model.category (英文) 的映射
# ============================================================================
JSON_CATEGORY_MAP = {
    '参数': 'parameter',
    '缺陷': 'defect',
    '缺陷位置': 'defect_position',
    '非工艺参数': 'parameter',      # 实际是辅机参数 + 模式参数，统一归入 parameter
    '其他': 'parameter',
}

# ============================================================================
# 关键词名前缀 → 物理量类型 的映射（高优先级，先按前缀匹配）
# ============================================================================
# 命名约定：JSON 里很多参数是分段命名（BT1/BT2, IP0/IP1, PT0/PT1）
# 前缀足以识别物理量，按前缀查表最稳
KEYWORD_TYPE_BY_PREFIX = {
    # 温度类
    'BT': 'temperature',    # 料筒温度 (Barrel Temperature)
    'ET': 'temperature',    # 下料口温度
    'HRT': 'temperature',   # 热流道温度
    'MT': 'temperature',    # 模温机温度
    # 压力类
    'IP': 'pressure',       # 注射压力
    'PP': 'pressure',       # 保压压力
    'MBP': 'pressure',      # 储料背压
    'MP': 'pressure',       # 储料压力
    'CLAMP': 'force',       # 锁模力
    # 速度类
    'IV': 'speed',          # 注射速度
    'PV': 'speed',          # 保压速度
    'MSR': 'speed',         # 螺杆转速
    # 时间类
    'PT': 'time',           # 保压时间
    'CT': 'time',           # 冷却时间
    'SCT': 'time',          # 阀口开启时间
    # 位置类
    'IL': 'position',       # 注射位置
    'IPOS': 'position',     # 注射位置（辅机）
    'ML': 'position',       # 储料位置
    'CUSION': 'position',   # 残留量
    'HRN': 'position',      # 热流道段数
    # 长度类（注射行程）
    'IDT': 'length',        # 注射行程
    # 重量类
    # （暂无专用前缀，依赖 description 推断）
    # VPT/DMB/DMA 类离散模式（不是物理量，用 position 占位）
    # 长前缀优先匹配，避免被 description 的“时间/压力/速度”关键词截胡
    'VPT': 'position',      # VP 切换相关（VPTL/M/P/T/V）
    'DMB': 'position',      # 储前松退模式 (DMBM)
    'DMA': 'position',      # 储后松退模式 (DMAM)
}

# description 关键词 → 物理量类型 的兜底映射
KEYWORD_TYPE_BY_DESC = {
    '温度': 'temperature',
    '压力': 'pressure',
    '背压': 'pressure',
    '速度': 'speed',
    '转速': 'speed',
    '时间': 'time',
    '冷却': 'time',
    '位置': 'position',
    '锁模力': 'force',
    '力': 'force',
    '行程': 'length',
    '长度': 'length',
    '残留量': 'position',
    '重量': 'weight',
    '段数': 'position',
}

# ============================================================================
# 物理量类型 → 标准单位 的映射
# ============================================================================
KEYWORD_TYPE_TO_UNIT = {
    'pressure': 'MPa',
    'speed': 'mm/s',         # 默认 mm/s，MSR 类关键词在脚本里特殊处理为 rpm
    'temperature': '℃',
    'position': 'mm',
    'time': 's',
    'force': 'kN',
    'length': 'mm',
    'weight': 'g',
}

# 特殊关键词的单位覆盖（某些速度类用 rpm 而非 mm/s）
KEYWORD_UNIT_OVERRIDE = {
    'MSR': 'rpm',    # 螺杆转速（metering screw rotation）
}

# ============================================================================
# 不导入的关键词清单（19 条）
# ============================================================================
EXCLUDED_KEYWORDS = set([
    # fuzzy 引擎 one-hot 预处理中间变量
    'HOLDEXIST', 'VALVEEXIST',
])
# injectstage/holdingstage/meteringstage 用前缀匹配排除
EXCLUDED_PREFIXES = (
    'injectstage',
    'holdingstage',
    'meteringstage',
)


def infer_keyword_type(keyword_name: str, description: str, category: str) -> str:
    """
    推断 keyword 的物理量类型

    优先级：
      1. 关键词名前缀匹配（KEYWORD_TYPE_BY_PREFIX，长前缀优先）
      2. description 关键词匹配（KEYWORD_TYPE_BY_DESC）
      3. category 是 defect/defect_position → 'position' 占位
      4. VPT/DMB/DMA 类离散模式 → 'position' 占位（模式本身不是物理量）
      5. 都匹配不到 → 'position' 兜底
    """
    # 1. 前缀匹配（**长前缀优先**：按 prefix 长度倒序，避免 IPOS 被 IP 截胡）
    upper = keyword_name.upper()
    sorted_prefixes = sorted(KEYWORD_TYPE_BY_PREFIX.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if upper.startswith(prefix):
            return KEYWORD_TYPE_BY_PREFIX[prefix]

    # 2. description 匹配（最长的关键词优先，避免"时间"被"温度时间"截胡）
    desc = description or ''
    for kw in sorted(KEYWORD_TYPE_BY_DESC.keys(), key=len, reverse=True):
        if kw in desc:
            return KEYWORD_TYPE_BY_DESC[kw]

    # 3. 缺陷类用 position 占位
    if category in ('defect', 'defect_position'):
        return 'position'

    # 4. VPT/DMB/DMA 类离散模式不是物理量，用 position 占位
    name_lower = keyword_name.lower()
    if any(name_lower.startswith(p) for p in ('vpt', 'dmbm', 'dmam', 'dm')):
        return 'position'

    # 5. 兜底
    return 'position'


def infer_unit(keyword_name: str, keyword_type: str) -> str:
    """
    推断 keyword 的标准单位

    优先级：
      1. KEYWORD_UNIT_OVERRIDE（特殊关键词，如 MSR → rpm）
      2. KEYWORD_TYPE_TO_UNIT（按物理量默认单位）
      3. 缺陷类 → 空字符串
    """
    upper = keyword_name.upper()
    for prefix, unit in KEYWORD_UNIT_OVERRIDE.items():
        if upper.startswith(prefix):
            return unit
    return KEYWORD_TYPE_TO_UNIT.get(keyword_type, '')


def should_exclude(keyword_name: str) -> bool:
    """判断是否在排除清单内"""
    if keyword_name in EXCLUDED_KEYWORDS:
        return True
    name_lower = keyword_name.lower()
    for prefix in EXCLUDED_PREFIXES:
        if name_lower.startswith(prefix):
            return True
    return False


class Command(BaseCommand):
    help = '从 process/refs/rule_keyword_curated.json 导入 RuleKeyword 主数据'

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
            help='覆盖已存在的关键词',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        json_path = Path(options['json'])
        dry_run = options['dry_run']
        force_update = options['force']

        self.stdout.write(self.style.NOTICE('=== 导入 RuleKeyword 主数据 ===\n'))

        # 校验 JSON 文件
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f'JSON 文件不存在: {json_path}'))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'JSON 解析失败: {e}'))
            return

        self.stdout.write(f'JSON 文件: {json_path}')
        self.stdout.write(f'读取到 {len(data)} 条原始数据')

        # 系统库归属到 system_demo 公司
        system_company = Company.objects.filter(code=SYSTEM_DEMO_COMPANY_CODE).first()
        if not system_company:
            self.stdout.write(self.style.ERROR(
                f'系统演示公司（code={SYSTEM_DEMO_COMPANY_CODE}）不存在，请先执行 init_platform'
            ))
            return

        # 步骤 1：按 keyword_name 去重（保留首条）
        seen = set()
        deduped = []
        for record in data:
            name = record.get('keyword_name', '').strip()
            if not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            deduped.append(record)
        self.stdout.write(f'去重后: {len(deduped)} 条')

        # 步骤 2：过滤排除清单
        filtered = [r for r in deduped if not should_exclude(r['keyword_name'])]
        excluded_count = len(deduped) - len(filtered)
        self.stdout.write(f'排除不导入: {excluded_count} 条')
        self.stdout.write(f'待导入: {len(filtered)} 条\n')

        # 步骤 3：入库
        imported = 0
        updated = 0
        skipped = 0
        errors = []

        for record in filtered:
            name = record['keyword_name']
            json_type = record.get('keyword_type', '').strip()
            description = record.get('description', '').strip()

            # 字段映射
            category = JSON_CATEGORY_MAP.get(json_type)
            if not category:
                errors.append(f'{name}: 无法映射 keyword_type={json_type!r}')
                continue

            keyword_type = infer_keyword_type(name, description, category)
            unit = infer_unit(name, keyword_type)
            alias = description[:100]  # alias 字段 max_length=100

            try:
                kw = RuleKeyword.objects.filter(
                    keyword_name=name,
                    company_id=system_company.id,
                    is_deleted=False,
                ).first()

                if kw:
                    if not force_update:
                        skipped += 1
                        continue
                    # 更新模式
                    kw.keyword_alias = alias
                    kw.category = category
                    kw.parameter_kind = 'setpoint'
                    kw.range_min = record.get('range_min', 0)
                    kw.range_max = record.get('range_max', 0)
                    kw.action_range_min = record.get('action_range_min')
                    kw.action_range_max = record.get('action_range_max')
                    kw.action_max_val = record.get('action_max_val')
                    kw.fuzzy_level = record.get('fuzzy_level', 3)
                    kw.keyword_type = keyword_type
                    kw.unit = unit
                    kw.description = description
                    if not dry_run:
                        kw.save()
                    updated += 1
                    self.stdout.write(f'  更新: {name} ({keyword_type}/{unit})')
                else:
                    # 新建
                    if not dry_run:
                        RuleKeyword.objects.create(
                            company_id=system_company.id,
                            keyword_name=name,
                            keyword_alias=alias,
                            category=category,
                            parameter_kind='setpoint',
                            range_min=record.get('range_min', 0),
                            range_max=record.get('range_max', 0),
                            action_range_min=record.get('action_range_min'),
                            action_range_max=record.get('action_range_max'),
                            action_max_val=record.get('action_max_val'),
                            fuzzy_level=record.get('fuzzy_level', 3),
                            keyword_type=keyword_type,
                            unit=unit,
                            description=description,
                        )
                    imported += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  新增: {name} ({category}/{keyword_type}/{unit})'
                    ))

            except Exception as e:
                errors.append(f'{name}: {e}')

        # 步骤 4：确保特殊 keyword DEFECTFREE（无缺陷）存在
        # 业务场景：产品本轮试模没有明显缺陷，但工艺仍可优化
        #   （如减少周期时间、提高产能、降低能耗等）。
        # 字段语义：
        #   - keyword_name='DEFECTFREE'：前哨标记，DefectFeedback 选中后隐藏 level/position
        #   - category='defect'：保持与其他缺陷同一类，走统一的 if-then 规则路径
        #   - parameter_kind='enum'：缺陷类不需要区分设定/实际
        # 排序：前端按 keyword_name='DEFECTFREE' 识别后排到第一，后端不需特殊排序。
        # 命名选择：DEFECTFREE 而非 NONE（None 容易产生"无关键字"的歧义）。
        defect_free_name = 'DEFECTFREE'
        defect_free_existing = RuleKeyword.objects.filter(
            keyword_name=defect_free_name,
            company_id=system_company.id,
            is_deleted=False,
        ).first()
        if defect_free_existing:
            self.stdout.write(f'  特殊 keyword 已存在: {defect_free_name} (id={defect_free_existing.id})')
        elif dry_run:
            self.stdout.write(self.style.WARNING(
                f'  [DRY-RUN] 待新增特殊 keyword: {defect_free_name} (无缺陷)'
            ))
        else:
            RuleKeyword.objects.create(
                company_id=system_company.id,
                keyword_name=defect_free_name,
                keyword_alias='无缺陷',
                category='defect',
                parameter_kind='enum',
                range_min=0,
                range_max=1,
                action_range_min=None,
                action_range_max=None,
                action_max_val=None,
                fuzzy_level=3,
                keyword_type='position',  # 缺陷类兑底用 position 占位
                unit='',
                description='无缺陷（产品本轮试模无缺陷，工艺仍可优化：减少周期时间、提产能、降能耗等）',
            )
            self.stdout.write(self.style.SUCCESS(
                f'  新增特殊 keyword: {defect_free_name} (无缺陷)'
            ))

        # 输出统计
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== 导入完成 ==='))
        self.stdout.write(f'  新增: {imported} 条')
        self.stdout.write(f'  更新: {updated} 条')
        self.stdout.write(f'  跳过: {skipped} 条')
        self.stdout.write(f'  错误: {len(errors)} 条')

        if errors:
            self.stdout.write(self.style.WARNING('\n=== 错误详情 ==='))
            for err in errors[:20]:
                self.stdout.write(f'  {err}')

        # 验证
        if not dry_run:
            self.stdout.write('\n=== 验证入库结果 ===')
            total = RuleKeyword.objects.filter(
                company_id=system_company.id,
                is_deleted=False,
            ).count()
            self.stdout.write(f'RuleKeyword 总数: {total}')
            # 按 category 统计
            from django.db.models import Count
            by_category = RuleKeyword.objects.filter(
                company_id=system_company.id,
                is_deleted=False,
            ).values('category').annotate(count=Count('id'))
            for item in by_category:
                self.stdout.write(f"  {item['category']}: {item['count']} 条")
        else:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN 模式，未写库]'))