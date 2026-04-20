
from mdprocess.models import ProcessIndex
from mdprocess.dao.process_record_model import ProcessParameterRecordDoc
from hsmolding.models import Machine, MachineInjector
from mdprocess.utils.unit_convert import unit_conversion
import copy

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

PI = 3.1415926


def get_process_no_list(
    company_id=None,
    mold_no=None,
    mold_id=None,
    status=2,
):
    query = ProcessIndex.objects.filter(company_id=company_id, status=status, mold_id=mold_id).all().order_by("-created_at")
    ret_list = [ { "id": e.id, "process_no": e.process_no } for e in query ]

    return ret_list



def transfer_process(
    company_id=None, 
    process_id=None,
    mac_id=None,
    mac_trademark=None,
    mac_serial_no=None
):
    record = ProcessParameterRecordDoc.objects.filter(process_index_id=process_id).first()
    # 原工艺参数
    record_dict = record.to_dict()
    o_mac_id = record_dict.get("precondition").get("machine_id")
    o_process: dict = record_dict.get("process_detail")
    # 原注塑机
    o_injector = MachineInjector.objects.filter(machine_id=o_mac_id).first()
    o_injector_dict = o_injector.to_dict()
    o_cv = {}
    
    # 待移植注塑机
    t_machine = Machine.objects.filter(company_id=company_id, trademark=mac_trademark, serial_no=mac_serial_no).first()
    t_injector = MachineInjector.objects.filter(machine_id=t_machine.id).first()
    t_injector_dict = t_injector.to_dict()
    t_cv = {}
    
    # 读取最大值和最大可设定值
    check_item = [ 
        "screw_diameter",
        "max_injection_pressure",
        "max_set_injection_pressure",
        "max_injection_velocity",
        "max_set_injection_velocity",
        "max_holding_pressure",
        "max_set_holding_pressure",
        "max_holding_velocity",
        "max_set_holding_velocity",
        "max_metering_pressure",
        "max_set_metering_pressure",
        "max_screw_rotation_speed",
        "max_set_screw_rotation_speed",
        "max_metering_back_pressure",
        "max_set_metering_back_pressure",
        "max_decompression_pressure",
        "max_set_decompression_pressure",
        "max_decompression_velocity",
        "max_set_decompression_velocity"
    ]
    for key in check_item:
        o_cv[key] = float(o_injector_dict.get(key))
        t_cv[key] = float(t_injector_dict.get(key))
    
    # 工艺移植
    t_process = copy.deepcopy(o_process)
    
    # 注射参数
    for i in range(0, 3):
        for j in range(int(o_process["inject_para"]["injection_stage"])):
            if i == 0:
                # 注射压力
                o_inj_pres = o_process["inject_para"]["table_data"][i]["sections"][j] 
                t_inj_pres = o_inj_pres * (o_cv["max_injection_pressure"] * t_cv["max_set_injection_pressure"]) / (o_cv["max_set_injection_pressure"] * t_cv["max_injection_pressure"])
                t_process["inject_para"]["table_data"][i]["sections"][j] = t_inj_pres
            if i == 1:
                # 注射速度
                o_inj_velo = o_process["inject_para"]["table_data"][i]["sections"][j] 
                t_inj_velo = o_inj_pres * (o_cv["max_injection_velocity"] * t_cv["max_set_injection_velocity"]) / (o_cv["max_set_injection_velocity"] * t_cv["max_injection_velocity"])
                t_process["inject_para"]["table_data"][i]["sections"][j]  = t_inj_velo
            if i == 2:
                # 注射位置
                o_inj_posi = o_process["inject_para"]["table_data"][i]["sections"][j]
                t_inj_posi = o_inj_posi * (PI * o_cv["screw_diameter"]**2 / 4) / (PI * t_cv["screw_diameter"]**2 / 4)
                t_process["inject_para"]["table_data"][i]["sections"][j]  = t_inj_posi
    
    t_process["inject_para"]["injection_time"] = o_process["inject_para"]["injection_time"]
    t_process["inject_para"]["injection_delay_time"] = o_process["inject_para"]["injection_delay_time"]
    t_process["inject_para"]["cooling_time"] = o_process["inject_para"]["cooling_time"]
    
    # 保压参数
    for i in range(0, 3):
        for j in range(int(o_process["holding_para"]["holding_stage"])):
            if i == 0:
                # 保压压力
                o_hld_pres = o_process["holding_para"]["table_data"][i]["sections"][j] 
                t_hld_pres = o_hld_pres * (o_cv["max_holding_pressure"] * t_cv["max_set_holding_pressure"]) / (o_cv["max_set_holding_pressure"] * t_cv["max_holding_pressure"])
                t_process["holding_para"]["table_data"][i]["sections"][j] = t_hld_pres
            if i == 1:
                # 保压速度
                o_hld_velo = o_process["holding_para"]["table_data"][i]["sections"][j] 
                t_hld_velo = o_hld_velo * (o_cv["max_holding_velocity"] * t_cv["max_set_holding_velocity"]) / (o_cv["max_set_holding_velocity"] * t_cv["max_holding_velocity"])
                t_process["inject_para"]["table_data"][i]["sections"][j]  = t_hld_velo
            if i == 2:
                # 保压时间
                o_hld_time = o_process["inject_para"]["table_data"][i]["sections"][j]
                t_process["inject_para"]["table_data"][i]["sections"][j]  = o_hld_time
                
    # vp切换
    t_process["VP_switch"]["VP_switch_mode"] = o_process["VP_switch"]["VP_switch_mode"]
    # 切换位置
    o_swt_posi = o_process["VP_switch"]["VP_switch_position"] 
    t_swt_posi = o_swt_posi * (PI * o_cv["screw_diameter"]**2 / 4) / (PI * t_cv["screw_diameter"]**2 / 4)
    t_process["VP_switch"]["VP_switch_position"] = t_swt_posi
    # 切换时间
    t_process["VP_switch"]["VP_switch_time"] = o_process["VP_switch"]["VP_switch_time"]
    # 切换压力
    o_swt_pres = o_process["VP_switch"]["VP_switch_pressure"]
    if o_swt_pres:
        t_swt_pres = o_swt_pres * (o_cv["max_injection_pressure"] * t_cv["max_set_injection_pressure"]) / (o_cv["max_set_injection_pressure"] * t_cv["max_injection_pressure"])
        t_process["VP_switch"]["VP_switch_pressure"] = t_swt_pres
    # 切换速度
    o_swt_velo = o_process["VP_switch"]["VP_switch_velocity"]
    if o_swt_velo:
        t_swt_velo = o_swt_velo * (o_cv["max_injection_velocity"] * t_cv["max_set_injection_velocity"]) / (o_cv["max_set_injection_velocity"] * t_cv["max_injection_velocity"])
        t_process["inject_para"]["table_data"][i]["sections"][j]  = t_swt_velo
    
    # 计量参数
    for i in range(0, 4):
        for j in range(int(o_process["metering_para"]["metering_stage"])):
            if i == 0:
                # 计量压力
                o_mtr_pres = o_process["metering_para"]["table_data"][i]["sections"][j] 
                t_mtr_pres = o_mtr_pres * (o_cv["max_metering_pressure"] * t_cv["max_set_metering_pressure"]) / (o_cv["max_set_metering_pressure"] * t_cv["max_metering_pressure"])
                t_process["metering_para"]["table_data"][i]["sections"][j] = t_mtr_pres
            if i == 1:
                # 螺杆转速
                o_mtr_screw_rot = o_process["metering_para"]["table_data"][i]["sections"][j] 
                t_mtr_screw_rot = o_mtr_screw_rot * (o_cv["max_screw_rotation_speed"] * t_cv["max_set_screw_rotation_speed"]) / (o_cv["max_set_screw_rotation_speed"] * t_cv["max_screw_rotation_speed"])
                t_process["metering_para"]["table_data"][i]["sections"][j]  = t_mtr_screw_rot
            if i == 2:
                # 计量背压
                o_mtr_back_res = o_process["metering_para"]["table_data"][i]["sections"][j] 
                t_mtr_back_res = o_mtr_back_res * (o_cv["max_metering_back_pressure"] * t_cv["max_set_metering_back_pressure"]) / (o_cv["max_set_metering_back_pressure"] * t_cv["max_metering_back_pressure"])
                t_process["metering_para"]["table_data"][i]["sections"][j]  = t_mtr_back_res
            if i == 3:
                # 计量位置
                o_mtr_posi = o_process["metering_para"]["table_data"][i]["sections"][j]
                t_mtr_posi = o_mtr_posi * (PI * o_cv["screw_diameter"]**2 / 4) / (PI * t_cv["screw_diameter"]**2 / 4)
                t_process["metering_para"]["table_data"][i]["sections"][j]  = t_mtr_posi
    
    # 储前松退模式
    t_process["metering_para"]["decompressure_mode_before_metering"] = o_process["metering_para"]["decompressure_mode_before_metering"]
    # 储后松退模式
    t_process["metering_para"]["decompressure_mode_after_metering"] = o_process["metering_para"]["decompressure_mode_after_metering"]
    
    # 松退
    for i in range(0, 2):
        # 松退压力
        o_deco_pres = t_process["metering_para"]["decompressure_paras"][i]["pressure"]
        if o_deco_pres:
            t_deco_pres = o_deco_pres * (o_cv["max_decompression_pressure"] * t_cv["max_set_decompression_pressure"]) / (o_cv["max_set_decompression_pressure"] * t_cv["max_decompression_pressure"])
            t_process["metering_para"]["decompressure_paras"][i]["pressure"] = t_deco_pres
        
        # 松退速度
        o_deco_velo = t_process["metering_para"]["decompressure_paras"][i]["velocity"]
        if o_deco_velo:
            t_deco_velo = o_deco_velo * (o_cv["max_decompression_velocity"] * t_cv["max_set_decompression_velocity"]) / (o_cv["max_set_decompression_velocity"] * t_cv["max_decompression_velocity"])
            t_process["metering_para"]["decompressure_paras"][i]["velocity"] = t_deco_velo
        
        # 松退位置
        o_deco_posi = o_process["metering_para"]["decompressure_paras"][i]["distance"]
        if o_deco_posi:
            t_deco_posi = o_deco_posi * (PI * o_cv["screw_diameter"]**2 / 4) / (PI * t_cv["screw_diameter"]**2 / 4)
            t_process["metering_para"]["decompressure_paras"][i]["distance"]  = t_deco_posi
        
        # 松退时间
        t_process["metering_para"]["decompressure_paras"][i]["distance"]  = o_process["metering_para"]["decompressure_paras"][i]["distance"]

    # 计量延迟
    t_process["metering_para"]["metering_delay_time"] = o_process["metering_para"]["metering_delay_time"]
    # 计量终点位置
    o_end_posi = o_process["metering_para"]["metering_ending_position"]
    t_end_posi = o_end_posi * (PI * o_cv["screw_diameter"]**2 / 4) / (PI * t_cv["screw_diameter"]**2 / 4)
    t_process["metering_para"]["metering_ending_position"] = t_end_posi
    
    # 料筒温度
    for j in range(int(o_process["temp_para"]["barrel_temperature_stage"])):
        t_process["temp_para"]["table_data"][0]["sections"][j] = o_process["temp_para"]["table_data"][0]["sections"][j]
        
    return {
        "title": t_process["title"],
        "name": t_process["name"],
        "inject_para": t_process["inject_para"],
        "holding_para": t_process["holding_para"],
        "VP_switch": t_process["VP_switch"],
        "metering_para": t_process["metering_para"],
        "temp_para": t_process["temp_para"]
    }

    