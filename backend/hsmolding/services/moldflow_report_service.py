# 读取moldflowppt
# 读取moldflowtxt
from hsmolding.dao.moldflow_report_model import MoldFlowReportDoc
from hsmolding.utils.code.get_code import detectCode
import logging
import datetime
from hsmolding.const import (
    MOLDFLOW_RESULT_CH,
    ANALYTICAL_SEQUENCE, 
    MOLDFLOW_RESULT_DESC, 
    MOLDFLOW_RESULT_GROUP,
    MOLDFLOW_RESULT_UNIT,
    INJECT_REL,
    INJECT_ABS,
    HOLDING_SET,
    VELOCITY_UNIT_SET,
    POSITION_UNIT_SET,
    INJECT_ABS_LABEL,
    ANALYZE_DATA
)


analyze_data = {}


def get_moldflow_list(
    project_id=None,
    mold_flow_no=None,
    analytical_sequence=None,
    machine_trademark=None,
    poly_trademark=None,
    created_at=None,
    ):
    moldflow = MoldFlowReportDoc.objects.filter(deleted=0).order_by("-updated_at")
    if project_id:
        moldflow = moldflow.filter(project_id=project_id)
    if mold_flow_no:
        moldflow = moldflow.filter(mold_flow_no=mold_flow_no)
    if analytical_sequence:
        moldflow = moldflow.filter(technology__analytical_sequence=analytical_sequence)
    if machine_trademark:
        moldflow = moldflow.filter(machine__trademark=machine_trademark)
    if poly_trademark:
        moldflow = moldflow.filter(polymer__poly_trademark=poly_trademark)
    if created_at:
        moldflow = moldflow.filter(created_at__gte=datetime.datetime.combine(created_at, datetime.datetime.min.time()),created_at__lte=datetime.datetime.combine(created_at, datetime.datetime.max.time()))
    return [e.to_dict() for e in moldflow] if moldflow else None


def get_moldflow_dict(project_id, mold_flow_no):
    moldflow = get_moldflow(project_id, mold_flow_no)
    return moldflow.to_dict() if moldflow else None


def get_moldflow(project_id, mold_flow_no):
    moldflow = MoldFlowReportDoc.objects.filter(project_id=project_id,mold_flow_no=mold_flow_no).order_by("-updated_at").first()
    return moldflow if moldflow else None


def update_moldflow(params):
    project_id = params.get("project_id")
    mold_flow_no = "".join(params.get("mold_flow_no"))
    moldflow = get_moldflow(project_id, mold_flow_no)
    if moldflow:
        moldflow.update(**params)
        moldflow = get_moldflow(project_id, mold_flow_no)
    return moldflow


def add_moldflow(params):
    moldflow = update_moldflow(params)
    if not moldflow:
        moldflow = MoldFlowReportDoc(**params)
        try:
            moldflow.save()
        except Exception as e:
            logging.error(e)
    return moldflow.to_dict() if moldflow else None


def delete_moldflow(project_id):
    if project_id:
        moldflow = get_moldflow(project_id)
        if moldflow:
            moldflow.delete()


def get_process_setting(txt_path, language="UTF-8"):
    process_result = []
    for line in open(txt_path, encoding=language):
        process = {}
        # '工艺设置'
        if "Process:" in line:
            current_result = translate_result(line, 8)
            if current_result:
                process["id"] = current_result[0]
                process["value"] = current_result[1]
                process_result.append(process)
    return process_result


