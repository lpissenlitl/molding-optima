"""
AI 推理类算法基类 + 注册中心

本目录（process/algorithms/）是所有 AI 推理类算法的统一实现库：
- 三个业务场景的算法都物理集中在这里
- algorithm_type 字段区分业务场景
- 调度方式由 service 层决定（algorithms/ 不做调度）

algorithm_type 含义：
- 'optimization': 工艺参数**优化**（请求-响应式推荐）
  - 由 optimization_advice service 通过 AlgorithmRegistry 编排 chain
  - 实现类：FuzzyEngine / LLMEngine / EmpiricalReasoning
- 'initialization': 工艺参数**初始化**（机器+材料+模具 → ProductionParams）
  - 由 parameter_init service 直调 ProcessInitializer，不走 Registry
  - 实现类：ProcessInitializer
- 'mining': 规则**挖掘**（历史数据 → 规则集，离线/异步）
  - 未来由独立 mining_service 编排
  - 实现类：RuleMinerEngine

设计原则：
- 算法层只负责"输入 context → 输出"——具体怎么调是 service 层的事
- AlgorithmRegistry 仅服务 optimization 场景（chain 调度需要）
- initialization / mining 各只有一个算法实现，service 直调即可
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Recommendation:
    """
    推荐结果数据类（optimization 类型算法使用）

    Attributes:
        param_name: 参数名称
        current_value: 当前值
        recommended_value: 推荐值
        confidence: 置信度 (0-1)
        reason: 推荐原因
        source: 来源算法 (fuzzy/llm/empirical)
    """
    param_name: str
    current_value: float
    recommended_value: float
    confidence: float
    reason: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'param': self.param_name,
            'current_value': self.current_value,
            'recommended_value': self.recommended_value,
            'confidence': self.confidence,
            'reason': self.reason,
            'source': self.source,
        }


class AlgorithmBase(ABC):
    """
    AI 推理类算法基类

    所有 process/algorithms/ 下的算法都应继承本类。

    Attributes:
        algorithm_name: 算法名称（人类可读）
        algorithm_type: 算法类型
            - 'optimization': 工艺参数优化（fuzzy/llm/empirical）
            - 'initialization': 工艺参数初始化（expert）
            - 'mining': 规则挖掘（rule_miner）
        algorithm_subtype: 算法子类型（fuzzy/llm/empirical/expert/rule_miner）

    子类实现要求：
    - 必须实现 run(context) -> Any（统一入口）
    - optimization 类型还应实现 recommend() 和 is_available()（被 chain 调度）
    - 返回类型由 algorithm_type 决定：
        * 'optimization': List[Recommendation]
        * 'initialization': ProductionParams
        * 'mining': List[Rule]（占位返回 []）
    """

    algorithm_name: str = "BaseAlgorithm"
    algorithm_type: str = ""           # 子类必填：optimization/initialization/mining
    algorithm_subtype: str = ""        # 子类必填

    @abstractmethod
    def run(self, context: dict) -> Any:
        """
        执行算法（统一入口）

        Args:
            context: 算法上下文（schema 由各 algorithm_type 决定）

        Returns:
            返回类型由 algorithm_type 决定：
            - 'optimization': List[Recommendation]
            - 'initialization': ProductionParams
            - 'mining': List[Rule]（占位返回 []）

        注意：
        本方法是基类统一入口，service 层通过 run() 调用算法。
        子类可以选择：
        - 直接实现 run()，自己处理所有逻辑
        - 实现领域方法（recommend / derive / mine），run() 内部转发
        """
        pass

    @abstractmethod
    def is_available(self, context: dict) -> bool:
        """
        判断当前算法是否适用于此场景

        Args:
            context: 推理上下文

        Returns:
            True if algorithm can handle this context
        """
        pass


class AlgorithmRegistry:
    """
    算法注册中心（仅供 optimization 类型使用）

    仅 service 层在 chain 调度时使用。initialization / mining 类型
    各只有一个算法，service 直调即可，不需要 Registry。

    使用方式：
        # 注册（在 algorithms/<subtype>/__init__.py 触发）
        AlgorithmRegistry.register('fuzzy', FuzzyEngine())

        # 查询（optimization_advice service 编排 chain 时）
        fuzzy = AlgorithmRegistry.get_algorithm('fuzzy')
        candidates = AlgorithmRegistry.get_algorithms_by_type('optimization')
    """

    _algorithms: Dict[str, AlgorithmBase] = {}
    _priorities: Dict[str, int] = {
        # 仅参与优化 chain 的算法：fuzzy / llm / empirical
        # initialization（expert）和 mining（rule_miner）不参与 chain，无需 priority
        'fuzzy': 1,        # 模糊推理 - 模型驱动
        'llm': 2,          # 大模型推理 - 占位
        'empirical': 3,    # 经验推理 - 兜底（chain 写死为最后一步，priority 仅为显式）
    }

    @classmethod
    def register(cls, algorithm_subtype: str, algorithm: AlgorithmBase):
        """
        注册算法

        Args:
            algorithm_subtype: 算法子类型
            algorithm: 算法实例
        """
        cls._algorithms[algorithm_subtype] = algorithm

    @classmethod
    def get_algorithm(cls, algorithm_subtype: str) -> Optional[AlgorithmBase]:
        """
        获取指定子类型的算法

        Args:
            algorithm_subtype: 算法子类型

        Returns:
            算法实例或 None
        """
        return cls._algorithms.get(algorithm_subtype)

    @classmethod
    def get_algorithms_by_type(
        cls,
        algorithm_type: str,
    ) -> List[AlgorithmBase]:
        """
        按 algorithm_type 过滤算法（不调用 is_available）

        设计意图：
        - type 是静态属性（类上定义），与运行时 context 无关
        - chain 调度需要拿到"所有 X 类型"算法集，然后逐个判断 is_available
        - 如需 is_available 过滤，调 cls.get_available_algorithms(context)

        Args:
            algorithm_type: 'optimization' / 'initialization' / 'mining'

        Returns:
            该 type 下的全部算法（不按可用性过滤）
        """
        return [
            a for a in cls._algorithms.values()
            if a.algorithm_type == algorithm_type
        ]

    @classmethod
    def get_available_algorithms(cls, context: dict) -> List[AlgorithmBase]:
        """
        获取所有当前 context 下可用的算法

        Args:
            context: 推理上下文

        Returns:
            可用算法列表
        """
        available = []
        for algorithm in cls._algorithms.values():
            if algorithm.is_available(context):
                available.append(algorithm)
        return available

    @classmethod
    def get_priority(cls, algorithm_subtype: str) -> int:
        """
        获取算法优先级

        Args:
            algorithm_subtype: 算法子类型

        Returns:
            优先级数值，数值越小优先级越高
        """
        return cls._priorities.get(algorithm_subtype, 99)

    @classmethod
    def set_priority(cls, algorithm_subtype: str, priority: int):
        """
        设置算法优先级

        Args:
            algorithm_subtype: 算法子类型
            priority: 优先级数值
        """
        cls._priorities[algorithm_subtype] = priority

    @classmethod
    def list_algorithms(cls) -> List[Dict[str, Any]]:
        """
        列出所有已注册的算法

        Returns:
            算法信息列表
        """
        return [
            {
                'subtype': subtype,
                'name': algorithm.algorithm_name,
                'type': algorithm.algorithm_type,
                'priority': cls.get_priority(subtype),
            }
            for subtype, algorithm in cls._algorithms.items()
        ]
