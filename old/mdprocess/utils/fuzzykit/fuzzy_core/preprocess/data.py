import numpy as np
import pandas as pd

from mdprocess.utils.fuzzykit.macros import HS_DEFECT_DICT


def trainset_from_csv(csv_path, config_path):
    config_dtype_dict = {'names': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'),
                         'formats': ('U20', 'i4', 'f4', 'f4', 'f4', 'f4', 'f4')}
    mapping_dict = {
        0: 'low',
        1: 'mid',
        2: 'high',
    }
    # 读取原始数据
    df = pd.read_csv(csv_path)
    # 删除名称列,添加标签列,创建空数据集
    cols = df.columns.tolist()
    del cols[-8:]
    cols.append('Class')
    train_set = pd.DataFrame(None, columns=cols)
    defect_set = []
    set_defect_dict = {}
    # 新增标签列
    # 遍历所有数据行,建立数据标签
    rows = df.shape[0]
    for i in range(1, rows):

        # 计算缺陷变化
        defect_tmp = df.iloc[-1, -8:] - df.iloc[i - 1, -8:]

        defect_diff = defect_tmp[defect_tmp < 0]
        defect_set.append(defect_diff)
        defect_diff_dict = defect_diff.to_dict()
        # 计算与上一模的参数变化
        tmp = df.iloc[-1, 1:-8] - df.iloc[i - 1, 1:-8]
        # tmp = df.iloc[i, 1:] - df.iloc[i - 1, 1:]
        diff = tmp[tmp != 0]
        diff_dict = diff.to_dict()
        # 翻译模次之间的差别数据,查找调整策略
        # 读取配置文件信息,转换成字典形式
        params_config = np.loadtxt(config_path, dtype=config_dtype_dict, encoding='utf-8', delimiter=',')
        params_config_dict = dict(map(lambda x: (x[0], x[1:]), params_config.tolist()))
        # 根据差异数据,每个差异变量,生成一行数据,建立新标签
        for k, val in diff_dict.items():
            lvl = int(params_config_dict[k][0])
            step = params_config_dict[k][-1]
            label = k
            if val > 0:
                label += '_add'
            else:
                label += '_reduce'
            # 根据可调整范围,计算调整程度
            bins = np.linspace(0, step, lvl + 1)
            degree_idx = np.digitize(abs(val), bins, right=True) - 1
            if degree_idx == lvl:  # 多级增加触发条件
                label += '_' + mapping_dict[2]
            else:
                label += '_' + mapping_dict[degree_idx]
            # 训练数据行,上一模状态数据加上当前模缺陷数据,以及标签
            set_defect_dict[label] = defect_diff_dict
            new_data = pd.concat([df.iloc[i, 1:-8], df.iloc[i, -8:]])
            # new_data = df.iloc[i, 1:]
            new_data['Class'] = label
            train_set.loc[train_set.shape[0]] = new_data
    return train_set, set_defect_dict
