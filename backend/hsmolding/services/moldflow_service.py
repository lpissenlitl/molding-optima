from hsmolding.dao.moldflow_model import MoldFlowDoc

import re
import logging
import chardet


def get_moldflow_dict(project_id):
    moldflow = get_moldflow(project_id)
    return moldflow.to_dict() if moldflow else None


def get_moldflow(project_id):
    moldflow = MoldFlowDoc.objects.filter(project_id=project_id).order_by("-updated_at").first()
    return moldflow if moldflow else None


def update_moldflow(params):
    project_id = params.get("project_id")
    moldflow = get_moldflow(project_id)
    if moldflow:
        moldflow.update(**params)
        moldflow = get_moldflow(project_id)
    return moldflow


def add_moldflow(params):
    moldflow = update_moldflow(params)
    if not moldflow:
        moldflow = MoldFlowDoc(**params)
        try:
            moldflow.save()
        except Exception as e:
            logging.error(e)
    return moldflow.to_dict() if moldflow else None


def delte_moldflow(project_id):
    if project_id:
        moldflow = get_moldflow(project_id)
        if moldflow:
            moldflow.delete()


def read_moldflow_time_part(txt_path=None, language="UTF-8"):
    i = 0
    lines = []

    for line in open(txt_path, encoding=language):
        if "Calculating 3D fluxes" in line or "正在计算 3D 通量" in line:
            i += 1
        if i == 1:
            lines.append(line)
        if "|External  |Cycle time|Avg temp  " in line or "|   外部   | 周期时间 | 平均温度 " in line:
            break
    if i > 0:
        time_part = re.findall(r"\d+\.?\d*", lines[-5] if lines else None)
        return {"time_part": time_part[0] if time_part else None}


def read_moldflow_cycle_time(txt_path=None, language="UTF-8"):
    i = 0
    lines = []
    for line in open(txt_path, encoding=language):
        if "Heat removal through the outer boundaries" in line or "通过外边界的热量排除" in line:
            i += 1
        if i == 1:
            lines.append(line)
        if "Cycle time                                           =" in line or "周期时间                                  =" in line:
            break
    if i > 0:
        cycle_time = re.findall(r"\d+\.?\d*", lines[-1] if lines else None)
        return {"cycle_time": cycle_time[0] if cycle_time else None}


def read_moldflow_temperature(txt_path=None, language="UTF-8"):
    melt_temperature = None
    mold_temperature = None
    injection_packing_cooling_time = None
    cooling_time = None
    polymer_trademark = None
    max_clamping_force = None
    injection_pressure = None
    single_volume = None
    product_projected_area = None
    for line in open(txt_path, encoding=language):
        if "Melt temperature" in line or "熔体温度" in line:
            melt_temperature = re.findall(r"\d+\.?\d*", line)
        if "Mold temperature" in line or "模具温度" in line:
            mold_temperature = re.findall(r"\d+\.?\d*", line)
        if "Injection + packing + cooling time " in line or "注射 + 保压 + 冷却时间" in line:
            injection_packing_cooling_time = re.findall(r"\d+\.?\d*", line)
        if "Cooling time                                       =" in line or "冷却时间                               =" in line:
            cooling_time = re.findall(r"\d+\.?\d*", line)
        if "Trade name" in line:
            polymer_trademark = line[23:]
        if "牌号" in line:
            polymer_trademark = line[14:]
        # 在注射期间最大的锁模力
        # if "Maximum Clamp force" in line:
        #     max_clamping_force = re.findall(r"\d+\.?\d*", line)
        # 注塑机最大锁模力
        if "Maximum machine clamp force" in line or "最大注塑机锁模力" in line:
            if "E+" not in line:
                max_clamping_force = re.findall(r"\d+\.?\d*", line)
            else:
                max_clamping_force = re.findall(r"\d+\.?\d+E[+-]\d*", line)
        # 注塑机最大注射压力
        if "Maximum injection pressure" in line or "最大注射压力" in line:
            if "E+" not in line:
                injection_pressure = re.findall(r"\d+\.?\d*", line)
            else:
                injection_pressure = re.findall(r"\d+\.?\d+E[+-]\d*", line)
        if "Total volume" in line or "总体积" in line:
            single_volume = re.findall(r"\d+\.?\d*", line)
        if "Total projected area " in line or "总投影面积" in line:
            product_projected_area = re.findall(r"\d+\.?\d*", line)

    return {
        "melt_temperature": melt_temperature[0] if melt_temperature else None,
        "mold_temperature": mold_temperature[0] if melt_temperature else None,
        "injection_packing_cooling_time": injection_packing_cooling_time[0] if injection_packing_cooling_time else None,
        "polymer_trademark": polymer_trademark,
        "cooling_time": cooling_time[0] if cooling_time else None,
        "max_clamping_force":max_clamping_force[0] if max_clamping_force else None,
        "injection_pressure":injection_pressure[0] if injection_pressure else None,
        "single_volume":single_volume[0] if single_volume else None,
        "product_projected_area": product_projected_area[0] if product_projected_area else None
    }


