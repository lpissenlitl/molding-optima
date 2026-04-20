from collections import defaultdict

import numpy as np

from mdprocess.utils.fuzzykit.fuzzy_core.functional import gauss_mf, tri_mf, defuzz
from mdprocess.utils.fuzzykit.macros import HS_MAPPING_DICT
from mdprocess.const import DEFECT_CONST

import logging


class FuzzyFeature:
    """
    每一个特征模糊化表示类,一般用作规则条件词
    储存原始数值、模糊化数值、对应的模糊化隶属度函数参数
    """

    def __init__(self, f_name, f_interval, f_membership_type='gauss', f_level=3, f_type='process'):
        """
        Parameters
        ----------
        f_name: str, 特征名,一般为工艺参数名
        f_interval: list[float], 特征取值区间
        f_membership_type: str, 所使用的模糊隶属度函数类型
        f_level: int, 特征的模糊划分数量
        f_type: str, 表示特征类型,可选类型目前支持工艺参数（process）、缺陷（defect）
        """
        self.f_type = f_type
        self.f_name = f_name
        self.f_interval = f_interval
        self.f_membership_type = f_membership_type
        self.f_level = f_level
        self.membership_dict = defaultdict(None)

        if f_membership_type == 'gauss':
            self.membership_func = gauss_mf
            sigmas = np.array([(f_interval[1] - f_interval[0]) / (2 * (f_level-1))] * f_level)
            means = np.r_[
                f_interval[0], np.quantile(f_interval, np.arange(1, f_level - 1) / (f_level - 1)), f_interval[1]]
            for i in range(f_level):
                self.membership_dict['degree_' + str(i)] = [means[i], sigmas[i]]

        elif f_membership_type == 'tri':
            self.membership_func = tri_mf
            a_values = np.r_[f_interval[0], np.quantile(f_interval, np.arange(0, f_level - 1) / (f_level - 1))]
            b_values = np.r_[np.quantile(f_interval, np.arange(0, f_level) / (f_level - 1))]
            c_values = np.r_[np.quantile(f_interval, np.arange(1, f_level) / (f_level - 1)), f_interval[1]]
            for i in range(f_level):
                self.membership_dict['degree_' + str(i)] = [a_values[i], b_values[i], c_values[i]]

    def get_value_by_level(self, x, level):
        """
        获取给定值 x、模糊级别 level 的模糊隶属度值
        Parameters
        ----------
        x: scalar or ndarray
        level: int, 指定模糊级别

        Returns
        -------
        membership_degree_val: scalar or ndarray, 返回指定模糊级别的隶属度值
        """
        if 0 <= level < self.f_level:
            degree_key = 'degree_' + str(level)
            membership_degree_val = self.membership_func(x, *self.membership_dict[degree_key])
        else:
            raise ValueError('level 超出定义范围！')
        return membership_degree_val

    def get_all_value(self, x):
        return np.array([self.get_value_by_level(x, i) for i in range(self.f_level)])


class FuzzyRule:
    """
    规则库中的每一条模糊规则的表示与计算类
    """

    def __init__(self, rule_string=''):
        """
        Parameters
        ----------
        rule_string: 符合规则模板的规则字符串
        """
        self.r_rule = rule_string
        self.r_preconditions, self.r_solutions = self._rule_process(rule_string)

    def _rule_process(self, rule):
        """
        处理规则字符串,分别存储条件和解决方法
        Parameters
        ----------
        rule: str, 规则字符串

        Returns
        -------
        r_preconditions: dict, 规则条件字典
        r_solutions: dict, 规则解决方法字典
        """
        words_list = rule.strip().split()
        r_preconditions = defaultdict(None)
        r_solutions = defaultdict(None)
        is_pre = False
        for phase in words_list:
            if phase == 'IF':
                is_pre = True
            elif phase in ['Then', 'THEN']:
                is_pre = False
            elif phase == 'AND':
                continue
            else:
                words = phase.split('_')
                if is_pre:
                    if words[0] not in DEFECT_CONST:
                        # 工艺参数条件,键为参数名,值为参数模糊级别、条件类型
                        r_preconditions[words[0]] = {'name': words[0], 'level': words[1], 
                                                     'p_type': 'process'}
                    else:
                        # 缺陷类型条件,键为缺陷类型,值为缺陷严重程度、缺陷位置、条件类型
                        r_preconditions[words[0]] = {'name': words[0], 'level': words[1], 
                                                     'p_type': 'defect'}
                else:
                    # 工艺参数修正,键为参数名,值为参数调整方向、调整模糊级别、条件类型
                    r_solutions[words[0]] = {'name': words[0], 'action': HS_MAPPING_DICT[words[1]], 'level': words[2],
                                             's_type': 'process'}
        return r_preconditions, r_solutions

    def __repr__(self):
        return self.r_rule


