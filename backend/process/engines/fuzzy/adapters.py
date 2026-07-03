"""
RuleMethod / RuleKeyword 适配层

将 DB 模型与 fuzzy_core 算法层的数据结构互转。

主要职责：
- RuleMethodAdapter：RuleMethod.rule_content JSON ↔ 算法层可解析的规则字符串
- RuleKeywordAdapter：RuleKeyword (Django model) ↔ FuzzyFeature 输入 dict
"""

from typing import Optional, List, Dict, Any

from process.models.rules import RuleKeyword


# ============================================================================
# RuleMethodAdapter: JSON ↔ 规则字符串
# ============================================================================

class RuleMethodAdapter:
    """RuleMethod.rule_content JSON ↔ fuzzykit 规则字符串。

    算法层（FuzzyRule / NumTskRule）期望的字符串格式：
        'IF X1_low AND X2_high THEN Y1_add_10 AND Y2_reduce_5%'

    数据库存储的 JSON 格式（参见 fuzzy-engine-reference.md §5）：
        {
            "conditions": [
                {"param": "hold_time", "fuzzy_level": "low"},
            ],
            "adjustments": [
                {"type": "param", "param": "hold_time",
                 "action": "add", "value": 4, "value_type": "absolute"},
            ],
        }
    """

    @staticmethod
    def to_rule_string(rule_method) -> str:
        """RuleMethod 模型实例（或 dict）→ fuzzykit 规则字符串。"""
        # 兼容传入 ORM 实例或 dict
        if hasattr(rule_method, 'rule_content'):
            content = rule_method.rule_content or {}
            defect_name = getattr(rule_method, 'defect_name', '')
        else:
            content = rule_method.get('rule_content', {}) or {}
            defect_name = rule_method.get('defect_name', '')

        conditions = content.get('conditions', []) or []
        adjustments = content.get('adjustments', []) or []

        cond_parts = []
        # 优先把缺陷名写入前置条件（与老 fuzzykit 习惯一致）
        if defect_name:
            # 取第一个 condition 中的 fuzzy_level 作严重程度；若没有则用 'low'
            severity = 'low'
            for c in conditions:
                if c.get('fuzzy_level'):
                    severity = c['fuzzy_level']
                    break
            cond_parts.append(f'{defect_name.upper()}_{severity}')

        for cond in conditions:
            if 'fuzzy_level' in cond and cond.get('param'):
                # 已作为 defect 处理过的不再加（避免重复）
                if cond.get('param') == defect_name:
                    continue
                cond_parts.append(f"{cond['param']}_{cond['fuzzy_level']}")
            elif cond.get('defect') and cond.get('fuzzy_level'):
                # 显式 defect 条件
                cond_parts.append(f"{cond['defect']}_{cond['fuzzy_level']}")

        if not cond_parts:
            cond_parts = ['True']  # 默认无条件规则

        adj_parts = []
        for adj in adjustments:
            if adj.get('type') == 'tip':
                continue  # 弹窗规则走 ParticularRules

            param = adj['param']
            action = adj.get('action', 'add')
            value_type = adj.get('value_type', 'absolute')

            if value_type == 'percent' or action.endswith('_pct'):
                # 百分比规则：add_5% / reduce_10%
                value = adj.get('value', 0)
                base_action = action.replace('_pct', '')
                adj_parts.append(f'{param}_{base_action}_{value}%')
            elif 'level' in adj:
                # 模糊级 add_low / reduce_mid
                adj_parts.append(f"{param}_{action}_{adj['level']}")
            elif 'value' in adj:
                adj_parts.append(f"{param}_{action}_{adj['value']}")

        cond_str = ' AND '.join(cond_parts) if cond_parts else 'True'
        adj_str = ' AND '.join(adj_parts) if adj_parts else ''

        if adj_str:
            return f'IF {cond_str} THEN {adj_str}'
        return f'IF {cond_str} THEN {param}_adjust_adjust'

    @staticmethod
    def from_rule_string(rule_str: str, defect_name: Optional[str] = None) -> Dict[str, Any]:
        """规则字符串 → JSON。"""
        words = rule_str.strip().split()
        is_pre = False
        conditions = []
        adjustments = []

        for phase in words:
            if phase == 'IF':
                is_pre = True
                continue
            if phase in ('Then', 'THEN'):
                is_pre = False
                continue
            if phase == 'AND':
                continue

            parts = phase.split('_')
            if len(parts) < 2:
                continue

            name = parts[0]
            level_or_action = parts[1]
            third = parts[2] if len(parts) > 2 else None

            if is_pre:
                # condition
                conditions.append({
                    'param': name if third else None,
                    'defect': name if not third else None,
                    'fuzzy_level': third or level_or_action,
                })
            else:
                # adjustment
                if third is None:
                    # popup 风格：phase_adjust
                    continue
                if third.endswith('%'):
                    value = float(third.rstrip('%'))
                    adjustments.append({
                        'type': 'param',
                        'param': name,
                        'action': level_or_action,
                        'value': value,
                        'value_type': 'percent',
                    })
                elif third in ('low', 'mid', 'high', 'very_low', 'very_high',
                                'level1', 'level2', 'level3', 'level4', 'level5'):
                    # 模糊级结论
                    adjustments.append({
                        'type': 'param',
                        'param': name,
                        'action': level_or_action,
                        'level': third,
                    })
                else:
                    # 数值结论
                    try:
                        value = float(third)
                    except ValueError:
                        continue
                    adjustments.append({
                        'type': 'param',
                        'param': name,
                        'action': level_or_action,
                        'value': value,
                        'value_type': 'absolute',
                    })

        return {
            'conditions': _dedup_conditions(conditions),
            'adjustments': adjustments,
            'defect_name': defect_name,
        }


