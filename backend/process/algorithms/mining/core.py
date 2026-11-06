"""挖掘内核 —— Apriori 关联规则挖掘（**纯函数**，零 ORM、零 Django 依赖）。

与 `rule_miner.py`（引擎外壳）的分工：
- 本模块只做「样本 → 事务 → 频繁项集 → 规则」，输入输出都是契约对象，
  不碰 Django、不碰数据库 ⇒ 可离线单测、可被任何来源（文件 / DB）复用。
- `rule_miner.py` 只负责把引擎入口接到本模块。

⚠️ **样本 → 事务的规约**
   一条样本（一次调机轮次）规约成**一个事务**（一个 item 集合）：
   - 每个缺陷 → item `D:SHORTSHOT`
   - 每个变更 → item `C:inj_pres_1:increase`
   - 标签     → item `L:qualified`

   挖的是「缺陷 + 变更 ⇒ 标签」的关联规则：前件 = 缺陷与变更的组合，
   后件 = 试模结果（合格 / 不合格）。

⚠️ **为什么限制每个样本的变更数（`max_changes_per_sample`）**
   一轮调机若改了十几个参数，事务的 item 基数就上去了；而项集基数决定
   候选集规模（Apriori 候选数随项集基数组合爆炸）⇒ 单事务只保留
   **幅度最大**的 N 个变更：幅度大的变更才是本轮真正起作用的动作。
"""

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from .contracts import SampleRecord, defect_level, defect_name, normalize_defect


# --- item 编码 --------------------------------------------------------

ITEM_DEFECT_PREFIX = 'D:'   # 缺陷：SHORTSHOT
ITEM_CHANGE_PREFIX = 'C:'   # 变更：inj_pres_1:increase
ITEM_LABEL_PREFIX = 'L:'    # 标签：qualified


def encode_sample(sample: SampleRecord) -> FrozenSet[str]:
    """把一条样本规约成一个事务（item 集合）。"""
    items: Set[str] = set()
    for defect in sample.defects:
        name = defect_name(defect)
        if name:
            items.add(f'{ITEM_DEFECT_PREFIX}{name}')
    for change in sample.changes:
        param = change.get('param')
        direction = change.get('direction')
        if param and direction:
            items.add(f'{ITEM_CHANGE_PREFIX}{param}:{direction}')
    items.add(f'{ITEM_LABEL_PREFIX}{sample.label}')
    return frozenset(items)


def decode_item(item: str) -> Tuple[str, object]:
    """item 编码 → (种类, 载荷)。"""
    kind, _, payload = item.partition(':')
    if kind == 'D':
        return 'defect', payload
    if kind == 'L':
        return 'label', payload
    if kind == 'C':
        param, _, direction = payload.partition(':')
        return 'change', {'param': param, 'direction': direction}
    return 'unknown', payload


# --- 挖掘产物 --------------------------------------------------------

