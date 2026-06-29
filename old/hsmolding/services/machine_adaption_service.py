# 模具的注塑机适配
# 工艺的注塑机适配
from hsmolding.services.machine_service import get_machine
from hsmolding.dao.reservation_model import MachineAdaptionDoc
import math
import logging


process_table_data = [
    {
        "desc": "参数",
        "value1": "原始工艺",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
    },
    {
        "desc": "",
        "value1": "值",
        "value2": "单位",
        "value3": "值",
        "value4": "单位",
        "value5": "值",
        "value6": "单位",
        "value7": "值",
        "value8": "单位",
        "value9": "值",
        "value10": "单位",
        "value11": "值",
        "value12": "单位",
    },
    {
        "desc": "注射量",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "VP切换位置",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "垫料",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "注射时间",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "设置注射速度",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "设置注射压力",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "保压",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "背压",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "螺杆转速",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "是否适配",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "工艺编号",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
    {
        "desc": "工艺id",
        "value1": "",
        "value2": "",
        "value3": "",
        "value4": "",
        "value5": "",
        "value6": "",
        "value7": "",
        "value8": "",
        "value9": "",
        "value10": "",
        "value11": "",
        "value12": "",
    },
]
process_color_data = [
    {
        "desc": "参数",
    },
    {
        "desc": "",
    },
    {
        "desc": "注射量",
    },
    {
        "desc": "VP切换位置",
    },
    {
        "desc": "垫料",
    },
    {
        "desc": "注射时间",
    },
    {
        "desc": "设置注射速度",
    },
    {
        "desc": "设置注射压力",
    },
    {
        "desc": "保压",
    },
    {
        "desc": "背压",
    },
    {
        "desc": "螺杆转速",
    },
    {
        "desc": "是否适配",
    },
]


def get_machine_adaption_dict(p_id, adaption_type, adaption_no=None):
    machine_adaption = get_machine_adaption(p_id, adaption_type, adaption_no)
    return machine_adaption.to_dict() if machine_adaption else None


def get_machine_adaption(p_id, adaption_type, adaption_no=None):
    machine_adaption = MachineAdaptionDoc.objects.filter(p_id=p_id,adaption_type=adaption_type)
    if adaption_no and machine_adaption:
        machine_adaption = machine_adaption.filter(adaption_no=adaption_no)
    machine_adaption = machine_adaption.order_by("-updated_at").first()
    return machine_adaption if machine_adaption else None


def update_machine_adaption(params):
    p_id = params.get("p_id")
    adaption_type = params.get("adaption_type")
    adaption_no = params.get("adaption_no")
    machine_adaption = get_machine_adaption(p_id, adaption_type, adaption_no)
    if machine_adaption:
        machine_adaption.update(**params)
        machine_adaption = get_machine_adaption(p_id, adaption_type, adaption_no)
    return machine_adaption


def add_machine_adaption(params):
    machine_adaption = update_machine_adaption(params)
    if not machine_adaption:
        machine_adaption = MachineAdaptionDoc(**params)
        try:
            machine_adaption.save()
        except Exception as e:
            logging.error(e)
    return machine_adaption.to_dict() if machine_adaption else None


def delete_machine_adaption(project_id):
    if project_id:
        machine_adaption = get_machine_adaption(project_id)
        if machine_adaption:
            machine_adaption.delete()


# 主要考虑:
# 1.注射量
# 2.V/P切换位置
# 3.垫料
# 4.注射时间
# 5.设定注射速度
# 6.实际峰值压力
# 7.设定注射压力
# 8.保压
# 9.保压时间
# 10.背压
# 11.螺杆转速
def calculate_adaption_process(process, process_no):
    global process_table_data
    global process_color_data
    global machine_no
    not_adapted = 0
    machine_info = get_machine(process.get("precondition").get("machine_id"))
    injectors_info = machine_info.get("injectors_info")
    setting_item = process.get("process_detail")

    set_unit(machine_info, machine_no)
    process_table_data[0]["value"+str(math.ceil(machine_no/2))] = machine_info.get("trademark")
    if setting_item.get("metering_para").get("metering_ending_position"):
        process_table_data[2]["value"+str(machine_no)] = str(setting_item.get("metering_para").get("metering_ending_position"))
        if injectors_info[0].get("max_injection_stroke") and injectors_info[0].get("max_injection_stroke") < setting_item.get("metering_para").get("metering_ending_position"):
            not_adapted = 1
            process_color_data[2]["value"+str(machine_no)] = "red"
        else:
            process_color_data[2]["value"+str(machine_no)] = "rgb(66, 237, 28)"

    if setting_item.get("VP_switch").get("VP_switch_position"):
        process_table_data[3]["value"+str(machine_no)] = str(setting_item.get("VP_switch").get("VP_switch_position"))

    # 工艺参数中没有垫料
    process_table_data[4]["value"+str(machine_no)] = ""

    # 注塑机中没有最大注射时间这个参数
    process_table_data[5]["value"+str(machine_no)] = str(setting_item.get("inject_para").get("injection_time"))

    max_injection_velocity = get_max(setting_item.get("inject_para").get("table_data")[1].get("sections"))
    if max_injection_velocity:
        process_table_data[6]["value"+str(machine_no)] = str(max_injection_velocity)
        if injectors_info[0].get("max_set_injection_velocity") < max_injection_velocity:
            not_adapted = 1
            process_color_data[6]["value"+str(machine_no)] = "red"
        else:
            process_color_data[6]["value"+str(machine_no)] = "rgb(66, 237, 28)"

    max_injection_pressure = get_max(setting_item.get("inject_para").get("table_data")[0].get("sections"))
    if max_injection_pressure:
        process_table_data[7]["value"+str(machine_no)] = str(max_injection_pressure)
        if injectors_info[0].get("max_set_injection_pressure") < max_injection_pressure:
            not_adapted = 1
            process_color_data[7]["value"+str(machine_no)] = "red"
        else:
            process_color_data[7]["value"+str(machine_no)] = "rgb(66, 237, 28)"

    max_holding_pressure = get_max(setting_item.get("holding_para").get("table_data")[0].get("sections"))
    if max_holding_pressure:
        process_table_data[8]["value"+str(machine_no)] = str(max_holding_pressure)
        if injectors_info[0].get("max_set_holding_pressure") < max_holding_pressure:
            not_adapted = 1
            process_color_data[8]["value"+str(machine_no)] = "red"
        else:
            process_color_data[8]["value"+str(machine_no)] = "rgb(66, 237, 28)"

    max_metering_back_pressure = get_max(setting_item.get("metering_para").get("table_data")[2].get("sections"))
    if max_metering_back_pressure:
        process_table_data[9]["value"+str(machine_no)] = str(max_metering_back_pressure)
        if injectors_info[0].get("max_set_metering_back_pressure") < max_metering_back_pressure:
            not_adapted = 1
            process_color_data[9]["value"+str(machine_no)] = "red"
        else:
            process_color_data[9]["value"+str(machine_no)] = "rgb(66, 237, 28)"

    max_screw_rotation_speed = get_max(setting_item.get("metering_para").get("table_data")[1].get("sections"))
    if max_screw_rotation_speed:
        process_table_data[10]["value"+str(machine_no)] = str(max_screw_rotation_speed)
        if injectors_info[0].get("max_set_screw_rotation_speed") < max_screw_rotation_speed:
            not_adapted = 1
            process_color_data[10]["value"+str(machine_no)] = "red"
        else:
            process_color_data[10]["value"+str(machine_no)] = "rgb(66, 237, 28)"
    process_table_data[11]["value"+str(machine_no)] = "是" if not_adapted == 0 else "否"
    process_table_data[12]["value"+str(math.ceil(machine_no/2))] = process_no
    process_table_data[13]["value"+str(math.ceil(machine_no/2))] = process.get("process_index_id")


def get_max(params_list):
    if params_list and list(filter(None, params_list)):
        return max(list(filter(None, params_list)))


def set_unit(machine_info, machine_no):
    global process_table_data
    pressure_unit = machine_info.get("pressure_unit")
    backpressure_unit = machine_info.get("backpressure_unit")
    velocity_unit = machine_info.get("velocity_unit")
    time_unit = machine_info.get("time_unit")
    position_unit = machine_info.get("position_unit")
    screw_rotation_unit = machine_info.get("screw_rotation_unit")
    process_table_data[2]["value"+str(machine_no+1)] = position_unit
    process_table_data[3]["value"+str(machine_no+1)] = position_unit
    process_table_data[4]["value"+str(machine_no+1)] = position_unit
    process_table_data[5]["value"+str(machine_no+1)] = time_unit
    process_table_data[6]["value"+str(machine_no+1)] = velocity_unit
    process_table_data[7]["value"+str(machine_no+1)] = pressure_unit
    process_table_data[8]["value"+str(machine_no+1)] = pressure_unit
    process_table_data[9]["value"+str(machine_no+1)] = backpressure_unit
    process_table_data[10]["value"+str(machine_no+1)] = screw_rotation_unit
