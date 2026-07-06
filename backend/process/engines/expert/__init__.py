"""
专家系统引擎模块

包含：
- ExpertEngine: 专家引擎主类
- ProcessInitializer: 工艺参数初始化器
- InitRuleLoader: 初始化规则加载器（JSON 文件）
- InitRuleMatcher: 初始化规则匹配器（数据库）
- ProcessParams: 注塑机工艺参数（行业默认的"工艺参数"）
- MoldTempParams: 模温机工艺参数
- HotRunnerParams: 热流道工艺参数
- ProductionParams: 完整生产工艺参数（多设备组合）

命名规范：
- ProcessParams: 注塑机工艺参数（行业默认叫"工艺参数"）
- ProductionParams: 完整生产工艺（包含多设备）
"""

from .expert_engine import ExpertEngine
from .initializer import ProcessInitializer
from .algorithm_engine import AlgorithmEngine
from .rule_loader import InitRuleLoader
from .rule_matcher import InitRuleMatcher
from .data_validator import DataValidator
from .param_types import (
    ProcessParams,
    MoldTempParams,
    HotRunnerParams,
    ProductionParams,
)
from .helpers import (
    compute_screw_cross_area,
    compute_total_injection_length,
    compute_cushion_length,
    parse_material_family,
    get_coeff,
)

__all__ = [
    "ExpertEngine",
    "ProcessInitializer",
    "AlgorithmEngine",
    "InitRuleLoader",
    "InitRuleMatcher",
    "DataValidator",
    "ProcessParams",
    "MoldTempParams",
    "HotRunnerParams",
    "ProductionParams",
    "compute_screw_cross_area",
    "compute_total_injection_length",
    "compute_cushion_length",
    "parse_material_family",
    "get_coeff",
]