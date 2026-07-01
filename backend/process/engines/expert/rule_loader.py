"""
工艺参数初始化规则加载器

从规则文件加载初始化规则，支持条件匹配和系数提取
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class InitRuleLoader:
    """初始化规则加载器"""

    _instance: Optional['InitRuleLoader'] = None
    _rules: List[Dict[str, Any]] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_rules()
        return cls._instance

    def _load_rules(self):
        """从规则文件加载规则"""
        rules_dir = Path(__file__).parent / 'expert_rules'
        rule_file = rules_dir / 'init_rules.json'

        if not rule_file.exists():
            logger.warning(f"规则文件不存在: {rule_file}")
            self._rules = []
            return

        try:
            with open(rule_file, encoding='utf-8') as f:
                data = json.load(f)
                self._rules = data.get('rules', [])
                logger.info(f"加载了 {len(self._rules)} 条初始化规则")
        except Exception as e:
            logger.error(f"加载规则文件失败: {e}")
            self._rules = []

    def reload(self):
        """重新加载规则"""
        self._load_rules()

    def match_rules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据上下文匹配规则

        Args:
            context: 匹配上下文，包含 polymer, product, machine 等信息
            {
                "polymer": {"abbreviation": "ABS", ...},
                "product": {"gate_type": "点浇口", ...},
                "machine": {"power_method": "液压机", ...}
            }

        Returns:
            合并后的系数字典
        """
        if not self._rules:
            logger.warning("没有可用的规则")
            return {}

        # 按优先级排序
        sorted_rules = sorted(self._rules, key=lambda r: r.get('priority', 9999))

        matched_coefficients = {}

        for rule in sorted_rules:
            if not rule.get('is_active', True):
                continue

            # 检查条件是否匹配
            if self._match_conditions(rule.get('conditions', []), context):
                # 合并系数
                matched_coefficients = self._merge_coefficients(
                    matched_coefficients,
                    rule.get('coefficients', {})
                )
                logger.debug(f"匹配规则: {rule['rule_code']}")

        return matched_coefficients

    def _match_conditions(self, conditions: List[Dict], context: Dict) -> bool:
        """
        检查条件是否匹配

        无条件规则（conditions为空）始终匹配
        """
        if not conditions:
            return True

        for cond in conditions:
            field = cond.get('field', '')
            operator = cond.get('operator', 'exact')
            value = cond.get('value')

            # 提取字段值
            field_value = self._get_field_value(field, context)
            if field_value is None:
                return False

            # 根据操作符检查匹配
            if operator == 'exact':
                if field_value != value:
                    return False
            elif operator == 'in':
                if field_value not in value:
                    return False
            elif operator == 'not_in':
                if field_value in value:
                    return False
            elif operator == 'gte':
                if field_value < value:
                    return False
            elif operator == 'lte':
                if field_value > value:
                    return False
            elif operator == 'gt':
                if field_value <= value:
                    return False
            elif operator == 'lt':
                if field_value >= value:
                    return False

        return True

    def _get_field_value(self, field: str, context: Dict) -> Any:
        """从上下文中提取字段值，支持嵌套字段"""
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

    def _merge_coefficients(
        self,
        base: Dict[str, Any],
        addition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        深度合并系数字典

        优先使用新值，但不覆盖已有的嵌套字典
        """
        result = base.copy()

        for key, value in addition.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_coefficients(result[key], value)
            else:
                result[key] = value

        return result

    def get_rule(self, rule_code: str) -> Optional[Dict[str, Any]]:
        """根据规则编码获取规则"""
        for rule in self._rules:
            if rule.get('rule_code') == rule_code:
                return rule
        return None

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        return self._rules.copy()
