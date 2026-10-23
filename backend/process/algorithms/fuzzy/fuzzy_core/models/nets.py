"""
模糊推理网络

本文件从 `old/mdprocess/utils/fuzzykit/fuzzy_core/models/nets.py` 迁移而来。

核心类（按【结论形态】分层，与 `fuzzy_algorithm.py` 的分流一致）：
- FuzzyFeature         特征模糊化（生产只用高斯；'tri' 分支因硬编码 'gauss' 不可达）
- FuzzyRule            Mamdani 规则解析（提示层用）
- FuzzyRuleNet         Mamdani 推理（提示层；结论为模糊等级，经 centroid 反模糊化）
- NumTskRule           数值结论规则解析（数值层用，生产主路径）
- NumTskRuleNet        零阶 T-S 推理（数值层，生产主路径）
- ParticularRules      检查/弹窗提示规则（纯文本建议）
- TskRuleNet           一阶代数式 T-S（占位死类，明确不做）

术语对齐（2026-10-22）：
  本文件原注释使用「工厂级 / 兜底层」——那是旧 HsMoldingService 的业务分层，
  迁入本项目后已失效。当前项目按【结论形态】分层（见 fuzzy_algorithm.py）：
    数值层 (numeric)  = 结论能算出数值    → NumTskRuleNet
    提示层 (advisory) = 结论是文本/模糊等级 → ParticularRules / FuzzyRuleNet
  ⚠️ 2026-10-22 实测：规则库 1646 条中，模糊等级结论 0 条 ⇒ FuzzyRuleNet
     代码路径已接线但**实际空跑**；99 条 adjust/popup 走 ParticularRules；
     1547 条数值结论走 NumTskRuleNet。

详细迁移对照与背景见 `backend/_dev_refs/fuzzy-engine-migration-design.md`。
"""

import logging
from collections import defaultdict

import numpy as np

from ..functional import gauss_mf, tri_mf, defuzz
from ..macros import (
    ACTION_MAP,
    ALL_LEVEL_WORDS,
    DEFECT_CONST,
    MIN_ACTIVATION_THRESHOLD,
    MAMDANI_SAMPLE_POINTS,
    EPSILON,
    resolve_bucket,          # ★ 档位→桶映射（按字段自己的档位词表定位）
)
from ..parsing import (
    classify_name as _classify_name,   # noqa: F401  保留旧名，历史 import 不断裂
    is_level_word,
    split_phase as _split_phase,       # noqa: F401  保留旧名，历史 import 不断裂
)


logger = logging.getLogger(__name__)


# ============================================================================
# 档位→桶解析
# ============================================================================

def _resolve_bucket_safe(lvl: int, word: str, where: str):
    """按字段的档位数解析桶索引；解析不了就显式告警并返回 None。

    档位→桶的映射**必须按字段自己的档位词表**定位：同一个 'high'
    在 3 档字段是桶 2（论域上界），在 5 档字段是桶 3（论域 75% 分位）。
    用全局静态 3 档表会让 5/7/9 档字段的门控整体错位一档。

    「禁止静默降级」：词表对不上时不能悄悄取错桶，必须留下可查的日志。
    返回 None 表示该前件建不了论域，调用方按"不作为门控"处理。
    """
    try:
        return resolve_bucket(lvl, word)
    except ValueError as e:
        logger.warning('[%s] 档位词 %r 无法映射到 lvl=%d 的桶：%s', where, word, lvl, e)
        return None


# ============================================================================
# 词法解析辅助
# ============================================================================

# 合法等级词全集（含前端/规则库用的 'medium' 与老 fuzzykit 的 'mid'）
_ALL_LEVEL_WORDS = set(ALL_LEVEL_WORDS)


# ============================================================================
# FuzzyFeature
# ============================================================================

