"""
模糊推理核心模型

按职责分三个来源：
- `features`：FuzzyFeature（论域实例）
- `rules`：FuzzyRule / NumTskRule / ParticularRules（规则串解析产物）
- `nets`：FuzzyRuleNet / NumTskRuleNet（推理网络）

内核的**输入契约**（KeywordProfile / RuleProfile）在 `fuzzy_core.profiles`。
"""

from .features import FuzzyFeature
from .nets import FuzzyRuleNet, NumTskRuleNet
from .rules import FuzzyRule, NumTskRule, ParticularRules

__all__ = [
    'FuzzyFeature',
    'FuzzyRule',
    'NumTskRule',
    'ParticularRules',
    'FuzzyRuleNet',
    'NumTskRuleNet',
]
