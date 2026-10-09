"""
模糊推理引擎 - 主入口

基于模糊规则进行缺陷修正推荐。

采用"双层并行架构"（见 fuzzy-engine-reference.md §2）：
- 工厂级 (NumTskRuleNet)   → 处理精确数值/百分比规则
- 兜底层 (FuzzyRuleNet)    → 处理模糊级结论规则（兼容 Rule.dat 风格）
- 合并策略                 → 同层聚合 + 跨层覆盖（方案 B）
"""

import logging
from typing import List, Dict, Any, Optional

from process.algorithms.base import AlgorithmBase, Recommendation, AlgorithmRegistry
from process.algorithms.fuzzy.adapters import RuleKeywordAdapter, RuleMethodAdapter
from process.algorithms.fuzzy.fuzzy_core.models.nets import (
    FuzzyRuleNet,
    NumTskRuleNet,
    ParticularRules,
)
from process.algorithms.fuzzy.services.rule_query_service import (
    RuleQueryService,
    RuleQueryContext,
    ResolvedRule,
)


logger = logging.getLogger(__name__)


class FuzzyEngine(AlgorithmBase):
    """模糊推理算法 - 基于模糊规则进行缺陷修正。

    algorithm_type='optimization'，由 optimization_advice service 编排 chain。
    适用于已知规则的场景，如工艺缺陷修正。
    """

    algorithm_name = "模糊推理"
    algorithm_type = "optimization"
    algorithm_subtype = "fuzzy"

    # ============================================================
    # 字段命名约束声明（Port-Adapter 模式的“端口”部分）
    #
    # 设计（见 algorithm-context-design.md §6.10）：
    # - fuzzy rule 用的字段名（来自 RuleKeyword.keyword_name）是稳定的“业务专家约定”
    # - 本声明让算法侧声明“我需要什么字段名”这种接口契约
    # - 上层（数据准备层 _normalize_field_name_by_spec）按此映射翻译业务命名
    # - 算法内部不需要懂业务命名（保持纯函数）
    #
    # 约定：每个 key 是业务 prefix 或完整字段名，value 是算法侧使用的字段名。
    # - 前缀映射：value 是算法 prefix，拼上原序号（如 IL1、BT3）
    # - 完整字段名映射：value 是算法完整名（如 NT、CT、MEL、DDBM）
    #
    # 设计原则（2026-09-30 确认）：
    # - 以算法侧 RuleKeyword 为准则：表中每个 mapping 都对应实际存在的算法 keyword
    # - 理论上 ProcessParameter 中每个工艺字段都能在此找到映射（70/71 已覆盖）
    # - 未映射场景只发生在业务控制字段（如 _stg / _mode）或算法未启用的边界 case（如 met_lim_t）
    # ============================================================
    FIELD_NAME_ALIAS: Dict[str, str] = {
        # ---- 注射阶段（inj_*_N → IL/IV/IP_N，前缀映射）----
        "inj_pos":  "IL",   # 注射位置 1-6 → IL1-IL6
        "inj_spd":  "IV",   # 注射速度 1-6 → IV1-IV6
        "inj_pres": "IP",   # 注射压力 1-6 → IP1-IP6
        # ---- 保压阶段（hold_*_N → PP/PV/PT_N，前缀映射）----
        # 注意：保压只有压力/速度/时间三组（无位置字段：算法 ML 实际是熔胶位置）
        "hold_pres": "PP",   # 保压压力 1-5 → PP1-PP5
        "hold_spd":  "PV",   # 保压速度 1-5 → PV1-PV5
        "hold_t":    "PT",   # 保压时间 1-5 → PT1-PT5
        # ---- 熔胶阶段（met_*_N → ML/MP/MBP/MSR_N，前缀映射）----
        "met_pos":      "ML",   # 熔胶位置 1-4 → ML1-ML4（算法侧 ML 实际是熔胶位置）
        "met_pres":     "MP",   # 熔胶压力 1-4 → MP1-MP4
        "met_back_pres":"MBP",  # 背压 1-4 → MBP1-MBP4
        "met_rot_spd":  "MSR",  # 螺杆转速 1-4 → MSR1-MSR4
        # ---- 温度（完整字段名映射 或 前缀映射）----
        "noz_temp":  "NT",   # 喷嘴温度 → NT
        "cool_t":    "CT",   # 冷却时间 → CT
        "brl_temp":  "BT",   # 料筒温度 1-9 → BT1-BT9
        # ---- 熔胶动作（完整字段名映射）----
        "pre_met_decomp_dist":    "DDBM", # 熔胶前松退距离 → DDBM
        "pst_met_decomp_dist":    "DDAM", # 熔胶后松退距离 → DDAM
        "met_end_pos":            "MEL",  # 计量终点位置 → MEL
        # ---- 注射耗时（完整字段名映射）----
        "inj_t":     "IT",       # 注射时间 → IT
        "inj_dly_t": "ID",       # 注射延迟 → ID
        # ---- VP 切换（完整字段名映射）----
        "vps_mode": "VPTM",      # VP 切换模式 → VPTM
        "vps_pos":  "VPTL",      # VP 切换位置 → VPTL
        "vps_pres": "VPTP",      # VP 切换压力 → VPTP
        "vps_spd":  "VPTV",      # VP 切换速度 → VPTV
        "vps_t":    "VPTT",      # VP 切换时间 → VPTT
    }

    # 工厂级网络和兜底层网络（每次 recommend 时构造；可考虑缓存）
    def __init__(self):
        self._rule_net = None  # 兼容旧接口，不使用

    def recommend(self, context: dict) -> List[Recommendation]:
        """根据缺陷反馈返回参数调整推荐。

        核心流程（见 fuzzy-engine-reference.md §4.8）：
          1) 拉规则（RuleQueryService + 三级特异性匹配）
          2) 双层分流（factory / fallback）
          3) 构造 NumTskRuleNet + FuzzyRuleNet，并行推理
          4) 合并：方案 B（同层聚合 + 跨层覆盖）
          5) 返回 Recommendation 列表

        Args:
            context: {
                'feedback': {                        # 反馈 dict（含 defect / observations / tuning_result）
                    'defect': [...],
                    'observations': [...],
                    'tuning_result': str | None,
                },
                'process_parameter': {...},          # 当前参数
                'iteration_trend': {...},            # 迭代趋势
                'machine': {...},
                # --- FuzzyEngine 扩展上下文 ---
                'polymer_abbreviation': 'PE',
                'product_category': '酒瓶',
                'rule_library_code': 'packaging',    # 可选
            }

        Returns:
            List[Recommendation]
        """
        defects = (context.get('feedback') or {}).get('defect', []) or []
        if not defects:
            return []

        # 兼容 defect_name 来自 defects[0] 或顶层 context
        defect_name = (
            context.get('defect_name')
            or (defects[0].get('defect_name') if isinstance(defects[0], dict) else None)
        )
        if not defect_name:
            logger.warning('[FuzzyEngine] 未指定 defect_name，跳过推荐')
            return []

        # 1) 拉规则
        query_ctx = RuleQueryContext(
            defect_name=defect_name,
            polymer_abbreviation=context.get('polymer_abbreviation'),
            product_category=context.get('product_category'),
            rule_library_code=context.get('rule_library_code'),
        )
        all_rules = RuleQueryService.get_rules(query_ctx)
        if not all_rules:
            logger.info('[FuzzyEngine] 未找到适用规则: %s', query_ctx)
            return []

        # 2) 双层分流
        split = RuleQueryService.split_by_level(all_rules)
        factory_rules = split['factory']
        fallback_rules = split['fallback']

        # 收集涉及的 RuleKeyword 名称（避免全表扫描）
        process_parameter = context.get('process_parameter') or {}
        trend = context.get('iteration_trend', {}) or {}
        adjustment_factor = self._trend_to_factor(trend.get('trend', 'unknown'))

        # 3) 双层并行推理
        factory_results = self._infer_factory_layer(factory_rules, process_parameter)
        fallback_results = self._infer_fallback_layer(fallback_rules, process_parameter)

        # 4) 合并（方案 B）：同层聚合 + 跨层覆盖
        merged = self._merge_layer_results(
            factory_results=factory_results,
            fallback_results=fallback_results,
            adjustment_factor=adjustment_factor,
            current_params=process_parameter,
        )

        return merged

    def is_available(self, context: dict) -> bool:
        """判断是否可用。"""
        if not (context.get('feedback') or {}).get('defect'):
            return False

        trend = context.get('iteration_trend', {})
        if trend.get('trend') == 'final':
            return False

        return True

    def run(self, context: dict) -> List[Recommendation]:
        """统一入口：包装 recommend()。

        algorithm_type='optimization'，返回 List[Recommendation]。
        """
        return self.recommend(context)

    # -----------------------------------------------------------------------
    # 内部方法
    # -----------------------------------------------------------------------

    @staticmethod
    def _trend_to_factor(trend: str) -> float:
        """迭代趋势 → 调整系数。"""
        return {
            'worsening': 0.5,
            'improving': 1.2,
            'stable': 1.0,
            'unknown': 1.0,
            'final': 1.0,
        }.get(trend, 1.0)

    @staticmethod
    def _collect_keyword_names(rules: List[ResolvedRule]) -> set:
        """从规则字符串中提取所有涉及的参数名（粗略解析）。"""
        names = set()
        for r in rules:
            for word in r.rule_str.split():
                if '_' in word and word.isupper() is False:
                    token = word.split('_')[0]
                    if token and not token[0].isupper():
                        names.add(token)
        return names

    def _infer_factory_layer(
        self,
        factory_rules: List[ResolvedRule],
        process_parameter: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """工厂级推理（NumTskRuleNet）。"""
        if not factory_rules:
            return []

        param_names = self._collect_keyword_names(factory_rules)
        keyword_dicts = []
        if param_names:
            try:
                keyword_dicts = RuleKeywordAdapter.get_keywords_by_names(list(param_names))
            except Exception as e:
                logger.warning('[FuzzyEngine] 加载 RuleKeyword 失败: %s', e)

        # 兜底：用 process_parameter 实时值补全 keyword 元数据
        known_keywords = {kw['keyword'] for kw in keyword_dicts}
        for name in param_names:
            if name not in known_keywords and name in process_parameter:
                keyword_dicts.append({
                    'keyword': name,
                    'lvl': 3,
                    'min_val': 0.0,
                    'max_val': float(process_parameter[name]) * 2,
                    'step': max(float(process_parameter[name]) * 0.1, 0.01),
                })

        if not keyword_dicts:
            logger.info('[FuzzyEngine] 工厂级无可用 RuleKeyword，跳过')
            return []

        rule_array = RuleQueryService.to_rule_array(factory_rules)
        priority_array = RuleQueryService.get_priority_array(factory_rules)

        try:
            net = NumTskRuleNet(rule_array, keyword_dicts, priority_array)
            results, extra = net.predict(process_parameter, top_k=len(factory_rules))
        except Exception as e:
            logger.exception('[FuzzyEngine] NumTskRuleNet 推理失败: %s', e)
            return []

        # 提取 [{param: value}] 字典 → List[Dict]
        out = []
        for rule_str, activation, adjustments in results:
            for param, value in adjustments.items():
                out.append({
                    'source': 'factory',
                    'param': param,
                    'delta': float(value) * float(activation),
                    'activation': float(activation),
                    'rule': rule_str,
                })
        return out

    def _infer_fallback_layer(
        self,
        fallback_rules: List[ResolvedRule],
        process_parameter: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """兜底层推理（FuzzyRuleNet）。"""
        if not fallback_rules:
            return []

        param_names = self._collect_keyword_names(fallback_rules)
        keyword_dicts = []
        if param_names:
            try:
                keyword_dicts = RuleKeywordAdapter.get_keywords_by_names(list(param_names))
            except Exception as e:
                logger.warning('[FuzzyEngine] 加载 RuleKeyword 失败: %s', e)

        known_keywords = {kw['keyword'] for kw in keyword_dicts}
        for name in param_names:
            if name not in known_keywords and name in process_parameter:
                keyword_dicts.append({
                    'keyword': name,
                    'lvl': 3,
                    'min_val': 0.0,
                    'max_val': float(process_parameter[name]) * 2,
                    'step': max(float(process_parameter[name]) * 0.1, 0.01),
                })

        if not keyword_dicts:
            return []

        rule_array = RuleQueryService.to_rule_array(fallback_rules)
        try:
            net = FuzzyRuleNet(rule_array, keyword_dicts)
            results = net.predict(process_parameter, top_k=len(fallback_rules))
        except Exception as e:
            logger.exception('[FuzzyEngine] FuzzyRuleNet 推理失败: %s', e)
            return []

        out = []
        for param_name, value, _ in results:
            out.append({
                'source': 'fallback',
                'param': param_name,
                'delta': float(value),
                'activation': float(_[0]) if isinstance(_, tuple) else 1.0,
                'rule': 'fallback',
            })
        return out

    @staticmethod
    def _merge_layer_results(
        factory_results: List[Dict[str, Any]],
        fallback_results: List[Dict[str, Any]],
        adjustment_factor: float,
        current_params: Dict[str, float],
    ) -> List[Recommendation]:
        """合并双层结果（方案 B：同层聚合 + 跨层覆盖）。

        返回 Recommendation 列表。
        """
        merged: Dict[str, Dict[str, Any]] = {}

        for rec in factory_results:
            p = rec['param']
            if p not in merged:
                merged[p] = {
                    'param': p,
                    'delta': rec['delta'],
                    'activation_sum': rec['activation'],
                    'rule_count': 1,
                    'sources': ['factory'],
                    'fallback_reference': None,
                }
            else:
                merged[p]['delta'] += rec['delta']
                merged[p]['activation_sum'] += rec['activation']
                merged[p]['rule_count'] += 1

        for rec in fallback_results:
            p = rec['param']
            if p not in merged:
                merged[p] = {
                    'param': p,
                    'delta': rec['delta'],
                    'activation_sum': rec['activation'],
                    'rule_count': 1,
                    'sources': ['fallback'],
                    'fallback_reference': None,
                }
                merged[p]['sources'] = ['fallback']
            else:
                # 工厂级已覆盖，仅作 fallback_reference 注释
                merged[p]['fallback_reference'] = rec['delta']
                merged[p]['sources'].append('fallback')

        # 转换为 Recommendation
        recommendations: List[Recommendation] = []
        for p, info in merged.items():
            raw_current = current_params.get(p)
            current_value = float(raw_current) if raw_current is not None else 0.0
            adjusted_delta = info['delta'] * adjustment_factor
            recommended_value = current_value + adjusted_delta

            recommendations.append(Recommendation(
                param_name=p,
                current_value=current_value,
                recommended_value=recommended_value,
                confidence=min(info['activation_sum'] / max(info['rule_count'], 1), 1.0),
                reason=f"模糊推理 (sources={info['sources']})",
                source='fuzzy.factory' if 'factory' in info['sources'] else 'fuzzy.fallback',
            ))

        return recommendations

    # -----------------------------------------------------------------------
    # 兼容老接口（暂时不实现）
    # -----------------------------------------------------------------------

    def load_rules(self):
        """加载模糊规则（兼容接口，占位）。"""
        # 当前实现：规则在每次 recommend 时通过 RuleQueryService 动态拉取
        pass


# 注册引擎
AlgorithmRegistry.register('fuzzy', FuzzyEngine())
