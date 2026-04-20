import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings")# project_name 项目名称
django.setup()

from django.conf import settings
import numpy as np
from base.settings import BASE_DIR

'''
    范围参数变换文件（完善中）
'''

class rangeTransferData:

    def __init__(self):
        range_path = settings.RANGES_PATH
        config_dtype_dict = {'names': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'),
                             'formats': ('U20', 'i4', 'f4', 'f4', 'f4', 'f4', 'f4')}
        params_range = np.loadtxt(range_path, dtype=config_dtype_dict, encoding='utf-8', delimiter=',')
        mid_dict = dict(map(lambda x: (x[0], x[1:]), params_range.tolist()))
        params_range_dict = {}
        for k, t in mid_dict.items():
            params_range_dict[k] = {
                'Name': k,
                'level': t[0],
                'all_range_min': t[1],
                'all_range_max': t[2],
                'action_range_min': t[3],
                'action_range_max': t[4],
                'action_maxVal': t[5],
            }
        self.params_range_dict = params_range_dict



    def transfer_by_stage(self, inject_stage, hold_stage):
        if inject_stage == 1:
            self.params_range_dict['IDT1']['all_range_max'] = float(100)
            self.params_range_dict['IDT1']['action_maxVal'] = float(15)
        elif inject_stage == 2:
            self.params_range_dict['IDT1']['all_range_max'] = float(15)
            self.params_range_dict['IDT1']['action_maxVal'] = float(6)
            self.params_range_dict['IDT2']['all_range_max'] = float(15)
            self.params_range_dict['IDT2']['action_maxVal'] = float(6)
        elif inject_stage == 3:
            pass
        elif inject_stage == 4:
            pass
        elif inject_stage == 5:
            pass
        elif inject_stage == 6:
            pass

        if hold_stage == 1:
            pass
        elif hold_stage == 2:
            pass
        elif hold_stage == 3:
            pass
        elif hold_stage == 4:
            pass
        elif hold_stage == 5:
            pass

        write_range_csv(self.params_range_dict)

    def tranfer_by_current(self, current_value_dict):
        pass


def write_range_csv(key_dict):
    rule_keywords_list = list(key_dict.values())
    range_path = BASE_DIR + "\\mdprocess\\utils\\fuzzykit\\range_test.csv"
    whole_key_list = []
    with open(range_path, 'w+', encoding='utf-8') as f:
        whole_key_list.append('#Name(变量名),level(模糊分级), all_range_min(参数取值范围最小值),all_range_max(参数取值范围最大值),action_range_min(参数调整区间最小值),action_range_max(参数调整区间最大值),action_maxVal(参数单次最大调整量)'+"\n")
        whole_key_list.append('#Defect' + "\n")
        for one_key in rule_keywords_list:
            if rule_keywords_list.index(one_key) == 8:
                whole_key_list.append('#Parameter' + "\n")
            one_key_line = ''
            one_key_line = one_key_line + (one_key['Name'] + ',')
            one_key_line = one_key_line + (str(one_key['level']) + ',')
            one_key_line = one_key_line + (str(one_key['all_range_min']) + ',')
            one_key_line = one_key_line + (str(one_key['all_range_max']) + ',')
            one_key_line = one_key_line + (str(one_key['action_range_min']) + ',')
            one_key_line = one_key_line + (str(one_key['action_range_max']) + ',')
            one_key_line = one_key_line + (str(one_key['action_maxVal']) + "\n")
            whole_key_list.append(one_key_line)
        f.writelines(list(map(lambda x: x, whole_key_list)))



# transfer_by_stage(4, 3)