class FuzzyFeature:
    """每一个特征模糊化表示类。

    用作规则条件词，储存原始数值、模糊化数值、对应的隶属度函数参数。

    Attributes
    ----------
    f_name : str
        特征名，一般为工艺参数名
    f_interval : list[float]
        特征取值区间
    f_membership_type : str
        'gauss' 或 'tri'
    f_level : int
        特征模糊划分数量 (3 或 5)
    f_type : str
        'process' 或 'defect'
    membership_dict : dict
        {degree_i: [均值/参数]}
    """

    def __init__(self, f_name, f_interval, f_membership_type='gauss', f_level=3, f_type='process'):
        self.f_type = f_type
        self.f_name = f_name
        self.f_interval = f_interval
        self.f_membership_type = f_membership_type
        self.f_level = f_level
        self.membership_dict = {}

        if f_membership_type == 'gauss':
            self.membership_func = gauss_mf
            sigmas = np.array([(f_interval[1] - f_interval[0]) / (2 * (f_level - 1))] * f_level)
            means = np.r_[
                f_interval[0],
                np.quantile(f_interval, np.arange(1, f_level - 1) / (f_level - 1)),
                f_interval[1],
            ]
            for i in range(f_level):
                self.membership_dict['degree_' + str(i)] = [float(means[i]), float(sigmas[i])]

        elif f_membership_type == 'tri':
            self.membership_func = tri_mf
            quantiles_inner = np.quantile(f_interval, np.arange(0, f_level - 1) / (f_level - 1))
            quantiles_outer = np.quantile(f_interval, np.arange(1, f_level) / (f_level - 1))
            a_values = np.r_[f_interval[0], quantiles_inner]
            b_values = np.r_[np.quantile(f_interval, np.arange(0, f_level) / (f_level - 1))]
            c_values = np.r_[quantiles_outer, f_interval[1]]
            for i in range(f_level):
                self.membership_dict['degree_' + str(i)] = [
                    float(a_values[i]), float(b_values[i]), float(c_values[i]),
                ]

        else:
            raise ValueError(f'不支持的隶属度函数类型: {f_membership_type}')

    def get_value_by_level(self, x, level):
        """获取给定值 x 在指定模糊级别上的隶属度值。"""
        if 0 <= level < self.f_level:
            degree_key = 'degree_' + str(level)
            return self.membership_func(x, *self.membership_dict[degree_key])
        raise ValueError('level 超出定义范围！')

    def get_all_value(self, x):
        """返回 x 对所有模糊级别的隶属度数组。"""
        return np.array([self.get_value_by_level(x, i) for i in range(self.f_level)])


# ============================================================================
# FuzzyRule: Mamdani 规则（提示层用）
# ============================================================================

class FuzzyRule:
    """规则库中的每一条全模糊规则的表示与计算类。

    规则字符串格式：
        IF X1_low AND X2_high THEN Y1_add_low AND Y2_reduce_mid

    解析后存储为：
        r_preconditions: {param_name: {name, level, p_type}}
        r_solutions:     {param_name: {name, action, level, s_type}}
    """

    def __init__(self, rule_string: str = ''):
        self.r_rule = rule_string
        self.r_preconditions, self.r_solutions = self._rule_process(rule_string)

    def _rule_process(self, rule: str):
        """解析规则字符串，分离条件和解决方法。"""
        words_list = rule.strip().split()
        r_preconditions = {}
        r_solutions = {}
        is_pre = False
        for phase in words_list:
            if phase == 'IF':
                is_pre = True
            elif phase in ('Then', 'THEN'):
                is_pre = False
            elif phase == 'AND':
                continue
            else:
                info = _split_phase(phase)
                if is_pre:
                    name = info['name']
                    level = info['level']
                    r_preconditions[name] = {
                        'name': name,
                        'level': level,
                        'p_type': _classify_name(name),
                    }
                else:
                    name = info['name']
                    action = info.get('action', '')
                    value = info.get('value', '')
                    # 老 fuzzykit：value 在 sol_dict 中存为 'level' 字段
                    r_solutions[name] = {
                        'name': name,
                        'action': ACTION_MAP.get(action, 0),
                        'level': value,
                        's_type': 'process',
                    }
        return r_preconditions, r_solutions

    def __repr__(self):
        return self.r_rule


# ============================================================================
# FuzzyRuleNet: Mamdani 网络（提示层）
# ============================================================================

