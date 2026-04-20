
import math

from mqtt.const import DECOM_MAP, VP_SWITCH_MAP

def getCylinderArea(inj: dict):
    if inj.get("use_small_size"):
        return float(inj.get("cylinder_numer")) * math.pi * float(inj.get("cylinder_diameter"))**2 / 4
    else:
        return float(inj.get("cylinder_numer")) * (math.pi * float(inj.get("cylinder_diameter"))**2 / 4 - math.pi * float(inj.get("piston_rod_diameter"))**2 / 4)


def getScrewArea(inj: dict):
    return math.pi * float(inj.get("screw_diameter") ** 2 / 4)


def getScrewCircumference(inj: dict):
    return math.pi * float(inj.get("screw_diameter"))


def pressure_unit_conv(input, inj: dict, orig_unit = "bar", conv_unit = "MPa"):
    if not input:
        return input
    
    if conv_unit == "MPa":
        if orig_unit == "bar":
            return input * 0.1
        elif orig_unit == "kgf/cm^2":
            return input * 0.98 * 0.1
        elif orig_unit == "PSI":
            return input / 145        
            
    if orig_unit == "MPa":
        if conv_unit == "bar":
            return input * 10
        elif conv_unit == "kgf/cm^2":
            return input * 10 * 1.01
        elif conv_unit == "PSI":
            return input * 145   
        
    return input


def velocity_unit_conv(input, inj: dict, orig_unit = "%", conv_unit = "mm/s"):
    if not input:
        return input
    
    if conv_unit == "mm/s":
        if orig_unit == "%":
            return input / 100 * float(inj.get("max_injection_velocity"))
        elif orig_unit == "inch/s":
            return input * 25.4
        elif orig_unit == "cm^3/s":
            return input * 1000 / getScrewArea(inj)
        elif orig_unit == "inch3/s":
            return input * 25.4**3 / getScrewArea(inj)
    
    if orig_unit == "mm/s":
        if conv_unit == "%":
            return input * 100 / float(inj.get("max_injection_velocity"))
        elif conv_unit == "inch/s":
            return input / 25.4
        elif conv_unit == "cm^3/s":
            return input * getScrewArea(inj) / 1000
        elif conv_unit == "inch3/s":
            return input * getScrewArea(inj) / 25.4**3
    
    return input


def position_unit_conv(input, inj: dict, orig_unit = "inch", conv_unit = "mm"):
    if not input:
        return input
    
    if conv_unit == "mm":
        if orig_unit == "inch":
            return input * 25.4
        elif orig_unit == "cm^3":
            return input * 1000 / getScrewArea(inj)
        elif orig_unit == "inch3":
            return input * 25.4**3 / getScrewArea(inj)
    
    if orig_unit == "mm":
        if conv_unit == "inch":
            return input / 25.4
        elif conv_unit == "cm^3":
            return input * getScrewArea(inj) / 1000
        elif conv_unit == "inch3":
            return input * getScrewArea(inj) / 25.4**3
    
    return input


def rotation_unit_conv(input, inj: dict, orig_unit = "mm/s", conv_unit = "rpm"):
    if not input:
        return input
    
    if conv_unit == "rpm":
        if orig_unit == "mm/s":
            return input * 60 / getScrewCircumference(inj)
        elif orig_unit == "cm/s":
            return input * 600 / getScrewCircumference(inj)
        elif orig_unit == "inch/s":
            return input * 60 * 25.4 / getScrewCircumference(inj)
        elif orig_unit == "m/s":
            return input * 6000 / getScrewCircumference(inj)
        elif orig_unit == "m/min":
            return input * 100 / getScrewCircumference(inj)
        elif orig_unit == "%":
            return input * inj.get("max_screw_rotation_speed")

    if orig_unit == "rpm":
        if conv_unit == "mm/s":
            return input * getScrewCircumference(inj) / 60
        elif conv_unit == "cm/s":
            return input * getScrewCircumference(inj) / 600
        elif conv_unit == "inch/s":
            return input * getScrewCircumference(inj) / (60 * 25.4)
        elif conv_unit == "m/s":
            return input * getScrewCircumference(inj) / 6000
        elif conv_unit == "m/min":
            return input * getScrewCircumference(inj) / 100
        elif conv_unit == "%":
            return input / inj.get("max_screw_rotation_speed")
    
    return input


