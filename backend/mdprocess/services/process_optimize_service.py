from gis.common.exceptions import BizException

from hsmolding.models import Machine, MachineInjector, Polymer
from hsmolding.exceptions import ERROR_DATA_NOT_EXIST, ERROR_MACHINE, ERROR_POLYMER, ERROR_PRODUCT
from hsmolding.services import project_service

from mdprocess.models import ProcessIndex
from mdprocess.dao.process_optimization_model import ProcessOptimizationDoc
from mdprocess.services import process_index_service, rule_service
from mdprocess.utils.process_initialization.process_generate import ProcessInitializer
from mdprocess.utils.fuzzykit.fuzzy_core.models import nets
from mdprocess.const import DEFECT_LEVEL, DEFECT_POSITION, DEFECT_FEEDBACK, MAIN_STAGE

import logging
from decimal import Decimal

optimize_target_defect = None

# 获取工艺优化记录
def get_process_optimization(process_index_id):
    optimization = ProcessOptimizationDoc.objects.filter(process_index_id=process_index_id).first()
    if optimization:
        return optimization.to_dict() if optimization else None
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, "该工艺优化记录不存在")


# 添加工艺优化记录
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


# 删除工艺优化记录
def delete_process_optimization(process_index_id):
    process_index = ProcessIndex.objects.filter(id=process_index_id).first()
    if process_index:
        process_index.delete()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, "该工艺优化记录不存在")
    optimization = ProcessOptimizationDoc.objects.filter(process_index_id=process_index_id).first()
    if optimization:
        optimization.delete()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, "该工艺优化记录不存在")


# 删除多条工艺优化记录
def delete_multiple_process(process_id_list: list):
    for process_index_id in process_id_list:
        delete_process_optimization(process_index_id)


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
        init_info["product_weight"] = params.get("product_total_weight")
    
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
    ret['mold_temp'] = result['mold_param'].mold_temp
    return ret


# 工艺参数初始化
def initialize_process(params: dict):
    process = process_index_service._add_process_index(params)
    # 推理初始工艺参数
    result = deduce_process(params)
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
    # 构建输出结果
    ret = construct_formatted_process(result)
    ret['process_index_id'] = process.id
    print("------------5.数据构建完成---------------")
    return ret


# 优化工艺记录
def optimize_process(current_value_dict: dict, type: str = "tsk_algorithm"):
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