class FuzzyRuleNet:
    """
    规则库中所有规则组成的计算网络
    """

    def __init__(self, rule_array: list, keyword_array: list):
        """
        读入规则本地文件,建立规则库；
        读入特征信息,必须包含特征名、特征范围；
        规则库和模糊化后的特征两者皆有才能进行构建模糊网络进行后续计算。
        Parameters
        ----------
        rules_path: str, 规则文件路径
        ranges_path: str, 特征变量配置文件路径
        """
        # 规则库输入,并获取当前规则库中所有条件变量和目标变量
        # self.rule_dict, self.pre_set, self.sol_set, self.rule_nums = self._read_rules_from_file(rules_path)

        # 读取工艺参数配置文件,为规则库中参数设置取值范围
        # self.pre_dict, self.sol_dict = self._read_ranges_from_file(ranges_path)
        self.rule_dict = None
        self.pre_set = None
        self.sol_set = None
        self.rule_nums = None
        self.pre_dict = None
        self.sol_dict = None
        self.resolve_input_paras(rule_array, keyword_array)

        # 模糊计算网络构建
        self.connected_matrix = None
        self.solution_matrix = None
        self._construct_ruleNet()
    

    def resolve_input_paras(self, rule_array: list, keyword_array: list):
        """
        解析传入的规则以及关键词

        ----------
        Parameters
        ----------
        rule_array: 输入的规则数组, 存储对象
        keyword_array: 输入的关键词数组, 存储对象

        -------
        Returns
        -------
        """
        self.rule_dict = defaultdict(FuzzyRule)
        self.pre_set = set()
        self.sol_set = set()
        self.rule_nums = len(rule_array)

        for i, rule in enumerate(rule_array):
            self.rule_dict[i] = FuzzyRule(rule.get("rule_description"))
            self.pre_set.update(self.rule_dict[i].r_preconditions.keys())
            self.sol_set.update(self.rule_dict[i].r_solutions.keys())
        
        self.pre_dict = defaultdict(dict)
        self.sol_dict = defaultdict(dict)

        for item in keyword_array:
            if item["keyword"] in self.pre_set:
                self.pre_dict[item["keyword"]] = {
                    'lvl': item["lvl"],
                    'min_val': item["min_val"],
                    'max_val': item["max_val"],
                    'step': item["step"]
                }
            if item["keyword"] in self.sol_set:
                self.sol_dict[item["keyword"]] = {
                    'lvl': item["lvl"],
                    'min_val': item["min_val"],
                    'max_val': item["max_val"],
                    'step': item["step"]
                }

        return


    def _read_ranges_from_file(self, ranges_path):
        """
        读取变量配置文件

        Parameters
        ----------
        ranges_path: str, 特征变量配置文件路径

        Returns
        -------

        """
        pre_dict = defaultdict(dict)
        sol_dict = defaultdict(dict)
        dtype_dict = {'names': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'),
                      'formats': ('U20', 'i4', 'f4', 'f4', 'f4', 'f4', 'f4')}
        records = np.loadtxt(ranges_path, dtype=dtype_dict, encoding='utf-8', delimiter=',')
        key_list = ['lvl', 'min_val', 'max_val', 'step']
        for name in self.pre_set:
            pre_dict[name] = dict(zip(key_list, *records[records['col1'] == name][['col2', 'col3', 'col4', 'col7']]))
        for name in self.sol_set:
            sol_dict[name] = dict(zip(key_list, *records[records['col1'] == name][['col2', 'col3', 'col4', 'col7']]))
        return pre_dict, sol_dict

    @staticmethod
    def _read_rules_from_file(rules_path):
        """
        读取规则库

        Parameters
        ----------
        rules_path: str, 规则库文件路径

        Returns
        -------

        """
        rule_dict = defaultdict(FuzzyRule)
        precondition_set = set()
        solution_set = set()
        with open(rules_path, encoding='utf-8') as f:
            num = 0
            for line in f.readlines():
                if line.strip('\n'):
                    rule_dict[num] = FuzzyRule(line)
                    precondition_set.update(rule_dict[num].r_preconditions.keys())
                    solution_set.update(rule_dict[num].r_solutions.keys())
                    num += 1
        return rule_dict, precondition_set, solution_set, num

    def _construct_ruleNet(self):
        """
        构建规则网络

        Returns
        -------

        """
        # 对条件变量建立特征模糊集合
        idx = 0
        for k, v in self.pre_dict.items():
            k_dict = self.pre_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(k, [k_dict['min_val'], k_dict['max_val']], f_level=k_dict['lvl'],
                                                 f_membership_type='gauss')
            idx += k_dict['lvl']
        # 对结果变量建立特征模糊集合
        idx = 0
        for k, v in self.sol_dict.items():
            k_dict = self.sol_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(k, [0., k_dict['step']], f_level=k_dict['lvl'],
                                                 f_membership_type='gauss')
            idx += k_dict['lvl']

        # 条件变量的模糊集合进行连接,用稀疏矩阵表示每条规则中的条件 shape = [rule_num,condition_feature_num*fuzzy_level]
        # 结果变量的连接矩阵, shape = [rule_num, solution_feature_num*fuzzy_level]
        rows = self.rule_nums
        p_cols, s_cols = 0, 0
        for k in self.pre_dict:
            p_cols += self.pre_dict[k]['lvl']
        self.connected_matrix = np.zeros(shape=(rows, p_cols))
        for k in self.sol_dict:
            s_cols += self.sol_dict[k]['lvl']
        self.solution_matrix = np.zeros(shape=(rows, s_cols))
        for row_idx, rule in self.rule_dict.items():
            for name, value in rule.r_preconditions.items():
                if name in self.pre_dict:
                    p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
                    self.connected_matrix[row_idx][p_col_idx] = 1

            for name, value in rule.r_solutions.items():
                if name in self.sol_dict:   
                    s_col_idx = self.sol_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
                    self.solution_matrix[row_idx][s_col_idx] = 1 * value['action']

    def inference(self, x):
        """

        Parameters
        ----------
        x: dict, 变量名和精确值构成的字典

        Returns
        -------

        """
        # 计算输入特征值的所有模糊隶属度
        if x['MT'] is None:
            x['MT'] = 0
        num_degrees = self.connected_matrix.shape[1]
        membership_degrees = np.zeros(shape=(num_degrees,)) + 0.01
        for k in x:

            if k not in self.pre_set:
                continue
            if not self.pre_dict[k]:
                continue
            idx, f_k = self.pre_dict[k]['index'], self.pre_dict[k]['memberships']
            for i in range(f_k.f_level):
                membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)
        # 根据输入计算每条规则的激活程度
        rule_matrix = self.connected_matrix * membership_degrees
        rule_activations = np.zeros(shape=(rule_matrix.shape[0],))
        
        for i in range(self.rule_nums):
            # 计算激活度
            conditions = rule_matrix[i, rule_matrix[i] != 0]
            if conditions.size != 0:
                rule_activations[i] = np.min(conditions)

        # 获取所有规则的可能策略
        points = 200  # 输出值的采样点数量,超参数
        # 构建结果变量输出矩阵
        # 计算输出对每个结果变量的输出影响
        outputs_matrix = None
        rule_to_outputs = np.zeros(shape=(self.solution_matrix.shape[1],))

        for k in self.sol_dict:
            idx = self.sol_dict[k]['index']
            # 获取调整步长
            step = self.sol_dict[k]['step']
            # 对结果变量进行初始化
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

                # 找到所有与该变量当前模糊级别下相关的规则,选择激活程度最大的规则, 并获取调整方向
                rules_by_degree = self.solution_matrix[:, idx + i] != 0
                if rules_by_degree.any():
                    selected_values = np.where(rules_by_degree, rule_activations, -1)

                    rule_to_outputs[idx + i] = np.max(selected_values)
                    rule_selected_list[int(np.argmax(selected_values))] = True
            # 所有模糊级别中激活度最大的规则作为该变量的最终调整方向
            final_rule = np.argmax(np.where(rule_selected_list, rule_activations, -1))

            final_action = self.rule_dict[final_rule].r_solutions[k]['action']
            self.sol_dict[k]['action'] = final_action
            self.sol_dict[k]['reason'] = final_rule

        # 过滤无效的规则激活变量
        # 设定需要填充的阈值
        for k in self.sol_dict:
            idx = self.sol_dict[k]['index']
            lvl = self.sol_dict[k]['lvl']
            # max_threshold = 0.8
            min_threshold = 0.01001
            degree_values = rule_to_outputs[idx:idx + lvl]

            if np.sum(degree_values) < min_threshold:  # 无效激活
                rule_to_outputs[idx:idx + lvl] = 0.

        # 根据模糊值反求每个结果变量的精确输出
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

        results = list(zip(self.sol_dict.keys(), res,
                           map(lambda x: (rule_activations[x['reason']], self.rule_dict[x['reason']]),
                               self.sol_dict.values())))

        # 结果排序
        results = sorted(results, key=lambda x: -x[-1][0])
        return results

    def predict(self, x, top_k=1):
        results = self.inference(x)
        if len(results) <= top_k:
            return results
        else:
            return results[:top_k]

    def predict_json(self, x, top_k=1):
        results = self.predict(x, top_k=top_k)
        json_results = dict((item[0], item[1]) for item in results)
        return json_results


