import { initArray } from "@/utils/array-help";
// import { getOptions} from "@/api/index";

// type DefectDescDict = {
//     [key: string]: string;
// };

// 导出缺陷常量, 这是原始值,从数据库获取最新的缺陷列表
export const defects_const =
[
    { label: "短射", desc: "SHORTSHOT" },        
    { label: "缩水", desc: "SHRINKAGE"},
    { label: "飞边", desc: "FLASH"},
    { label: "气纹", desc: "GASVEINS"},
    { label: "熔接痕", desc: "WELDLINE"},
    { label: "料花", desc: "MATERIALFLOWER"},
    { label: "困气", desc: "AIRTRAP"},
    { label: "色差", desc: "ABERRATION"},
    { label: "烧焦", desc: "BURN"},
    { label: "水波纹", desc: "WATERRIPPLE"},
    { label: "脱模不良", desc: "HARDDEMOLDING"},
    { label: "顶白", desc: "TOPWHITE"},
    { label: '变形', desc: "WARPING"},
    { label: '尺寸偏大', desc: "OVERSIZE"},
    { label: '尺寸偏小', desc: "UNDERSIZE"},
    { label: '浇口印', desc: "GATEMARK"},
    { label: '阴阳面', desc: "SHADING"},
]

export function getLastLabel(defects: any) {
    if (defects.length > 0) {
        return defects[defects.length - 1].label;
    } else {
        return null; // 或者可以返回一个默认值
    }
}
  
// 定义 createOptimizeList 函数
export function createOptimizeList(tab_name: string) {
    return {
        title: tab_name == "0" ? "init" : "opt#" + tab_name,
        name: String(tab_name),
        process_detail: {
            title: "射台 #1",
            name: "0",
            inject_para: {
                injection_stage: 4,
                max_injection_stage_option: 6,
                table_data: [
                    { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
                    { label: "速度", unit: "mm/s", sections: initArray(6, null) },
                    { label: "位置", unit: "mm", sections: initArray(6, null) }
                ],
                injection_time: null,
                injection_delay_time: null,
                cooling_time: null
            },
            holding_para: {
                holding_stage: 3,
                max_holding_stage_option: 5,
                table_data: [
                    { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
                    { label: "速度", unit: "mm/s", sections: initArray(5, null) },
                    { label: "时间", unit: "s", sections: initArray(5, null) }
                ]
            },
            VP_switch: {
                VP_switch_mode: "位置",
                VP_switch_position: null,
                VP_switch_time: null,
                VP_switch_pressure: null,
                VP_switch_velocity: null,
            },
            metering_para: {
                metering_stage: 1,
                max_metering_stage_option: 4,
                table_data: [
                    { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
                    { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
                    { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
                    { label: "位置", unit: "mm", sections: initArray(4, null) }
                ],
                decompressure_mode_before_metering: "否",
                decompressure_mode_after_metering: "距离",
                decompressure_paras: [
                    { label: "储前", pressure: null, velocity: null, time: null, distance: null },
                    { label: "储后", pressure: null, velocity: null, time: null, distance: null }
                ],
                metering_delay_time: null,
                metering_ending_position: null
            },
            temp_para: {
                barrel_temperature_stage: 5,
                max_barrel_temperature_stage_option: 10,
                table_data: [
                    { label: "温度", unit: "℃", sections: initArray(10, null) },
                ],
            },
        },
        auxiliary_detail: {
            hot_runner: {
                valve_num: null,
                sequential_ctrl_time: []
            },
            mold_temp: {
                mold_temp_num:20,
                setting_temp: null,
                mold_temp_list:initArray(20,null)
            },
            hot_runner_temperatures:initArray(14,null)
        },
        feedback_detail: {
            actual_product_weight: null,
            // 这是初始化的缺陷列表，实际从数据库读取之后更新
            defect_info: [
                {label: "短射", desc: "SHORTSHOT", level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "缩水", desc: "SHRINKAGE",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "飞边", desc: "FLASH",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "气纹", desc: "GASVEINS",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "熔接痕", desc: "WELDLINE",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "料花", desc: "MATERIALFLOWER",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "困气", desc: "AIRTRAP",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "色差", desc: "ABERRATION",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "烧焦", desc: "BURN",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "水波纹", desc: "WATERRIPPLE",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "脱模不良", desc: "HARDDEMOLDING",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: "顶白", desc: "TOPWHITE",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: '变形', desc: "WARPING",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: '尺寸偏大', desc: "OVERSIZE",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: '尺寸偏小', desc: "UNDERSIZE",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: '浇口印', desc: "GATEMARK",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },
                {label: '阴阳面', desc: "SHADING",level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remark: null },  
            ],
            optimize_export: {
                defect_num: null,
                defect_feedback: null,
                defect_name: null,
                defect_position: null,
                defect_level: null,
                adjust_name: null,
                adjust_direction: null,
                adjust_value: null,
                rule_in_use: null,
                rule_valid: null,

                candidate_rules: [],
            }
        }
    };
}

export const DEFAULT_FORM_INFO = {
    active_collapse: ["1", "2"],
    active_tab_index: "0",
    optimize_type: 0, // 0: 保压参数初始化为0
    mac_unit: {
        pressure_unit: "MPa",
        backpressure_unit: "MPa",
        oc_pressure_unit: "MPa",
        oc_velocity_unit: "mm/s",
        position_unit: "mm",
        power_unit: "KW",
        temperature_unit: "℃",
        velocity_unit: "mm/s",
        time_unit: "s",
        clamping_force_unit: "Ton",
        screw_rotation_unit: "rpm",
        power_method: null,

        max_injection_stroke: null,
        max_set_injection_pressure: null,
        max_set_injection_velocity: null,
        max_set_holding_pressure: null,
        max_set_holding_velocity: null,
        max_set_metering_pressure: null,
        max_set_screw_rotation_speed: null,
        max_set_metering_back_pressure: null,
        max_set_decompression_pressure: null,
        max_set_decompression_velocity: null,
        max_mold_open_stroke: null,
        max_ejection_stroke: null,
        max_set_ejector_forward_velocity: null,
        max_set_ejector_backward_velocity: null,
        max_set_mold_opening_velocity: null,
        max_set_mold_clamping_velocity: null,
    },
    mold_info: {
        valve_num: null,
        product_infos: [],
    },
    process_index_id: null,
    precondition: {
        machine_id: null,
        machine_data_source: null,
        machine_trademark: null,
        machine_serial_no: null,

        polymer_id: null,
        polymer_abbreviation: null,
        polymer_trademark: null,
        recommend_melt_temperature:null,

        mold_id: null,
        mold_no: null,
        cavity_num: null,
        runner_length: null,
        runner_weight: null,
        gate_type: null,
        gate_num: null,
        gate_shape: null,
        gate_area: null,
        gate_radius: null,
        gate_length: null,
        gate_width: null,

        runner_type:null,
        hot_runner_num:null,

        inject_part: null,
        product_type: null,
        product_total_weight: null,

        product_no: null,
        product_name: null,
        product_ave_thickness: null,
        product_max_thickness: null,
        product_max_length: null,

        data_sources: "工艺优化"
    },
    optimize_list: [createOptimizeList("0")],
    init_holding_para: [
        { pp: 0, sections: initArray(6, null) },
        { pv: 0, sections: initArray(6, null) },
        { pt: 0, sections: initArray(6, null) },
    ],
    flaw_picture_url: null,
};
