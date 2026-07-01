"""
工艺智能引擎

包含以下模块：
- base_engine.py: 引擎基类和注册中心
- expert/: 专家系统引擎
- fuzzy/: 模糊推理引擎
- llm/: 大模型引擎
- rule_miner/: 规则挖掘引擎
"""

from .base_engine import AIEngineBase, EngineRegistry, Recommendation

__all__ = [
    "AIEngineBase",
    "EngineRegistry",
    "Recommendation",
]