class FuzzyRuleNet:
    """Mamdani 推理网络（提示层）。

    处理'条件模糊 + 结论模糊级别'规则，结果经 centroid 反模糊化得到精确值。

    ⚠️ 2026-10-22 实测：当前规则库中模糊等级结论 0 条 ⇒ 本引擎实际空跑，
       代码路径已接线但无数据流入。
    """

    def __init__(self, rule_array: list, keyword_array: list):
        self.rule_dict = None
        self.pre_set = None
        self.sol_set = None
        self.rule_nums = None
        self.pre_dict = None
        self.sol_dict = None
        self.connected_matrix = None
        self.solution_matrix = None
        self.resolve_input_paras(rule_array, keyword_array)
        self._construct_ruleNet()

    def resolve_input_paras(self, rule_array: list, keyword_array: list):
        """解析传入规则 + 关键词，构建 pre_dict / sol_dict。"""
        self.rule_dict = {}
        self.pre_set = set()
        self.sol_set = set()
        self.rule_nums = len(rule_array)

        for i, rule in enumerate(rule_array):
            self.rule_dict[i] = FuzzyRule(rule.get('rule_description'))
            self.pre_set.update(self.rule_dict[i].r_preconditions.keys())
            self.sol_set.update(self.rule_dict[i].r_solutions.keys())

        self.pre_dict = defaultdict(dict)
        self.sol_dict = defaultdict(dict)

        for item in keyword_array:
            if item['keyword'] in self.pre_set:
                self.pre_dict[item['keyword']].update({
                    'lvl': item['lvl'],
                    'min_val': item['min_val'],
                    'max_val': item['max_val'],
                    'step': item['step'],
                })
            if item['keyword'] in self.sol_set:
                self.sol_dict[item['keyword']].update({
                    'lvl': item['lvl'],
                    'min_val': item['min_val'],
                    'max_val': item['max_val'],
                    'step': item['step'],
                })

    def _construct_ruleNet(self):
        """构建规则网络（连接矩阵 + 解决方案矩阵）。"""
        # 条件变量模糊集合
        idx = 0
        for k, v in self.pre_dict.items():
            k_dict = self.pre_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(
                k, [k_dict['min_val'], k_dict['max_val']],
                f_level=k_dict['lvl'], f_membership_type='gauss',
            )
            idx += k_dict['lvl']

        # 结果变量模糊集合（区间是 [0, step]）
        idx = 0
        for k, v in self.sol_dict.items():
            k_dict = self.sol_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(
                k, [0., k_dict['step']],
                f_level=k_dict['lvl'], f_membership_type='gauss',
            )
            idx += k_dict['lvl']

        rows = self.rule_nums
        p_cols = sum(self.pre_dict[k]['lvl'] for k in self.pre_dict)
        s_cols = sum(self.sol_dict[k]['lvl'] for k in self.sol_dict)
        self.connected_matrix = np.zeros(shape=(rows, p_cols))
        self.solution_matrix = np.zeros(shape=(rows, s_cols))

        for row_idx, rule in self.rule_dict.items():
            for name, value in rule.r_preconditions.items():
                level = str(value.get('level', '')).lower()
                if not is_level_word(level):
                    # 不可判级的前件（'worse' / 缺陷名）→ 不作为门控
                    continue
                if name in self.pre_dict:
                    bucket = _resolve_bucket_safe(
                        self.pre_dict[name]['lvl'], level, 'FuzzyRuleNet.pre')
                    if bucket is None:
                        continue
                    p_col_idx = self.pre_dict[name]['index'] + bucket
                    self.connected_matrix[row_idx][p_col_idx] = 1

            for name, value in rule.r_solutions.items():
                level = str(value.get('level', '')).lower()
                if not is_level_word(level):
                    # Mamdani 层的结论必须是模糊等级（add_low / reduce_mid），
                    # 数值结论（add_2）属于工厂级 TSK 层
                    continue
                if name in self.sol_dict:
                    # ⚠️ 结论侧用【输出变量自己的档位数】sol_dict[name]['lvl']
                    bucket = _resolve_bucket_safe(
                        self.sol_dict[name]['lvl'], level, 'FuzzyRuleNet.sol')
                    if bucket is None:
                        continue
                    s_col_idx = self.sol_dict[name]['index'] + bucket
                    self.solution_matrix[row_idx][s_col_idx] = 1 * value['action']

    def inference(self, x):
        """Mamdani 推理。

        Parameters
        ----------
        x : dict
            变量名 -> 精确值

        Returns
        -------
        list of (param_name, value, (activation, rule))
        """
        # 兼容老 fuzzykit 的 MT 缺陷名习惯
        if x.get('MT') is None:
            x['MT'] = 0

        num_degrees = self.connected_matrix.shape[1]
        membership_degrees = np.zeros(shape=(num_degrees,)) + 0.01
        for k in x:
            if k not in self.pre_set:
                continue
            if not self.pre_dict[k]:
                continue
            idx = self.pre_dict[k]['index']
            f_k = self.pre_dict[k]['memberships']
            for i in range(f_k.f_level):
                membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)

        # 激活度（Mamdani 用 min 连接）
        rule_matrix = self.connected_matrix * membership_degrees
        rule_activations = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(self.rule_nums):
            # ★ 用【连接关系】取门控列，而不是用【隶属度非零】：
            #   后者会把隶属度恰为 0 的门控踢出 min ⇒
            #   「门控不满足」被当成了「门控不存在」⇒ 规则反而激活。
            #   语义（2026-10-23 拍板）：隶属度 0 ⇒ 视为门控不满足 ⇒ 激活度 0。
            gate_cols = np.flatnonzero(self.connected_matrix[i])
            if gate_cols.size == 0:
                continue
            conditions = rule_matrix[i, gate_cols]
            rule_activations[i] = np.min(conditions)

        # 输出聚合与反模糊化
        points = MAMDANI_SAMPLE_POINTS
        outputs_matrix = None
        rule_to_outputs = np.zeros(shape=(self.solution_matrix.shape[1],))

        for k in self.sol_dict:
            idx = self.sol_dict[k]['index']
            step = self.sol_dict[k]['step']
            k_samples = np.linspace(0, step, points)
            lvl = self.sol_dict[k]['lvl']
            action_selected = -1
            rule_selected_list = [False] * self.rule_nums
            for i in range(lvl):
                k_fuzzy_points = self.sol_dict[k]['memberships'].get_value_by_level(k_samples, i)
                if outputs_matrix is None:
                    outputs_matrix = k_fuzzy_points.reshape(1, -1)
                else:
                    outputs_matrix = np.vstack([outputs_matrix, k_fuzzy_points.reshape(1, -1)])

                rules_by_degree = self.solution_matrix[:, idx + i] != 0
                if rules_by_degree.any():
                    selected_values = np.where(rules_by_degree, rule_activations, -1)
                    rule_to_outputs[idx + i] = np.max(selected_values)
                    rule_selected_list[int(np.argmax(selected_values))] = True

            final_rule = int(np.argmax(np.where(rule_selected_list, rule_activations, -1)))
            final_action = self.rule_dict[final_rule].r_solutions[k]['action']
            self.sol_dict[k]['action'] = final_action
            self.sol_dict[k]['reason'] = final_rule

        # 无效激活过滤
        for k in self.sol_dict:
            idx = self.sol_dict[k]['index']
            lvl = self.sol_dict[k]['lvl']
            degree_values = rule_to_outputs[idx:idx + lvl]
            if np.sum(degree_values) < MIN_ACTIVATION_THRESHOLD:
                rule_to_outputs[idx:idx + lvl] = 0.

        # 反模糊化
        res = np.zeros(shape=(len(self.sol_set),))
        outputs = np.fmin(outputs_matrix.T, rule_to_outputs).T
        i = 0
        for k in self.sol_dict:
            idx = self.sol_dict[k]['index']
            lvl = self.sol_dict[k]['lvl']
            step = self.sol_dict[k]['step']
            if not rule_to_outputs[idx:idx + lvl].any():
                i += 1
                continue
            k_samples = np.linspace(0, step, points)
            k_aggregated = np.max(outputs[idx:idx + lvl], axis=0)
            res[i] = defuzz(k_samples, k_aggregated, 'centroid')
            res[i] *= self.sol_dict[k]['action']
            i += 1

        results = list(zip(
            self.sol_dict.keys(),
            res,
            map(
                lambda x: (rule_activations[x['reason']], self.rule_dict[x['reason']]),
                self.sol_dict.values(),
            ),
        ))
        # 按激活度降序
        return sorted(results, key=lambda x: -x[-1][0])

    def predict(self, x, top_k: int = 1):
        results = self.inference(x)
        if len(results) <= top_k:
            return results
        return results[:top_k]

    def predict_json(self, x, top_k: int = 1):
        results = self.predict(x, top_k=top_k)
        return {item[0]: item[1] for item in results}


