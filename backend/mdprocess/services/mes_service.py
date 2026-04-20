import requests
import json
import logging
from hsmolding.services.machine_service import get_machine
from mdprocess.services import process_optimize_service
from mdprocess.utils.unit_convert import unit_conversion
from gis.common.django_ext.outer_request import request_post
from gis.common.django_ext.json import JsonEncoder
from django.conf import settings
from mdprocess.const import PROCESS


TRANSFER_PRESSURE_UNIT = "MPa"
TRANSFER_BACK_PRESSURE_UNIT = "MPa"
TRANSFER_TIME_UNIT = "s"
TRANSFER_POSITION_UNIT = "cm³"
TRANSFER_VELOCITY_UNIT = "cm³/s"
TRANSFER_ROTATION_UNIT = "cm/s"
TRANSFER_DE_VELOCITY_UNIT = "cm³/s"  # 松退速度
TRANSFER_OC_PRESSURE_UNIT = "MPa"  # 开合模和顶进顶退
TRANSFER_OC_VELOCITY_UNIT = "mm/s"
TRANSFER_OC_POSITION_UNIT = "mm"
TRANSFER_TEMP_UNIT = "℃"

machine_info = None  # dict


def getProcessTech(machine_id=None, internal_id=None, token=None):
    global machine_info
    machine_info = get_machine(machine_id)
    # return getProcessTechOne(token=token)
    # return getProcessTechTwo(token=token)
    # return getProcessTechThree(token=token)
    # return getProcessTechFour(token=token)
    # return getProcessTechFive(token=token)
    # 如果通讯接口选择开通,则通过统一MES读取和下发
    if machine_info.get("communication_interface"):
        return getProcessTechMES()
    # 如果通讯接口选择未开通,则通过原始协议读取和下发
    if machine_info.get("agreement") == "keba1175":
        return getProcessTechSix()
    if machine_info.get("agreement") == "keba映翰通":
        return getProcessTechSeven()
    if machine_info.get("agreement") == "盟立":
        return getProcessTechEight()


def setProcessTech(process_detail=None, precondition=None):
    global machine_info
    machine_info = get_machine(precondition.get("machine_id"))
    # 如果通讯接口选择开通,则通过统一MES读取和下发
    if machine_info.get("communication_interface"):
        return setProcessTechMES(process_detail=process_detail, precondition=precondition)
    # 如果通讯接口选择未开通,则通过原始协议读取和下发
    if machine_info.get("agreement") == "keba1175":
        return setProcessTechSix(process_detail=process_detail, precondition=precondition)
    if machine_info.get("agreement") == "keba映翰通":
        return setProcessTechSeven(process_detail=process_detail, precondition=precondition)   
    if machine_info.get("agreement") == "盟立":
        return setProcessTechEight(process_detail=process_detail, precondition=precondition)


# 统一接口
def getProcessTechMES():
    global machine_info

    try:
        token = loginYuzimi()
        url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=1&type=1"
        # url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn=FF160Z0127&tag=1&type=1"
        # url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn=S0120L0005&tag=1&type=1"
        # url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn=GL5022219000151&tag=1&type=1"
        header_dict = {"Authorization": token}

        res_data = None
        resp = requests.get(url, headers=header_dict)
        if resp.status_code == 200:
            res = json.loads(resp.text)
            if res.get("code") == 200 and res.get("msg") == "success":
                res_data = res.get("data")
        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        pressure_unit = machine_info.get("pressure_unit")
        velocity_unit = machine_info.get("velocity_unit")
        position_unit = machine_info.get("position_unit")
        time_unit = machine_info.get("time_unit")
        rotation_unit = machine_info.get("screw_rotation_unit")
        backpressure_unit = machine_info.get("backpressure_unit")
        temp_unit = machine_info.get("temperature_unit")
        for i in range(int(res_data.get("inj_points"))):
            injection_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("inj_press_"+str(i)), convert_type="injection_pressure_read") if res_data.get("inj_press_"+str(i)) else None)
            injection_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get("inj_speed_"+str(i)), convert_type="injection") if res_data.get("inj_speed_"+str(i)) else None)
            injection_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("inj_pos_"+str(i))) if res_data.get("inj_pos_"+str(i)) else None)

        inject_para = {
            "injection_stage": res_data.get("inj_points"),
            "max_injection_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            "cooling_time": res_data.get("cooling_time"),
            "injection_delay_time":res_data.get("inj_delay"),
            "injection_time":round(float(res_data.get("inj_time")), 2) if res_data.get("inj_time") else None
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(int(res_data.get("pack_points"))):
            holding_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("pack_press_"+str(i)), convert_type="holding_pressure_read") if res_data.get("pack_press_"+str(i)) else None)
            holding_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get("pack_speed_"+str(i)), convert_type="holding") if res_data.get("pack_speed_"+str(i)) else None)
            holding_time_sections.append(res_data.get(
                "pack_time_"+str(i)) if res_data.get("pack_time_"+str(i)) else None)

        holding_para = {
            "holding_stage": res_data.get("pack_points"),
            "max_holding_stage_option": 5,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        VP_switch["VP_switch_mode"] = "位置"
        VP_switch["VP_switch_position"] = getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("vps_str")) if res_data.get("vps_str") else None
        VP_switch["VP_switch_time"] = round(float(res_data.get("vps_time")), 2) if res_data.get("vps_time") else None
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []

        for i in range(int(res_data.get("plst_points"))):
            metering_rotation_sections.append(
                getConversion(TRANSFER_ROTATION_UNIT, rotation_unit, res_data.get("plst_speed_"+str(i))) if res_data.get("plst_speed_"+str(i)) else None)
            metering_back_pressure_sections.append(
                getConversion(TRANSFER_BACK_PRESSURE_UNIT, backpressure_unit, res_data.get("plst_bp_"+str(i))) if res_data.get("plst_bp_"+str(i)) else None)
            metering_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("plst_pos_"+str(i))) if res_data.get("plst_pos_"+str(i)) else None)

        metering_para = {
            "metering_stage": res_data.get("plst_points"),
            "max_metering_stage_option": 4,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("backpressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    # "pressure":  getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("186")) if res_data.get("186") else None,
                    "velocity": getConversion(TRANSFER_DE_VELOCITY_UNIT, velocity_unit, res_data.get("sb1_speed")) if res_data.get("sb1_speed") else None,
                    # "time": res_data.get("189") if res_data.get("189") and float(res_data.get("189")) != 0 else None,
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("sb1_str")) if res_data.get("sb1_str") else None
                },
                {
                    "label": "储后",
                    # "pressure": getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("190")) if res_data.get("190") else None,
                    "velocity": getConversion(TRANSFER_DE_VELOCITY_UNIT, velocity_unit, res_data.get("sb2_speed")) if res_data.get("sb2_speed") else None,
                    # "time": res_data.get("193") if res_data.get("193") and float(res_data.get("193")) != 0 else None,
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("sb2_str") if res_data.get("sb2_str") else None)
                }
            ],
            "decompressure_mode_before_metering": "否",
            "decompressure_mode_after_metering": "距离",
            "metering_ending_position": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("screw_pos")) if res_data.get("screw_pos") else None,
            "metering_delay_time": getConversion(TRANSFER_TIME_UNIT, time_unit, res_data.get("plst_delay")) if res_data.get("plst_delay") else None
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        for i in range(int(res_data.get("fb_points"))):
            temp_sections.append(
                getConversion(TRANSFER_TEMP_UNIT, temp_unit, res_data.get("fb_sp_"+str(i))))
        temp_para = {
            "barrel_temperature_stage": res_data.get("fb_points"),
            "max_barrel_temperature_stage_option": 10,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para
        process_detail = getProcessTechSixMES(process_detail, res_data, machine_info.get("agreement"))
        process_detail = getProcessTechSixEjectorMES(process_detail, res_data, machine_info.get("agreement"))
        mold_no = res_data.get("CurrentMoldNo")
        product_no = res_data.get("CurrentProduct")

        return {"process_detail":process_detail, "mold_no":mold_no,"product_no":product_no}
    except Exception as e:
        logging.error(e)
        logging.error(e.__traceback__)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


# 开合模统一接口
def getProcessTechSixMES(process_detail, res_data, agreement):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        if agreement == "盟立":
            TRANSFER_OC_PRESSURE_UNIT = "bar"  # 开合模和顶进顶退
            TRANSFER_OC_VELOCITY_UNIT = "mm/s"
            TRANSFER_OC_POSITION_UNIT = "mm"
        open_pressure_sections = []
        open_velocity_sections = []
        open_position_sections = []
        clamp_pressure_sections = []
        clamp_velocity_sections = []
        clamp_position_sections = []
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")
        open_stage = 5
        if agreement in ["keba映翰通", "keba1175"]:
            open_stage = int(res_data.get("open_points"))
        elif agreement in ["盟立"]:
            open_stage = 5
        for i in range(open_stage):
            if agreement in ["keba1175", "盟立"]:
                open_pressure_sections.append(
                    getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get("op_press_"+str(i)), convert_type="origin_press") if res_data.get("op_press_"+str(i)) else None)
            open_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get("op_speed_"+str(i)), convert_type="opening") if res_data.get("op_speed_"+str(i)) else None)
            open_position_sections.append(
                res_data.get("op_pos_"+str(i)))
        # keba映翰通,合模段数5段,模保单独赋值,前面减1
        clamp_stage = 5
        if agreement in ["keba1175"]:
            clamp_stage = int(res_data.get("clamp_points"))
        if agreement in ["keba映翰通"]:
            clamp_stage = int(res_data.get("clamp_points"))-1
        elif agreement in ["盟立"]:
            clamp_stage = 5
        for i in range(clamp_stage):
            if agreement in ["keba1175","盟立"]:
                clamp_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get("cl_press_"+str(i)), convert_type="origin_press") if res_data.get("cl_press_"+str(i)) else None)
            clamp_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get("cl_speed_"+str(i)), convert_type="clamping") if res_data.get("cl_speed_"+str(i)) else None)
   
            clamp_position_sections.append(
                res_data.get("cl_pos_"+str(i)))
        # 模保
        if agreement == "keba映翰通":
            clamp_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get("pro_speed"), convert_type="clamping") if res_data.get("pro_speed") else None)
            clamp_position_sections.append(res_data.get("pro_pos"))

        mold_opening = {
            "mold_opening_stage": open_stage,
            "max_mold_opening_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": open_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": open_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": open_position_sections}
            ],
        }
        mold_clamping = {
            "mold_clamping_stage": clamp_stage +1 if agreement in ["keba映翰通"] else clamp_stage,
            "max_mold_clamping_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": clamp_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": clamp_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": clamp_position_sections}
            ],
        }
        opening_and_clamping_mold_setting = {
            "mold_opening": mold_opening,
            "mold_clamping": mold_clamping,
        }
        process_detail["opening_and_clamping_mold_setting"] = opening_and_clamping_mold_setting
        return process_detail
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


# 顶针统一接口
def getProcessTechSixEjectorMES(process_detail, res_data, agreement):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        ejector_forward_pressure_sections = []
        ejector_forward_velocity_sections = []
        ejector_forward_position_sections = []
        ejector_backward_pressure_sections = []
        ejector_backward_velocity_sections = []
        ejector_backward_position_sections = []
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")
        # position_unit = machine_info.get("oc_position_unit")
        for i in range(int(res_data.get("forward_points"))):
            ejector_forward_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get("fw_press_"+str(i)), convert_type="origin_press") if res_data.get("fw_press_"+str(i)) else None)
            # keba映翰通没有顶进最大速度,暂时用顶退最大速度代替.如果从注塑机上查到,录入数据库,可以直接读取数据库中的参数
            ejector_forward_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get("fw_speed_"+str(i)),convert_type="forward") if res_data.get("fw_speed_"+str(i)) else None)
            ejector_forward_position_sections.append(
                res_data.get("fw_pos_"+str(i)))

        for i in range(int(res_data.get("backward_points"))):
            ejector_backward_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get("bk_press_"+str(i)), convert_type="origin_press") if res_data.get("bk_press_"+str(i)) else None)
            ejector_backward_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get("bk_speed_"+str(i)),convert_type="backward") if res_data.get("bk_speed_"+str(i)) else None)
            ejector_backward_position_sections.append(
                res_data.get("bk_pos_"+str(i)))

        ejector_forward = {
            "ejector_forward_stage": res_data.get("forward_points"),
            "max_ejector_forward_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": ejector_forward_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": ejector_forward_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": ejector_forward_position_sections}
            ],
        }
        ejector_backward = {
            "ejector_backward_stage": res_data.get("backward_points"),
            "max_ejector_backward_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": ejector_backward_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": ejector_backward_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": ejector_backward_position_sections}
            ],
        }
        ejector_setting = {
            "ejector_forward": ejector_forward,
            "ejector_backward": ejector_backward,
        }
        process_detail["ejector_setting"] = ejector_setting
        return process_detail
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


# 统一接口
def setProcessTechMES(process_detail=None, precondition=None):
    try:
        global machine_info

        pressure_unit = process_detail.get(
            "inject_para").get("table_data")[0].get("unit")
        velocity_unit = process_detail.get(
            "inject_para").get("table_data")[1].get("unit")
        position_unit = process_detail.get(
            "inject_para").get("table_data")[2].get("unit")
        time_unit = process_detail.get("holding_para").get(
            "table_data")[2].get("unit")
        rotation_unit = process_detail.get(
            "metering_para").get("table_data")[1].get("unit")
        backpressure_unit = process_detail.get(
            "metering_para").get("table_data")[2].get("unit")
        temp_unit = process_detail.get("temp_para").get("table_data")[0].get("unit")
        # 温度段数不需要发,是默认的.
        temp = process_detail.get("temp_para").get("table_data")[0].get("sections")
        metering = process_detail.get("metering_para").get("table_data")
        holding = process_detail.get("holding_para").get("table_data")
        injection = process_detail.get("inject_para").get("table_data")
        process_dict = dict({                
            "fb_sp_0": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[0]) if len(temp) >=1 and temp[0] else None,  # 料筒温度1段实际值
            "fb_sp_1": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[1]) if len(temp) >=2 and temp[1] else None,  # 料筒温度2段实际值
            "fb_sp_2": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[2]) if len(temp) >=3 and temp[2] else None,  # 料筒温度3段实际值
            "fb_sp_3": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[3]) if len(temp) >=4 and temp[3] else None,  # 料筒温度4段实际值
            "fb_sp_4": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[4]) if len(temp) >=5 and temp[4] else None,  # 料筒温度5段实际值
			"fb_sp_5": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[5]) if len(temp) >=6 and temp[5] else None,  # 料筒温度6段实际值
			"fb_sp_6": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[6]) if len(temp) >=7 and temp[6] else None,  # 料筒温度7段实际值
            "plst_points": process_detail.get("metering_para").get("metering_stage"),  # 熔胶段数
            "plst_speed_0": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[0]) if len(metering)>=1 and len(metering[1].get("sections")) >=1 and metering[1].get("sections")[0] else None,  # 储料一段速度
            "plst_speed_1": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[1]) if len(metering)>=1 and len(metering[1].get("sections")) >=2 and metering[1].get("sections")[1] else None,  # 储料二段速度
            "plst_speed_2": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[2]) if len(metering)>=1 and len(metering[1].get("sections")) >=3 and metering[1].get("sections")[2] else None,  # 储料三段速度
            "plst_speed_3": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[3]) if len(metering)>=1 and len(metering[1].get("sections")) >=4 and metering[1].get("sections")[3] else None,  # 储料四段速度
            "plst_bp_0": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[0],convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=1 and metering[2].get("sections")[0] else None,  # 储料一段背压
            "plst_bp_1": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[1],convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=2 and metering[2].get("sections")[1] else None,  # 储料二段背压
            "plst_bp_2": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[2],convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=3 and metering[2].get("sections")[2] else None,  # 储料三段背压
            "plst_bp_3": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[3],convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=4 and metering[2].get("sections")[3] else None,  # 储料四段背压
            "plst_pos_0": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[0]) if len(metering)>=3 and len(metering[1].get("sections")) >=1 and metering[3].get("sections")[0] else None,  # 储料一段位置
            "plst_pos_1": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[1]) if len(metering)>=3 and len(metering[1].get("sections")) >=2 and metering[3].get("sections")[1] else None,  # 储料二段位置
            "plst_pos_2": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[2]) if len(metering)>=3 and len(metering[1].get("sections")) >=3 and metering[3].get("sections")[2] else None,  # 储料三段位置
            "plst_pos_3": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[3]) if len(metering)>=3 and len(metering[1].get("sections")) >=4 and metering[3].get("sections")[3] else None,  # 储料四段位置
            # "186": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure")) if process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure") else None,  # 熔胶前松退压力
            "sb1_speed": get_decompression_velocity(process_detail, 0, velocity_unit),  # 熔胶前松退速度
            "sb1_str": getConversion(position_unit, TRANSFER_POSITION_UNIT, decompression_params[0].get("distance")) if (decompression_params := process_detail.get("metering_para", {}).get("decompressure_paras", [])) and len(decompression_params) > 0 and "distance" in decompression_params[0] else None,  # 熔胶前松退位置
            # "189": process_detail.get("metering_para").get("decompressure_paras")[0].get("time"),  # 熔胶前松退时间
            # "190": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure")) if process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure") else None,  # 熔胶后松退压力
            "sb2_speed": get_decompression_velocity(process_detail, 1, velocity_unit),  # 熔胶后松退速度
            "sb2_str": getConversion(position_unit, TRANSFER_POSITION_UNIT, decompression_params[1].get("distance")) if (decompression_params := process_detail.get("metering_para", {}).get("decompressure_paras", [])) and len(decompression_params) > 1 and "distance" in decompression_params[1] else None,  # 熔胶后松退位置
            # "193": process_detail.get("metering_para").get("decompressure_paras")[1].get("time"),  # 熔胶后松退时间
            "pack_points": process_detail.get("holding_para").get("holding_stage"),  # 保压段数
            "pack_press_0": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[0], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 1 and holding[0].get("sections")[0] else None,  # 保压一段压力
            "pack_press_1": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[1], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 2 and holding[0].get("sections")[1] else None,  # 保压二段压力
            "pack_press_2": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[2], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 3 and holding[0].get("sections")[2] else None,  # 保压三段压力
            "pack_press_3": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[3], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 4 and holding[0].get("sections")[3] else None,  # 保压四段压力
            "pack_press_4": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[4], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 5 and holding[0].get("sections")[4] else None,  # 保压五段压力
            "pack_press_5": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[5], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 6 and holding[0].get("sections")[5] else None,  # 保压六段压力
            "pack_press_6": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[6], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 7 and holding[0].get("sections")[6] else None,  # 保压七段压力
            "pack_press_7": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[7], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 8 and holding[0].get("sections")[7] else None,  # 保压八段压力
            "pack_press_8": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[8], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 9 and holding[0].get("sections")[8] else None,  # 保压九段压力
            "pack_press_9": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[9], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 10 and holding[0].get("sections")[9] else None,  # 保压十段压力
            "pack_speed_0": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[0], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 1 and holding[1].get("sections")[0] else None,  # 保压一段速度
            "pack_speed_1": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[1], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 2 and holding[1].get("sections")[1] else None,  # 保压二段速度
            "pack_speed_2": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[2], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 3 and holding[1].get("sections")[2] else None,  # 保压三段速度
            "pack_speed_3": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[3], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 4 and holding[1].get("sections")[3] else None,  # 保压四段速度
            "pack_speed_4": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[4], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 5 and holding[1].get("sections")[4] else None,  # 保压五段速度
            "pack_speed_5": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[5], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 6 and holding[1].get("sections")[5] else None,  # 保压六段速度
            "pack_speed_6": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[6], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 7 and holding[1].get("sections")[6] else None,  # 保压七段速度
            "pack_speed_7": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[7], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 8 and holding[1].get("sections")[7] else None,  # 保压八段速度
            "pack_speed_8": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[8], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 9 and holding[1].get("sections")[8] else None,  # 保压九段速度
            "pack_speed_9": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[9], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 10 and holding[1].get("sections")[9]	else None,  # 保压十段速度
            "pack_time_0": holding[2].get("sections")[0] if len(holding) >= 3 and len(holding[0].get("sections")) >= 1 else None,  # 保压一段时间
            "pack_time_1": holding[2].get("sections")[1] if len(holding) >= 3 and len(holding[0].get("sections")) >= 2 else None,  # 保压二段时间
            "pack_time_2": holding[2].get("sections")[2] if len(holding) >= 3 and len(holding[0].get("sections")) >= 3 else None,  # 保压三段时间
			"pack_time_3": holding[2].get("sections")[3] if len(holding) >= 3 and len(holding[0].get("sections")) >= 4 else None,  # 保压四段时间
            "pack_time_4": holding[2].get("sections")[4] if len(holding) >= 3 and len(holding[0].get("sections")) >= 5 else None,  # 保压五段时间
            "pack_time_5": holding[2].get("sections")[5] if len(holding) >= 3 and len(holding[0].get("sections")) >= 6 else None,  # 保压六段时间
            "pack_time_6": holding[2].get("sections")[6] if len(holding) >= 3 and len(holding[0].get("sections")) >= 7 else None,  # 保压七段时间
			"pack_time_7": holding[2].get("sections")[7] if len(holding) >= 3 and len(holding[0].get("sections")) >= 8 else None,  # 保压八段时间
            "pack_time_8": holding[2].get("sections")[8] if len(holding) >= 3 and len(holding[0].get("sections")) >= 9 else None,  # 保压九段时间
            "pack_time_9": holding[2].get("sections")[9] if len(holding) >= 3 and len(holding[0].get("sections")) >= 10 else None,  # 保压十段时间
            "inj_points": process_detail.get("inject_para").get("injection_stage"),  # 注射段数
            "inj_pos_0": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[0]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 1 and injection[2].get("sections")[0] else None,  # 注射一段位置
            "inj_pos_1": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[1]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 2 and injection[2].get("sections")[1] else None,  # 注射二段位置
            "inj_pos_2": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[2]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 3 and injection[2].get("sections")[2] else None,  # 注射三段位置
            "inj_pos_3": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[3]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 4 and injection[2].get("sections")[3] else None,  # 注射四段位置
            "inj_pos_4": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[4]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 5 and injection[2].get("sections")[4] else None,  # 注射五段位置
            "inj_pos_5": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[5]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 6 and injection[2].get("sections")[5] else None,  # 注射六段位置
            "inj_pos_6": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[6]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 7 and injection[2].get("sections")[6] else None,  # 注射七段位置
            "inj_pos_7": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[7]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 8 and injection[2].get("sections")[7] else None,  # 注射八段位置
            "inj_pos_8": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[8]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 9 and injection[2].get("sections")[8] else None,  # 注射九段位置
            "inj_pos_9": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[9]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 10 and injection[2].get("sections")[9] else None,  # 注射十段位置
            "inj_press_0": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[0], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 1 and injection[0].get("sections")[0] else None,  # 注射一段压力
            "inj_press_1": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[1], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 2 and injection[0].get("sections")[1] else None,  # 注射二段压力
            "inj_press_2": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[2], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 3 and injection[0].get("sections")[2] else None,  # 注射三段压力
            "inj_press_3": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[3], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 4 and injection[0].get("sections")[3] else None,  # 注射四段压力
            "inj_press_4": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[4], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 5 and injection[0].get("sections")[4] else None,  # 注射五段压力
            "inj_press_5": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[5], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 6 and injection[0].get("sections")[5] else None,  # 注射六段压力
            "inj_press_6": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[6], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 7 and injection[0].get("sections")[6] else None,  # 注射七段压力
            "inj_press_7": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[7], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 8 and injection[0].get("sections")[7] else None,  # 注射八段压力
            "inj_press_8": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[8], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 9 and injection[0].get("sections")[8] else None,  # 注射九段压力
            "inj_press_9": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[9], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 10 and injection[0].get("sections")[9] else None,  # 注射十段压力
            "inj_speed_0": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[0], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 1 and injection[1].get("sections")[0] else None,  # 注射一段速度
            "inj_speed_1": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[1], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 2 and injection[1].get("sections")[1] else None,  # 注射二段速度
            "inj_speed_2": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[2], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 3 and injection[1].get("sections")[2] else None,  # 注射三段速度
            "inj_speed_3": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[3], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 4 and injection[1].get("sections")[3] else None,  # 注射四段速度
            "inj_speed_4": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[4], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 5 and injection[1].get("sections")[4] else None,  # 注射五段速度
            "inj_speed_5": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[5], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 6 and injection[1].get("sections")[5] else None,  # 注射六段速度
            "inj_speed_6": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[6], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 7 and injection[1].get("sections")[6] else None,  # 注射七段速度
            "inj_speed_7": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[7], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 8 and injection[1].get("sections")[7] else None,  # 注射八段速度
            "inj_speed_8": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[8], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 9 and injection[1].get("sections")[8] else None,  # 注射九段速度
            "inj_speed_9": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[9], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 10 and injection[1].get("sections")[9] else None,  # 注射十段速度	
            "cooling_time": process_detail.get("inject_para").get("cooling_time"),
            "injection_delay_time": process_detail.get("inject_para").get("injection_delay_time"),
            "injection_time": process_detail.get("inject_para").get("injection_time"),
            "vps_str": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("VP_switch").get("VP_switch_position")) if process_detail.get("VP_switch").get("VP_switch_position") else None,  # 保压切换位置
            "vps_time": process_detail.get("VP_switch").get("VP_switch_time"),
            "screw_pos": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("metering_ending_position")) if process_detail.get("metering_para").get("metering_ending_position") else None,
            "plst_delay": process_detail.get("metering_para").get("metering_delay_time"),
        })

        # 下发开合模,顶进顶退
        if(precondition.get("data_sources") != "工艺优化"):
            process_dict = setProcessTechSixPart(process_detail, machine_info.get("agreement"), process_dict)
            process_dict = setProcessTechSixEjector(process_detail, machine_info.get("agreement"), process_dict)
        new_process = {}
        # 下发之前,去掉空值
        for key in process_dict:
            if process_dict.get(key) not in (None, ""):
                new_process[key] = process_dict.get(key)
        logging.info(f"下发之前,检查参数是否正确{new_process}")
        json_data = json.dumps(new_process)
        url = settings.MES+"/api/custom/equipment/craft/data/input/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=2&type=1"
        token = loginYuzimi()
        header_dict = {"Content-Type": "application/json; charset=UTF-8"}
        header_dict["Authorization"] = token
        res = None
        resp = requests.post(url, data=json_data, headers=header_dict)
        if resp.status_code == 200:
            res = json.loads(resp.text)
        if res and res.get("msg") == "会话已过期,请重新登录":
            return dict(result="outdated")
        else:
            return dict(result="success")
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


