import logging
from django.core.management.base import BaseCommand
from django.db import transaction
import paho.mqtt.client as mqtt
import json

from hsmolding.models import Company, Machine, MachineInjector, Polymer
from hsmolding.services import project_service, polymer_service, machine_service
from mdprocess.services import process_optimize_service, process_transplant_service
from mdprocess.dao.process_record_model import ProcessParameterRecordDoc

import threading
from mqtt.utils import (
    construct_saved_format, 
    conv_spc_data, 
    conv_view_data, 
    conv_process_from_database, 
    conv_simple_format
)
from mqtt.const import DECOM_MAP, VP_SWITCH_MAP

from datetime import datetime
from django.db import connection
import copy

import traceback


sub_topic = "yizumi/request"
pub_topic = "yizumi/response"

'''
data = {
    "process_index_id" : data.get("process_index_id"),
    "injection_stage" : data.get("injection_stage"),
    "IP0" : data.get("IP0"),
    "IV0" : data.get("IV0"),
    "IL0" : data.get("IL0"),
    "IP1" : data.get("IP1"),
    "IV1" : data.get("IV1"),
    "IL1" : data.get("IL1"),
    "IP2" : data.get("IP2"),
    "IV2" : data.get("IV2"),
    "IL2" : data.get("IL2"),
    "IP3" : data.get("IP3"),
    "IV3" : data.get("IV3"),
    "IL3" : data.get("IL3"),
    "IP4" : data.get("IP4"),
    "IV4" : data.get("IV4"),
    "IL4" : data.get("IL4"),
    "IP5" : data.get("IP5"),
    "IV5" : data.get("IV5"),
    "IL5" : data.get("IL5"),
    "IT" : data.get("IT"),
    "ID" : data.get("ID"),
    "CT" : data.get("CT"),
    "VPTM" : VP_SWITCH_MAP[data.get("VPTM")],
    "VPTT" : data.get("VPTT"),
    "VPTL" : data.get("VPTL"),
    "VPTP" : data.get("VPTP"),
    "VPTV" : data.get("VPTV"),
    "holding_stage" : data.get("holding_stage"),
    "PP0" : data.get("PP0"),
    "PV0" : data.get("PV0"),
    "PT0" : data.get("PT0"),
    "PP1" : data.get("PP1"),
    "PV1" : data.get("PV1"),
    "PT1" : data.get("PT1"),
    "PP2" : data.get("PP2"),
    "PV2" : data.get("PV2"),
    "PT2" : data.get("PT2"),
    "PP3" : data.get("PP3"),
    "PV3" : data.get("PV3"),
    "PT3" : data.get("PT3"),
    "PP4" : data.get("PP4"),
    "PV4" : data.get("PV4"),
    "PT4" : data.get("PT4"),
    "metering_stage" : data.get("metering_stage"),
    "MP0" : data.get("MP0"),
    "MSR0" : data.get("MSR0"),
    "MBP0" : data.get("MBP0"),
    "ML0" : data.get("ML0"),
    "MP1" : data.get("MP1"),
    "MSR1" : data.get("MSR1"),
    "MBP1" : data.get("MBP1"),
    "ML1" : data.get("ML1"),
    "MP2" : data.get("MP2"),
    "MSR2" : data.get("MSR2"),
    "MBP2" : data.get("MBP2"),
    "ML2" : data.get("ML2"),
    "MP3" : data.get("MP3"),
    "MSR3" : data.get("MSR3"),
    "MBP3" : data.get("MBP3"),
    "ML3" : data.get("ML3"),
    "DMBM" : DECOM_MAP[data.get("DMBM")],
    "DMAM" : DECOM_MAP[data.get("DMAM")],
    "DPBM" : data.get("DPBM"),
    "DVBM" : data.get("DVBM"),
    "DDBM" : data.get("DDBM"),
    "DTBM" : data.get("DTBM"),
    "DPAM" : data.get("DPAM"),
    "DVAM" : data.get("DVAM"),
    "DDAM" : data.get("DDAM"),
    "DTAM" : data.get("DTAM"),
    "MD" : data.get("MD"),
    "MEL" : data.get("MEL"),
    "barrel_temperature_stage" : data.get("barrel_temperature_stage"),
    "NT" : data.get("NT"),
    "BT1" : data.get("BT1"),
    "BT2" : data.get("BT2"),
    "BT3" : data.get("BT3"),
    "BT4" : data.get("BT4"),
    "BT5" : data.get("BT5"),
    "BT6" : data.get("BT6"),
    "BT7" : data.get("BT7"),
    "BT8" : data.get("BT8"),
    "BT9" : data.get("BT9"),
    "mold_temp" : data.get("BT9"),
    "opt_nums" : 0
}
'''


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(sub_topic)