# ============================================================================
# NumTskRule: 数值结论规则（数值层用）
# ============================================================================

class NumTskRule:
    """规则库中的每一条具体数值形式的 TSK 模糊规则的表示与计算类。

    规则字符串解析后生成：
      r_preconditions: {param_name: {name, level, p_type}}
      r_solutions:     {param_name: {name, action, level, s_type}}
                        或 {param_name: {name, parameter_vector, ratio_vector, s_type}}
      r_extra:         {原短语: value}（弹窗规则）

    支持三种结论形式：
      1. _add_10 / _reduce_5      → 绝对数值结论
      2. _add_5% / _reduce_10%   → 百分比数值结论
      3. _popup_xxx              → 弹窗特殊规则
    """

    def __init__(self, rule_string: str = ''):
        self.r_rule = rule_string
        self.r_preconditions, self.r_solutions, self.r_extra = self._rule_process(rule_string)

    def _rule_process(self, rule: str):
        words_list = rule.strip().split()
        r_preconditions = {}
        r_solutions = {}
        r_extra = {}
        is_pre = False
        for phase in words_list:
            if phase == 'IF':
                is_pre = True
            elif phase in ('Then', 'THEN'):
                is_pre = False
            elif phase == 'AND':
                continue
            else:
                if is_pre:
                    info = _split_phase(phase)
                    name = info['name']
                    level = info['level']
                    r_preconditions[name] = {
                        'name': name,
                        'level': level,
                        'p_type': _classify_name(name),
                    }
                else:
                    # 结论区域：可能是 <name>_add_xxx / _reduce_xxx / _popup_xxx
                    info = _split_phase(phase)
                    action = info.get('action', '')
                    name = info['name']
                    value = info.get('value', '')

                    if action == 'popup':
                        # 弹窗规则结论：仅作 r_extra 提示，原 fuzzykit 也仅存于 r_extra
                        r_extra[phase] = value
                    elif action in ('add', 'reduce', 'adjust'):
                        r_solutions[name] = {
                            'name': name,
                            'action': ACTION_MAP.get(action, 0),
                            'level': value,
                            's_type': 'process',
                        }
                    elif info.get('kind') == 'algebra':
                        # 代数式结论（极少见，预留接口）
                        expressions = phase.split('=')
                        items = expressions[1].split('+')
                        parameter_vector = np.zeros(len(items))
                        ratio_vector = np.zeros(len(items))
                        for i, item_str in enumerate(items):
                            item = item_str.split('*')
                            ratio = item[0]
                            if '(' in ratio or ')' in ratio:
                                ratio_vector[i] = float(ratio[1:-1])
                            else:
                                ratio_vector[i] = float(ratio)
                        r_solutions[expressions[0]] = {
                            'name': expressions[0],
                            'parameter_vector': parameter_vector,
                            'ratio_vector': ratio_vector,
                            's_type': 'process',
                        }
        return r_preconditions, r_solutions, r_extra

    def __repr__(self):
        return self.r_rule