def injection_pressure_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_injection_pressure")) / float(orig_inj.get("max_set_injection_pressure"))) \
        / (float(conv_inj.get("max_injection_pressure")) / float(conv_inj.get("max_set_injection_pressure")))


def injection_velocity_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_injection_velocity")) / float(orig_inj.get("max_set_injection_velocity"))) \
        / (float(conv_inj.get("max_injection_velocity")) / float(conv_inj.get("max_set_injection_velocity")))


def position_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * getScrewArea(orig_inj) / getScrewArea(conv_inj)


def holding_pressure_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_holding_pressure")) / float(orig_inj.get("max_set_holding_pressure"))) \
        / (float(conv_inj.get("max_holding_pressure")) / float(conv_inj.get("max_set_holding_pressure")))


def holding_velocity_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_holding_velocity")) / float(orig_inj.get("max_set_holding_velocity"))) \
        / (float(conv_inj.get("max_holding_velocity")) / float(conv_inj.get("max_set_holding_velocity")))
    
    
def metering_pressure_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_metering_pressure")) / float(orig_inj.get("max_set_metering_pressure"))) \
        / (float(conv_inj.get("max_metering_pressure")) / float(conv_inj.get("max_set_metering_pressure")))


def metering_screw_rotation_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_screw_rotation_speed")) / float(orig_inj.get("max_set_screw_rotation_speed"))) \
        / (float(conv_inj.get("max_screw_rotation_speed")) / float(conv_inj.get("max_set_screw_rotation_speed")))


def metering_back_pressure_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_metering_back_pressure")) / float(orig_inj.get("max_set_metering_back_pressure"))) \
        / (float(conv_inj.get("max_metering_back_pressure")) / float(conv_inj.get("max_set_metering_back_pressure")))


def decom_pressure_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_decompression_pressure")) / float(orig_inj.get("max_set_decompression_pressure"))) \
        / (float(conv_inj.get("max_decompression_pressure")) / float(conv_inj.get("max_set_decompression_pressure")))


def decom_velocity_conv(input, orig_inj: dict, conv_inj: dict):
    if not input:
        return input
    
    return input * (float(orig_inj.get("max_decompression_velocity")) / float(orig_inj.get("max_set_decompression_velocity"))) \
        / (float(conv_inj.get("max_decompression_velocity")) / float(conv_inj.get("max_set_decompression_velocity")))
        

def spc_var_normalize_conv(input, inj: dict, orig_unit = "barspec", conv_unit = "MPa"):
    if not input:
        return input
    
    if conv_unit == "MPa":
        # 压力转换 -> MPa
        if orig_unit == "barspec":
            return input * getScrewArea(inj) / getCylinderArea(inj) * 0.1
        elif orig_unit == "bar":
            return input * 0.1
    elif conv_unit == "mm/s":
        # 速度转换 -> mm/s
        if orig_unit == "cm3/s":
            return input * 1000 / getScrewArea(inj)
    elif conv_unit == "mm":
        # 位置转换 -> mm
        if orig_unit == "cm3":
            return input * 1000 / getScrewArea(inj)
    elif conv_unit == "rpm":
        # 螺杆转速 -> rpm
        if orig_unit == "cm/s":
            return input * 600 / getScrewCircumference(inj)
    elif conv_unit == "s":
        # 时间 -> s
        if orig_unit == "us":
            return input / 1000000
        
    if orig_unit == "MPa":
        # 压力转换 -> MPa
        if conv_unit == "barspec":
            return input * 10 * getCylinderArea(inj) / getScrewArea(inj)
        elif conv_unit == "bar":
            return input * 10
    elif orig_unit == "mm/s":
        # 速度转换 -> mm/s
        if conv_unit == "cm3/s":
            return input *  getScrewArea(inj) / 1000
    elif orig_unit == "mm":
        # 位置转换 -> mm
        if conv_unit == "cm3":
            return input * getScrewArea(inj) / 1000
    elif orig_unit == "rpm":
        # 螺杆转速 -> rpm
        if conv_unit == "cm/s":
            return input * getScrewCircumference(inj) / 600
    elif orig_unit == "s":
        # 时间 -> s
        if conv_unit == "us":
            return input * 1000000
    return input