# 开合模 统一接口
def setProcessTechSixMES(process_detail, agreement, process_dict):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        if agreement == "盟立":
            TRANSFER_OC_PRESSURE_UNIT = "bar"  # 开合模和顶进顶退
            TRANSFER_OC_VELOCITY_UNIT = "mm/s"
            TRANSFER_OC_POSITION_UNIT = "mm"
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")
        mold_opening = process_detail.get("opening_and_clamping_mold_setting").get("mold_opening").get("table_data")
        mold_clamping = process_detail.get("opening_and_clamping_mold_setting").get("mold_clamping").get("table_data")
        for i in range(min(6,process_detail.get("opening_and_clamping_mold_setting").get("mold_opening").get("mold_opening_stage"))):
            process_dict["op_speed_"+str(i)] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, mold_opening[1].get("sections")[i], convert_type="opening") if len(mold_opening) >=2 and len(mold_opening[1].get("sections"))>i else None
            process_dict["op_pos_"+str(i)] = mold_opening[2].get("sections")[i] if len(mold_opening) >=3 and len(mold_opening[2].get("sections"))>i else None
        # keba映翰通,模保在合模段数中.
        clamping_stage = min(6,process_detail.get("opening_and_clamping_mold_setting").get("mold_clamping").get("mold_clamping_stage"))
        for i in range(clamping_stage-1):
            process_dict["cl_speed_"+str(i)] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, mold_clamping[1].get("sections")[i], convert_type="clamping") if len(mold_clamping) >=2 and len(mold_clamping[1].get("sections"))>i else None
            process_dict["cl_pos_"+str(i)] = mold_clamping[2].get("sections")[i] if len(mold_clamping) >=3 and len(mold_clamping[2].get("sections"))>i else None
        # 模保
        if agreement == "keba映翰通":
            process_dict["pro_speed"] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, mold_clamping[1].get("sections")[clamping_stage-1], convert_type="clamping") if len(mold_clamping) >=2 and len(mold_clamping[1].get("sections"))>clamping_stage-1 else None
            process_dict["pro_pos"] = mold_clamping[2].get("sections")[clamping_stage-1] if len(mold_clamping) >=3 and len(mold_clamping[2].get("sections"))>clamping_stage-1 else None
        if agreement != "盟立":
            process_dict["clamp_points"] = clamping_stage
            process_dict["open_points"] = min(6,process_detail.get("opening_and_clamping_mold_setting").get("mold_opening").get("mold_opening_stage"))
        return process_dict
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


# 顶针 统一接口
def setProcessTechSixEjectorMES(process_detail, agreement, process_dict):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        if agreement == "盟立":
            TRANSFER_OC_PRESSURE_UNIT = "bar"  # 开合模和顶进顶退
            TRANSFER_OC_VELOCITY_UNIT = "mm/s"
            TRANSFER_OC_POSITION_UNIT = "mm"
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")        
        ejector_forward = process_detail.get("ejector_setting").get("ejector_forward").get("table_data")
        ejector_backward = process_detail.get("ejector_setting").get("ejector_backward").get("table_data")
        for i in range(min(3,process_detail.get("ejector_setting").get("ejector_forward").get("ejector_forward_stage"))):
            process_dict["fw_press_"+str(i)] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, ejector_forward[0].get("sections")[i],convert_type="origin_press") if len(ejector_forward) >=1 and len(ejector_forward[0].get("sections"))>=i else None

            process_dict["fw_speed_"+str(i)] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, ejector_forward[1].get("sections")[i], convert_type="forward") if len(ejector_forward) >=2 and len(ejector_forward[1].get("sections"))>=i else None
            process_dict["fw_pos_"+str(i)] = ejector_forward[2].get("sections")[i] if len(ejector_forward) >=3 and len(ejector_forward[2].get("sections"))>=i else None
        for i in range(min(3,process_detail.get("ejector_setting").get("ejector_backward").get("ejector_backward_stage"))):
            process_dict["bk_press_"+str(i)] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, ejector_backward[0].get("sections")[i],convert_type="origin_press") if len(ejector_backward) >=1 and len(ejector_backward[0].get("sections"))>=i else None
            
            process_dict["bk_speed_"+str(i)] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, ejector_backward[1].get("sections")[i], convert_type="backward") if len(ejector_backward) >=2 and len(ejector_backward[1].get("sections"))>=i else None
            process_dict["bk_pos_"+str(i)] = ejector_backward[2].get("sections")[i] if len(ejector_backward) >=3 and len(ejector_backward[2].get("sections"))>=i else None
        process_dict["forward_points"] = min(3,process_detail.get("ejector_setting").get("ejector_forward").get("ejector_forward_stage"))
        process_dict["backward_points"] = min(3,process_detail.get("ejector_setting").get("ejector_backward").get("ejector_backward_stage"))
        return process_dict
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


def getConversion(original_unit, converted_unit, original_value, convert_type=None):
    try:
        if original_value in ["-1000.0"]:
            return None
        elif original_value in ["0.0", 0.0, 0]:
            return 0 
        elif original_unit == converted_unit:
            return round(float(original_value), 2) if original_value else None
        elif original_unit and converted_unit and original_value and original_value not in ["0.0",0,"-1000",-1000] and machine_info and machine_info.get("injectors_info"):
            if machine_info:
                injector_info = machine_info.get("injectors_info")
                if isinstance(injector_info, list) and len(injector_info) > 0:
                    injector = injector_info[0]
                    converted_value = unit_conversion.conversion(original_unit, converted_unit, float(original_value), injector, convert_type=convert_type)
                    print(f"转换前{original_unit}  转换后{converted_unit} 转换前{original_value}  转换后{converted_value}")
                    return converted_value
    except Exception as e:
        logging.error(f"{e} 行号{e.__traceback__.tb_lineno}")