# ============================================================================
# NumTskRuleNet: 零阶 T-S 网络（数值层，生产主路径）
# ============================================================================

class NumTskRuleNet:
    """数值结论零阶 T-S 推理网络（数值层，生产主路径）。

    处理'条件模糊 + 结论数值/百分比'规则：
      1) 隶属度层
      2) 规则激活（prod 连接）
      3) 归一化 + priority 加权
      4) 结论层（sol_matrix × cur_params，百分比规则乘当前值）
    """

    def __init__(self, rule_array: list, keyword_array: list, priority_array: list):
        self.rule_dict = None
        self.pre_set = None
        self.sol_set = None
        self.rule_nums = None
        self.pre_dict = None
        self.sol_dict = None
        self.extra_dict = {}
        # 数值规则为 0，百分比规则为 1
        self.rule_classify = []
        self.rule_solution = []
        self.priority_array = priority_array
        self.resolve_input_paras(rule_array, keyword_array)
        self.connected_matrix = None
        self.solution_matrix = None
        self.percent_set = None
        self._construct_numtskruleNet()

    def resolve_input_paras(self, rule_array: list, keyword_array: list):
        """解析传入的规则和关键词。

        规则筛选原则（2026-10-20 修正）：
        - 只排除**结论是检查/弹窗**的规则（`X_adjust_提示语`）：这类规则的结论
          不是数值，放进数值推理层会产生 9999.9 的垃圾值。
        - 旧实现是"规则串里出现 worse 就整条跳过"，但规则库里 154 条含 worse
          的规则中有 55 条结论是数值（`X_reduce_2`），worse 只是前件里的人工
          判断词（"该参数不合理"）。按旧逻辑跳过会：
            1) 白白丢掉 55 条可用的数值规则；
            2) 让 rule_dict 的下标出现空洞，而矩阵按 rule_nums 行开，
               空洞之后的规则行号与矩阵行错位（甚至越界被丢）；
            3) `self.rule_dict[i]` 取不到被跳过的规则 → KeyError，整个推理崩掉。
          现在改为：被排除的规则不再占用下标（重新连续编号），priority 同步对齐。
        """
        self.rule_dict = {}
        self.pre_set = set()
        self.sol_set = set()
        self.rule_solution = []
        self.rule_classify = []
        kept_priorities = []

        for orig_idx, rule in enumerate(rule_array):
            desc = rule.get('rule_description', '')
            num_rule = NumTskRule(desc)
            if self._is_check_rule(num_rule):
                # 结论是检查/弹窗类（adjust / popup）：不参与数值推理
                continue

            idx = len(self.rule_dict)
            self.rule_dict[idx] = num_rule
            # 数值规则为 0，百分比规则为 1
            self.rule_classify.append(1 if '%' in desc else 0)
            if orig_idx < len(self.priority_array):
                kept_priorities.append(self.priority_array[orig_idx])
            else:
                kept_priorities.append(1.0)
            self.pre_set.update(num_rule.r_preconditions.keys())
            self.sol_set.update(num_rule.r_solutions.keys())
            # 无结论的规则也要占位，否则 rule_solution 与 rule_dict 下标错位
            self.rule_solution.append(
                list(num_rule.r_solutions.keys())[0] if num_rule.r_solutions else None
            )

        self.rule_nums = len(self.rule_dict)
        self.priority_array = kept_priorities

        self.pre_dict = defaultdict(dict)
        self.sol_dict = defaultdict(dict)

        for item in keyword_array:
            if item['keyword'] in self.pre_set:
                self.pre_dict[item['keyword']].update({
                    'lvl': item['lvl'],
                    'min_val': item['min_val'],
                    'max_val': item['max_val'],
                    'step': item['step'],
                })
            if item['keyword'] in self.sol_set:
                self.sol_dict[item['keyword']].update({
                    'lvl': item['lvl'],
                    'min_val': item['min_val'],
                    'max_val': item['max_val'],
                    'step': item['step'],
                })

    @staticmethod
    def _is_check_rule(num_rule) -> bool:
        """规则结论是否是检查/弹窗类（`X_adjust_提示语` / `X_popup_xxx`）。

        这类规则的结论不是数值（弹窗标记值为 9999.9），不能进数值推理层。
        """
        if num_rule.r_extra:
            return True
        return any(sol.get('action') == -2 for sol in num_rule.r_solutions.values())

    def _construct_numtskruleNet(self):
        """构建网络（连接矩阵 + 解决方案矩阵）。"""
        # 条件变量
        idx = 0
        for k, v in self.pre_dict.items():
            k_dict = self.pre_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(
                k, [k_dict['min_val'], k_dict['max_val']],
                f_level=k_dict['lvl'], f_membership_type='gauss',
            )
            idx += k_dict['lvl']

        # 结果变量（TSK 模式：输出为精确数值，不需隶属度函数）
        idx = 0
        for k, v in self.sol_dict.items():
            k_dict = self.sol_dict[k]
            k_dict['index'] = idx
            # TSK 不构造 sol_dict[k]['memberships']（输出走 solution_matrix 直接算）
            idx += 1

        rows = self.rule_nums
        p_cols = sum(self.pre_dict[k]['lvl'] for k in self.pre_dict)
        s_cols = sum(1 for _ in self.sol_dict)  # TSK 每个输出变量仅占 1 列
        self.connected_matrix = np.zeros(shape=(rows, p_cols))
        self.solution_matrix = np.zeros(shape=(rows, s_cols))
        self.percent_set = []

        for row_idx, rule in self.rule_dict.items():
            for name, value in rule.r_preconditions.items():
                level = str(value.get('level', '')).lower()
                if not is_level_word(level):
                    # 不可判级的前件，不作为门控：
                    #   - 'worse'：人工判断词（"该参数不合理"），没有隶属度可言
                    #   - 缺陷名：缺陷程度在规则匹配阶段（defect_code + level）
                    #     已经保证，缺陷本身也没有数值论域
                    continue
                if not self.pre_dict.get(name):
                    # 无 RuleKeyword 元数据 → 建不了论域 → 不作为门控
                    logger.debug('[NumTskRuleNet] pre_dict 中没有 %s，跳过该前件', name)
                    continue
                # ★ 按【该字段自己的档位数】取桶：同一个 'high' 在 3 档字段是桶 2，
                #   在 5 档字段是桶 3（论域 75% 分位）。用全局静态表会整体错位一档。
                bucket = _resolve_bucket_safe(
                    self.pre_dict[name]['lvl'], level, 'NumTskRuleNet.pre')
                if bucket is None:
                    continue
                p_col_idx = self.pre_dict[name]['index'] + bucket
                if row_idx < len(self.connected_matrix):
                    self.connected_matrix[row_idx][p_col_idx] = 1
                else:
                    logger.error(
                        f"index {row_idx} is out of bounds for axis 0 with size {len(self.connected_matrix)}"
                    )

            for name, value in rule.r_solutions.items():
                if not self.sol_dict.get(name):
                    # 结论参数无 RuleKeyword 元数据 → 调整量无处安放，丢弃该结论
                    logger.debug('[NumTskRuleNet] sol_dict 中没有 %s，跳过该结论', name)
                    continue
                s_col_idx = self.sol_dict[name]['index']
                # 特殊规则结论（弹窗）
                if value.get('action') == -2:
                    self.solution_matrix[row_idx][s_col_idx] = 9999.9
                else:
                    if row_idx < len(self.solution_matrix):
                        if '%' in value['level']:
                            self.percent_set.append(name)
                            self.solution_matrix[row_idx][s_col_idx] = (
                                float(value['level'].rstrip('%')) * value['action'] / 100
                            )
                        else:
                            self.solution_matrix[row_idx][s_col_idx] = (
                                float(value['level']) * value['action']
                            )
                    else:
                        logger.error(
                            f"index {row_idx} is out of bounds for axis 0 with size {len(self.solution_matrix)}"
                        )

            for name, value in rule.r_extra.items():
                self.extra_dict[name] = value

    def tsk_inference(self, x, priority_array=None):
        """执行四层零阶 TSK 推理。

        Parameters
        ----------
        x : dict
            变量名 -> 精确值
        priority_array : list[float], optional
            优先级数组（与 rule_array 等长）。默认用 self.priority_array。

        Returns
        -------
        (results, extra_dict)
            results: [(rule_str, weighted_activation, {param: value}), ...] 按激活度降序
            extra_dict: 弹窗规则文本
        """
        if priority_array is None:
            priority_array = self.priority_array

        # 第一层（隶属度层）
        num_degrees = self.connected_matrix.shape[1]
        membership_degrees = np.zeros(shape=(num_degrees,)) + EPSILON
        for k in x:
            if k not in self.pre_set:
                continue
            if not self.pre_dict[k]:
                continue
            idx, f_k = self.pre_dict[k]['index'], self.pre_dict[k]['memberships']
            for i in range(f_k.f_level):
                membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)

        # 第二层（规则层）
        rule_matrix = self.connected_matrix * membership_degrees
        rule_activations = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(self.rule_nums):
            # ★ 用【连接关系】取门控列，而不是用【隶属度非零】：
            #   后者会把隶属度恰为 0 的门控踢出乘积 ⇒
            #   「门控不满足」被当成了「门控不存在」⇒ **规则反而激活**。
            #   语义（2026-10-23 拍板）：隶属度 0 ⇒ 视为门控不满足 ⇒ 激活度 0。
            gate_cols = np.flatnonzero(self.connected_matrix[i])
            if gate_cols.size == 0:
                continue
            conditions = rule_matrix[i, gate_cols]
            rule_activations[i] = np.prod(conditions)  # 各项激活度相乘（TSK 风格）

        # 第三层（归一化 + priority 加权）
        activations_sum = np.sum(rule_activations)
        new_activations = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(0, rule_activations.size):
            new_activations[i] = rule_activations[i] / max(activations_sum, EPSILON)
        activations_with_priority = new_activations * np.asarray(priority_array)

        # ★ 无效激活过滤（与 Mamdani 的 MIN_ACTIVATION_THRESHOLD 语义对齐）：
        #   权重过低的规则不参与结论层 —— 否则它会以 delta≈0 的形式混进
        #   推荐列表（实测见过 confidence=1.68e-282 的项）。
        #   ⚠️ 阈值作用在【归一化×priority 之后】的权重上，**不能卡原始激活度**：
        #      原始激活度里含缺陷门控的 EPSILON=1e-7 因子，卡原始值会全军覆没。
        activations_with_priority[
            activations_with_priority < MIN_ACTIVATION_THRESHOLD] = 0.0

        # 第四层（结论层）
        cur_params = np.ones(shape=(self.connected_matrix.shape[0],))
        for i in range(self.rule_nums):
            if i >= len(self.rule_solution):
                continue
            k = self.rule_solution[i]
            if k is None or k not in x:
                continue
            if self.rule_classify[i] == 1:  # 百分比规则
                cur_params[i] = x[k]

        sol_matrix = self.solution_matrix.T * cur_params

        # 输出组装（只保留有效激活的规则）
        #
        # ⚠️ 三个列表必须**同步**构建：过滤掉的规则同时从
        #    rule_list / activations_out / calculate_list 中消失，
        #    否则 zip 会把规则与激活度错位配对。
        rule_list = []
        activations_out = []
        calculate_list = []
        sol_len = np.size(sol_matrix, 0)
        for i in range(0, self.rule_nums):
            if activations_with_priority[i] <= 0:
                # 无效激活 ⇒ 不产出结论：否则它会以 delta≈0 的形式混进推荐列表
                continue
            cal_dict = {}
            darray = self.solution_matrix[i, :]
            sol_darray = sol_matrix[:, i]
            for j in range(0, sol_len):
                if darray[j] != 0:
                    for k, v in self.sol_dict.items():
                        if j == v['index']:
                            cal_dict[k] = sol_darray[j]
            rule_list.append(self.rule_dict[i].r_rule)
            activations_out.append(float(activations_with_priority[i]))
            calculate_list.append(cal_dict)

        res = list(zip(rule_list, activations_out, calculate_list))
        res = sorted(res, key=lambda x: -float(x[1]))

        return res, self.extra_dict

    def predict(self, x, top_k: int = 1):
        results, extra_dict = self.tsk_inference(x, self.priority_array)
        if len(results) <= top_k:
            return results, extra_dict
        return results[:top_k], extra_dict

    def predict_json(self, x, top_k: int = 1):
        results, extra_dict = self.predict(x, top_k=top_k)
        json_results = {}
        for i in range(0, min(top_k, len(results))):
            json_results.update(results[i][2])
        return json_results, extra_dict