def conv_spc_data(data: dict, mac: dict, inj: dict):
    # 注射参数
    for i in range(0, data["injection_stage"]):
        # 注射压力
        data["IP" + str(i)] = spc_var_normalize_conv(pressure_unit_conv(data["IP" + str(i)], inj, mac.get("pressure_unit"), "MPa"), inj, "MPa", "bar")
        # 注射速度
        data["IV" + str(i)] = spc_var_normalize_conv(velocity_unit_conv(data["IV" + str(i)], inj, mac.get("velocity_unit"), "mm/s"), inj, "mm/s", "cm3/s")
        # 注射位置
        data["IL" + str(i)] = spc_var_normalize_conv(position_unit_conv(data["IL" + str(i)], inj, mac.get("position_unit"), "mm"), inj, "mm", "cm3")
    data["IT"] = spc_var_normalize_conv(data["IT"], inj, "s", "us")
    data["ID"] = spc_var_normalize_conv(data["ID"], inj, "s", "us")
    data["CT"] = spc_var_normalize_conv(data["CT"], inj, "s", "us")
    # 保压参数
    for i in range(0, data["holding_stage"]):
        # 保压压力
        data["PP" + str(i)] = spc_var_normalize_conv(pressure_unit_conv(data["PP" + str(i)], inj, mac.get("pressure_unit"), "MPa"), inj, "MPa", "bar")
        # 保压速度
        data["PV" + str(i)] = spc_var_normalize_conv(velocity_unit_conv(data["PV" + str(i)], inj, mac.get("velocity_unit"), "mm/s"), inj, "mm/s", "cm3/s")
        # 保压时间
        data["PT" + str(i)] = spc_var_normalize_conv(data["PT" + str(i)], inj, "s", "s")
    # vp切换
    data["VPTM"] = VP_SWITCH_MAP[data["VPTM"]]            
    data["VPTL"] = spc_var_normalize_conv(position_unit_conv(data["VPTL"], inj, mac.get("position_unit"), "mm"), inj, "mm", "cm3")
    data["VPTT"] = spc_var_normalize_conv(data["VPTT"], inj, "s", "us")
    data["VPTP"] = spc_var_normalize_conv(pressure_unit_conv(data["VPTP"], inj, mac.get("pressure_unit"), "MPa"), inj, "MPa", "bar")
    data["VPTV"] = spc_var_normalize_conv(velocity_unit_conv(data["VPTV"], inj, mac.get("velocity_unit"), "mm/s"), inj, "mm/s", "cm3/s")
    for i in range(0, data["metering_stage"]):
        # 计量压力
        data["MP" + str(i)] = spc_var_normalize_conv(pressure_unit_conv(data["MP" + str(i)], inj, mac.get("pressure_unit"), "MPa"), inj, "MPa", "bar")
        # 螺杆转速
        data["MSR" + str(i)] = spc_var_normalize_conv(rotation_unit_conv(data["MSR" + str(i)], inj, mac.get("screw_rotation_unit"), "rpm"), inj, "rpm", "cm/s")
        # 计量背压
        data["MBP" + str(i)] = spc_var_normalize_conv(pressure_unit_conv(data["MBP" + str(i)], inj, mac.get("pressure_unit"), "MPa"), inj, "MPa", "bar")
        # 计量位置
        data["ML" + str(i)] = spc_var_normalize_conv(position_unit_conv(data["ML" + str(i)], inj, mac.get("position_unit"), "mm"), inj, "mm", "cm3")
    # 松退
    data["DMBM"] = DECOM_MAP[data["DMBM"]]
    data["DMAM"] = DECOM_MAP[data["DMAM"]]
    data["DPBM"] = spc_var_normalize_conv(pressure_unit_conv(data["DPBM"], inj, mac.get("pressure_unit"), "MPa"), inj, "MPa", "bar")
    data["DVBM"] = spc_var_normalize_conv(velocity_unit_conv(data["DVBM"], inj, mac.get("velocity_unit"), "mm/s"), inj, "mm/s", "mm/s")
    data["DDBM"] = spc_var_normalize_conv(position_unit_conv(data["DDBM"], inj, mac.get("position_unit"), "mm"), inj, "mm", "cm3")
    data["DTBM"] = spc_var_normalize_conv(data["DTBM"], inj, "s", "us")
    data["DPAM"] = spc_var_normalize_conv(pressure_unit_conv(data["DPAM"], inj, mac.get("pressure_unit"), "MPa"), inj, "MPa", "bar")
    data["DVAM"] = spc_var_normalize_conv(velocity_unit_conv(data["DVAM"], inj, mac.get("velocity_unit"), "mm/s"), inj, "mm/s", "mm/s")
    data["DDAM"] = spc_var_normalize_conv(position_unit_conv(data["DDAM"], inj, mac.get("position_unit"), "mm"), inj, "mm", "cm3")
    data["DTAM"] = spc_var_normalize_conv(data["DTAM"], inj, "s", "us")
    
    data["MD"] = spc_var_normalize_conv(data["MD"], inj, "s", "us")
    data["MEL"] = spc_var_normalize_conv(position_unit_conv(data["MEL"], inj, mac.get("position_unit"), "mm"), inj, "mm", "cm3")