class TskRule:
    """
    规则库中的每一条TSK模糊规则的表示与计算类
    """

    def __init__(self, rule_string=''):
        """
        Parameters
        ----------
        rule_string: 符合规则模板的规则字符串
        """
        self.r_rule = rule_string
        self.r_preconditions, self.r_solutions, self.r_extra = self._rule_process(rule_string)

    def _rule_process(self, rule):
        """
        处理规则字符串,分别存储条件和解决方法
        Parameters
        ----------
        rule: str, 规则字符串

        Returns
        -------
        r_preconditions: dict, 规则条件字典
        r_solutions: dict, 规则解决方法字典
        """
        words_list = rule.strip().split()
        r_preconditions = defaultdict(None)
        r_solutions = defaultdict(None)
        r_extra = defaultdict(None)
        is_pre = False
        for phase in words_list:
            if phase == 'IF':
                is_pre = True
            elif phase in ['Then', 'THEN']:
                is_pre = False
            elif phase == 'AND':
                continue
            else:
                # words = phase.split('_')
                if is_pre:
                    words = phase.split('_')
                    if words[0] not in DEFECT_CONST:
                        # 工艺参数条件,键为参数名,值为参数模糊级别、条件类型
                        r_preconditions[words[0]] = {'name': words[0], 'level': words[1], 'p_type': 'process'}
                    else:
                        # 缺陷类型条件,键为缺陷类型,值为缺陷严重程度、缺陷位置、条件类型
                        r_preconditions[words[0]] = {'name': words[0], 'level': words[1], 'p_type': 'defect'}
                else:
                    # 工艺参数修正,键为参数名,值为参数调整方向、调整模糊级别、条件类型
                    if '_' in phase:
                        # 普通规则，直接执行增加或减少某参数
                        if 'add' or 'reduce' in phase:
                            words = phase.split('_')
                            r_solutions[words[0]] = {'name': words[0], 'action': HS_MAPPING_DICT[words[1]], 'level': words[2],
                                                 's_type': 'process'}
                        # 特殊规则，目标是弹窗显示
                        elif 'popup' in phase:
                            words = phase.split('_')
                            if len(words) == 3:
                                r_solutions[words[0]] = {'name': words[0], 'action': HS_MAPPING_DICT[words[1]],
                                                         'level': words[2],
                                                         's_type': 'process'}
                            elif len(words) == 2:
                                r_extra[phase] = words[1]
                                pass
                    elif '=' in phase:
                        expressions = phase.split('=')
                        items = expressions[1].split('+')
                        parameter_vector = np.zeros(len(items))
                        ratio_vector = np.zeros(len(items))
                        for i in range(0, len(items)):
                            item = items[i].split('*')
                            ratio = item[0]
                            if '(' or ')' in ratio:
                                ratio_vector[i] = float(ratio[1:-1])
                            else:
                                ratio_vector[i] = float(ratio)
                        r_solutions[expressions[0]] = {'name': expressions[0],
                                                 # 'action': HS_MAPPING_DICT[words[1]],
                                                 'parameter_vector': parameter_vector,
                                                 'ratio_vector': ratio_vector,
                                                 's_type': 'process'}

        return r_preconditions, r_solutions, r_extra

    def __repr__(self):
        return self.r_rule



