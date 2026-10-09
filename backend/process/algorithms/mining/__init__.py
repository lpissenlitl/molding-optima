"""
规则挖掘算法模块（algorithm_type='mining'）

包含：
- RuleMinerEngine: 规则挖掘算法（FP-Growth / Apriori 占位实现）

algorithm_type='mining'，**不注册**到 AlgorithmRegistry。
未来由独立 mining_service 编排。
"""

from .rule_miner import RuleMinerEngine

__all__ = ["RuleMinerEngine"]
