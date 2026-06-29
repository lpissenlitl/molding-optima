import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings")# project_name 项目名称
django.setup()

import numpy as np
from mdprocess.utils.fuzzykit.fuzzy_core.models import nets
from mdprocess.services.process_optimize_service import optimize_process, get_process_optimization


# 这是一个缺陷优化算法测试文件
def test_many_molds():
    # test_data = [4.0, 133.0, 36.3, 0.0, 133.0, 36.3, 0.0, 133.0, 36.3, 0.0, 133.0, 36.3, 0.0, 0.8, 20.0, 1.0, 36.58,
    #              30.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 30.0, 1.0, 21.27, 2.0, 74.25, 10.0,
    #              22.82, 74.25, 10.0, 24.36, 0.0, 0.0, 26.36, 15.0, 0.0, 235.0, 240.0, 235.0, 230.0, 225.0, 220.0,
    #              215.0, 2.0, 2.0, 3.0]
    # data_dict = inputs_to_dict(test_data)
    model = nets.FuzzyRuleNet("E:/mydoc/HsMoldingService-master/mdprocess/utils/fuzzykit/fuzzy_core/dataset/Rule.dat", "E:/mydoc/HsMoldingService-master/mdprocess/utils/fuzzykit/fuzzy_core/dataset/process_ranges.csv")
    current_value_dict = {
                 'IP0': 50,
                 'IV0': 18,
                 'IL0': 90,
                 'IP1': 129,
                 'IV1': 20,
                 'IL1': 28,
                 'IP2': 123,
                 'IV2': 20,
                 'IL2': 24.53,
                 'IP3': 136,
                 'IV3': 16,
                 'IL3': 21.15,
                 'IP4': 129,
                 'IV4': 16,
                 'IL4': 21.61,
                 'IP5': 123,
                 'IV5': 20,
                 'IL5': 21.15,
                 'IT': 0.8,
                 'CT': 20.0,
                 'PP0': 80,
                 'PV0': 20,
                 'PT0': 5,
                 'PP1': 101,
                 'PV1': 24.0,
                 'PT1': 5,
                 'PP2': 50.5,
                 'PV2': 24,
                 'PT2': 5.5,
                 'PP3': 0.0,
                 'PV3': 12.0,
                 'PT3': 0.0,
                 'PP4': 0.0,
                 'PV4': 6.0,
                 'PT4': 0.0,
                 'VPTL': 17,
                 'MSR0': 33,
                 'MBP0': 2,
                 'ML0': 22.02,
                 'MSR1': 66,
                 'MBP1': 5,
                 'ML1': 23.55,
                 'MSR2': 98,
                 'MBP2': 8,
                 'ML2': 25.07,
                 'MSR3': 131,
                 'MBP3': 10,
                 'ML3': 26.09,
                 'MEL': 180,
                 'DDBM': 0.0,
                 'DVBM': 0.0,
                 'DDAM': 26.36,
                 'DVAM': 15.0,
                 'NT': 260.,
                 'BT1': 240.0,
                 'BT2': 235.0,
                 'BT3': 230.0,
                 'BT4': 225.0,
                 'BT5': 220.0,
                 # 'BT6': 220.0,
                 # 'BT7': 220.0,
                 # 'BT8': 220.0,
                 # 'BT9': 220.0,
                 'SHORTSHOT': 0.2,
                 'DLSHORTSHOT': 0,
                 'shortshot_feedback': 0,
                 'FLASH': 0.,
                 # 'DLFLASH': 0,
                 # 'flash_feedback': 0,
                 'SHRINKAGE': 0.,
                 # 'DLSHRINKAGE': 0,
                 'shrinkage_feedback': 0,
                 'WELDLINE': 0.,
                 # 'DLWELDLINE': 0,
                 'weldline_feedback': 0,
                 'ABERRATION': 0.,
                 'DLABERRATION': 0,
                 'aberration_feedback': 0,
                 'AIRTRAP': 0.,
                 # 'DLAIRTRAP': 0,
                 'airtrap_feedback': 0,
                 'injection_stage': 3,
                 'metering_stage': 2,
                 'barrel_temperature_stage': 6,
                 'machine_id': 5,
                 'holding_stage': 1,
                 'product_weight': 160,
                 # 'actual_product_weight': 150
                 'actual_product_weight': None,
                 'opt_nums': 2,
                 # 'process_id': 1
                 # 'MELfeedback': 0.99,
                 # 'VPTLfeedback': 0.99,
                 # 'IPfeedback': 0.99
                 }
    one_dict = {'metering_stage': 1, 'PV4': 0.0, 'PP4': 0.0, 'PT4': 0.0, 'barrel_temperature_stage': 6, 'DVAM': 8.0,
                'PP0': 0.0, 'PT0': 0.0, 'DDBM': 0.0, 'injection_stage': 1, 'PV3': 0.0, 'ML1': 22.34, 'MBP2': 0.0,
                'DLAIRTRAP': 0.0, 'machine_id': 5, 'BT6': None, 'DLSHRINKAGE': 0.0, 'VPTL': 21.04, 'IP1': 1.0,
                'WELDLINE': 0.0, 'MEL': 24.34, 'IP0': 1.0, 'DLWELDLINE': 0.0, 'IP2': 1.0, 'BT2': 240.0,
                'ABERRATION': 0.0, 'PV1': 0.0, 'ML3': 22.34, 'BT4': 220.0, 'FLASH': 0.0, 'IV1': 0.0, 'CT': 20.0,
                'MBP0': 0.0, 'IV5': 0.0, 'PP3': 0.0, 'BT1': 250.0, 'DLSHORTSHOT': 0.1, 'DLABERRATION': 0.0, 'DVBM': 8.0,
                'PT3': 0.0, 'MSR1': 0.0, 'IP5': 1.0, 'IV2': 0.0, 'BT5': None, 'IP4': 1.0, 'DDAM': 2.0, 'ML0': 22.34,
                'SHORTSHOT': 0.3, 'MSR3': 0.0, 'PT1': 0.0, 'BT8': None, 'MBP1': 0.0, 'IL0': 0.0, 'IV0': 0.0, 'PP1': 0.0,
                'DLFLASH': 0.0, 'IV3': 0.0, 'AIRTRAP': 0.0, 'PV2': 0.0, 'IV4': 0.0, 'IT': 0.8, 'MBP3': 0.0, 'NT': 245.0,
                'PP2': 0.0, 'SHRINKAGE': 0.0, 'IP3': 1.0, 'ML2': 22.34, 'holding_stage': 1, 'BT9': None, 'PT2': 0.0,
                'BT7': None, 'MSR2': 0.0, 'BT3': 230.0, 'PV0': 0.0, 'MSR0': 0.0}

    # 去除多出的注射、保压和计量段
    injection_stage = current_value_dict['injection_stage']
    holding_stage = current_value_dict['holding_stage']
    metering_stage = current_value_dict['metering_stage']
    for i in range(injection_stage, 6):
        current_value_dict.pop('IP' + str(i))
        current_value_dict.pop('IV' + str(i))
        current_value_dict.pop('IL' + str(i))
    for i in range(holding_stage, 5):
        current_value_dict.pop('PP' + str(i))
        current_value_dict.pop('PV' + str(i))
        current_value_dict.pop('PT' + str(i))
    for i in range(metering_stage, 4):
        current_value_dict.pop('MSR' + str(i))
        current_value_dict.pop('MBP' + str(i))
        current_value_dict.pop('ML' + str(i))

    dl_dict = {}
    for k in list(current_value_dict.keys()):
        if k in {'DLSHORTSHOT', 'DLFLASH', 'DLSHRINKAGE', 'DLWELDLINE', 'DLABERRATION', 'DLAIRTRAP',
                 'DLGASVEINS', 'DLMATERIALFLOWER'}:
            # if k[:2] == 'DL':
            if current_value_dict[k[2:]] != 0:
                dl_dict[k] = current_value_dict[k]
    for k in dl_dict:
        if dl_dict[k] != 0:
            current_value_dict[k + str(dl_dict[k])] = 0.99
        else:
            current_value_dict[k + '1'] = 0.99

    # 对于缩水缺陷新增保压段数的判断

    # 添加段数注射、保压、计量段数参数
    injection_stage = current_value_dict['injection_stage']
    metering_stage = current_value_dict['metering_stage']
    current_value_dict['injectstage' + str(injection_stage)] = 0.95
    current_value_dict['holdingstage' + str(holding_stage)] = 0.95
    current_value_dict['meteringstage' + str(metering_stage)] = 0.95

    # 找出字典中缺陷对应的键值对
    defect_dict = get_all_defect(current_value_dict)
    # 若有短射缺陷，则优先优化短射
    if current_value_dict['SHORTSHOT'] != 0:
        for key in defect_dict:
            current_value_dict[key] = 0
        current_value_dict['SHORTSHOT'] = defect_dict['SHORTSHOT']
    # 对六种缺陷的值做判断，把值为0的缺陷删去，只保留存在的缺陷
    for key in list(defect_dict):
        if current_value_dict.get(key) == 0:
            current_value_dict.pop(key)
            defect_dict.pop(key)

    update_dict = model.predict_json(current_value_dict, top_k=1)

    # 取缺陷最大值作为更新时的输入
    defect_degree = max(defect_dict.values())
    # 更新页面工艺参数
    if defect_degree == 0.2:
        w = 0.68
    elif defect_degree == 0.5:
        w = 1.29
    elif defect_degree == 0.8:
        w = 1.93
    elif defect_degree == 0.9:
        w = 2.57
    else:
        w = 1.0
    current_value_dict['ML1'] = current_value_dict.get('MEL')

    for k in update_dict:
        # 如果优化后的值小于0,则限定为0
        if current_value_dict.get(k) + update_dict.get(k) < 0:
            current_value_dict[k] = 0

        # VPTL即注射末段的位置
        if k == 'VPTL':
            current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 2)
            current_value_dict['IL' + str(injection_stage - 1)] = current_value_dict[k]
        elif k in ['IL0', 'IL1', 'IL2', 'IL3', 'IL4', 'IL5'] and k[2] == str(current_value_dict['injection_stage'] - 1):
            current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 2)
            current_value_dict['VPTL'] = current_value_dict[k]

        # 保压时间需保留一位小数
        elif k in ['PT0', 'PT1', 'PT2', 'PT3', 'PT4']:
            current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 1)

        # 储料终止位置=计量末段位置+储后距离，同时其他段也相应变化
        elif k == 'MEL':
            current_value_dict['MEL'] = round(current_value_dict['MEL'] + update_dict.get(k) * w, 2)
            ML = round(current_value_dict['MEL'] - current_value_dict['DDAM'], 2)
            ML_length = current_value_dict["metering_stage"]  # measurelength
            d = {1: [1], 2: [1, 0.5], 3: [1, 0.7, 0.3], 4: [1, 0.75, 0.5, 0.25]}
            f_injection_length = ML - 21  # fInjectionLen
            for i in range(ML_length):
                current_value_dict['ML' + str(ML_length - i - 1)] = round(d.get(ML_length)[i] * f_injection_length + 21,
                                                                          2)
                print(current_value_dict['ML' + str(ML_length - i - 1)])
        else:
            if k in current_value_dict:
                current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w)

                # 料筒温度设为各段联调
                if k == 'BT1':
                    for i in range(2, 6):
                        current_value_dict['BT' + str(i)] = current_value_dict['BT' + str(i - 1)] - 5
            else:
                # 考虑修正时增加保压段数，从而新增了参数的情况
                if k in ['PT0', 'PT1', 'PT2', 'PT3', 'PT4']:
                    current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 1)
                else:
                    current_value_dict[k] = round(update_dict.get(k) * w)

    return current_value_dict


def get_all_defect(info_dict):
    # 获取缺陷程度信息
    d_dict = {}
    for key, value in info_dict.items():
        if key in ['SHORTSHOT', 'FLASH', 'SHRINKAGE', 'WELDLINE', 'ABERRATION', 'AIRTRAP', 'GASVEINS',
                   'MATERIALFLOWER']:
            d_dict[key] = value
    return d_dict
test_many_molds()