class TskRuleNet:
    """
    规则库中所有TSK规则组成的计算网络
    """
    def __init__(self, rule_array: list, keyword_array: list):
        """
        读入规则本地文件,建立规则库；
        读入特征信息,必须包含特征名、特征范围；
        规则库和模糊化后的特征两者皆有才能进行构建模糊网络进行后续计算。
        Parameters
        ----------
        rules_path: str, 规则文件路径
        ranges_path: str, 特征变量配置文件路径
        """
        # # 规则库输入,并获取当前规则库中所有条件变量和目标变量
        # self.rule_dict, self.pre_set, self.sol_set, self.rule_nums = self._read_rules_from_file(rules_path)
        #
        # # 读取工艺参数配置文件,为规则库中参数设置取值范围
        # self.pre_dict, self.sol_dict = self._read_ranges_from_file(ranges_path)

        self.rule_dict = None
        self.pre_set = None
        self.sol_set = None
        self.rule_nums = None
        self.pre_dict = None
        self.sol_dict = None
        self.extra_dict = None
        self.resolve_input_paras(rule_array, keyword_array)

        # 模糊计算网络构建
        self.connected_matrix = None
        self.solution_matrix = None
        self._construct_tskruleNet()

    def resolve_input_paras(self, rule_array: list, keyword_array: list):
        """
        解析传入的规则以及关键词

        ----------
        Parameters
        ----------
        rule_array: 输入的规则数组, 存储对象
        keyword_array: 输入的关键词数组, 存储对象

        -------
        Returns
        -------
        """
        self.rule_dict = defaultdict(TskRule)
        self.pre_set = set()
        self.sol_set = set()
        self.rule_nums = len(rule_array)

        for i, rule in enumerate(rule_array):
            if 'worse' in rule.get('rule_description'):
                self.rule_nums -= 1
                continue
            self.rule_dict[i] = TskRule(rule.get("rule_description"))
            self.pre_set.update(self.rule_dict[i].r_preconditions.keys())
            self.sol_set.update(self.rule_dict[i].r_solutions.keys())

        self.pre_dict = defaultdict(dict)
        self.sol_dict = defaultdict(dict)

        for item in keyword_array:
            if item["keyword"] in self.pre_set:
                self.pre_dict[item["keyword"]] = {
                    'lvl': item["lvl"],
                    'min_val': item["min_val"],
                    'max_val': item["max_val"],
                    'step': item["step"]
                }
            if item["keyword"] in self.sol_set:
                self.sol_dict[item["keyword"]] = {
                    'lvl': item["lvl"],
                    'min_val': item["min_val"],
                    'max_val': item["max_val"],
                    'step': item["step"]
                }

        return

    def _read_ranges_from_file(self, ranges_path):
        """
        读取变量配置文件

        Parameters
        ----------
        ranges_path: str, 特征变量配置文件路径

        Returns
        -------

        """
        pre_dict = defaultdict(dict)
        sol_dict = defaultdict(dict)
        dtype_dict = {'names': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'),
                      'formats': ('U20', 'i4', 'f4', 'f4', 'f4', 'f4', 'f4')}
        records = np.loadtxt(ranges_path, dtype=dtype_dict, encoding='utf-8', delimiter=',')
        key_list = ['lvl', 'min_val', 'max_val', 'step']
        for name in self.pre_set:
            pre_dict[name] = dict(zip(key_list, *records[records['col1'] == name][['col2', 'col3', 'col4', 'col7']]))
        for name in self.sol_set:
            sol_dict[name] = dict(zip(key_list, *records[records['col1'] == name][['col2', 'col3', 'col4', 'col7']]))
        return pre_dict, sol_dict

    @staticmethod
    def _read_rules_from_file(rules_path):
        """
        读取规则库

        Parameters
        ----------
        rules_path: str, 规则库文件路径

        Returns
        -------

        """
        rule_dict = defaultdict(TskRule)
        precondition_set = set()
        solution_set = set()
        with open(rules_path, encoding='utf-8') as f:
            num = 0
            for line in f.readlines():
                if line.strip('\n'):
                    rule_dict[num] = TskRule(line)
                    precondition_set.update(rule_dict[num].r_preconditions.keys())
                    solution_set.update(rule_dict[num].r_solutions.keys())
                    num += 1
        return rule_dict, precondition_set, solution_set, num

    def _construct_tskruleNet(self):
        """
        构建规则网络

        Returns
        -------

        """
        # 对条件变量建立特征模糊集合
        idx = 0
        for k, v in self.pre_dict.items():
            k_dict = self.pre_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(k, [k_dict['min_val'], k_dict['max_val']], f_level=k_dict['lvl'],
                                                 f_membership_type='gauss')
            idx += k_dict['lvl']
        # 对结果变量建立特征模糊集合
        idx = 0
        for k, v in self.sol_dict.items():
            k_dict = self.sol_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(k, [0., k_dict['step']], f_level=k_dict['lvl'],
                                                 f_membership_type='gauss')
            idx += 1

        # 条件变量的模糊集合进行连接,用稀疏矩阵表示每条规则中的条件 shape = [rule_num,condition_feature_num*fuzzy_level]
        # 结果变量的连接矩阵, shape = [rule_num, solution_feature_num*fuzzy_level]
        rows = self.rule_nums
        p_cols, s_cols = 0, 0
        for k in self.pre_dict:
            p_cols += self.pre_dict[k]['lvl']
        self.connected_matrix = np.zeros(shape=(rows, p_cols))
        for k in self.sol_dict:
            s_cols += 1  # 此处原为模糊等级数，mamdani中一个结论参数对应数个模糊等级，tsk中只需要对应一个
        self.solution_matrix = np.zeros(shape=(rows, s_cols))

        for row_idx, rule in self.rule_dict.items():

            for name, value in rule.r_preconditions.items():
                p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
                self.connected_matrix[row_idx][p_col_idx] = 1

            for name, value in rule.r_solutions.items():
                # s_col_idx = self.sol_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
                s_col_idx = self.sol_dict[name]['index']
                # 特殊规则的结论
                if value['action'] == -2:
                    self.solution_matrix[row_idx][s_col_idx] = 9999.9
                # 普通规则结论
                else:
                    self.solution_matrix[row_idx][s_col_idx] = float(value['level']) * value['action']

            for name, value in rule.r_extra.items():
                self.extra_dict[name] = value

    def tsk_inference(self, x):
        """

        Parameters
        ----------
        x: dict, 变量名和精确值构成的字典

        Returns
        -------

        """
        # 第一层（隶属度层），输入特征值的所有模糊隶属度计算
        num_degrees = self.connected_matrix.shape[1]
        membership_degrees = np.zeros(shape=(num_degrees,)) + 0.0000001
        for k in x:
            if k not in self.pre_set:
                continue
            if not self.pre_dict[k]:
                continue
            idx, f_k = self.pre_dict[k]['index'], self.pre_dict[k]['memberships']
            for i in range(f_k.f_level):
                membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)

        # 第二层（规则层），根据输入计算每条规则的激活程度
        rule_matrix = self.connected_matrix * membership_degrees
        rule_activations = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(self.rule_nums):
            # 计算激活度
            conditions = rule_matrix[i, rule_matrix[i] != 0]  # 筛选出非零数
            if conditions.size != 0:
                # rule_activations[i] = np.min(conditions)  # 最小值作为整条规则的激活度
                rule_activations[i] = np.prod(conditions)  # 各项激活度相乘

        # 第三层（归一化层），对规则的触发强度进行归一化
        activations_sum = np.sum(rule_activations)
        new_activations = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(0, rule_activations.size):
            new_activations[i] = rule_activations[i]/activations_sum

        # 第四层（结论层），输入线性组合计算
        # 初始化一个结论变量矩阵
        cur_params = np.zeros(shape=(self.sol_set.__len__(), ))
        # 将当前值填入结论变量矩阵中
        for k in self.sol_dict:
            if k not in x:
                continue
            else:
                idx = self.sol_dict[k]['index']
                cur_params[idx] = x[k]
        # 计算结论矩阵
        sol_matrix = self.solution_matrix * cur_params

        rule_list = []
        for i in range(0, self.rule_nums):
            rule_list.append(self.rule_dict[i].r_rule)

        calculate_list = []
        sol_len = np.size(sol_matrix, 1)
        for i in range(0, self.rule_nums):
            cal_dict = {}
            darray = self.solution_matrix[i, :]
            sol_darray = sol_matrix[i, :]
            for j in range(0, sol_len):
                if darray[j] != 0:
                    for k, v in self.sol_dict.items():
                        if j == v['index']:
                            cal_dict[k] = sol_darray[j]
            calculate_list.append(cal_dict)

        # # 第五层（输出层），将结论层加权求和
        # sol_param = {}
        # for k in self.sol_set:
        #     idx = self.sol_dict[k]['index']
        #     a = sol_matrix[idx, :]
        #     sol_param[k] = np.dot(sol_matrix[:, idx], new_activations)
        #
        # # 算法输出处理
        # rule_list = []
        # for i in range(0, self.rule_nums):
        #     rule_list.append(self.rule_dict[i].r_rule)
        #
        # calculate_list = []
        # for i in range(0, self.rule_nums):
        #     cal_dict = {}
        #     param_keys = self.rule_dict[i].r_solutions.keys()
        #     for key in param_keys:
        #         cal_dict[key] = sol_param[key]
        #     calculate_list.append(cal_dict)

        res = list(zip(rule_list, new_activations, calculate_list))
        res = sorted(res, key=lambda x: -x[1])

        return res, self.extra_dict

    def predict(self, x, top_k=1):
        results, extra_dict = self.tsk_inference(x)
        if len(results) <= top_k:
            return results, extra_dict
        else:
            return results[:top_k], extra_dict

    def predict_json(self, x, top_k=1):
        results, extra_dict = self.predict(x, top_k=top_k)
        json_results = {}
        for i in range(0, top_k):
            json_results.update(results[i][2])
        return json_results, extra_dict