def read_moldflow_injection_time(txt_path=None, language="UTF-8"):
    i = 0
    lines = []
    for line in open(txt_path, encoding=language):
        if "End of filling phase results summary :" in line or "充填阶段结束的结果摘要" in line:
            i += 1
        if i == 1:
            lines.append(line)
        if "   Injection pressure                                 =" in line or "   注射压力                               =" in line:
            break
    if lines:
        injection_time = re.findall(r"\d+\.?\d*", lines[-4])
        injection_pressure = re.findall(r"\d+\.?\d*", lines[-1])
        return {"injection_time": injection_time[0] if injection_time else None, "injection_pressure": injection_pressure[0] if injection_pressure else None}


def read_moldflow_pressure(txt_path=None, language="UTF-8"):
    injection_pressure = read_moldflow_injection_time(txt_path,language).get("injection_pressure") if read_moldflow_injection_time(txt_path,language) else None
    actual = 0
    percent = 0
    line_num = 0
    lines = []
    holding_time = []
    holding_pressure = []
    for line in open(txt_path, encoding=language):
        # 给的实际压力值
        if "duration            pressure" in line or "持续时间            压力" in line:
            actual += 1
        # 给的比例,用注射压力乘以百分比
        if "duration  % filling pressure" in line:
            percent += 1
        if actual == 1 or percent == 1:
            lines.append(line)
            line_num += 1
        if "Cooling time:" in line or "冷却时间" in line:
            break
    if lines:
        total_holding_time = 0
        for num in range(2, line_num - 2):
            holding = re.findall(r"\d+\.?\d*", lines[num])
            holding_time.append(holding[0])
            if actual == 1:
                holding_pressure.append(holding[1])
            if percent == 1:
                holding_pressure.append(str(float(holding[1]) / 100 * float(injection_pressure))) if injection_pressure else None
            total_holding_time = total_holding_time + float(holding[0])

        return {"holding_time": holding_time, "holding_pressure": holding_pressure, "total_holding_time": total_holding_time}


def read_moldflow(txt_path):
    # 查看文件的编码类型
    with open(txt_path, 'rb') as f:
        encode = chardet.detect((f.read()))
    injection_packing_cooling_time = None
    cooling_time = None
    total_holding_time = None
    params = {}
    time_part = read_moldflow_time_part(txt_path, language=encode.get("encoding"))
    cycle_time = read_moldflow_cycle_time(txt_path, language=encode.get("encoding"))
    temperature = read_moldflow_temperature(txt_path, language=encode.get("encoding"))
    injection_time = read_moldflow_injection_time(txt_path, language=encode.get("encoding"))
    pressure = read_moldflow_pressure(txt_path, language=encode.get("encoding"))
    if time_part:
        time_part = time_part.get("time_part")
    if cycle_time:
        params["cycle_time"] = cycle_time.get("cycle_time")
    if temperature:
        params["melt_temp"] = temperature.get("melt_temperature")
        params["cavity_temp"] = temperature.get("mold_temperature")
        params["core_temp"] = temperature.get("mold_temperature")
        injection_packing_cooling_time = temperature.get("injection_packing_cooling_time")
        cooling_time = temperature.get("cooling_time")
        params["polymer_trademark"] = temperature.get("polymer_trademark")
        params["injection_pressure"] = temperature.get("injection_pressure")
        params["max_clamping_force"] = temperature.get("max_clamping_force")
        params["product_projected_area"] = temperature.get("product_projected_area")
        params["single_volume"] = temperature.get("single_volume")
    if injection_time:
        params["injection_time"] = injection_time.get("injection_time")
        # 这是注射时的压力,页面实际展示的注塑机 最大注射压力
    holding_pressure_list = []
    holding_time_list = []
    if pressure:
        # 用时间来控制保压
        params["holding_time"] = pressure.get("holding_time")[-1]
        holding_pressure_list = pressure.get("holding_pressure")
        holding_time_list = pressure.get("holding_time")
        total_holding_time = pressure.get("total_holding_time")
    if injection_packing_cooling_time and total_holding_time and params["injection_time"]:
        params["cooling_time"] = str(
            round(float(injection_packing_cooling_time) - float(params.get("injection_time")) - float(total_holding_time),2)
        )
    if cooling_time:
        params["cooling_time"] = cooling_time
    inject_para = [             
        { "label": "压力", "unit": "MPa", "sections": [] },
        { "label": "速度", "unit": "cm³/s", "sections": [] }] 
    holding_para = [             
        { "label": "压力", "unit": "MPa", "sections": holding_pressure_list },
        { "label": "时间", "unit": "s", "sections": holding_time_list }] 
    params["inject_para"] = inject_para
    params["holding_para"] = holding_para
    
    return params