# ============================================================================
# ParticularRules: 弹窗/提示规则
# ============================================================================

class ParticularRules:
    """规则库中的特殊规则：前后件均非已有工艺参数，作弹窗处理。"""

    def __init__(self, import_list):
        self.adjust_rule_list = self._rule_process(import_list)

    def _rule_process(self, import_list):
        """从规则字符串中解析出关联缺陷与输出文本。"""
        output_list = []
        for a_rule in import_list:
            a_rule_list = {}
            a_rule_list['rule_description'] = a_rule['rule_description']
            words_list = a_rule['rule_description'].strip().split()
            is_pre = False
            for phase in words_list:
                if phase == 'IF':
                    is_pre = True
                elif phase in ('Then', 'THEN'):
                    is_pre = False
                elif phase == 'AND':
                    continue
                else:
                    if is_pre:
                        words = phase.split('_')
                        if words[0] not in DEFECT_CONST:
                            pass  # 工艺参数条件，跳过
                        else:
                            a_rule_list['rule_defect'] = words[0]
                    else:
                        # 弹窗/检查类结论：用词法解析取完整提示语
                        # （提示语本身可能含下划线，不能按 split('_')[2] 截断）
                        info = _split_phase(phase)
                        if info.get('action') in ('adjust', 'popup') and info.get('value'):
                            a_rule_list['rule_output'] = info['value']
            output_list.append(a_rule_list)
        return output_list