class ParticularRules:
    """
    规则库中的特殊规则，包括：1.前后件均非已有工艺参数，作弹窗处理
    """
    def __init__(self, import_list):
        """
        Parameters
        ----------
        import_list: 包含有规则语句的规则列表，不包含规则的组件解析信息
        """
        self.adjust_rule_list = self._rule_process(import_list)

    def _rule_process(self, import_list):
        """
        处理规则字符串,分别存储条件和弹窗显示的解决方法
        Parameters
        ----------
        import_list: list, 特定格式的规则列表

        Returns
        -------
        output_list: list, 包含规则组件解析结果的规则列表
        """
        output_list = []
        for a_rule in import_list:
            a_rule_list = {}
            a_rule_list['rule_description'] = a_rule['rule_description']
            words_list = a_rule['rule_description'].strip().split()
            is_pre = False
            for phase in words_list:
                if phase == 'IF':
                    is_pre = True
                elif phase in ['Then', 'THEN']:
                    is_pre = False
                elif phase == 'AND':
                    continue
                else:
                    if is_pre:
                        words = phase.split('_')
                        if words[0] not in DEFECT_CONST:
                            # 工艺参数条件,键为参数名,值为参数模糊级别、条件类型
                            pass
                        else:
                            # 缺陷类型条件,键为缺陷类型,值为缺陷严重程度、缺陷位置、条件类型
                            a_rule_list['rule_defect'] = words[0]
                    else:
                        words = phase.split('_')
                        a_rule_list['rule_output'] = words[2]
            output_list.append(a_rule_list)
        return output_list


