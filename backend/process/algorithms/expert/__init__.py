"""
专家系统算法模块（工艺参数初始化）

algorithm_type='initialization'，**不注册**到 AlgorithmRegistry。
由 process.services.parameter_initialize service 直接调用 ProcessInitializer.derive()。

模块组成：
- ProcessInitializer: 工艺参数初始化器（service 层入口）
- AlgorithmEngine: 强约束推导器（辅助类）
- InitRuleLoader: 初始化规则加载器（JSON 文件）
- InitRuleMatcher: 初始化规则匹配器（数据库）
- DataValidator: 数据校验
- param_types: ProcessParams / MoldTempParams / HotRunnerParams / ProductionParams
- helpers / macros: 工具函数与常量
- expert_rules: JSON 规则文件

命名规范：
- ProcessParams: 注塑机工艺参数（行业默认的"工艺参数"）
- ProductionParams: 完整生产工艺（包含多设备组合）
"""

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
