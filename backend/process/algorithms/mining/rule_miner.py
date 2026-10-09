"""
规则挖掘算法 - 从历史工艺数据中学习关联规则

重要：本算法属于 mining 类型，不进入工艺参数优化 chain。
- algorithm_type = "mining"（不是 "optimization"）
- 不注册到 AlgorithmRegistry（mining 类型由未来独立 service 直调）
- 优化 chain 调用 get_algorithms_by_type('optimization') 会自动排除本算法

使用场景：
- 从成功调参案例中提取关联规则（FP-Growth / Apriori）
- 生成新的 RuleMethod / RuleKeyword 写入数据库
- 生成的规则后续被 FuzzyEngine 查询使用
"""
from typing import List

from process.algorithms.base import AlgorithmBase


class RuleMinerEngine(AlgorithmBase):
    """
    规则挖掘算法 - 从历史数据中学习规则

    algorithm_type='mining'，未来由独立 mining_service 编排。
    使用 FP-Growth 或 Apriori 算法从成功案例中提取关联规则。
    本算法为占位实现，未来会接入独立的异步任务。
    """

    algorithm_name = "规则挖掘"
    algorithm_type = "mining"   # 明确为 mining，不进优化 chain
    algorithm_subtype = "rule_miner"

    def __init__(self, min_confidence: float = 0.7, min_support: float = 0.05):
        self.min_confidence = min_confidence
        self.min_support = min_support

    def is_available(self, context: dict) -> bool:
        """
        判断是否可用

        需要至少 10 条历史记录
        """
        return len(context.get('tuning_history', [])) >= 10

    def run(self, context: dict) -> List[dict]:
        """统一入口：占位实现。

        algorithm_type='mining'，返回 List[Rule]（占位返回 []）。
        """
        # TODO: 未来实现规则挖掘推理
        return []

    def mine_rules(self, cases: List[dict]) -> List[dict]:
        """
        从案例中挖掘规则

        Args:
            cases: 成功案例列表

        Returns:
            挖掘出的规则列表
        """
        # TODO: 后续实现 FP-Growth 或 Apriori 算法
        return []

    def evaluate_rule(self, rule: dict, cases: List[dict]) -> dict:
        """
        评估规则质量

        Args:
            rule: 规则
            cases: 案例

        Returns:
            评估结果 (confidence, support, lift)
        """
        # TODO: 后续实现
        return {
            'confidence': 0.0,
            'support': 0.0,
            'lift': 0.0,
        }


# 注意：本算法 algorithm_type='mining'，**不注册**到 AlgorithmRegistry。
# mining 类型由未来独立的 service 直接 import 使用。
