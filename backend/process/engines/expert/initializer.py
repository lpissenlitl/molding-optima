"""
工艺参数初始化器（编排层）

职责：
    - 数据校验（委托 DataValidator）
    - 规则加载（委托 rule_matcher）
    - 算法推理（委托 AlgorithmEngine）
    - 组装输出

实际的算法推导逻辑在 AlgorithmEngine 中。
"""

import logging
from typing import Dict, Any, Optional

from .param_types import ProcessParams, MoldTempParams, HotRunnerParams, ProductionParams
from .rule_matcher import InitRuleMatcher
from .data_validator import DataValidator
from .algorithm_engine import AlgorithmEngine
from .helpers import parse_material_family

logger = logging.getLogger(__name__)


class ProcessInitializer:
    """
    工艺参数初始化器（编排层）

    基于机器、材料、产品信息，使用专家规则推理初始工艺参数。

    设备分组：
    - 注塑机参数（ProcessParams）
    - 模温机参数（MoldTempParams）
    - 热流道参数（HotRunnerParams）

    Usage:
        initializer = ProcessInitializer(
            mold_info=mold_info,        # 模具信息
            machine_info=machine_info,  # 设备信息
            polymer_info=polymer_info,  # 材料信息
            process_set=process_set,   # 工艺设定
        )
        params = initializer.derive()  # 返回 ProductionParams
    """

    def __init__(
        self,
        mold_info: Dict[str, Any],
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        process_set: Optional[Dict[str, Any]] = None,
        rule_matcher: Optional[InitRuleMatcher] = None,
    ):
        """
        工艺参数初始化器（4 维独立 dict 输入）

        接受 4 个独立维度的输入，顺序统一为：模具 → 设备 → 材料 → 工艺设定
        - mold_info：模具信息（模具级 + 产品/浇口/壁厚派生合一）
        - machine_info：设备信息（机台本身 + 注射单元合一）
        - polymer_info：材料信息
        - process_set：工艺设置（段数 + 模式），None 时用空 dict
        """
        if not mold_info:
            raise ValueError("模具信息不能为空")
        if not machine_info:
            raise ValueError("设备信息不能为空")
        if not polymer_info:
            raise ValueError("材料信息不能为空")

        self.mold = mold_info
        self.machine = machine_info
        self.material = polymer_info
        self.process_set = process_set or {}
        self.rule_matcher = rule_matcher or InitRuleMatcher()
        self._validator = DataValidator()

    # ========== 工具方法（供测试和调试用）==========

    def _parse_family(self, abbrev: str) -> str:
        """
        解析材料 family（委托 helpers）

        保留此方法以兼容旧代码和测试。
        """
        return parse_material_family(abbrev)

    @property
    def engine(self) -> AlgorithmEngine:
        """
        获取算法引擎实例（供测试和调试用）

        在 derive() 调用后可用。
        """
        return getattr(self, '_engine', None)

    def derive(self) -> ProductionParams:
        """
        推导初始工艺参数

        流程：
        1. 数据校验（DataValidator）
        2. 规则加载（InitRuleMatcher）
        3. 算法推理（AlgorithmEngine）
        4. 返回 ProductionParams
        """
        # 1. 数据校验
        self._validator.validate(self.machine, self.material, self.mold)

        # 2. 规则加载
        coeffs = self.rule_matcher.match({
            'machine': self.machine,
            'material': self.material,
            'mold': self.mold,
            'process_set': self.process_set,
        })

        # 3. 创建算法引擎并执行推理
        self._engine = AlgorithmEngine(
            mold=self.mold,
            machine=self.machine,
            material=self.material,
            process_set=self.process_set,
            coeffs=coeffs,
        )

        params = ProductionParams(
            process=ProcessParams(),
            mold_temp=MoldTempParams(),
            hot_runner=HotRunnerParams(),
        )

        self._engine.derive(params)

        return params
