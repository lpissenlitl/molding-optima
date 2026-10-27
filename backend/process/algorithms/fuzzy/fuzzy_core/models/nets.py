"""
模糊推理网络（net）—— 真正构建并执行推理的那一层。

内核内部的配套模块：

- `fuzzy_core.profiles`   —— **输入契约**（KeywordProfile / RuleProfile），
  由数据来源适配层构造，内核唯一接受的输入对象
- `fuzzy_core.models.features` —— FuzzyFeature（论域实例，由 Profile 派生）
- `fuzzy_core.models.rules`    —— FuzzyRule / NumTskRule / ParticularRules
  （规则串解析产物，由 Profile 派生）
- `fuzzy_core.parsing`    —— 规则串词法底座（split_phase / classify_name）
- `fuzzy_core.memberships` / `fuzzy_core.defuzz` —— 隶属度函数与反模糊化

核心类（按【结论形态】分层，与 `engine.py` 的分流一致）：
- FuzzyRuleNet         Mamdani 推理（提示层；结论为模糊等级，经 centroid 反模糊化）
- NumTskRuleNet        零阶 T-S 推理（数值层，生产主路径）

**输入契约**：两个 net 都直接吃**契约对象**：
- `FuzzyRuleNet(rules: List[FuzzyRule], keywords: List[KeywordProfile])`
- `NumTskRuleNet(rules: List[NumTskRule], keywords: List[KeywordProfile])`
  —— 优先级取自每条规则自己的档案 `rule.profile.priority`，不再由外部传数组。

规则对象由**第 4 层 filter**（`fuzzy_core.rules_filter.build_rule_objects`）产出：
net 不再自己拆规则串，也不再自己分类（检查/弹窗类归提示层，不进数值层）。

分层口径（见 engine.py）：
    数值层 (numeric)  = 结论能算出数值    → NumTskRuleNet
    提示层 (advisory) = 结论是文本/模糊等级 → FuzzyRuleNet
  ⚠️ 实测：规则库 1646 条中，模糊等级结论 0 条 ⇒ FuzzyRuleNet
     代码路径已接线但**实际空跑**；99 条 adjust/popup 走 ParticularRules；
     1547 条数值结论走 NumTskRuleNet。
"""

import logging
from collections import defaultdict
from typing import List

import numpy as np

from ..defuzz import defuzz
from ..macros import (
    ALL_LEVEL_WORDS,
    DEFAULT_MEMBERSHIP_TYPE,
    MIN_ACTIVATION_THRESHOLD,
    MAMDANI_SAMPLE_POINTS,
    EPSILON,
    resolve_bucket,          # ★ 档位→桶映射（按字段自己的档位词表定位）
)
from ..parsing import is_level_word, parse_rule
from ..profiles import KeywordProfile, RuleProfile
from .features import FuzzyFeature
from .rules import FuzzyRule, NumTskRule


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

# 合法等级词全集（含前端/规则库用的 'medium' 与兼容写法 'mid'）
_ALL_LEVEL_WORDS = set(ALL_LEVEL_WORDS)


# ============================================================================
# FuzzyRuleNet: Mamdani 网络（提示层）
# ============================================================================