def on_message(client, userdata, msg):
    connection.close()
    
    # 先检查接收到的内容
    try:
        payload_str = msg.payload.decode('utf-8')
    except Exception as e:
        payload_str = msg.payload.decode('gbk')
    payload_str = payload_str.replace('\t','').replace('\n','').replace('\r','').replace("'", '"')
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + payload_str)
    
    # 处理数据
    try:
        req = dict(json.loads(payload_str))
        request_name = req.get("request")
        request_operate = req.get("operate")
        if request_name == "yizumi":
            company = Company.objects.filter(name=request_name).first()
            yizumi_id = company.id
        else:
            raise Exception("Invalid request object")
        
        data = {} # 返回数据
        if request_operate == "getMoldList":
            """_summary_
            # 获取模具列表
            """
            items = project_service.get_prompt_list_of_column(column="mold_no", input_str="", company_id=yizumi_id)
            data = [ { "id": item.get("mold_id"), "mold_no": item.get("value") } for item in items ]

        elif request_operate == "getMoldInfo":
            """_summary_
            # 获取模具信息
            """
            if not req.get("id"):
                raise Exception("Get mold info failed, invalid id.")
            mold_info = project_service.get_mold_dict_by_id(int(req.get("id")))
            data = {
                "id": mold_info.get("id"),
                "mold_no": mold_info.get("mold_no"),
                "product_name": mold_info.get("product_name"),
                "product_type": mold_info.get("product_type"),
                "cavity_num": mold_info.get("cavity_num"),

            }
            # 构建制品信息
            product_info: dict = mold_info.get("product_infos")[0]
            if product_info:
                data.update({
                    "product_ave_thickness": float(product_info.get("ave_thickness")) if product_info.get("ave_thickness") else None,
                    "product_max_thickness": float(product_info.get("max_thickness")) if product_info.get("max_thickness") else None,
                    "product_max_length": float(product_info.get("flow_length")) if product_info.get("flow_length") else None,
                    "product_total_weight": float(product_info.get("single_weight")) if product_info.get("single_weight") else 0 
                    + float(product_info.get("runner_weight")) if product_info.get("runner_weight") else 0,
                    
                    "runner_length": float(product_info.get("runner_length")) if product_info.get("runner_length") else None,
                    "runner_weight": float(product_info.get("runner_weight")) if product_info.get("runner_weight") else None,
                    "gate_type": product_info.get("gate_type"),
                    "gate_num": product_info.get("gate_num"),
                    "gate_shape": product_info.get("gate_shape"),
                    "gate_area": float(product_info.get("gate_area")) if product_info.get("gate_area") else None,
                    "gate_radius": float(product_info.get("gate_radius")) if product_info.get("gate_radius") else None,
                    "gate_length": float(product_info.get("gate_length")) if product_info.get("gate_length") else None,
                    "gate_width": float(product_info.get("gate_width")) if product_info.get("gate_width") else None,

                    "runner_type": product_info.get("runner_type"),
                })
            
        elif request_operate == "getPolyTypeList":
            """_summary_
            # 获取材料列表
            """
            items = polymer_service.list_polymer_abbreviation(company_id=yizumi_id)
            data = [ { "polymer_type": item.get("value") } for item in items ]
            
        elif request_operate == "getPolyAbbrList":
            """_summary_
            # 获取材料牌号
            """
            polymer_type = req.get("polymer_type") if req.get("polymer_type") else ""
            items = polymer_service.list_polymer_trademark(abbreviation=polymer_type, company_id=yizumi_id)
            data = [ { "id": item.get("id"), "abbreviation": item.get("abbreviation"), "trademark": item.get("trademark") } for item in items ]
            
        elif request_operate == "getInitProcess":
            """_summary_
            # 获取初始工艺
            """
            # 获取模具信息
            mold_info = project_service.get_mold_dict_by_id(int(req.get("mold_id")))
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
            
            # 获取机器信息
            machine_dict = Machine.objects.filter(serial_no=str(req.get("machine_serial_no"))).first().to_dict()
            
            # 获取材料信息
            polymer_dict = Polymer.objects.get(pk=int(req.get("polymer_id"))).to_dict()

            # 为了适配后端接口，构建接口所需参数
            params: dict = {}
            params = {
                "company_id": yizumi_id,
                "optimize_type": 1,
                "status": 1,
                "process_no": "P" + datetime.now().strftime("%Y%m%d%H%M%S"),

                **precondition_dict,

                "machine_id": machine_dict.get("id"),
                "polymer_id": polymer_dict.get("id"),
                
                "injection_stage": req.get("injection_stage"),
                "holding_stage": req.get("holding_stage"),
                "VP_switch_mode": VP_SWITCH_MAP.get(req.get("VP_switch_mode")),
                "metering_stage": req.get("metering_stage"),
                "decompressure_mode_before_metering": DECOM_MAP.get(req.get("decompressure_mode_before_metering")),
                "decompressure_mode_after_metering": DECOM_MAP.get(req.get("decompressure_mode_after_metering")),
                "barrel_temperature_stage": req.get("barrel_temperature_stage"),
            }
            data = process_optimize_service.initialize_process(params)
            # 保压参数 (首模不加保压)
            for i in range(0, int(data["holding_stage"])):
                data["PT" + str(i)] = 0

            # 构建初始工艺数据存储结构
            optimize_record = {
                'precondition': {
                    'machine_id': params.get("machine_id"), 
                    'machine_trademark': machine_dict.get("trademark"), 
                    'machine_data_source': machine_dict.get("data_source"), 
                    'machine_serial_no': machine_dict.get("serial_no"), 
                    'polymer_id': params.get("polymer_id"),  
                    'polymer_trademark': polymer_dict.get("trademark"), 
                    'polymer_abbreviation': polymer_dict.get("abbreviation"),
                    'recommend_melt_temperature': polymer_dict.get("recommend_melt_temperature"), 
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
                    'product_name': params.get("product_name"), 
                    'runner_weight': params.get("runner_weight"), 
                    'data_sources': params.get("data_sources"), 
                    'gate_radius': params.get("gate_radius"), 
                    'runner_length': params.get("runner_length"), 
                    'gate_width': params.get("gate_width"), 
                    'product_max_length': params.get("product_max_length"),  
                    'product_type': params.get("product_type"), 
                    'runner_type': params.get("runner_type"),  
                    'mold_no': params.get("mold_no"), 
                    'inject_part': '0', 
                    'gate_length':  params.get("gate_length"), 
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
                'process_index_id': data.get("process_index_id"), 
                'flaw_picture_url': None
            }
            process_detail = construct_saved_format(data, machine_dict)
            optimize_record["optimize_list"][0]["process_detail"] = process_detail
            if optimize_record.get("process_index_id"):
                process_optimize_service.add_process_optimization(optimize_record)
            
            # 适配 yizumi 需求，进行参数映射
            injection_dict: dict = MachineInjector.objects.filter(machine_id=machine_dict.get("id")).first().to_dict()
            data["opt_nums"] = 0
            
            # 转换成伊之密可识别的opc数据
            conv_spc_data(data, machine_dict, injection_dict)
        elif request_operate == "getOptProcess":
            """_summary_
            # 优化工艺参数
            """
            if not req.get("process_index_id"):
                raise Exception("Invalid process i id")
            
            # 获取机器信息
            machine_serial_no = str(req.get("machine_serial_no"))
            machine = Machine.objects.filter(serial_no=machine_serial_no).first()
            machine_id = machine.id
            machine_dict = machine.to_dict()
            injection_dict = MachineInjector.objects.filter(machine_id=machine_id).first().to_dict()
            
            # 为了适配后端接口，构建接口所需参数
            params: dict = {}
            params = {
                "actual_product_weight": req.get("actual_product_weight"),
                "process_index_id": int(req.get("process_index_id")),
                "machine_id": machine_id,
                "product_weight": req.get("product_weight"),
                "opt_nums": int(req.get("opt_nums", 1)),
                "polymer_abbreviation": req.get("polymer_abbreviation"),
                "product_small_type": req.get("product_small_type"),
                "subrule_no": "R20240702164137",
                "general": True
            }
            
            # 转换成系统可识别的参数
            conv_view_data(req, machine_dict, injection_dict)
            
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
            params["VPTM"] = req.get("VPTM")
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
            
            params["DMBM"] = req.get("DMBM")
            params["DMAM"] = req.get("DMAM")
            
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
                    
            if req.get("mold_temp"):
                params["MT"] = req.get("mold_temp")
        
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
                    if req.get(defect_reflect["degree"]) is not None and req.get(defect_reflect["degree"]) != "无缺陷":
                        defect["level"] = req.get(defect_reflect["degree"])
                        defect["position"] = req.get(defect_reflect["position"])
                        if not defect["position"] or defect["position"] == "缺陷位置在0段":
                            defect["position"] = "缺陷位置不指定"
                        defect["feedback"] = req.get(defect_reflect["lastEffect"])
                        defect["count"] += 1
                        defect_feedback = defect["feedback"]
                        feedback_info_correct = True
                        break
            if not feedback_info_correct:
                raise Exception("Invalid defect feedback, please select the appropriate defect feedback information.")
            
            params["defect_info"] = defect_info

            # 获取工艺优化记录
            process_optimize = process_optimize_service.get_process_optimization(params.get("process_index_id"))
            del process_optimize["_id"]
            if not process_optimize:
                raise Exception("Process optimize record not exist.")
            if params["opt_nums"] > len(process_optimize["optimize_list"]):
                raise Exception("Invalid opt nums, data no exist.")

            if process_optimize["precondition"]["mold_id"]:
                project = project_service.get_project_obj_by_id(process_optimize["precondition"]["mold_id"])
                if project.subrule_no:
                    params["subrule_no"] = project.subrule_no
                    params["general"] = False
                
            print("*"*30, defect_feedback)
            # 获取优化记录参数
            process_optimize["optimize_list"] = process_optimize["optimize_list"][:params["opt_nums"]]
            feedback_detail = process_optimize["optimize_list"][params["opt_nums"] - 1]["feedback_detail"]
            params["optimize_export"] = copy.deepcopy(feedback_detail["optimize_export"])
            params["optimize_export"]["defect_feedback"] = defect_feedback
            # 获取模具信息
            
            
            # 调用工艺优化算法
            data = process_optimize_service.optimize_process(params)
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
            process_optimize_service.update_process_optimization(process_optimize)

            # 转换成伊之密可识别的opc数据
            conv_spc_data(data, machine_dict, injection_dict)
        elif request_operate == "getProcessList":
            """_summary_
            # 获取工艺参数列表
            """
            data = process_transplant_service.get_process_no_list(
                company_id=yizumi_id, 
                mold_no=req.get("mold_no", None),
                mold_id=req.get("mold_id", None)
            )
        elif request_operate == "getTransferProcess":
            """_summary_
            # 获取一直工艺参数
            """

            # 获取系统中记录的工艺参数
            record_dict = ProcessParameterRecordDoc.objects.filter(process_index_id=req.get("process_id")).first().to_dict()
            
            # 获取原始注塑机信息
            orig_inj = MachineInjector.objects.filter(machine_id=record_dict.get("precondition").get("machine_id")).first()
            orig_inj_dict = orig_inj.to_dict()
            
            # 获取转换注塑机信息
            conv_machine = Machine.objects.filter(company_id=yizumi_id,  serial_no=req.get("mac_serial_no")).first()
            conv_mac_dict = conv_machine.to_dict()
            conv_inj = MachineInjector.objects.filter(machine_id=conv_machine.id).first()
            conv_inj_dict = conv_inj.to_dict()
            req["machine_serial_no"] = req.get("mac_serial_no")
            
            # 原始工艺参数
            process: dict = record_dict.get("process_detail")
            
            # 工艺参数移植
            conv_process_from_database(process, orig_inj_dict, conv_inj_dict)
            data = conv_simple_format(process)
            
            # 转换成伊之密可识别的opc数据
            conv_spc_data(data, conv_mac_dict, conv_inj_dict)


        elif request_operate == "getDefectTypeList":
            """_summary_
            # 获取缺陷类型
            """
            data = {
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
        res = {
            "status": 0,
            "timestamp": req.get("timestamp",datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "machine_serial_no": req.get("machine_serial_no"),
            "operate": request_operate,
            "data": data
        }
        json_data = json.dumps(res, ensure_ascii=False)
        json_data = json_data.replace('\t','').replace('\\n','').replace('\\r','').replace('\n','').replace('\r','').replace("'", '"')
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + json_data)

        if msg.topic == sub_topic:
            if req.get("machine_serial_no"):
                machine_serial_no = req.get("machine_serial_no")
                topic = f"{pub_topic}-{machine_serial_no}"
                client.publish(topic, json_data.encode('utf-8'))
            else:
                client.publish(pub_topic, json_data.encode('utf-8'))

    except Exception as e:
        logging.exception("mqtt service exception")
        trace_detail  = traceback.format_exc()
        print("mqtt service exception：", trace_detail)
        res = {
            "error": f'{trace_detail}'
        }
        json_data = json.dumps(res, ensure_ascii=False)
        try:
            if req.get("machine_serial_no"):
                machine_serial_no = req.get("machine_serial_no")
                topic = f"{pub_topic}-{machine_serial_no}"
                client.publish(topic, json_data.encode('utf-8'))
            else:
                client.publish(pub_topic, json_data.encode('utf-8'))
        except Exception as e:
            print(e)


def start_mqtt_service():
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        
        from django.conf import settings
        print("start mqtt service")
        # client.connect("47.96.83.203", 1883, 60)
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(e)


def start_mqtt_service_thread():
    mqtt_thread = threading.Thread(target=start_mqtt_service)
    mqtt_thread.daemon = True
    mqtt_thread.start()
