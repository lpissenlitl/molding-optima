from mdprocess.models import RuleKeyword
KeyWord = {
"low":"轻微",
"mid":"中等",
"high":"严重",
"level1": "等级一",
"level2": "等级二",
"level3": "等级三",
"level4": "等级四",
"level5": "等级五",
"level6": "等级六",
"level7": "等级七",
"level8": "等级八",
"level9": "等级九",

"add":"增加",
"reduce":"减小",
"adjust":"调整",
}
def get_keyword_dict():
    query = RuleKeyword.objects.filter(rule_type="基础库").values("name", "comment").distinct()
    final_result = {}
    for item in query:
        name = item["name"]
        comment = item["comment"]

        final_result[name] = comment

    # 返回最终结果字典
    return final_result
    
new_keywords = get_keyword_dict()  # 假设get_keyword_dict()是从后端获取关键字字典的方法

# 更新KeyWord字典
KeyWord.update(new_keywords)

optimizeKeyWord = {
    "low": "少量",
    "mid": "中等",
    "high": "大量",
    "level1": "等级一",
    "level2": "等级二",
    "level3": "等级三",
    "level4": "等级四",
    "level5": "等级五",
    "level6": "等级六",
    "level7": "等级七",
    "level8": "等级八",
    "level9": "等级九",
}

LocationKeyWord = {
    "low": "激活程度低",
    "mid": "激活程度中等",
    "high": "激活程度高",
    "level1": "等级一",
    "level2": "等级二",
    "level3": "等级三",
    "level4": "等级四",
    "level5": "等级五",
    "level6": "等级六",
    "level7": "等级七",
    "level8": "等级八",
    "level9": "等级九",
}

Paramkeyword = {
    "low": "偏小",
    "mid": "中等大小",
    "high": "偏大",

    "level1": "等级一",
    "level2": "等级二",
    "level3": "等级三",
    "level4": "等级四",
    "level5": "等级五",
    "level6": "等级六",
    "level7": "等级七",
    "level8": "等级八",
    "level9": "等级九",

    "worse":"不合理",
    "proper":"合理",
}

DEFECT_LEVEL = {
    "无缺陷": 0,
    "轻微": 0.2,
    "中等": 0.5,
    "严重": 0.8,
    "非常严重": 0.9,
}

DEFECT_POSITION = {
    "缺陷位置不指定": 0,
    "缺陷位置在1段": 1,
    "缺陷位置在2段": 2,
    "缺陷位置在3段": 3,
    "缺陷位置在4段": 4,
    "缺陷位置在5段": 5,
    "缺陷位置在6段": 6,
    "在第1、2个阀口间": 7,
    "在第2、3个阀口间": 8,
    "在第3、4个阀口间": 9,
    "在第4、5个阀口间": 10,
    "在第5、6个阀口间": 11,
    "在第6、7个阀口间": 12,
    "在第7、8个阀口间": 13,
    "在第8、9个阀口间": 14,
}

DEFECT_FEEDBACK = {
    "上一模修正效果佳": 0,
    "上一模修正效果不佳": 1
}

# 缺陷对应规则中的关键字:弃用,去掉了小写
# DEFECT_KEYWORD = {
    # "short_shot": "SHORTSHOT",
    # "flash": "FLASH",
    # "shrinkage": "SHRINKAGE",
    # "weld_line": "WELDLINE",
    # "aberration": "ABERRATION",
    # "air_trap": "AIRTRAP",
    # "gas_veins": "GASVEINS",
    # "material_flower": "MATERIALFLOWER",
    # "burn": "BURN",
    # "water_ripple": "WATERRIPPLE",
    # "hard_demolding": "HARDDEMOLDING",
    # "top_white":"TOPWHITE",
    # "warping":"WARPING",
    # "oversize":"OVERSIZE",
    # "undersize":"UNDERSIZE",
    # "gatemark": "GATEMARK",
    # "shading": "SHADING",
# }

# DEFECTS_LIST = [
    # "short_shot", 
    # "flash", 
    # "shrinkage", 
    # "weld_line", 
    # "aberration", 
    # "air_trap", 
    # "gas_veins", 
    # "material_flower", 
    # "burn",
    # "water_ripple",
    # "hard_demolding",
    # "top_white", 
    # "warping", 
    # "oversize", 
    # "undersize",
    # "gatemark",
    # "shading",
# ]

# 需要从数据库获取最新的缺陷列表
def get_defect_list():
    query = RuleKeyword.objects.filter(keyword_type="缺陷", rule_type="基础库").values("name", "comment").distinct()
    defect_list: list = [{ "label": item.get("comment"), "desc": item.get("name") } for item in query ]
    return defect_list
