"""
专家系统引擎

用于根据模具/材料/机台推理初始工艺参数
"""

from typing import List, Optional, Dict, Any

from process.engines.base_engine import AIEngineBase, Recommendation, EngineRegistry
from process.engines.expert.initializer import ProcessInitializer
from process.engines.expert.param_types import ProcessParams


class ExpertEngine(AIEngineBase):
    """
    专家系统引擎 - 基于专家规则推理初始工艺参数

    用于工艺初始化阶段，根据模具/材料/产品/机台信息推理初始工艺参数
    """

    engine_name = "专家系统"
    engine_type = "initialization"
    engine_subtype = "expert"

    def __init__(self):
        """初始化专家引擎"""
        self._initializer: Optional[ProcessInitializer] = None

    def recommend(self, context: dict) -> List[Recommendation]:
        """
        根据上下文推理初始工艺参数

        返回推荐结果列表（兼容基类接口）
        如需获取完整参数集，使用 infer_initial_params()

        Args:
            context: {
                'machine': {...},      # 机器信息
                'polymer': {...},      # 材料信息
                'product': {...},      # 产品信息
            }

        Returns:
            初始工艺参数推荐列表
        """
        try:
            params = self.infer_initial_params(context)
        except ValueError:
            return []

        # 转换为推荐结果
        recommendations = []
        params_dict = params.to_dict()

        # 注射参数
        if params_dict.get('injection_pressure'):
            recommendations.append(Recommendation(
                param_name='injection_pressure',
                current_value=0,
                recommended_value=params_dict['injection_pressure'][0],
                confidence=0.9,
                reason='基于机器最大压力和材料特性计算',
                source='expert'
            ))

        return recommendations

    def is_available(self, context: dict) -> bool:
        """
        判断是否可用

        需要机器、材料、产品信息完整
        """
        return all([
            context.get('machine'),
            context.get('polymer'),
            context.get('product'),
        ])

    def infer_initial_params(self, context: dict) -> ProcessParams:
        """
        推理初始工艺参数

        使用专家规则基于机器/材料/产品信息推导初始工艺参数

        Args:
            context: 推理上下文
                {
                    'machine': {...},      # 机器信息
                    'polymer': {...},      # 材料信息
                    'product': {...},      # 产品信息
                }

        Returns:
            ProcessParams: 工艺参数

        Raises:
            ValueError: 必要信息不完整时
        """
        machine = context.get('machine', {})
        polymer = context.get('polymer', {})
        product = context.get('product', {})

        if not machine:
            raise ValueError("缺少机器信息")
        if not polymer:
            raise ValueError("缺少材料信息")
        if not product:
            raise ValueError("缺少产品信息")

        initializer = ProcessInitializer(machine, polymer)
        return initializer.derive(product)


# 注册引擎
EngineRegistry.register('expert', ExpertEngine())
