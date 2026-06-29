from hsmolding.services import project_service
from hsmolding.models import Machine, Polymer, MachineInjector
from mqtt.utils import construct_saved_format, conv_view_data
from mdprocess.services import process_optimize_service, process_index_service
from datetime import datetime
from mqtt.const import DECOM_MAP, VP_SWITCH_MAP
from gis.admin.models import Company
from gis.common.exceptions import BizException
from hsmolding.exceptions import ERROR_EXPERT_ERROR
import logging


def add_expert_process(request_params):
    logging.info(request_params)

    request_name = request_params.get("request")
    yizumi_id = None
    if request_name == "yizumi":
        company = Company.objects.filter(name=request_name).first()
        if company:
            yizumi_id = company.id
    else:
        raise BizException(ERROR_EXPERT_ERROR, "request需要等于yizumi")
    mold_id = request_params.get("mold_id")
    if not mold_id:
        raise BizException(ERROR_EXPERT_ERROR, "mold_id是必填项")
    machine_serial_no = request_params.get("machine_serial_no")
    polymer_id = request_params.get("polymer_id")
    precondition_dict, machine_dict, polymer_dict = construct_basic_info(mold_id, machine_serial_no, polymer_id)
    if request_params.get("opt_nums") == 0:
        process_no = "P" + datetime.now().strftime("%Y%m%d%H%M%S")
        # 构建参数
        params: dict = {}
        params = {
            "company_id": yizumi_id,
            "status": 4,
            "process_no": process_no,
            "data_sources": "专家调优",

            **precondition_dict,

            "machine_id": machine_dict.get("id"),
            "machine_trademark": machine_dict.get("trademark"),
            "machine_serial_no": machine_dict.get("serial_no"),
            "machine_data_source": machine_dict.get("data_source"),

            "polymer_id": polymer_dict.get("id"),
            "polymer_trademark":polymer_dict.get("trademark"),
            "polymer_abbreviation":polymer_dict.get("abbreviation"),
            "recommend_melt_temperature":polymer_dict.get("min_melt_temperature"),
            
            "injection_stage": request_params.get("injection_stage"),
            "holding_stage": request_params.get("holding_stage"),
            "VP_switch_mode": VP_SWITCH_MAP.get(request_params.get("VPTM")),
            "metering_stage": request_params.get("metering_stage"),
            "decompressure_mode_before_metering": DECOM_MAP.get(request_params.get("DMBM")),
            "decompressure_mode_after_metering": DECOM_MAP.get(request_params.get("DMAM")),
            "barrel_temperature_stage": request_params.get("barrel_temperature_stage"),
        }

        # 保存process_index,获得id
        process_index = process_index_service.add_process_index(params)
        process_optimization = construct_process_record(params, request_params, machine_dict, polymer_dict, process_index.get("id"))
        if process_optimization:
            return {"process_index_id": process_optimization.get("process_index_id"), "process_no": process_no, "opt_nums":request_params.get("opt_nums")}
    else:
        # 获取工艺优化记录
        process_no = request_params.get("process_no")
        process_optimize = process_optimize_service.get_process_optimization(request_params.get("process_index_id"))
        del process_optimize["_id"]

        process_optimize["optimize_list"] = process_optimize["optimize_list"][:request_params["opt_nums"]]
        feedback_detail = process_optimize["optimize_list"][request_params["opt_nums"] - 1]["feedback_detail"]
        
        injection_dict: dict = MachineInjector.objects.filter(machine_id=machine_dict.get("id")).first().to_dict()
        conv_view_data(request_params, machine_dict, injection_dict)
        process_detail = construct_saved_format(request_params, machine_dict)
        defect_info = construct_defect_info(request_params)
        optimize_detail = {
            "title": "opt#" + str(request_params["opt_nums"]),
            "name": str(request_params["opt_nums"]),
            "process_detail": process_detail,
            'auxiliary_detail': {
                'mold_temp': {
                    'setting_temp': polymer_dict.get("max_mold_temperature")
                }, 
                'hot_runner_temperatures': [], 
                'hot_runner': {
                    'sequential_ctrl_time': []
                }
            }, 
            "feedback_detail": {
                "actual_product_weight": None,
                "defect_info": defect_info
            }
        }

        # 更新上一模的缺陷反馈
        feedback_detail["actual_product_weight"] = request_params.get("actual_product_weight")
        feedback_detail["defect_info"] = defect_info
        process_optimize["optimize_list"][-1]["feedback_detail"] = feedback_detail
        # 保存新生成的工艺
        process_optimize["optimize_list"].append(optimize_detail)
        process_optimization = process_optimize_service.update_process_optimization(process_optimize)
        process_optimization = process_optimization.to_dict()
        return {"process_index_id": process_optimization.get("process_index_id"), "process_no": process_no, "opt_nums":request_params.get("opt_nums")}