# 二板机三板机KEBA+OPCUA1.0.xlsx
def getProcessTechOne(token=None):
    try:
        token = "063cd032-4bba-4c7e-9d97-85a04e8f06e1"
        url = "http://kunpeng.yizumi.com:82/api/web/equipment/getSingleMonitorData?equipmentId=9006"

        header_dict = {"Authorization": token}

        res = None
        resp = requests.get(url, headers=header_dict)
        logging.info(f"返回值是多少{resp}")
        if resp.status_code == 200:
            res = json.loads(resp.text)
        res_data = dict({

            "82": 1,  # 料筒温度1段实际值
            "83": 1,  # 料筒温度2段实际值
            "84": 1,  # 料筒温度3段实际值
            "85": 1,  # 料筒温度4段实际值
            "86": 1,  # 料筒温度5段实际值
            "87": 1,  # 料筒温度6段实际值
            "88": 1,  # 料筒温度7段实际值

            "66": 1,  # 储料一段压力
            "63": 1,  # 储料一段速度
            "64": 1,  # 储料二段速度
            "65": 1,  # 储料三段速度
            "60": 1,  # 储料一段背压
            "61": 1,  # 储料二段背压
            "62": 1,  # 储料三段背压
            "57": 1,  # 储料一段位置
            "58": 1,  # 储料二段位置
            "59": 1,  # 储料三段位置

            "67": 1,  # 溶胶前松退压力
            "68": 1,  # 溶胶前松退速度
            "69": 1,  # 溶胶前松退位置
            "70": 1,  # 溶胶前松退时间
            "71": 1,  # 溶胶后松退压力
            "72": 1,  # 溶胶后松退速度
            "73": 1,  # 溶胶后松退位置
            "74": 1,  # 溶胶后松退时间

            "48": 1,  # 保压一段压力
            "49": 1,  # 保压二段压力
            "50": 1,  # 保压三段压力
            "51": 1,  # 保压一段速度
            "52": 1,  # 保压二段速度
            "53": 1,  # 保压三段速度
            "54": 1,  # 保压一段时间
            "55": 1,  # 保压二段时间
            "56": 1,  # 保压三段时间

            "30": 1,  # 注射一段位置
            "31": 1,  # 注射二段位置
            "32": 1,  # 注射三段位置
            "33": 1,  # 注射四段位置
            "34": 1,  # 注射五段位置
            "35": 1,  # 注射六段位置
            "36": 1,  # 注射一段压力
            "37": 1,  # 注射二段压力
            "38": 1,  # 注射三段压力
            "39": 1,  # 注射四段压力
            "40": 1,  # 注射五段压力
            "41": 1,  # 注射六段压力
            "42": 1,  # 注射一段速度
            "43": 1,  # 注射二段速度
            "44": 1,  # 注射三段速度
            "45": 1,  # 注射四段速度
            "46": 1,  # 注射五段速度
            "47": 1  # 注射六段速度
        })
        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        for i in range(6):
            injection_pressure_sections.append(
                res_data.get(str(36+i)))
            injection_velocity_sections.append(
                res_data.get(str(42+i)))
            injection_distance_sections.append(
                res_data.get(str(30+i)))

        inject_para = {
            "injection_stage": 6,
            "max_injection_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            "cooling_time": res_data.get("cooling_time")
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(3):
            holding_pressure_sections.append(
                res_data.get(str(48+i)))
            holding_velocity_sections.append(
                res_data.get(str(51+i)))
            holding_time_sections.append(res_data.get(str(54+i)))

        holding_para = {
            "holding_stage": 3,
            "max_holding_stage_option": 5,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("vps_by_str_enbl"):
            VP_switch["VP_switch_mode"] = "位置"
            VP_switch["VP_switch_position"] = res_data.get("97")
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []
        for i in range(3):
            metering_rotation_sections.append(
                res_data.get(str(63+i)))
            metering_back_pressure_sections.append(
                res_data.get(str(60+i)))
            metering_distance_sections.append(
                res_data.get(str(57+i)))
        metering_pressure_sections.append(
            res_data.get("66"))

        metering_para = {
            "metering_stage": 3,
            "max_metering_stage_option": 3,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("pressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    "pressure": res_data.get("67"),
                    "velocity": res_data.get("68"),
                    "time": res_data.get("70"),
                    "distance": res_data.get("69")
                },
                {
                    "label": "储后",
                    "pressure": res_data.get("71"),
                    "velocity": res_data.get("72"),
                    "time": res_data.get("74"),
                    "distance": res_data.get("73")
                }
            ]
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        for i in range(7):
            temp_sections.append(
                res_data.get(str(82+i)))
        temp_para = {
            "barrel_temperature_stage": 7,
            "max_barrel_temperature_stage_option": 7,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para

        return process_detail
    except Exception as e:
        logging.error(e)
        return dict(result="failed")


#  二板机三板机KEBA+OPCUA1.1.xlsx
def getProcessTechTwo(machine_id=None, internal_id=None, token=None):
    try:
        # url = "http://kunpeng.yizumi.com:82/api/web/equipment/getSingleMonitorData?equipmentId=9006"

        # header_dict = {"Authorization": token}

        # res = None
        # resp = requests.get(url, headers=header_dict)
        # if resp.status_code == 200:
        #     res = json.loads(resp.text)
        res_data = dict({
            "194": 7,  # 温度段数
            "195": 1,  # 料筒温度1段实际值
            "197": 1,  # 料筒温度2段实际值
            "199": 1,  # 料筒温度3段实际值
            "201": 1,  # 料筒温度4段实际值
            "203": 1,  # 料筒温度5段实际值
            "205": 1,  # 料筒温度6段实际值
            "207": 1,  # 料筒温度7段实际值

            "146": 3,  # 熔胶段数
            "148": 1,  # 储料一段速度
            "151": 1,  # 储料二段速度
            "154": 1,  # 储料三段速度
            "147": 1,  # 储料一段背压
            "150": 1,  # 储料二段背压
            "153": 1,  # 储料三段背压
            "149": 1,  # 储料一段位置
            "152": 1,  # 储料二段位置
            "155": 1,  # 储料三段位置

            "162": 1,  # 熔胶前松退压力
            "163": 1,  # 熔胶前松退速度
            "164": 1,  # 熔胶前松退位置
            "165": 1,  # 熔胶前松退时间
            "166": 1,  # 熔胶后松退压力
            "167": 1,  # 熔胶后松退速度
            "168": 1,  # 熔胶后松退位置
            "169": 1,  # 熔胶后松退时间

            "114": 5,  # 保压段数
            "115": 1,  # 保压一段压力
            "118": 1,  # 保压二段压力
            "121": 1,  # 保压三段压力
            "124": 1,  # 保压四段压力
            "127": 1,  # 保压五段压力
            "116": 1,  # 保压一段速度
            "119": 1,  # 保压二段速度
            "122": 1,  # 保压三段速度
            "125": 1,  # 保压四段速度
            "128": 1,  # 保压五段速度
            "117": 1,  # 保压一段时间
            "120": 1,  # 保压二段时间
            "123": 1,  # 保压三段时间
            "126": 1,  # 保压四段时间
            "129": 1,  # 保压五段时间

            "83": 6,  # 注射段数
            "86": 1,  # 注射一段位置
            "89": 1,  # 注射二段位置
            "92": 1,  # 注射三段位置
            "95": 1,  # 注射四段位置
            "98": 1,  # 注射五段位置
            "101": 1,  # 注射六段位置
            "84": 1,  # 注射一段压力
            "87": 1,  # 注射二段压力
            "90": 1,  # 注射三段压力
            "93": 1,  # 注射四段压力
            "96": 1,  # 注射五段压力
            "99": 1,  # 注射六段压力
            "85": 1,  # 注射一段速度
            "88": 1,  # 注射二段速度
            "91": 1,  # 注射三段速度
            "94": 1,  # 注射四段速度
            "97": 1,  # 注射五段速度
            "100": 1,  # 注射六段速度

            "217": 1,  # 保压切换
            "223": 1,  # 冷却时间
        })
        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        for i in range(6):
            injection_pressure_sections.append(
                res_data.get(str(84+i*3)))
            injection_velocity_sections.append(
                res_data.get(str(85+i*3)))
            injection_distance_sections.append(
                res_data.get(str(86+i*3)))

        inject_para = {
            "injection_stage": res_data.get("83"),
            "max_injection_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            "cooling_time": res_data.get("223")
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(5):
            holding_pressure_sections.append(
                res_data.get(str(115+i*3)))
            holding_velocity_sections.append(
                res_data.get(str(116+i*3)))
            holding_time_sections.append(res_data.get(str(117+i*3)))

        holding_para = {
            "holding_stage": res_data.get("114"),
            "max_holding_stage_option": 5,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("vps_by_str_enbl"):
            VP_switch["VP_switch_mode"] = "位置"
            VP_switch["VP_switch_position"] = res_data.get("217")
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []
        for i in range(3):
            metering_rotation_sections.append(
                res_data.get(str(148+i*3)))
            metering_back_pressure_sections.append(
                res_data.get(str(147+i*3)))
            metering_distance_sections.append(
                res_data.get(str(149+i*3)))
        # metering_pressure_sections.append(
        #     res_data.get("66"))

        metering_para = {
            "metering_stage": 3,
            "max_metering_stage_option": 3,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("pressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    "pressure": res_data.get("162"),
                    "velocity": res_data.get("163"),
                    "time": res_data.get("165"),
                    "distance": res_data.get("164")
                },
                {
                    "label": "储后",
                    "pressure": res_data.get("166"),
                    "velocity": res_data.get("167"),
                    "time": res_data.get("169"),
                    "distance": res_data.get("168")
                }
            ]
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        for i in range(7):
            temp_sections.append(
                res_data.get(str(195+i*2)))
        temp_para = {
            "barrel_temperature_stage": res_data.get("194"),
            "max_barrel_temperature_stage_option": 7,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para

        return process_detail
    except Exception as e:
        logging.error(e)
        return dict(result="failed")


#  2022-KEBA全电.xlsx
def getProcessTechThree(machine_id=None, internal_id=None, token=None):
    try:
        # token = "063cd032-4bba-4c7e-9d97-85a04e8f06e1"
        # url = "http://kunpeng.yizumi.com:82/api/web/equipment/getSingleMonitorData?equipmentId=9006"

        # header_dict = {"Authorization": token}

        # res = None
        # resp = requests.get(url, headers=header_dict)
        # if resp.status_code == 200:
        #     res = json.loads(resp.text)
        res_data = dict({
            "159": 7,  # 温度段数
            "161": 1,  # 料筒温度1段实际值
            "166": 1,  # 料筒温度2段实际值
            "171": 1,  # 料筒温度3段实际值
            "176": 1,  # 料筒温度4段实际值

            "182": 1,  # 料筒温度5段实际值
            "187": 1,  # 料筒温度6段实际值
            "193": 1,  # 料筒温度7段实际值

            "76": 3,  # 熔胶段数
            "79": 1,  # 储料一段速度
            "82": 1,  # 储料二段速度
            "85": 1,  # 储料三段速度
            "80": 1,  # 储料一段压力
            "83": 1,  # 储料二段压力
            "86": 1,  # 储料三段压力
            "77": 1,  # 储料一段位置

            "81": 1,  # 储料二段位置
            "84": 1,  # 储料三段位置

            "70": 1,  # 熔胶前松退压力
            "69": 1,  # 熔胶前松退速度
            "68": 1,  # 熔胶前松退位置
            "101": 1,  # 熔胶后松退压力
            "100": 1,  # 熔胶后松退速度
            "99": 1,  # 熔胶后松退位置

            "53": 3,  # 保压段数
            "57": 1,  # 保压一段压力
            "60": 1,  # 保压二段压力
            "63": 1,  # 保压三段压力
            "55": 1,  # 保压一段速度
            "59": 1,  # 保压二段速度
            "62": 1,  # 保压三段速度
            "54": 1,  # 保压一段位置
            "58": 1,  # 保压二段位置
            "61": 1,  # 保压三段位置

            "18": 5,  # 注射段数
            "19": 1,  # 注射一段位置
            "22": 1,  # 注射二段位置
            "26": 1,  # 注射三段位置
            "29": 1,  # 注射四段位置
            "32": 1,  # 注射五段位置
            "21": 1,  # 注射一段压力
            "25": 1,  # 注射二段压力
            "28": 1,  # 注射三段压力
            "31": 1,  # 注射四段压力
            "35": 1,  # 注射五段压力
            "20": 1,  # 注射一段速度
            "24": 1,  # 注射二段速度
            "27": 1,  # 注射三段速度
            "30": 1,  # 注射四段速度
            "33": 1,  # 注射五段速度

            "41": 1,  # 保压切换
        })
        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        inject_pressure_list = ["21", "25", "28", "31", "35"]
        inject_velocity_list = ["20", "24", "27", "30", "33"]
        inject_distance_list = ["19", "22", "26", "29", "32"]
        for i in range(5):
            injection_pressure_sections.append(
                res_data.get(inject_pressure_list[i]))
            injection_velocity_sections.append(
                res_data.get(inject_velocity_list[i]))
            injection_distance_sections.append(
                res_data.get(inject_distance_list[i]))

        inject_para = {
            "injection_stage": res_data.get("18"),
            "max_injection_stage_option": 5,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            # "cooling_time": res_data.get("223")
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        # holding_time_sections = []
        # 有保压位置,没有保压时间
        holding_pressure_list = ["57", "60", "63"]
        holding_velocity_list = ["55", "59", "62"]
        # holding_time_list = ["54", "58", "61"]
        for i in range(3):
            holding_pressure_sections.append(
                res_data.get(holding_pressure_list[i]))
            holding_velocity_sections.append(
                res_data.get(holding_velocity_list[i]))
            # holding_time_sections.append(res_data.get(str(117+i*3)))

        holding_para = {
            "holding_stage": res_data.get("53"),
            "max_holding_stage_option": 3,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                # {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("vps_by_str_enbl"):
            VP_switch["VP_switch_mode"] = "位置"
            VP_switch["VP_switch_position"] = res_data.get("41")
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []

        metering_distance_list = ["77", "81", "84"]
        for i in range(3):
            metering_rotation_sections.append(
                res_data.get(str(79+i*3)))
            # metering_back_pressure_sections.append(
            #     res_data.get(str(147+i*3)))
            metering_distance_sections.append(
                res_data.get(metering_distance_list[i]))
            metering_pressure_sections.append(
                res_data.get(str(80+i*3)))

        metering_para = {
            "metering_stage": res_data.get("76"),
            "max_metering_stage_option": 3,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("pressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    "pressure": res_data.get("70"),
                    "velocity": res_data.get("69"),
                    # "time": res_data.get("165"),
                    "distance": res_data.get("68")
                },
                {
                    "label": "储后",
                    "pressure": res_data.get("101"),
                    "velocity": res_data.get("100"),
                    # "time": res_data.get("169"),
                    "distance": res_data.get("99")
                }
            ]
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        temp_list = ["161", "166", "171", "176", "182", "187", "193"]
        for i in range(6):
            temp_sections.append(
                res_data.get(temp_list[i]))
        temp_para = {
            "barrel_temperature_stage": res_data.get("159"),
            "max_barrel_temperature_stage_option": 6,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para

        return process_detail
    except Exception as e:
        logging.error(e)
        return dict(result="failed")


#  注塑机OPC变量表(20220513YZM).xlsx 1175
def getProcessTechFour(machine_id=None, internal_id=None, token=None):
    try:
        # token = "063cd032-4bba-4c7e-9d97-85a04e8f06e1"
        # url = "http://kunpeng.yizumi.com:82/api/web/equipment/getSingleMonitorData?equipmentId=9006"

        # header_dict = {"Authorization": token}

        # res = None
        # resp = requests.get(url, headers=header_dict)
        # if resp.status_code == 200:
        #     res = json.loads(resp.text)
        res_data = dict({
            "225": 7,  # 温度段数
            "227": 235,  # 料筒温度1段实际值
            "229": 235,  # 料筒温度2段实际值
            "231": 230,  # 料筒温度3段实际值
            "233": 225,  # 料筒温度4段实际值
            "235": 220,  # 料筒温度5段实际值
            "237": 215,  # 料筒温度6段实际值
            "239": 210,  # 料筒温度7段实际值

            "169": 1,  # 熔胶段数
            "170": 3000,  # 熔胶延时
            "172": 45,  # 储料一段速度
            # "175": 1,  # 储料二段速度
            # "178": 1,  # 储料三段速度
            "171": 10,  # 储料一段背压
            # "174": 1,  # 储料二段背压
            # "177": 1,  # 储料三段背压
            "173": 120,  # 储料一段位置
            # "176": 1,  # 储料二段位置
            # "179": 1,  # 储料三段位置

            # "186": 1,  # 熔胶前松退压力
            # "187": 1,  # 熔胶前松退速度
            # "188": 1,  # 熔胶前松退位置
            # "189": 1,  # 熔胶前松退时间
            "190": 53,  # 熔胶后松退压力
            "191": 14,  # 熔胶后松退速度
            "192": 2,  # 熔胶后松退位置
            "193": 1,  # 熔胶后松退时间

            "137": 5,  # 保压段数
            "138": 99,  # 保压一段压力
            "141": 35,  # 保压二段压力
            "144": 88,  # 保压三段压力
            "147": 66,  # 保压四段压力
            "150": 20,  # 保压五段压力
            "139": 8,  # 保压一段速度
            "142": 8,  # 保压二段速度
            "145": 15,  # 保压三段速度
            "148": 8,  # 保压四段速度
            "151": 3,  # 保压五段速度
            "140": 35.92,  # 保压一段时间
            "143": 42.45,  # 保压二段时间
            "146": 36.05,  # 保压三段时间
            "149": 37.77,  # 保压四段时间
            "152": 20,  # 保压五段时间

            "103": 6,  # 注射段数
            "107": 75,  # 注射一段位置
            "110": 65,  # 注射二段位置
            "113": 50,  # 注射三段位置
            "116": 46,  # 注射四段位置
            "119": 42,  # 注射五段位置
            "122": 40,  # 注射六段位置
            "105": 95,  # 注射一段压力
            "108": 70,  # 注射二段压力
            "111": 98,  # 注射三段压力
            "114": 95,  # 注射四段压力
            "117": 85,  # 注射五段压力
            "120": 50,  # 注射六段压力
            "106": 22,  # 注射一段速度
            "109": 9,  # 注射二段速度
            "112": 38,  # 注射三段速度
            "115": 25,  # 注射四段速度
            "118": 12,  # 注射五段速度
            "121": 6,  # 注射六段速度

            "136": 40,  # 保压切换
        })
        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []

        pressure_unit = machine_info.get("pressure_unit")
        velocity_unit = machine_info.get("velocity_unit")
        position_unit = machine_info.get("position_unit")
        time_unit = machine_info.get("position_unit")
        rotation_unit = machine_info.get("screw_rotation_unit")
        for i in range(6):
            injection_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(105+i*3))) if res_data.get(str(105+i*3)) else None)
            injection_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(106+i*3))) if res_data.get(str(106+i*3)) else None)
            injection_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(107+i*3))) if res_data.get(str(107+i*3)) else None)

        inject_para = {
            "injection_stage": res_data.get("103"),
            "max_injection_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            # "cooling_time": res_data.get("223")
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(5):
            holding_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(138+i*3))) if res_data.get(str(138+i*3)) else None)
            holding_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(139+i*3))) if res_data.get(str(139+i*3)) else None)
            holding_time_sections.append(res_data.get(
                str(140+i*3)) if res_data.get(str(140+i*3)) else None)

        holding_para = {
            "holding_stage": res_data.get("137"),
            "max_holding_stage_option": 5,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("vps_by_str_enbl"):
            VP_switch["VP_switch_mode"] = "位置"
            VP_switch["VP_switch_position"] = res_data.get("41")
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []

        for i in range(3):
            metering_rotation_sections.append(
                res_data.get(str(172+i*3)))
            metering_back_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(171+i*3))) if res_data.get(str(171+i*3)) else None)
            metering_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(173+i*3))) if res_data.get(str(173+i*3)) else None)
            # metering_pressure_sections.append(
            #     getPressureConversion(res_data.get(str(80+i*3))))

        metering_para = {
            "metering_stage": res_data.get("169"),
            "max_metering_stage_option": 3,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("pressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    "pressure":  getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("186")) if res_data.get("186") else None,
                    "velocity": getConversion(TRANSFER_ROTATION_UNIT, rotation_unit, res_data.get("187")) if res_data.get("187") else None,
                    "time": res_data.get("189"),
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("188")) if res_data.get("188") else None
                },
                {
                    "label": "储后",
                    "pressure": getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("190")) if res_data.get("190") else None,
                    "velocity": getConversion(TRANSFER_ROTATION_UNIT, rotation_unit, res_data.get("191")) if res_data.get("191") else None,
                    "time": res_data.get("193"),
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("192") if res_data.get("192") else None)
                }
            ],
            "metering_ending_position": None,
            "metering_delay_time": getConversion(TRANSFER_TIME_UNIT, time_unit, res_data.get("170")) if res_data.get("170") else None
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        for i in range(7):
            temp_sections.append(
                res_data.get(str(227+i*2)))
        temp_para = {
            "barrel_temperature_stage": res_data.get("225"),
            "max_barrel_temperature_stage_option": 7,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para

        return process_detail
    except Exception as e:
        logging.error(e)
        logging.error(e.__traceback__)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


#  yiplus_equipment_equipment_template_point_1669687618575.xlsx
def getProcessTechFive(machine_id=None, internal_id=None, token=None):
    try:
        # url = "http://kunpeng.yizumi.com:82/api/web/equipment/getSingleMonitorData?equipmentId=9006"

        # header_dict = {"Authorization": token}

        # res_data = None
        # resp = requests.get(url, headers=header_dict)
        # if resp.text.msg == "会话已过期,请重新登录":
        #     return dict(result="outdated")
        # elif resp.status_code == 200:
        #     res_data = json.loads(resp.text).get("data")
        res_data = dict({
            "74": 235,  # 料筒温度1段实际值
            "1": 235,  # 料筒温度2段实际值
            "2": 230,  # 料筒温度3段实际值
            "3": 225,  # 料筒温度4段实际值
            "4": 220,  # 料筒温度5段实际值
            "5": 215,  # 料筒温度6段实际值
            "6": 210,  # 料筒温度7段实际值

            "251": 99,  # 保压一段压力
            "254": 35,  # 保压二段压力
            "257": 88,  # 保压三段压力
            "260": 66,  # 保压四段压力
            "263": 20,  # 保压五段压力
            "250": 8,  # 保压一段速度
            "253": 8,  # 保压二段速度
            "256": 15,  # 保压三段速度
            "259": 8,  # 保压四段速度
            "262": 3,  # 保压五段速度
            "249": 35.92,  # 保压一段时间
            "252": 42.45,  # 保压二段时间
            "255": 36.05,  # 保压三段时间
            "258": 37.77,  # 保压四段时间
            "261": 20,  # 保压五段时间

            "19": 84,  # 注射一段位置 # 没有给
            "346": 75,  # 注射二段位置
            "349": 65,  # 注射三段位置
            "352": 50,  # 注射四段位置
            "355": 46,  # 注射五段位置
            "358": 42,  # 注射六段位置
            "347": 95,  # 注射一段压力
            "350": 70,  # 注射二段压力
            "353": 98,  # 注射三段压力
            "356": 95,  # 注射四段压力
            "359": 85,  # 注射五段压力
            "362": 50,  # 注射六段压力
            "345": 22,  # 注射一段速度
            "348": 9,  # 注射二段速度
            "351": 38,  # 注射三段速度
            "354": 25,  # 注射四段速度
            "357": 12,  # 注射五段速度
            "360": 6,  # 注射六段速度

            "72": 6,  # 注射时间

            "60": 40,  # 保压切换
        })
        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        for i in range(6):
            injection_pressure_sections.append(
                res_data.get(str(347+i*3)))
            injection_velocity_sections.append(
                res_data.get(str(345+i*3)))
            if i == 0:
                injection_distance_sections.append(None)
            if i > 0:
                injection_distance_sections.append(
                    res_data.get(str(343+i*3)))

        inject_para = {
            "injection_stage": 6,
            "max_injection_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            # "cooling_time": res_data.get("223")
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(5):
            holding_pressure_sections.append(
                res_data.get(str(251+i*3)))
            holding_velocity_sections.append(
                res_data.get(str(250+i*3)))
            holding_time_sections.append(res_data.get(str(249+i*3)))

        holding_para = {
            "holding_stage": 5,
            "max_holding_stage_option": 5,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("60"):
            VP_switch["VP_switch_mode"] = "位置"
            VP_switch["VP_switch_position"] = res_data.get("60")
        process_detail["VP_switch"] = VP_switch

        # metering_pressure_sections = []
        # metering_rotation_sections = []
        # metering_back_pressure_sections = []
        # metering_distance_sections = []

        # metering_distance_list = ["77", "81", "84"]
        # for i in range(3):
        #     metering_rotation_sections.append(
        #         res_data.get(str(79+i*3)))
        #     # metering_back_pressure_sections.append(
        #     #     res_data.get(str(147+i*3)))
        #     metering_distance_sections.append(
        #         res_data.get(metering_distance_list[i]))
        #     metering_pressure_sections.append(
        #         res_data.get(str(80+i*3)))

        metering_para = {
            "metering_stage": 3,
            "max_metering_stage_option": 3,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": []},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": []},
                {"label": "背压", "unit": machine_info.get("pressure_unit"),
                 "sections": []},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": []}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    "pressure": None,
                    "velocity": None,
                    "time": None,
                    "distance": None
                },
                {
                    "label": "储后",
                    "pressure": None,
                    "velocity": None,
                    "time": None,
                    "distance": None
                }
            ]
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        temp_list = ["74", "1", "2", "3", "4", "5", "6"]
        for i in range(7):
            temp_sections.append(
                res_data.get(temp_list[i]))
        temp_para = {
            "barrel_temperature_stage": 7,
            "max_barrel_temperature_stage_option": 7,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para
        # 需要先确定是哪台机器machine_id
        process_detail = param_check(process_detail)
        return process_detail
    except Exception as e:
        logging.error(e)
        logging.error(e.__traceback__)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


# 校验参数,使其不超过机器设定范围。读取和写入之前都要做校验
def param_check(process_detail):
    try:
        machine_id = process_detail["machine_id"]
        machine_info = process_optimize_service.extract_machine(machine_id)
        if process_detail.get("VP_switch") and process_detail.get("VP_switch").get("VP_switch_position") and process_detail["VP_switch"]["VP_switch_position"] > float(machine_info.get("max_injection_stroke")):
            process_detail["VP_switch"]["VP_switch_position"] = float(
                machine_info.get("max_injection_stroke"))

        for i in range(0, process_detail['inject_para']['injection_stage']):
            if process_detail.get("inject_para").get("table_data")[0].get("sections")[i] > machine_info.get("max_injection_pressure"):
                process_detail["inject_para"]["table_data"][0]["sections"][i] = machine_info.get(
                    "max_injection_pressure")
            if process_detail.get("inject_para").get("table_data")[1].get("sections")[i] > machine_info.get("max_injection_velocity"):
                process_detail["inject_para"]["table_data"][1]["sections"][i] = machine_info.get(
                    "max_injection_velocity")

        for i in range(0, process_detail['holding_para']['holding_stage']):
            if process_detail.get("holding_para").get("table_data")[0].get("sections")[i] > machine_info.get("max_holding_pressure"):
                process_detail["holding_para"]["table_data"][0]["sections"][i] = machine_info.get(
                    "max_holding_pressure")
            if process_detail.get("holding_para").get("table_data")[1].get("sections")[i] > machine_info.get("max_holding_velocity"):
                process_detail["holding_para"]["table_data"][1]["sections"][i] = machine_info.get(
                    "max_holding_velocity")

        for i in range(0, process_detail['metering_para']['metering_stage'] and len(process_detail.get("metering_para").get("table_data")[0].get("sections")) > 0):
            if process_detail.get("metering_para").get("table_data")[0].get("sections")[i] > machine_info.get("max_screw_rotation_speed"):
                process_detail["metering_para"]["table_data"][0]["sections"][i] = machine_info.get(
                    "max_screw_rotation_speed")
            if process_detail.get("metering_para").get("table_data")[0].get("sections")[i] > machine_info.get("max_metering_back_pressure"):
                process_detail["metering_para"]["table_data"][0]["sections"][i] = machine_info.get(
                    "max_metering_back_pressure")
            if i < process_detail['metering_stage'] - 1 and process_detail.get("ML"+str(i)) > process_detail.get("ML" + str(i+1)):
                process_detail["ML" +
                               str(i)] = process_detail.get("ML" + str(i+1))
        if process_detail.get("metering_para").get("decompressure_paras")[0].get("velocity") and process_detail.get("metering_para").get("decompressure_paras")[0].get("velocity")[i] > machine_info.get("max_decompression_velocity"):
            process_detail["metering_para"]["decompressure_paras"][0]["velocity"][i] = 999
        if process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure") and process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure")[i] > machine_info.get("max_decompression_pressure"):
            process_detail["metering_para"]["decompressure_paras"][0]["pressure"][i] = 55

        # 位置需要限制：储料位置>4段位置>3段位置>2段位置>1段位置>切换位置

    except Exception as e:
        logging.error(e)
        logging.error(e.__traceback__)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")
    return process_detail


# 2000控制器
def setProcessTechOne(process_detail=None, token=None):
    try:
        res_data = dict({
            "74": 1,  # 料筒温度1段实际值
            "1": 1,  # 料筒温度2段实际值
            "2": 1,  # 料筒温度3段实际值
            "3": 1,  # 料筒温度4段实际值
            "4": 1,  # 料筒温度5段实际值
            "5": 1,  # 料筒温度6段实际值
            "6": 1,  # 料筒温度7段实际值

            "251": 1,  # 保压一段压力
            "254": 1,  # 保压二段压力
            "257": 1,  # 保压三段压力
            "260": 1,  # 保压四段压力
            "263": 1,  # 保压五段压力
            "250": 1,  # 保压一段速度
            "253": 1,  # 保压二段速度
            "256": 1,  # 保压三段速度
            "259": 1,  # 保压四段速度
            "262": 1,  # 保压五段速度
            "249": 1,  # 保压一段时间
            "252": 1,  # 保压二段时间
            "255": 1,  # 保压三段时间
            "258": 1,  # 保压四段时间
            "261": 1,  # 保压五段时间

            # "19": 1,  # 注射一段位置 # 没有给
            "346": 1,  # 注射二段位置
            "349": 1,  # 注射三段位置
            "352": 1,  # 注射四段位置
            "355": 1,  # 注射五段位置
            "358": 1,  # 注射六段位置
            "347": 1,  # 注射一段压力
            "350": 1,  # 注射二段压力
            "353": 1,  # 注射三段压力
            "356": 1,  # 注射四段压力
            "359": 1,  # 注射五段压力
            "362": 1,  # 注射六段压力
            "345": 1,  # 注射一段速度
            "348": 1,  # 注射二段速度
            "351": 1,  # 注射三段速度
            "354": 1,  # 注射四段速度
            "357": 1,  # 注射五段速度
            "360": 1,  # 注射六段速度

            "72": 1,  # 注射时间

            "60": 1,  # 保压切换
        })
        injection_pressure_sections = process_detail.get(
            "inject_para").get("table_data")[0].get("sections")
        injection_velocity_sections = process_detail.get(
            "inject_para").get("table_data")[1].get("sections")
        injection_distance_sections = process_detail.get(
            "inject_para").get("table_data")[2].get("sections")
        for i in range(6):
            res_data[str(347+i*3)] = injection_pressure_sections[i]
            res_data[str(345+i*3)] = injection_velocity_sections[i]
            if i > 0:
                res_data[str(343+i*3)] = injection_distance_sections[i]
        holding_pressure_sections = process_detail.get(
            "holding_para").get("table_data")[0].get("sections")
        holding_velocity_sections = process_detail.get(
            "holding_para").get("table_data")[1].get("sections")
        holding_time_sections = process_detail.get(
            "holding_para").get("table_data")[2].get("sections")
        for i in range(5):
            res_data[str(251+i*3)] = holding_pressure_sections[i]
            res_data[str(250+i*3)] = holding_velocity_sections[i]
            res_data[str(249+i*3)] = holding_time_sections[i]

        VP_switch = process_detail.get("VP_switch")
        res_data["60"] = VP_switch.get("VP_switch_position")

        temp_sections = process_detail.get("temp_para").get("table_data")[
            0].get("sections")
        temp_list = ["74", "1", "2", "3", "4", "5", "6"]
        for i in range(7):
            res_data[str(temp_list[i])] = temp_sections[i]
        url = "http://kunpeng.yizumi.com:82/api/web/equipment/craft/issue"
        header_dict = {"Content-Type": "application/json; charset=UTF-8"}
        header_dict["Authorization"] = token

        res = None
        json_data = json.dumps({
            "equipmentId": 8997,
            "data": [{
                "name": "103",
                "value": "6"
            },
                {
                "name": "104",
                "value": "7"
            },
                {
                "name": "105",
                "value": "8"
            },
                {
                "name": "106",
                "value": "9"
            }
            ]
        })
        resp = requests.post(url, data=json_data, headers=header_dict)
        logging.info(f"返回值是多少{resp}")
        if resp.status_code == 200:
            res = json.loads(resp.text)
        if res.msg == "会话已过期,请重新登录":
            return dict(result="outdated")
        else:
            return dict(result="success")
    except Exception as e:
        logging.error(e.args)
        return dict(result="failed")


# 注塑机OPC变量表(20220513YZM).xlsx 1175
def setProcessTechFour(process_detail=None, token=None):
    try:
        pressure_unit = process_detail.get(
            "inject_para").get("table_data")[0].get("unit")
        velocity_unit = process_detail.get(
            "inject_para").get("table_data")[1].get("unit")
        position_unit = process_detail.get(
            "inject_para").get("table_data")[2].get("unit")
        time_unit = process_detail.get("holding_para").get(
            "table_data")[2].get("unit")
        rotation_unit = process_detail.get(
            "metering_para").get("table_data")[1].get("unit")
        # 温度段数不需要发,是默认的.
        json_data = json.dumps({
            "equipmentId": 8997,
            "data": [
                {"name": "228", "value": process_detail.get("temp_para").get("table_data")[
                    0].get("sections")[0]},  # 料筒温度1段实际值
                {"name": "230", "value": process_detail.get("temp_para").get("table_data")[
                    0].get("sections")[1]},  # 料筒温度2段实际值
                {"name": "232", "value": process_detail.get("temp_para").get("table_data")[
                    0].get("sections")[2]},  # 料筒温度3段实际值
                {"name": "234", "value": process_detail.get("temp_para").get("table_data")[
                    0].get("sections")[3]},  # 料筒温度4段实际值
                {"name": "236", "value": process_detail.get("temp_para").get("table_data")[
                    0].get("sections")[4]},  # 料筒温度5段实际值
                {"name": "169", "value": process_detail.get(
                    "metering_para").get("metering_stage")},  # 熔胶段数
                {"name": "172", "value": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, process_detail.get("metering_para").get("table_data")[
                    1].get("sections")[0])},  # 储料一段速度
                {"name": "175", "value": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, process_detail.get("metering_para").get("table_data")[
                    1].get("sections")[1])},  # 储料二段速度
                {"name": "178", "value": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, process_detail.get("metering_para").get("table_data")[
                    1].get("sections")[2])},  # 储料三段速度
                {"name": "171", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("table_data")[
                    2].get("sections")[0])},  # 储料一段背压
                {"name": "174", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("table_data")[
                    2].get("sections")[1])},  # 储料二段背压
                {"name": "177", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("table_data")[
                    2].get("sections")[2])},  # 储料三段背压
                {"name": "173", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("table_data")[
                    3].get("sections")[0])},  # 储料一段位置
                {"name": "176", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("table_data")[
                    3].get("sections")[1])},  # 储料二段位置
                {"name": "179", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("table_data")[
                    3].get("sections")[2])},  # 储料三段位置
                {"name": "186", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get(
                    "decompressure_paras")[0].get("pressure"))},  # 熔胶前松退压力
                {"name": "187", "value": process_detail.get("metering_para").get(
                    "decompressure_paras")[0].get("velocity")},  # 熔胶前松退速度
                {"name": "188", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get(
                    "decompressure_paras")[0].get("distance"))},  # 熔胶前松退位置
                {"name": "189", "value": process_detail.get("metering_para").get(
                    "decompressure_paras")[0].get("time")},  # 熔胶前松退时间
                {"name": "190", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get(
                    "decompressure_paras")[1].get("pressure"))},  # 熔胶后松退压力
                {"name": "191", "value": process_detail.get("metering_para").get(
                    "decompressure_paras")[1].get("velocity")},  # 熔胶后松退速度
                {"name": "192", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get(
                    "decompressure_paras")[1].get("distance"))},  # 熔胶后松退位置
                {"name": "193", "value": process_detail.get("metering_para").get(
                    "decompressure_paras")[1].get("time")},  # 熔胶后松退时间
                {"name": "137", "value": process_detail.get(
                    "holding_para").get("holding_stage")},  # 保压段数
                {"name": "138", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("holding_para").get("table_data")[
                    0].get("sections")[0])},  # 保压一段压力
                {"name": "141", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("holding_para").get("table_data")[
                    0].get("sections")[1])},  # 保压二段压力
                {"name": "144", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("holding_para").get("table_data")[
                    0].get("sections")[2])},  # 保压三段压力
                {"name": "139", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("holding_para").get("table_data")[
                    1].get("sections")[0])},  # 保压一段速度
                {"name": "142", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("holding_para").get("table_data")[
                    1].get("sections")[1])},  # 保压二段速度
                {"name": "145", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("holding_para").get("table_data")[
                    1].get("sections")[2])},  # 保压三段速度
                {"name": "140", "value": process_detail.get("holding_para").get("table_data")[
                    2].get("sections")[0]},  # 保压一段时间
                {"name": "143", "value": process_detail.get("holding_para").get("table_data")[
                    2].get("sections")[1]},  # 保压二段时间
                {"name": "146", "value": process_detail.get("holding_para").get("table_data")[
                    2].get("sections")[2]},  # 保压三段时间
                {"name": "103", "value": process_detail.get(
                    "inject_para").get("injection_stage")},  # 注射段数
                {"name": "107", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("inject_para").get("table_data")[
                    2].get("sections")[0])},  # 注射一段位置
                {"name": "110", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("inject_para").get("table_data")[
                    2].get("sections")[1])},  # 注射二段位置
                {"name": "113", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("inject_para").get("table_data")[
                    2].get("sections")[2])},  # 注射三段位置
                {"name": "116", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("inject_para").get("table_data")[
                    2].get("sections")[3])},  # 注射四段位置
                {"name": "119", "value": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("inject_para").get("table_data")[
                    2].get("sections")[4])},  # 注射五段位置
                {"name": "105", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("inject_para").get("table_data")[
                    0].get("sections")[0])},  # 注射一段压力
                {"name": "108", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("inject_para").get("table_data")[
                    0].get("sections")[1])},  # 注射二段压力
                {"name": "111", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("inject_para").get("table_data")[
                    0].get("sections")[2])},  # 注射三段压力
                {"name": "114", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("inject_para").get("table_data")[
                    0].get("sections")[3])},  # 注射四段压力
                {"name": "117", "value": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("inject_para").get("table_data")[
                    0].get("sections")[4])},  # 注射五段压力
                {"name": "106", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("inject_para").get("table_data")[
                    1].get("sections")[0])},  # 注射一段速度
                {"name": "109", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("inject_para").get("table_data")[
                    1].get("sections")[1])},  # 注射二段速度
                {"name": "112", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("inject_para").get("table_data")[
                    1].get("sections")[2])},  # 注射三段速度
                {"name": "115", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("inject_para").get("table_data")[
                    1].get("sections")[3])},  # 注射四段速度
                {"name": "118", "value": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("inject_para").get("table_data")[
                    1].get("sections")[4])},  # 注射五段速度
                {"name": "136", "value": process_detail.get(
                    "VP_switch").get("VP_switch_position")},  # 保压切换
            ]
        })

        url = "http://kunpeng.yizumi.com:82/api/web/equipment/craft/issue"

        header_dict = {"Content-Type": "application/json; charset=UTF-8"}
        header_dict["Authorization"] = token
        # res = None
        # resp = requests.post(url, data=json_data, headers=header_dict)
        # if resp.status_code == 200:
        #     res = json.loads(resp.text)
        # if res.msg == "会话已过期,请重新登录":
        #     return dict(result="outdated")
        # else:
        #     return dict(result="success")
        return dict(result="success")
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