defect_list = get_defect_list()
DEFECT_CONST = [item['desc'] for item in defect_list]
# [ 
    # "SHORTSHOT", 
    # "FLASH", 
    # "SHRINKAGE", 
    # "WELDLINE", 
    # "ABERRATION", 
    # "AIRTRAP", 
    # "GASVEINS", 
    # "MATERIALFLOWER",
    # "HARDDEMOLDING",
    # "BURN",
    # "WATERRIPPLE",
    # "TOPWHITE",
    # "WARPING",
    # "OVERSIZE",
    # "UNDERSIZE",
    # "GATEMARK",
    # "SHADING",
# ]
# 需要从数据库获取最新的缺陷列表
DEFECTS_NAME_LIST = [item['label'] for item in defect_list]
# [
    # "短射", 
    # "飞边", 
    # "缩水", 
    # "气纹",
    # "熔接痕",
    # "料花",
    # "困气",
    # "色差",
    # "烧焦",
    # "水波纹",
    # "脱模不良",
    # "顶白",
    # "变形",
    # "尺寸偏大",
    # "尺寸偏小",
    # "浇口印",
    # "阴阳面"
# ]

# 多级注射时，产品的主打段
MAIN_STAGE = {
    1: 1,
    2: 2,
    3: 2,
    4: 3,
    5: 3,
    6: 4
}

# 读取MES对应的开合模顶针
PROCESS = {
    "keba1175":{
        "mold_opening_stage":"19",
        "mold_opening_pressure":["20", "23", "26", "29", "32"],
        "mold_opening_velocity":["21", "24", "27", "30", "33"],
        "mold_opening_position":["22", "25", "28", "31", "34"],
        "mold_clamping_stage":"0",
        "mold_clamping_pressure":["1", "4", "7", "10", "13"],
        "mold_clamping_velocity":["2", "5", "8", "11", "14"],
        "mold_clamping_position":["3", "6", "9", "12", "15"],
        "ejector_forward_stage":"46",
        "ejector_forward_pressure":["49", "52", "55"],
        "ejector_forward_velocity":["50", "53", "56"],
        "ejector_forward_position":["51", "54", "57"],
        "ejector_backward_stage":"58",
        "ejector_backward_pressure":["59", "62", "65"],
        "ejector_backward_velocity":["60", "63", "66"],
        "ejector_backward_position":["61", "64", "67"],   
    },
    "keba映翰通":{
        "mold_opening_stage":"21",
        # "mold_opening_pressure":[],
        "mold_opening_velocity":["22", "24", "26", "28", "30", "32"],
        "mold_opening_position":["23", "25", "27", "29", "31", "33"],
        "mold_clamping_stage":"8",
        # "mold_clamping_pressure":[],
        "mold_clamping_velocity":["9","11", "13", "15", "17"],
        "mold_clamping_position":["10","12", "14", "16", "18"],
        "ejector_forward_stage":"43",
        "ejector_forward_pressure":["44", "47", "50"],
        "ejector_forward_velocity":["45", "48", "51"],
        "ejector_forward_position":["46", "49", "52"],
        "ejector_backward_stage":"55",
        "ejector_backward_pressure":["56", "59", "62"],
        "ejector_backward_velocity":["57", "60", "63"],
        "ejector_backward_position":["58", "61", "64"],
        "mold_protect_velocity":"19",
        "mold_protect_position":"20"
    },
    "盟立":{
        # "mold_opening_stage":"19",
        "mold_opening_pressure":["408", "411", "414", "417", "420"],
        "mold_opening_velocity":["409", "412", "415", "418", "421"],
        "mold_opening_position":["407", "410", "413", "416", "419"],
        # "mold_clamping_stage":"0",
        "mold_clamping_pressure":["388", "391", "394", "401", "398"],  # 最后两段是低压段和高压段
        "mold_clamping_velocity":["389", "392", "395", "402", "399"],  # 最后两段是低压段和高压段
        "mold_clamping_position":["387", "390", "393", "400", "397"],  # 最后两段是低压段和高压段
        "ejector_forward_stage":"244",
        "ejector_forward_pressure":["218", "221", "224"],
        "ejector_forward_velocity":["219", "222", "225"],
        "ejector_forward_position":["217", "220", "223"],
        "ejector_backward_stage":"235",
        "ejector_backward_pressure":["227", "230", "233"],
        "ejector_backward_velocity":["228", "231", "234"],
        "ejector_backward_position":["226", "229", "232"],   
    },
}