def get_inject_para(txt_path, language="UTF-8",process_setting=None):
    i=0
    inject_para = []
    inject_lines = []
    velocity_unit = "mm/s"
    position_unit = "mm"
    fill_control = get_tcode(process_setting, 10109)
    fill_set_code = None
    if fill_control == "5":
        # By是10602
        fill_control_by = get_tcode(process_setting, 10602)
        fill_set_code = INJECT_REL.get(fill_control_by)
        velocity_unit = "%"
        position_unit = "%"
    if fill_control == "6":
        # By是10603
        fill_control_by = get_tcode(process_setting, 10603)
        fill_set_code = INJECT_ABS.get(fill_control_by)
        velocity_unit = VELOCITY_UNIT_SET.get(fill_set_code)
        position_unit = POSITION_UNIT_SET.get(fill_set_code)
    for line in open(txt_path, encoding=language):
        # '注射'
        if str(fill_set_code)+"-Injection Pressure and Position:" in line:
            i += 1
        if i == 1:
            inject_lines.append(line)
            if "End" in line:
                break
    velocity_sec = []
    position_sec = []
    stage = 0
    for i in range(2, len(inject_lines), 4):
        if "Value" in inject_lines[i]:
            stage += 1
            velocity_sec.append(float(inject_lines[i][9:].strip()))
            position_sec.append(float(inject_lines[i+2][9:].strip()))
    # 单位需要和tcode匹配
    inject_para = [
        {"label": "速度", "unit": velocity_unit, "sections": velocity_sec, "max": None},
        {"label": INJECT_ABS_LABEL.get(fill_set_code), "unit": position_unit, "sections": position_sec, "max": None}
    ]
    return inject_para, stage, velocity_unit, velocity_sec, position_unit, position_sec


def get_holding_para(txt_path, language="UTF-8",process_setting=None):
    i = 0
    holding_para = []
    lines = []
    holding_control = get_tcode(process_setting, 10704)
    holding_set_code = HOLDING_SET.get(holding_control)
    for line in open(txt_path, encoding=language):
        if str(holding_set_code)+"-Pack Pressure and Time:" in line:
            i += 1
        if i == 1:
            lines.append(line)
            if "End" in line:
                break
    pressure_sec = []
    time_sec = []
    stage = 0
    for i in range(2, len(lines), 4):
        if "Value" in lines[i]:
            stage += 1
            pressure_sec.append(float(lines[i][9:].strip()))
            time_sec.append(float(lines[i+2][9:].strip()))
    # 单位需要和tcode匹配
    holding_para = [
        {"label": "压力", "unit": "MPa" if holding_control in ["2", "1"] else "%", "sections": pressure_sec, "max": None},
        {"label": "时间", "unit": "s", "sections": time_sec, "max": None}
    ]
    return holding_para, stage, holding_control, pressure_sec, time_sec


def get_process_data(txt_path, language="UTF-8",process_setting=None):
    inject_para,inject_stage, velocity_unit, velocity_sec, position_unit, position_sec = get_inject_para(txt_path, language=language,process_setting=process_setting)
    holding_para, holding_stage, holding_control, pressure_sec, time_sec = get_holding_para(txt_path, language=language,process_setting=process_setting)
    process_data = {
        "inject_stage":inject_stage,
        "holding_stage":holding_stage,
        "max_inject_stage_option":5,
        "max_holding_stage_option":5,
        "inject_para":inject_para,
        "holding_para":holding_para,
    }
    setting_result = {
        "velocity_unit":velocity_unit,
        "velocity_sec":velocity_sec,
        "position_unit":position_unit,
        "position_sec":position_sec,

        "holding_control":holding_control,
        "pressure_sec":pressure_sec,
        "time_sec":time_sec
    }
    return process_data, setting_result 


def get_start_ram_position(txt_path, language="UTF-8", log_content=None):
    i = 0
    lines = []
    cushion_warning_limit = None
    start_ram_position = None
    for line in open(txt_path, encoding=language):
        # "10306-Start Ram Position:"
        # "10304-V/P Switch:"
        if log_content in line:
            i += 1
        if i == 1:
            lines.append(line)
            if "End" in line:
                break
    for i in range(2, len(lines), 4):
        if "Value" in lines[i]:
            cushion_warning_limit = float(lines[i][9:].strip())
            start_ram_position = float(lines[i+2][9:].strip())
    return cushion_warning_limit,start_ram_position