#  注塑机OPC变量表(20220513YZM).xlsx 1175 以国际单位进行传输
def getProcessTechSix():
    global machine_info
    try:
        token = loginYuzimi()
        # token = "77a6b28c-16e4-4e12-a552-e4e55b9bccce"
        # sn=GL5022219000151
        url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=1"
        header_dict = {"Authorization": token}

        res_data = None
        resp = requests.get(url, headers=header_dict)
        if resp.status_code == 200:
            res = json.loads(resp.text)
            if res.get("code") == 200 and res.get("msg") == "success":
                res_data = res.get("data")
        # res_data = dict({
        #     "225": 4,  # 温度段数
			
        #     #"227": 235,  # 料筒温度1段实际值
        #     #"229": 235,  # 料筒温度2段实际值
        #     #"231": 230,  # 料筒温度3段实际值
        #     #"233": 225,  # 料筒温度4段实际值
        #     #"235": 220,  # 料筒温度5段实际值
        #     #"237": 215,  # 料筒温度6段实际值
        #     #"239": 210,  # 料筒温度7段实际值

        #     "169": 1,  # 熔胶段数
        #     "170": 0.1, # 熔胶延时
        #     "172": 18.33,  # 储料一段速度
        #     # "175": 1,  # 储料二段速度
        #     # "178": 1,  # 储料三段速度
        #     "171": 10,  # 储料一段背压
        #     # "174": 1,  # 储料二段背压
        #     # "177": 1,  # 储料三段背压
        #     "173": 76.97,  # 储料一段位置
        #     # "176": 1,  # 储料二段位置
        #     # "179": 1,  # 储料三段位置

        #     "186": 50,  # 熔胶前松退压力
        #     "187": 38.9,  # 熔胶前松退速度
        #     "188": 9.62,  # 熔胶前松退位置
        #     "189": 0,  # 熔胶前松退时间
        #     "190": 20,  # 熔胶后松退压力
        #     "191": 15.56,  # 熔胶后松退速度
        #     "192": 4.81,  # 熔胶后松退位置

        #     "193": 1,  # 熔胶后松退时间

        #     "137": 1,  # 保压段数
        #     "138": 530.61,  # 保压一段压力
        #     # "141": 35,  # 保压二段压力
        #     "144": 530.61,  # 保压三段压力
        #     # "147": 66,  # 保压四段压力
        #     # "150": 20,  # 保压五段压力
        #     "139": 8,  # 保压一段速度
        #     # "142": 8,  # 保压二段速度
        #     "145": 27.99,  # 保压三段速度
        #     # "148": 8,  # 保压四段速度
        #     # "151": 3,  # 保压五段速度
        #     "140": 10,  # 保压一段时间
        #     "143": 2,  # 保压二段时间
        #     "146": 1,  # 保压三段时间
        #     # "149": 37.77,  # 保压四段时间
        #     # "152": 20,  # 保压五段时间

        #     "103": 1,  # 注射段数
        #     "107": 75,  # 注射一段位置
        #     "110": 65,  # 注射二段位置
        #     "113": 50,  # 注射三段位置
        #     "116": 46,  # 注射四段位置
        #     "119": 42,  # 注射五段位置
        #     "122": 40,  # 注射六段位置
        #     "105": 95,  # 注射一段压力
        #     "108": 70,  # 注射二段压力
        #     "111": 98,  # 注射三段压力
        #     "114": 95,  # 注射四段压力
        #     "117": 85,  # 注射五段压力
        #     "120": 50,  # 注射六段压力
			
        #     "106": 55.97,  # 注射一段速度
			
        #     "109": 9,  # 注射二段速度
        #     "112": 38,  # 注射三段速度
        #     "115": 25,  # 注射四段速度
        #     "118": 12,  # 注射五段速度
        #     "121": 6,  # 注射六段速度

        #     "136": 40,  # 保压切换
        # })