def conv_view_data(data: dict, mac: dict, inj: dict):
    # 注射参数
    for i in range(0, data["injection_stage"]):
        # 注射压力
        data["IP" + str(i)] = pressure_unit_conv(spc_var_normalize_conv(data["IP" + str(i)], inj, "bar", "MPa"), inj, "MPa", mac.get("pressure_unit"))
        # 注射速度
        data["IV" + str(i)] = velocity_unit_conv(spc_var_normalize_conv(data["IV" + str(i)], inj, "cm3/s", "mm/s"), inj, "mm/s", mac.get("velocity_unit"))
        # 注射位置
        data["IL" + str(i)] = position_unit_conv(spc_var_normalize_conv(data["IL" + str(i)], inj, "cm3", "mm"), inj, "mm", mac.get("position_unit"))
        
    data["IT"] = spc_var_normalize_conv(data["IT"], inj, "us", "s")
    data["ID"] = spc_var_normalize_conv(data["ID"], inj, "us", "s")
    data["CT"] = spc_var_normalize_conv(data["CT"], inj, "us", "s")
    # 保压参数
    for i in range(0, data["holding_stage"]):
        # 保压压力
        data["PP" + str(i)] = pressure_unit_conv(spc_var_normalize_conv(data["PP" + str(i)], inj, "bar", "MPa"), inj, "MPa", mac.get("pressure_unit"))
        # 保压速度
        data["PV" + str(i)] = velocity_unit_conv(spc_var_normalize_conv(data["PV" + str(i)], inj, "cm3/s", "mm/s"), inj, "mm/s", mac.get("velocity_unit"))
        # 保压时间
        data["PT" + str(i)] = spc_var_normalize_conv(data["PT" + str(i)], inj, "s", "s")
    # vp切换
    data["VPTM"] = VP_SWITCH_MAP[data["VPTM"]]            
    data["VPTL"] = position_unit_conv(spc_var_normalize_conv(data["VPTL"], inj, "cm3", "mm"), inj, "mm", mac.get("position_unit"))
    data["VPTT"] = spc_var_normalize_conv(data["VPTT"], inj, "us", "s")
    data["VPTP"] = pressure_unit_conv(spc_var_normalize_conv(data["VPTP"], inj, "bar", "MPa"), inj, "MPa", mac.get("pressure_unit"))
    data["VPTV"] = velocity_unit_conv(spc_var_normalize_conv(data["VPTV"], inj, "cm3/s", "mm/s"), inj, "mm/s", mac.get("velocity_unit"))
    for i in range(0, data["metering_stage"]):
        # 计量压力
        data["MP" + str(i)] = pressure_unit_conv(spc_var_normalize_conv(data["MP" + str(i)], inj, "bar", "MPa"), inj, "MPa", mac.get("pressure_unit"))
        # 螺杆转速
        data["MSR" + str(i)] = rotation_unit_conv(spc_var_normalize_conv(data["MSR" + str(i)], inj, "cm/s", "rpm"), inj, "rpm", mac.get("screw_rotation_unit"))
        # 计量背压
        data["MBP" + str(i)] = pressure_unit_conv(spc_var_normalize_conv(data["MBP" + str(i)], inj, "bar", "MPa"), inj, "MPa", mac.get("pressure_unit"))
        # 计量位置
        data["ML" + str(i)] = position_unit_conv(spc_var_normalize_conv(data["ML" + str(i)], inj, "cm3", "mm"), inj, "mm", mac.get("position_unit"))
    # 松退
    data["DMBM"] = DECOM_MAP[data["DMBM"]]
    data["DMAM"] = DECOM_MAP[data["DMAM"]]
    data["DPBM"] = pressure_unit_conv(spc_var_normalize_conv(data["DPBM"], inj, "bar", "MPa"), inj, "MPa", mac.get("pressure_unit"))
    data["DVBM"] = velocity_unit_conv(spc_var_normalize_conv(data["DVBM"], inj, "mm/s", "mm/s"), inj, "mm/s", mac.get("velocity_unit"))
    data["DDBM"] = position_unit_conv(spc_var_normalize_conv(data["DDBM"], inj, "cm3", "mm"), inj, "mm", mac.get("position_unit"))
    data["DTBM"] = spc_var_normalize_conv(data["DTBM"], inj, "us", "s")
    data["DPAM"] = pressure_unit_conv(spc_var_normalize_conv(data["DPAM"], inj, "bar", "MPa"), inj, "MPa", mac.get("pressure_unit"))
    data["DVAM"] = velocity_unit_conv(spc_var_normalize_conv(data["DVAM"], inj, "mm/s", "mm/s"), inj, "mm/s", mac.get("velocity_unit"))
    data["DDAM"] = position_unit_conv(spc_var_normalize_conv(data["DDAM"], inj, "cm3", "mm"), inj, "mm", mac.get("position_unit"))
    data["DTAM"] = spc_var_normalize_conv(data["DTAM"], inj, "us", "s")
    
    data["MD"] = spc_var_normalize_conv(data["MD"], inj, "us", "s")
    data["MEL"] = position_unit_conv(spc_var_normalize_conv(data["MEL"], inj, "cm3", "mm"), inj, "mm", mac.get("position_unit"))


