from gis.common.exceptions import BizException

from hsmolding.models import Machine, MachineInjector, Polymer
from hsmolding.exceptions import ERROR_PARAM_ERROR, ERROR_DATA_NOT_EXIST, ERROR_MACHINE, ERROR_POLYMER, ERROR_PRODUCT
from hsmolding.services import machine_service, polymer_service, project_service

from mdprocess.models import ProcessIndex
from mdprocess.dao.process_optimization_model import ProcessOptimizationDoc
from mdprocess.services import process_index_service, rule_service
from mdprocess.utils.process_initialization.process_generate import ProcessInitializer
from mdprocess.utils.fuzzykit.fuzzy_core.models import nets
from mdprocess.const import DEFECT_LEVEL, DEFECT_POSITION, DEFECT_FEEDBACK, MAIN_STAGE

import logging
from decimal import Decimal
import copy

optimize_target_defect = None

RUNNER_TYPE_FORWARD_MAP = {
    0: "热流道",
    1: "冷流道",
    2: "热转冷"
}

RUNNER_TYPE_BACKWARD_MAP = {v: k for k, v in RUNNER_TYPE_FORWARD_MAP.items()}

COOL_RUNNER_GATE_TYPE_FORWARD_MAP = {
    0: "直浇口",
    1: "侧浇口",
    2: "点浇口",
    3: "搭接式浇口",
    4: "护耳浇口",
    5: "薄片浇口",
    6: "扇形浇口",
    7: "环形浇口",
    8: "盘形浇口",
    9: "伞形浇口",
    10: "潜伏式浇口",
    11: "弧形浇口"
}

COOL_RUNNER_GATE_TYPE_BACKWARD_MAP = {v: k for k, v in COOL_RUNNER_GATE_TYPE_FORWARD_MAP.items()}

HOT_RUNNER_GATE_TYPE_FORWARD_MAP = {
    0: "开放式",
    1: "尖点式",
    2: "针阀式"
}

HOT_RUNNER_GATE_TYPE_BACKWARD_MAP = {v: k for k, v in HOT_RUNNER_GATE_TYPE_FORWARD_MAP.items()}

HOT_TO_COLD_TYPE_FORWARD_MAP = {
    0: "开放式+直浇口",
    1: "开放式+侧浇口",
    2: "开放式+点浇口",
    3: "开放式+搭接式浇口",
    4: "开放式+护耳浇口",
    5: "开放式+薄片浇口",
    6: "开放式+扇形浇口",
    7: "开放式+环形浇口",
    8: "开放式+盘形浇口",
    9: "开放式+伞形浇口",
    10: "开放式+潜伏式浇口",
    11: "开放式+弧形浇口",
    12: "尖点式+直浇口",
    13: "尖点式+侧浇口",
    14: "尖点式+点浇口",
    15: "尖点式+搭接式浇口",
    16: "尖点式+护耳浇口",
    17: "尖点式+薄片浇口",
    18: "尖点式+扇形浇口",
    19: "尖点式+环形浇口",
    20: "尖点式+盘形浇口",
    21: "尖点式+伞形浇口",
    22: "尖点式+潜伏式浇口",
    23: "尖点式+弧形浇口",
    24: "针阀式+直浇口",
    25: "针阀式+侧浇口",
    26: "针阀式+点浇口",
    27: "针阀式+搭接式浇口",
    28: "针阀式+护耳浇口",
    29: "针阀式+薄片浇口",
    30: "针阀式+扇形浇口",
    31: "针阀式+环形浇口",
    32: "针阀式+盘形浇口",
    33: "针阀式+伞形浇口",
    34: "针阀式+潜伏式浇口",
    35: "针阀式+弧形浇口"
}

HOT_TO_COLD_TYPE_BACKWARD_MAP = {v: k for k, v in HOT_TO_COLD_TYPE_FORWARD_MAP.items()}

GATE_SHAPE_FORWARD_MAP = {
    0: "圆形",
    1: "矩形",
}

GATE_SHAPE_BACKWARD_MAP = {v: k for k, v in GATE_SHAPE_FORWARD_MAP.items()}

VP_MODE_FORWARD_MAP = {
    0: "无保压",
    1: "位置",
    2: "时间",
    3: "时间&位置",
    4: "压力",
    5: "速度"
}

VP_MODE_BACKWARD_MAP = {
    "无保压": 0,
    "位置": 1,
    "时间": 2,
    "时间&位置": 3,
    "压力": 4,
    "速度": 5
}

DECOM_MODE_FORWARD_MAP = {
    0: "否",
    1: "距离",
    2: "时间"
}

DECOM_MODE_BACKWARD_MAP = {
    "否": 0,
    "距离": 1,
    "时间": 2
}

DEFECT_LEVEL_FORWARD_MAP = {
    0: "无缺陷", 
    1: "轻微", 
    2: "中等", 
    3: "严重",
    4: "非常严重"
}

DEFECT_LEVEL_BACKWARD_MAP = {
    v: k for k, v in DEFECT_LEVEL_FORWARD_MAP.items()
}

DEFECT_POSITION_FORWARD_MAP = {
    0: "缺陷位置不指定",
    1: "缺陷位置在1段",
    2: "缺陷位置在2段",
    3: "缺陷位置在3段",
    4: "缺陷位置在4段",
    5: "缺陷位置在5段",
    6: "缺陷位置在6段"
}

DEFECT_POSITION_BACKWARD_MAP = {
    v: k for k, v in DEFECT_POSITION_FORWARD_MAP.items()
}

DEFECT_FEEDBACK_FORWARD_MAP = {
    0: "上一模修正效果不佳",
    1: "上一模修正效果佳"
}

DEFECT_FEEDBACK_BACKWARD_MAP = {
    v: k for k, v in DEFECT_FEEDBACK_FORWARD_MAP.items()
}


############################# 项目服务 ###############################
def forward_inovance_mold(params: dict):
    for product_info in params["mold_info"]["product_infos"]:
        product_info["runner_type"] = RUNNER_TYPE_FORWARD_MAP.get(product_info["runner_type"], None)
        if product_info["runner_type"] == "热流道":
            product_info["gate_type"] = HOT_RUNNER_GATE_TYPE_FORWARD_MAP.get(product_info["gate_type"], None)
        elif product_info["runner_type"] == "冷流道":
            product_info["gate_type"] = COOL_RUNNER_GATE_TYPE_FORWARD_MAP.get(product_info["gate_type"], None)
        elif product_info["runner_type"] == "热转冷":
            product_info["gate_type"] = HOT_TO_COLD_TYPE_FORWARD_MAP.get(product_info["gate_type"], None)
        product_info["gate_shape"] = GATE_SHAPE_FORWARD_MAP.get(product_info["gate_shape"], None)
    return params


def backward_inovance_mold(params: dict):
    for product_info in params["mold_info"]["product_infos"]:
        product_info["runner_type"] = RUNNER_TYPE_BACKWARD_MAP.get(product_info["runner_type"], None)
        if product_info["runner_type"] == 0:
            product_info["gate_type"] = HOT_RUNNER_GATE_TYPE_BACKWARD_MAP.get(product_info["gate_type"], None)
        elif product_info["runner_type"] == 1:
            product_info["gate_type"] = COOL_RUNNER_GATE_TYPE_BACKWARD_MAP.get(product_info["gate_type"], None)
        elif product_info["runner_type"] == 2:
            product_info["gate_type"] = HOT_TO_COLD_TYPE_BACKWARD_MAP.get(product_info["gate_type"], None)
        product_info["gate_shape"] = GATE_SHAPE_BACKWARD_MAP.get(product_info["gate_shape"], None)
    return params


def add_project(params: dict):
    # 同步数据
    return project_service.add_project(forward_inovance_mold(params))


def get_project(project_id):
    return backward_inovance_mold(project_service.get_project(project_id))


def update_project(project_id, params: dict):
    return project_service.update_project(project_id, forward_inovance_mold(params))


def delete_project(project_id):
    return project_service.delete_project(project_id)


############################### 材料服务 #############################
def add_polymer(params: dict):
    return polymer_service.add_polymer(params)


def get_polymer(polymer_id):
    return polymer_service.get_polymer(polymer_id)


def update_polymer(polymer_id, params: dict):
    return polymer_service.update_polymer(polymer_id, params)


def delete_polymer(polymer_id):
    return polymer_service.delete_polymer(polymer_id)


############################## 工艺优化服务 ###############################
# 获取工艺优化记录
def get_process_optimization(process_index_id):
    optimization = ProcessOptimizationDoc.objects.filter(process_index_id=process_index_id).first()
    if optimization:
        return optimization.to_dict() if optimization else None
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, "该工艺优化记录不存在")


def add_process_optimization(params: dict):
    optimization = ProcessOptimizationDoc.objects.filter(process_index_id=params.get("process_index_id")).first()
    if not optimization:
        optimization = ProcessOptimizationDoc(**params)
        optimization.save()
    else:
        update_process_optimization(params)
    return optimization.to_dict() if optimization else None


# 更新工艺优化记录
def update_process_optimization(params: dict):
    process_index_id = params.get("process_index_id")
    if process_index_id:
        optimization = ProcessOptimizationDoc.objects.filter(process_index_id=process_index_id).first()
        if optimization:
            optimization.update(**params)
            return optimization
        else:
            raise BizException(ERROR_DATA_NOT_EXIST, "该工艺优化记录不存在")
    else:
        return None