#         res_data = dict(
# {
# 	'CurrentPack': None,
# 	'0': '5',
# 	'1': '500.0',
# 	'2': '208.35',
# 	'3': '280.0',
# 	'4': '650.0',
# 	'5': '333.36',
# 	'6': '30.0',
# 	'7': '500.0',
# 	'8': '208.35',
# 	'9': '20.0',
# 	'TotalIdleTime': None,
# 	'ShiftUpTime': None,
# 	'MaterialCode': None,
# 	'2001': '0',
# 	'2000': '700.28',
# 	'DefectiveProduct': None,
# 	'TotalMould': None,
# 	'2012': '2',
# 	'2010': '0.0',
# 	'2009': '77.81',
# 	'2008': '35.0',
# 	'2007': '93.29',
# 	'2006': '36.29',
# 	'2005': '827.52',
# 	'2004': '22.4',
# 	'2003': '45.0',
# 	'2002': '1',
# 	'2021': '0.0',
# 	'2020': '25.0',
# 	'2019': '50.0',
# 	'2018': '0.0',
# 	'2017': '416.7',
# 	'2016': '93.29',
# 	'2015': '0.0',
# 	'2014': '40.0',
# 	'2013': '90.0',
# 	'ActualCycle': None,
# 	'CmsProductName': None,
# 	'CmsFinishTime': None,
# 	'PlanEndDate': None,
# 	'OperatoinState': None,
# 	'PrintProgress': None,
# 	'TotalProduct': None,
# 	'TimeEfficency': None,
# 	'300': '0.0',
# 	'301': '0.0',
# 	'302': '0.0',
# 	'303': '0.0',
# 	'304': '0.0',
# 	'305': '0.0',
# 	'306': '0.0',
# 	'307': '0.0',
# 	'308': '0.0',
# 	'309': '0.0',
# 	'TotalFaultTime': None,
# 	'310': '0.0',
# 	'311': '0.0',
# 	'312': '0.0',
# 	'313': '0.0',
# 	'314': '0.0',
# 	'315': '0.0',
# 	'316': '0.0',
# 	'317': '0.0',
# 	'318': '0.0',
# 	'319': '0.0',
# 	'ShiftProduct': None,
# 	'320': '0.0',
# 	'200': None,
# 	'321': '0',
# 	'201': None,
# 	'322': '100',
# 	'202': None,
# 	'323': '1.039379',
# 	'203': None,
# 	'324': '1',
# 	'204': None,
# 	'325': '1',
# 	'205': None,
# 	'326': '100',
# 	'206': None,
# 	'327': '1',
# 	'207': None,
# 	'328': '1',
# 	'208': None,
# 	'329': '1',
# 	'209': None,
# 	'330': None,
# 	'210': None,
# 	'331': '0.0',
# 	'211': None,
# 	'332': None,
# 	'212': None,
# 	'333': '0',
# 	'213': None,
# 	'334': '0.0',
# 	'214': None,
# 	'335': None,
# 	'215': None,
# 	'336': '0',
# 	'216': None,
# 	'337': '0.0',
# 	'217': None,
# 	'338': None,
# 	'218': None,
# 	'339': '0',
# 	'219': None,
# 	'340': '0.0',
# 	'220': None,
# 	'341': None,
# 	'100': '0.0',
# 	'221': None,
# 	'342': '0',
# 	'101': '0.0',
# 	'222': None,
# 	'343': '0.0',
# 	'102': '0',
# 	'223': None,
# 	'344': None,
# 	'103': '1',
# 	'224': None,
# 	'345': '0',
# 	'104': '1857.14',
# 	'225': '4',
# 	'346': None,
# 	'105': '1200.000576923077',
# 	'226': '160.0',
# 	'347': '0.0',
# 	'106': '55.97',
# 	'227': None,
# 	'348': '0.0',
# 	'107': '-1000.0',
# 	'228': '210.0',
# 	'349': '17.7',
# 	'108': '0.0',
# 	'229': None,
# 	'109': '0.0',
# 	'350': '60.0',
# 	'230': '210.0',
# 	'351': '60.0',
# 	'110': '0.0',
# 	'231': None,
# 	'352': '10.0',
# 	'111': '0.0',
# 	'232': '200.0',
# 	'353': '0.0',
# 	'112': '0.0',
# 	'233': None,
# 	'354': '2',
# 	'113': '0.0',
# 	'234': '190.0',
# 	'355': '0',
# 	'114': '0.0',
# 	'235': None,
# 	'356': '0',
# 	'115': '0.0',
# 	'236': '270.0',
# 	'357': '0',
# 	'116': '0.0',
# 	'237': None,
# 	'358': '0',
# 	'CurrentState': None,
# 	'117': '0.0',
# 	'238': '250.0',
# 	'359': '0',
# 	'118': '0.0',
# 	'239': None,
# 	'119': '0.0',
# 	'10': '300.0',
# 	'11': '83.34',
# 	'CurrentMaterialNo': None,
# 	'12': '5.0',
# 	'13': '1000.0',
# 	'14': '125.01',
# 	'15': '0.0',
# 	'16': '20.0',
# 	'17': '5.0',
# 	'18': '0.0',
# 	'19': '5',
# 	'360': '0',
# 	'240': '250.0',
# 	'361': '0',
# 	'120': '0.0',
# 	'241': '5340',
# 	'362': '0',
# 	'121': '0.0',
# 	'242': '0.0',
# 	'363': '0',
# 	'122': '0.0',
# 	'243': '0.0',
# 	'364': '0',
# 	'123': '0.0',
# 	'244': '0.0',
# 	'365': '0',
# 	'124': '0.0',
# 	'245': '0.0',
# 	'366': '0',
# 	'125': '0.0',
# 	'246': '0.0',
# 	'126': '0.0',
# 	'247': '0.0',
# 	'127': '0.0',
# 	'248': '0.0',
# 	'128': '0.0',
# 	'249': '0.0',
# 	'129': '0.0',
# 	'PlanPack': None,
# 	'20': '900.0',
# 	'21': '105.04',
# 	'22': '5.0',
# 	'23': '800.0',
# 	'24': '560.23',
# 	'25': '100.0',
# 	'26': '500.0',
# 	'27': '350.14',
# 	'28': '200.0',
# 	'CurrentProduct': None,
# 	'29': '400.0',
# 	'250': '0.0',
# 	'130': '0.0',
# 	'251': '0.0',
# 	'131': '0.0',
# 	'252': '0.0',
# 	'132': '0.0',
# 	'253': '0.33',
# 	'133': '0.0',
# 	'254': '0.0',
# 	'134': '0.0',
# 	'255': '0.0',
# 	'135': '10.0',
# 	'256': '0.0',
# 	'136': '53.88',
# 	'257': '0.0',
# 	'137': '1',
# 	'258': '0.0',
# 	'138': '499.9978846153846',
# 	'259': '9999',
# 	'139': '37.32',
# 	'30': '175.07',
# 	'31': '250.0',
# 	'32': '300.0',
# 	'33': '105.04',
# 	'34': '280.0',
# 	'Progress': None,
# 	'35': '30.0',
# 	'36': '20.0',
# 	'37': '30.0',
# 	'ErpNo': None,
# 	'MouldCode': None,
# 	'38': '20.0',
# 	'39': '0',
# 	'260': '5340',
# 	'140': '10.0',
# 	'261': '4659',
# 	'141': '0.0',
# 	'262': '43.64',
# 	'142': '0.0',
# 	'263': '43.77',
# 	'143': '2.0',
# 	'264': '87.41',
# 	'144': '499.9978846153846',
# 	'265': 'YZ',
# 	'145': '27.99',
# 	'266': '--',
# 	'146': '1.0',
# 	'267': '--',
# 	'147': '0.0',
# 	'268': '0',
# 	'148': '0.0',
# 	'269': '0',
# 	'149': '0.0',
# 	'CurrentMoldNo': None,
# 	'40': '0',
# 	'41': '0',
# 	'42': '0.0',
# 	'43': '290.0',
# 	'44': '800.0',
# 	'45': '0.0',
# 	'46': '1',
# 	'47': '2',
# 	'48': '1',
# 	'49': '70.16168544830965',
# 	'PlanQuantity': None,
# 	'270': None,
# 	'150': '0.0',
# 	'271': '2812',
# 	'151': '0.0',
# 	'272': None,
# 	'152': '0.0',
# 	'273': '0',
# 	'PlanProduct': None,
# 	'153': '0.0',
# 	'274': '0',
# 	'154': '0.0',
# 	'275': '0',
# 	'155': '0.0',
# 	'276': '0.0',
# 	'156': '0.0',
# 	'277': '0.0',
# 	'157': '0.0',
# 	'278': '0.0',
# 	'158': '0.0',
# 	'279': '0',
# 	'159': '0.0',
# 	'50': '186.74',
# 	'51': '45.0',
# 	'52': '9.799118079372857',
# 	'53': '40.0',
# 	'54': '0.0',
# 	'55': '0.0',
# 	'56': '0.0',
# 	'57': '50.0',
# 	'ShiftIdleTime': None,
# 	'58': '2',
# 	'59': '35.178833904948554',
# 	'280': '0.0',
# 	'MesFinishTime': None,
# 	'160': '0.0',
# 	'281': '0',
# 	'161': '0.0',
# 	'282': '0.0',
# 	'162': '0.0',
# 	'283': '10.0',
# 	'163': '0.0',
# 	'284': '150.0',
# 	'164': '0.0',
# 	'285': '0.0',
# 	'ShiftFaultTime': None,
# 	'165': '0.0',
# 	'286': '0.0',
# 	'166': '0.0',
# 	'287': '0.0',
# 	'167': '0.0',
# 	'288': '0.0',
# 	'168': '80.0',
# 	'289': '0.0',
# 	'MouldName': None,
# 	'169': '1',
# 	'60': '248.26',
# 	'61': '50.0',
# 	'62': '23.41989220970113',
# 	'63': '165.5',
# 	'64': '5.0',
# 	'65': '9.799118079372857',
# 	'66': '40.0',
# 	'67': '0.0',
# 	'68': '0',
# 	'69': '0',
# 	'290': '0.0',
# 	'170': '1.0000000000000001E-7',
# 	'291': '0.0',
# 	'171': '20.0',
# 	'292': '0.0',
# 	'172': '18.33',
# 	'293': '0.0',
# 	'173': '76.97',
# 	'294': '0.0',
# 	'174': '0.0',
# 	'295': '0',
# 	'175': '0.0',
# 	'296': '0',
# 	'176': '0.0',
# 	'297': '0',
# 	'177': '0.0',
# 	'298': '0.0',
# 	'178': '0.0',
# 	'299': '0.0',
# 	'179': '0.0',
# 	'70': '0',
# 	'71': '100.0',
# 	'72': '17.82',
# 	'73': '0.0',
# 	'74': '0',
# 	'75': '100.0',
# 	'76': '17.82',
# 	'77': '0.0',
# 	'78': '0',
# 	'79': '100.0',
# 	'180': '0.0',
# 	'181': '0.0',
# 	'182': '0.0',
# 	'183': '0.0',
# 	'184': '0.0',
# 	'185': '0.0',
# 	'186': '500.0',
# 	'WoNo': None,
# 	'187': '37.4072125',
# 	'188': '9.62',
# 	'189': '0.0',
# 	'80': '17.82',
# 	'TotalUpTime': None,
# 	'81': '0.0',
# 	'82': '0',
# 	'83': '100.0',
# 	'84': '17.82',
# 	'85': '0.0',
# 	'86': '0',
# 	'87': '0.0',
# 	'88': '0.0',
# 	'89': '0.0',
# 	'190': '200.0',
# 	'191': '14.962885',
# 	'192': '4.81',
# 	'193': '0.0',
# 	'194': None,
# 	'195': None,
# 	'196': None,
# 	'197': None,
# 	'TotalDefectiveProduct': None,
# 	'198': None,
# 	'199': None,
# 	'90': '0',
# 	'91': '0.0',
# 	'92': '0.0',
# 	'93': '0.0',
# 	'94': '0',
# 	'95': '0.0',
# 	'96': '0.0',
# 	'97': '0.0',
# 	'98': '0',
# 	'99': '0.0',
# 	'StandardCycle': None,
# 	'BadQuantity': None,
# 	'EquipmentModel': None,
# 	'ReportQuantity': None,
# 	'UpTimeRate': None,
# 	'ProducedQuantity': None,
# 	'TotalRunTime': None,
# 	'CavityNum': None,
# 	'LeftQuantity': None,
# 	'ShiftRunTime': None,
# 	'GoodQuantity': None,
# 	'MaterialName': None
# }
#         )
        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        pressure_unit = machine_info.get("pressure_unit")
        velocity_unit = machine_info.get("velocity_unit")
        position_unit = machine_info.get("position_unit")
        time_unit = machine_info.get("time_unit")
        rotation_unit = machine_info.get("screw_rotation_unit")
        backpressure_unit = machine_info.get("backpressure_unit")
        for i in range(int(res_data.get("103"))):
            injection_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(105+i*3)), convert_type="injection_pressure_read") if res_data.get(str(105+i*3)) else None)
            # 2007 是最大注射体积cm³/s
            injection_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(106+i*3)), convert_type="injection") if res_data.get(str(106+i*3)) else None)
            injection_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(107+i*3))) if res_data.get(str(107+i*3)) else None)

        inject_para = {
            "injection_stage": res_data.get("103"),
            "max_injection_stage_option": int(res_data.get("103")),
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            "cooling_time": res_data.get("255"),            
            # "injection_delay_time":res_data.get("312"),
            "injection_time":round(float(res_data.get("248")), 2) if res_data.get("248") else None
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(int(res_data.get("137"))):
            holding_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(138+i*3)), convert_type="holding_pressure_read") if res_data.get(str(138+i*3)) else None)
            holding_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(139+i*3)), convert_type="holding") if res_data.get(str(139+i*3)) else None)
            holding_time_sections.append(res_data.get(
                str(140+i*3)) if res_data.get(str(140+i*3)) else None)

        holding_para = {
            "holding_stage": res_data.get("137"),
            "max_holding_stage_option": int(res_data.get("137")),
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("136"):
            VP_switch["VP_switch_position"] = getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("136")) if res_data.get("136") else None
        if res_data.get("135"):
            VP_switch["VP_switch_mode"] = "时间"
            VP_switch["VP_switch_time"] = res_data.get("135")
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []

        for i in range(int(res_data.get("169"))):
            metering_rotation_sections.append(
                getConversion(TRANSFER_ROTATION_UNIT, rotation_unit, res_data.get(str(172+i*3))) if res_data.get(str(171+i*3)) else None)
            metering_back_pressure_sections.append(
                getConversion(TRANSFER_BACK_PRESSURE_UNIT, backpressure_unit, res_data.get(str(171+i*3))) if res_data.get(str(171+i*3)) else None)
            metering_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(173+i*3))) if res_data.get(str(173+i*3)) else None)

        metering_para = {
            "metering_stage": res_data.get("169"),
            "max_metering_stage_option": int(res_data.get("169")),
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("backpressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    # "pressure":  getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("186")) if res_data.get("186") else None,
                    # "velocity": getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get("187")) if res_data.get("187") else None,
                    # "time": res_data.get("189") if res_data.get("189") and float(res_data.get("189")) != 0 else None,
                    # "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("188")) if res_data.get("188") else None
                },
                {
                    "label": "储后",
                    "pressure": getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("190"),convert_type="decompressure_pressure_read") if res_data.get("190") else None,
                    # 2009是最大松退速度
                    "velocity": getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get("191"), convert_type="decompressure") if res_data.get("191") else None,
                    "time": res_data.get("193") if res_data.get("193") and float(res_data.get("193")) != 0 else None,
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("192") if res_data.get("192") else None)
                }
            ],
            "decompressure_mode_before_metering": "否",
            "decompressure_mode_after_metering": "距离",
            "metering_ending_position": None,
            # "metering_delay_time": round(getConversion(TRANSFER_TIME_UNIT, time_unit, res_data.get("170")),0) if res_data.get("170") else None
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        for i in range(int(res_data.get("225"))):
            temp_sections.append(
                res_data.get(str(228+i*2)))
        temp_para = {
            "barrel_temperature_stage": res_data.get("225"),
            "max_barrel_temperature_stage_option": int(res_data.get("225")),
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para

        process_detail = getProcessTechSixPart(process_detail, res_data, machine_info.get("agreement"))
        process_detail = getProcessTechSixEjector(process_detail, res_data, machine_info.get("agreement"))
        return {"process_detail":process_detail}
    except Exception as e:
        logging.error(e)
        logging.error(e.__traceback__)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


def loginYuzimi():
    # 获取加密后的密码
    # url = "http://kunpeng.yizumi.com:82/api/web/auth/password/encrypted"
    url = settings.MES + "/api/web/auth/password/encrypted"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    ret = json.loads(request_post(url, json.dumps({
        "username": "HK_TEST_admin",
        "rawPassword": "123456"
    },            
    ensure_ascii=False,
    cls=JsonEncoder,), headers, flag=0))

    # 登录
    if ret.get("code") == 200 and ret.get("msg") == "success":
        url = settings.MES + "/api/web/auth/login"
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        resp = json.loads(request_post(url, json.dumps(ret.get("data"),ensure_ascii=False,
        cls=JsonEncoder,), headers, flag=0))
        
        if resp.get("code") == 200 and resp.get("msg") == "success":
            return resp.get("data").get("token")


# 注塑机OPC变量表(20220513YZM).xlsx 1175 以国际单位进行传输
def setProcessTechSix(process_detail=None, precondition=None):
    try:
        global machine_info
        machine_info = get_machine(precondition.get("machine_id"))
        pressure_unit = process_detail.get(
            "inject_para").get("table_data")[0].get("unit")
        velocity_unit = process_detail.get(
            "inject_para").get("table_data")[1].get("unit")
        position_unit = process_detail.get(
            "inject_para").get("table_data")[2].get("unit")
        time_unit = process_detail.get("holding_para").get(
            "table_data")[2].get("unit")
        rotation_unit = process_detail.get(
            "metering_para").get("table_data")[1].get("unit")
        backpressure_unit = process_detail.get(
            "metering_para").get("table_data")[2].get("unit")
        # 温度段数不需要发,是默认的.
        temp = process_detail.get("temp_para").get("table_data")[0].get("sections")
        metering = process_detail.get("metering_para").get("table_data")
        holding = process_detail.get("holding_para").get("table_data")
        injection = process_detail.get("inject_para").get("table_data")
        process_dict = dict({                
            "228": temp[0] if len(temp) >=1 else None,  # 料筒温度1段实际值
            "230": temp[1] if len(temp) >=2 else None,  # 料筒温度2段实际值
            "232": temp[2] if len(temp) >=3 else None,  # 料筒温度3段实际值
            "234": temp[3] if len(temp) >=4 else None,  # 料筒温度4段实际值
            "236": temp[4] if len(temp) >=5 else None,  # 料筒温度5段实际值
            "169": process_detail.get("metering_para").get("metering_stage"),  # 熔胶段数
            "172": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[0]) if len(metering)>=1 and len(metering[1].get("sections")) >=1 else None,  # 储料一段速度
            "175": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[1]) if len(metering)>=1 and len(metering[1].get("sections")) >=2 else None,  # 储料二段速度
            "178": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[2]) if len(metering)>=1 and len(metering[1].get("sections")) >=3 else None,  # 储料三段速度
            "171": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[0],convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=1 else None,  # 储料一段背压
            "174": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[1],convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=2 else None,  # 储料二段背压
            "177": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[2],convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=3 else None,  # 储料三段背压
            "173": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[0]) if len(metering)>=3 and len(metering[1].get("sections")) >=1 else None,  # 储料一段位置
            "176": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[1]) if len(metering)>=3 and len(metering[1].get("sections")) >=2 else None,  # 储料二段位置
            "179": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[2]) if len(metering)>=3 and len(metering[1].get("sections")) >=3 else None,  # 储料三段位置
            "186": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure"), convert_type="decompression_pressure_write") if process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure") else None,  # 熔胶前松退压力
            "187": process_detail.get("metering_para").get("decompressure_paras")[0].get("velocity"),  # 熔胶前松退速度
            "188": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("decompressure_paras")[0].get("distance")),  # 熔胶前松退位置
            "189": process_detail.get("metering_para").get("decompressure_paras")[0].get("time"),  # 熔胶前松退时间
            "190": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure"), convert_type="decompression_pressure_write") if process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure") else None,  # 熔胶后松退压力
            "191": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("velocity"), covert_type="decompressure"),  # 熔胶后松退速度
            "192": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("distance")),  # 熔胶后松退位置
            "193": process_detail.get("metering_para").get("decompressure_paras")[1].get("time"),  # 熔胶后松退时间
            "137": process_detail.get("holding_para").get("holding_stage"),  # 保压段数
            "138": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[0], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 1 else None,  # 保压一段压力
            "141": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[1], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 2 else None,  # 保压二段压力
            "144": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[2], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 3 else None,  # 保压三段压力
            "139": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[0], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 1 else None,  # 保压一段速度
            "142": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[1], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 2 else None,  # 保压二段速度
            "145": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[2], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 3 else None,  # 保压三段速度
            "140": holding[2].get("sections")[0] if len(holding) >= 3 and len(holding[0].get("sections")) >= 1 else None,  # 保压一段时间
            "143": holding[2].get("sections")[1] if len(holding) >= 3 and len(holding[0].get("sections")) >= 2 else None,  # 保压二段时间
            "146": holding[2].get("sections")[2] if len(holding) >= 3 and len(holding[0].get("sections")) >= 3 else None,  # 保压三段时间
            "103": process_detail.get("inject_para").get("injection_stage"),  # 注射段数
            "107": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[0]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 1 else None,  # 注射一段位置
            "110": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[1]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 2 else None,  # 注射二段位置
            "113": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[2]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 3 else None,  # 注射三段位置
            "116": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[3]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 4 else None,  # 注射四段位置
            "119": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[4]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 5 else None,  # 注射五段位置
            "105": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[0], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 1 else None,  # 注射一段压力
            "108": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[1], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 2 else None,  # 注射二段压力
            "111": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[2], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 3 else None,  # 注射三段压力
            "114": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[3], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 4 else None,  # 注射四段压力
            "117": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[4], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 5 else None,  # 注射五段压力
            "106": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[0], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 1 else None,  # 注射一段速度
            "109": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[1], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 2 else None,  # 注射二段速度
            "112": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[2], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 3 else None,  # 注射三段速度
            "115": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[3], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 4 else None,  # 注射四段速度
            "118": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[4], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 5 else None,  # 注射五段速度
            "136": process_detail.get("VP_switch").get("VP_switch_position"),  # 保压切换
        })
        # 下发开合模,顶进顶退
        if(precondition.get("data_sources") != "工艺优化"):
            process_dict = setProcessTechSixPart(process_detail, machine_info.get("agreement"), process_dict)
            process_dict = setProcessTechSixEjector(process_detail, machine_info.get("agreement"), process_dict)
        new_process = {}
        # 下发之前,去掉空值
        for key in process_dict:
            if process_dict.get(key):
                new_process[key] = process_dict.get(key)
        json_data = json.dumps(new_process)
        #sn=GL5022219000151
        url = settings.MES+"/api/custom/equipment/craft/data/input/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=2"
        token = loginYuzimi()
        header_dict = {"Content-Type": "application/json; charset=UTF-8"}
        header_dict["Authorization"] = token
        res = None
        resp = requests.post(url, data=json_data, headers=header_dict)
        logging.info(f"返回值是多少{resp}")
        if resp.status_code == 200:
            res = json.loads(resp.text)
        if res and res.get("msg") == "会话已过期,请重新登录":
            return dict(result="outdated")
        else:
            return dict(result="success")
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


# 全电机 keba 映翰通
def getProcessTechSeven():
    global machine_info

    try:
        token = loginYuzimi()
        # url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn=FF200Z0047&tag=1"
        # url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn=FF160Z0127&tag=1"
        url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=1"
        
        header_dict = {"Authorization": token}

        res_data = None
        resp = requests.get(url, headers=header_dict)
        if resp.status_code == 200:
            res = json.loads(resp.text)
            if res.get("code") == 200 and res.get("msg") == "success":
                res_data = res.get("data")
        # res_data = dict({
        #     # "225": 4,  # 温度段数
			
        #     "474": 235,  # 料筒温度1段实际值
        #     "479": 235,  # 料筒温度2段实际值
        #     "484": 230,  # 料筒温度3段实际值
        #     "489": 225,  # 料筒温度4段实际值
        #     "495": 220,  # 料筒温度5段实际值
        #     "499": 215,  # 料筒温度6段实际值
        #     "504": 210,  # 料筒温度7段实际值

        #     "394": 1,  # 熔胶段数
        #     "412": 0.1, # 熔胶延时
        #     "396": 18.33,  # 储料一段速度
        #     "399": 1,  # 储料二段速度
        #     "402": 1,  # 储料三段速度
        #     "405": 1,  # 储料四段速度
        #     "395": 10,  # 储料一段背压
        #     "398": 1,  # 储料二段背压
        #     "401": 1,  # 储料三段背压
        #     "404": 1,  # 储料四段背压
        #     "397": 76.97,  # 储料一段位置
        #     "400": 1,  # 储料二段位置
        #     "403": 1,  # 储料三段位置
        #     "406": 1,  # 储料四段位置

        #     # "186": 50,  # 熔胶前松退压力
        #     "392": 38.9,  # 熔胶前松退速度
        #     "393": 9.62,  # 熔胶前松退位置
        #     # "189": 0,  # 熔胶前松退时间
        #     # "190": 20,  # 熔胶后松退压力
        #     "408": 15.56,  # 熔胶后松退速度
        #     "409": 4.81,  # 熔胶后松退位置
        #     # "193": 1,  # 熔胶后松退时间

        #     "281": 1,  # 保压段数
        #     "282": 530.61,  # 保压一段压力
        #     "285": 35,  # 保压二段压力
        #     "288": 530.61,  # 保压三段压力
        #     "291": 66,  # 保压四段压力
        #     "294": 20,  # 保压五段压力
        #     "297": 20,  # 保压六段压力
        #     "300": 20,  # 保压七段压力
        #     "303": 20,  # 保压八段压力
        #     "306": 20,  # 保压九段压力
        #     "309": 20,  # 保压十段压力
        #     "283": 8,  # 保压一段速度
        #     "286": 8,  # 保压二段速度
        #     "289": 27.99,  # 保压三段速度
        #     "292": 8,  # 保压四段速度
        #     "295": 3,  # 保压五段速度
        #     "298": 8,  # 保压六段速度
        #     "301": 8,  # 保压七段速度
        #     "304": 27.99,  # 保压八段速度
        #     "307": 8,  # 保压九段速度
        #     "310": 3,  # 保压十段速度
        #     "284": 10,  # 保压一段时间
        #     "287": 2,  # 保压二段时间
        #     "290": 1,  # 保压三段时间
        #     "293": 37.77,  # 保压四段时间
        #     "296": 20,  # 保压五段时间
        #     "299": 10,  # 保压六段时间
        #     "302": 2,  # 保压七段时间
        #     "305": 1,  # 保压八段时间
        #     "308": 37.77,  # 保压九段时间
        #     "311": 20,  # 保压十段时间

        #     "249": 1,  # 注射段数
        #     "253": 75,  # 注射一段位置
        #     "256": 65,  # 注射二段位置
        #     "259": 50,  # 注射三段位置
        #     "262": 46,  # 注射四段位置
        #     "264": 42,  # 注射五段位置
        #     "268": 40,  # 注射六段位置
        #     "271": 50,  # 注射七段位置
        #     "274": 46,  # 注射八段位置
        #     "277": 42,  # 注射九段位置
        #     "280": 40,  # 注射十段位置
        #     "251": 95,  # 注射一段压力
        #     "254": 70,  # 注射二段压力
        #     "257": 98,  # 注射三段压力
        #     "260": 95,  # 注射四段压力
        #     "263": 85,  # 注射五段压力
        #     "266": 50,  # 注射六段压力
        #     "269": 98,  # 注射七段压力
        #     "272": 95,  # 注射八段压力
        #     "275": 85,  # 注射九段压力
        #     "278": 50,  # 注射十段压力
        #     "252": 55.97,  # 注射一段速度			
        #     "255": 9,  # 注射二段速度
        #     "258": 38,  # 注射三段速度
        #     "261": 25,  # 注射四段速度
        #     "264": 12,  # 注射五段速度
        #     "267": 6,  # 注射六段速度
        #     "270": 38,  # 注射七段速度
        #     "273": 25,  # 注射八段速度
        #     "276": 12,  # 注射九段速度
        #     "279": 6,  # 注射十段速度

        #     "317": 40,  # 设定切换时间
        #     "320": 40,  # 实际切换位置
        #     "322": 40,  # 实际切换压力
        # })

        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        pressure_unit = machine_info.get("pressure_unit")
        velocity_unit = machine_info.get("velocity_unit")
        position_unit = machine_info.get("position_unit")
        time_unit = machine_info.get("time_unit")
        rotation_unit = machine_info.get("screw_rotation_unit")
        backpressure_unit = machine_info.get("backpressure_unit")
        temp_unit = machine_info.get("temperature_unit")
        for i in range(int(res_data.get("249"))):
            injection_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(251+i*3)), convert_type="injection_pressure_read") if res_data.get(str(251+i*3)) else None)
            injection_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(252+i*3)), convert_type="injection") if res_data.get(str(252+i*3)) else None)
            injection_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(253+i*3))) if res_data.get(str(253+i*3)) else None)

        inject_para = {
            "injection_stage": res_data.get("249"),
            "max_injection_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            "cooling_time": res_data.get("314"),
            "injection_delay_time":res_data.get("312"),
            "injection_time":round(float(res_data.get("317")), 2) if res_data.get("317") else None
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(int(res_data.get("281"))):
            holding_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(282+i*3)), convert_type="holding_pressure_read") if res_data.get(str(282+i*3)) else None)
            holding_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(283+i*3)), convert_type="holding") if res_data.get(str(283+i*3)) else None)
            holding_time_sections.append(res_data.get(
                str(284+i*3)) if res_data.get(str(284+i*3)) else None)

        holding_para = {
            "holding_stage": res_data.get("281"),
            "max_holding_stage_option": 5,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("319"):
            VP_switch["VP_switch_mode"] = "位置"
            VP_switch["VP_switch_position"] = getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("319")) if res_data.get("319") else None
        if res_data.get("317"):
            # VP_switch["VP_switch_mode"] = "时间"
            VP_switch["VP_switch_time"] = round(float(res_data.get("317")), 2) if res_data.get("317") else None
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []

        for i in range(int(res_data.get("394"))):
            metering_rotation_sections.append(
                getConversion(TRANSFER_ROTATION_UNIT, rotation_unit, res_data.get(str(396+i*3))) if res_data.get(str(171+i*3)) else None)
            metering_back_pressure_sections.append(
                getConversion(TRANSFER_BACK_PRESSURE_UNIT, backpressure_unit, res_data.get(str(395+i*3))) if res_data.get(str(171+i*3)) else None)
            metering_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(397+i*3))) if res_data.get(str(173+i*3)) else None)

        metering_para = {
            "metering_stage": res_data.get("394"),
            "max_metering_stage_option": 4,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("backpressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    # "pressure":  getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("186")) if res_data.get("186") else None,
                    "velocity": getConversion(TRANSFER_DE_VELOCITY_UNIT, velocity_unit, res_data.get("392")) if res_data.get("392") else None,
                    # "time": res_data.get("189") if res_data.get("189") and float(res_data.get("189")) != 0 else None,
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("393")) if res_data.get("393") else None
                },
                {
                    "label": "储后",
                    # "pressure": getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("190")) if res_data.get("190") else None,
                    "velocity": getConversion(TRANSFER_DE_VELOCITY_UNIT, velocity_unit, res_data.get("408")) if res_data.get("408") else None,
                    # "time": res_data.get("193") if res_data.get("193") and float(res_data.get("193")) != 0 else None,
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("409") if res_data.get("409") else None)
                }
            ],
            "decompressure_mode_before_metering": "否",
            "decompressure_mode_after_metering": "距离",
            "metering_ending_position": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("250")) if res_data.get("250") else None,
            "metering_delay_time": getConversion(TRANSFER_TIME_UNIT, time_unit, res_data.get("412")) if res_data.get("412") else None
        }

        process_detail["metering_para"] = metering_para

        temp_sections = []
        for i in range(int(res_data.get("2044"))):
            temp_sections.append(
                getConversion(TRANSFER_TEMP_UNIT, temp_unit, res_data.get(str(474+i*5))))
        temp_para = {
            "barrel_temperature_stage": res_data.get("2044"),
            "max_barrel_temperature_stage_option": 10,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para
        process_detail = getProcessTechSixPart(process_detail, res_data, machine_info.get("agreement"))
        process_detail = getProcessTechSixEjector(process_detail, res_data, machine_info.get("agreement"))
        return {"process_detail":process_detail}
    except Exception as e:
        logging.error(e)
        logging.error(e.__traceback__)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")

# V/P切换方式: 0:时间 1:位置 2:压力
def getVPKey(label):
    mappings = {
        "时间":0,
        "位置":1,
        "压力":2,
    }
    return mappings.get(label)


# 前/后松退: 0:不启用 1:启用
def getDecompressureKey(label):
    mappings = {
        "距离":1,
        "时间":1,
        "否":0   # 全电 391 使用前松退
    }
    return mappings.get(label)


def get_decompression_velocity(data, index, velocity_unit):
    try:
        metering_para = data.get("metering_para", {})
        decompression_params = metering_para.get("decompressure_paras", [])
        
        if isinstance(decompression_params, list) and len(decompression_params) > index:
            param = decompression_params[index]
            velocity = param.get("velocity")
            if velocity:
                return getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, velocity, convert_type="decompressure")
        else:
            logging.warning("Decompression params list is empty or not a list.")
            return None
    except Exception as e:
        logging.error(f"Error accessing decomposition velocity: {e} 行号{e.__traceback__.tb_lineno}")
        return None