def conv_processs(data: dict, orig_inj: dict, conv_inj: dict):
    # 注射参数
    for i in range(0, data["injection_stage"]):
        # 注射压力
        data["IP" + str(i)] = injection_pressure_conv(data["IP" + str(i)], orig_inj, conv_inj)
        # 注射速度
        data["IV" + str(i)] = injection_velocity_conv(data["IV" + str(i)], orig_inj, conv_inj)
        # 注射位置
        data["IL" + str(i)] = position_conv(data["IL" + str(i)], orig_inj, conv_inj)
    data["IT"] = data["IT"]
    data["ID"] = data["ID"]
    data["CT"] = data["CT"]
    # 保压参数
    for i in range(0, data["holding_stage"]):
        # 保压压力
        data["PP" + str(i)] = holding_pressure_conv(data["PP" + str(i)], orig_inj, conv_inj)
        # 保压速度
        data["PV" + str(i)] = holding_velocity_conv(data["PV" + str(i)], orig_inj, conv_inj)
        # 保压时间
        data["PT" + str(i)] = data["PT" + str(i)]
    # vp切换
    data["VPTM"] = VP_SWITCH_MAP[data["VPTM"]]            
    data["VPTL"] = position_conv(data["VPTL"], orig_inj, conv_inj)
    data["VPTT"] = data["VPTT"]
    data["VPTP"] = injection_pressure_conv(data["VPTP"], orig_inj, conv_inj)
    data["VPTV"] = injection_velocity_conv(data["VPTV"], orig_inj, conv_inj)
    for i in range(0, data["metering_stage"]):
        # 计量压力
        data["MP" + str(i)] = metering_pressure_conv(data["MP" + str(i)], orig_inj, conv_inj)
        # 螺杆转速
        data["MSR" + str(i)] = metering_screw_rotation_conv(data["MSR" + str(i)], orig_inj, conv_inj)
        # 计量背压
        data["MBP" + str(i)] = metering_back_pressure_conv(data["MBP" + str(i)], orig_inj, conv_inj)
        # 计量位置
        data["ML" + str(i)] = position_conv(data["ML" + str(i)], orig_inj, conv_inj)
    # 松退
    data["DMBM"] = DECOM_MAP[data["DMBM"]]
    data["DMAM"] = DECOM_MAP[data["DMAM"]]
    data["DPBM"] = decom_pressure_conv(data["DPBM"], orig_inj, conv_inj)
    data["DVBM"] = decom_velocity_conv(data["DVBM"], orig_inj, conv_inj)
    data["DDBM"] = position_conv(data["DDBM"], orig_inj, conv_inj)
    data["DTBM"] = data["DTBM"]
    data["DPAM"] = decom_pressure_conv(data["DPAM"], orig_inj, conv_inj)
    data["DVAM"] = decom_velocity_conv(data["DVAM"], orig_inj, conv_inj)
    data["DDAM"] = position_conv(data["DDAM"], orig_inj, conv_inj)
    data["DTAM"] = data["DTAM"]
    
    data["MD"] = data["MD"]
    data["MEL"] = position_conv(data["MEL"], orig_inj, conv_inj)


