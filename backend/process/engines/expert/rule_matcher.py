"""
工艺参数初始化规则匹配器（数据库版）

数据源优先级：
    1. 数据库 ExpertRule（生产环境主路径）
    2. InitRuleLoader(JSON 文件)（本地/无 DB 场景）
    3. 内置 _BUILTIN_DEFAULTS（兜底）

匹配逻辑：
    - 按 priority 升序遍历（数字越小越优先）
    - 条件数组 AND 关系，空条件表示默认规则
    - 多条匹配规则深度合并 coefficients
"""

import logging
from typing import Dict, Any, Optional, List

from .rule_loader import InitRuleLoader

logger = logging.getLogger(__name__)


# ========== 内置兜底默认值 ==========
# 数据库与 JSON 都没数据时使用的硬编码兜底，
# 与 init_rules.json 的 DEFAULT 规则保持完全一致。
_BUILTIN_DEFAULTS: Dict[str, Any] = {
    'injection': {
        'inj_pres_ratio': 0.65,
        'inj_time_coef': 4.0,
        'inj_time_min': 3.0,
        # 材料分支默认（其他材料）
        'inj_velo_ratio_thin': 0.35,
        'inj_velo_ratio_thick': 0.42,
        'inj_ratio_threshold': 100,
        'inj_ratio_coef': 500.0,
    },
    'vp_switch': {
        'base_posi_small': 10,
        'base_posi_large': 15,
        'base_posi_threshold_weight': 120,
    },
    'holding': {
        'hold_pres_base_ratio': 0.25,
        'hold_pres_thickness_factor': 10,
        'hold_pres_max_limit': 120,
        'hold_pres_inj_ratio': 0.65,
        'hold_velo_ratio': 0.15,
        'hold_time_min': 2.0,
        'hold_time_max': 10.0,
        # 保压时间策略默认（其他浇口）
        'hold_time_strategy': 'quadratic',
        'hold_time_linear_a': 0.5,
        'hold_time_linear_b': 0.1,
        'hold_time_area_coef': 2.0,
        'hold_time_quadratic_a': 0.3,
        'hold_time_quadratic_b': 0.6,
    },
    'cooling': {
        'cool_time_factor': 5.0,
        'cool_time_min': 5.0,
        'weight_factor_threshold': 100,
        'else_time': 1.5,
    },
    'metering': {
        'meter_pres_ratio_straight': 0.55,
        'meter_pres_ratio_locking': 0.6,
        'meter_speed_temp_ratio_min': 0.3,
        'meter_speed_temp_ratio_max': 0.75,
        'screw_speed_factor': 60.0,
    },
    'decompression': {
        'pre_decomp_mode': 0,
        'pst_decomp_mode': 0,
        'decomp_dist_ratio': 0.1,
        'decomp_dist_min': 2.0,
        'decomp_dist_max': 10.0,
    },
    'temperature': {
        'noz_temp_offset_straight': -5.0,
        'noz_temp_offset_locking': 0.0,
        'brl_temp_decrement_normal': 10.0,
        'brl_temp_decrement_high': 8.0,
        'brl_temp_stage_threshold': 7,
    },
    'mold_temp': {
        'PP': 40, 'PC': 80, 'ABS': 50, 'PC+ABS': 70, 'PC/ABS': 70,
        'PS': 40, 'PE': 40, 'LDPE': 40, 'HDPE': 40, 'LLDPE': 40,
        'PVC': 40, 'PA6': 60, 'PA66': 70, 'PA': 60, 'PET': 90,
        'default': 50,
    },
}