# 全电机 keba 映翰通
def setProcessTechSeven(process_detail=None, precondition=None):
    try:
        global machine_info

        pressure_unit = process_detail.get(
            "inject_para").get("table_data")[0].get("unit")
        velocity_unit = process_detail.get(
            "inject_para").get("table_data")[1].get("unit")
        position_unit = process_detail.get(
            "inject_para").get("table_data")[2].get("unit")
        time_unit = process_detail.get("holding_para").get(
            "table_data")[2].get("unit")
        rotation_unit = process_detail.get(
            "metering_para").get("table_data")[1].get("unit")
        backpressure_unit = process_detail.get(
            "metering_para").get("table_data")[2].get("unit")
        temp_unit = process_detail.get("temp_para").get("table_data")[0].get("unit")
        # 温度段数不需要发,是默认的.
        temp = process_detail.get("temp_para").get("table_data")[0].get("sections")
        metering = process_detail.get("metering_para").get("table_data")
        holding = process_detail.get("holding_para").get("table_data")
        injection = process_detail.get("inject_para").get("table_data")
        process_dict = dict({                
            "474": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[0]) if len(temp) >=1 and temp[0] else None,  # 料筒温度1段实际值
            "479": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[1]) if len(temp) >=2 and temp[1] else None,  # 料筒温度2段实际值
            "484": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[2]) if len(temp) >=3 and temp[2] else None,  # 料筒温度3段实际值
            "489": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[3]) if len(temp) >=4 and temp[3] else None,  # 料筒温度4段实际值
            "494": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[4]) if len(temp) >=5 and temp[4] else None,  # 料筒温度5段实际值
			"499": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[5]) if len(temp) >=6 and temp[5] else None,  # 料筒温度6段实际值
			"504": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[6]) if len(temp) >=7 and temp[6] else None,  # 料筒温度7段实际值
            "394": process_detail.get("metering_para").get("metering_stage"),  # 熔胶段数
            "396": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[0]) if len(metering)>=1 and len(metering[1].get("sections")) >=1 and metering[1].get("sections")[0] else None,  # 储料一段速度
            "399": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[1]) if len(metering)>=1 and len(metering[1].get("sections")) >=2 and metering[1].get("sections")[1] else None,  # 储料二段速度
            "402": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[2]) if len(metering)>=1 and len(metering[1].get("sections")) >=3 and metering[1].get("sections")[2] else None,  # 储料三段速度
            "405": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[3]) if len(metering)>=1 and len(metering[1].get("sections")) >=4 and metering[1].get("sections")[3] else None,  # 储料四段速度
            "395": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[0]) if len(metering)>=2 and len(metering[1].get("sections")) >=1 and metering[2].get("sections")[0] else None,  # 储料一段背压
            "398": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[1]) if len(metering)>=2 and len(metering[1].get("sections")) >=2 and metering[2].get("sections")[1] else None,  # 储料二段背压
            "401": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[2]) if len(metering)>=2 and len(metering[1].get("sections")) >=3 and metering[2].get("sections")[2] else None,  # 储料三段背压
            "404": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[3]) if len(metering)>=2 and len(metering[1].get("sections")) >=4 and metering[2].get("sections")[3] else None,  # 储料四段背压
            "397": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[0]) if len(metering)>=3 and len(metering[1].get("sections")) >=1 and metering[3].get("sections")[0] else None,  # 储料一段位置
            "400": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[1]) if len(metering)>=3 and len(metering[1].get("sections")) >=2 and metering[3].get("sections")[1] else None,  # 储料二段位置
            "403": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[2]) if len(metering)>=3 and len(metering[1].get("sections")) >=3 and metering[3].get("sections")[2] else None,  # 储料三段位置
            "406": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[3]) if len(metering)>=3 and len(metering[1].get("sections")) >=4 and metering[3].get("sections")[3] else None,  # 储料四段位置
            "186": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure")) if process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure") else None,  # 熔胶前松退压力

            "391": getDecompressureKey(process_detail.get("metering_para").get("decompressure_mode_before_metering")),
            "392": get_decompression_velocity(process_detail, 0, velocity_unit),  # 熔胶前松退速度
            "393": getConversion(position_unit, TRANSFER_POSITION_UNIT, decompression_params[0].get("distance")) if (decompression_params := process_detail.get("metering_para", {}).get("decompressure_paras", [])) and decompression_params and "distance" in decompression_params[0] and decompression_params[0].get("distance") is not None else None,   # 熔胶前松退位置
            "189": process_detail.get("metering_para").get("decompressure_paras")[0].get("time"),  # 熔胶前松退时间
            "190": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure")) if process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure") else None,  # 熔胶后松退压力
            "407": getDecompressureKey(process_detail.get("metering_para").get("decompressure_mode_after_metering")),
            "408": get_decompression_velocity(process_detail, 2, velocity_unit),  # 熔胶后松退速度
            "409": getConversion(position_unit, TRANSFER_POSITION_UNIT, decompression_params[1].get("distance")) if (decompression_params := process_detail.get("metering_para", {}).get("decompressure_paras", [])) and len(decompression_params) > 1 and "distance" in decompression_params[1] and decompression_params[1].get("distance") is not None else None,  # 熔胶后松退位置
            "410": process_detail.get("metering_para").get("decompressure_paras")[1].get("time"),  # 熔胶后松退时间
            "412": process_detail.get("metering_para").get("metering_delay_time"),  # 熔胶延时  
            "281": process_detail.get("holding_para").get("holding_stage"),  # 保压段数
            "282": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[0], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 1 and holding[0].get("sections")[0] else None,  # 保压一段压力
            "285": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[1], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 2 and holding[0].get("sections")[1] else None,  # 保压二段压力
            "288": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[2], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 3 and holding[0].get("sections")[2] else None,  # 保压三段压力
            "291": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[3], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 4 and holding[0].get("sections")[3] else None,  # 保压四段压力
            "294": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[4], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 5 and holding[0].get("sections")[4] else None,  # 保压五段压力
            "297": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[5], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 6 and holding[0].get("sections")[5] else None,  # 保压六段压力
            "300": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[6], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 7 and holding[0].get("sections")[6] else None,  # 保压七段压力
            "303": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[7], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 8 and holding[0].get("sections")[7] else None,  # 保压八段压力
            "306": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[8], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 9 and holding[0].get("sections")[8] else None,  # 保压九段压力
            "309": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[9], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 10 and holding[0].get("sections")[9] else None,  # 保压十段压力
            "283": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[0], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 1 and holding[1].get("sections")[0] else None,  # 保压一段速度
            "286": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[1], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 2 and holding[1].get("sections")[1] else None,  # 保压二段速度
            "289": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[2], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 3 and holding[1].get("sections")[2] else None,  # 保压三段速度
            "292": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[3], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 4 and holding[1].get("sections")[3] else None,  # 保压四段速度
            "295": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[4], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 5 and holding[1].get("sections")[4] else None,  # 保压五段速度
            "298": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[5], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 6 and holding[1].get("sections")[5] else None,  # 保压六段速度
            "301": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[6], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 7 and holding[1].get("sections")[6] else None,  # 保压七段速度
            "304": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[7], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 8 and holding[1].get("sections")[7] else None,  # 保压八段速度
            "307": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[8], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 9 and holding[1].get("sections")[8] else None,  # 保压九段速度
            "310": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[9], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 10 and holding[1].get("sections")[9]	else None,  # 保压十段速度
            "284": holding[2].get("sections")[0] if len(holding) >= 3 and len(holding[0].get("sections")) >= 1 else None,  # 保压一段时间
            "287": holding[2].get("sections")[1] if len(holding) >= 3 and len(holding[0].get("sections")) >= 2 else None,  # 保压二段时间
            "290": holding[2].get("sections")[2] if len(holding) >= 3 and len(holding[0].get("sections")) >= 3 else None,  # 保压三段时间
			"293": holding[2].get("sections")[3] if len(holding) >= 3 and len(holding[0].get("sections")) >= 4 else None,  # 保压四段时间
            "296": holding[2].get("sections")[4] if len(holding) >= 3 and len(holding[0].get("sections")) >= 5 else None,  # 保压五段时间
            "299": holding[2].get("sections")[5] if len(holding) >= 3 and len(holding[0].get("sections")) >= 6 else None,  # 保压六段时间
            "302": holding[2].get("sections")[6] if len(holding) >= 3 and len(holding[0].get("sections")) >= 7 else None,  # 保压七段时间
			"305": holding[2].get("sections")[7] if len(holding) >= 3 and len(holding[0].get("sections")) >= 8 else None,  # 保压八段时间
            "308": holding[2].get("sections")[8] if len(holding) >= 3 and len(holding[0].get("sections")) >= 9 else None,  # 保压九段时间
            "311": holding[2].get("sections")[9] if len(holding) >= 3 and len(holding[0].get("sections")) >= 10 else None,  # 保压十段时间
            "249": process_detail.get("inject_para").get("injection_stage"),  # 注射段数
            "253": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[0]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 1 and injection[2].get("sections")[0] is not None else None,  # 注射一段位置
            "256": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[1]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 2 and injection[2].get("sections")[1] is not None else None,  # 注射二段位置
            "259": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[2]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 3 and injection[2].get("sections")[2] is not None else None,  # 注射三段位置
            "262": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[3]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 4 and injection[2].get("sections")[3] is not None else None,  # 注射四段位置
            "264": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[4]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 5 and injection[2].get("sections")[4] is not None else None,  # 注射五段位置
            "268": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[5]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 6 and injection[2].get("sections")[5] is not None else None,  # 注射六段位置
            "271": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[6]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 7 and injection[2].get("sections")[6] is not None else None,  # 注射七段位置
            "274": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[7]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 8 and injection[2].get("sections")[7] is not None else None,  # 注射八段位置
            "277": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[8]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 9 and injection[2].get("sections")[8] is not None else None,  # 注射九段位置
            "280": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[9]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 10 and injection[2].get("sections")[9] is not None else None,  # 注射十段位置
            "251": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[0], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 1 and injection[0].get("sections")[0] is not None else None,  # 注射一段压力
            "254": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[1], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 2 and injection[0].get("sections")[1] is not None else None,  # 注射二段压力
            "257": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[2], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 3 and injection[0].get("sections")[2] is not None else None,  # 注射三段压力
            "260": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[3], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 4 and injection[0].get("sections")[3] is not None else None,  # 注射四段压力
            "263": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[4], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 5 and injection[0].get("sections")[4] is not None else None,  # 注射五段压力
            "266": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[5], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 6 and injection[0].get("sections")[5] is not None else None,  # 注射六段压力
            "269": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[6], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 7 and injection[0].get("sections")[6] is not None else None,  # 注射七段压力
            "272": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[7], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 8 and injection[0].get("sections")[7] is not None else None,  # 注射八段压力
            "275": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[8], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 9 and injection[0].get("sections")[8] is not None else None,  # 注射九段压力
            "278": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[9], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 10 and injection[0].get("sections")[9] is not None else None,  # 注射十段压力
            "252": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[0], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 1 and injection[1].get("sections")[0] is not None else None,  # 注射一段速度
            "255": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[1], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 2 and injection[1].get("sections")[1] is not None else None,  # 注射二段速度
            "258": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[2], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 3 and injection[1].get("sections")[2] is not None else None,  # 注射三段速度
            "261": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[3], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 4 and injection[1].get("sections")[3] is not None else None,  # 注射四段速度
            "264": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[4], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 5 and injection[1].get("sections")[4] is not None else None,  # 注射五段速度
            "267": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[5], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 6 and injection[1].get("sections")[5] is not None else None,  # 注射六段速度
            "270": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[6], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 7 and injection[1].get("sections")[6] is not None else None,  # 注射七段速度
            "273": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[7], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 8 and injection[1].get("sections")[7] is not None else None,  # 注射八段速度
            "276": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[8], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 9 and injection[1].get("sections")[8] is not None else None,  # 注射九段速度
            "279": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[9], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 10 and injection[1].get("sections")[9] is not None else None,  # 注射十段速度	
            "312": process_detail.get("inject_para").get("injection_delay_time"),
            "314": process_detail.get("inject_para").get("cooling_time"),
            "316": getVPKey(process_detail.get("VP_switch").get("VP_switch_mode")),
            # "317": process_detail.get("VP_switch").get("VP_switch_time"),  # 保压切换时间
            "317": process_detail.get("inject_para").get("injection_time"),  # 注射时间
            "319": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("VP_switch").get("VP_switch_position")) if process_detail.get("VP_switch").get("VP_switch_position") is not None else None,  # 保压切换位置
            "321": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("VP_switch").get("VP_switch_pressure")) if process_detail.get("VP_switch").get("VP_switch_pressure") is not None else None,  # 保压切换压力
        })

        # 下发开合模,顶进顶退
        if(precondition.get("data_sources") != "工艺优化"):
            process_dict = setProcessTechSixPart(process_detail, machine_info.get("agreement"), process_dict)
            process_dict = setProcessTechSixEjector(process_detail, machine_info.get("agreement"), process_dict)
        new_process = {}
        # 下发之前,去掉空值
        new_process = {key: value for key, value in process_dict.items() if value is not None}
        logging.info(f"下发之前,检查参数是否正确{new_process}")
        json_data = json.dumps(new_process)
        # sn=FF200Z0047
        url = settings.MES+"/api/custom/equipment/craft/data/input/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=2"
        token = loginYuzimi()
        header_dict = {"Content-Type": "application/json; charset=UTF-8"}
        header_dict["Authorization"] = token
        res = None
        resp = requests.post(url, data=json_data, headers=header_dict)
        if resp.status_code == 200:
            res = json.loads(resp.text)
        if res and res.get("msg") == "会话已过期,请重新登录":
            return dict(result="outdated")
        else:
            return dict(result="success")
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


# 开合模:包括盟立
def getProcessTechSixPart(process_detail, res_data, agreement):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        if agreement == "盟立":
            TRANSFER_OC_PRESSURE_UNIT = machine_info.get("oc_pressure_unit") if machine_info.get("oc_pressure_unit") else "bar"  # 开合模和顶进顶退
            TRANSFER_OC_VELOCITY_UNIT = machine_info.get("oc_velocity_unit") if machine_info.get("oc_velocity_unit") else "mm/s" # 或者"%"
        open_pressure_sections = []
        open_velocity_sections = []
        open_position_sections = []
        clamp_pressure_sections = []
        clamp_velocity_sections = []
        clamp_position_sections = []
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")
        # position_unit = machine_info.get("oc_position_unit")
        open_stage = 5
        if agreement in ["keba映翰通", "keba1175"]:
            open_stage = int(res_data.get(PROCESS.get(agreement).get("mold_opening_stage")))
        elif agreement in ["盟立"]:
            open_stage = 5
        for i in range(open_stage):
            if agreement in ["keba1175", "盟立"]:
                open_pressure_sections.append(
                    getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get(PROCESS.get(agreement).get("mold_opening_pressure")[i]),convert_type="origin_press") if res_data.get(PROCESS.get(agreement).get("mold_opening_pressure")[i]) else None)
            open_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get(PROCESS.get(agreement).get("mold_opening_velocity")[i]), convert_type="opening") if res_data.get(PROCESS.get(agreement).get("mold_opening_velocity")[i]) else None)
            open_position_sections.append(
                res_data.get(PROCESS.get(agreement).get("mold_opening_position")[i]))
        # keba映翰通,合模段数5段,模保单独赋值,前面减1
        clamp_stage = 5
        if agreement in ["keba1175"]:
            clamp_stage = int(res_data.get(PROCESS.get(agreement).get("mold_clamping_stage")))
        if agreement in ["keba映翰通"]:
            clamp_stage = int(res_data.get(PROCESS.get(agreement).get("mold_opening_stage")))-1
        elif agreement in ["盟立"]:
            clamp_stage = 5
        for i in range(clamp_stage):
            if agreement in ["keba1175","盟立"]:
                clamp_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get(PROCESS.get(agreement).get("mold_clamping_pressure")[i]),convert_type="origin_press") if res_data.get(PROCESS.get(agreement).get("mold_clamping_pressure")[i]) else None)
            clamp_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get(PROCESS.get(agreement).get("mold_clamping_velocity")[i]), convert_type="clamping") if res_data.get(PROCESS.get(agreement).get("mold_clamping_velocity")[i]) else None)
   
            clamp_position_sections.append(
                res_data.get(PROCESS.get(agreement).get("mold_clamping_position")[i]))
        # 模保
        if agreement == "keba映翰通":
            clamp_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get(PROCESS.get(agreement).get("mold_protect_velocity")), convert_type="clamping") if res_data.get(PROCESS.get(agreement).get("mold_protect_velocity")) else None)
            clamp_position_sections.append(res_data.get(PROCESS.get(agreement).get("mold_protect_position")))

        mold_opening = {
            "mold_opening_stage": open_stage,
            "max_mold_opening_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": open_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": open_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": open_position_sections}
            ],
        }
        mold_clamping = {
            "mold_clamping_stage": clamp_stage +1 if agreement in ["keba映翰通"] else clamp_stage,
            "max_mold_clamping_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": clamp_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": clamp_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": clamp_position_sections}
            ],
        }
        opening_and_clamping_mold_setting = {
            "mold_opening": mold_opening,
            "mold_clamping": mold_clamping,
        }
        process_detail["opening_and_clamping_mold_setting"] = opening_and_clamping_mold_setting
        return process_detail
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