def conv_process_from_database(data: dict, orig_inj: dict, conv_inj: dict):
    # 注射参数
    for i in range(0, int(data["inject_para"]["injection_stage"])):
        # 注射压力
        data["inject_para"]["table_data"][0]["sections"][i] = injection_pressure_conv(data["inject_para"]["table_data"][0]["sections"][i] , orig_inj, conv_inj)
        # 注射速度
        data["inject_para"]["table_data"][1]["sections"][i] = injection_velocity_conv(data["inject_para"]["table_data"][1]["sections"][i], orig_inj, conv_inj)
        # 注射位置
        data["inject_para"]["table_data"][2]["sections"][i] = position_conv(data["inject_para"]["table_data"][2]["sections"][i], orig_inj, conv_inj)
    data["inject_para"]["injection_time"] = data["inject_para"]["injection_time"]
    data["inject_para"]["injection_delay_time"] = data["inject_para"]["injection_delay_time"]
    data["inject_para"]["cooling_time"] = data["inject_para"]["cooling_time"]
    # 保压参数
    for i in range(0, data["holding_para"]["holding_stage"]):
        # 保压压力
        data["holding_para"]["table_data"][0]["sections"][i] = holding_pressure_conv(data["holding_para"]["table_data"][0]["sections"][i], orig_inj, conv_inj)
        # 保压速度
        data["holding_para"]["table_data"][1]["sections"][i] = holding_velocity_conv(data["holding_para"]["table_data"][1]["sections"][i], orig_inj, conv_inj)
        # 保压时间
        data["holding_para"]["table_data"][2]["sections"][i] = data["holding_para"]["table_data"][2]["sections"][i]
    # vp切换
    data["VP_switch"]["VP_switch_mode"] = data["VP_switch"]["VP_switch_mode"]     
    data["VP_switch"]["VP_switch_position"] = position_conv(data["VP_switch"]["VP_switch_position"], orig_inj, conv_inj)
    data["VP_switch"]["VP_switch_time"] = data["VP_switch"]["VP_switch_time"]
    data["VP_switch"]["VP_switch_pressure"] = injection_pressure_conv(data["VP_switch"]["VP_switch_pressure"], orig_inj, conv_inj)
    data["VP_switch"]["VP_switch_velocity"] = injection_velocity_conv(data["VP_switch"]["VP_switch_velocity"], orig_inj, conv_inj)
    for i in range(0, data["metering_para"]["metering_stage"]):
        # 计量压力
        data["metering_para"]["table_data"][0]["sections"][i] = metering_pressure_conv(data["metering_para"]["table_data"][0]["sections"][i], orig_inj, conv_inj)
        # 螺杆转速
        data["metering_para"]["table_data"][1]["sections"][i] = metering_screw_rotation_conv(data["metering_para"]["table_data"][1]["sections"][i], orig_inj, conv_inj)
        # 计量背压
        data["metering_para"]["table_data"][2]["sections"][i] = metering_back_pressure_conv(data["metering_para"]["table_data"][2]["sections"][i], orig_inj, conv_inj)
        # 计量位置
        data["metering_para"]["table_data"][3]["sections"][i] = position_conv(data["metering_para"]["table_data"][3]["sections"][i], orig_inj, conv_inj)
    # 松退
    data["metering_para"]["decompressure_mode_before_metering"] = data["metering_para"]["decompressure_mode_before_metering"]
    data["metering_para"]["decompressure_mode_after_metering"] = data["metering_para"]["decompressure_mode_after_metering"]
    data["metering_para"]["decompressure_paras"][0]["pressure"] = decom_pressure_conv(data["metering_para"]["decompressure_paras"][0]["pressure"], orig_inj, conv_inj)
    data["metering_para"]["decompressure_paras"][0]["velocity"] = decom_velocity_conv(data["metering_para"]["decompressure_paras"][0]["velocity"], orig_inj, conv_inj)
    data["metering_para"]["decompressure_paras"][0]["distance"] = position_conv(data["metering_para"]["decompressure_paras"][0]["distance"], orig_inj, conv_inj)
    data["metering_para"]["decompressure_paras"][0]["time"] = data["metering_para"]["decompressure_paras"][0]["time"]
    data["metering_para"]["decompressure_paras"][1]["pressure"] = decom_pressure_conv(data["metering_para"]["decompressure_paras"][1]["pressure"], orig_inj, conv_inj)
    data["metering_para"]["decompressure_paras"][1]["velocity"] = decom_velocity_conv(data["metering_para"]["decompressure_paras"][1]["velocity"], orig_inj, conv_inj)
    data["metering_para"]["decompressure_paras"][1]["distance"] = position_conv(data["metering_para"]["decompressure_paras"][1]["distance"], orig_inj, conv_inj)
    data["metering_para"]["decompressure_paras"][1]["time"] = data["metering_para"]["decompressure_paras"][1]["time"]
    
    data["metering_para"]["metering_delay_time"] = data["metering_para"]["metering_delay_time"]
    data["metering_para"]["metering_ending_position"] = position_conv(data["metering_para"]["metering_ending_position"], orig_inj, conv_inj)


