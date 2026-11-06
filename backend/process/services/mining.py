"""规则挖掘编排 service —— 采集样本 → 挖掘规则 → 候选规则入库。

三层中间态（机器 → 机器 → 人）：

    TuningRecord（业务流水，DB）
        ↓ collect（提炼：调机记录 → 样本）
    MiningSample（样本池，JSONL 文件）    ← 机器对机器，append-only 日志
        ↓ mine（Apriori 关联规则）
    MiningRule（候选规则，DB，待审核）    ← 人机审核

⚠️ **为什么采集与挖掘分两步**
    - 采集是**增量**的：只把「新增的 / 内容变了的」样本追加进语料；
    - 挖掘是**全量**的：每次基于整个语料重算 ⇒ 指标始终反映最新语料。
    分开才能既不重复写语料、又不漏掉「新样本改变了旧规则指标」的情况。

⚠️ **采集为什么不用「已采集最大 id」做游标**
    调机记录的试模结果是**后补**的（`pending` → `qualified`），且
    `adjustments` 会在每次 upsert 时重算 ⇒
    - 一条 id 较小的记录可能晚于游标才定稿 ⇒ 用 id 游标会**永久漏掉**它；
    - 已入语料的样本内容也可能漂移 ⇒ 需要能**修订**。
    所以采集走「全量扫描 + 与语料现状 diff + 只追加差异项」，语料读取时
    同 `sample_id` 取最后一行（见 `samples.FileSampleRepository.get_samples`）。
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.db import transaction
from django.db.models import Max

from process.algorithms.mining.collect import TuningRecordCollector
from process.algorithms.mining.contracts import normalize_defect
from process.algorithms.mining.core import MinedRule, rule_fingerprint
from process.algorithms.mining.provider import resolve_sample_repository
from process.algorithms.mining.rule_miner import RuleMinerEngine
from process.models import MiningRule


_logger = logging.getLogger(__name__)


# ============================================================================
# 采集：调机流水 → 样本池（文件）
# ============================================================================

def collect_samples(
    company_id: int,
    tenant_slug: str,
    corpus_dir: Optional[str] = None,
) -> Dict:
    """从调机流水采集样本并增量追加到语料。

    只追加「新增的」与「内容变了的」样本 ⇒ 重复执行不会产生重复行，
    也不会把未变的样本重复写入。

    Args:
        company_id: 公司 id。
        tenant_slug: 租户标识（`Company.tenant_slug`）。
        corpus_dir: 显式指定语料目录（默认按租户解析）。

    Returns:
        ``{'scanned': n, 'appended': n, 'corpus_size': n, 'corpus_path': str}``
    """
    repository = resolve_sample_repository(
        tenant_slug, company_id=company_id, corpus_dir=corpus_dir,
    )
    existing = {r.sample_id: r for r in repository.get_samples()}
    samples = TuningRecordCollector(company_id=company_id).get_samples()

    changed: List = []
    for sample in samples:
        previous = existing.get(sample.sample_id)
        if previous is None or previous != sample:
            changed.append(sample)

    appended = repository.append_samples(changed)
    _logger.info(
        '[mining/collect] 公司=%s 扫描=%s 新增/修订=%s 语料=%s',
        company_id, len(samples), appended, repository.corpus_path,
    )
    return {
        'scanned': len(samples),
        'appended': appended,
        'corpus_size': len(existing) + appended,
        'corpus_path': repository.corpus_path,
    }


# ============================================================================
# 挖掘：样本池 → 候选规则（DB）
# ============================================================================

def mine_rules(
    company_id: int,
    tenant_slug: str,
    min_support: float = 0.05,
    min_confidence: float = 0.7,
    min_lift: float = 1.0,
    max_len: int = 4,
    max_changes_per_sample: int = 3,
    min_samples: int = 10,
    corpus_dir: Optional[str] = None,
    persist: bool = True,
) -> Dict:
    """基于语料挖掘关联规则，并落库为**候选规则**（待审核）。

    Args:
        company_id: 公司 id。
        tenant_slug: 租户标识。
        min_support: 最小支持度。
        min_confidence: 最小置信度。
        min_lift: 最小提升度。
        max_len: 频繁项集最大长度（含标签项）。
        max_changes_per_sample: 单样本最多保留几个变更。
        min_samples: 低于此样本数不产出规则。
        corpus_dir: 显式指定语料目录。
        persist: 是否落库（False = 只算不存，用于试跑）。

    Returns:
        ``{'samples': n, 'rules': n, 'created': n, 'updated': n, 'rules_detail': [...]}``
    """
    repository = resolve_sample_repository(
        tenant_slug, company_id=company_id, corpus_dir=corpus_dir,
    )
    samples = repository.get_samples()
    cursor = samples[-1].sample_id if samples else ''

    engine = RuleMinerEngine(
        min_confidence=min_confidence,
        min_support=min_support,
        min_lift=min_lift,
        max_len=max_len,
        max_changes_per_sample=max_changes_per_sample,
        min_samples=min_samples,
    )
    rules = engine.run({'samples': samples})

    created = updated = 0
    if persist and rules:
        created, updated = _persist_rules(company_id, rules, cursor)

    _logger.info(
        '[mining/mine] 公司=%s 样本=%s 规则=%s 新增=%s 更新=%s',
        company_id, len(samples), len(rules), created, updated,
    )
    return {
        'samples': len(samples),
        'rules': len(rules),
        'created': created,
        'updated': updated,
        'corpus_cursor': cursor,
        'rules_detail': [rule.to_dict() for rule in rules],
    }


def run_mining(
    company_id: int,
    tenant_slug: str,
    corpus_dir: Optional[str] = None,
    **mining_options,
) -> Dict:
    """跑通完整闭环：采集 → 挖掘 → 候选规则入库。

    Args:
        company_id: 公司 id。
        tenant_slug: 租户标识。
        corpus_dir: 显式指定语料目录。
        **mining_options: 透传给 `mine_rules` 的挖掘参数。

    Returns:
        ``{'collect': {...}, 'mine': {...}}``
    """
    collected = collect_samples(
        company_id=company_id,
        tenant_slug=tenant_slug,
        corpus_dir=corpus_dir,
    )
    mined = mine_rules(
        company_id=company_id,
        tenant_slug=tenant_slug,
        corpus_dir=corpus_dir,
        **mining_options,
    )
    return {'collect': collected, 'mine': mined}


# ============================================================================
# 定时调度：攒够最小样本数再挖
# ============================================================================
#
# ⚠️ **为什么是「定时」而不是「定稿即挖」**
#   挖掘是 Apriori **全量重算**（每次基于整个语料重算指标）—— 放在定稿请求
#   里会拖慢响应，更会让业务请求承担挖掘失败的连带风险。
#   ⇒ 挖掘走独立调度入口（`manage.py mine_rules_scheduled`），由运维侧 cron
#     定时拉起；定稿请求只负责把经验写进调机流水（`TuningRecord`）。
#
# ⚠️ **触发标签口径 = 采集器口径**（`mining/contracts.py::VALID_LABELS`）
#   = qualified / unqualified / improved / worse；
#   `unchanged` 无方向性、`pending` 未定稿，两者都不构成「某个动作带来了
#   某种结果」的证据。
#   ⚠️ 该过滤**已在采集器内**（`TuningRecordCollector.get_samples` 的
#     `result__in=VALID_LABELS`）⇒ 调度层**不重复判断**，避免两处口径漂移。
#
# ⚠️ **触发条件（两条都要满足）**
#   1. 语料可用样本数 ≥ `min_samples` —— 样本不足时 Apriori 挖不出东西，
#      空跑纯属浪费（与挖掘内核用同一个参数，口径一致）。
#   2. 语料最新样本 > 上次挖掘水位 —— 没有新经验进来，指标不会变，
#      重算结果是幂等的，没必要再跑一趟。


def get_mining_watermark(company_id: int) -> str:
    """取上次挖掘覆盖到的语料水位（样本 id）。

    ⚠️ **水位取自候选规则表的 `corpus_cursor` 最大值**：
      `_persist_rules` 把「产出该批规则时的语料游标」写进每条规则的
      `corpus_cursor`，其最大值 = 上次挖掘覆盖到的最新样本。
      样本 id 是零填充的（`tr:000000000070`）⇒ 字符串比较等价于数值比较。

    ⚠️ **产出 0 条规则时水位不前进**（`_persist_rules` 只在有规则时才写库）
      ⇒ 下次调度会再挖一次。代价是一次幂等的 Apriori 全量重算
      （不产生新数据，指标与上次一致）；在「每天几十条」的语料量级下可接受。
      若将来语料量级上来、空跑成为瓶颈，再引入独立的「挖掘运行记录表」。
    """
    row = MiningRule.objects.filter(
        company_id=company_id,
    ).exclude(corpus_cursor='').aggregate(m=Max('corpus_cursor'))
    return row.get('m') or ''


def should_mine(
    company_id: int,
    tenant_slug: str,
    min_samples: int = 10,
    force: bool = False,
    corpus_dir: Optional[str] = None,
) -> Dict:
    """判断该公司当前是否值得挖一次。

    Args:
        company_id: 公司 id。
        tenant_slug: 租户标识。
        min_samples: 触发所需的最小语料样本数。
        force: 忽略全部触发条件，强制挖一次。
        corpus_dir: 显式指定语料目录。

    Returns:
        ``{'should': bool, 'reason': str, 'samples': int, 'cursor': str,
           'watermark': str}``
    """
    repository = resolve_sample_repository(
        tenant_slug, company_id=company_id, corpus_dir=corpus_dir,
    )
    samples = repository.get_samples()
    cursor = samples[-1].sample_id if samples else ''
    watermark = get_mining_watermark(company_id)

    if force:
        return {
            'should': True, 'reason': '强制执行',
            'samples': len(samples), 'cursor': cursor, 'watermark': watermark,
        }

    if len(samples) < min_samples:
        return {
            'should': False,
            'reason': f'样本不足（{len(samples)}/{min_samples}）',
            'samples': len(samples), 'cursor': cursor, 'watermark': watermark,
        }

    if cursor <= watermark:
        return {
            'should': False, 'reason': '无新样本（指标不会变）',
            'samples': len(samples), 'cursor': cursor, 'watermark': watermark,
        }

    return {
        'should': True, 'reason': '有新样本',
        'samples': len(samples), 'cursor': cursor, 'watermark': watermark,
    }


def _scheduled_mining_companies(
    company_ids: Optional[List[int]] = None,
) -> List:
    """待调度的公司列表。

    ⚠️ 默认只取**可访问**的公司（激活且未过期）—— 过期租户的语料不该
      再增长，也不该占用调度时间。
    """
    from identity.models import Company

    if company_ids:
        candidates = list(Company.objects.filter(id__in=company_ids))
    else:
        candidates = list(Company.objects.filter(is_active=True))

    return [c for c in candidates if c.is_accessible()]


def run_scheduled_mining(
    company_ids: Optional[List[int]] = None,
    min_samples: int = 10,
    force: bool = False,
    dry_run: bool = False,
    corpus_dir: Optional[str] = None,
    **mining_options,
) -> Dict:
    """定时调度入口 —— 逐公司「采集 → 判水位 → 挖掘 → 候选规则入库」。

    ⚠️ **每个公司独立 try/except**：一个公司的语料损坏 / 指标异常不得
      中断其余公司的调度（一个租户的数据问题不能拖垮全平台）。

    ⚠️ **采集先于判定**：新定稿的样本只有进了语料，`should_mine` 才看得到
      ⇒ 否则「攒够样本数」的判据永远滞后一轮。

    Args:
        company_ids: 指定公司；None = 全部可访问公司。
        min_samples: 触发所需的最小语料样本数。
        force: 忽略触发条件强制挖一次（首次上线 / 手工补挖）。
        dry_run: 只判定不挖（不写库），返回将要发生什么。
        corpus_dir: 显式指定语料目录。
        **mining_options: 透传给 `mine_rules` 的挖掘参数。

    Returns:
        ``{'companies': n, 'mined': n, 'skipped': n, 'failed': n,
           'details': [...]}``
    """
    companies = _scheduled_mining_companies(company_ids)
    details: List[Dict] = []
    mined = skipped = failed = 0

    for company in companies:
        detail: Dict = {
            'company_id': company.id,
            'company_name': company.name,
            'status': 'skipped',
            'reason': '',
            'collected': 0,
            'samples': 0,
            'rules': 0,
            'created': 0,
            'updated': 0,
        }
        try:
            collected = collect_samples(
                company_id=company.id,
                tenant_slug=company.tenant_slug,
                corpus_dir=corpus_dir,
            )
            detail['collected'] = collected['appended']

            decision = should_mine(
                company_id=company.id,
                tenant_slug=company.tenant_slug,
                min_samples=min_samples,
                force=force,
                corpus_dir=corpus_dir,
            )
            detail['samples'] = decision['samples']
            detail['reason'] = decision['reason']

            if not decision['should']:
                skipped += 1
                details.append(detail)
                continue

            if dry_run:
                detail['status'] = 'dry_run'
                details.append(detail)
                continue

            mined_result = mine_rules(
                company_id=company.id,
                tenant_slug=company.tenant_slug,
                min_samples=min_samples,
                corpus_dir=corpus_dir,
                **mining_options,
            )
            detail['status'] = 'mined'
            detail['rules'] = mined_result['rules']
            detail['created'] = mined_result['created']
            detail['updated'] = mined_result['updated']
            mined += 1

        except Exception as exc:  # noqa: BLE001 —— 单公司失败不影响其余公司
            failed += 1
            detail['status'] = 'failed'
            detail['reason'] = f'{type(exc).__name__}: {exc}'
            _logger.exception(
                '[mining/schedule] 公司=%s 挖掘失败（不影响其余公司）', company.id,
            )
        details.append(detail)

    _logger.info(
        '[mining/schedule] 公司=%s 挖掘=%s 跳过=%s 失败=%s',
        len(companies), mined, skipped, failed,
    )
    return {
        'companies': len(companies),
        'mined': mined,
        'skipped': skipped,
        'failed': failed,
        'details': details,
    }


# ============================================================================
# 内部
# ============================================================================

def _next_rule_code(company_id: int) -> str:
    """生成候选规则编号（`MR-{YYYYMM}-{NNNNN}`，公司内连续）。

    Args:
        company_id: 公司 id。

    Returns:
        规则编号。
    """
    prefix = f'MR-{datetime.now().strftime("%Y%m")}-'
    taken = set(
        MiningRule.objects.filter(
            company_id=company_id, rule_code__startswith=prefix,
        ).values_list('rule_code', flat=True)
    )
    for seq in range(1, 100000):
        code = f'{prefix}{seq:05d}'
        if code not in taken:
            return code
    raise RuntimeError('候选规则编号已耗尽，无法继续生成')


def _persist_rules(
    company_id: int,
    rules: List[MinedRule],
    corpus_cursor: str,
) -> tuple:
    """把挖出的规则落库为候选规则（新增或刷新指标）。

    ⚠️ **审核状态不被重置**：已审核的规则不因指标微调被打回待审，
      避免审核流程被反复打断。

    Args:
        company_id: 公司 id。
        rules: 挖出的规则。
        corpus_cursor: 产出该批规则时的语料游标。

    Returns:
        ``(created, updated)``
    """
    created = 0
    updated = 0
    with transaction.atomic():
        for rule in rules:
            fingerprint = rule_fingerprint(rule)
            # ⚠️ **存完整变更项**（含 before / after 均值）：
            #    统计维度只用 param + direction（指纹不变），但落地成
            #    RuleMethod 时需要 before（算参数档位）与幅度（算动作量）。
            changes = [
                {
                    'param': change.get('param'),
                    'direction': change.get('direction'),
                    'before': change.get('before'),
                    'after': change.get('after'),
                }
                for change in rule.changes
            ]
            obj = MiningRule.objects.filter(
                company_id=company_id, rule_hash=fingerprint,
            ).first()

            if obj is None:
                MiningRule.objects.create(
                    company_id=company_id,
                    rule_code=_next_rule_code(company_id),
                    rule_hash=fingerprint,
                    defects=[normalize_defect(d) for d in rule.defects],
                    changes=changes,
                    consequent=rule.consequent,
                    support=rule.support,
                    confidence=rule.confidence,
                    lift=rule.lift,
                    evidence=list(rule.evidence),
                    sample_count=len(rule.evidence),
                    corpus_cursor=corpus_cursor,
                    status='pending',
                )
                created += 1
                continue

            obj.defects = [normalize_defect(d) for d in rule.defects]
            obj.changes = changes
            obj.consequent = rule.consequent
            obj.support = rule.support
            obj.confidence = rule.confidence
            obj.lift = rule.lift
            obj.evidence = list(rule.evidence)
            obj.sample_count = len(rule.evidence)
            obj.corpus_cursor = corpus_cursor
            obj.save(update_fields=[
                'defects', 'changes', 'consequent',
                'support', 'confidence', 'lift', 'evidence', 'sample_count',
                'corpus_cursor', 'updated_at',
            ])
            updated += 1
    return created, updated