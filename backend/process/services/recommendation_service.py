"""
推荐服务 - 对外统一入口

整合多个 AI 引擎，提供统一的推荐接口
"""

import logging
from typing import List, Optional

from process.engines.base_engine import EngineRegistry, Recommendation as EngineRecommendation
from process.models import (
    ProcessCondition,
    ProcessParameter,
    Recommendation,
    TuningRecord,
)
from process.services.tuning_service import ProcessTuningService

_logger = logging.getLogger(__name__)


class ProcessRecommendationService:
    """
    推荐服务 - 对外统一入口

    使用方式：
    1. 实例化服务（自动注册默认引擎）
    2. 调用 get_recommendations 获取推荐
    3. 调用 adopt_recommendation 采纳推荐

    阶段（当前骨架）：
      - FuzzyEngine 已在 EngineRegistry 注册并调用
      - trend 后处理、多引擎合并策略留 TODO（设计中）
    """

    def __init__(self):
        # 引擎自注册（lazy import 避免循环依赖）
        self._register_default_engines()

    def _register_default_engines(self):
        """
        注册默认引擎。

        设计约束（临时）：
          - 当前只注册 FuzzyEngine，后续接入 RuleMiner / LLM
          - 幂等：多次调用不会重复注册
        """
        try:
            from process.engines.fuzzy import FuzzyEngine

            if not EngineRegistry.get_engine("fuzzy"):
                EngineRegistry.register("fuzzy", FuzzyEngine())
        except Exception as e:  # noqa: BLE001
            _logger.warning("[recommendation_service] FuzzyEngine 注册失败: %s", e)

    def get_recommendations(
        self,
        process_condition_id: int,
        defect_feedbacks: List[dict] = None,
        engine_types: List[str] = None,
    ) -> dict:
        """
        获取推荐结果

        流程：
          1. _build_context 拼装推理上下文（含 iteration_trend）
          2. 从 EngineRegistry 获取可用引擎（按优先级排序）
          3. 各引擎独立调用 recommend()，收集结果
          4. trend 后处理（TODO）
          5. 合并多引擎结果（TODO：当前为各引擎结果并列返回）

        Args:
            process_condition_id: 工艺条件 ID
            defect_feedbacks: 缺陷反馈列表
            engine_types: 指定使用的引擎子类型列表，None 表示使用所有可用引擎

        Returns:
            {
                'recommendations': [...],
                'engine_sources': {'模糊推理': [...]},
                'best_recommendation': {...} | None,
            }
        """
        # 1. 构建上下文
        context = self._build_context(process_condition_id, defect_feedbacks or [])
        if not context:
            return {
                "recommendations": [],
                "engine_sources": {},
                "best_recommendation": None,
            }

        # 2. 获取可用引擎
        engines = EngineRegistry.get_engines_by_priority(
            context=context,
            prefer_engines=engine_types,
        )
        if not engines:
            _logger.info(
                "[recommendation_service] 无可用引擎: condition_id=%s", process_condition_id
            )
            return {
                "recommendations": [],
                "engine_sources": {},
                "best_recommendation": None,
            }

        # 3. 逐个引擎调用
        all_recommendations: List[EngineRecommendation] = []
        engine_sources: dict = {}
        for engine in engines:
            try:
                recs = engine.recommend(context) or []
            except Exception as e:  # noqa: BLE001
                _logger.warning(
                    "[recommendation_service] 引擎 %s 推理失败: %s",
                    engine.engine_name, e,
                )
                recs = []
            engine_sources[engine.engine_name] = [r.to_dict() for r in recs]
            all_recommendations.extend(recs)

        # 4. trend 后处理（TODO：设计中）
        # TODO: 按 iteration_trend.trend 调整 absolute 类的推荐值
        #       worsening -> *0.5 / improving -> *1.2 / stable -> 1.0

        # 5. 合并去重（TODO：当前为各引擎结果并列）
        # TODO: 同一参数多引擎推荐时按 confidence 取最高
        merged = [r.to_dict() for r in all_recommendations]

        return {
            "recommendations": merged,
            "engine_sources": engine_sources,
            "best_recommendation": merged[0] if merged else None,
        }

    def _build_context(
        self,
        condition_id: int,
        defect_feedbacks: List[dict]
    ) -> dict:
        """
        构建推理上下文

        包含迭代趋势分析结果，供引擎选择策略使用：
        - improving: 持续改善，继续当前方向
        - worsening: 持续恶化，需回退或换策略
        - stable: 改善/恶化交替，陷入僵局
        - final: 已达终态
        """
        try:
            condition = ProcessCondition.objects.get(id=condition_id)
        except ProcessCondition.DoesNotExist:
            return {}

        parameter = ProcessParameter.objects.filter(
            process_condition=condition,
            is_deleted=False
        ).first()

        tuning_history = TuningRecord.objects.filter(
            process_parameter=parameter
        ).order_by('-created_at')[:50] if parameter else []

        # 分析迭代趋势
        if parameter:
            trend = ProcessTuningService.analyze_iteration_trend(parameter)
            trend_dict = {
                'trend': trend.trend,
                'improving_count': trend.improving,
                'worsening_count': trend.worsening,
                'unchanged_count': trend.unchanged,
                'last_result': trend.last_result,
                'recommendation': trend.recommendation,
            }
        else:
            trend_dict = {
                'trend': 'unknown',
                'improving_count': 0,
                'worsening_count': 0,
                'unchanged_count': 0,
                'last_result': 'pending',
                'recommendation': '等待创建参数',
            }

        # 构建上下文
        context = {
            'process_condition': self._serialize_condition(condition),
            'process_parameter': self._serialize_parameter(parameter) if parameter else {},
            'defect_feedbacks': defect_feedbacks,
            'tuning_history': [self._serialize_record(r) for r in tuning_history],
            'iteration_trend': trend_dict,
        }

        # 添加设备能力信息
        if condition.injection_machine:
            context['machine'] = self._get_machine_capabilities(condition.injection_machine)

        return context

    def _serialize_condition(self, condition: ProcessCondition) -> dict:
        """序列化工艺条件"""
        return {
            'id': condition.id,
            'condition_no': condition.condition_no,
            'status': condition.status,
            'origin_type': condition.origin_type,
            'mold_id': condition.mold_id,
            'injection_machine_id': condition.injection_machine_id,
            'polymer_id': condition.polymer_id,
            'shot_index': condition.shot_index,
            'injection_index': condition.injection_index,
        }

    def _serialize_parameter(self, parameter: ProcessParameter) -> dict:
        """序列化工艺参数"""
        data = {}
        for field in parameter._meta.fields:
            if field.name.startswith('_') or field.name in ['id', 'created_at', 'updated_at']:
                continue
            value = getattr(parameter, field.name, None)
            if value is not None:
                data[field.name] = value
        return data

    def _serialize_record(self, record: TuningRecord) -> dict:
        """序列化调参记录"""
        return {
            'id': record.id,
            'defect_feedbacks': record.defect_feedbacks,
            'result': record.result,
            'note': record.note,
            'parameter_snapshot': record.parameter_snapshot,
            'created_at': record.created_at.isoformat() if record.created_at else None,
        }

    def _get_machine_capabilities(self, machine) -> dict:
        """
        获取设备能力信息

        TODO: 后续根据实际设备模型完善
        """
        return {
            'id': machine.id,
            'name': getattr(machine, 'name', str(machine)),
            # TODO: 添加设备参数范围
            'capabilities': {},
        }

    def adopt_recommendation(
        self,
        recommendation_id: int,
        process_parameter_id: int,
    ) -> ProcessParameter:
        """
        采纳推荐，创建新的参数版本

        Args:
            recommendation_id: 推荐 ID
            process_parameter_id: 当前参数 ID

        Returns:
            新创建的参数版本
        """
        recommendation = Recommendation.objects.get(id=recommendation_id)
        current_param = ProcessParameter.objects.get(id=process_parameter_id)

        # 创建新版本
        new_param = ProcessParameter.objects.create(
            process_condition=current_param.process_condition,
            parent_param=current_param,
            param_source='ai_recommended',
            **self._apply_recommendations(
                current_param,
                recommendation.recommendations
            )
        )

        # 更新推荐状态
        recommendation.is_adopted = True
        recommendation.adopted_param = new_param
        recommendation.save()

        return new_param

    def _apply_recommendations(
        self,
        current_param: ProcessParameter,
        recommendations: List[dict]
    ) -> dict:
        """
        应用推荐到参数

        TODO: 后续完善推荐应用逻辑
        """
        updates = {}
        for rec in recommendations:
            param_name = rec.get('param')
            if param_name and hasattr(current_param, param_name):
                # TODO: 根据 action 计算新值
                # currently just use recommended_value directly
                updates[param_name] = rec.get('recommended_value')
        return updates

    def create_recommendation(
        self,
        parameter: ProcessParameter,
        source_type: str,
        recommendations: List[dict],
    ) -> Recommendation:
        """
        创建推荐记录

        Args:
            parameter: 工艺参数
            source_type: 推荐来源 (fuzzy_rule/rule_miner/llm/doe)
            recommendations: 推荐列表

        Returns:
            Recommendation 实例
        """
        return Recommendation.objects.create(
            process_parameter=parameter,
            source_type=source_type,
            recommendations=recommendations,
        )