# ============================================================================
# TskRuleNet: 一阶代数式 TSK（**不迁**，占位类）
# ============================================================================

class TskRuleNet:
    """一阶代数式 TSK 网络（占位类）。

    **状态**：死代码，从未在生产中真实使用。

    项目早期命名混乱导致存在此类型，但实际项目从未有过代数式结论规则，
    因此本次迁移不实现具体算法。保留占位仅用于避免破坏 import。
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            'TskRuleNet 不在本次迁移范围。若有调用，请改用 NumTskRuleNet 或 FuzzyRuleNet。'
        )

    def predict(self, *args, **kwargs):
        raise NotImplementedError


# ============================================================================
# 模块级导出
# ============================================================================

__all__ = [
    'FuzzyFeature',
    'FuzzyRule',
    'FuzzyRuleNet',       # Mamdani (兜底层)
    'NumTskRule',         # 数值结论规则
    'NumTskRuleNet',      # 零阶 TSK (工厂级生产主路径)
    'ParticularRules',    # 弹窗规则
    'TskRuleNet',         # 占位，未实现
]


# ============================================================================
# 模块自检（仅 `python -m nets` 时执行）
# ============================================================================

if __name__ == '__main__':
    # 最小可运行 demo：1 条规则 + 1 个 keyword
    rule_array = [
        {'rule_description': 'IF inj_pres_1_low THEN inj_pres_1_add_5'},
    ]
    keyword_array = [
        {'keyword': 'inj_pres_1', 'lvl': 3, 'min_val': 0, 'max_val': 200, 'step': 10},
    ]
    priority_array = [1.0]

    net = NumTskRuleNet(rule_array, keyword_array, priority_array)
    results, extra = net.predict({'inj_pres_1': 30}, top_k=1)
    print('== Rule ==:', rule_array[0]['rule_description'])
    print('== Input ==: inj_pres_1=30')
    print('== Result ==:', results)

