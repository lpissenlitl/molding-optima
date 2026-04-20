import numpy as np
import pandas as pd

from django.conf import settings


def defect_translate(defect):
    defect_output = []
    for index, value in defect.items():
        label = index
        if value >= -0.3:
            label += '_low'
        elif -0.6 <= value < -0.3:
            label += '_mid'
        else:
            label += '_high'
        defect_output.append(label)
    return defect_output

def  rule_standard(label, rules, defect):
    cond_split_words = "^"

    def trans_func(rule):
        if isinstance(rule, str):
            rule = rule.lstrip('[').rstrip(']')
            conds = rule.split(cond_split_words)
            # conds = list(map(lambda x: x.replace('=', '_(') + ')', conds))
            output_dict = {}
            if conds[0] == 'True':
                standard_rule = []
                a_rule = ' '.join(['IF', ' AND '.join(defect), 'THEN', label])
                standard_rule.extend([a_rule])
                return standard_rule
            else:
                for k in conds:
                    a = k.split('=')
                    name = a[0]
                    value = float(a[1])
                    # 根据name获取到取值范围
                    config_path = settings.RANGES_PATH
                    dtype_dict = {'names': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'),
                                         'formats': ('U20', 'i4', 'f4', 'f4', 'f4', 'f4', 'f4')}
                    param_config = np.loadtxt(config_path, dtype=dtype_dict, encoding='utf-8', delimiter=',')
                    param_config_dict = dict(map(lambda x: (x[0], x[1:]), param_config.tolist()))
                    value_min = float(param_config_dict[name][3])
                    value_max = float(param_config_dict[name][4])
                    # 将取值范围分为三等：low、mid、high，根据value获取等级
                    p = (value_max - value_min)/3
                    v_degree = ''
                    if value_min <= value <= value_min + p:
                        v_degree = 'low'
                    elif value_min + p <= value <= value_min + 2*p:
                        v_degree = 'mid'
                    elif value_min + 2*p <= value <= value_max:
                        v_degree = 'high'
                    # 完善输出规则格式
                    output_dict[k] = name + '_' + v_degree
                standard_rule = []
                for word in defect:
                    output = list(output_dict.values())
                    output.insert(0, word)
                    a_rule = ' '.join(['IF', ' AND '.join(output), 'THEN', label])
                    standard_rule.extend([a_rule])
                return standard_rule
        else:
            raise TypeError("rules must contain rule in string！")
    st_rules = []
    for i in rules:
        st_rules += trans_func(i)
    # st_rules = list(map(trans_func, rules))
    return st_rules