def conv_simple_format(process: dict):
    output: dict = {}
    injection_dict: dict = process.get('inject_para')
    output['injection_stage'] = injection_dict.get('injection_stage')
    for i in range(0, output['injection_stage']):
        output['IP' + str(i)] = injection_dict["table_data"][0]["sections"][i]
        output['IV' + str(i)] = injection_dict["table_data"][1]["sections"][i]
        output['IL' + str(i)] = injection_dict["table_data"][2]["sections"][i]
    output["IT"] = injection_dict["injection_time"]
    output["ID"] = injection_dict["injection_delay_time"]
    output["CT"] = injection_dict["cooling_time"]

    # 保压参数
    holding_dict: dict = process.get('holding_para')
    output['holding_stage'] = holding_dict.get('holding_stage')
    for i in range(0, output['holding_stage']):
        output['PP' + str(i)] = holding_dict["table_data"][0]["sections"][i]
        output['PV' + str(i)] = holding_dict["table_data"][1]["sections"][i]
        output['PT' + str(i)] = holding_dict["table_data"][2]["sections"][i]

    # VP切换
    VP_switch_dict: dict = process.get('VP_switch')
    output['VPTM'] = VP_switch_dict.get('VP_switch_mode')
    output['VPTT'] = VP_switch_dict.get('VP_switch_time')
    output['VPTL'] = VP_switch_dict.get('VP_switch_position')
    output['VPTP'] = VP_switch_dict.get('VP_switch_pressure')
    output['VPTV'] = VP_switch_dict.get('VP_switch_velocity')

    # 计量参数
    metering_dict: dict = process.get('metering_para')
    output['metering_stage'] = metering_dict.get('metering_stage')
    for i in range(0, output['metering_stage']):
        output['MP' + str(i)] = metering_dict["table_data"][0]["sections"][i]
        output['MSR' + str(i)] = metering_dict["table_data"][1]["sections"][i]
        output['MBP' + str(i)] = metering_dict["table_data"][2]["sections"][i]
        output['ML' + str(i)] = metering_dict["table_data"][3]["sections"][i]

    output['DMBM'] = metering_dict.get('decompressure_mode_before_metering')
    output['DMAM'] = metering_dict.get('decompressure_mode_after_metering')

    decom_dict = metering_dict['decompressure_paras']
    output['DPBM'] = decom_dict[0].get('pressure')
    output['DVBM'] = decom_dict[0].get('velocity')
    output['DDBM'] = decom_dict[0].get('distance')
    output['DTBM'] = decom_dict[0].get('time')
    output['DPAM'] = decom_dict[1].get('pressure')
    output['DVAM'] = decom_dict[1].get('velocity')
    output['DDAM'] = decom_dict[1].get('distance')
    output['DTAM'] = decom_dict[1].get('time')

    output['MD'] = metering_dict.get('metering_delay_time')
    output['MEL'] = metering_dict.get('metering_ending_position')

    # 温度参数
    temp_dict: dict = process.get('temp_para')
    output['barrel_temperature_stage'] = temp_dict.get('barrel_temperature_stage')
    for i in range(0, output['barrel_temperature_stage']):
        if i == 0:
            output['NT'] = temp_dict["table_data"][0]["sections"][i]
        else:
            output['BT' + str(i)] = temp_dict["table_data"][0]["sections"][i]
    return output


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