# 提取注塑机信息
def extract_machine(machine_id: int):
    if not machine_id:
        raise BizException(ERROR_MACHINE, message="无效机器id,请在机器管理中录入相应注塑机信息")
    machine = Machine.objects.filter(id=machine_id).first()
    injector = MachineInjector.objects.filter(machine_id=machine_id).first()  # 目前只考虑射台1
    common_params = {
        "power_method": machine.power_method,
        "nozzle_type": injector.nozzle_type,
        "screw_diameter": injector.screw_diameter,
        "max_injection_stroke": injector.max_injection_stroke,
        
        "max_injection_pressure": injector.max_injection_pressure,
        "max_injection_velocity": injector.max_injection_velocity,
        "max_holding_pressure": injector.max_holding_pressure,
        "max_holding_velocity": injector.max_holding_velocity,
        "max_metering_back_pressure": injector.max_metering_back_pressure,
        "max_screw_rotation_speed": injector.max_screw_rotation_speed,
        "max_decompression_velocity": injector.max_decompression_velocity,
    
        "max_set_injection_pressure": injector.max_set_injection_pressure,
        "max_set_injection_velocity": injector.max_set_injection_velocity,
        "max_set_holding_pressure": injector.max_set_holding_pressure,
        "max_set_holding_velocity": injector.max_set_holding_velocity,
        "max_set_metering_back_pressure": injector.max_set_metering_back_pressure,
        "max_set_screw_rotation_speed": injector.max_set_screw_rotation_speed,
        "max_set_decompression_velocity": injector.max_set_decompression_velocity
    }
    if machine.power_method == '液压机':
        machine_info = {
            **common_params,

            "max_metering_pressure": injector.max_metering_pressure,
            "max_decompression_pressure": injector.max_decompression_pressure,

            "max_set_metering_pressure": injector.max_set_metering_pressure,
            "max_set_decompression_pressure": injector.max_set_decompression_pressure,
        }
    elif machine.power_method == '电动机':
        machine_info = {
            **common_params
        }
    else:
        raise BizException(ERROR_MACHINE, message='无法识别注塑机驱动类型，请补充相关信息')
    # 浮点数转换
    for key, value in machine_info.items():
        if isinstance(value, Decimal):
            machine_info[key] = float(value)
    return machine_info


# 提取胶料信息
def extract_polymer(polymer_id: int):
    if not polymer_id:
        raise BizException(ERROR_POLYMER, message="无效材料id")
    polymer = Polymer.objects.filter(pk=int(polymer_id)).first()
    polymer_info = {
        "abbreviation": polymer.abbreviation,
        "category": polymer.category,  # 结晶型、无定形
        "recommend_melt_temperature": polymer.recommend_melt_temperature,
        "recommend_shear_linear_speed": polymer.recommend_shear_linear_speed,
        "recommend_back_pressure": polymer.recommend_back_pressure,
        "recommend_mold_temperature": polymer.recommend_mold_temperature,
        "ejection_temperature": polymer.ejection_temperature,
        "melt_density": polymer.melt_density
    }
    # 浮点数转换
    for key, value in polymer_info.items():
        if isinstance(polymer_info.get(key), Decimal):
            polymer_info[key] = float(value)
    return polymer_info


# 提取制品信息
def extract_product(params: dict):
    print("传入的制品参数：", params)
    init_info = {
        "runner_weight": params.get("runner_weight"),
        "gate_type": params.get("gate_type"),
        "gate_shape": params.get("gate_shape"),
        "gate_radius": params.get("gate_radius"),
        "gate_length": params.get("gate_length"),
        "gate_width": params.get("gate_width"),
        "product_type": params.get("product_type"),
        "max_thickness": params.get("product_max_thickness"),
        "ave_thickness": params.get("product_ave_thickness"),
        "max_length": params.get("product_max_length"),
        "injection_stage": params.get("injection_stage"),
        "holding_stage": params.get("holding_stage"),
        "metering_stage": params.get("metering_stage"),
        "barrel_temperature_stage": params.get("barrel_temperature_stage"),
        "VP_switch_mode": params.get("VP_switch_mode"),
        "decompressure_mode_before_metering": params.get("decompressure_mode_before_metering"),
        "decompressure_mode_after_metering": params.get("decompressure_mode_after_metering"),
        "valve_num": params.get("valve_num"),
        "inject_cycle_require": params.get("inject_cycle_require"),
    }
    
    if init_info.get("runner_weight"):
        init_info["product_weight"] = float(init_info.get("runner_weight")) + float(params.get("product_total_weight"))
    else:
        init_info["product_weight"] = float(params.get("product_total_weight"))
    init_info["product_weight"] = round(init_info.get("product_weight"), 2)
    
    # 浮点数转换
    for key, value in init_info.items():
        if isinstance(init_info.get(key), Decimal):
            init_info[key] = float(value)
    return init_info


# 校验参数,使其不超过机器设定范围
def param_check(ret):
    machine_id = ret["machine_id"]
    machine_info = extract_machine(machine_id)

    if ret["MEL"] > float(machine_info.get("max_injection_stroke")):
        ret["MEL"] = float(machine_info.get("max_injection_stroke"))

    for i in range(0, ret['injection_stage']):
        if ret.get('IP' + str(i)) > machine_info.get("max_set_injection_pressure"):
            ret['IP' + str(i)] = machine_info.get("max_set_injection_pressure")
        if ret['IV' + str(i)] > machine_info.get("max_set_injection_velocity"):
            ret['IV' + str(i)] = machine_info.get("max_set_injection_velocity")

    # 位置需要限制：储料位置>4段位置>3段位置>2段位置>1段位置>切换位置
    inj_stage = ret.get('injection_stage')

    if ret.get('VPTL') != ret.get('IL' + str(inj_stage - 1)):
        ret['VPTL'] = ret.get('IL' + str(inj_stage - 1))
    for key in ret:
        if key[:2] in ['IV', 'IL', 'NT', 'BT'] and ret.get(key) <= 0:
            ret[key] = 1


#  读取注塑机实际可设定范围
def read_machine_setting_para(machine_info: dict, params):
    if machine_info:
        for item in params:
            if item["keyword"] in ["IP0", "IP1", "IP2", "IP3", "IP4", "IP5"]:
                if not machine_info.get("max_set_injection_pressure"):
                    raise BizException(ERROR_MACHINE, message="最大注射压力为空!")
                else:
                    item["max_val"] = float(machine_info.get("max_set_injection_pressure"))
            elif item["keyword"] in ["IV0", "IV1", "IV2", "IV3", "IV4", "IV5"]:
                if not machine_info.get("max_set_injection_velocity"):
                    raise BizException(ERROR_MACHINE, message="最大注射速度为空!")
                else:
                    item["max_val"] = float(machine_info.get("max_set_injection_velocity"))
            elif item["keyword"] in ["IL0", "IL1", "IL2", "IL3", "IL4", "IL5"]:
                if not machine_info.get("max_injection_stroke"):
                    raise BizException(ERROR_MACHINE, message="最大注射行程为空!")
                else:     
                    item["max_val"] = float(machine_info.get("max_injection_stroke"))
            elif item["keyword"] in ["PP0", "PP1", "PP2", "PP3", "PP4"]:
                if not machine_info.get("max_set_holding_pressure"):
                    raise BizException(ERROR_MACHINE, message="最大保压压力为空!")
                else: 
                    item["max_val"] = float(machine_info.get("max_set_holding_pressure"))
            elif item["keyword"] in ["PV0", "PV1", "PV2", "PV3", "PV4"]:
                if not machine_info.get("max_set_holding_velocity"):
                    raise BizException(ERROR_MACHINE, message="最大保压速度为空!")
                else: 
                    item["max_val"] = float(machine_info.get("max_set_holding_velocity"))
            elif item["keyword"] in ["MP0", "MP1", "MP2", "MP3"]:
                # 全电机没有计量压力,给一个固定值150
                if not machine_info.get("max_set_metering_pressure"):
                    item["max_val"] = 150
                else: 
                    item["max_val"] = float(machine_info.get("max_set_metering_pressure"))
            elif item["keyword"] in ["MBP0", "MBP1", "MBP2", "MBP3"]:
                if not machine_info.get("max_set_metering_back_pressure"):
                    raise BizException(ERROR_MACHINE, message="最大计量背压为空!")
                else: 
                    item["max_val"] = float(machine_info.get("max_set_metering_back_pressure"))
            elif item["keyword"] in ["MSR0", "MSR1", "MSR2", "MSR3"]:
                if not machine_info.get("max_set_screw_rotation_speed"):
                    raise BizException(ERROR_MACHINE, message="最大螺杆转速为空!")
                else: 
                    item["max_val"] = float(machine_info.get("max_set_screw_rotation_speed"))
            elif item["keyword"] in ["ML0", "ML1", "ML2", "ML3", "VPTL", "MEL"]:
                if not machine_info.get("max_injection_stroke"):
                    raise BizException(ERROR_MACHINE, message="最大注射行程为空!")
                else: 
                    item["max_val"] = float(machine_info.get("max_injection_stroke"))