class InitRuleMatcher:
    """初始化规则匹配器（数据库版）

    Usage:
        matcher = InitRuleMatcher()
        coeffs = matcher.match({'polymer': {...}, 'product': {...}})
        inj_pres = max_inj_pres * coeffs['injection']['inj_pres_ratio']
    """

    def __init__(self, library_code: str = 'init_rules'):
        self.library_code = library_code
        self._cached_rules: Optional[List[Dict[str, Any]]] = None
        # 最近一次 match 命中的规则代码列表（按 priority 顺序）
        self.last_matched_codes: List[str] = []

    def match(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """匹配规则并返回合并后的嵌套系数字典

        Args:
            context: 匹配上下文
                {
                    'polymer': {'abbreviation': 'ABS', ...},
                    'product': {'gate_type': '点浇口', 'ave_thickness': 2.0, ...},
                    'machine': {...},
                }

        Returns:
            合并后的嵌套系数字典，结构如：
            {
                'injection': {'inj_pres_ratio': 0.65, ...},
                'holding':   {'hold_pres_base_ratio': 0.25, ...},
                ...
            }

        副作用：
            self.last_matched_codes 被填充为本次命中规则代码列表（按 priority 升序）。
        """
        self.last_matched_codes = []
        rules = self._load_rules()

        if not rules:
            return self._build_fallback(context)

        # 按 priority 升序排序
        sorted_rules = sorted(rules, key=lambda r: r.get('priority', 9999))

        matched_coefficients: Dict[str, Any] = {}

        for rule in sorted_rules:
            if not rule.get('is_active', True):
                continue
            if self._match_conditions(rule.get('conditions', []), context):
                matched_coefficients = self._merge_coefficients(
                    matched_coefficients,
                    rule.get('coefficients', {}),
                )
                code = rule.get('rule_code')
                if code:
                    self.last_matched_codes.append(code)

        logger.debug(f"InitRuleMatcher 命中规则: {self.last_matched_codes}")

        # 用内置默认兜底，确保所有必要键都存在
        return self._merge_coefficients(_BUILTIN_DEFAULTS, matched_coefficients)

    def reload(self) -> None:
        """清除缓存，强制下次 match 时重新加载"""
        self._cached_rules = None

    # ========== 数据加载 ==========

    def _load_rules(self) -> List[Dict[str, Any]]:
        """加载规则：先 DB，后 JSON；都不行返回空"""
        if self._cached_rules is not None:
            return self._cached_rules

        # 1. 数据库
        rules = self._load_from_db()
        if rules:
            logger.info(f"InitRuleMatcher: 从数据库加载 {len(rules)} 条规则")
            self._cached_rules = rules
            return rules

        # 2. JSON 文件
        rules = self._load_from_json()
        if rules:
            logger.info(f"InitRuleMatcher: 从 JSON 加载 {len(rules)} 条规则")
            self._cached_rules = rules
            return rules

        logger.warning("InitRuleMatcher: 数据库和 JSON 均无可用规则，将使用内置默认值")
        return []

    def _load_from_db(self) -> List[Dict[str, Any]]:
        try:
            from process.models.rules import RuleLibrary  # noqa
        except Exception as e:
            logger.debug(f"InitRuleMatcher: 导入 RuleLibrary 失败: {e}")
            return []

        try:
            library = RuleLibrary.objects.filter(
                library_code=self.library_code,
                is_active=True,
            ).first()
            if not library:
                return []

            qs = library.expert_rules.filter(is_active=True).values(
                'rule_code', 'rule_name', 'priority', 'is_active',
                'conditions', 'coefficients',
            )
            rules = list(qs)
            return rules
        except Exception as e:
            logger.warning(f"InitRuleMatcher: 数据库加载失败: {e}")
            return []

    def _load_from_json(self) -> List[Dict[str, Any]]:
        try:
            loader = InitRuleLoader()
            return loader.get_all_rules()
        except Exception as e:
            logger.warning(f"InitRuleMatcher: JSON 加载失败: {e}")
            return []

    # ========== 匹配逻辑（复用 InitRuleLoader 的实现） ==========

    @staticmethod
    def _match_conditions(conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """所有条件 AND 满足返回 True；无条件规则始终匹配"""
        if not conditions:
            return True

        for cond in conditions:
            field = cond.get('field', '')
            operator = cond.get('operator', 'exact')
            value = cond.get('value')
            field_value = InitRuleMatcher._get_field_value(field, context)
            if field_value is None:
                return False
            if not InitRuleMatcher._compare(field_value, operator, value):
                return False
        return True

    @staticmethod
    def _get_field_value(field: str, context: Dict[str, Any]) -> Any:
        """从上下文中提取字段值，支持嵌套字段（polymer.abbreviation 形式）"""
        parts = field.split('.')
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
            if value is None:
                return None
        return value

    @staticmethod
    def _compare(field_value: Any, operator: str, target: Any) -> bool:
        """单条件比较"""
        try:
            if operator == 'exact':
                return field_value == target
            if operator == 'in':
                return field_value in target
            if operator == 'not_in':
                return field_value not in target
            if operator == 'gte':
                return field_value >= target
            if operator == 'lte':
                return field_value <= target
            if operator == 'gt':
                return field_value > target
            if operator == 'lt':
                return field_value < target
        except TypeError:
            return False
        return False

    @staticmethod
    def _merge_coefficients(base: Dict[str, Any], addition: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并：嵌套 dict 递归合并，标量值由 addition 覆盖 base"""
        result = {k: v for k, v in (base or {}).items()}
        for key, value in (addition or {}).items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = InitRuleMatcher._merge_coefficients(result[key], value)
            else:
                result[key] = value
        return result

    # ========== 兜底 ==========

    def _build_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """DB 与 JSON 都拿不到数据时的纯内置默认值"""
        return {k: {kk: vv for kk, vv in v.items()} for k, v in _BUILTIN_DEFAULTS.items()}