def get_analyze(txt_path, language="UTF-8"):
    analyze = ""
    machine_trademark = ""
    machine_manufacturer = ""
    material_trademark = ""
    material_abbreviation = ""
    for line in open(txt_path, encoding=language):
        # 分析序列
        if "Analyze:" in line:
            analyze = line[8:]
        # 机器
        if "machine trademark:" in line:
            machine_trademark = line[18:]
        if "machine manufacturer:" in line:
            machine_manufacturer = line[21:]
        # 材料牌号 
        if "Material:" in line:
            material_trademark = line[9:]
        if "material-1999:" in line:
            material_abbreviation = line[14:]
    return analyze, machine_trademark, machine_manufacturer, material_trademark, material_abbreviation


def get_tcode(result, tcode):
    for per_result in result:
        if str(tcode) == per_result.get("id"):
            return per_result.get("value") if per_result else None


def get_analyze_data(plot):
    global analyze_data
    if plot.get("id") in ANALYZE_DATA.keys():
        analyze_data[ANALYZE_DATA.get(plot.get("id"))] = round(float(plot.get("max_value")),2)


def get_result(txt_path, language="UTF-8"):
    result = []
    flow_result = []
    cool_result = []
    warp_result = []
    test_list = []
    result_tcode = {}
    for line in open(txt_path, encoding=language):
        plot = {}
        # 模流分析结果
        if "Result:" in line:
            current_result = translate_result(line, 7)
            plot["id"] = current_result[0]
            plot["max_value"] = current_result[1]  
            get_analyze_data(plot)
            plot["name"] = MOLDFLOW_RESULT_CH.get(int(current_result[0]))
            plot["desc"] = MOLDFLOW_RESULT_DESC.get(int(current_result[0]))
            plot["unit"] = MOLDFLOW_RESULT_UNIT.get(int(current_result[0]))
            result_tcode[current_result[0]] = current_result[1]
            if MOLDFLOW_RESULT_GROUP.get(int(current_result[0])) == "流动":
                flow_result.append(plot)
            if MOLDFLOW_RESULT_GROUP.get(int(current_result[0])) == "冷却":
                cool_result.append(plot)
            if MOLDFLOW_RESULT_GROUP.get(int(current_result[0])) == "翘曲":
                warp_result.append(plot)
            test_list.append(current_result[0])
    if flow_result:
        result.append(
            {
                "name":"流动",
                "children":flow_result
            }
        )
    if cool_result:
        result.append(
            {
                "name":"冷却",
                "children":cool_result
            }
        )
    if warp_result:
        result.append(
            {
                "name":"翘曲",
                "children":warp_result
            }
        )
    
    return result,test_list, result_tcode
    

def translate_result(line, num):
    # 模流分析结果:5082-3.73749993741512E-02
    # 如果有E-02这样的,需要先处理一下
    values = line[num:].rstrip().split("--")
    return values