# 从mongo数据库中取修正过程数据
def update_value_dict(process, output_dict):
    # 注射参数
    injection_dict = process.get('inject_para')
    output_dict['injection_stage'] = injection_dict.get('injection_stage')
    for index in range(0, output_dict['injection_stage']):
        output_dict['IP' + str(index)] = injection_dict["table_data"][0]["sections"][index]
        output_dict['IV' + str(index)] = injection_dict["table_data"][1]["sections"][index]
        output_dict['IL' + str(index)] = injection_dict["table_data"][2]["sections"][index]
    output_dict["IT"] = injection_dict["injection_time"]
    output_dict["ID"] = injection_dict["injection_delay_time"]
    output_dict["CT"] = injection_dict["cooling_time"]

    # 保压参数
    holding_dict = process.get('holding_para')
    output_dict['holding_stage'] = holding_dict.get('holding_stage')
    # defect_info是list,第2个是缩水
    if len(output_dict["defect_info"])>=2 and output_dict["defect_info"][1]["label"] == "缩水" and output_dict["defect_info"][1]["count"] == 0 and output_dict["defect_info"][1]["level"] != 0:
        pass
    else:
        for index in range(0, output_dict['holding_stage']):
            output_dict['PP' + str(index)] = holding_dict["table_data"][0]["sections"][index]
            output_dict['PV' + str(index)] = holding_dict["table_data"][1]["sections"][index]
            output_dict['PT' + str(index)] = holding_dict["table_data"][2]["sections"][index]

    # VP切换
    VP_switch_dict = process.get('VP_switch')
    output_dict['VPTM'] = VP_switch_dict.get('VP_switch_mode')
    output_dict['VPTT'] = VP_switch_dict.get('VP_switch_time')
    output_dict['VPTL'] = VP_switch_dict.get('VP_switch_position')
    output_dict['VPTP'] = VP_switch_dict.get('VP_switch_pressure')
    output_dict['VPTV'] = VP_switch_dict.get('VP_switch_velocity')

    # 计量参数
    metering_dict = process.get('metering_para')
    output_dict['metering_stage'] = metering_dict.get('metering_stage')
    for index in range(0, output_dict['metering_stage']):
        output_dict['MP' + str(index)] = metering_dict["table_data"][0]["sections"][index]
        output_dict['MSR' + str(index)] = metering_dict["table_data"][1]["sections"][index]
        output_dict['MBP' + str(index)] = metering_dict["table_data"][2]["sections"][index]
        output_dict['ML' + str(index)] = metering_dict["table_data"][3]["sections"][index]

    output_dict['DMBM'] = metering_dict.get('decompressure_mode_before_metering')
    output_dict['DMAM'] = metering_dict.get('decompressure_mode_after_metering')

    decom_dict = metering_dict['decompressure_paras']
    output_dict['DPBM'] = decom_dict[0].get('pressure')
    output_dict['DVBM'] = decom_dict[0].get('velocity')
    output_dict['DDBM'] = decom_dict[0].get('distance')
    output_dict['DTBM'] = decom_dict[0].get('time')
    output_dict['DPAM'] = decom_dict[1].get('pressure')
    output_dict['DVAM'] = decom_dict[1].get('velocity')
    output_dict['DDAM'] = decom_dict[1].get('distance')
    output_dict['DTAM'] = decom_dict[1].get('time')

    output_dict['MD'] = metering_dict.get('metering_delay_time')
    output_dict['MEL'] = metering_dict.get('metering_ending_position')

    # 温度参数
    temp_dict = process.get('temp_para')
    output_dict['barrel_temperature_stage'] = temp_dict.get('barrel_temperature_stage')
    for index in range(0, output_dict['barrel_temperature_stage']):
        if index == 0:
            output_dict['NT'] = temp_dict["table_data"][0]["sections"][index]
        else:
            output_dict['BT' + str(index)] = temp_dict["table_data"][0]["sections"][index]

    # 其他参数
    output_dict['actual_product_weight'] = process.get('actual_product_weight')


def construct_initialize_precondition(params: dict):
    # 获取模具信息
    mold_info = project_service.get_mold_dict_by_id(int(params.get("mold_id")))
    precondition_dict = {
        **params,
        "mold_no": mold_info.get("mold_no"),
        "cavity_num": mold_info.get("cavity_num"),
        "inject_cycle_require": mold_info.get("inject_cycle_require"),
        "subrule_no": mold_info.get("subrule_no"),
        "product_type": mold_info.get("product_small_type"),
        "product_no": mold_info.get("product_no"),
        "product_name": mold_info.get("product_name"),
        "product_total_weight": float(mold_info.get("product_total_weight")) if mold_info.get("product_total_weight") else 0,
    }
    # 获取制品信息
    product_info: dict = mold_info["product_infos"][0]
    if product_info:
        precondition_dict.update({
            "inject_part": "0",
            "product_ave_thickness": float(product_info.get("ave_thickness")) if product_info.get("ave_thickness") else 0,
            "product_max_thickness": float(product_info.get("max_thickness")) if product_info.get("max_thickness") else 0,
            "product_max_length": float(product_info.get("flow_length")) if product_info.get("flow_length") else 0,
            
            "runner_length": float(product_info.get("runner_length")) if product_info.get("runner_length") else 0,
            "runner_weight": float(product_info.get("runner_weight")) if product_info.get("runner_weight") else 0,
            "gate_type": product_info.get("gate_type") if product_info.get("gate_type") else None,
            "gate_num": product_info.get("gate_num") if product_info.get("gate_num") else None,
            "gate_shape": product_info.get("gate_shape") if product_info.get("gate_shape") else None,
            "gate_area": float(product_info.get("gate_area")) if product_info.get("gate_area") else 0,
            "gate_radius": float(product_info.get("gate_radius")) if product_info.get("gate_radius") else 0,
            "gate_length": float(product_info.get("gate_length")) if product_info.get("gate_length") else 0,
            "gate_width": float(product_info.get("gate_width")) if product_info.get("gate_width") else 0,

            "runner_type": product_info.get("runner_type") if product_info.get("runner_type") else None,
            "hot_runner_num": product_info.get("hot_runner_num") if product_info.get("hot_runner_num") else None,
            "valve_num": product_info.get("valve_num") if product_info.get("valve_num") else None,
        })
    
    # 获取注塑机信息
    machine_info = machine_service.get_machine(int(params.get("machine_id")))
    precondition_dict.update({
        "machine_data_source": machine_info.get("data_source"),
        "machine_trademark": machine_info.get("trademark"),
        "machine_serial_no": machine_info.get("serial_no"),
    })
    
    # 获取材料信息
    polymer_info = polymer_service.get_polymer(int(params.get("polymer_id")))
    precondition_dict.update({
        "polymer_abbreviation": polymer_info.get("abbreviation"),
        "polymer_trademark": polymer_info.get("trademark"),
    })
    
    return precondition_dict


def construct_saved_format(data: dict, machine_info: dict = None):
    
    # 更新机器单位
    if machine_info is None:
        machine_info = {
            "pressure_unit": "bar",
            "velocity_unit": "%",
            "screw_rotation_unit": "rpm"
        }

    process_detail = {
        'name': '0', 
        'title': '射台 #1', 
        'temp_para': {
            'table_data': [{'unit': '℃', 'sections': [None, None, None, None, None, None, None, None, None, None], 'label': '温度'}], 
            'barrel_temperature_stage': 5, 
            'max_barrel_temperature_stage_option': 10
        }, 
        'holding_para': {
            'max_holding_stage_option': 5, 
            'holding_stage': 3, 
            'table_data': [
                {'unit': machine_info.get("pressure_unit"), 'sections': [None, None, None, None, None], 'label': '压力'}, 
                {'unit': machine_info.get("velocity_unit"), 'sections': [None, None, None, None, None], 'label': '速度'}, 
                {'unit': 's', 'sections': [None, None, None, None, None], 'label': '时间'}
            ]
        }, 
        'metering_para': {
            'metering_delay_time': None, 
            'metering_ending_position': None, 
            'table_data': [
                {'unit': machine_info.get("pressure_unit"), 'sections': [None, None, None, None], 'label': '压力'}, 
                {'unit': machine_info.get("screw_rotation_unit"), 'sections': [None, None, None, None], 'label': '螺杆转速'}, 
                {'unit': machine_info.get("pressure_unit"), 'sections': [None, None, None, None], 'label': ' 背压'}, 
                {'unit': 'mm', 'sections': [None, None, None, None], 'label': '位置'}
            ], 
            'metering_stage': 1, 
            'decompressure_mode_before_metering': '否', 
            'decompressure_mode_after_metering': '距离',
            'max_metering_stage_option': 4, 
            'decompressure_paras': [
                {'distance': None, 'velocity': None, 'pressure': None, 'label': '储前', 'time': None}, 
                {'distance': None, 'velocity': None, 'pressure': None, 'label': '储后', 'time': None}
            ], 
        }, 
        'inject_para': {
            'table_data': [
                {'unit': machine_info.get("pressure_unit"), 'sections': [None, None, None, None, None, None], 'label': '压力'}, 
                {'unit': machine_info.get("velocity_unit"), 'sections': [None, None, None, None, None, None], 'label': '速度'}, 
                {'unit': 'mm', 'sections': [None, None, None, None, None, None], 'label': '位置'}
            ], 
            'cooling_time': None,
            'injection_delay_time': None, 
            'injection_stage': 4, 
            'max_injection_stage_option': 6, 
            'injection_time': None
        }, 
        'VP_switch': {
            'VP_switch_pressure': None,
            'VP_switch_time': None,
            'VP_switch_mode': '位置', 
            'VP_switch_velocity': None,
            'VP_switch_position': None
        }
    }
    
    # 注射参数
    process_detail["inject_para"]["injection_stage"] = data["injection_stage"]
    for i in range(0, int(data["injection_stage"])):
        process_detail["inject_para"]["table_data"][0]["sections"][i] = round(data["IP" + str(i)], 2)
        process_detail["inject_para"]["table_data"][1]["sections"][i] = round(data["IV" + str(i)], 2)
        process_detail["inject_para"]["table_data"][2]["sections"][i] = round(data["IL" + str(i)], 2)
    process_detail["inject_para"]["injection_time"] = round(data["IT"], 2)
    process_detail["inject_para"]["injection_delay_time"] = round(data["ID"], 2)
    process_detail["inject_para"]["cooling_time"] = round(data["CT"], 2)

    # 保压参数
    process_detail["holding_para"]["holding_stage"] = data["holding_stage"]
    for i in range(0, int(data["holding_stage"])):
        process_detail["holding_para"]["table_data"][0]["sections"][i] = round(data["PP" + str(i)], 2)
        process_detail["holding_para"]["table_data"][1]["sections"][i] = round(data["PV" + str(i)], 2)
        process_detail["holding_para"]["table_data"][2]["sections"][i] = round(data["PT" + str(i)], 2)

    # VP切换
    process_detail["VP_switch"]["VP_switch_mode"] = data["VPTM"]
    process_detail["VP_switch"]["VP_switch_time"] = round(data["VPTT"], 2)
    process_detail["VP_switch"]["VP_switch_velocity"] = round(data["VPTV"], 2)
    process_detail["VP_switch"]["VP_switch_position"] = round(data["VPTL"], 2)
    process_detail["VP_switch"]["VP_switch_pressure"] = round(data["VPTP"], 2)

    # 计量参数
    process_detail["metering_para"]["metering_stage"] = data["metering_stage"]
    for i in range(0, int(data["metering_stage"])):
        process_detail["metering_para"]["table_data"][0]["sections"][i] = round(data["MP" + str(i)], 2)
        process_detail["metering_para"]["table_data"][1]["sections"][i] = round(data["MSR" + str(i)], 2)
        process_detail["metering_para"]["table_data"][2]["sections"][i] = round(data["MBP" + str(i)], 2)
        process_detail["metering_para"]["table_data"][3]["sections"][i] = round(data["ML" + str(i)], 2)

    process_detail["metering_para"]["decompressure_mode_before_metering"] = data["DMBM"]
    process_detail["metering_para"]["decompressure_mode_after_metering"] = data["DMAM"]

    process_detail["metering_para"]["decompressure_paras"][0]["pressure"] = round(data["DPBM"], 2)
    process_detail["metering_para"]["decompressure_paras"][0]["velocity"] = round(data["DVBM"], 2)
    process_detail["metering_para"]["decompressure_paras"][0]["distance"] = round(data["DDBM"], 2)
    process_detail["metering_para"]["decompressure_paras"][0]["time"] = round(data["DTBM"], 2)

    process_detail["metering_para"]["decompressure_paras"][1]["pressure"] = round(data["DPAM"], 2)
    process_detail["metering_para"]["decompressure_paras"][1]["velocity"] = round(data["DVAM"], 2)
    process_detail["metering_para"]["decompressure_paras"][1]["distance"] = round(data["DDAM"], 2)
    process_detail["metering_para"]["decompressure_paras"][1]["time"] = round(data["DTAM"], 2)

    process_detail["metering_para"]["metering_delay_time"] = round(data["MD"], 2)
    process_detail["metering_para"]["metering_ending_position"] = round(data["MEL"], 2)

    # 料筒温度
    process_detail["temp_para"]["barrel_temperature_stage"] = data["barrel_temperature_stage"]
    for i in range(0, int(data["barrel_temperature_stage"])):
        if i == 0:
            process_detail["temp_para"]["table_data"][0]["sections"][i] = round(data["NT"], 2)
        else:
            process_detail["temp_para"]["table_data"][0]["sections"][i] = round(data["BT" + str(i)], 2)

    return process_detail