# 顶针:不包括盟立
def getProcessTechSixEjector(process_detail, res_data, agreement):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        ejector_forward_pressure_sections = []
        ejector_forward_velocity_sections = []
        ejector_forward_position_sections = []
        ejector_backward_pressure_sections = []
        ejector_backward_velocity_sections = []
        ejector_backward_position_sections = []
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")
        # position_unit = machine_info.get("oc_position_unit")
        for i in range(int(res_data.get(PROCESS.get(agreement).get("ejector_forward_stage")))):
            ejector_forward_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get(PROCESS.get(agreement).get("ejector_forward_pressure")[i]),convert_type="origin_press") if res_data.get(PROCESS.get(agreement).get("ejector_forward_pressure")[i]) else None)
            # keba映翰通没有顶进最大速度,暂时用顶退最大速度代替.如果从注塑机上查到,录入数据库,可以直接读取数据库中的参数
            ejector_forward_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get(PROCESS.get(agreement).get("ejector_forward_velocity")[i]),convert_type="forward") if res_data.get(PROCESS.get(agreement).get("ejector_forward_velocity")[i]) else None)
            ejector_forward_position_sections.append(
                res_data.get(PROCESS.get(agreement).get("ejector_forward_position")[i]))

        for i in range(int(res_data.get(PROCESS.get(agreement).get("ejector_backward_stage")))):
            ejector_backward_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get(PROCESS.get(agreement).get("ejector_backward_pressure")[i]),convert_type="origin_press") if res_data.get(PROCESS.get(agreement).get("ejector_backward_pressure")[i]) else None)
            ejector_backward_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get(PROCESS.get(agreement).get("ejector_backward_velocity")[i]),convert_type="backward") if res_data.get(PROCESS.get(agreement).get("ejector_backward_velocity")[i]) else None)
            ejector_backward_position_sections.append(
                res_data.get(PROCESS.get(agreement).get("ejector_backward_position")[i]))

        ejector_forward = {
            "ejector_forward_stage": res_data.get(PROCESS.get(agreement).get("ejector_forward_stage")),
            "max_ejector_forward_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": ejector_forward_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": ejector_forward_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": ejector_forward_position_sections}
            ],
        }
        ejector_backward = {
            "ejector_backward_stage": res_data.get(PROCESS.get(agreement).get("ejector_backward_stage")),
            "max_ejector_backward_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": ejector_backward_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": ejector_backward_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": ejector_backward_position_sections}
            ],
        }
        ejector_setting = {
            "ejector_forward": ejector_forward,
            "ejector_backward": ejector_backward,
        }
        process_detail["ejector_setting"] = ejector_setting
        return process_detail
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)
        

# 包括盟立
def setProcessTechSixPart(process_detail, agreement, process_dict):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        if agreement == "盟立":
            TRANSFER_OC_PRESSURE_UNIT = machine_info.get("oc_pressure_unit") if machine_info.get("oc_pressure_unit") else "bar"  # 开合模和顶进顶退
            TRANSFER_OC_VELOCITY_UNIT = machine_info.get("oc_velocity_unit") if machine_info.get("oc_velocity_unit") else "mm/s" # 或者"%"
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")
        mold_opening = process_detail.get("opening_and_clamping_mold_setting").get("mold_opening").get("table_data")
        mold_clamping = process_detail.get("opening_and_clamping_mold_setting").get("mold_clamping").get("table_data")
        for i in range(min(6,process_detail.get("opening_and_clamping_mold_setting").get("mold_opening").get("mold_opening_stage"))):
            if agreement == "盟立":
                process_dict[PROCESS.get(agreement).get("mold_opening_pressure")[i]] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, mold_opening[0].get("sections")[i],convert_type="origin_press") if len(mold_opening) >=1 and len(mold_opening[0].get("sections"))>i and mold_opening[0].get("sections")[i] else None
            process_dict[PROCESS.get(agreement).get("mold_opening_velocity")[i]] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, mold_opening[1].get("sections")[i], convert_type="opening") if len(mold_opening) >=2 and len(mold_opening[1].get("sections"))>i and mold_opening[1].get("sections")[i] else None
            process_dict[PROCESS.get(agreement).get("mold_opening_position")[i]] = mold_opening[2].get("sections")[i] if len(mold_opening) >=3 and len(mold_opening[2].get("sections"))>i and mold_opening[2].get("sections")[i] else None
        # keba映翰通,模保在合模段数中.
        clamping_stage = min(6,process_detail.get("opening_and_clamping_mold_setting").get("mold_clamping").get("mold_clamping_stage"))
        for i in range(clamping_stage - 1):
            if agreement == "盟立":
                process_dict[PROCESS.get(agreement).get("mold_clamping_pressure")[i]] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, mold_clamping[0].get("sections")[i],convert_type="origin_press") if len(mold_clamping) >=1 and len(mold_clamping[0].get("sections"))>i and mold_clamping[0].get("sections")[i] else None
            process_dict[PROCESS.get(agreement).get("mold_clamping_velocity")[i]] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, mold_clamping[1].get("sections")[i], convert_type="clamping") if len(mold_clamping) >=2 and len(mold_clamping[1].get("sections"))>i and mold_clamping[1].get("sections")[i] else None
            process_dict[PROCESS.get(agreement).get("mold_clamping_position")[i]] = mold_clamping[2].get("sections")[i] if len(mold_clamping) >=3 and len(mold_clamping[2].get("sections"))>i and mold_clamping[2].get("sections")[i] else None
        # 模保
        if agreement == "keba映翰通":
            process_dict[PROCESS.get(agreement).get("mold_protect_velocity")] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, mold_clamping[1].get("sections")[clamping_stage-1], convert_type="clamping") if len(mold_clamping) >=2 and len(mold_clamping[1].get("sections"))>clamping_stage-1 else None
            process_dict[PROCESS.get(agreement).get("mold_protect_position")] = mold_clamping[2].get("sections")[clamping_stage-1] if len(mold_clamping) >=3 and len(mold_clamping[2].get("sections"))>clamping_stage-1 else None
        if agreement != "盟立":
            process_dict[PROCESS.get(agreement).get("mold_clamping_stage")] = clamping_stage
            process_dict[PROCESS.get(agreement).get("mold_opening_stage")] = min(6,process_detail.get("opening_and_clamping_mold_setting").get("mold_opening").get("mold_opening_stage"))
        return process_dict
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


# 不包括盟立
def setProcessTechSixEjector(process_detail, agreement, process_dict):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")        
        ejector_forward = process_detail.get("ejector_setting").get("ejector_forward").get("table_data")
        ejector_backward = process_detail.get("ejector_setting").get("ejector_backward").get("table_data")
        for i in range(min(3,process_detail.get("ejector_setting").get("ejector_forward").get("ejector_forward_stage"))):
            if agreement != "keba映翰通":
                process_dict[PROCESS.get(agreement).get("ejector_forward_pressure")[i]] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, ejector_forward[0].get("sections")[i],convert_type="origin_press") if len(ejector_forward) >=1 and len(ejector_forward[0].get("sections"))>=i else None

            process_dict[PROCESS.get(agreement).get("ejector_forward_velocity")[i]] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, ejector_forward[1].get("sections")[i], convert_type="forward") if len(ejector_forward) >=2 and len(ejector_forward[1].get("sections"))>=i else None
            process_dict[PROCESS.get(agreement).get("ejector_forward_position")[i]] = ejector_forward[2].get("sections")[i] if len(ejector_forward) >=3 and len(ejector_forward[2].get("sections"))>=i else None
        for i in range(min(3,process_detail.get("ejector_setting").get("ejector_backward").get("ejector_backward_stage"))):
            if agreement != "keba映翰通":
                process_dict[PROCESS.get(agreement).get("ejector_backward_pressure")[i]] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, ejector_backward[0].get("sections")[i],convert_type="origin_press") if len(ejector_backward) >=1 and len(ejector_backward[0].get("sections"))>=i else None
            
            process_dict[PROCESS.get(agreement).get("ejector_backward_velocity")[i]] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, ejector_backward[1].get("sections")[i], convert_type="backward") if len(ejector_backward) >=2 and len(ejector_backward[1].get("sections"))>=i else None
            process_dict[PROCESS.get(agreement).get("ejector_backward_position")[i]] = ejector_backward[2].get("sections")[i] if len(ejector_backward) >=3 and len(ejector_backward[2].get("sections"))>=i else None
        process_dict[PROCESS.get(agreement).get("ejector_forward_stage")] = min(3,process_detail.get("ejector_setting").get("ejector_forward").get("ejector_forward_stage"))
        process_dict[PROCESS.get(agreement).get("ejector_backward_stage")] = min(3,process_detail.get("ejector_setting").get("ejector_backward").get("ejector_backward_stage"))
        return process_dict
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


# 盟立
def getProcessTechEight():
    global machine_info
    # 当前盟立不进行参数转换,按照界面单位来
    TRANSFER_PRESSURE_UNIT = machine_info.get("pressure_unit") if machine_info.get("pressure_unit") else "bar"
    TRANSFER_BACK_PRESSURE_UNIT = machine_info.get("backpressure_unit") if machine_info.get("backpressure_unit") else "bar"
    # TRANSFER_TIME_UNIT = "s"
    TRANSFER_POSITION_UNIT = machine_info.get("position_unit") if machine_info.get("position_unit") else "mm"
    TRANSFER_VELOCITY_UNIT = machine_info.get("velocity_unit") if machine_info.get("velocity_unit") else "%"
    TRANSFER_ROTATION_UNIT = machine_info.get("screw_rotation_unit") if machine_info.get("screw_rotation_unit") else "rpm"
    TRANSFER_DE_VELOCITY_UNIT = machine_info.get("velocity_unit") if machine_info.get("velocity_unit") else "%"  # 松退速度

    TRANSFER_TEMP_UNIT = "℃"
    try:
        token = loginYuzimi()
        # url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn=mirleTest&tag=1"
        url = settings.MES+"/api/custom/equipment/craft/data/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=1"
        header_dict = {"Authorization": token}

        res_data = None
        resp = requests.get(url, headers=header_dict)
        if resp.status_code == 200:
            res = json.loads(resp.text)
            if res.get("code") == 200 and res.get("msg") == "success":
                res_data = res.get("data")
                logging.info(res_data)
        # res_data = dict({
        #     # "225": 4,  # 温度段数
			
        #     "71": 235,  # 料筒温度1段实际值
        #     "73": 235,  # 料筒温度2段实际值
        #     "75": 230,  # 料筒温度3段实际值
        #     "77": 225,  # 料筒温度4段实际值
        #     "79": 220,  # 料筒温度5段实际值
        #     "81": 215,  # 料筒温度6段实际值
        #     "83": 210,  # 料筒温度7段实际值
        #     "85": 235,  # 料筒温度8段实际值
        #     "87": 235,  # 料筒温度9段实际值
        #     "89": 230,  # 料筒温度10段实际值
        #     "91": 225,  # 料筒温度11段实际值
        #     "93": 220,  # 料筒温度12段实际值
        #     "95": 215,  # 料筒温度13段实际值
        #     "97": 210,  # 料筒温度14段实际值
        #     "99": 215,  # 料筒温度15段实际值
        #     "101": 210,  # 料筒温度16段实际值

        #     "133": 1,  # 熔胶段数
        #     "412": 0.1, # 熔胶延时
        #     "107": 76.97,  # 储料一段压力
        #     "111": 1,  # 储料二段压力
        #     "115": 1,  # 储料三段压力
        #     "119": 1,  # 储料四段压力
        #     "108": 18.33,  # 储料一段速度
        #     "112": 1,  # 储料二段速度
        #     "116": 1,  # 储料三段速度
        #     "120": 1,  # 储料四段速度
        #     "105": 10,  # 储料一段背压
        #     "109": 1,  # 储料二段背压
        #     "113": 1,  # 储料三段背压
        #     "117": 1,  # 储料四段背压
        #     "106": 76.97,  # 储料一段位置
        #     "110": 1,  # 储料二段位置
        #     "114": 1,  # 储料三段位置
        #     "118": 1,  # 储料四段位置

        #     "125":1, # 熔胶终点

        #     "453": 50,  # 熔胶前松退压力
        #     "454": 38.9,  # 熔胶前松退速度
        #     "452": 9.62,  # 熔胶前松退位置
        #     # "189": 0,  # 熔胶前松退时间
        #     "485": 20,  # 熔胶后松退压力
        #     "486": 15.56,  # 熔胶后松退速度
        #     "484": 4.81,  # 熔胶后松退位置
        #     # "193": 1,  # 熔胶后松退时间

        #     "273": 1,  # 保压段数
        #     "255": 530.61,  # 保压一段压力
        #     "258": 35,  # 保压二段压力
        #     "261": 530.61,  # 保压三段压力
        #     "264": 66,  # 保压四段压力
        #     "267": 20,  # 保压五段压力
        #     "270": 20,  # 保压六段压力

        #     "256": 8,  # 保压一段速度
        #     "259": 8,  # 保压二段速度
        #     "262": 27.99,  # 保压三段速度
        #     "265": 8,  # 保压四段速度
        #     "268": 3,  # 保压五段速度
        #     "271": 8,  # 保压六段速度

        #     "257": 10,  # 保压一段时间
        #     "260": 2,  # 保压二段时间
        #     "263": 1,  # 保压三段时间
        #     "266": 37.77,  # 保压四段时间
        #     "269": 20,  # 保压五段时间
        #     "272": 10,  # 保压六段时间

        #     "361": 1,  # 注射段数
        #     "328": 75,  # 注射一段位置
        #     "333": 65,  # 注射二段位置
        #     "338": 50,  # 注射三段位置
        #     "343": 46,  # 注射四段位置
        #     "348": 42,  # 注射五段位置
        #     "353": 40,  # 注射六段位置

        #     "329": 95,  # 注射一段压力
        #     "334": 70,  # 注射二段压力
        #     "339": 98,  # 注射三段压力
        #     "344": 95,  # 注射四段压力
        #     "349": 85,  # 注射五段压力
        #     "354": 50,  # 注射六段压力

        #     "330": 55.97,  # 注射一段速度			
        #     "335": 9,  # 注射二段速度
        #     "340": 38,  # 注射三段速度
        #     "345": 25,  # 注射四段速度
        #     "350": 12,  # 注射五段速度
        #     "355": 6,  # 注射六段速度

        #     "137":1, # 冷却时间

        #     "491": 40,  # 切保压模式
        #     "514": 40,  # 设定切换时间
        #     "512": 40,  # 实际切换位置
        #     "513": 40,  # 实际切换压力
        # })

        process_detail = {}
        injection_pressure_sections = []
        injection_velocity_sections = []
        injection_distance_sections = []
        pressure_unit = machine_info.get("pressure_unit")
        velocity_unit = machine_info.get("velocity_unit")
        position_unit = machine_info.get("position_unit")
        time_unit = machine_info.get("time_unit")
        rotation_unit = machine_info.get("screw_rotation_unit")
        backpressure_unit = machine_info.get("backpressure_unit")
        temp_unit = machine_info.get("temperature_unit")
        for i in range(int(res_data.get("361"))):
            injection_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(329+i*5)), convert_type="injection_pressure_read") if res_data.get(str(329+i*5)) else None)
            injection_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(330+i*5)), convert_type="injection") if res_data.get(str(330+i*5)) else None)
            injection_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(328+i*5))) if res_data.get(str(328+i*5)) else None)

        inject_para = {
            "injection_stage": res_data.get("361"),
            "max_injection_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": injection_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": injection_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": injection_distance_sections}
            ],
            "cooling_time": res_data.get("137"),
            "injection_time":round(float(res_data.get("364")), 2) if res_data.get("364") else None
        }
        process_detail["inject_para"] = inject_para

        holding_pressure_sections = []
        holding_velocity_sections = []
        holding_time_sections = []
        for i in range(int(res_data.get("273"))):
            holding_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(255+i*3)), convert_type="holding_pressure_read") if res_data.get(str(255+i*3)) else None)
            holding_velocity_sections.append(
                getConversion(TRANSFER_VELOCITY_UNIT, velocity_unit, res_data.get(str(256+i*3)), convert_type="holding") if res_data.get(str(256+i*3)) else None)
            holding_time_sections.append(res_data.get(
                str(257+i*3)) if res_data.get(str(257+i*3)) else None)

        holding_para = {
            "holding_stage": res_data.get("273"),
            "max_holding_stage_option": 6,
            "table_data":  [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": holding_pressure_sections},
                {"label": "速度", "unit": machine_info.get("velocity_unit"),
                    "sections": holding_velocity_sections},
                {"label": "时间", "unit": machine_info.get("time_unit"), "sections": holding_time_sections}
            ]
        }
        process_detail["holding_para"] = holding_para

        VP_switch = {}
        if res_data.get("491") == "0":
            VP_switch["VP_switch_mode"] = "位置"
        if res_data.get("491") == "1":
            VP_switch["VP_switch_mode"] = "时间"  
        if res_data.get("491") == "2":
            VP_switch["VP_switch_mode"] = "时间&位置"
        if res_data.get("512"):
            # VP_switch["VP_switch_mode"] = "位置"
            VP_switch["VP_switch_position"] = getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("512")) if res_data.get("512") else None
        if res_data.get("514"):
            # VP_switch["VP_switch_mode"] = "时间"
            VP_switch["VP_switch_time"] = round(float(res_data.get("514")), 2) if res_data.get("514") else None
        if res_data.get("513"):
            # VP_switch["VP_switch_mode"] = "压力"
            VP_switch["VP_switch_pressure"] = getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("513"), convert_type="injection_pressure_read") if res_data.get("513") else None
        process_detail["VP_switch"] = VP_switch

        metering_pressure_sections = []
        metering_rotation_sections = []
        metering_back_pressure_sections = []
        metering_distance_sections = []

        for i in range(int(res_data.get("133"))):
            metering_rotation_sections.append(
                getConversion(TRANSFER_ROTATION_UNIT, rotation_unit, res_data.get(str(108+i*4))) if res_data.get(str(108+i*4)) else None)
            metering_back_pressure_sections.append(
                getConversion(TRANSFER_BACK_PRESSURE_UNIT, backpressure_unit, res_data.get(str(105+i*4))) if res_data.get(str(105+i*4)) else None)
            metering_distance_sections.append(
                getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get(str(106+i*4))) if res_data.get(str(106+i*4)) else None)
            metering_pressure_sections.append(
                getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get(str(107+i*4))) if res_data.get(str(107+i*4)) else None)

        metering_para = {
            "metering_stage": res_data.get("133"),
            "max_metering_stage_option": 4,
            "table_data": [
                {"label": "压力", "unit": machine_info.get("pressure_unit"),
                    "sections": metering_pressure_sections},
                {"label": "螺杆转速", "unit": machine_info.get("screw_rotation_unit"),
                 "sections": metering_rotation_sections},
                {"label": "背压", "unit": machine_info.get("backpressure_unit"),
                 "sections": metering_back_pressure_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": metering_distance_sections}],
            "decompressure_paras": [
                {
                    "label": "储前",
                    "pressure":  getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("453"),convert_type="decompressure_pressure_read") if res_data.get("453") else None,
                    "velocity": getConversion(TRANSFER_DE_VELOCITY_UNIT, velocity_unit, res_data.get("454"), convert_type="decompressure") if res_data.get("454") else None,
                    # "time": res_data.get("189") if res_data.get("189") and float(res_data.get("189")) != 0 else None,
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("452")) if res_data.get("452") else None
                },
                {
                    "label": "储后",
                    "pressure": getConversion(TRANSFER_PRESSURE_UNIT, pressure_unit, res_data.get("485"),convert_type="decompressure_pressure_read") if res_data.get("485") else None,
                    "velocity": getConversion(TRANSFER_DE_VELOCITY_UNIT, velocity_unit, res_data.get("486"), convert_type="decompressure") if res_data.get("486") else None,
                    # "time": res_data.get("193") if res_data.get("193") and float(res_data.get("193")) != 0 else None,
                    "distance": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("484") if res_data.get("484") else None)
                }
            ],
            "decompressure_mode_before_metering": "否",
            "decompressure_mode_after_metering": "距离",
            "metering_ending_position": getConversion(TRANSFER_POSITION_UNIT, position_unit, res_data.get("125")) if res_data.get("125") else None,
            # "metering_delay_time": getConversion(TRANSFER_TIME_UNIT, time_unit, res_data.get("412")) if res_data.get("412") else None
        }
        process_detail["metering_para"] = metering_para

        temp_sections = []
        for i in range(6):
            temp_sections.append(
                getConversion(TRANSFER_TEMP_UNIT, temp_unit, res_data.get(str(71+i*2))))
        temp_para = {
            "barrel_temperature_stage":6,
            "max_barrel_temperature_stage_option": 16,
            "table_data": [{"label": "温度", "unit": "℃", "sections": temp_sections}],
        }
        process_detail["temp_para"] = temp_para
        process_detail = getProcessTechSixPart(process_detail, res_data, machine_info.get("agreement"))
        process_detail = getProcessTechEightEjector(process_detail, res_data, machine_info.get("agreement"))
        return {"process_detail":process_detail}
    except Exception as e:
        logging.error(e)
        logging.error(e.__traceback__)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


