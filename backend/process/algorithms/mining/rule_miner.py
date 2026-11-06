"""规则挖掘引擎 —— 从历史工艺数据中学习关联规则。

重要：本算法属于 mining 类型，不进入工艺参数优化 chain。
- algorithm_type = "mining"（不是 "optimization"）
- 不注册到 AlgorithmRegistry（mining 类型由独立 service 直调）
- 优化 chain 调用 get_algorithms_by_type('optimization') 会自动排除本算法

模块分层（每层职责单一）：
- 【0 契约】contracts: SampleRecord（来源无关样本档案）+ MiningSampleRepository 协议
- 【1 内核】core: Apriori 频繁项集挖掘（**纯函数**，零 ORM，可离线跑）
- 【2 来源】samples: 文件来源的样本仓库（JSONL 语料，append-only）
- 【3 外壳】本文件: RuleMinerEngine —— 只做「上下文 → 内核调用 → 结果」

使用场景：
- 从调机案例中提取关联规则（缺陷 + 参数变更 ⇒ 试模结果）
- 产出的候选规则经人工审核后写入 RuleMethod（source='rule_miner'）
- 生效规则后续被 FuzzyEngine 查询使用
"""

from typing import Dict, List, Optional, Sequence

from process.algorithms.base import AlgorithmBase

from .contracts import MiningSampleRepository, SampleRecord, defect_name
from .core import MinedRule, encode_sample, mine_association_rules


#: 挖掘所需的最少样本数（低于此数不产出规则 —— 样本太少时置信度不可信）
DEFAULT_MIN_SAMPLES = 10


class RuleMinerEngine(AlgorithmBase):
    """规则挖掘引擎 —— 从调机案例中学习「缺陷 + 变更 ⇒ 结果」的关联规则。

    algorithm_type='mining'，由独立 mining_service 编排。
    """

    algorithm_name = "规则挖掘"
    algorithm_type = "mining"   # 明确为 mining，不进优化 chain
    algorithm_subtype = "rule_miner"

    def __init__(
        self,
        min_confidence: float = 0.7,
        min_support: float = 0.05,
        min_lift: float = 1.0,
        max_len: int = 4,
        max_changes_per_sample: int = 3,
        min_samples: int = DEFAULT_MIN_SAMPLES,
    ):
        """
        Args:
            min_confidence: 最小置信度。
            min_support: 最小支持度。
            min_lift: 最小提升度（> 1 表示正相关）。
            max_len: 频繁项集最大长度（含标签项）。
            max_changes_per_sample: 单样本最多保留几个变更（幅度最大的）。
            min_samples: 低于此样本数不产出规则。
        """
        self.min_confidence = min_confidence
        self.min_support = min_support
        self.min_lift = min_lift
        self.max_len = max_len
        self.max_changes_per_sample = max_changes_per_sample
        self.min_samples = min_samples

    # --- 统一入口 ---

    def is_available(self, context: dict) -> bool:
        """判断是否可用：可用样本数达到阈值。

        「可用样本」= 有标签 + 有缺陷 + 有变更（见 `SampleRecord.is_usable`）。
        """
        return len(self._collect_samples(context)) >= self.min_samples

    def run(self, context: dict) -> List[MinedRule]:
        """统一入口。

        Args:
            context: mining 上下文字典，支持两种形态：
                - ``{'samples': [SampleRecord, ...]}`` —— 直接给样本
                - ``{'repository': MiningSampleRepository, 'since': str}``
                  —— 从仓库取（增量挖掘时传 `since` 游标）

        Returns:
            挖出的规则列表（按 confidence 降序）。
        """
        samples = self._collect_samples(context)
        if len(samples) < self.min_samples:
            return []
        return self.mine_rules(samples)

    # --- 领域方法 ---

    def mine_rules(self, samples: Sequence[SampleRecord]) -> List[MinedRule]:
        """从样本中挖掘关联规则（转发到纯函数内核）。

        Args:
            samples: 训练样本。

        Returns:
            规则列表。
        """
        return mine_association_rules(
            samples,
            min_support=self.min_support,
            min_confidence=self.min_confidence,
            min_lift=self.min_lift,
            max_len=self.max_len,
            max_changes_per_sample=self.max_changes_per_sample,
        )

    def evaluate_rule(self, rule: MinedRule, samples: Sequence[SampleRecord]) -> Dict:
        """评估规则质量（基于全量样本重新计算支持度 / 置信度 / 提升度）。

        与挖掘时的口径一致，但用**全量样本**为分母 ⇒ 可用于复核一条
        已入库规则在最新语料上的表现。

        Args:
            rule: 待评估的规则。
            samples: 全量样本。

        Returns:
            ``{'support': ..., 'confidence': ..., 'lift': ..., 'evidence': [...]}``
        """
        total = len(samples)
        if total == 0:
            return {'support': 0.0, 'confidence': 0.0, 'lift': 0.0, 'evidence': []}

        antecedent_items = set()
        for defect in rule.defects:
            name = defect_name(defect)
            if name:
                antecedent_items.add(f'D:{name}')
        for change in rule.changes:
            antecedent_items.add(
                f"C:{change.get('param')}:{change.get('direction')}"
            )
        consequent_item = f'L:{rule.consequent}'

        antecedent_support = 0
        joint_support = 0
        consequent_support = 0
        evidence: List[str] = []
        for sample in samples:
            tx = encode_sample(sample)
            has_ant = antecedent_items.issubset(tx)
            has_con = consequent_item in tx
            if has_ant:
                antecedent_support += 1
                evidence.append(sample.sample_id)
            if has_con:
                consequent_support += 1
            if has_ant and has_con:
                joint_support += 1

        support = joint_support / total
        confidence = (joint_support / antecedent_support) if antecedent_support else 0.0
        base = (consequent_support / total) if consequent_support else 0.0
        lift = (confidence / base) if base else 0.0
        return {
            'support': support,
            'confidence': confidence,
            'lift': lift,
            'evidence': evidence,
        }

    # --- 内部 ---

    def _collect_samples(self, context: dict) -> List[SampleRecord]:
        """从上下文收集样本（两种形态统一到这里）。"""
        samples = context.get('samples')
        if samples is not None:
            return list(samples)

        repository: Optional[MiningSampleRepository] = context.get('repository')
        if repository is not None:
            return list(repository.get_samples(context.get('since')))
        return []


# 注意：本算法 algorithm_type='mining'，**不注册**到 AlgorithmRegistry。
# mining 类型由未来独立的 service 直接 import 使用。