def construct_saved_optimize_data(params: dict):
    optimize_record = {
        'precondition': {
            'mold_id': params.get("mold_id"), 
            'mold_no': params.get("mold_no"), 
            'cavity_num': params.get("cavity_num"), 
            'inject_cycle_require': params.get("inject_cycle_require"), 
            'subrule_no': params.get("subrule_no"), 
            'runner_length': params.get("runner_length"), 
            'runner_weight': params.get("runner_weight"), 
            'gate_type': params.get("gate_type"), 
            'gate_num': params.get("gate_num"), 
            'gate_shape': params.get("gate_shape"), 
            'gate_area': params.get("gate_area"), 
            'gate_radius': params.get("gate_radius"), 
            'gate_length':  params.get("gate_length"), 
            'gate_width': params.get("gate_width"), 
            'inject_part': params.get("inject_part"), 
            'product_type': params.get("product_type"), 
            'product_total_weight': params.get("product_total_weight"), 
            'product_no': params.get("product_no"),
            'product_name': params.get("product_name"), 
            'product_max_thickness': params.get("product_max_thickness"), 
            'product_ave_thickness': params.get("product_ave_thickness"), 
            'product_max_length': params.get("product_max_length"),  
            'machine_id': params.get("machine_id"), 
            'machine_trademark': params.get("machine_trademark"), 
            'machine_data_source': params.get("machine_data_source"), 
            'machine_serial_no': params.get("machine_serial_no"), 
            'polymer_id': params.get("polymer_id"),  
            'polymer_trademark': params.get("polymer_trademark"), 
            'polymer_abbreviation': params.get("polymer_abbreviation"),
            'recommend_melt_temperature': params.get("recommend_melt_temperature"), 
            'data_sources': params.get("data_sources"), 
            'runner_type': params.get("runner_type"),  
            'hot_runner_num': params.get("hot_runner_num"), 
            'valve_num': params.get("valve_num"),
            'injection_stage': params.get("injection_stage"), 
            'holding_stage': params.get("holding_stage"), 
            'VP_switch_mode': params.get("VP_switch_mode"), 
            'metering_stage': params.get("metering_stage"), 
            'decompressure_mode_before_metering': params.get("decompressure_mode_before_metering"), 
            'decompressure_mode_after_metering': params.get("decompressure_mode_after_metering"), 
            'barrel_temperature_stage': params.get("barrel_temperature_stage"),
        }, 
        'optimize_list': [{
            'name': '0',
            'title': 'init', 
            'feedback_detail': {
                'optimize_export': {
                    'defect_num': None,
                    'defect_feedback': None,
                    'defect_level': None, 
                    'rule_in_use': None, 
                    'defect_position': None, 
                    'defect_name': None, 
                    'adjust_name': None, 
                    'candidate_rules': [], 
                    'rule_valid': None, 
                    'adjust_value': None, 
                    'adjust_direction': None
                }, 
                'defect_info': [
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'SHORTSHOT', 'label': '短射', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'SHRINKAGE', 'label': '缩水', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'FLASH', 'label': '飞边', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'GASVEINS', 'label': '气纹', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'WELDLINE', 'label': '熔接痕', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'MATERIALFLOWER', 'label': '料花', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'AIRTRAP', 'label': '困气', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'ABERRATION', 'label': '色差', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'BURN', 'label': '烧焦', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'WATERRIPPLE', 'label': '水波纹', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'HARDDEMOLDING', 'label': '脱模不良', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'TOPWHITE', 'label': '顶白', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'WARPING', 'label': ' 变形', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'OVERSIZE', 'label': '尺寸偏大', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'UNDERSIZE', 'label': '尺寸偏小', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'GATEMARK', 'label': '浇口印', 'level': '无缺陷', 'count': 0, 'remark': None}, 
                    {'feedback': None, 'position': '缺陷位置不指定', 'desc': 'SHADING', 'label': '阴阳面', 'level': '无缺陷', 'count': 0, 'remark': None}
                ], 
                'actual_product_weight': None
            }, 
            'process_detail': {
                'name': '0', 
                'title': '射台 #1', 
                'temp_para': {
                    'table_data': [{'unit': '℃', 'sections': [220.0, 225.0, 215.0, 205.0, 195.0, None, None, None, None, None], 'label': '温度'}], 
                    'barrel_temperature_stage': 5, 
                    'max_barrel_temperature_stage_option': 10
                }, 
                'holding_para': {
                    'max_holding_stage_option': 5, 
                    'holding_stage': 3, 
                    'table_data': [
                        {'unit': 'bar', 'sections': [0.0, 0.0, 0.0, None, None], 'label': '压力'}, 
                        {'unit': '%', 'sections': [0.0, 0.0, 0.0, None, None], 'label': '速度'}, 
                        {'unit': 's', 'sections': [0.0, 0.0, 0.0, None, None], 'label': '时间'}
                    ]
                }, 
                'metering_para': {
                    'metering_delay_time': 0.5, 
                    'metering_ending_position': 45.78, 
                    'table_data': [
                        {'unit': 'bar', 'sections': [96.0, None, None, None], 'label': '压力'}, 
                        {'unit': 'rpm', 'sections': [60.0, None, None, None], 'label': '螺杆转速'}, 
                        {'unit': 'bar', 'sections': [150.0, None, None, None], 'label': ' 背压'}, 
                        {'unit': 'mm', 'sections': [43.78, None, None, None], 'label': '位置'}
                    ], 
                    'metering_stage': 1, 
                    'decompressure_mode_before_metering': '否', 
                    'max_metering_stage_option': 4, 
                    'decompressure_paras': [
                        {'distance': 0.0, 'velocity': 19.0, 'pressure': 70.0, 'label': '储前', 'time': 0.0}, 
                        {'distance': 2.0, 'velocity': 19.0, 'pressure': 70.0, 'label': '储后', 'time': 0.0}
                    ], 
                    'decompressure_mode_after_metering': '距离'
                }, 
                'inject_para': {
                    'table_data': [
                        {'unit': 'bar', 'sections': [114.0, 114.0, 119.0, 57.0, None, None], 'label': '压力'}, 
                        {'unit': '%', 'sections': [40.0, 14.0, 40.0, 8.0, None, None], 'label': '速度'}, 
                        {'unit': 'mm', 'sections': [41.98, 41.41, 31.93, 30.69, None, None], 'label': '位置'}
                    ], 
                    'cooling_time': 5.0, 
                    'injection_delay_time': 0.2, 
                    'injection_stage': 4, 
                    'max_injection_stage_option': 6, 
                    'injection_time': 3.3
                }, 
                'VP_switch': {
                    'VP_switch_pressure': 0.0, 
                    'VP_switch_time': 0.0, 
                    'VP_switch_mode': '位置', 
                    'VP_switch_velocity': 0.0, 
                    'VP_switch_position': 30.69
                }
            }, 
            'auxiliary_detail': {'mold_temp': {'setting_temp': 70.0}, 'hot_runner_temperatures': [], 'hot_runner': {'sequential_ctrl_time': []}}, 
        }], 
        'process_index_id': None, 
        'flaw_picture_url': None
    }
    return optimize_record


def deduce_process(params: dict):
    # 提取机器参数
    machine_id = params.get("machine_id")
    if not machine_id:
        raise BizException(ERROR_MACHINE, message="无效机器id")
    machine_info = extract_machine(machine_id)
    print("------------1.获取机器参数------------")
    # 提取胶料参数
    polymer_id = params.get("polymer_id")
    if not polymer_id:
        raise BizException(ERROR_POLYMER, message="无效材料id")
    polymer_info = extract_polymer(polymer_id)
    print("------------2.获取材料参数------------")
    # 提取产品信息
    init_info = extract_product(params)
    print("------------3.获取制品参数------------")
    # 初始化工艺参数
    initializer = ProcessInitializer(machine_info=machine_info, polymer_info=polymer_info)
    result = initializer.deduce(init_info=init_info)
    print("------------4.推理初始工艺--------------")
    return result