@dataclass
class MinedRule:
    """挖掘出的关联规则（**来源无关**，可直接转成候选规则表 / RuleMethod）。

    Attributes
    ----------
    defects : List[Dict]
        前件里的缺陷，元素形如 ``{'name': 'SHORTSHOT', 'level': 'medium'}``。
    changes : List[Dict]
        前件里的参数变更，元素形如
        ``{'param': 'inj_pres_1', 'direction': 'increase'}``。
    consequent : str
        后件标签（``qualified`` / ``unqualified`` / ``improved`` / ``worse``）。
    support : float
        支持度 = 同时含前件与后件的事务占比（分母是**全部**可用样本数）。
    confidence : float
        置信度 = support(前件∪后件) / support(前件)。
    lift : float
        提升度 = confidence / support(后件)。> 1 表示正相关。
    evidence : List[str]
        证据样本 id 列表（可回溯到业务流水）。
    context : Dict
        附加上下文（取自证据样本；证据不一致时为空）。
    """

    defects: List[Dict] = field(default_factory=list)
    changes: List[Dict] = field(default_factory=list)
    consequent: str = ''
    support: float = 0.0
    confidence: float = 0.0
    lift: float = 0.0
    evidence: List[str] = field(default_factory=list)
    context: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转成可 JSON 序列化的 dict（落库 / 导出用）。"""
        return {
            'defects': [normalize_defect(d) for d in self.defects],
            'changes': list(self.changes),
            'consequent': self.consequent,
            'support': self.support,
            'confidence': self.confidence,
            'lift': self.lift,
            'evidence': list(self.evidence),
            'context': dict(self.context),
        }


# --- Apriori ---------------------------------------------------------

def rule_fingerprint(rule: MinedRule) -> str:
    """规则的自然键指纹（sha1）—— 前件 + 后件的规范化摘要。

    同一规则无论被挖出多少次、指标怎么变，指纹恒定 ⇒ 可作候选规则表的
    唯一键（重复挖掘只更新不新增，不会堆出重复行）。

    Args:
        rule: 挖掘出的规则。

    Returns:
        40 位十六进制 sha1 摘要。
    """
    payload = {
        'defects': sorted(defect_name(d) for d in rule.defects),
        'changes': sorted(
            (change.get('param') or '', change.get('direction') or '')
            for change in rule.changes
        ),
        'consequent': rule.consequent,
    }
    raw = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
    )
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()

def _count_support(itemset: FrozenSet[str], transactions: Sequence[FrozenSet[str]]) -> int:
    """项集支持度计数（含该 itemset 的事务数）。"""
    return sum(1 for t in transactions if itemset <= t)


def _generate_candidates(itemsets: Set[FrozenSet[str]], k: int) -> Set[FrozenSet[str]]:
    """从 k-频繁项集生成 (k+1)-候选。

    Apriori 连接：按 **k-1 前缀**分组后两两合并。
    - 前缀唯一 ⇒ 不会产生重复候选
    - Lk 的每个项集其 k-1 子集都频繁 ⇒ 候选必含频繁子集（该性质由
      Lk 的构造保证，不需要额外剪枝）
    """
    prefix_groups: Dict[Tuple[str, ...], List[Tuple[str, ...]]] = defaultdict(list)
    for fs in itemsets:
        prefix_groups[tuple(sorted(fs)[:k - 1])].append(tuple(sorted(fs)))

    candidates: Set[FrozenSet[str]] = set()
    for tails in prefix_groups.values():
        for i in range(len(tails)):
            for j in range(i + 1, len(tails)):
                merged = frozenset(tails[i]) | frozenset(tails[j])
                if len(merged) == k + 1:
                    candidates.add(merged)
    return candidates


def _find_frequent_itemsets(
    transactions: Sequence[FrozenSet[str]],
    min_support: float,
    max_len: int,
) -> Dict[FrozenSet[str], int]:
    """Apriori 频繁项集挖掘。

    Returns:
        {项集: 支持度计数}
    """
    total = len(transactions)
    if total == 0:
        return {}

    threshold = min_support * total

    item_counts: Counter = Counter()
    for t in transactions:
        for item in t:
            item_counts[item] += 1

    # ⚠️ 计数容器必须以 **frozenset** 为键：
    #   后续层级的候选是 frozenset，若 L1 仍以 str 为键，
    #   `counts[frozenset([item])]` 会查不到 ⇒ L1 支持度恒为 0
    #   ⇒ 规则生成阶段取前件/后件支持度时全部为 0 ⇒ 一条规则都产不出。
    counts: Dict[FrozenSet[str], int] = {
        frozenset([item]): cnt for item, cnt in item_counts.items()
    }

    current = {fs for fs, cnt in counts.items() if cnt >= threshold}
    frequent: Dict[FrozenSet[str], int] = {}
    k = 1
    while current:
        for fs in current:
            frequent[fs] = counts[fs]
        if k >= max_len:
            break
        next_level: Set[FrozenSet[str]] = set()
        for cand in _generate_candidates(current, k):
            cnt = _count_support(cand, transactions)
            if cnt >= threshold:
                next_level.add(cand)
                counts[cand] = cnt
        current = next_level
        k += 1
    return frequent


def _select_changes(
    sample: SampleRecord,
    max_changes: int,
) -> List[Dict]:
    """挑选本样本参与挖掘的变更：幅度最大的 N 个。

    `adjustments.changes[].before/after` 给出变更幅度；没有幅度的变更
    按原序补足（不因数据不全而丢样本）。
    """
    if max_changes <= 0 or len(sample.changes) <= max_changes:
        return list(sample.changes)

    def magnitude(change: Dict) -> float:
        before = change.get('before')
        after = change.get('after')
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            return abs(after - before)
        return 0.0

    ranked = sorted(sample.changes, key=magnitude, reverse=True)
    return ranked[:max_changes]


def _aggregate_change_values(
    changes: List[Dict],
    evidence: List[str],
    tx_samples: List[Tuple[str, SampleRecord, FrozenSet[str]]],
) -> List[Dict]:
    """从证据样本聚合前件变更的 before / after 均值。

    统计维度只用 ``param`` + ``direction``（见 `rule_fingerprint`），
    但**落地**成 RuleMethod 时需要两个额外的量：
    - ``before``：变更前的参数值 ⇒ 用参数量程算出它处于哪个档位（IF 条件）
    - ``after - before``：调整幅度 ⇒ THEN 的动作量（如 ``IP0_add_10``）

    同一条规则的不同证据样本幅度可能不同 ⇒ 取**均值**；
    取不到数值（样本缺 before/after）时保留原项、只留 param + direction。
    """
    if not changes:
        return []

    evidence_set = set(evidence)
    buckets: Dict[Tuple[str, str], Dict[str, List[float]]] = defaultdict(
        lambda: {'before': [], 'after': []},
    )
    for sample_id, trimmed, _ in tx_samples:
        if sample_id not in evidence_set:
            continue
        for change in trimmed.changes:
            param = change.get('param')
            direction = change.get('direction')
            if not param or not direction:
                continue
            bucket = buckets[(param, direction)]
            for key in ('before', 'after'):
                value = change.get(key)
                if isinstance(value, (int, float)):
                    bucket[key].append(float(value))

    aggregated: List[Dict] = []
    for change in changes:
        param = change.get('param')
        direction = change.get('direction')
        bucket = buckets.get((param, direction))
        item: Dict = {'param': param, 'direction': direction}
        if bucket:
            if bucket['before']:
                item['before'] = sum(bucket['before']) / len(bucket['before'])
            if bucket['after']:
                item['after'] = sum(bucket['after']) / len(bucket['after'])
        aggregated.append(item)
    return aggregated


def _aggregate_defects(
    defects: List[Dict],
    evidence: List[str],
    tx_samples: List[Tuple[str, SampleRecord, FrozenSet[str]]],
) -> List[Dict]:
    """给前件缺陷补上严重等级（证据众数）。

    等级**不参与**指标计算，只作为落地时的条件词来源
    （``SHORTSHOT`` + ``medium`` ⇒ ``SHORTSHOT_medium``）。

    ⚠️ **证据样本里没有该缺陷的等级时，保留缺陷名、等级留空**（宁缺勿造）——
      缺陷名是**统计维度**（参与指纹与项集），不能因为缺等级就丢掉；
      落地时该缺陷因「等级未知」被剔除条件（见 `mining_landing`）。
    """
    if not defects:
        return []

    levels: Dict[str, Counter] = defaultdict(Counter)
    evidence_set = set(evidence)
    for sample_id, trimmed, _ in tx_samples:
        if sample_id not in evidence_set:
            continue
        for item in trimmed.defects:
            name = defect_name(item)
            level = defect_level(item)
            if name and level:
                levels[name][level] += 1

    result: List[Dict] = []
    for item in defects:
        name = defect_name(item)
        if not name:
            continue
        level = ''
        counter = levels.get(name)
        if counter:
            # 众数；平局时取字典序最小者（保证同一规则的展示稳定）
            level = sorted(
                counter.items(), key=lambda kv: (-kv[1], kv[0]),
            )[0][0]
        result.append({'name': name, 'level': level})
    return result


def mine_association_rules(
    samples: Sequence[SampleRecord],
    min_support: float = 0.05,
    min_confidence: float = 0.7,
    min_lift: float = 1.0,
    max_len: int = 4,
    max_changes_per_sample: int = 3,
    target_label: Optional[str] = None,
) -> List[MinedRule]:
    """从样本中挖掘关联规则。

    Args:
        samples: 训练样本（来源无关，见 ``contracts.SampleRecord``）。
        min_support: 最小支持度（项集占比）。
        min_confidence: 最小置信度（前件成立时后件发生的概率）。
        min_lift: 最小提升度（> 1 表示正相关，= 1 表示独立）。
        max_len: 频繁项集最大长度（**含标签项**）。4 = 前件最多 3 个 item
            （如 2 个缺陷 + 1 个变更）。
        max_changes_per_sample: 单个样本最多保留几个变更（幅度最大的）。
        target_label: 只挖指向该标签的规则；**None = 挖所有标签方向**
            （默认）。⚠️ 不能只挖 ``qualified`` —— 调机是逐步逼近的过程，
            ``improved``（相对上一轮改善）是最常见也最有指导价值的信号，
            只挖合格会漏掉绝大部分可用经验。

    Returns:
        规则列表，按 (confidence 降序, support 降序) 排序。
    """
    usable = [s for s in samples if s.is_usable()]
    if not usable:
        return []

    # 规约事务：变更多的样本只保留幅度最大的 N 个
    transactions: List[FrozenSet[str]] = []
    tx_samples: List[Tuple[str, SampleRecord, FrozenSet[str]]] = []
    for sample in usable:
        trimmed = SampleRecord(
            sample_id=sample.sample_id,
            defects=[normalize_defect(d) for d in sample.defects],
            changes=_select_changes(sample, max_changes_per_sample),
            label=sample.label,
            context=dict(sample.context),
            source_ref=sample.source_ref,
        )
        tx = encode_sample(trimmed)
        transactions.append(tx)
        tx_samples.append((sample.sample_id, trimmed, tx))

    total = len(transactions)
    frequent = _find_frequent_itemsets(transactions, min_support, max_len)
    if not frequent:
        return []

    target_items = (
        {f'{ITEM_LABEL_PREFIX}{target_label}'} if target_label else None
    )

    rules: List[MinedRule] = []
    for fs, count in frequent.items():
        if len(fs) < 2:
            continue
        label_items = {i for i in fs if i.startswith(ITEM_LABEL_PREFIX)}
        if target_items is not None:
            label_items &= target_items
        if not label_items:
            continue

        for label_item in label_items:
            antecedent = fs - {label_item}
            if not antecedent:
                continue
            antecedent_support = frequent.get(antecedent)
            if not antecedent_support:
                continue

            confidence = count / antecedent_support
            if confidence < min_confidence:
                continue

            label_support = frequent.get(frozenset([label_item]), 0)
            if not label_support:
                continue
            lift = confidence / (label_support / total)
            if lift < min_lift:
                continue

            defects: List[Dict] = []
            changes: List[Dict] = []
            for item in sorted(antecedent):
                kind, payload = decode_item(item)
                if kind == 'defect':
                    defects.append({'name': str(payload), 'level': ''})
                elif kind == 'change':
                    changes.append(dict(payload))

            evidence: List[str] = []
            for sample_id, _, tx in tx_samples:
                if fs <= tx:
                    evidence.append(sample_id)

            # 缺陷等级取自证据样本（众数）：等级不是统计维度，
            # 只用于落地成 RuleMethod 时的条件词
            defects = _aggregate_defects(defects, evidence, tx_samples)
            # 变更幅度取自证据样本（均值）：用于落地时算档位与动作量
            changes = _aggregate_change_values(
                changes, evidence, tx_samples,
            )

            # 上下文取自首个证据样本（证据间上下文不一致时不附加）
            context: Dict = {}
            if evidence:
                for sample_id, trimmed, _ in tx_samples:
                    if sample_id == evidence[0]:
                        context = dict(trimmed.context)
                        break

            rules.append(MinedRule(
                defects=defects,
                changes=changes,
                consequent=decode_item(label_item)[1],
                support=count / total,
                confidence=confidence,
                lift=lift,
                evidence=evidence,
                context=context,
            ))

    rules.sort(key=lambda r: (-r.confidence, -r.support))
    return rules


__all__ = [
    'MinedRule',
    'mine_association_rules',
    'encode_sample',
    'decode_item',
    'rule_fingerprint',
    'ITEM_DEFECT_PREFIX',
    'ITEM_CHANGE_PREFIX',
    'ITEM_LABEL_PREFIX',
]
