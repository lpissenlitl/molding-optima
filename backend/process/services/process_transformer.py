"""
工艺参数数据转换模块

负责前端嵌套结构与后端扁平字段之间的相互转换
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from process.models import ProcessParameter


def _transform_frontend_to_flat(setting_process: dict) -> dict:
    """
    将前端嵌套结构的 setting_process 转换为扁平化的数据库字段
    
    Args:
        setting_process: 前端嵌套结构
    
    Returns:
        dict: 扁平化的字段字典，可直接用于创建/更新工艺参数
    """
    flat = {}
    
    # --- 注射参数 ---
    injection = setting_process.get("injection", {})
    inj_stg = injection.get("stage", 1)
    flat["inj_stg"] = inj_stg
    
    table_data = injection.get("table_data", [])
    inj_pres_list = table_data[0].get("sections", []) if len(table_data) >= 1 else []
    inj_spd_list = table_data[1].get("sections", []) if len(table_data) >= 2 else []
    inj_pos_list = table_data[2].get("sections", []) if len(table_data) >= 3 else []
    
    for i in range(1, 7):  # 最多6段
        idx = i - 1
        flat[f"inj_pres_{i}"] = inj_pres_list[idx] if idx < len(inj_pres_list) else None
        flat[f"inj_spd_{i}"] = inj_spd_list[idx] if idx < len(inj_spd_list) else None
        flat[f"inj_pos_{i}"] = inj_pos_list[idx] if idx < len(inj_pos_list) else None
    
    flat["inj_t"] = injection.get("injection_time")
    flat["inj_dly_t"] = injection.get("delay_time")
    
    # --- VP切换参数 ---
    vp_switch = setting_process.get("vp_switch", {})
    flat["vps_mode"] = vp_switch.get("mode", 0)
    flat["vps_pos"] = vp_switch.get("position")
    flat["vps_t"] = vp_switch.get("time")
    flat["vps_pres"] = vp_switch.get("pressure")
    flat["vps_spd"] = vp_switch.get("velocity")
    
    # --- 保压参数 ---
    holding = setting_process.get("holding", {})
    hold_stg = holding.get("stage", 1)
    flat["hold_stg"] = hold_stg
    
    hold_table_data = holding.get("table_data", [])
    hold_pres_list = hold_table_data[0].get("sections", []) if len(hold_table_data) >= 1 else []
    hold_spd_list = hold_table_data[1].get("sections", []) if len(hold_table_data) >= 2 else []
    hold_t_list = hold_table_data[2].get("sections", []) if len(hold_table_data) >= 3 else []
    
    for i in range(1, 6):  # 最多5段
        idx = i - 1
        flat[f"hold_pres_{i}"] = hold_pres_list[idx] if idx < len(hold_pres_list) else None
        flat[f"hold_spd_{i}"] = hold_spd_list[idx] if idx < len(hold_spd_list) else None
        flat[f"hold_t_{i}"] = hold_t_list[idx] if idx < len(hold_t_list) else None
    
    # --- 冷却参数 ---
    flat["cool_t"] = injection.get("cooling_time")
    
    # --- 熔胶参数 ---
    metering = setting_process.get("metering", {})
    met_stg = metering.get("stage", 1)
    flat["met_stg"] = met_stg
    
    met_table_data = metering.get("table_data", [])
    met_pres_list = met_table_data[0].get("sections", []) if len(met_table_data) >= 1 else []
    met_rot_spd_list = met_table_data[1].get("sections", []) if len(met_table_data) >= 2 else []
    met_back_pres_list = met_table_data[2].get("sections", []) if len(met_table_data) >= 3 else []
    met_pos_list = met_table_data[3].get("sections", []) if len(met_table_data) >= 4 else []
    
    for i in range(1, 5):  # 最多4段
        idx = i - 1
        flat[f"met_pres_{i}"] = met_pres_list[idx] if idx < len(met_pres_list) else None
        flat[f"met_rot_spd_{i}"] = met_rot_spd_list[idx] if idx < len(met_rot_spd_list) else None
        flat[f"met_back_pres_{i}"] = met_back_pres_list[idx] if idx < len(met_back_pres_list) else None
        flat[f"met_pos_{i}"] = met_pos_list[idx] if idx < len(met_pos_list) else None
    
    # --- 松退参数 ---
    decompress_data = metering.get("decompress_table_data", [])
    pre_decomp = decompress_data[0] if len(decompress_data) >= 1 else {}
    pst_decomp = decompress_data[1] if len(decompress_data) >= 2 else {}
    
    flat["pre_met_decomp_mode"] = metering.get("pre_decompress_mode", 0)
    flat["pre_met_decomp_pres"] = pre_decomp.get("pressure")
    flat["pre_met_decomp_spd"] = pre_decomp.get("velocity")
    flat["pre_met_decomp_t"] = pre_decomp.get("time")
    flat["pre_met_decomp_dist"] = pre_decomp.get("distance")
    
    flat["pst_met_decomp_mode"] = metering.get("post_decompress_mode", 0)
    flat["pst_met_decomp_pres"] = pst_decomp.get("pressure")
    flat["pst_met_decomp_spd"] = pst_decomp.get("velocity")
    flat["pst_met_decomp_t"] = pst_decomp.get("time")
    flat["pst_met_decomp_dist"] = pst_decomp.get("distance")
    
    flat["met_lim_t"] = metering.get("delay_time")
    flat["met_end_pos"] = metering.get("ending_position")
    
    # --- 料筒温度 ---
    barrel_temp = setting_process.get("barrel_temperature", {})
    brl_stg = barrel_temp.get("stage", 5)
    flat["brl_temp_stg"] = brl_stg
    
    temp_sections = barrel_temp.get("table_data", [{}])[0].get("sections", []) if barrel_temp.get("table_data") else []
    flat["noz_temp"] = temp_sections[0] if len(temp_sections) >= 1 else None
    
    for i in range(1, 10):  # 最多9段料筒温度
        idx = i  # sections[1] 对应 brl_temp_1
        flat[f"brl_temp_{i}"] = temp_sections[idx] if idx < len(temp_sections) else None
    
    return flat


def _construct_setting_process_frontend(parameter, injection_unit=None) -> dict:
    """
    将扁平化的工艺参数转换为前端嵌套结构
    
    Args:
        parameter: ProcessParameter 模型实例
        injection_unit: 注射单元（用于获取单位系统）
    
    Returns:
        dict: 前端嵌套结构的 setting_process
    """
    # 获取单位系统
    if injection_unit:
        pressure_unit = injection_unit.pressure_unit or "MPa"
        speed_unit = injection_unit.speed_unit or "mm/s"
        screw_rotation_unit = injection_unit.screw_rotation_unit or "rpm"
        back_pressure_unit = injection_unit.back_pressure_unit or "MPa"
        temperature_unit = injection_unit.temperature_unit or "℃"
    else:
        pressure_unit = "MPa"
        speed_unit = "mm/s"
        screw_rotation_unit = "rpm"
        back_pressure_unit = "MPa"
        temperature_unit = "℃"
    
    return {
        "injection": {
            "stage": parameter.inj_stg or 1,
            "max_stage": 6,
            "table_data": [
                { 
                    "label": "压力", 
                    "unit": pressure_unit,
                    "sections": [
                        parameter.inj_pres_1, parameter.inj_pres_2,
                        parameter.inj_pres_3, parameter.inj_pres_4,
                        parameter.inj_pres_5, parameter.inj_pres_6
                    ]
                },
                { 
                    "label": "速度", 
                    "unit": speed_unit,
                    "sections": [
                        parameter.inj_spd_1, parameter.inj_spd_2,
                        parameter.inj_spd_3, parameter.inj_spd_4,
                        parameter.inj_spd_5, parameter.inj_spd_6
                    ]
                },
                { 
                    "label": "位置", 
                    "unit": "mm",
                    "sections": [
                        parameter.inj_pos_1, parameter.inj_pos_2,
                        parameter.inj_pos_3, parameter.inj_pos_4,
                        parameter.inj_pos_5, parameter.inj_pos_6
                    ]
                }
            ],
            "injection_time": parameter.inj_t,
            "delay_time": parameter.inj_dly_t,
            "cooling_time": parameter.cool_t
        },
        
        "vp_switch": {
            "mode": parameter.vps_mode or 0,
            "position": parameter.vps_pos,
            "time": parameter.vps_t,
            "pressure": parameter.vps_pres,
            "velocity": parameter.vps_spd
        },
        
        "holding": {
            "stage": parameter.hold_stg or 1,
            "max_stage": 5,
            "table_data": [
                { 
                    "label": "压力", 
                    "unit": pressure_unit,
                    "sections": [
                        parameter.hold_pres_1, parameter.hold_pres_2,
                        parameter.hold_pres_3, parameter.hold_pres_4,
                        parameter.hold_pres_5
                    ]
                },
                { 
                    "label": "速度", 
                    "unit": speed_unit,
                    "sections": [
                        parameter.hold_spd_1, parameter.hold_spd_2,
                        parameter.hold_spd_3, parameter.hold_spd_4,
                        parameter.hold_spd_5
                    ]
                },
                { 
                    "label": "时间", 
                    "unit": "s",
                    "sections": [
                        parameter.hold_t_1, parameter.hold_t_2,
                        parameter.hold_t_3, parameter.hold_t_4,
                        parameter.hold_t_5
                    ]
                }
            ]
        },
        
        "metering": {
            "stage": parameter.met_stg or 1,
            "max_stage": 4,
            "table_data": [
                { 
                    "label": "压力", 
                    "unit": pressure_unit,
                    "sections": [
                        parameter.met_pres_1, parameter.met_pres_2,
                        parameter.met_pres_3, parameter.met_pres_4
                    ]
                },
                { 
                    "label": "螺杆转速", 
                    "unit": screw_rotation_unit,
                    "sections": [
                        parameter.met_rot_spd_1, parameter.met_rot_spd_2,
                        parameter.met_rot_spd_3, parameter.met_rot_spd_4
                    ]
                },
                { 
                    "label": "背压", 
                    "unit": back_pressure_unit,
                    "sections": [
                        parameter.met_back_pres_1, parameter.met_back_pres_2,
                        parameter.met_back_pres_3, parameter.met_back_pres_4
                    ]
                },
                { 
                    "label": "位置", 
                    "unit": "mm",
                    "sections": [
                        parameter.met_pos_1, parameter.met_pos_2,
                        parameter.met_pos_3, parameter.met_pos_4
                    ]
                }
            ],
            "pre_decompress_mode": parameter.pre_met_decomp_mode or 0,
            "post_decompress_mode": parameter.pst_met_decomp_mode or 0,
            "decompress_table_data": [
                {
                    "label": "储前",
                    "pressure": parameter.pre_met_decomp_pres,
                    "velocity": parameter.pre_met_decomp_spd,
                    "time": parameter.pre_met_decomp_t,
                    "distance": parameter.pre_met_decomp_dist
                },
                {
                    "label": "储后",
                    "pressure": parameter.pst_met_decomp_pres,
                    "velocity": parameter.pst_met_decomp_spd,
                    "time": parameter.pst_met_decomp_t,
                    "distance": parameter.pst_met_decomp_dist
                }
            ],
            "delay_time": parameter.met_lim_t,
            "ending_position": parameter.met_end_pos
        },
        
        "barrel_temperature": {
            "stage": parameter.brl_temp_stg or 5,
            "max_stage": 10,
            "table_data": [
                { 
                    "label": "温度", 
                    "unit": temperature_unit,
                    "sections": [
                        parameter.noz_temp,
                        parameter.brl_temp_1, parameter.brl_temp_2,
                        parameter.brl_temp_3, parameter.brl_temp_4,
                        parameter.brl_temp_5, parameter.brl_temp_6,
                        parameter.brl_temp_7, parameter.brl_temp_8,
                        parameter.brl_temp_9
                    ]
                }
            ]
        }
    }
