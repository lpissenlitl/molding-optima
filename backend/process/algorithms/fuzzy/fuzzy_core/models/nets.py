"""
模糊推理网络（net）—— 真正构建并执行推理的那一层。

内核内部的配套模块：

- `fuzzy_core.profiles`   —— **输入契约**（KeywordProfile / RuleProfile），
  由数据来源适配层构造，内核唯一接受的输入对象
- `fuzzy_core.models.features` —— FuzzyFeature（论域实例，由 Profile 派生）
- `fuzzy_core.models.rules`    —— FuzzyRule / NumTskRule
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
     代码路径已接线但**实际空跑**；99 条 adjust/popup 由第 4 层 filter
     抽成文本建议（`advice_items`），不进任何推理网络；
     1547 条数值结论走 NumTskRuleNet。
"""

import json
import logging
from collections import defaultdict
from typing import List

import numpy as np

from ..defuzz import defuzz
from ..macros import (
    DEFAULT_MEMBERSHIP_TYPE,
    MIN_CONCLUSION_DEGREE,   # ① Mamdani 输出侧：结论隶属度之和下限
    MIN_RULE_ACTIVATION,    # ② TSK 输入侧：规则绝对激活度下限
    MIN_GROUP_SHARE,        # ③ TSK 相对量：组内占比下限
    GATE_TAU,               # M-1 门控：未命中门限（结构量 exp(-2)）
    GATE_EPSILON,           # M-1 门控：明确态门限（纯代价旋钮）
    GATE_BETA_MIN,          # M-1 门控：降权下限（效果旋钮）
    MAMDANI_SAMPLE_POINTS,
    EPSILON,
    resolve_bucket,          # ★ 档位→桶映射（按字段自己的档位词表定位）
    specificity_weight,      # ★ 特异级→匹配度权重
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
    用全局静态 3 档表会让 5/7 档字段的门控整体错位一档。

    「禁止静默降级」：词表对不上时不能悄悄取错桶，必须留下可查的日志。
    返回 None 表示该前件建不了论域，调用方按"不作为门控"处理。
    """
    try:
        return resolve_bucket(lvl, word)
    except ValueError as e:
        logger.warning('[%s] 档位词 %r 无法映射到 lvl=%d 的桶：%s', where, word, lvl, e)
        return None


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
        # ⚠️ 先复制再补默认值 —— **不就地修改入参**。
        #   提示层传进来的是编排层的 process_parameter **原对象**，
        #   就地写 x['MT'] = 0 会把引擎的原始参数污染掉
        #   （数值层传的是副本，两层口径必须一致）。
        # 兼容 MT 缺陷名习惯
        x = {**x}
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

            # ★ 主导规则：**只从「命中了该输出变量」的规则里选**。
            #   ⚠️ 原实现 `argmax(where(rule_selected_list, rule_activations, -1))`
            #     在**一条规则都没命中该输出变量**时会返回 0 ⇒ 去取 `rule_dict[0]`
            #     （那条规则可能根本没有这个参数 ⇒ KeyError；即使不崩，
            #      也会把**无关规则**当成主导规则）。
            #   语义等价性：选中者的激活度 ≥ 0 > -1 ⇒ 原来的 argmax 本来就
            #     落在选中集合内 ⇒ 改写**不改变任何有效路径**的结果。
            selected = np.flatnonzero(rule_selected_list)
            if selected.size:
                final_rule = int(selected[np.argmax(rule_activations[selected])])
                self.sol_dict[k]['action'] = (
                    self.rule_dict[final_rule].r_solutions[k]['action'])
                self.sol_dict[k]['reason'] = final_rule
            else:
                # 无规则命中该输出变量 ⇒ 无主导规则（`reason = -1` 是哨兵）
                logger.warning(
                    '[FuzzyRuleNet] 输出变量 %s 没有任何规则命中，无主导规则', k)
                self.sol_dict[k]['action'] = 0
                self.sol_dict[k]['reason'] = -1

        # 无效激活过滤（**输出侧**判据：结论隶属度之和）
        for k in self.sol_dict:
            idx = self.sol_dict[k]['index']
            lvl = self.sol_dict[k]['lvl']
            degree_values = rule_to_outputs[idx:idx + lvl]
            if np.sum(degree_values) < MIN_CONCLUSION_DEGREE:
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

        results = []
        for param_name, value in zip(self.sol_dict.keys(), res):
            reason = self.sol_dict[param_name].get('reason', -1)
            if reason is None or reason < 0:
                # 无主导规则（没有任何规则命中该输出变量）⇒ 激活度记 0、规则记 None
                results.append((param_name, value, (0.0, None)))
                continue
            results.append((
                param_name, value,
                (rule_activations[reason], self.rule_dict[reason]),
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
        # 数值规则为 0，百分比规则为 1
        self.rule_classify = []
        self.rule_solution = []
        self.priority_array = []
        self.resolve_input_paras(rules, keywords)
        self.connected_matrix = None
        self.solution_matrix = None
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
        specificities = []

        for rule in rules:
            idx = len(self.rule_dict)
            self.rule_dict[idx] = rule
            # 数值规则为 0，百分比规则为 1
            self.rule_classify.append(
                1 if '%' in rule.profile.rule_description else 0)
            # 优先级取自规则档案（取值即快照）
            priorities.append(float(rule.profile.priority))
            # 特异级取自规则档案（用于匹配度权重，见 `macros.specificity_weight`）
            spec = getattr(rule.profile, 'specificity', 4)
            specificities.append(int(spec) if spec else 4)
            self.pre_set.update(rule.r_preconditions.keys())
            self.sol_set.update(rule.r_solutions.keys())
            # 无结论的规则也要占位，否则 rule_solution 与 rule_dict 下标错位
            self.rule_solution.append(
                list(rule.r_solutions.keys())[0] if rule.r_solutions else None
            )

        self.rule_nums = len(self.rule_dict)
        self.priority_array = priorities
        self.specificity_array = specificities

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
        # ★ M-1 门控规格（design §5.3.2「符号定义」）：
        #   每条规则**实际连上**的每个前件，记下 (参数名, 桶索引, 列下标)。
        #   ⚠️ 为什么不能只靠 `connected_matrix`：矩阵只记「哪些列非零」，
        #      **丢掉了「这些列属于哪个参数、是该参数的第几桶」**
        #      ⇒ 光有矩阵算不出 `μ_alt`（该参数其余桶的最大 μ）⇒ 必须另存。
        #   ⚠️ 「不可判级前件」（`worse` / 无元数据）**不连桶** ⇒ 不入规格
        #      ⇒ 不参与三态判定、也不降权（design §5.3.3 明文）。
        self.gate_specs = [[] for _ in range(rows)]

        for row_idx, rule in self.rule_dict.items():
            # ★ 档位词填不进该字段的档位词表 ⇒ **整条规则不参与推理**。
            #   语义：档位词是**绝对词义**（low 就是「偏低」这一档），它落在向量的
            #   哪一格由**字段自己的档数**决定；词不在该字段词表内 ⇒ 这个条件
            #   **无法判定** ⇒ 该条件匹配度为 0 ⇒ 整条规则匹配度为 0。
            #   ⚠️ 绝不能「只跳过这一个前件」：那等于把条件从门控里删掉，
            #      门控乘数变少 ⇒ 匹配度不降反升（实测：删掉填不进去的
            #      very_low 后，激活度从 0 变成 1.0）。
            #   ⚠️ 与下面两种「不作为门控」严格区分，它们是「该条件不参与」，
            #      不是「条件无法判定」：
            #      - 'worse' 等人工判断词：本来就没有隶属度可言
            #      - pre_dict 里没有该维度：建不了论域（缺陷反馈未给程度等）
            unresolvable = False
            gate_specs = []
            for name, value in rule.r_preconditions.items():
                level = str(value.get('level', '')).lower()
                if not is_level_word(level):
                    # 不可判级的前件，不作为门控：
                    #   - 'worse'：人工判断词（"该参数不合理"），没有隶属度可言
                    #
                    # 缺陷前件**不在这里**被跳过：它的 level 本身就是档位词
                    # （`SHORTSHOT_low` ⇒ 'low'）。缺陷维度能否作门控，取决于
                    # 有没有拿到论域元数据（见下面的 pre_dict 判断）。
                    continue
                if not self.pre_dict.get(name):
                    # 无 RuleKeyword 元数据 → 建不了论域 → 不作为门控
                    # （缺陷维度在「反馈未给出程度」时也走这条路）
                    logger.debug('[NumTskRuleNet] pre_dict 中没有 %s，跳过该前件', name)
                    continue
                # ★ 按【该字段自己的档位数】取桶：同一个 'high' 在 3 档字段是桶 2，
                #   在 5 档字段是桶 3（论域 75% 分位）。用全局静态表会整体错位一档。
                bucket = _resolve_bucket_safe(
                    self.pre_dict[name]['lvl'], level, 'NumTskRuleNet.pre')
                if bucket is None:
                    # 合法档位词但该字段档数不够 ⇒ 条件无法判定 ⇒ 整条规则作废
                    unresolvable = True
                    continue
                p_col_idx = self.pre_dict[name]['index'] + bucket
                if row_idx < len(self.connected_matrix):
                    self.connected_matrix[row_idx][p_col_idx] = 1
                    # ★ 记下门控规格（M-1 要用它算 μ_used / μ_alt）
                    gate_specs.append((name, bucket, p_col_idx))
                else:
                    logger.error(
                        f"index {row_idx} is out of bounds for axis 0 with size {len(self.connected_matrix)}"
                    )

            if unresolvable and row_idx < len(self.connected_matrix):
                # 该规则门控列清零 ⇒ 激活度 0 ⇒ 被 too_weak 闸剔除，不参与结论
                # （其余规则完全不受影响 —— 规则库是渐进生长的，一条不可用
                #   不该拖垮整批推理）
                self.connected_matrix[row_idx][:] = 0
                # ★ 整条规则作废 ⇒ 门控规格一并作废
                #   （否则 M-1 会拿一个「已清零的列」算 μ_used ⇒ 假门控）
                gate_specs = []
            self.gate_specs[row_idx] = gate_specs

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

            # ⚠️ 这里**不再收集 `r_extra`**（弹窗/检查类结论）：
            #   第 4 层 filter 已把它们抽成 `advice_items` 并整条跳过，
            #   根本不会进推理网络 ⇒ `r_extra` 恒空 ⇒ 收集它是死路径。

    def tsk_inference(self, x):
        """执行四层零阶 TSK 推理。

        Parameters
        ----------
        x : dict
            变量名 -> 精确值

        Returns
        -------
        (results, extra_dict)
            results: [(rule_str, group_weight, {param: value}, raw_activation), ...]
                     按**组内占比**降序。
                     - ``group_weight``：该规则在它所属**输出参数组**里的占比
                       （同组之和 = 1）⇒ 聚合层裸累加 = 加权平均。
                     - ``raw_activation``：**原始激活度** $a_i$（前件隶属度之积），
                       不含 priority / specificity 乘数 ⇒ 供置信度使用。
            extra_dict: **恒空**（保留仅为返回值签名兼容）
                ⚠️ 弹窗/检查类结论由第 4 层 filter 抽成 ``advice_items``，
                不进推理网络 ⇒ net 层拿不到 ``r_extra``（原 `extra_dict`
                收集路径已删除）。

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
            # ★ 多前件用 **min（弱连接）**，不是 prod（相乘）：
            #   规则是 AND 条件判断 ⇒ “最弱的那条证据说了算”。
            #   - prod 会让多前件规则被**指数级稀释**（两个 0.5 的条件 ⇒ 0.25），
            #     条件越多激活度越接近 0 ⇒ 整批规则被 too_weak 闸门拦掉。
            #   - min 的性质：>=2 门控时真正起作用；**单门控时 min == 该值本身**，
            #     天然正确（单前件规则不受影响）。
            #   - min(0, x) == 0 ⇒ 门控不满足时激活度仍为 0，语义不变。
            #   规格见设计文档 §5.2（2026-10-28 实施，批 M）。
            rule_activations[i] = np.min(conditions)  # 各项激活度取最弱（弱连接）

        # ============================================================
        # M-1 门控三态（design §5.3「门控状态机」）
        # ============================================================
        # 逐前件判三态（design §5.3.3）：
        #   ① μ_used < τ                      → 未命中：规则不参与结论
        #   ② μ_used ≥ τ 且 competition < ε   → 边界态：生效但降权
        #   ③ competition ≥ ε                 → 明确态：正常生效
        #
        #   β_p = clamp(competition / ε, β_min, 1)   （连续衰减，无阶跃）
        #   β_r = min(β_p1, …, β_pk)                （最弱前件说了算，方案 (a)）
        #
        # ⚠️ 为什么 τ 判「整条规则出局」而不是只压低该前件的权重：
        #   前件是 AND 关系 ⇒ 任一前提不成立 ⇒ 整条规则的前提不成立。
        #   副产品（重要）：这保证了「τ 的剔除集 ⊇ MIN_RULE_ACTIVATION 的剔除集」
        #   —— 全部前件 μ_used ≥ τ ⇒ 激活度 = min(各前件 μ_used) ≥ τ = 0.1353
        #   > MIN_RULE_ACTIVATION ⇒ 绝对激活度闸对**有可判级前件**的规则
        #   永不触发（design §5.3.8「冗余可删」的成立条件）。
        #
        # ⚠️ `μ_used` / `μ_alt` 的定义（design §5.3.2，**勿回退**成 μ_max/μ_second）：
        #   μ_used = 规则**实际引用的那个桶**上的隶属度
        #   μ_alt  = 该参数**其余桶**里隶属度的最大值（其余桶为空 ⇒ 0）
        #   competition = μ_used − μ_alt
        #     （>0 归属一致 / =0 分不清 / <0 归属不一致 ← 这就是「档位不符」）
        m1_beta = np.ones(shape=(self.rule_nums,), dtype=float)
        m1_unmatched = np.zeros(shape=(self.rule_nums,), dtype=bool)
        m1_boundary = set()
        m1_competition = {}
        # ★ 逐规则的「档位归属」分类（design §5.3.7 疗效指标要求**分开统计**）：
        #   mismatch = 存在某前件 competition < 0（=「档位不符」）
        #   match    = 全部前件 competition ≥ 0（=「档位相符」）
        #   ⚠️ 计算块里**不许 break**：τ 出局后仍要把其余前件的 competition 算完，
        #      否则分不清「τ 误杀了相符规则」还是「出局的是本就不符的规则」
        #      ⇒ 误杀率（假阴性）永远算不出来（design §5.3.7 要求双向统计）。
        m1_mismatch = np.zeros(shape=(self.rule_nums,), dtype=bool)
        m1_match = np.zeros(shape=(self.rule_nums,), dtype=bool)
        for i in range(self.rule_nums):
            specs = self.gate_specs[i]
            if not specs:
                # 没有任何可判级前件 ⇒ 不参与三态判定
                # （激活度 0 ⇒ 由 too_weak 闸兜底剔除）
                continue
            betas = []
            competitions = []
            for name, bucket, col_idx in specs:
                mu_used = float(membership_degrees[col_idx])
                p_idx = self.pre_dict[name]['index']
                p_lvl = self.pre_dict[name]['lvl']
                mu_alt = 0.0
                for b in range(p_lvl):
                    if b == bucket:
                        continue
                    alt = float(membership_degrees[p_idx + b])
                    if alt > mu_alt:
                        mu_alt = alt
                competition = mu_used - mu_alt
                # ⚠️ competition 无论 μ_used 是否达标都记（误杀率统计要用）
                competitions.append(competition)
                if mu_used < GATE_TAU:
                    # ① 未命中 ⇒ 整条规则出局（AND 语义）
                    #    ⚠️ 这里**不 break**：见上方 m1_mismatch 的注释
                    m1_unmatched[i] = True
                    continue
                beta_p = competition / GATE_EPSILON
                if beta_p < GATE_BETA_MIN:
                    beta_p = GATE_BETA_MIN
                elif beta_p > 1.0:
                    beta_p = 1.0
                betas.append(beta_p)
            m1_mismatch[i] = any(c < 0.0 for c in competitions)
            m1_match[i] = not m1_mismatch[i]
            if m1_unmatched[i]:
                m1_beta[i] = 0.0
                continue
            # ★ β_r = min（方案 (a)「最弱前件说了算」——与 §5.2 的 min 弱连接同哲学）
            m1_beta[i] = min(betas) if betas else 1.0
            weakest = min(competitions) if competitions else None
            if weakest is not None:
                m1_competition[i] = weakest
                if weakest < GATE_EPSILON:
                    m1_boundary.add(i)

        # 第三层（分组归一化 + priority × 匹配度加权）
        #
        # ⚠️ 为什么按【输出变量】分组，而不是全局归一化：
        #   全局分母让「全池规则条数」变成了每个建议的稀释系数 ——
        #   某个参数只被 1 条规则命中时，它的权重也只有 1/N（N = 全池条数），
        #   推荐值被压到 1/N（实测：conf=0.1、结论 +2 被压成 +0.2）。
        #   分组后每个输出参数组内独立归一化 ⇒ 组内权重和恒为 1 ⇒
        #   聚合层裸累加 = **加权平均**，推荐量级与规则总数脱钩。
        #
        # ⚠️ 匹配度权重（specificity）与 priority 是同类乘数，但含义不同：
        #   priority 是**人为设定的优先级**，specificity 是**匹配程度**
        #   （越精确越该被采信）。两者相乘后再归一化。
        spec_weights = np.asarray(
            [specificity_weight(s) for s in self.specificity_array], dtype=float)
        # ★ M-1 的 β 乘进 raw（design §5.3.3 的权重式）
        #   `raw = μ × priority × specificity × β_r`
        #   ⚠️ β 必须乘在**归一化之前**：若在归一化后再压占比，
        #      占比会被重新摊平 ⇒ 降权完全失效（design §5.3.5）。
        raw = (rule_activations * np.asarray(priority_array) * spec_weights
               * m1_beta)

        # ★ 绝对激活度下限（**与池大小无关**）：
        #   原始激活度过低的规则**不参与结论**。
        #   ⚠️ 这道闸不能省：分组归一化把权重变成了「组内纯相对量」——
        #      一条激活度近乎为零的规则（实测：低桶在远处 μ=exp(-8)≈3.35e-4）
        #      只要**独占某个输出参数组**，就会拿到组内占比 1.0 ⇒ 反而独占
        #      100% 的建议权重，把「几乎没匹配上」变成满额建议。
        #      改造前这道闸由「全局归一化 + 阈值」顺带完成；去掉全局分母后
        #      必须显式补上，否则 C2 回归锁（低激活度不产出结论）失效。
        #   判据用**原始激活度**（不含 priority / specificity 乘数）——
        #   「这条规则到底匹配得多准」与人为权重无关。
        #   ⚠️ 这道闸（**输入侧绝对强度**）与下面「组内占比」那道闸**量纲不同**：
        #      一个是绝对强度，一个是相对份额 ⇒ 各自独立取值
        #      （`MIN_RULE_ACTIVATION` / `MIN_GROUP_SHARE`）。
        #   ⚠️ **M-1 落地后本闸已成冗余**（τ=0.1353 的剔除集**严格包含**本闸）：
        #      M-1 要求「全部前件 μ_used ≥ τ」才让规则参与
        #      ⇒ 规则激活度 = min(各前件 μ_used) ≥ τ = 0.1353 > 0.01001
        #      ⇒ 本闸对**有可判级前件**的规则永不触发。
        #      ⚠️ 但**保留它**：无可判级前件的规则（激活度 0）仍由它兜底剔除。
        #      （`m1_unmatched` = M-1 的 τ 判未命中 ⇒ 与本闸同一个去路。）
        too_weak = (rule_activations < MIN_RULE_ACTIVATION) | m1_unmatched

        # 组归属 = 该规则的结论参数名（`rule_solution[i]`）
        group_of = [
            self.rule_solution[i] if i < len(self.rule_solution) else None
            for i in range(self.rule_nums)
        ]

        group_sums = {}
        for i in range(self.rule_nums):
            key = group_of[i]
            if key is None or too_weak[i]:
                continue
            group_sums[key] = group_sums.get(key, 0.0) + raw[i]

        group_weights = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(self.rule_nums):
            key = group_of[i]
            if key is None or too_weak[i]:
                continue
            denom = group_sums.get(key, 0.0)
            if denom > EPSILON:
                group_weights[i] = raw[i] / denom

        # ★ 无效激活过滤（**组内占比**下限，与 Mamdani 的结论隶属度下限**同值不同义**）：
        #   权重过低的规则不参与结论层 —— 否则它会以 delta≈0 的形式混进
        #   推荐列表（实测见过 confidence=1.68e-282 的项）。
        #   ⚠️ 阈值作用在【组内占比】上：占比是「这条规则在它所属参数组里
        #      占多少」的相对量，与全池规模无关 ⇒ 阈值语义稳定。
        #   （绝对强度那道闸在上面 `too_weak` —— 两者量纲不同、缺一不可）
        #
        # ⚠️ mask 留一份：下面要统计「这道闸剔了多少、剔掉多大份额」
        #    ⇒ **放大倍数 = 1/(1−S)**（S = 被剔除规则的总份额，组内口径）。
        #    纯观测，**不设任何阈值、不改任何数值**
        #    （design §5.3.8 阈值清单 · `MIN_GROUP_SHARE` 行）。
        #
        # ★ 观测拆成两条（**都是只读，不改任何数值**）：
        #   ① `group_dist`（**debug 级**，每次推理一条）—— 每组的**最小占比**分布。
        #      用途：论证「占比闸到底剔了多少」—— 若分布天然远离阈值，
        #      则「放大倍数护栏」根本不需要存在（先观测后定值，见 review §27.3）。
        #      生产默认不输出（DEBUG 才可见）⇒ 不刷屏。
        #   ② `group_share`（**info 级**，仅在**确实发生剔除**时）—— 剔除明细。
        group_min_share = {}
        group_size = {}
        for i in range(self.rule_nums):
            key = group_of[i]
            if key is None or too_weak[i]:
                continue
            group_size[key] = group_size.get(key, 0) + 1
            w = group_weights[i]
            if key not in group_min_share or w < group_min_share[key]:
                group_min_share[key] = w

        weak_mask = group_weights < MIN_GROUP_SHARE
        group_weights[weak_mask] = 0.0

        # 剔除后重新归一化：保证存活规则的组内权重和仍为 1
        # （否则「组内只命中 1 条」时，推荐量级会随被剔除的规则条数漂移）
        alive_sums = {}
        for i in range(self.rule_nums):
            if group_weights[i] <= 0:
                continue
            key = group_of[i]
            if key is None:
                continue
            alive_sums[key] = alive_sums.get(key, 0.0) + group_weights[i]
        for i in range(self.rule_nums):
            if group_weights[i] <= 0:
                continue
            key = group_of[i]
            if key is None:
                continue
            denom = alive_sums.get(key, 0.0)
            if denom > EPSILON:
                group_weights[i] = group_weights[i] / denom

        # ★ 观测（**只读，不改任何数值**）：占比闸的剔除效果
        #   「剔除后重新归一化」会把存活规则的组内权重**放大** `1/(1−S)` 倍
        #   （S = 该组被剔除规则的总份额）。
        #   ⚠️ 这个放大倍数**从未被量化过** ⇒ 这里只**记录**，不设护栏
        #      （设护栏需要判据；拍一个数值等同无判据硬编码，见 review §27.3）。
        #   ⚠️ S 直接由 `alive_sums` 反算（剔除前组内占比和恒为 1 ⇒
        #      存活份额 = 1−S）⇒ 不受“占比本来就是 0”的规则干扰。
        dropped_counts = {}
        alive_counts = {}
        for i in range(self.rule_nums):
            key = group_of[i]
            if key is None or too_weak[i]:
                continue
            if weak_mask[i]:
                dropped_counts[key] = dropped_counts.get(key, 0) + 1
            elif group_weights[i] > 0:
                alive_counts[key] = alive_counts.get(key, 0) + 1
        group_stats = []
        for key in sorted(group_sums):
            dropped = dropped_counts.get(key, 0)
            if not dropped:
                continue
            alive_share = alive_sums.get(key, 0.0)
            group_stats.append({
                'param': key,
                'alive': alive_counts.get(key, 0),
                'dropped': dropped,
                'dropped_share': round(max(0.0, 1.0 - alive_share), 6),
                # 整组被剔空时 alive_share = 0 ⇒ 放大倍数无定义（不是无限大）
                'amplify': round(1.0 / alive_share, 6) if alive_share > EPSILON else None,
            })
        if group_stats:
            # 只在**确实发生了剔除**时记一条（事件驱动）⇒ 无剔除就不刷屏
            logger.info('[fuzzy.net.group_share] %s',
                        json.dumps({'groups': group_stats}, ensure_ascii=False))

        # ① 分布摘要（debug 级，每次推理一条）
        #    「每组的最小占比」= 该组里最弱那条规则的组内份额 ⇒
        #    若它都远高于 `MIN_GROUP_SHARE`，则这道闸在本场景下根本不会剔任何东西。
        if group_min_share:
            shares = sorted(group_min_share.values())
            lowest_key = min(group_min_share, key=group_min_share.get)
            logger.debug(
                '[fuzzy.net.group_dist] %s',
                json.dumps({
                    'rules': int(self.rule_nums),
                    'groups': len(group_min_share),
                    'min_share': round(shares[0], 8),
                    'min_share_group_size': group_size.get(lowest_key, 0),
                    'median_share': round(shares[len(shares) // 2], 8),
                    'max_share': round(shares[-1], 8),
                    'threshold': MIN_GROUP_SHARE,
                }, ensure_ascii=False))

        # ★ M-1 门控观测（**只读，不改任何数值**）：三态分布
        #   design §5.3.7 的诊断项「三态分布（未命中 / 边界 / 明确）」。
        #   ⚠️ 「边界态」是 **ε 的唯一在线探针**：ε 若被调大，
        #      相符规则会开始落进边界态（被误伤降权）⇒ 这条日志就是
        #      review §26.7 列的 ε 证伪信号（「相符规则上出现 boundary 标记」）。
        #   ⚠️ 「未命中」是 **τ 的在线探针**：它突然变大 ⇒ τ 压过头了
        #      （或规则库长大后引入了大量「档位不符且偏离大」的规则）。
        if self.rule_nums:
            # ★ 四态分布（design §5.3.7 的「三态分布」+ 边界态两子情形拆分）：
            #   unmatched  = ① τ 未命中（规则出局）
            #   mismatched = ② 命中但**存在**前件 competition < 0（档位不符）
            #   borderline = ③ 命中、全部 competition ≥ 0，但最小者 < ε
            #                （归属一致但领先不足 ⇒ 连续衰减，**不算错配**）
            #   explicit   = ④ 明确态
            #   ⚠️ 「错配」与「边界」必须分开：前者治法是**压到 β_min**（硬下限），
            #    后者是**连续衰减**；混在一起看不出 ε 有没有误伤（§26.7 证伪信号）。
            m1_states = {'unmatched': 0, 'mismatched': 0, 'borderline': 0,
                         'explicit': 0, 'no_gate': 0}
            false_kill = 0
            for i in range(self.rule_nums):
                if not self.gate_specs[i]:
                    m1_states['no_gate'] += 1
                elif m1_unmatched[i]:
                    m1_states['unmatched'] += 1
                    # ★ 误杀（假阴性）：出局但「全部前件 competition ≥ 0」
                    #   ⇒ 本是相符规则却被 τ 剔掉（design §5.3.7 要求双向统计）
                    if m1_match[i]:
                        false_kill += 1
                elif m1_mismatch[i]:
                    m1_states['mismatched'] += 1
                elif i in m1_boundary:
                    m1_states['borderline'] += 1
                else:
                    m1_states['explicit'] += 1
            # ★ 核心疗效指标（design §5.3.7「档位不符规则参与结论的权重占比」）：
            #   口径 ①（组内等权）：每组 = 一个输出参数 = 一条推荐
            #                ⇒ 该组「错配规则组内占比之和」→ 对所有组取均值
            #   口径 ②（全池 raw 加权）：Σ错配raw / Σ存活raw（跨组可比）
            #   ⚠️ 这两个口径在 **M-1 旁路时同样可算**（τ=0 ⇒ 无出局，
            #      β_min=1 ⇒ 错配不降权）⇒ 可直接做 baseline vs M-1 对照。
            group_mismatch = {}
            raw_mismatch = 0.0
            raw_alive = 0.0
            # ★ 绝对权重分项（review §25.2「干净口径」必需）：
            #   Σraw 不符 / Σraw 相符 各自独立 ⇒ 分子分母互不污染
            #   ⇒ 可直接算「不符权重降幅」与「相符权重削减」
            raw_mismatch_sum = 0.0
            raw_matched_sum = 0.0
            for i in range(self.rule_nums):
                key = group_of[i] if i < len(group_of) else None
                if key is None or too_weak[i] or group_weights[i] <= 0:
                    continue
                raw_alive += float(raw[i])
                if m1_mismatch[i]:
                    group_mismatch[key] = (group_mismatch.get(key, 0.0)
                                           + float(group_weights[i]))
                    raw_mismatch += float(raw[i])
                    raw_mismatch_sum += float(raw[i])
                elif m1_match[i]:
                    raw_matched_sum += float(raw[i])
            group_n = len(group_sums)
            m1_beta_alive = m1_beta[m1_beta > 0]
            borderline_comps = [m1_competition[i] for i in m1_boundary
                                if i in m1_competition and m1_match[i]]
            logger.debug(
                '[fuzzy.net.m1_gate] %s',
                json.dumps({
                    'rules': int(self.rule_nums),
                    'states': m1_states,
                    'false_kill': false_kill,
                    'mismatch_share_mean': (
                        round(sum(group_mismatch.values()) / group_n, 8)
                        if group_n else None),
                    'mismatch_share_max': (
                        round(max(group_mismatch.values()), 8)
                        if group_mismatch else None),
                    'mismatch_raw_ratio': (
                        round(raw_mismatch / raw_alive, 8)
                        if raw_alive > EPSILON else None),
                    'raw_mismatch_sum': round(raw_mismatch_sum, 8),
                    'raw_matched_sum': round(raw_matched_sum, 8),
                    'raw_alive_sum': round(raw_alive, 8),
                    'beta_min_seen': (round(float(m1_beta_alive.min()), 8)
                                      if m1_beta_alive.size else None),
                    'beta_max_seen': (round(float(m1_beta_alive.max()), 8)
                                      if m1_beta_alive.size else None),
                    'borderline_competition_min': (
                        round(min(borderline_comps), 8)
                        if borderline_comps else None),
                    'borderline_competition_max': (
                        round(max(borderline_comps), 8)
                        if borderline_comps else None),
                    'tau': GATE_TAU,
                    'gate_epsilon': GATE_EPSILON,
                    'beta_min': GATE_BETA_MIN,
                }, ensure_ascii=False))

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
        raw_activations_out = []
        calculate_list = []
        sol_len = np.size(sol_matrix, 0)
        for i in range(0, self.rule_nums):
            if group_weights[i] <= 0:
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
            activations_out.append(float(group_weights[i]))
            # 原始激活度（含 M-1 的 β 修正，不含 priority / specificity 乘数）
            # ⚠️ **含 β** 是口径变更（design §5.3.7）：raw_activation 表达的是
            #    「这条规则到底匹配得多准」⇒ 必须包含「归属是否一致」这一维，
            #    否则一条被压到 β_min 的**档位不符**规则仍会报出 confidence=1.0
            #    （而它实际只占组内 20% 权重）⇒ 前端会把「把握不大」显示成
            #    「满把握」。边界态同理。
            raw_activations_out.append(float(rule_activations[i] * m1_beta[i]))
            calculate_list.append(cal_dict)

        res = list(zip(rule_list, activations_out, calculate_list,
                       raw_activations_out))
        res = sorted(res, key=lambda x: -float(x[1]))

        return res, {}

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