def get_mold_flow_data(txt_path):
    global analyze_data
    # 在读取之前,先确定文档的编码方式
    language = detectCode(txt_path)
    result, test_list, result_tcode = get_result(txt_path, language=language)
    process_setting = get_process_setting(txt_path, language=language)
    analyze, machine_trademark, machine_manufacturer, material_trademark, material_abbreviation = get_analyze(txt_path, language=language)
    process_data,setting_result = get_process_data(txt_path, language=language, process_setting=process_setting)
    cushion_warning_limit,start_ram_position = get_start_ram_position(txt_path, language=language, log_content="10306-Start Ram Position:")
    node, pressure = get_start_ram_position(txt_path, language=language, log_content="10304-V/P Switch:")
    mold_flow_data = dict({
        "machine": {
            "id": None,
            "trademark": machine_trademark,
            "data_source": None,
            "manufacturer": machine_manufacturer,
            "machine_type": None,
        },
        "polymer": {
            "id": None,
            "poly_trademark": material_trademark,
            "max_melt_temperature": None,
            "min_melt_temperature": None,
            "recommend_melt_temperature": None,
            "max_mold_temperature": None,
            "min_mold_temperature": None,
            "recommend_mold_temperature": None,
            "max_shear_linear_speed": None,
            "min_shear_linear_speed": None,
            "recommend_shear_linear_speed": None,
            "recommend_injection_rate": None,
            "degradation_temperature": None,
            "ejection_temperature": None,
            "max_sheer_rate": None,
            "max_sheer_stress": None,
            "recommend_back_pressure": None,
            "barrel_residence_time": None,
        },
        "technology": {
            "analytical_sequence": ANALYTICAL_SEQUENCE.get(analyze.strip()),
            "fill_holding": {
                "surface_temperature": get_tcode(process_setting, 11108),
                "melt_temperature": get_tcode(process_setting, 11002),
                "fill_control": get_tcode(process_setting, 10109),
                "inject_time": get_tcode(process_setting, 10100),
                "flow_rate": get_tcode(process_setting, 10107),
                "control_options": get_tcode(process_setting, 10603),
                "reference": get_tcode(process_setting, 10110),
                "nominal_injection_time": get_tcode(process_setting, 10100),
                "nominal_rate": get_tcode(process_setting, 10107),
                "injection_volume": get_tcode(process_setting, 10302),
                "screw_diameter": get_tcode(process_setting, 10008),
                "start_screw_diameter": get_tcode(process_setting, 10200),
                "packing_warning_limit": cushion_warning_limit,
                "starting_screw_position": start_ram_position,
                "speed_switching": get_tcode(process_setting, 10310),
                "fill_volume": get_tcode(process_setting, 10308),
                "screw_position": get_tcode(process_setting, 10313),
                "injection_pressure": get_tcode(process_setting, 10307),
                "hydraulic_pressure": get_tcode(process_setting, 10303),
                "clamping_force": get_tcode(process_setting, 10305),
                "injection_time": get_tcode(process_setting, 10309),
                "node": node,
                "pressure": pressure,
                "pressure_holding_control": get_tcode(process_setting, 10704),
                "cooling_time": get_tcode(process_setting, 11109),
                "cool_time": get_tcode(process_setting, 10102),
            },
            "fill": {
                "surface_temperature": get_tcode(process_setting, 11108),
                "melt_temperature": get_tcode(process_setting, 11002),
                "fill_control": get_tcode(process_setting, 10109),
                "inject_time": get_tcode(process_setting, 10100),
                "flow_rate": get_tcode(process_setting, 10107),
                "control_options": get_tcode(process_setting, 10603),
                "reference": get_tcode(process_setting, 10110),
                "nominal_injection_time": get_tcode(process_setting, 10100),
                "nominal_rate": get_tcode(process_setting, 10107),
                "injection_volume": get_tcode(process_setting, 10302),
                "screw_diameter": get_tcode(process_setting, 10008),
                "start_screw_diameter": get_tcode(process_setting, 10200),
                "packing_warning_limit": cushion_warning_limit,
                "starting_screw_position": start_ram_position,
                "speed_switching": get_tcode(process_setting, 10310),
                "fill_volume": get_tcode(process_setting, 10308),
                "screw_position": get_tcode(process_setting, 10313),
                "injection_pressure": get_tcode(process_setting, 10307),
                "hydraulic_pressure": get_tcode(process_setting, 10303),
                "clamping_force": get_tcode(process_setting, 10305),
                "injection_time": get_tcode(process_setting, 10309),
                "node": node,
                "pressure": pressure,
                "pressure_holding_control": get_tcode(process_setting, 10704),
            },
            "cooling": {
                "melt_temperature": get_tcode(process_setting, 11002),
                "mold_open_time": get_tcode(process_setting, 10104),
                "injection_holding_cooling_time": get_tcode(process_setting, 11112),
                "injection_holding_cool_time": get_tcode(process_setting, 13312),
            },
            "fill_holding_warping": {
                "surface_temperature": get_tcode(process_setting, 11108),
                "melt_temperature": get_tcode(process_setting, 11002),
                "fill_control": get_tcode(process_setting, 10109),
                "inject_time": get_tcode(process_setting, 10100),
                "flow_rate": get_tcode(process_setting, 10107),
                "control_options": get_tcode(process_setting, 10603),
                "reference": get_tcode(process_setting, 10110),
                "nominal_injection_time": get_tcode(process_setting, 10100),
                "nominal_rate": get_tcode(process_setting, 10107),
                "injection_volume": get_tcode(process_setting, 10302),
                "screw_diameter": get_tcode(process_setting, 10008),
                "start_screw_diameter": get_tcode(process_setting, 10200),
                "packing_warning_limit": cushion_warning_limit,
                "starting_screw_position": start_ram_position,
                "speed_switching": get_tcode(process_setting, 10310),
                "fill_volume": get_tcode(process_setting, 10308),
                "screw_position": get_tcode(process_setting, 10313),
                "injection_pressure": get_tcode(process_setting, 10307),
                "hydraulic_pressure": get_tcode(process_setting, 10303),
                "clamping_force": get_tcode(process_setting, 10305),
                "injection_time": get_tcode(process_setting, 10309),
                "node": node,
                "pressure": pressure,
                "pressure_holding_control": get_tcode(process_setting, 10704),
                "cooling_time": get_tcode(process_setting, 11109),
                "cool_time": get_tcode(process_setting, 10102),

                "warping_analysis_type": get_tcode(process_setting, 601),
                "parallel_thread": get_tcode(process_setting, 641),
                "amg_select": get_tcode(process_setting, 621),
                "thread_count": get_tcode(process_setting, 642),
            },
            "cooling_fill_holding_warping": {
                "melt_temperature": get_tcode(process_setting, 11002),
                "mold_open_time": get_tcode(process_setting, 10104),
                "injection_holding_cooling_time": get_tcode(process_setting, 11112),
                "injection_holding_cool_time": get_tcode(process_setting, 13312),

                "fill_control": get_tcode(process_setting, 10109),
                "inject_time": get_tcode(process_setting, 10100),
                "flow_rate": get_tcode(process_setting, 10107),
                "control_options": get_tcode(process_setting, 10603),
                "reference": get_tcode(process_setting, 10110),
                "nominal_injection_time": get_tcode(process_setting, 10100),
                "nominal_rate": get_tcode(process_setting, 10107),
                "injection_volume": get_tcode(process_setting, 10302),
                "screw_diameter": get_tcode(process_setting, 10008),
                "start_screw_diameter": get_tcode(process_setting, 10200),
                "packing_warning_limit": cushion_warning_limit,
                "starting_screw_position": start_ram_position,
                "speed_switching": get_tcode(process_setting, 10310),
                "fill_volume": get_tcode(process_setting, 10308),
                "screw_position": get_tcode(process_setting, 10313),
                "injection_pressure": get_tcode(process_setting, 10307),
                "hydraulic_pressure": get_tcode(process_setting, 10303),
                "clamping_force": get_tcode(process_setting, 10305),
                "injection_time": get_tcode(process_setting, 10309),
                "node": node,
                "pressure": pressure,
                "pressure_holding_control": get_tcode(process_setting, 10704),

                "warping_analysis_type": get_tcode(process_setting, 601),
                "parallel_thread": get_tcode(process_setting, 641),
                "amg_select": get_tcode(process_setting, 621),
                "thread_count": get_tcode(process_setting, 642),
            },
            "cooling_fem": {
                "melt_temperature": get_tcode(process_setting, 11002),
                "mold_open_time": get_tcode(process_setting, 10104),
                "mold_close_time": get_tcode(process_setting, 63185),
                "injection_holding_cooling_time": get_tcode(process_setting, 11112),
                "injection_holding_cool_time": get_tcode(process_setting, 13312),
                "mold_temperature": get_tcode(process_setting, 11113),
            },
            "cooling_fem_fill_holding_warping": {
                "melt_temperature":get_tcode(process_setting, 11002),
                "mold_open_time": get_tcode(process_setting, 10104),
                "mold_close_time": get_tcode(process_setting, 63185),
                "injection_holding_cooling_time": get_tcode(process_setting, 11112),
                "injection_holding_cool_time": get_tcode(process_setting, 13312),
                "mold_temperature": get_tcode(process_setting, 11113),

                "fill_control": get_tcode(process_setting, 10109),
                "inject_time": get_tcode(process_setting, 10100),
                "flow_rate": get_tcode(process_setting, 10107),
                "control_options": get_tcode(process_setting, 10603),
                "reference": get_tcode(process_setting, 10110),
                "nominal_injection_time": get_tcode(process_setting, 10100),
                "nominal_rate": get_tcode(process_setting, 10107),
                "injection_volume": get_tcode(process_setting, 10302),
                "screw_diameter": get_tcode(process_setting, 10008),
                "start_screw_diameter": get_tcode(process_setting, 10200),
                "packing_warning_limit": cushion_warning_limit,
                "starting_screw_position": start_ram_position,
                "speed_switching": get_tcode(process_setting, 10310),
                "fill_volume": get_tcode(process_setting, 10308),
                "screw_position": get_tcode(process_setting, 10313),
                "injection_pressure": get_tcode(process_setting, 10307),
                "hydraulic_pressure": get_tcode(process_setting, 10303),
                "clamping_force": get_tcode(process_setting, 10305),
                "injection_time": get_tcode(process_setting, 10309),
                "node": node,
                "pressure": pressure,
                "pressure_holding_control": get_tcode(process_setting, 10704),

                "warping_analysis_type": get_tcode(process_setting, 601),
                "parallel_thread": get_tcode(process_setting, 641),
                "amg_select": get_tcode(process_setting, 621),
                "thread_count":get_tcode(process_setting, 642),
            },
            "process_data":process_data
        },
        "result": result,
        "test_list": test_list,
        "analyze_data":analyze_data
    })
    params = {}
    params["mold_flow_data"] = mold_flow_data
    params["process_data"] = process_data
    params["material_trademark"] = material_trademark
    params["material_abbreviation"] = material_abbreviation
    params["machine_manufacturer"] = machine_manufacturer
    params["machine_trademark"] = machine_trademark
    params["process_setting"] = process_setting
    params["start_ram_position"] = start_ram_position
    params["setting_result"] = setting_result
    params["global_txt_path"] = txt_path
    params["result_tcode"] = result_tcode
    params["cooling_time"] = get_tcode(process_setting, 10102)
    return params


def get_prompt_list_of_column(column: str, input_str: str, project_id: int = None):
    items = []
    if project_id:
        query = MoldFlowReportDoc.objects.filter(project_id=project_id).filter(deleted=0) # 过滤公司&已删除
    else:
        query = MoldFlowReportDoc.objects.all()
    if column == "mold_flow_no":
        items = query.filter(mold_flow_no__icontains=input_str).values_list("mold_flow_no")
    if column == "analytical_sequence":
        items = set(query.filter(technology__analytical_sequence__icontains=input_str).values_list("technology__analytical_sequence"))
    if column == "mold_flow_machine_trademark":
        items = set(query.filter(machine__trademark__icontains=input_str).values_list("machine__trademark"))
    if column == "poly_trademark":
        items = set(query.filter(polymer__poly_trademark__icontains=input_str).values_list("polymer__poly_trademark"))
    return list(items)