class FuzzyRuleNet:
    """Mamdani 推理网络（提示层）。

    处理'条件模糊 + 结论模糊级别'规则，结果经 centroid 反模糊化得到精确值。

    ⚠️ 实测：当前规则库中模糊等级结论 0 条 ⇒ 本引擎实际空跑，
       代码路径已接线但无数据流入。
    """

    def __init__(self, rules: List[FuzzyRule], keywords: List[KeywordProfile]):
        """构造 Mamdani 网络。

        输入
        ----
        rules : list[FuzzyRule]
            第 4 层 filter（`fuzzy_core.rules_filter.build_rule_objects`）产出的
            提示层规则对象 —— 已拆解、已分类。
        keywords : list[KeywordProfile]
            论域元数据档案（参数名 / 档位数 / 论域 / 步长）。
        """
        self.rule_dict = None
        self.pre_set = None
        self.sol_set = None
        self.rule_nums = None
        self.pre_dict = None
        self.sol_dict = None
        self.connected_matrix = None
        self.solution_matrix = None
        self.resolve_input_paras(rules, keywords)
        self._construct_ruleNet()

    def resolve_input_paras(self, rules: List[FuzzyRule],
                            keywords: List[KeywordProfile]):
        """装配规则对象与论域元数据，构建 pre_dict / sol_dict。

        ⚠️ 本方法**不再拆规则串、不再分类** —— 规则对象由第 4 层 filter 产出，
        net 只负责把已定形的结构装进矩阵。
        """
        self.rule_dict = {}
        self.pre_set = set()
        self.sol_set = set()
        self.rule_nums = len(rules)

        for i, rule in enumerate(rules):
            self.rule_dict[i] = rule
            self.pre_set.update(rule.r_preconditions.keys())
            self.sol_set.update(rule.r_solutions.keys())

        self.pre_dict = defaultdict(dict)
        self.sol_dict = defaultdict(dict)

        for kp in keywords:
            if kp.keyword in self.pre_set:
                self.pre_dict[kp.keyword].update({
                    'lvl': kp.lvl,
                    'min_val': kp.min_val,
                    'max_val': kp.max_val,
                    'step': kp.step,
                })
            if kp.keyword in self.sol_set:
                self.sol_dict[kp.keyword].update({
                    'lvl': kp.lvl,
                    'min_val': kp.min_val,
                    'max_val': kp.max_val,
                    'step': kp.step,
                })

    def _construct_ruleNet(self):
        """构建规则网络（连接矩阵 + 解决方案矩阵）。"""
        # 条件变量模糊集合
        idx = 0
        for k, v in self.pre_dict.items():
            k_dict = self.pre_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(
                [k_dict['min_val'], k_dict['max_val']],
                f_level=k_dict['lvl'], f_membership_type=DEFAULT_MEMBERSHIP_TYPE,
            )
            idx += k_dict['lvl']

        # 结果变量模糊集合（区间是 [0, step]）
        idx = 0
        for k, v in self.sol_dict.items():
            k_dict = self.sol_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(
                [0., k_dict['step']],
                f_level=k_dict['lvl'], f_membership_type=DEFAULT_MEMBERSHIP_TYPE,
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
        # 兼容 MT 缺陷名习惯
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
            #   语义：隶属度 0 ⇒ 视为门控不满足 ⇒ 激活度 0。
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

    def __init__(self, rules: List[NumTskRule], keywords: List[KeywordProfile]):
        """构造零阶 T-S 网络。

        输入
        ----
        rules : list[NumTskRule]
            第 4 层 filter（`fuzzy_core.rules_filter.build_rule_objects`）产出的
            数值层规则对象 —— 已拆解、已分类、已剔除「结论值不是数值」的规则。
        keywords : list[KeywordProfile]
            论域元数据档案（参数名 / 档位数 / 论域 / 步长）。

        优先级取自每条规则自己的档案 ``rule.profile.priority``（取值即快照）。
        """
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
        self.priority_array = []
        self.resolve_input_paras(rules, keywords)
        self.connected_matrix = None
        self.solution_matrix = None
        self.percent_set = None
        self._construct_numtskruleNet()

    def resolve_input_paras(self, rules: List[NumTskRule],
                            keywords: List[KeywordProfile]):
        """装配数值层规则对象与论域元数据。

        ⚠️ 本方法**不再过滤、不再拆规则串** —— 那是第 4 层 filter 的职责：
        检查/弹窗类结论（`X_adjust_提示语` / `X_popup_xxx`）由 filter 判为
        提示类，根本不会进数值层。

        历史教训（保留以防重蹈）：
        旧实现曾在这里「按规则串含 worse 就整条跳过」，白白丢掉 55 条结论是数值
        的可用规则，还让 rule_dict 下标出现空洞（矩阵按 rule_nums 行开 ⇒ 行号
        错位甚至越界被丢）。后来改成「被排除的规则不占下标、priority 人工重排」，
        仍然是在错误的地方修错误的问题。现在跳过规则的责任归第 4 层 ——
        被排除的规则**根本不会出现在这个列表里** ⇒ 下标天然连续、priority 天然对齐。
        """
        self.rule_dict = {}
        self.pre_set = set()
        self.sol_set = set()
        self.rule_solution = []
        self.rule_classify = []
        priorities = []

        for rule in rules:
            idx = len(self.rule_dict)
            self.rule_dict[idx] = rule
            # 数值规则为 0，百分比规则为 1
            self.rule_classify.append(
                1 if '%' in rule.profile.rule_description else 0)
            # 优先级取自规则档案（取值即快照）
            priorities.append(float(rule.profile.priority))
            self.pre_set.update(rule.r_preconditions.keys())
            self.sol_set.update(rule.r_solutions.keys())
            # 无结论的规则也要占位，否则 rule_solution 与 rule_dict 下标错位
            self.rule_solution.append(
                list(rule.r_solutions.keys())[0] if rule.r_solutions else None
            )

        self.rule_nums = len(self.rule_dict)
        self.priority_array = priorities

        self.pre_dict = defaultdict(dict)
        self.sol_dict = defaultdict(dict)

        for kp in keywords:
            if kp.keyword in self.pre_set:
                self.pre_dict[kp.keyword].update({
                    'lvl': kp.lvl,
                    'min_val': kp.min_val,
                    'max_val': kp.max_val,
                    'step': kp.step,
                })
            if kp.keyword in self.sol_set:
                self.sol_dict[kp.keyword].update({
                    'lvl': kp.lvl,
                    'min_val': kp.min_val,
                    'max_val': kp.max_val,
                    'step': kp.step,
                })

    def _construct_numtskruleNet(self):
        """构建网络（连接矩阵 + 解决方案矩阵）。"""
        # 条件变量
        idx = 0
        for k, v in self.pre_dict.items():
            k_dict = self.pre_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(
                [k_dict['min_val'], k_dict['max_val']],
                f_level=k_dict['lvl'], f_membership_type=DEFAULT_MEMBERSHIP_TYPE,
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

    def tsk_inference(self, x):
        """执行四层零阶 TSK 推理。

        Parameters
        ----------
        x : dict
            变量名 -> 精确值

        Returns
        -------
        (results, extra_dict)
            results: [(rule_str, weighted_activation, {param: value}), ...] 按激活度降序
            extra_dict: 弹窗规则文本

        ⚠️ 优先级**只有一个来源**：每条规则自己的档案 `rule.profile.priority`
        （构造时已固化进 `self.priority_array`）。
        这里刻意不开放「外部注入优先级数组」的口子 —— 否则同一批规则存在
        两套优先级，net 内部算出来的权重与规则档案会对不上。
        """
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
            #   语义：隶属度 0 ⇒ 视为门控不满足 ⇒ 激活度 0。
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
        results, extra_dict = self.tsk_inference(x)
        if len(results) <= top_k:
            return results, extra_dict
        return results[:top_k], extra_dict


# ============================================================================
# 模块级导出
# ============================================================================

__all__ = [
    'FuzzyRuleNet',       # Mamdani (提示层)
    'NumTskRuleNet',      # 零阶 TSK (数值层，生产主路径)
]


# ============================================================================
# 模块自检（仅 `python -m nets` 时执行）
# ============================================================================

if __name__ == '__main__':
    # 最小可运行 demo：1 条规则 + 1 个论域档案
    # ⚠️ net 吃的是**契约对象**（NumTskRule / KeywordProfile），不是裸 dict
    rule_desc = 'IF inj_pres_1_low THEN inj_pres_1_add_5'
    keywords = [
        KeywordProfile(keyword='inj_pres_1', lvl=3, min_val=0, max_val=200, step=10),
    ]
    rules = [
        NumTskRule(
            RuleProfile(rule_description=rule_desc, priority=1.0),
            parse_rule(rule_desc),
        )
    ]

    net = NumTskRuleNet(rules, keywords)
    results, extra = net.predict({'inj_pres_1': 30}, top_k=1)
    print('== Rule ==:', rule_desc)
    print('== Input ==: inj_pres_1=30')
    print('== Result ==:', results)