def construct_formatted_process(result: dict):
    ret = {}
    ret['injection_stage'] = result['injection_param'].injection_stage
    for i in range(0, ret['injection_stage']):
        ret['IP' + str(i)] = result['injection_param'].fInjectPresSteps[i]
        ret['IV' + str(i)] = result['injection_param'].fInjectVelocitySteps[i]
        ret['IL' + str(i)] = result['injection_param'].fInjectPositionSteps[i]
    ret['IT'] = result['injection_param'].fInjectTime
    ret['ID'] = result['injection_param'].fInjectDelay
    ret['CT'] = result['cooling_param'].fCoolTime

    ret['VPTM'] = result['vp_switch_param'].sVPSwitchMode
    ret['VPTT'] = result['vp_switch_param'].fVPTime
    ret['VPTL'] = result['vp_switch_param'].fVPPos
    ret['VPTP'] = result['vp_switch_param'].fVPPres
    ret['VPTV'] = result['vp_switch_param'].fVPVelo

    ret['holding_stage'] = result['holding_param'].holding_stage
    for i in range(0, ret['holding_stage']):
        ret['PP' + str(i)] = result['holding_param'].fPackPresSteps[i]
        ret['PV' + str(i)] = result['holding_param'].fPackVeloSteps[i]
        ret['PT' + str(i)] = result['holding_param'].fPackTimeSteps[i]

    ret['metering_stage'] = result['metering_param'].metering_stage
    for i in range(0, ret['metering_stage']):
        ret['MP' + str(i)] = result['metering_param'].fPressure[i]
        ret['MSR' + str(i)] = result['metering_param'].fVelocity[i]
        ret['MBP' + str(i)] = result['metering_param'].fBackPressure[i]
        ret['ML' + str(i)] = result['metering_param'].fMeteringPos[i]

    ret['DMBM'] = result['decompression_param'].sBeforeSuckMode
    ret['DMAM'] = result['decompression_param'].sAfterSuckMode

    ret['DPBM'] = result['decompression_param'].fBeforeBackPressure
    ret['DVBM'] = result['decompression_param'].fBeforeMeasureVel
    ret['DDBM'] = result['decompression_param'].fBeforeMeasureDis
    ret['DTBM'] = result['decompression_param'].fBeforeTime

    ret['DPAM'] = result['decompression_param'].fAfterBackPressure
    ret['DVAM'] = result['decompression_param'].fAfterMeasureVel
    ret['DDAM'] = result['decompression_param'].fAfterMeasureDis
    ret['DTAM'] = result['decompression_param'].fAfterTime

    ret['MD'] = result['metering_param'].fStartDelay
    ret['MEL'] = result['decompression_param'].fStopPos
    
    ret['barrel_temperature_stage'] = result['temperature_param'].barrel_temperature_stage
    ret['NT'] = result['temperature_param'].nozzle_temp
    for i in range(0, ret['barrel_temperature_stage'] - 1):
        ret['BT' + str(i + 1)] = result['temperature_param'].fTemperature[i]
    
    for i in range(0, len(result['valve_param'].fTime)):
        ret['SCT' + str(i)] = result['valve_param'].fTime[i]
    ret['MT'] = result['mold_param'].mold_temp
    return ret
    

# 工艺参数初始化
def initialize_process(user: dict, params: dict):
    if params.get("VP_switch_mode") < 0 or params.get("VP_switch_mode") > 5:
        raise BizException(ERROR_PARAM_ERROR, message="无效VP切换模式")
    params["VP_switch_mode"] = VP_MODE_FORWARD_MAP.get(params.get("VP_switch_mode"), 1)
    if params.get("decompressure_mode_before_metering") < 0 or params.get("decompressure_mode_before_metering") > 2:
        raise BizException(ERROR_PARAM_ERROR, message="无效储前射退模式")
    params["decompressure_mode_before_metering"] = DECOM_MODE_FORWARD_MAP.get(params.get("decompressure_mode_before_metering"), 0)
    if params.get("decompressure_mode_after_metering") < 0 or params.get("decompressure_mode_after_metering") > 2:
        raise BizException(ERROR_PARAM_ERROR, message="无效储后射退模式")
    params["decompressure_mode_after_metering"] = DECOM_MODE_FORWARD_MAP.get(params.get("decompressure_mode_after_metering"), 1)
    precondition = construct_initialize_precondition(params)
    precondition.update({
        "company_id": user.get("company_id"),
        "status": 1,
        "optimize_type": 0,
    })
    result = deduce_process(precondition)
    # 构建输出结果
    ret = construct_formatted_process(result)
    # 创建工艺索引
    process = process_index_service._add_process_index(precondition)
    ret['process_index_id'] = process.id
    print("------------5.数据构建完成---------------")
    # 保存结果
    if precondition.get("optimize_type", 0) == 0:
        # 判断是否初始加保压
        for i in range(0, ret['holding_stage']):
            ret['PT' + str(i)] = 0
    process_detail = construct_saved_format(ret)
    optimize_template = construct_saved_optimize_data(precondition)
    optimize_template["process_index_id"] = process.id
    optimize_template["optimize_list"][0]["process_detail"] = process_detail
    add_process_optimization(optimize_template)
    ret["opt_nums"] = 0
    ret["VPTM"] = VP_MODE_BACKWARD_MAP.get(ret.get("VPTM"))
    ret["DMBM"] = DECOM_MODE_BACKWARD_MAP.get(ret.get("DMBM"))
    ret["DMAM"] = DECOM_MODE_BACKWARD_MAP.get(ret.get("DMAM"))
    return ret