# 盟立
def setProcessTechEight(process_detail=None, precondition=None):
    try:
        # 当前盟立不进行参数转换,按照界面单位来
        global machine_info
        TRANSFER_PRESSURE_UNIT = machine_info.get("pressure_unit") if machine_info.get("pressure_unit") else "bar"
        TRANSFER_BACK_PRESSURE_UNIT = machine_info.get("backpressure_unit") if machine_info.get("backpressure_unit") else "bar"
        # TRANSFER_TIME_UNIT = "s"
        TRANSFER_POSITION_UNIT = machine_info.get("position_unit") if machine_info.get("position_unit") else "mm"
        TRANSFER_VELOCITY_UNIT = machine_info.get("velocity_unit") if machine_info.get("velocity_unit") else "%"
        TRANSFER_ROTATION_UNIT = machine_info.get("screw_rotation_unit") if machine_info.get("screw_rotation_unit") else "rpm"
        TRANSFER_DE_VELOCITY_UNIT = machine_info.get("velocity_unit") if machine_info.get("velocity_unit") else "%"  # 松退速度

        pressure_unit = process_detail.get(
            "inject_para").get("table_data")[0].get("unit")
        velocity_unit = process_detail.get(
            "inject_para").get("table_data")[1].get("unit")
        position_unit = process_detail.get(
            "inject_para").get("table_data")[2].get("unit")
        time_unit = process_detail.get("holding_para").get(
            "table_data")[2].get("unit")
        rotation_unit = process_detail.get(
            "metering_para").get("table_data")[1].get("unit")
        backpressure_unit = process_detail.get(
            "metering_para").get("table_data")[2].get("unit")
        temp_unit = process_detail.get("temp_para").get("table_data")[0].get("unit")
        # 温度段数不需要发,是默认的.
        temp = process_detail.get("temp_para").get("table_data")[0].get("sections")
        metering = process_detail.get("metering_para").get("table_data")
        holding = process_detail.get("holding_para").get("table_data")
        injection = process_detail.get("inject_para").get("table_data")
        process_dict = dict({                
            "71": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[0]) if len(temp) >=1 and temp[0] else None,  # 料筒温度1段实际值
            "73": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[1]) if len(temp) >=2 and temp[1] else None,  # 料筒温度2段实际值
            "75": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[2]) if len(temp) >=3 and temp[2] else None,  # 料筒温度3段实际值
            "77": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[3]) if len(temp) >=4 and temp[3] else None,  # 料筒温度4段实际值
            "79": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[4]) if len(temp) >=5 and temp[4] else None,  # 料筒温度5段实际值
			"81": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[5]) if len(temp) >=6 and temp[5] else None,  # 料筒温度6段实际值
			"83": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[6]) if len(temp) >=7 and temp[6] else None,  # 料筒温度7段实际值
            "85": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[7]) if len(temp) >=8 and temp[7] else None,  # 料筒温度8段实际值
            "87": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[8]) if len(temp) >=9 and temp[8] else None,  # 料筒温度9段实际值
            "89": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[9]) if len(temp) >=10 and temp[9] else None,  # 料筒温度10段实际值
            "91": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[10]) if len(temp) >=11 and temp[10] else None,  # 料筒温度11段实际值
            "93": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[11]) if len(temp) >=12 and temp[11] else None,  # 料筒温度12段实际值
			"95": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[12]) if len(temp) >=13 and temp[12] else None,  # 料筒温度13段实际值
			"97": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[13]) if len(temp) >=14 and temp[13] else None,  # 料筒温度14段实际值
			"99": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[14]) if len(temp) >=15 and temp[14] else None,  # 料筒温度15段实际值
			"101": getConversion(temp_unit, TRANSFER_TEMP_UNIT, temp[15]) if len(temp) >=16 and temp[15] else None,  # 料筒温度16段实际值
            "133": process_detail.get("metering_para").get("metering_stage"),  # 熔胶段数
            "108": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[0]) if len(metering)>=1 and len(metering[1].get("sections")) >=1 and metering[1].get("sections")[0] else None,  # 储料一段速度
            "112": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[1]) if len(metering)>=1 and len(metering[1].get("sections")) >=2 and metering[1].get("sections")[1] else None,  # 储料二段速度
            "116": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[2]) if len(metering)>=1 and len(metering[1].get("sections")) >=3 and metering[1].get("sections")[2] else None,  # 储料三段速度
            "120": getConversion(rotation_unit, TRANSFER_ROTATION_UNIT, metering[1].get("sections")[3]) if len(metering)>=1 and len(metering[1].get("sections")) >=4 and metering[1].get("sections")[3] else None,  # 储料四段速度
            "105": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[0], convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=1 and metering[2].get("sections")[0] else None,  # 储料一段背压
            "109": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[1], convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=2 and metering[2].get("sections")[1] else None,  # 储料二段背压
            "113": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[2], convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=3 and metering[2].get("sections")[2] else None,  # 储料三段背压
            "117": getConversion(backpressure_unit, TRANSFER_BACK_PRESSURE_UNIT, metering[2].get("sections")[3], convert_type="origin_press") if len(metering)>=2 and len(metering[1].get("sections")) >=4 and metering[2].get("sections")[3] else None,  # 储料四段背压
            "106": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[0]) if len(metering)>=3 and len(metering[1].get("sections")) >=1 and metering[3].get("sections")[0] else None,  # 储料一段位置
            "110": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[1]) if len(metering)>=3 and len(metering[1].get("sections")) >=2 and metering[3].get("sections")[1] else None,  # 储料二段位置
            "114": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[2]) if len(metering)>=3 and len(metering[1].get("sections")) >=3 and metering[3].get("sections")[2] else None,  # 储料三段位置
            "118": getConversion(position_unit, TRANSFER_POSITION_UNIT, metering[3].get("sections")[3]) if len(metering)>=3 and len(metering[1].get("sections")) >=4 and metering[3].get("sections")[3] else None,  # 储料四段位置
            "107": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, metering[0].get("sections")[0], convert_type="metering_pressure_write") if len(metering)>=0 and len(metering[1].get("sections")) >=1 and metering[0].get("sections")[0] else None,  # 储料一段压力
            "111": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, metering[0].get("sections")[1], convert_type="metering_pressure_write") if len(metering)>=0 and len(metering[1].get("sections")) >=2 and metering[0].get("sections")[1] else None,  # 储料二段压力
            "115": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, metering[0].get("sections")[2], convert_type="metering_pressure_write") if len(metering)>=0 and len(metering[1].get("sections")) >=3 and metering[0].get("sections")[2] else None,  # 储料三段压力
            "119": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, metering[0].get("sections")[3], convert_type="metering_pressure_write") if len(metering)>=0 and len(metering[1].get("sections")) >=4 and metering[0].get("sections")[3] else None,  # 储料四段压力
            "453": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure"), convert_type="decompression_pressure_write") if process_detail.get("metering_para").get("decompressure_paras")[0].get("pressure") else None,  # 熔胶前松退压力
            "454": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("metering_para").get("decompressure_paras")[0].get("velocity"), convert_type="decompressure") if process_detail.get("metering_para").get("decompressure_paras")[0].get("velocity") else None,  # 熔胶前松退速度
            "452": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("decompressure_paras")[0].get("distance")) if process_detail.get("metering_para").get("decompressure_paras")[0].get("distance") else None,  # 熔胶前松退位置
            # "189": process_detail.get("metering_para").get("decompressure_paras")[0].get("time"),  # 熔胶前松退时间
            "485": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure"), convert_type="decompression_pressure_write") if process_detail.get("metering_para").get("decompressure_paras")[1].get("pressure") else None,  # 熔胶后松退压力
            "486": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("velocity"), convert_type="decompressure") if process_detail.get("metering_para").get("decompressure_paras")[1].get("velocity") else None,  # 熔胶后松退速度
            "484": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("metering_para").get("decompressure_paras")[1].get("distance")) if process_detail.get("metering_para").get("decompressure_paras")[1].get("distance") else None,  # 熔胶后松退位置
            # "193": process_detail.get("metering_para").get("decompressure_paras")[1].get("time"),  # 熔胶后松退时间
            "273": process_detail.get("holding_para").get("holding_stage"),  # 保压段数
            "255": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[0], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 1 and holding[0].get("sections")[0] else None,  # 保压一段压力
            "258": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[1], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 2 and holding[0].get("sections")[1] else None,  # 保压二段压力
            "261": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[2], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 3 and holding[0].get("sections")[2] else None,  # 保压三段压力
            "264": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[3], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 4 and holding[0].get("sections")[3] else None,  # 保压四段压力
            "267": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[4], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 5 and holding[0].get("sections")[4] else None,  # 保压五段压力
            "270": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, holding[0].get("sections")[5], convert_type="holding_pressure_write") if len(holding) >= 1 and len(holding[0].get("sections")) >= 6 and holding[0].get("sections")[5] else None,  # 保压六段压力

            "256": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[0], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 1 and holding[1].get("sections")[0] else None,  # 保压一段速度
            "259": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[1], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 2 and holding[1].get("sections")[1] else None,  # 保压二段速度
            "262": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[2], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 3 and holding[1].get("sections")[2] else None,  # 保压三段速度
            "265": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[3], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 4 and holding[1].get("sections")[3] else None,  # 保压四段速度
            "268": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[4], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 5 and holding[1].get("sections")[4] else None,  # 保压五段速度
            "271": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, holding[1].get("sections")[5], convert_type="holding") if len(holding) >= 2 and len(holding[0].get("sections")) >= 6 and holding[1].get("sections")[5] else None,  # 保压六段速度

            "257": holding[2].get("sections")[0] if len(holding) >= 3 and len(holding[0].get("sections")) >= 1 else None,  # 保压一段时间
            "260": holding[2].get("sections")[1] if len(holding) >= 3 and len(holding[0].get("sections")) >= 2 else None,  # 保压二段时间
            "263": holding[2].get("sections")[2] if len(holding) >= 3 and len(holding[0].get("sections")) >= 3 else None,  # 保压三段时间
			"266": holding[2].get("sections")[3] if len(holding) >= 3 and len(holding[0].get("sections")) >= 4 else None,  # 保压四段时间
            "269": holding[2].get("sections")[4] if len(holding) >= 3 and len(holding[0].get("sections")) >= 5 else None,  # 保压五段时间
            "272": holding[2].get("sections")[5] if len(holding) >= 3 and len(holding[0].get("sections")) >= 6 else None,  # 保压六段时间

            "361": process_detail.get("inject_para").get("injection_stage"),  # 注射段数
            "328": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[0]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 1 and injection[2].get("sections")[0] else None,  # 注射一段位置
            "333": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[1]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 2 and injection[2].get("sections")[1] else None,  # 注射二段位置
            "338": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[2]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 3 and injection[2].get("sections")[2] else None,  # 注射三段位置
            "343": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[3]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 4 and injection[2].get("sections")[3] else None,  # 注射四段位置
            "348": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[4]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 5 and injection[2].get("sections")[4] else None,  # 注射五段位置
            "353": getConversion(position_unit, TRANSFER_POSITION_UNIT, injection[2].get("sections")[5]) if len(injection) >= 3 and len(injection[2].get("sections")) >= 6 and injection[2].get("sections")[5] else None,  # 注射六段位置

            "329": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[0], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 1 and injection[0].get("sections")[0] else None,  # 注射一段压力
            "334": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[1], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 2 and injection[0].get("sections")[1] else None,  # 注射二段压力
            "339": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[2], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 3 and injection[0].get("sections")[2] else None,  # 注射三段压力
            "344": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[3], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 4 and injection[0].get("sections")[3] else None,  # 注射四段压力
            "349": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[4], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 5 and injection[0].get("sections")[4] else None,  # 注射五段压力
            "354": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, injection[0].get("sections")[5], convert_type="injection_pressure_write") if len(injection) >= 1 and len(injection[2].get("sections")) >= 6 and injection[0].get("sections")[5] else None,  # 注射六段压力

            "330": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[0], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 1 and injection[1].get("sections")[0] else None,  # 注射一段速度
            "335": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[1], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 2 and injection[1].get("sections")[1] else None,  # 注射二段速度
            "340": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[2], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 3 and injection[1].get("sections")[2] else None,  # 注射三段速度
            "345": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[3], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 4 and injection[1].get("sections")[3] else None,  # 注射四段速度
            "350": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[4], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 5 and injection[1].get("sections")[4] else None,  # 注射五段速度
            "355": getConversion(velocity_unit, TRANSFER_VELOCITY_UNIT, injection[1].get("sections")[5], convert_type="injection") if len(injection) >= 2 and len(injection[2].get("sections")) >= 6 and injection[1].get("sections")[5] else None,  # 注射六段速度

            "512": getConversion(position_unit, TRANSFER_POSITION_UNIT, process_detail.get("VP_switch").get("VP_switch_position")) if process_detail.get("VP_switch").get("VP_switch_position") else None,  # 保压切换位置
            "513": getConversion(pressure_unit, TRANSFER_PRESSURE_UNIT, process_detail.get("VP_switch").get("VP_switch_pressure"), convert_type="injection_pressure_write") if process_detail.get("VP_switch").get("VP_switch_pressure") else None,  # 保压切换压力
            "514": process_detail.get("VP_switch").get("VP_switch_time") if process_detail.get("VP_switch").get("VP_switch_time") else None,  # 保压切换时间
        })

        # 下发开合模,顶进顶退
        if(precondition.get("data_sources") != "工艺优化"):
            process_dict = setProcessTechSixPart(process_detail, machine_info.get("agreement"), process_dict)
            process_dict = setProcessTechEightEjector(process_detail, machine_info.get("agreement"), process_dict)
        new_process = {}
        # 下发之前,去掉空值
        for key in process_dict:
            if key and process_dict.get(key):
                new_process[key] = process_dict.get(key)
        logging.info(f"下发之前,检查参数是否正确{new_process}")
        json_data = json.dumps(new_process)
        #sn=mirleTest
        url = settings.MES+"/api/custom/equipment/craft/data/input/unit/transfer?sn="+machine_info.get("serial_no")+"&tag=2"
        token = loginYuzimi()
        header_dict = {"Content-Type": "application/json; charset=UTF-8"}
        header_dict["Authorization"] = token
        res = None
        resp = requests.post(url, data=json_data, headers=header_dict)
        logging.info(f"返回值是多少{resp}")
        if resp.status_code == 200:
            res = json.loads(resp.text)
        if res and res.get("msg") == "会话已过期,请重新登录":
            return dict(result="outdated")
        else:
            return dict(result="success")
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)
        return dict(result="failed")


# 顶针-盟立
def getProcessTechEightEjector(process_detail, res_data, agreement):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        if agreement == "盟立":
            TRANSFER_OC_PRESSURE_UNIT = machine_info.get("oc_pressure_unit") if machine_info.get("oc_pressure_unit") else "bar"  # 开合模和顶进顶退
            TRANSFER_OC_VELOCITY_UNIT = machine_info.get("oc_velocity_unit") if machine_info.get("oc_velocity_unit") else "mm/s" # 或者"%"
            # TRANSFER_OC_POSITION_UNIT = machine_info.get("position_unit") if machine_info.get("position_unit") else"mm"
        ejector_forward_pressure_sections = []
        ejector_forward_velocity_sections = []
        ejector_forward_position_sections = []
        ejector_backward_pressure_sections = []
        ejector_backward_velocity_sections = []
        ejector_backward_position_sections = []
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")
        # position_unit = machine_info.get("oc_position_unit")
        stage = int(res_data.get(PROCESS.get(agreement).get("ejector_forward_stage")))
        # "0":3段, "1":2段 ,只有2段和3段两种情况
        forward_stage = 2 if stage == "1" else 3
        for i in range(forward_stage):
            # 如果是2段,读取第2和第3的值
            if forward_stage == 2:
                j = i+1
            elif forward_stage == 3:
                j = i
            ejector_forward_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get(PROCESS.get(agreement).get("ejector_forward_pressure")[j]),convert_type="origin_press") if res_data.get(PROCESS.get(agreement).get("ejector_forward_pressure")[i]) else None)
            ejector_forward_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get(PROCESS.get(agreement).get("ejector_forward_velocity")[j]),convert_type="forward") if res_data.get(PROCESS.get(agreement).get("ejector_forward_velocity")[i]) else None)
            ejector_forward_position_sections.append(
                res_data.get(PROCESS.get(agreement).get("ejector_forward_position")[j]))

        stage = int(res_data.get(PROCESS.get(agreement).get("ejector_backward_stage")))
        # "0":3段, "1":2段 ,只有2段和3段两种情况
        backward_stage = 2 if stage == "1" else 3
        for i in range(backward_stage):
            if backward_stage == 2:
                j = i+1
            elif backward_stage == 3:
                j = i
            ejector_backward_pressure_sections.append(
                getConversion(TRANSFER_OC_PRESSURE_UNIT, pressure_unit, res_data.get(PROCESS.get(agreement).get("ejector_backward_pressure")[j]),convert_type="origin_press") if res_data.get(PROCESS.get(agreement).get("ejector_backward_pressure")[i]) else None)
            ejector_backward_velocity_sections.append(
                getConversion(TRANSFER_OC_VELOCITY_UNIT, velocity_unit, res_data.get(PROCESS.get(agreement).get("ejector_backward_velocity")[j]),convert_type="backward") if res_data.get(PROCESS.get(agreement).get("ejector_backward_velocity")[i]) else None)
            ejector_backward_position_sections.append(
                res_data.get(PROCESS.get(agreement).get("ejector_backward_position")[j]))

        ejector_forward = {
            "ejector_forward_stage": forward_stage,
            "max_ejector_forward_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": ejector_forward_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": ejector_forward_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": ejector_forward_position_sections}
            ],
        }
        ejector_backward = {
            "ejector_backward_stage": backward_stage,
            "max_ejector_backward_stage_option": 8,
            "table_data":  [
                {"label": "压力", "unit": pressure_unit,
                    "sections": ejector_backward_pressure_sections},
                {"label": "速度", "unit": velocity_unit,
                    "sections": ejector_backward_velocity_sections},
                {"label": "位置", "unit": machine_info.get("position_unit"), "sections": ejector_backward_position_sections}
            ],
        }
        ejector_setting = {
            "ejector_forward": ejector_forward,
            "ejector_backward": ejector_backward,
        }
        process_detail["ejector_setting"] = ejector_setting
        return process_detail
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)


# 顶针-盟立
def setProcessTechEightEjector(process_detail, agreement, process_dict):
    try:
        global TRANSFER_OC_VELOCITY_UNIT
        global TRANSFER_OC_PRESSURE_UNIT
        if agreement == "盟立":
            TRANSFER_OC_PRESSURE_UNIT = machine_info.get("oc_pressure_unit") if machine_info.get("oc_pressure_unit") else "bar"  # 开合模和顶进顶退
            TRANSFER_OC_VELOCITY_UNIT = machine_info.get("oc_velocity_unit") if machine_info.get("oc_velocity_unit") else "mm/s" # 或者"%"
            # TRANSFER_OC_POSITION_UNIT = "mm"
        pressure_unit = machine_info.get("oc_pressure_unit")
        velocity_unit = machine_info.get("oc_velocity_unit")        
        ejector_forward = process_detail.get("ejector_setting").get("ejector_forward").get("table_data")
        ejector_backward = process_detail.get("ejector_setting").get("ejector_backward").get("table_data")
        for i in range(min(3,process_detail.get("ejector_setting").get("ejector_forward").get("ejector_forward_stage"))):
            process_dict[PROCESS.get(agreement).get("ejector_forward_pressure")[i]] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, ejector_forward[0].get("sections")[i],convert_type="origin_press") if len(ejector_forward) >=1 and len(ejector_forward[0].get("sections"))>=i else None

            process_dict[PROCESS.get(agreement).get("ejector_forward_velocity")[i]] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, ejector_forward[1].get("sections")[i], convert_type="forward") if len(ejector_forward) >=2 and len(ejector_forward[1].get("sections"))>=i else None
            process_dict[PROCESS.get(agreement).get("ejector_forward_position")[i]] = ejector_forward[2].get("sections")[i] if len(ejector_forward) >=3 and len(ejector_forward[2].get("sections"))>=i else None
        for i in range(min(3,process_detail.get("ejector_setting").get("ejector_backward").get("ejector_backward_stage"))):
            process_dict[PROCESS.get(agreement).get("ejector_backward_pressure")[i]] = getConversion(pressure_unit, TRANSFER_OC_PRESSURE_UNIT, ejector_backward[0].get("sections")[i],convert_type="origin_press") if len(ejector_backward) >=1 and len(ejector_backward[0].get("sections"))>=i else None
            
            process_dict[PROCESS.get(agreement).get("ejector_backward_velocity")[i]] = getConversion(velocity_unit, TRANSFER_OC_VELOCITY_UNIT, ejector_backward[1].get("sections")[i], convert_type="backward") if len(ejector_backward) >=2 and len(ejector_backward[1].get("sections"))>=i else None
            process_dict[PROCESS.get(agreement).get("ejector_backward_position")[i]] = ejector_backward[2].get("sections")[i] if len(ejector_backward) >=3 and len(ejector_backward[2].get("sections"))>=i else None
        ejector_forward_stage = process_detail.get("ejector_setting").get("ejector_forward").get("ejector_forward_stage")
        forward_stage = "1" if ejector_forward_stage == 2 else "0"
        process_dict[PROCESS.get(agreement).get("ejector_forward_stage")] = forward_stage

        ejector_backward_stage = process_detail.get("ejector_setting").get("ejector_forward").get("ejector_backward_stage")
        backward_stage = "1" if ejector_backward_stage == 2 else "0"
        process_dict[PROCESS.get(agreement).get("ejector_backward_stage")] = backward_stage
        return process_dict
    except Exception as e:
        logging.error(e.args)
        logging.error(e.__traceback__.tb_lineno)