class NumTskRule:
    """
    规则库中的每一条具体数值形式的TSK模糊规则的表示与计算类
    """

    def __init__(self, rule_string=''):
        """
        Parameters
        ----------
        rule_string: 符合规则模板的规则字符串
        """
        self.r_rule = rule_string
        self.r_preconditions, self.r_solutions, self.r_extra = self._rule_process(rule_string)

    def _rule_process(self, rule):
        """
        处理规则字符串,分别存储条件和解决方法
        Parameters
        ----------
        rule: str, 规则字符串

        Returns
        -------
        r_preconditions: dict, 规则条件字典
        r_solutions: dict, 规则解决方法字典
        """
        words_list = rule.strip().split()
        r_preconditions = defaultdict(None)
        r_solutions = defaultdict(None)
        r_extra = defaultdict(None)
        is_pre = False
        for phase in words_list:
            if phase == 'IF':
                is_pre = True
            elif phase in ['Then', 'THEN']:
                is_pre = False
            elif phase == 'AND':
                continue
            else:
                # words = phase.split('_')
                if is_pre:
                    words = phase.split('_')
                    if words[0] not in DEFECT_CONST:
                        # 工艺参数条件,键为参数名,值为参数模糊级别、条件类型
                        r_preconditions[words[0]] = {'name': words[0], 'level': words[1], 'p_type': 'process'}
                    else:
                        # 缺陷类型条件,键为缺陷类型,值为缺陷严重程度、缺陷位置、条件类型
                        r_preconditions[words[0]] = {'name': words[0], 'level': words[1], 'p_type': 'defect'}
                else:
                    # 工艺参数修正,键为参数名,值为参数调整方向、调整模糊级别、条件类型
                    if '_' in phase:
                        # 普通规则，直接执行增加或减少某参数
                        if 'add' or 'reduce' in phase:
                            words = phase.split('_')
                            r_solutions[words[0]] = {'name': words[0], 'action': HS_MAPPING_DICT[words[1]], 'level': words[2],
                                                 's_type': 'process'}
                        # 特殊规则，目标是弹窗显示
                        elif 'popup' in phase:
                            words = phase.split('_')
                            if len(words) == 3:
                                r_solutions[words[0]] = {'name': words[0], 'action': HS_MAPPING_DICT[words[1]],
                                                         'level': words[2],
                                                         's_type': 'process'}
                            elif len(words) == 2:
                                r_extra[phase] = words[1]
                                pass
                    elif '=' in phase:
                        expressions = phase.split('=')
                        items = expressions[1].split('+')
                        parameter_vector = np.zeros(len(items))
                        ratio_vector = np.zeros(len(items))
                        for i in range(0, len(items)):
                            item = items[i].split('*')
                            ratio = item[0]
                            if '(' or ')' in ratio:
                                ratio_vector[i] = float(ratio[1:-1])
                            else:
                                ratio_vector[i] = float(ratio)
                        r_solutions[expressions[0]] = {'name': expressions[0],
                                                 # 'action': HS_MAPPING_DICT[words[1]],
                                                 'parameter_vector': parameter_vector,
                                                 'ratio_vector': ratio_vector,
                                                 's_type': 'process'}

        return r_preconditions, r_solutions, r_extra

    def __repr__(self):
        return self.r_rule