def optimize_process(req: dict):
    process_index = process_index_service.get_process_index(req.get("process_index_id"))
    product_weight = float(process_index.get("product_total_weight"))
    if process_index.get("runner_weight"):
        product_weight += float(process_index.get("runner_weight"))
    
    # 获取机器信息
    machine_id = process_index.get("machine_id")
    machine = Machine.objects.filter(id=machine_id).first()
    machine_dict = machine.to_dict()
    injection_dict = MachineInjector.objects.filter(machine_id=machine_id).first().to_dict()
    
    params = {
        "process_index_id": req.get("process_index_id"),
        "opt_nums": req.get("opt_nums", 1),
        "machine_id": machine_id,
        "product_weight": product_weight,
        "actual_product_weight": req.get("actual_product_weight"),
        "subrule_no": "R20240702164137",
        "general": True
    }

    # 注射参数
    params["injection_stage"] = req.get("injection_stage")
    for idx in range(0, int(req.get("injection_stage"))):
        params["IP" + str(idx)] = req.get("IP" + str(idx))
        params["IV" + str(idx)] = req.get("IV" + str(idx))
        params["IL" + str(idx)] = req.get("IL" + str(idx))
    params["IT"] = req.get("IT")
    params["ID"] = req.get("ID")
    params["CT"] = req.get("CT")

    # 保压参数
    params["holding_stage"] = req.get("holding_stage")
    for idx in range(0, int(req.get("holding_stage"))):
        params["PP" + str(idx)] = req.get("PP" + str(idx))
        params["PV" + str(idx)] = req.get("PV" + str(idx))
        params["PT" + str(idx)] = req.get("PT" + str(idx))

    # vp切换
    if req.get("VPTM") < 0 or req.get("VPTM") > 5:
        raise BizException(ERROR_PARAM_ERROR, message="无效VP切换模式")
    params["VPTM"] = VP_MODE_FORWARD_MAP.get(req.get("VPTM"))
    params["VPTT"] = req.get("VPTT")
    params["VPTP"] = req.get("VPTP")
    params["VPTV"] = req.get("VPTV")
    
    # 计量参数
    params["metering_stage"] = req.get("metering_stage")
    for idx in range(0, int(req.get("metering_stage"))):
        params["MP" + str(idx)] = req.get("MP" + str(idx))
        params["MSR" + str(idx)] = req.get("MSR" + str(idx))
        params["MBP" + str(idx)] = req.get("MBP" + str(idx))
        params["ML" + str(idx)] = req.get("ML" + str(idx))
    
    if req.get("DMBM") < 0 or req.get("DMBM") > 2:
        raise BizException(ERROR_PARAM_ERROR, message="无效储前射退模式")
    params["DMBM"] = DECOM_MODE_FORWARD_MAP.get(req.get("DMBM"))
    if req.get("DMAM") < 0 or req.get("DMAM") > 2:
        raise BizException(ERROR_PARAM_ERROR, message="无效储后射退模式")
    params["DMAM"] = DECOM_MODE_FORWARD_MAP.get(req.get("DMAM"))
    
    params["DPBM"] = req.get("DPBM")
    params["DVBM"] = req.get("DVBM")
    params["DDBM"] = req.get("DDBM")
    params["DTBM"] = req.get("DTBM")
    
    params["DPAM"] = req.get("DPAM")
    params["DVAM"] = req.get("DVAM")
    params["DDAM"] = req.get("DDAM")
    params["DTAM"] = req.get("DTAM")
    
    params["MD"] = req.get("MD")
    params["MEL"] = req.get("MEL")

    # 温度参数
    params["barrel_temperature_stage"] = req.get("barrel_temperature_stage")
    for idx in range(0, int(req.get("barrel_temperature_stage"))):
        if idx == 0:
            params["NT"] = req.get("NT")
        else:
            params["BT" + str(idx)] = req.get("BT" + str(idx))
            
    if req.get("MT"):
        params["MT"] = req.get("MT")

    # 构建缺陷反馈信息
    defect_info: list = [
        { "label": "短射", "desc": "SHORTSHOT", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "缩水", "desc": "SHRINKAGE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "飞边", "desc": "FLASH", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "熔接痕", "desc": "WELDLINE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "困气", "desc": "AIRTRAP", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "气纹", "desc": "GASVEINS", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "烧焦", "desc": "BURN", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "料花", "desc": "MATERIALFLOWER", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "色差", "desc": "ABERRATION", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "水波纹", "desc": "WATERRIPPLE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "脱模不良", "desc": "HARDDEMOLDING", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "顶白", "desc": "TOPWHITE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "变形", "desc": "WARPING", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "尺寸偏大", "desc": "OVERSIZE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "尺寸偏小", "desc": "UNDERSIZE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "浇口印", "desc": "GATEMARK", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
        { "label": "阴阳面", "desc": "SHADING", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
    ]
    
    defect_map: dict = {
        "短射": { "name": "short_shot", "degree": "B000", "position": "B001", "lastEffect": "B002" },
        "缩水": { "name": "shrinkage", "degree": "B003", "position": "B004", "lastEffect": "B005" },
        "飞边": { "name": "flash", "degree": "B006", "position": "B007", "lastEffect": "B008" },
        "熔接痕": { "name": "weld_line", "degree": "B009", "position": "B010", "lastEffect": "B011" },
        "困气": { "name": "air_trap", "degree": "B012", "position": "B013", "lastEffect": "B014" },
        "气纹": { "name": "gas_veins", "degree": "B015", "position": "B016", "lastEffect": "B017" },
        "烧焦": { "name": "burn", "degree": "B018", "position": "B019", "lastEffect": "B020" },
        "料花": { "name": "material_flower", "degree": "B021", "position": "B022", "lastEffect": "B023" },
        "色差": { "name": "aberration", "degree": "B024", "position": "B025", "lastEffect": "B026" },
        "水波纹": { "name": "water_ripple", "degree": "B027", "position": "B028", "lastEffect": "B029" },
        "脱模不良": { "name": "hardder_molding", "degree": "B030", "position": "B031", "lastEffect": "B032" },
        "顶白": { "name": "top_white", "degree": "B033", "position": "B034", "lastEffect": "B035" },
        "变形": { "name": "warping", "degree": "B036", "position": "B037", "lastEffect": "B038" },
        "尺寸偏大": { "name": "oversize", "degree": "B039", "position": "B040", "lastEffect": "B041" },
        "尺寸偏小": { "name": "undersize", "degree": "B042", "position": "B043", "lastEffect": "B044" },
        "浇口印": { "name": "gate_mark", "degree": "B045", "position": "B046", "lastEffect": "B047" },
        "阴阳面": { "name": "shading", "degree": "B048", "position": "B049", "lastEffect": "B050" },
    }
    defect_feedback = "上一模修正效果佳"
    feedback_info_correct = False
    for defect in defect_info:
        if defect_map.get(defect["label"]):
            defect_reflect = defect_map.get(defect["label"])
            defect_level = DEFECT_LEVEL_FORWARD_MAP.get(req.get(defect_reflect["degree"]))
            if defect_level is not None and defect_level != "无缺陷":
                defect["level"] = defect_level
                defect["position"] = DEFECT_POSITION_FORWARD_MAP.get(req.get(defect_reflect["position"]))
                if not defect["position"] or defect["position"] == "缺陷位置在0段":
                    defect["position"] = "缺陷位置不指定"
                defect["feedback"] = DEFECT_FEEDBACK_FORWARD_MAP.get(req.get(defect_reflect["lastEffect"]))
                defect["count"] += 1
                defect_feedback = defect["feedback"]
                feedback_info_correct = True
                break
    if not feedback_info_correct:
        raise BizException(ERROR_PARAM_ERROR, "Invalid defect feedback, please select the appropriate defect feedback information.")
    
    params["defect_info"] = defect_info

    # 获取工艺优化记录
    process_optimize = get_process_optimization(params.get("process_index_id"))
    del process_optimize["_id"]
    if not process_optimize:
        raise BizException(ERROR_PARAM_ERROR, "Process optimize record not exist.")
    
    if params["opt_nums"] <= 0:
        raise BizException(ERROR_PARAM_ERROR, "Invalid opt nums, need > 0.")

    if params["opt_nums"] > len(process_optimize["optimize_list"]):
        raise BizException(ERROR_PARAM_ERROR, "Invalid opt nums, data no exist.")

    if process_optimize["precondition"]["mold_id"]:
        project = project_service.get_project_obj_by_id(process_optimize["precondition"]["mold_id"])
        if project.subrule_no:
            params["subrule_no"] = project.subrule_no
            params["general"] = False
        
    # 获取优化记录参数
    process_optimize["optimize_list"] = process_optimize["optimize_list"][:params["opt_nums"]]
    feedback_detail = process_optimize["optimize_list"][params["opt_nums"] - 1]["feedback_detail"]
    params["optimize_export"] = copy.deepcopy(feedback_detail["optimize_export"])
    params["optimize_export"]["defect_feedback"] = defect_feedback
    # 获取模具信息
    
    
    # 调用工艺优化算法
    data = deduce_optimize_process(params)
    # 构建并存储优化数据
    process_detail = construct_saved_format(data, machine_dict)
    optimize_detail = {
        "title": "opt#" + str(data["opt_nums"]),
        "name": str(data["opt_nums"]),
        "process_detail": process_detail,
        'auxiliary_detail': {
            'mold_temp': {
                'setting_temp': data.get("MT")
            }, 
            'hot_runner_temperatures': [], 
            'hot_runner': {
                'sequential_ctrl_time': []
            }
        }, 
        "feedback_detail": {
            "actual_product_weight": None,
            "defect_info": [
                { "label": "短射", "desc": "SHORTSHOT", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "缩水", "desc": "SHRINKAGE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "飞边", "desc": "FLASH", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "熔接痕", "desc": "WELDLINE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "困气", "desc": "AIRTRAP", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "气纹", "desc": "GASVEINS", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "烧焦", "desc": "BURN", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "料花", "desc": "MATERIALFLOWER", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "色差", "desc": "ABERRATION", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "水波纹", "desc": "WATERRIPPLE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "脱模不良", "desc": "HARDDEMOLDING", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "顶白", "desc": "TOPWHITE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "变形", "desc": "WARPING", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "尺寸偏大", "desc": "OVERSIZE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "尺寸偏小", "desc": "UNDERSIZE", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "浇口印", "desc": "GATEMARK", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
                { "label": "阴阳面", "desc": "SHADING", "level": "无缺陷", "position": "缺陷位置不指定", "count": 0, "feedback": None, "remark": None },
            ],
            "optimize_export": data["optimize_export"]
        }
    }
    
    # 更新上一模的缺陷反馈
    feedback_detail["actual_product_weight"] = data.get("actual_product_weight")
    feedback_detail["defect_info"] = data["defect_info"]
    process_optimize["optimize_list"][-1]["feedback_detail"] = feedback_detail
    # 保存新生成的工艺
    process_optimize["optimize_list"].append(optimize_detail)
    update_process_optimization(process_optimize)
    
    data["VPTM"] = VP_MODE_BACKWARD_MAP.get(data.get("VPTM"))
    data["DMBM"] = DECOM_MODE_BACKWARD_MAP.get(data.get("DMBM"))
    data["DMAM"] = DECOM_MODE_BACKWARD_MAP.get(data.get("DMAM"))
    return data


# 优化工艺记录
def deduce_optimize_process(current_value_dict: dict, type: str = "tsk_algorithm"):
    if type == "tsk_algorithm":
        return tsk_algorithm(current_value_dict)


def tsk_algorithm(current_value_dict: dict):
    current_value_dict = {key: value for key, value in current_value_dict.items() if value is not None}
    # 1. 处理缺陷信息（需要增加新的几个缺陷）:获得当前的缺陷名称,大写,位置,程度
    target_defect = None
    target_position = None
    target_level = None
    target_num = 0  # 指的是缺陷在缺陷列表中的序号,0表示短射, 1表示缩水...
    defect_info = current_value_dict.get("defect_info")
    for defect in defect_info:
        if defect["level"] and defect["level"] != "无缺陷":
            target_defect = defect["desc"]  # 大写字母
            target_position = defect["position"]  # 位置
            target_level = defect["level"]  # 程度
            break
        else:
            target_num += 1
    # 2. 构建规则网络（范围不再按照机器设定参数，改为按照子规则库的工艺参数表）
    rule_array, keyword_array, rule_library, rule_priority = rule_service.load_rule_from_database(subrule_no=current_value_dict.get("subrule_no"))
    machine_info = extract_machine(current_value_dict.get("machine_id"))
    read_machine_setting_para(machine_info, keyword_array)

    # 新建列表，将普通规则与特殊规则分开存放
    adjust_array = []
    tsk_array = []
    for a_rule in rule_array:
        # 特殊规则的调整关键字为‘adjust’
        if 'adjust' in a_rule['rule_description']:
            adjust_array.append(a_rule)
        else:
            tsk_array.append(a_rule)
    # model = nets.TskRuleNet(tsk_array, keyword_array)
    model = nets.NumTskRuleNet(tsk_array, keyword_array, rule_priority)
    particular_list = nets.ParticularRules(adjust_array)

    # 3. 构建输入参数
    # 3.1 添加段数注射、保压、计量段数参数
    injection_stage = current_value_dict['injection_stage']
    holding_stage = current_value_dict['holding_stage']
    metering_stage = current_value_dict['metering_stage']
    if injection_stage == 1:
        current_value_dict['injectstage1'] = 0.95
    else:
        current_value_dict['injectstage1'] = 0.05
        current_value_dict['injectstage' + str(injection_stage)] = 0.95
    current_value_dict['holdingstage' + str(holding_stage)] = 0.95
    current_value_dict['meteringstage' + str(metering_stage)] = 0.95

    # 3.2 计算注射各段行程
    if current_value_dict['MEL'] and current_value_dict['IL0']:
        current_value_dict['IDT1'] = current_value_dict['MEL'] - current_value_dict['IL0']
    else:
        logging.info(f"MEL为空?{current_value_dict['MEL']} IL0为空?{current_value_dict['IL0']}")
    for stage in range(0, injection_stage - 1):
        if current_value_dict['IL' + str(stage)] and current_value_dict['IL' + str(stage + 1)]:
            current_value_dict['IDT' + str(stage + 2)] = current_value_dict['IL' + str(stage)] - current_value_dict[
                'IL' + str(stage + 1)]
        else:
            logging.info(
                f"current_value_dict['IL' + str(stage)]为空?{current_value_dict['IL' + str(stage)]} current_value_dict['IL' + str(stage + 1)]为空{current_value_dict['IL' + str(stage + 1)]}")

    # 3.3 是否加上了保压，判断方式：一段保压压力（PP0）是否为0
    # 如果是从工艺列表直接优化,手动输入的保压参数为0,而本次缺陷是缩水的话,那么需要调用初始化获得保压参数
    packing_list = ['PP0', 'PP1', 'PP2', 'PP3', 'PP4', 'PV0', 'PV1', 'PV2', 'PV3', 'PV4', 'PT0', 'PT1', 'PT2', 'PT3', 'PT4',]
    if target_defect == "SHRINKAGE" and current_value_dict['PT0'] == 0:  # 表示缩水
        process_opt_record = get_process_optimization(current_value_dict.get("process_index_id"))
        print(process_opt_record.get("precondition"))
        packing_dict = construct_formatted_process(deduce_process(process_opt_record.get("precondition")))
        current_value_dict.update({key: packing_dict[key] for key in packing_list if key in packing_dict})
    temporary_packing_dict = {}  # 临时存储取出的键值对
    if current_value_dict['PT0'] == 0:
        HOLDEXIST = 0
        # current_value_dict = {key: value for key, value in current_value_dict.items() if key not in packing_list}
        for key in packing_list:
            if key in current_value_dict:
                temporary_packing_dict[key] = current_value_dict.pop(key)
    else:
        HOLDEXIST = 1
    print(HOLDEXIST, temporary_packing_dict)
    current_value_dict['HOLDEXIST'] = HOLDEXIST

    # 3.4 是否是热流道，判断方式：阀口一（SCT0）是否存在
    if current_value_dict.get('SCT0'):
        current_value_dict['VALVEEXIST'] = 1
    else:
        current_value_dict['VALVEEXIST'] = 0

    # 3.5 获取当前注射主打段
    inject_main_stage = MAIN_STAGE.get(injection_stage)

    opt_nums = int(current_value_dict['opt_nums'])
    optimize_export = current_value_dict.get("optimize_export")
    actived_rule_list = []  # 获取有效规则
    extra_dict = {}

    # 3.6 获取反馈的实际产品重量，先判断是否反馈了该参数
    product_weight = current_value_dict['product_weight']
    if 'actual_product_weight' in current_value_dict:
        actual_product_weight = current_value_dict.get('actual_product_weight')
    else:
        actual_product_weight = None


    # 3.7 添加保压切换模式的参数
    VPTM = current_value_dict.get('VPTM')
    if VPTM == '位置':
        current_value_dict['VPTM0'] = 1
    elif VPTM == '时间':
        current_value_dict['VPTM1'] = 1
    elif VPTM == '时间&位置':
        current_value_dict['VPTM2'] = 1
    elif VPTM == '压力':
        current_value_dict['VPTM3'] = 1
    elif VPTM == '速度':
        current_value_dict['VPTM4'] = 1


    # 3.8 添加储前和储后松退模式的参数
    DMBM = current_value_dict.get('DMBM')
    if DMBM == '否':
        current_value_dict['DMBM0'] = 1
    elif DMBM == '距离':
        current_value_dict['DMBM1'] = 1
    elif DMBM == '时间':
        current_value_dict['DMBM2'] = 1

    DMAM = current_value_dict.get('DMAM')
    if DMAM == '否':
        current_value_dict['DMAM0'] = 1
    elif DMAM == '距离':
        current_value_dict['DMAM1'] = 1
    elif DMAM == '时间':
        current_value_dict['DMAM2'] = 1


    # 4. 参数优化计算
    if opt_nums == 1:
        # 首次缺陷修正
        # 针对缺陷，选出激活度最高的几个有效规则
        if target_defect:
            current_value_dict[target_defect] = 0
            if DEFECT_POSITION[target_position] == 0:
                if target_defect == "gas_veins":
                    current_value_dict["DL" + target_defect + str(inject_main_stage)] = 0.99
                else:
                    current_value_dict["DL" + target_defect + '1'] = 0.99
            else:
                current_value_dict[
                    "DL" + target_defect + str(DEFECT_POSITION[target_position])] = 0.99
            actived_rule_list, extra_dict = model.predict(current_value_dict, top_k=10)
            # 过滤列表中激活度低的无效规则
            actived_rule_list = [rule for rule in actived_rule_list if rule[1] > 0.01]
            # 如果缺陷重量未达标，则始终把调整储料行程作为第一选择
            if target_defect == "SHORTSHOT" and actual_product_weight and actual_product_weight < product_weight:
                # 获取注射行程
                for i in range(len(actived_rule_list)):
                    if list(actived_rule_list[0][2].items())[0][0] != 'MEL':
                        actived_rule_list.append(actived_rule_list[0])
                        actived_rule_list.pop(0)
                    else:
                        break

        optimize_export["candidate_rules"] = []
        for rule in actived_rule_list:
            result_key, result_value = 0, 0
            for k, v in rule[2].items():
                result_key = k
                result_value = v
            optimize_export["candidate_rules"].append({
                "rule_id": -1,
                "rule_description": rule[0],
                "rule_activation": rule[1],
                "rule_result_key": result_key,
                "rule_result_value": result_value,
            })
        optimize_export["adjust_rules"] = []
        for a_rule in particular_list.adjust_rule_list:
            if 'rule_defect' in a_rule and a_rule['rule_defect'] in current_value_dict:
                optimize_export["adjust_rules"].append({
                    "rule_id": -1,
                    "rule_description": a_rule['rule_description'] if 'rule_description' in a_rule else None,
                    'rule_defect': a_rule['rule_defect'] if 'rule_defect' in a_rule else None,
                    'rule_output': a_rule['rule_output'] if 'rule_output' in a_rule else None
                })

    elif opt_nums > 1:
        # 获取上一模缺陷以及反馈
        last_defect = optimize_export["defect_name"]
        last_position = optimize_export["defect_position"]
        current_position = target_position
        # 获得上一模缺陷的反馈
        feedback = optimize_export["defect_feedback"]  # 从前端页面获得
        last_defect_feedback = None
        if feedback:
            if DEFECT_FEEDBACK[feedback] or DEFECT_FEEDBACK[feedback] == 0:
                last_defect_feedback = feedback

            # 修正效果佳
            if DEFECT_FEEDBACK[last_defect_feedback] == 0:

                # 获取缺陷等级
                # current_value_dict[target_defect] = DEFECT_LEVEL[defect_info[target_defect]["level"]]  
                current_value_dict[target_defect] = 0
                # 字典中添加缺陷位置参数，参与模糊计算
                if DEFECT_POSITION[target_position] == 0:
                    if target_defect == "gas_veins":
                        current_value_dict["DL" + target_defect + str(inject_main_stage)] = 0.99
                    else:
                        current_value_dict["DL" + target_defect + '1'] = 0.99
                else:
                    current_value_dict[
                        "DL" + target_defect + str(
                            DEFECT_POSITION[target_position])] = 0.99
                actived_rule_list, extra_dict = model.predict(current_value_dict, top_k=10)
                # 过滤列表中激活度低的无效规则
                actived_rule_list = [rule for rule in actived_rule_list if rule[1] > 0.05]

                if target_defect == last_defect and last_position == current_position:
                    # 缺陷程度减轻，沿用上一模调整策略，但是调整幅度的等级要变
                    for rule in actived_rule_list:
                        result_key, result_value = 0, 0
                        for k, v in rule[2].items():
                            result_key, result_value = k, v
                        for rule_num in range(0, len(optimize_export["candidate_rules"])):
                            if result_key == optimize_export["candidate_rules"][rule_num]["rule_result_key"]:
                                optimize_export["candidate_rules"][rule_num]["rule_id"] = -1
                                optimize_export["candidate_rules"][rule_num]["rule_description"] = rule[0]
                                optimize_export["candidate_rules"][rule_num]["rule_activation"] = rule[1]
                                optimize_export["candidate_rules"][rule_num]["rule_result_value"] = result_value
                else:
                    optimize_export["candidate_rules"] = []
                    for rule in actived_rule_list:
                        result_key, result_value = 0, 0
                        for k, v in rule[2].items():
                            result_key = k
                            result_value = v
                        optimize_export["candidate_rules"].append({
                            "rule_id": -1,
                            "rule_description": rule[0],
                            "rule_activation": rule[1],
                            "rule_result_key": result_key,
                            "rule_result_value": result_value,
                        })
                    optimize_export["adjust_rules"] = []
                    for a_rule in particular_list.adjust_rule_list:
                        if 'rule_defect' in a_rule and a_rule['rule_defect'] in current_value_dict:
                            optimize_export["adjust_rules"].append({
                                "rule_id": -1,
                                "rule_description": a_rule['rule_description'] if 'rule_description' in a_rule else None,
                                'rule_defect': a_rule['rule_defect'] if 'rule_defect' in a_rule else None,
                                'rule_output': a_rule['rule_output'] if 'rule_output' in a_rule else None
                            })
            elif DEFECT_FEEDBACK[last_defect_feedback] == 1:
                # 修正效果不佳，调用上一模参数数据
                if current_value_dict['process_index_id']:
                    process_id = current_value_dict['process_index_id']
                else:
                    raise BizException(ERROR_DATA_NOT_EXIST, message="无效工艺id")
                process_optimization = get_process_optimization(process_id)
                if process_optimization:
                    optimize_list = process_optimization.get("optimize_list")
                    optimize_detail = optimize_list[opt_nums - 1]["process_detail"]
                    update_value_dict(optimize_detail, current_value_dict)
                    # current_value_dict[target_defect] = DEFECT_LEVEL[defect_info[target_defect]["level"]]
                    current_value_dict[target_defect] = 0

                    if target_position == 0:
                        if target_defect == "gas_veins":
                            current_value_dict["DL" + target_defect + str(inject_main_stage)] = 0.99
                        else:
                            current_value_dict["DL" + target_defect + '1'] = 0.99
                    else:
                        current_value_dict[
                            "DL" + target_defect + str(DEFECT_POSITION[target_position])] = 0.99
                    actived_rule_list, extra_dict = model.predict(current_value_dict, top_k=10)
                    # 过滤列表中激活度低的无效规则
                    actived_rule_list = [rule for rule in actived_rule_list if rule[1] > 0.01]
                    optimize_export["candidate_rules"] = []
                    for rule in actived_rule_list:
                        result_key, result_value = 0, 0
                        for k, v in rule[2].items():
                            result_key = k
                            result_value = v
                        optimize_export["candidate_rules"].append({
                            "rule_id": -1,
                            "rule_description": rule[0],
                            "rule_activation": rule[1],
                            "rule_result_key": result_key,
                            "rule_result_value": result_value,
                        })
                        optimize_export["adjust_rules"] = []
                        for a_rule in particular_list.adjust_rule_list:
                            if 'rule_defect' in a_rule and a_rule['rule_defect'] in current_value_dict:
                                optimize_export["adjust_rules"].append({
                                    "rule_id": -1,
                                    "rule_description": a_rule['rule_description'] if 'rule_description' in a_rule else None,
                                    'rule_defect': a_rule['rule_defect'] if 'rule_defect' in a_rule else None,
                                    'rule_output': a_rule['rule_output'] if 'rule_output' in a_rule else None
                                })
                    # 对规则进行排序
                    for idx in range(0, len(actived_rule_list)):
                        if actived_rule_list[idx][0] == optimize_export["rule_in_use"]:
                            next_index = (idx + 1) % len(actived_rule_list)
                            optimize_export["candidate_rules"] = optimize_export["candidate_rules"][
                                                                next_index:len(actived_rule_list)] \
                                                                + optimize_export["candidate_rules"][0:next_index]
            # 如果修正幅度过头
            elif DEFECT_FEEDBACK[last_defect_feedback] == 2:

                pass
    # 目前可用规则
    if len(optimize_export["candidate_rules"]) > 0:
        optimize_export["rule_library_in_use"] = "通用规则库"+rule_library if current_value_dict.get("general") else rule_library
        optimize_export["rule_in_use"] = optimize_export["candidate_rules"][0]["rule_description"]
        optimize_export["adjust_name"] = optimize_export["candidate_rules"][0]["rule_result_key"]
        optimize_export["adjust_value"] = optimize_export["candidate_rules"][0]["rule_result_value"]
    else:
        if len(particular_list.adjust_rule_list) != 0:
            # 设置弹窗
            pass
        else:
            raise BizException(ERROR_DATA_NOT_EXIST, message="无候选规则可用！")

    optimize_export["defect_num"] = target_num
    optimize_export["defect_name"] = target_defect
    optimize_export["defect_position"] = target_position
    optimize_export["defect_level"] = target_level
    # 记录调整内容
    current_value_dict["optimize_export"] = optimize_export

    # 根据缺陷程度确定调整系数
    defect_degree = DEFECT_LEVEL[optimize_export["defect_level"]]

    if defect_degree == 0.9:
        w = 2.1
    elif defect_degree == 0.8:
        w = 1.9
    elif defect_degree == 0.5:
        w = 1.5
    else:
        w = 1.0


    if current_value_dict['HOLDEXIST'] == 0:
        current_value_dict.update(temporary_packing_dict)
    update_dict = {}
    # 去掉空值
    update_dict.update({optimize_export["adjust_name"]: optimize_export["adjust_value"]} if optimize_export["adjust_value"] is not None else {})

    for k in update_dict.keys():
        # 如果优化后的值小于0,则限定为0
        if current_value_dict.get(k) and update_dict.get(k) and current_value_dict.get(k) + update_dict.get(k) < 0:
            current_value_dict[k] = 0

        # 如果大于限定值，则限定为该设定的限定值

        if k == 'VPTL':
            # VPTL即注射末段的位置
            current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 2)
            # current_value_dict['IL' + str(injection_stage - 1)] = current_value_dict[k]
            current_value_dict['IDT' + str(inject_main_stage)] -= update_dict.get(k) * w
        # elif k in ['IL0', 'IL1', 'IL2', 'IL3', 'IL4', 'IL5']:
        #     # 最后一级注射位置为VP位置
        #     current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 2)
        #     if k[2] == str(current_value_dict['injection_stage'] - 1):
        #         current_value_dict['VPTL'] = current_value_dict[k]
        elif k in ['IDT1', 'IDT2', 'IDT3', 'IDT4', 'IDT5', 'IDT6']:
            if current_value_dict[k] + update_dict.get(k) * w > 0:
                current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 2)
            if injection_stage >= 2:
                if k[3] == str(inject_main_stage):
                    if injection_stage == 2:
                        current_value_dict['IDT' + str(int(k[3]) - 1)] -= update_dict.get(k) * w
                    else:
                        current_value_dict['IDT' + str(int(k[3]) + 1)] -= update_dict.get(k) * w
                else:
                    if k[3] == str(injection_stage):
                        current_value_dict['IDT' + str(int(k[3]) - 1)] -= update_dict.get(k) * w
                    else:
                        for j in range(1, injection_stage - int(k[3]) + 1):
                            if current_value_dict['IDT' + str(int(k[3]) + j)] - update_dict.get(k) * w > 0:
                                current_value_dict['IDT' + str(int(k[3]) + j)] -= update_dict.get(k) * w
                                break

        elif k in ['PT0', 'PT1', 'PT2', 'PT3', 'PT4', 'SCT0', 'SCT1', 'SCT2', 'SCT3', 'SCT4', 'SCT5', 'SCT6', 'SCT7', 'SCT8',]:
            # 保留一位小数的参数（保压时间和热流道时间）
            current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 1)
        elif k == 'MEL':
            # 计量终止位置，储料终止位置=计量末段位置+储前距离+储后距离
            MEL_update_dict = {}
            product_weight = current_value_dict['product_weight']
            actual_product_weight = current_value_dict.get('actual_product_weight') if 'actual_product_weight' in current_value_dict else None
            meter_stage = int(current_value_dict["metering_stage"])
            # 根据制品重量进行动态调整
            if target_defect == "SHORTSHOT" and actual_product_weight and actual_product_weight < product_weight:
                # 获取注射行程
                act_inject_lenth = current_value_dict["ML" + str(meter_stage - 1)] - current_value_dict["VPTL"]
                rec_inject_lenth = round(product_weight * act_inject_lenth / actual_product_weight, 2)
                if current_value_dict.get('DDBM'):
                    metering_end_location = round(
                        rec_inject_lenth + current_value_dict["VPTL"] + current_value_dict["DDBM"] + current_value_dict["DDAM"], 2)
                else:
                    metering_end_location = round(
                        rec_inject_lenth + current_value_dict["VPTL"] + current_value_dict["DDAM"], 2)
                MEL_update_dict['value'] = metering_end_location - current_value_dict['MEL']
                current_value_dict['MEL'] = metering_end_location
            else:
                current_value_dict['MEL'] = round(current_value_dict['MEL'] + update_dict.get(k) * w, 2)
                MEL_update_dict['value'] = update_dict.get(k) * w
            # 更新计量位置(考虑调整受限)
            if machine_info.get("max_injection_stroke") and current_value_dict['MEL'] > machine_info.get(
                    "max_injection_stroke"):
                current_value_dict['MEL'] = machine_info.get("max_injection_stroke")
                MEL_update_dict['value'] -= float(current_value_dict['MEL']) - float(machine_info.get("max_injection_stroke"))

            if current_value_dict.get('DDBM'):
                current_value_dict["ML" + str(meter_stage - 1)] = round(float(current_value_dict['MEL']) - float(current_value_dict['DDBM']) - float(current_value_dict['DDAM']), 2)
            else:
                current_value_dict["ML" + str(meter_stage - 1)] = round(float(current_value_dict['MEL']) - float(current_value_dict['DDAM']), 2)
            d = {1: [1], 2: [1, 0.5], 3: [1, 0.7, 0.3], 4: [1, 0.75, 0.5, 0.25]}
            rec_inject_lenth = current_value_dict["ML" + str(meter_stage - 1)] - 30  # fInjectionLen
            for i in range(meter_stage):
                current_value_dict['ML' + str(meter_stage - i - 1)] = round(
                    d.get(meter_stage)[i] * rec_inject_lenth + 30, 2)
            current_value_dict['IDT' + str(inject_main_stage)] += MEL_update_dict['value']
        elif k in ["NT", "BT1"]:
            # 料筒温度
            if k == "NT":
                current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 0)
                current_value_dict['BT1'] = current_value_dict['NT'] + 5
                for i in range(2, 6):
                    current_value_dict['BT' + str(i)] = current_value_dict['BT' + str(i - 1)] - 10
            elif k == "BT1":
                current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w, 0)
                current_value_dict['NT'] = current_value_dict['BT1'] - 5
                for i in range(2, 6):
                    current_value_dict['BT' + str(i)] = current_value_dict['BT' + str(i - 1)] - 10
        else:
            if k in current_value_dict:
                current_value_dict[k] = round(current_value_dict[k] + update_dict.get(k) * w)
    if injection_stage >= 2:
        current_value_dict['IL0'] = round(float(current_value_dict.get('MEL')) - float(current_value_dict.get('IDT1')), 2)
        current_value_dict['IL1'] = round(current_value_dict.get('IL0') - current_value_dict.get('IDT2'), 2)
        if injection_stage >= 3:
            current_value_dict['IL2'] = round(current_value_dict.get('IL1') - current_value_dict.get('IDT3'), 2)
            if injection_stage >= 4:
                current_value_dict['IL3'] = round(current_value_dict.get('IL2') - current_value_dict.get('IDT4'), 2)
                if injection_stage >= 5:
                    current_value_dict['IL4'] = round(
                        current_value_dict.get('IL3') - current_value_dict.get('IDT5'), 2)
                    if injection_stage >= 6:
                        current_value_dict['IL5'] = round(
                            current_value_dict.get('IL4') - current_value_dict.get('IDT6'), 2)
    current_value_dict['VPTL'] = current_value_dict.get('IL' + str(injection_stage - 1))

    param_check(current_value_dict)

    return current_value_dict