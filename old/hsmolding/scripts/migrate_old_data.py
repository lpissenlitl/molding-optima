import pymongo


# 定义缺陷类型映射
defect_mapping = {
    "short_shot": {"label": "短射", "desc": "SHORTSHOT", "defect_num":0},
    "shrinkage": {"label": "缩水", "desc": "SHRINKAGE", "defect_num":1},
    "flash": {"label": "飞边", "desc": "FLASH", "defect_num":2},
    "gas_veins": {"label": "气纹", "desc": "GASVEINS", "defect_num":3},
    "weld_line": {"label": "熔接痕", "desc": "WELDLINE", "defect_num":4},
    "material_flower": {"label": "料花", "desc": "MATERIALFLOWER", "defect_num":5},
    "air_trap": {"label": "困气", "desc": "AIRTRAP", "defect_num":6},
    "aberration": {"label": "色差", "desc": "ABERRATION", "defect_num":7},
    "burn": {"label": "烧焦", "desc": "BURN", "defect_num":8},
    "water_ripple": {"label": "水波纹", "desc": "WATERRIPPLE", "defect_num":9},
    "hard_demolding": {"label": "脱模不良", "desc": "HARDDEMOLDING", "defect_num":10},
    "top_white": {"label": "顶白", "desc": "TOPWHITE", "defect_num":11},
    "warping": {"label": "变形", "desc": "WARPING", "defect_num":12},
    "oversize": {"label": "尺寸偏大", "desc": "OVERSIZE", "defect_num":13},
    "undersize": {"label": "尺寸偏小", "desc": "UNDERSIZE", "defect_num":14},
    "gatemark": {"label": "浇口印", "desc": "GATEMARK", "defect_num":15},
    "shading": {"label": "阴阳面", "desc": "SHADING", "defect_num":16}
}

# 定义数据转换函数
def transform_defect_info(defect_info):
    new_defect_info = []
    for defect_type, defect_data in defect_info.items():
        if defect_type in defect_mapping:
            new_defect = defect_mapping[defect_type].copy()
            new_defect.update(defect_data)
            new_defect_info.append(new_defect)
    return new_defect_info


def transform_optimize_export(optimize_export, defect_info):
    if "defect_name" in optimize_export:
        defect_name = optimize_export["defect_name"]
        if defect_name in defect_mapping:
            if defect_name in defect_info:
                optimize_export["defect_feedback"] = defect_info[defect_name]["feedback"] if defect_info[defect_name]["feedback"] else None
            optimize_export["defect_name"] = defect_mapping[defect_name]["desc"] if defect_mapping[defect_name]["desc"] else None
            optimize_export["defect_num"] = defect_mapping[defect_name]["defect_num"] if defect_mapping[defect_name]["defect_num"] else None
    return optimize_export


# 定义数据转换函数
def transform_document(doc):
    if "optimize_list" in doc:
        for optimize in doc["optimize_list"]:
            optimize["feedback_detail"] = transform_feedback(optimize["feedback_detail"])
    return doc

def transform_feedback(doc):
    if "feedback_detail" in doc:
        feedback_detail = doc["feedback_detail"]
        
        if "optimize_export" in feedback_detail:
            doc["feedback_detail"]["optimize_export"] = transform_optimize_export(feedback_detail["optimize_export"], feedback_detail["defect_info"])
        if "defect_info" in feedback_detail:
            doc["feedback_detail"]["defect_info"] = transform_defect_info(feedback_detail["defect_info"])
        
    return doc


from hsmolding.services import export_report_service


def run():
    export_report_service.export_optimize()