class NumTskRuleNet:
    """
    规则库中所有TSK规则组成的计算网络
    """
    def __init__(self, rule_array: list, keyword_array: list, priority_array: list):
        """
        读入规则本地文件,建立规则库；
        读入特征信息,必须包含特征名、特征范围；
        规则库和模糊化后的特征两者皆有才能进行构建模糊网络进行后续计算。
        Parameters
        ----------
        rules_path: str, 规则文件路径
        ranges_path: str, 特征变量配置文件路径
        """
        # # 规则库输入,并获取当前规则库中所有条件变量和目标变量
        # self.rule_dict, self.pre_set, self.sol_set, self.rule_nums = self._read_rules_from_file(rules_path)
        #
        # # 读取工艺参数配置文件,为规则库中参数设置取值范围
        # self.pre_dict, self.sol_dict = self._read_ranges_from_file(ranges_path)

        self.rule_dict = None
        self.pre_set = None
        self.sol_set = None
        self.rule_nums = None
        self.pre_dict = None
        self.sol_dict = None
        self.extra_dict = None
        self.rule_classify = [] # 数值规则为0，百分比规则为1
        self.rule_solution = []
        self.priority_array = priority_array
        self.resolve_input_paras(rule_array, keyword_array)

        # 模糊计算网络构建
        self.connected_matrix = None
        self.solution_matrix = None
        self.percent_set = None
        self._construct_numtskruleNet()

    def resolve_input_paras(self, rule_array: list, keyword_array: list):
        """
        解析传入的规则以及关键词

        ----------
        Parameters
        ----------
        rule_array: 输入的规则数组, 存储对象
        keyword_array: 输入的关键词数组, 存储对象

        -------
        Returns
        -------
        """
        self.rule_dict = defaultdict(TskRule)
        self.pre_set = set()
        self.sol_set = set()
        self.rule_nums = len(rule_array)
        self.rule_classify = [0] * self.rule_nums

        for i, rule in enumerate(rule_array):
            if 'worse' in rule.get('rule_description'):
                self.rule_nums -= 1
                continue
            if '%' in rule.get('rule_description'):
                self.rule_classify[i] = 1
            self.rule_dict[i] = NumTskRule(rule.get("rule_description"))
            self.pre_set.update(self.rule_dict[i].r_preconditions.keys())
            self.sol_set.update(self.rule_dict[i].r_solutions.keys())
            self.rule_solution.append(list(self.rule_dict[i].r_solutions.keys())[0])

        self.pre_dict = defaultdict(dict)
        self.sol_dict = defaultdict(dict)

        for item in keyword_array:
            if item["keyword"] in self.pre_set:
                self.pre_dict[item["keyword"]] = {
                    'lvl': item["lvl"],
                    'min_val': item["min_val"],
                    'max_val': item["max_val"],
                    'step': item["step"]
                }
            if item["keyword"] in self.sol_set:
                self.sol_dict[item["keyword"]] = {
                    'lvl': item["lvl"],
                    'min_val': item["min_val"],
                    'max_val': item["max_val"],
                    'step': item["step"]
                }

        return

    def _read_ranges_from_file(self, ranges_path):
        """
        读取变量配置文件

        Parameters
        ----------
        ranges_path: str, 特征变量配置文件路径

        Returns
        -------

        """
        pre_dict = defaultdict(dict)
        sol_dict = defaultdict(dict)
        dtype_dict = {'names': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'),
                      'formats': ('U20', 'i4', 'f4', 'f4', 'f4', 'f4', 'f4')}
        records = np.loadtxt(ranges_path, dtype=dtype_dict, encoding='utf-8', delimiter=',')
        key_list = ['lvl', 'min_val', 'max_val', 'step']
        for name in self.pre_set:
            pre_dict[name] = dict(zip(key_list, *records[records['col1'] == name][['col2', 'col3', 'col4', 'col7']]))
        for name in self.sol_set:
            sol_dict[name] = dict(zip(key_list, *records[records['col1'] == name][['col2', 'col3', 'col4', 'col7']]))
        return pre_dict, sol_dict

    @staticmethod
    def _read_rules_from_file(rules_path):
        """
        读取规则库

        Parameters
        ----------
        rules_path: str, 规则库文件路径

        Returns
        -------

        """
        rule_dict = defaultdict(TskRule)
        precondition_set = set()
        solution_set = set()
        with open(rules_path, encoding='utf-8') as f:
            num = 0
            for line in f.readlines():
                if line.strip('\n'):
                    rule_dict[num] = NumTskRule(line)
                    precondition_set.update(rule_dict[num].r_preconditions.keys())
                    solution_set.update(rule_dict[num].r_solutions.keys())
                    num += 1
        return rule_dict, precondition_set, solution_set, num

    def _construct_numtskruleNet(self):
        """
        构建规则网络

        Returns
        -------

        """
        # 对条件变量建立特征模糊集合
        idx = 0
        for k, v in self.pre_dict.items():
            k_dict = self.pre_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(k, [k_dict['min_val'], k_dict['max_val']], f_level=k_dict['lvl'],
                                                 f_membership_type='gauss')
            idx += k_dict['lvl']
        # 对结果变量建立特征模糊集合
        idx = 0
        for k, v in self.sol_dict.items():
            k_dict = self.sol_dict[k]
            k_dict['index'] = idx
            k_dict['memberships'] = FuzzyFeature(k, [0., k_dict['step']], f_level=k_dict['lvl'],
                                                 f_membership_type='gauss')
            idx += 1

        # 条件变量的模糊集合进行连接,用稀疏矩阵表示每条规则中的条件 shape = [rule_num,condition_feature_num*fuzzy_level]
        # 结果变量的连接矩阵, shape = [rule_num, solution_feature_num*fuzzy_level]
        rows = self.rule_nums
        p_cols, s_cols = 0, 0
        for k in self.pre_dict:
            p_cols += self.pre_dict[k]['lvl']
        self.connected_matrix = np.zeros(shape=(rows, p_cols))
        for k in self.sol_dict:
            s_cols += 1  # 此处原为模糊等级数，mamdani中一个结论参数对应数个模糊等级，tsk中只需要对应一个
        self.solution_matrix = np.zeros(shape=(rows, s_cols))
        self.percent_set = []

        for row_idx, rule in self.rule_dict.items():

            for name, value in rule.r_preconditions.items():
                if self.pre_dict[name]:
                    p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
                    if row_idx < len(self.connected_matrix):
                        self.connected_matrix[row_idx][p_col_idx] = 1
                    else:
                        logging.error(f"index {row_idx} is out of bounds for axis 0 with size {len(self.connected_matrix)}")
                else:
                    logging.error(f"self.pre_dict中没有{name}")

            for name, value in rule.r_solutions.items():
                # s_col_idx = self.sol_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
                if self.sol_dict[name]:
                    s_col_idx = self.sol_dict[name]['index']
                    # 特殊规则的结论
                    if value['action'] == -2:
                        self.solution_matrix[row_idx][s_col_idx] = 9999.9
                    # 普通规则结论
                    else:
                        if row_idx < len(self.solution_matrix):
                            if '%' in value['level']:
                                self.percent_set.append(name)
                                self.solution_matrix[row_idx][s_col_idx] = float(value['level'].rstrip('%')) * value['action']/100
                            else:
                                self.solution_matrix[row_idx][s_col_idx] = float(value['level']) * value['action']
                        else:
                            logging.error(f"index {row_idx} is out of bounds for axis 0 with size {len(self.solution_matrix)}")
                else:
                    logging.error(f"self.sol_dict中没有{name}")

            for name, value in rule.r_extra.items():
                self.extra_dict[name] = value

    def tsk_inference(self, x, priority_array):
        """

        Parameters
        ----------
        x: dict, 变量名和精确值构成的字典

        Returns
        -------

        """
        # 第一层（隶属度层），输入特征值的所有模糊隶属度计算
        num_degrees = self.connected_matrix.shape[1]
        membership_degrees = np.zeros(shape=(num_degrees,)) + 0.0000001
        for k in x:
            if k not in self.pre_set:
                continue
            if not self.pre_dict[k]:
                continue
            idx, f_k = self.pre_dict[k]['index'], self.pre_dict[k]['memberships']
            for i in range(f_k.f_level):
                membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)

        # 第二层（规则层），根据输入计算每条规则的激活程度
        rule_matrix = self.connected_matrix * membership_degrees
        rule_activations = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(self.rule_nums):
            # 计算激活度
            conditions = rule_matrix[i, rule_matrix[i] != 0]  # 筛选出非零数
            if conditions.size != 0:
                # rule_activations[i] = np.min(conditions)  # 最小值作为整条规则的激活度
                rule_activations[i] = np.prod(conditions)  # 各项激活度相乘

        # 第三层（归一化层），对规则的触发强度进行归一化
        activations_sum = np.sum(rule_activations)
        new_activations = np.zeros(shape=(rule_matrix.shape[0],))
        for i in range(0, rule_activations.size):
            new_activations[i] = rule_activations[i]/activations_sum
        activations_with_priority = new_activations * priority_array

        # 第四层（结论层），输入线性组合计算
        # 初始化一个结论变量矩阵
        cur_params = np.ones(shape=(self.connected_matrix.shape[0], ))
        # 将当前值填入结论变量矩阵中
        for i in range(self.rule_nums):
            k = self.rule_solution[i]
            if k not in x:
                continue
            else:
                if self.rule_classify[i] == 1:
                    cur_params[i] = x[k]
        # 计算结论矩阵
        sol_matrix = self.solution_matrix.T * cur_params
        # sol_matrix = self.solution_matrix

        rule_list = []
        for i in range(0, self.rule_nums):
            rule_list.append(self.rule_dict[i].r_rule)

        calculate_list = []
        sol_len = np.size(sol_matrix, 0)
        for i in range(0, self.rule_nums):
            cal_dict = {}
            darray = self.solution_matrix[i, :]
            sol_darray = sol_matrix[:, i]
            for j in range(0, sol_len):
                if darray[j] != 0:
                    for k, v in self.sol_dict.items():
                        if j == v['index']:
                            cal_dict[k] = sol_darray[j]
            calculate_list.append(cal_dict)

        # # 第五层（输出层），将结论层加权求和
        # sol_param = {}
        # for k in self.sol_set:
        #     idx = self.sol_dict[k]['index']
        #     a = sol_matrix[idx, :]
        #     sol_param[k] = np.dot(sol_matrix[:, idx], new_activations)
        #
        # # 算法输出处理
        # rule_list = []
        # for i in range(0, self.rule_nums):
        #     rule_list.append(self.rule_dict[i].r_rule)
        #
        # calculate_list = []
        # for i in range(0, self.rule_nums):
        #     cal_dict = {}
        #     param_keys = self.rule_dict[i].r_solutions.keys()
        #     for key in param_keys:
        #         cal_dict[key] = sol_param[key]
        #     calculate_list.append(cal_dict)

        res = list(zip(rule_list, activations_with_priority, calculate_list))
        res = sorted(res, key=lambda x: -x[1])

        return res, self.extra_dict

    def predict(self, x, top_k=1):
        results, extra_dict = self.tsk_inference(x, self.priority_array)
        if len(results) <= top_k:
            return results, extra_dict
        else:
            return results[:top_k], extra_dict

    def predict_json(self, x, top_k=1):
        results, extra_dict = self.predict(x, top_k=top_k)
        json_results = {}
        for i in range(0, top_k):
            json_results.update(results[i][2])

        return json_results, extra_dict