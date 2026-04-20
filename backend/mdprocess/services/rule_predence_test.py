# 建立子规则库时，根据用户选择的方案自主规定规则优先级
# 输入：defect:单个缺陷；ways_list:方案列表
def rule_predence_test(defect, ways_list):

    # 对应每一个检查项目
    # 格式['MEL', 'IP0', 'IV0']
    param_list = []
    # 对应这一条检查项目的现状:是大了,还是小了;不合理的反义词:合理
    current = {}
    # 对应这一条检查项目的调整方案
    # 格式:{'MEL': 'MEL_add_2', 'IV0': 'IV0_add_1', 'IP0': 'IP0_add_1.5', 'NT': 'NT_reduce_1', 'BT': 'BT_reduce_1'}
    ways_dict = {}
    for way in ways_list:
        solution = way[way.index("THEN")+5:]
        words = solution.split('_')
        way_param = words[0]
        param_list.append(way_param)
        current[way_param] = way[way.index(way_param)+len(way_param):way.index("THEN")-1]
        ways_dict[way_param] = solution

    num_dict = {}
    len_of_predence = len(get_defect_order(defect))

    # 初始化优先级列表
    for i in range(len_of_predence):
        num_dict[i] = []
    num_dict[len_of_predence] = []

    # 将用户选择的方案填充到优先级列表中
    for param in param_list:
        find = 0
        for i in range(len_of_predence):
            if param in get_defect_order(defect)[i]:
                num_dict[i].append(param)
                find = 1
        # 在优先级里没有找到,那么放在最后的列表里
        if find == 0:
            num_dict[len_of_predence].append(param)

    # 初始化rule_list
    rule_list = []


    # 根据优先级列表生成规则
    for level in ["_low ", "_mid ", "_high "]:
        advance_list = []
        for i in range(len_of_predence+1):
            if i == 0:
                advance = 'IF '+defect+level
                for param in num_dict[i]:
                    rule_list.append('IF '+defect+level+'AND '+param+current[param]+' THEN '+ get_value_by_rule(ways_dict[param], level, param))
                    advance += 'AND '+param+get_opposite(current[param])+" "
                advance_list.append(advance)
            else:
                advance = advance_list[i-1]
                for param in num_dict[i]:
                    rule_list.append(advance_list[i-1]+'AND '+param+current[param]+' THEN '+ get_value_by_rule(ways_dict[param], level, param))
                    advance += 'AND '+param+get_opposite(current[param])+" "
                advance_list.append(advance)
    return rule_list


def get_value_by_rule(way, level, name):
    value = 1 if level == "_low " else 1.5 if level == "_mid " else 1.9
    # 不同类型的参数，默认初始值不同，暂时全部默认为2
    # 1. 注射时间、保压时间，默认为0.5
    # 2. 背压默认为1
    # 3. 其余均默认为2
    rule = way[:way.rfind("_")+1]
    if name == "IT" or name.startswith("PT"):
        return rule+str(0.5*value)
    if "MBP" in name:
        return rule+str(1*value)
    else:
        return rule+str(2*value)


def get_opposite(current):
    if current == "_low":
        return "_high"
    if current == "_high":
        return "_low"
    if current == "_worse":
        return "_proper"
    return current


# 如果新增了缺陷,默认顺位为[]
defect_predence_dict = {
    # # 短射顺位：1、储料行程（MEL）；2、注射压力和注射速度；3、其他
    'SHORTSHOT': [['MEL'], ['IP0', 'IV0']],

    # 缩水顺位：1、保压压力和保压时间；2、其他
    'SHRINKAGE': [['PP0', 'PV0']],

    # 飞边顺位：1、如果有保压，优先调保压压力和时间；如果无保压，优先降低注射压力和速度。2、调储料行程。3、其他
    'FLASH': [['PP0', 'PT0', 'IV0', 'IP0'], ['VPTL']],

    # 料花、气纹、熔接痕顺位：1、注射速度；2、其他
    'GASVEINS': [['IV0']],
    'WELDLINE': [['IV0']],
    'MATERIALFLOWER': [['IV0']],

    # 其余缺陷：无明显顺位
    'ABERRATION': [],
    'AIRTRAP': [],
    'BURN': [],
    'WATERRIPPLE': [],
    'HARDDEMOLDING': [],
    'TOPWHITE': [],
    'WARPING': [],
    'OVERSIZE': [],
    'UNDERSIZE': [],
    "GATEMARK": [],
    "SHADING": [],
}


# 获取缺陷对应的顺序列表，如果不存在则返回 []
def get_defect_order(defect):
    return defect_predence_dict.get(defect, [])


if __name__ == '__main__':
    # 假如缺陷是短射（SHORTSHOT）
    my_defect = 'SHORTSHOT'

    # 假如建立子规则库时，通过节点所选择的方案如下，已经取好了调整幅度
    my_ways_list = [
        'MEL_add_2', 
        'IV0_add_1', 
        'IP0_add_1.5', 
        'NT_reduce_1', 
        'BT_reduce_1'
        ]

    # 得到有关该缺陷的规则（仅包含轻微，中等和严重需要进行复制）
    rule_list = rule_predence_test(my_defect, my_ways_list)