"""
引擎基类和注册中心

提供 AI 引擎的统一接口和动态注册机制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Recommendation:
    """
    推荐结果数据类

    Attributes:
        param_name: 参数名称
        current_value: 当前值
        recommended_value: 推荐值
        confidence: 置信度 (0-1)
        reason: 推荐原因
        source: 来源引擎 (fuzzy/rule_miner/llm/expert)
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


class AIEngineBase(ABC):
    """
    AI 算法引擎基类

    所有具体引擎需实现此接口

    Attributes:
        engine_name: 引擎名称
        engine_type: 引擎类型 (initialization/optimization)
        engine_subtype: 引擎子类型 (fuzzy/llm/rule_miner/doe/ga)
    """

    engine_name: str = "BaseEngine"
    engine_type: str = ""  # initialization / optimization
    engine_subtype: str = ""

    @abstractmethod
    def recommend(self, context: dict) -> List[Recommendation]:
        """
        根据上下文返回推荐结果

        Args:
            context: 推理上下文
                {
                    'process_condition': {...},
                    'process_parameter': {...},
                    'defect_feedbacks': [...],
                    'tuning_history': [...],
                    'iteration_trend': {           # 迭代趋势分析
                        'trend': 'improving/worsening/stable/final',
                        'improving_count': 0,
                        'worsening_count': 0,
                        'last_result': 'pending',
                        'recommendation': '...',
                    },
                    'machine': {...},
                    'mold': {...},
                    'polymer': {...},
                    'product': {...},
                }

        Returns:
            推荐结果列表
        """
        pass

    @abstractmethod
    def is_available(self, context: dict) -> bool:
        """
        判断当前引擎是否适用于此场景

        Args:
            context: 推理上下文

        Returns:
            True if engine can provide recommendations
        """
        pass

    def get_priority(self) -> int:
        """
        获取引擎优先级

        Returns:
            优先级数值，数值越小优先级越高
        """
        return EngineRegistry.get_priority(self.engine_subtype)


class EngineRegistry:
    """
    引擎注册中心

    支持策略模式动态切换引擎
    """

    _engines: Dict[str, AIEngineBase] = {}
    _priorities: Dict[str, int] = {
        'expert': 1,       # 专家系统 - 优先
        'fuzzy': 2,         # 模糊推理 - 次优
        'rule_miner': 3,    # 规则挖掘
        'llm': 4,           # 大模型
        'doe': 5,           # 实验设计
        'ga': 6,            # 遗传算法
    }

    @classmethod
    def register(cls, engine_subtype: str, engine: AIEngineBase):
        """
        注册引擎

        Args:
            engine_subtype: 引擎子类型
            engine: 引擎实例
        """
        cls._engines[engine_subtype] = engine

    @classmethod
    def get_engine(cls, engine_subtype: str) -> Optional[AIEngineBase]:
        """
        获取指定类型的引擎

        Args:
            engine_subtype: 引擎子类型

        Returns:
            引擎实例或 None
        """
        return cls._engines.get(engine_subtype)

    @classmethod
    def get_available_engines(cls, context: dict) -> List[AIEngineBase]:
        """
        获取所有可用的引擎

        Args:
            context: 推理上下文

        Returns:
            可用引擎列表
        """
        available = []
        for engine in cls._engines.values():
            if engine.is_available(context):
                available.append(engine)
        return available

    @classmethod
    def get_engines_by_priority(
        cls,
        context: dict,
        prefer_engines: List[str] = None,
        exclude_engines: List[str] = None,
    ) -> List[AIEngineBase]:
        """
        按优先级获取引擎

        Args:
            context: 推理上下文
            prefer_engines: 优先使用的引擎列表
            exclude_engines: 排除的引擎列表

        Returns:
            按优先级排序的引擎列表
        """
        available = cls.get_available_engines(context)

        # 过滤排除
        if exclude_engines:
            available = [e for e in available if e.engine_subtype not in exclude_engines]

        # 优先引擎过滤
        if prefer_engines:
            preferred = [e for e in available if e.engine_subtype in prefer_engines]
            others = [e for e in available if e.engine_subtype not in prefer_engines]
            available = preferred + others

        # 按优先级排序
        available.sort(key=lambda e: cls.get_priority(e.engine_subtype))

        return available

    @classmethod
    def get_priority(cls, engine_subtype: str) -> int:
        """
        获取引擎优先级

        Args:
            engine_subtype: 引擎子类型

        Returns:
            优先级数值
        """
        return cls._priorities.get(engine_subtype, 99)

    @classmethod
    def set_priority(cls, engine_subtype: str, priority: int):
        """
        设置引擎优先级

        Args:
            engine_subtype: 引擎子类型
            priority: 优先级
        """
        cls._priorities[engine_subtype] = priority

    @classmethod
    def list_engines(cls) -> List[Dict[str, Any]]:
        """
        列出所有已注册的引擎

        Returns:
            引擎信息列表
        """
        return [
            {
                'subtype': subtype,
                'name': engine.engine_name,
                'type': engine.engine_type,
                'priority': cls.get_priority(subtype),
            }
            for subtype, engine in cls._engines.items()
        ]
