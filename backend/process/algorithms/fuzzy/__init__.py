"""
模糊推理算法模块

algorithm_type='optimization'，由 condition service 通过 AlgorithmRegistry 编排 chain。

模块分层（每层职责单一，文件名各自自解释）：
- 【0 对外接口】specs: 调优入参契约（字段选择 + 必填等级）+ OptimizeDataValidator
  契约定在算法层，所有调用方（service / 第三方 / CLI）自动受约束
- 【1 编排】engine: FuzzyEngine 主流程；recommendations: 推荐结果产出；field_names: 字段名映射
- 【2 规则库适配】library: 对外契约 library.contracts（AlgorithmResourceRepository 协议 +
  RuleQueryContext，零依赖）/ library.rules（规则资源：取数 + 规则串语义）/ library.keywords（关键字资源）
  / library.repository（资源集合：编排选库→收集→组装，算法实际要用的资源）
  / library.files（文件来源 + 规则格式翻译，预留）
- 【3 内核】fuzzy_core: 归属它自己的**输入契约**（profiles: KeywordProfile / RuleProfile）
  + 论域实例（features: FuzzyFeature）+ 规则串解析（rules: FuzzyRule / NumTskRule）
  + 推理网络（nets: FuzzyRuleNet / NumTskRuleNet）

命名约定：`specs` = 对外接口格式（与 expert 包同名同层）；`profiles` = 内核输入契约；`field_names` = 字段**名**映射（与 `specs` 的字段**规格**互补）；`engine` = 模糊推理引擎（与类名 `FuzzyEngine` 对应）；`recommendations` = 推理结果 → 对外推荐契约（与 `base.AlgorithmRecommendation` 同词根）。
"""

from . import field_names
from .engine import FuzzyEngine
from .specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OPTIMIZE_POLYMER_INFO_FIELDS,
    OPTIMIZE_MOLD_INFO_FIELDS,
    REQUIRED_OPTIMIZE_MACHINE_FIELDS,
    REQUIRED_OPTIMIZE_POLYMER_FIELDS,
    REQUIRED_OPTIMIZE_MOLD_FIELDS,
    OptimizeDataValidator,
    VALID_DEFECT_LEVEL_WORDS,
    VALID_DEFECT_LEVEL_WORDS_TEXT,
    is_valid_defect_level_word,
)

__all__ = [
    "FuzzyEngine",
    "field_names",
    "OPTIMIZE_MACHINE_INFO_FIELDS",
    "OPTIMIZE_POLYMER_INFO_FIELDS",
    "OPTIMIZE_MOLD_INFO_FIELDS",
    "REQUIRED_OPTIMIZE_MACHINE_FIELDS",
    "REQUIRED_OPTIMIZE_POLYMER_FIELDS",
    "REQUIRED_OPTIMIZE_MOLD_FIELDS",
    "OptimizeDataValidator",
    "VALID_DEFECT_LEVEL_WORDS",
    "VALID_DEFECT_LEVEL_WORDS_TEXT",
    "is_valid_defect_level_word",
]