def construct_defect_info(request_params):
    defect_info = [
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
    
    for defect in defect_info:
        if defect_map.get(defect["label"]):
            defect_reflect = defect_map.get(defect["label"])
            if request_params.get(defect_reflect["degree"]) and request_params.get(defect_reflect["degree"]) != "无缺陷":
                defect["level"] = request_params.get(defect_reflect["degree"])
                defect["position"] = request_params.get(defect_reflect["position"])
                if not defect["position"] or defect["position"] == "缺陷位置在0段":
                    defect["position"] = "缺陷位置不指定"
                defect["feedback"] = request_params.get(defect_reflect["lastEffect"])
                defect["count"] += 1
                defect_feedback = defect["feedback"]
                if defect_feedback is None:
                    defect_feedback = "上一模修正效果佳"
    return defect_info


def construct_basic_info(mold_id, machine_serial_no, polymer_id):
    # 获取模具信息
    if mold_id:
        mold_info = project_service.get_mold_dict_by_id(int(mold_id))
        if mold_info:
            precondition_dict = {
                "mold_id": mold_info.get("id"),
                "mold_no": mold_info.get("mold_no"),
                "cavity_num": mold_info.get("cavity_num"),
                "inject_cycle_require": mold_info.get("inject_cycle_require"),
                "subrule_no": mold_info.get("subrule_no"),
                "product_type": mold_info.get("product_small_type"),
                "product_no": mold_info.get("product_no"),
                "product_name": mold_info.get("product_name"),
            }
            # 获取制品信息
            product_info: dict = mold_info["product_infos"][0]
            if product_info:
                precondition_dict.update({
                    "inject_part": "0",
                    "product_ave_thickness": float(product_info.get("ave_thickness")) if product_info.get("ave_thickness") else None,
                    "product_max_thickness": float(product_info.get("max_thickness")) if product_info.get("max_thickness") else None,
                    "product_max_length": float(product_info.get("flow_length")) if product_info.get("flow_length") else None,
                    "product_total_weight": float(mold_info.get("product_total_weight", 0)) + float(product_info.get("runner_weight", 0)),
                    
                    "runner_length": float(product_info.get("runner_length")) if product_info.get("runner_length") else None,
                    "runner_weight": float(product_info.get("runner_weight")) if product_info.get("runner_weight") else None,
                    "gate_type": product_info.get("gate_type") if product_info.get("gate_type") else None,
                    "gate_num": product_info.get("gate_num") if product_info.get("gate_num") else None,
                    "gate_shape": product_info.get("gate_shape") if product_info.get("gate_shape") else None,
                    "gate_area": float(product_info.get("gate_area")) if product_info.get("gate_area") else None,
                    "gate_radius": float(product_info.get("gate_radius")) if product_info.get("gate_radius") else None,
                    "gate_length": float(product_info.get("gate_length")) if product_info.get("gate_length") else None,
                    "gate_width": float(product_info.get("gate_width")) if product_info.get("gate_width") else None,

                    "runner_type": product_info.get("runner_type") if product_info.get("runner_type") else None,
                    "hot_runner_num": product_info.get("hot_runner_num") if product_info.get("hot_runner_num") else None,
                    "valve_num": product_info.get("valve_num") if product_info.get("valve_num") else None,
                })
        else:
            raise BizException(ERROR_EXPERT_ERROR, "请填写有效的mold_id")   
        # 获取机器信息
        machine_dict = None
        polymer_dict = None
        if machine_serial_no:
            machine_obj = Machine.objects.filter(serial_no=str(machine_serial_no)).first()
            if not machine_obj:
                raise BizException(ERROR_EXPERT_ERROR, "请填写有效的machine_serial_no")
            else:
                machine_dict = machine_obj.to_dict()
        else:
            raise BizException(ERROR_EXPERT_ERROR, "请填写有效的machine_serial_no")       
        # 获取材料信息
        if polymer_id:
            polymer_obj = Polymer.objects.filter(pk=int(polymer_id)).first()
            if not polymer_obj:
                raise BizException(ERROR_EXPERT_ERROR, "请填写有效的polymer_id") 
            else:
                polymer_dict = polymer_obj.to_dict()
        else:
            raise BizException(ERROR_EXPERT_ERROR, "请填写有效的polymer_id") 
        return precondition_dict, machine_dict, polymer_dict
    else:
        raise BizException(ERROR_EXPERT_ERROR, "请填写有效的mold_id") 


def construct_process_record(params, data, machine_dict, polymer_dict, process_index_id):
    setting_temp = polymer_dict.get("max_mold_temperature")
    optimize_record = {
        'precondition': {
            'machine_trademark': params.get("machine_trademark"), 
            'polymer_trademark': params.get("polymer_trademark"), 
            'hot_runner_num': params.get("hot_runner_num"), 
            'product_max_thickness': params.get("product_max_thickness"), 
            'gate_num': params.get("gate_num"), 
            'product_ave_thickness': params.get("product_ave_thickness"), 
            'product_no': params.get("product_no"),
            'product_total_weight': params.get("product_total_weight"), 
            'mold_id': params.get("mold_id"), 
            'gate_shape': params.get("gate_shape"), 
            'gate_type': params.get("gate_type"), 
            'cavity_num': params.get("cavity_num"), 
            'gate_area': params.get("gate_area"), 
            'machine_serial_no': params.get("machine_serial_no"), 
            'polymer_id': params.get("polymer_id"),  
            'machine_id': params.get("machine_id"), 
            'product_name': params.get("product_name"), 
            'runner_weight': params.get("runner_weight"), 
            'data_sources': params.get("data_sources"), 
            'gate_radius': params.get("gate_radius"), 
            'runner_length': params.get("runner_length"), 
            'gate_width': params.get("gate_width"), 
            'product_max_length': params.get("product_max_length"),  
            'recommend_melt_temperature': params.get("recommend_melt_temperature"), 
            'product_type': params.get("product_type"), 
            'runner_type': params.get("runner_type"),  
            'machine_data_source': params.get("machine_data_source"), 
            'mold_no': params.get("mold_no"), 
            'inject_part': '0', 
            'gate_length':  params.get("gate_length"), 
            'polymer_abbreviation': params.get("polymer_abbreviation"),
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
                    'table_data': [{'unit': '℃', 'sections': [None, None, None, None, None, None, None, None, None, None], 'label': '温度'}], 
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
                    'metering_delay_time': None, 
                    'metering_ending_position': None, 
                    'table_data': [
                        {'unit': 'bar', 'sections': [None, None, None, None], 'label': '压力'}, 
                        {'unit': 'rpm', 'sections': [None, None, None, None], 'label': '螺杆转速'}, 
                        {'unit': 'bar', 'sections': [None, None, None, None], 'label': ' 背压'}, 
                        {'unit': 'mm', 'sections': [None, None, None, None], 'label': '位置'}
                    ], 
                    'metering_stage': 1, 
                    'decompressure_mode_before_metering': '否', 
                    'max_metering_stage_option': 4, 
                    'decompressure_paras': [
                        {'distance': None, 'velocity': None, 'pressure': None, 'label': '储前', 'time': 0.0}, 
                        {'distance': None, 'velocity': None, 'pressure': None, 'label': '储后', 'time': 0.0}
                    ], 
                    'decompressure_mode_after_metering': '距离'
                }, 
                'inject_para': {
                    'table_data': [
                        {'unit': 'bar', 'sections': [None, None, None, None, None, None], 'label': '压力'}, 
                        {'unit': '%', 'sections': [None, None, None, None, None, None], 'label': '速度'}, 
                        {'unit': 'mm', 'sections': [None, None, None, None, None, None], 'label': '位置'}
                    ], 
                    'cooling_time': None, 
                    'injection_delay_time': None, 
                    'injection_stage': None, 
                    'max_injection_stage_option': None, 
                    'injection_time': None
                }, 
                'VP_switch': {
                    'VP_switch_pressure': None, 
                    'VP_switch_time': None, 
                    'VP_switch_mode': '位置', 
                    'VP_switch_velocity': None, 
                    'VP_switch_position': None
                }
            }, 
            'auxiliary_detail': {'mold_temp': {'setting_temp': setting_temp}, 'hot_runner_temperatures': [], 'hot_runner': {'sequential_ctrl_time': []}}, 
        }], 
        'process_index_id': process_index_id, 
        'flaw_picture_url': None
    }
    injection_dict: dict = MachineInjector.objects.filter(machine_id=machine_dict.get("id")).first().to_dict()
    conv_view_data(data, machine_dict, injection_dict)
    process_detail = construct_saved_format(data, machine_dict)
    optimize_record["optimize_list"][0]["process_detail"] = process_detail
    defect_info = construct_defect_info(data)
    optimize_record["optimize_list"][0]["feedback_detail"]["defect_info"] = defect_info
    if optimize_record.get("process_index_id"):
        process_optimization = process_optimize_service.add_process_optimization(optimize_record)
        return process_optimization