def _dedup_conditions(conditions: List[Dict]) -> List[Dict]:
    """按 (param/defect, fuzzy_level) 去重。"""
    seen = set()
    deduped = []
    for c in conditions:
        key = (c.get('param'), c.get('defect'), c.get('fuzzy_level'))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return deduped


# ============================================================================
# RuleKeywordAdapter: RuleKeyword ↔ FuzzyFeature 输入 dict
# ============================================================================

class RuleKeywordAdapter:
    """RuleKeyword 模型 → FuzzyFeature 输入 dict。

    FuzzyFeature / NumTskRuleNet 期望的 keyword dict 格式：
        {
            'keyword': 'inj_pres_1',
            'lvl': 3,
            'min_val': 0,
            'max_val': 200,
            'step': 10,
        }
    """

    @staticmethod
    def to_fuzzy_dict(keyword) -> Dict[str, Any]:
        """RuleKeyword 实例 → fuzzy dict。"""
        if isinstance(keyword, dict):
            return RuleKeywordAdapter._dict_to_fuzzy_dict(keyword)
        return RuleKeywordAdapter._orm_to_fuzzy_dict(keyword)

    @staticmethod
    def _orm_to_fuzzy_dict(keyword: RuleKeyword) -> Dict[str, Any]:
        step = getattr(keyword, 'step', None)
        if step is None:
            # 兜底：step 字段为空时使用区间范围的 1/3
            try:
                span = float(keyword.range_max) - float(keyword.range_min)
                step = max(span / 3.0, 0.01)
            except Exception:
                step = 1.0
        return {
            'keyword': keyword.keyword_name,
            'lvl': int(keyword.fuzzy_level or 3),
            'min_val': float(keyword.range_min),
            'max_val': float(keyword.range_max),
            'step': float(step),
        }

    @staticmethod
    def _dict_to_fuzzy_dict(keyword: Dict[str, Any]) -> Dict[str, Any]:
        step = keyword.get('step')
        if step is None:
            try:
                span = float(keyword['range_max']) - float(keyword['range_min'])
                step = max(span / 3.0, 0.01)
            except Exception:
                step = 1.0
        return {
            'keyword': keyword.get('keyword_name') or keyword.get('keyword'),
            'lvl': int(keyword.get('fuzzy_level', 3)),
            'min_val': float(keyword.get('range_min', 0)),
            'max_val': float(keyword.get('range_max', 1)),
            'step': float(step),
        }

    @staticmethod
    def get_keywords_by_names(names: List[str]) -> List[Dict[str, Any]]:
        """按参数名批量查询 RuleKeyword，返回 fuzzy dict 列表。"""
        keywords = RuleKeyword.objects.filter(keyword_name__in=names)
        return [RuleKeywordAdapter.to_fuzzy_dict(kw) for kw in keywords]


# ============================================================================
# 模块自检
# ============================================================================

if __name__ == '__main__':
    # JSON → 规则字符串
    rm = {
        'defect_name': 'SHORTSHOT',
        'rule_content': {
            'conditions': [
                {'param': 'hold_time', 'fuzzy_level': 'low'},
            ],
            'adjustments': [
                {'type': 'param', 'param': 'hold_time',
                 'action': 'add', 'value': 4, 'value_type': 'absolute'},
            ],
        },
    }
    s = RuleMethodAdapter.to_rule_string(rm)
    print('== JSON → string ==:', s)

    parsed = RuleMethodAdapter.from_rule_string(s, defect_name='SHORTSHOT')
    print('== string → JSON ==:', parsed)
