
export const IS_MOLD_INSPECTION_EQUIVALENT = false 

export const TRIAL_PHASES = {
  PRE: {
    label: "试模前准备",
    type: "pre_root",
    children: [
      { label: "试模前确认", type: "pre_trial_check" }, 
      // { label: "试模前模具表现评估", type: "pre_trial_evaluation" }
    ],
  },
  TRIAL: {
    label: "模具测试项",
    type: "trial_root",
    // children 动态注入
  },
  POST: {
    label: "试模后处理",
    type: "post_root",
    children: [
      // { label: "试模后模具表现评估", type: "mold_performance_evaluation" },
      { label: "试模检验报告", type: "mold_inspection_report" },
      { label: "样件检验报告", type: "sample_inspection_report" },
      { label: "拆模检验报告", type: "mold_dismantling_inspection_report" },
      { label: "工艺条件记录", type: "process_conditions_record" },
      { label: "试模总结报告", type: "trial_summary_report" },
      { label: "试模过程记录", type: "trial_process_record" },
      { label: "试模问题履历", type: "trial_problem_resume" },
      { label: "试模报告生成", type: "trial_report_generator" }
    ],
  }
}

export const TRIAL_TYPES = [
  { key: "cooling_liquid", label: "冷却液流动状况测试", bit: 0, type: "cooling_liquid_flow_test" },
  { key: "mold_cooling", label: "模具冷却均匀性测试", bit: 1, type: "mold_cooling_balance_test" },
  { key: "effective_viscosity", label: "有效粘度测试", bit: 2, type: "effective_viscosity_test" },
  { key: "multi_cavity_balance", label: "多型腔平衡测试", bit: 3, type: "multi_cavity_balance_test" },
  { key: "pressure_loss", label: "压力损失测试", bit: 4, type: "pressure_loss_test" },
  { key: "holding_pressure", label: "保压压力测试", bit: 5, type: "holding_pressure_test" },
  { key: "gate_freezing_time", label: "浇口冻结时间测试", bit: 6, type: "gate_freeze_time_test" },
  { key: "cooling_time", label: "冷却时间测试", bit: 7, type: "cooling_time_test" },
  { key: "clamping_force", label: "锁模力测试", bit: 8, type: "clamping_force_test" },
  { key: "cycle_time", label: "周期时间测试", bit: 9, type: "cycle_time_test" },
]

import { moldInfoForm, gatingSystemForm } from "./mold-const"
import { injectionUnitForm, machineInfoForm } from "./machine-const"
import { polymerInfoForm } from "./polymer-const"
import { initArray } from "@/utils/array-utils"

export const basicInfoForm = {
  mold_no: null,
  mold_name: null,
  cavity_layout: null,
  target_cycle_time: null,
  rec_inj_mac_type: null,
  rec_inj_mac_tonn: null,
  // 项目信息
  initiator: null,
  project_engineer: null,
  production_engineer: null,
  order_date: null,
  // 预约信息
  trial_version: "T0",
  planned_mold_handover_at: null,
  preferred_trial_start_at: null,
  estimated_trial_duration_hours: null,
  trial_location: null,
  outsourcing_reason: null,
}

export const trialTypeForm = {
  value: -1,
  select_items: [
    { label: "科学试模", value: 1, disabled: false },
    { label: "正常注塑(满足生产时)", value: 2, disabled: false },
    { label: "非正常注塑", value: 3, disabled: false },
  ]
}

export const moldTempCtrlForm = {
  // 模温控制
  temp_control: {
    heat_way: {
      value: -1,
      select_items: [
        { label: "水温", value: 1 },
        { label: "油温", value: 2 },
        { label: "电加热", value: 3 }
      ]
    },
    cavity_measure_temp: initArray(9, null),
    core_measure_temp: initArray(9, null),
    gate_core: { 
      setting_temp: null,
      measure_temp: null,
    },
    tappet_core: { 
      setting_temp: null,
      measure_temp: null,
    },
    slide_core: { 
      setting_temp: null,
      measure_temp: null,
    },
  },
  cooling_system: {
    max_circuit_option: 24,
    cavity_circuit_num: 5,
    cavity_table_data: initArray(5, { 
      circuit_connect_desc: null,
      assistant_equipment: null,
      setting_temperature: null,
      cooling_liquid_flow: null,
      cooling_liquid_pressure: null,
      cooling_medium: null,
      run_water_code: null,
    }),
    core_circuit_num: 5,
    core_table_data: initArray(5, { 
      circuit_connect_desc: null,
      assistant_equipment: null,
      setting_temperature: null,
      cooling_liquid_flow: null,
      cooling_liquid_pressure: null,
      cooling_medium: null,
      run_water_code: null,
    }),
    tappet_circuit_num: 5,
    tappet_table_data: initArray(5, { 
      circuit_connect_desc: null,
      assistant_equipment: null,
      setting_temperature: null,
      cooling_liquid_flow: null,
      cooling_liquid_pressure: null,
      cooling_medium: null,
      run_water_code: null,
    }),
    slider_circuit_num: 5,
    slider_table_data: initArray(5, { 
      circuit_connect_desc: null,
      assistant_equipment: null,
      setting_temperature: null,
      cooling_liquid_flow: null,
      cooling_liquid_pressure: null,
      cooling_medium: null,
      run_water_code: null,
    }),
    mold_photos: {
      cavity: {},
      core: {} 
    },
  }
}

export const hotrunnerTempCtrlForm = {
  max_hotrunner_number: 512,
  hotrunner_number: 14,
  temperatures: initArray(14, null),
  manifold_zones_temps: [],
  max_center_nozzle_number: 512,
  center_nozzle_number: 14,
  center_nozzle_temps: initArray(14, null),
  thermocouple_type: null,
}

export const hotrunnerTimingCtrlForm = {
  control_mode: null,
  seq_control_mode: "位置",
  valve_needle_num: 4,
  max_valve_needle_num: 12,
  table_data: initArray(4, { 
    label: "阀针", 
    // screw_position: null, 
    // inject_time: null, 
    on_position: null,
    off_position: null,
    on_time: null,
    off_time: null,
    holding_start_time: null,
    // holding_end_time: null,
    // delay_inject: null, 
    // actual_inject: null,
    delay_open: null,
    delay_off: null,
  }),
  input_voltage: null,
  timing_control_num: 1,
  max_timing_control_num: 12,
  table_data_set: [
    {
      valve_needle_num: 4,
      max_valve_needle_num: 12,
      table_data: initArray(4, { 
        label: "阀针", 
        on_position: null,
        off_position: null,
        on_time: null,
        off_time: null,
        holding_start_time: null,
        delay_open: null,
        delay_off: null,
      }),
    }
  ]
}

export const fillerInfoForm = {
  name: null,
  percentage: null
}

export const colorantInfoForm  = {
  type: null,
  ratio: null
}

export const materialReqForm = {
  // 物料属性
  category: null,
  material_name: null,
  color: null,
  percentage: null,
  // 物料信息
  material_id: null,
  material_source: null,
  material_code: null,
  sap_material_code: null,
  material_grade: null,
  unit: null,
  // 需求信息
  requirement_id: null,
  quantity: null,
}

export const shotFormulationForm = {
  unit_index: 0,
  poly_info: structuredClone(polymerInfoForm),
  resin_req: structuredClone(materialReqForm),
  additives: [],
  inserts: []
}

export const settingProcessForm = {
  injection: {
    max_stage: 6,
    stage: 1,
    table_data: [
      { label: "压力", unit: "MPa", sections: initArray(6, null) },
      { label: "速度", unit: "mm/s", sections: initArray(6, null) },
      { label: "位置", unit: "mm", sections: initArray(6, null) }
    ],
    injection_time: null,
    delay_time: null,
    cooling_time: null,
    setting_clamping_force: null
  },
  vp_switch: {
    mode: null,
    position: null,
    time: null,
    pressure: null,
    velocity: null,
  },
  holding: {
    max_stage: 5,
    stage: 1,
    table_data: [
      { label: "压力", unit: "MPa", sections: initArray(5, null) },
      { label: "速度", unit: "mm/s", sections: initArray(5, null) },
      { label: "时间", unit: "s", sections: initArray(5, null) }
    ]
  },
  metering: {
    max_stage: 4,
    stage: 1,
    table_data: [
      { label: "压力", unit: "MPa", sections: initArray(4, null) },
      { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
      { label: "背压", unit: "MPa", sections: initArray(4, null) },
      { label: "位置", unit: "mm", sections: initArray(4, null) }
    ],
    pre_decompress_mode: "否",
    post_decompress_mode: "距离",
    decompress_table_data: [
      { label: "储前", pressure: null, velocity: null, time: null, distance: null },
      { label: "储后", pressure: null, velocity: null, time: null, distance: null }
    ],
    delay_time: null,
    ending_position: null
  },
  barrel_temperature: {
    max_stage: 10,
    stage: 5,
    table_data: [
      { label: "温度", unit: "℃", sections: initArray(10, null) },
    ],
  }
}

export const heatAndCoolInjectionForm = {
  setting_pressure: null,
  steam_temp: null,
  cooling_water_temp: null,
  heat_time: null,
  cooling_time: null,
  blow_time: null,
  temp_in_mold_after_cooling: null,
  temp_in_mold_before_injection: null,
}

export const gasAssistInjectionForm = { 
  delay_time: null,
  max_count: 10,
  count: 3,
  pressure_unit: "PSI",
  table_data: initArray(3, { 
    pressure: null, 
    holding_time: null, 
  })
}

export const coreParametersForm = [
  {
    core_label: "中子A进",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
  {
    core_label: "中子A退",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
  {
    core_label: "中子B进",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
  {
    core_label: "中子B退",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
  {
    core_label: "中子C进",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
  {
    core_label: "中子C退",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
  {
    core_label: "中子D进",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
  {
    core_label: "中子D退",
    core_pulling: null,
    pressure: null,
    speed: null,
    time: null,
    position: null,
    control_mode: null,
  },
]

export const ejectionParametersForm = {
  max_stage: 10,
  stage: 2,
  table_data:[
    {
      pressure: null,
      speed: null,
      position: null,
      distance: null,
    },
    {
      pressure: null,
      speed: null,
      position: null,
      distance: null,
    },
  ]
}

export const monitorProcessForm = {
  actual_injection_time: null,
  actual_cooling_time: null,
  actual_metering_time: null,
  actual_ejector_backward_time: null,
  actual_ejector_forward_time: null,

  actual_holding_ending_position: null,
  actual_VP_switch_position: null,
  actual_injection_starting_position: null,
  remain_volume: null,
  actual_metering_starting_position: null,
  actual_metering_ending_position: null,

  actual_peak_pressure: null,
  actual_VP_switch_pressure: null,
  actual_torque: null,
}

export const shotStepForm = {
  injection_unit: structuredClone(injectionUnitForm),
  shot_formulation: structuredClone(shotFormulationForm),
  gating_system: structuredClone(gatingSystemForm),
  hotrunner_temp_ctrl: structuredClone(hotrunnerTempCtrlForm),
  hotrunner_timing_ctrl: structuredClone(hotrunnerTimingCtrlForm),
  setting_process: structuredClone(settingProcessForm),
  monitor_process: structuredClone(monitorProcessForm)
}

export const measureParametersForm = { 
  product_weight: null,
  runner_weight: null,
  product_thickness: null,
}

export const airBlowParametersForm = {
  fixed_mold_is_air_blow: null,
  fixed_mold_air_blow_time: null,
  fixed_mold_air_blow_open_delay: null,
  moving_mold_is_air_blow: null,
  moving_mold_air_blow_time: null,
  moving_mold_air_blow_open_delay: null,
}

export const moldClosingOpeningParametersForm = {
  max_stage: 10,
  stage: 5,
  table_data: initArray(5, { 
    pressure: null,
    speed: null,
    position: null,
    distance: null,
  })
}

export const processConditionsForm = {
  trial_session_id: null,
  trial_type: null,
  basic_info: structuredClone(basicInfoForm),
  mold_info: structuredClone(moldInfoForm),
  machine_info: structuredClone(machineInfoForm),
  mold_temp_ctrl: structuredClone(moldTempCtrlForm),
  shot_steps: [structuredClone(shotStepForm)],
  heat_and_cool_injection: structuredClone(heatAndCoolInjectionForm),
  gas_assist_injection: structuredClone(gasAssistInjectionForm),
  core_parameters: structuredClone(coreParametersForm),
  ejection_parameters: structuredClone(ejectionParametersForm),
  ejector_parameters: structuredClone(ejectionParametersForm),
  measure_parameters: structuredClone(measureParametersForm),
  air_blow_parameters: structuredClone(airBlowParametersForm),
  mold_closing_parameters: structuredClone(moldClosingOpeningParametersForm),
  mold_opening_parameters: structuredClone(moldClosingOpeningParametersForm),
  remarks: null,
}

export const trialStatusOptions = [
  { value: "pending", label: "准备中" },
  { value: "mold_mounting", label: "模具上模" },
  { value: "mounting_completed", label: "上模完毕" },
  { value: "mold_testing", label: "模具测试" },
  { value: "testing_completed", label: "模具测试完毕" },
  { value: "sample_production", label: "样件生产" },
  { value: "production_completed", label: "样件生产完毕" },
  { value: "mold_unmounting", label: "模具卸模" },
  { value: "completed", label: "已完成" },
]

export const trialStatusMap = Object.fromEntries(
  trialStatusOptions.map(item => [item.value, item.label])
)

export const exportedStatusOptions = [
  { value: false, label: "未导出" },
  { value: true, label: "已导出" },
]

export const exportedStatusMap = Object.fromEntries(
  exportedStatusOptions.map(item => [item.value, item.label])
)


export const HISENSE_MOLD_TRIAL_ISSUE_TEMPLATE = [
  {
    inspection_key: "mold_open_close",
    inspection_item: "模具开合",
    inspection_criteria: ["10%-90%的速度40%-90%的压力开合模无异常"],
    category_level_1: "模具",
    category_level_2: "模具研配",
    options: [
      { issue_item: "开合模异响", grade: "A", deduction: 5 },
      { issue_item: "模具起刺（要图片）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "parting_surface_fitting",
    inspection_item: "分型面研配",
    inspection_criteria: [
      "分型面研配均匀一致，接触面积≥80%",
      "封料线清晰接触面积100%"
    ],
    category_level_1: "模具",
    category_level_2: "模具研配",
    options: [
      { issue_item: "封料面研配明显不均匀，无蓝丹印记", grade: "A", deduction: 5 },
      { issue_item: "封料面研配不均匀，蓝丹印记虚", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "locator_surface_fitting",
    inspection_item: "定位面研配",
    inspection_criteria: [
      "定位面接触均匀且无偏移，接触面不少于80%",
      "无过紧现象"
    ],
    category_level_1: "模具",
    category_level_2: "模具研配",
    options: [
      { issue_item: "定位面不足（<80%），局部研配过紧（发黑）", grade: "A", deduction: 5 },
      { issue_item: "定位面研配偏（一侧有痕迹，一侧无痕迹）", grade: "A", deduction: 5 },
      { issue_item: "局部研配黑点，不均匀", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "pressure_plate_fitting",
    inspection_item: "承压面",
    inspection_criteria: ["承压板蓝丹印迹满足要求"],
    category_level_1: "模具",
    category_level_2: "模具研配",
    options: [
      { issue_item: "承压板无蓝丹印记", grade: "A", deduction: 5 },
      { issue_item: "承压板蓝丹印记虚/不均匀", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "core_cavity_sliding_surface",
    inspection_item: "运动插穿面",
    inspection_criteria: [
      "配合面有无起刺、过紧现象",
      "蓝丹接触面积大于80%，封料线清晰接触面积100%",
      "配合面有无起刺、过紧现象"
    ],
    category_level_1: "模具",
    category_level_2: "模具研配",
    options: [
      { issue_item: "图示配合面起刺、发黑", grade: "A", deduction: 5 },
      { issue_item: "图示研配面小于80%", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "ejector_function",
    inspection_item: "顶出",
    inspection_criteria: ["10%-90%的速度40%-90%的压力顶出无异响、干涉、起刺、卡死现象"],
    category_level_1: "模具",
    category_level_2: "顶出系统",
    options: [
      { issue_item: "顶出异响、干涉、起刺、卡死", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "ejector_return_position",
    inspection_item: "顶出回位",
    inspection_criteria: ["顶杆、斜顶杆、顶出块回位是否已到底（以限位钉和B3板的距离为准）"],
    category_level_1: "模具",
    category_level_2: "顶出系统",
    options: [
      { issue_item: "顶出或复位不能正常到底", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "ejector_rotation",
    inspection_item: "顶杆转动性",
    inspection_criteria: ["顶杆顶出后是否能转动"],
    category_level_1: "模具",
    category_level_2: "顶出系统",
    options: [
      { issue_item: "部分顶杆转不动", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "hydraulic_cylinder_side_action",
    inspection_item: "油缸、侧抽",
    inspection_criteria: [
      "10%-60%的速度40%-60%的压力动作无异响、干涉、起刺、卡死等异常现象。",
      "油缸顶出回位的模具验证顶出回位是否正常，油压不能高于80Bar动作顺畅，加锁模力前各斜顶头段差不能高于Bc大面0.20mm。",
      "模具异响时需要记录描述异响响声所在的动作节点，同步记录当时的模具实际温度，保压压力，冷却时间。"
    ],
    category_level_1: "模具",
    category_level_2: "液压系统",
    options: [
      { issue_item: "抽芯干涉", grade: "A", deduction: 5 },
      { issue_item: "抽芯起刺、卡死", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "slider_movement",
    inspection_item: "滑块运动",
    inspection_criteria: ["动作无异响、干涉、起刺、卡死等异常现象"],
    category_level_1: "模具",
    category_level_2: "抽芯系统",
    options: [
      { issue_item: "滑块干涉", grade: "A", deduction: 5 },
      { issue_item: "滑块起刺、卡死", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "slider_travel_distance",
    inspection_item: "滑块行程量",
    inspection_criteria: ["滑块行程量不小于产品倒扣量"],
    category_level_1: "模具",
    category_level_2: "抽芯系统",
    options: [
      { issue_item: "滑块行程不足，产品无法顺利脱模", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "slider_guide_sequence",
    inspection_item: "滑块导向顺序",
    inspection_criteria: ["合模时大导柱是否优先斜导柱进入导向位置"],
    category_level_1: "模具",
    category_level_2: "抽芯系统",
    options: [
      { issue_item: "斜导柱先插入滑块，大导柱长度不足", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "slider_wear_plate_fitting",
    inspection_item: "滑块耐磨板配合",
    inspection_criteria: ["滑块背面耐磨板配合面均匀一致，无起刺"],
    category_level_1: "模具",
    category_level_2: "模具研配",
    options: [
      { issue_item: "滑块背面耐磨板研配虚、紧、起刺", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "angled_lifter_condition",
    inspection_item: "斜导柱状态",
    inspection_criteria: ["斜导柱无起刺松动现象"],
    category_level_1: "模具",
    category_level_2: "抽芯系统",
    options: [
      { issue_item: "斜导柱松动、起刺", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "cooling_channel_leakage",
    inspection_item: "水路",
    inspection_criteria: ["无漏水、渗水、水路不通现象"],
    category_level_1: "模具",
    category_level_2: "冷却系统",
    options: [
      { issue_item: "模具漏水（要带图片）", grade: "A", deduction: 5 },
      { issue_item: "模具水路不通（要带图片）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "cooling_heating_normal_mold",
    inspection_item: "冷却、加热（普通模具）",
    inspection_criteria: [
      "动静模无局部过热，冷却不良位置；无局部升温不良。",
      "标准参考模流提供的标准值。"
    ],
    category_level_1: "模具",
    category_level_2: "冷却系统",
    options: [
      { issue_item: "图示位置加热不良（要带图片）", grade: "B", deduction: 3 },
      { issue_item: "图示位置冷却不良（要带图片）", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "cooling_heating_high_gloss_mold",
    inspection_item: "冷却、加热（高光模具）",
    inspection_criteria: [
      "蒸汽高光模具加热冷却正常、表面痕迹容易调整（浮纤、浇口印、熔接痕）。",
      "标准参考模流提供的标准值"
    ],
    category_level_1: "模具",
    category_level_2: "冷却系统",
    options: [
      { issue_item: "图示位置加热冷却不良（要带图片）", grade: "B", deduction: 3 },
      { issue_item: "图示位置缺陷不易调整（要带图片说明）", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "hot_runner_heating",
    inspection_item: "热流道加热",
    inspection_criteria: ["加热满足量产无异常，温控正常"],
    category_level_1: "模具",
    category_level_2: "浇注系统",
    options: [
      { issue_item: "热流道不能正常控温（图片说明）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "hot_runner_valve_pin_action",
    inspection_item: "热流道阀针动作",
    inspection_criteria: ["针阀浇口动作有无异常、封料是否到位"],
    category_level_1: "模具",
    category_level_2: "浇注系统",
    options: [
      { issue_item: "阀针动作卡滞", grade: "A", deduction: 5 },
      { issue_item: "浇口毛刺", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "melt_flow_balance",
    inspection_item: "料流",
    inspection_criteria: ["料流均衡、无料流不均衡导致出现异常现象（25%、50%、75%、95% 转保压时料流照片）"],
    category_level_1: "模具",
    category_level_2: "料流",
    options: [
      { issue_item: "产品成型90%时，外轮廓明显成型明显不对称，图示位置偏慢", grade: "B", deduction: 3 },
      { issue_item: "产品成型90%时，外轮廓成型少有不对称", grade: "C", deduction: 1 }
    ]
  },
  {
    inspection_key: "sink_mark",
    inspection_item: "缩痕",
    inspection_criteria: ["外观产品无缩痕"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "图示位置明显缩痕（目视清晰可见）", grade: "B", deduction: 3 },
      { issue_item: "图示位置轻微缩痕（迎光可见）", grade: "C", deduction: 1 }
    ]
  },
  {
    inspection_key: "weld_line",
    inspection_item: "熔痕",
    inspection_criteria: [
      "高光件无熔接线。",
      "普通外观件0.5m内目视不明显，无手感。",
      "冰箱类（抽屉/面板）透明件熔接线位置-深浅-长短能否满足客户要求"
    ],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "0.5米内目测明显", grade: "B", deduction: 3 },
      { issue_item: "冰箱类（抽屉/面板）透明件熔接线位置符合料流方案", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "air_trap",
    inspection_item: "包气",
    inspection_criteria: [
      "无包气及气泡现象。（排气是否起作用）",
      "包气验证条件：正常工艺连续生产30模，判定产品是否存在困气问题。"
    ],
    category_level_1: "模具",
    category_level_2: "料流",
    options: [
      { issue_item: "产品大面困气", grade: "B", deduction: 3 },
      { issue_item: "产品末端（含筋位）困气", grade: "C", deduction: 1 }
    ]
  },
  {
    inspection_key: "color_variation",
    inspection_item: "色差",
    inspection_criteria: ["无明显色差、亮斑、暗斑等缺陷"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "浇口明显色差", grade: "B", deduction: 3 },
      { issue_item: "产品明显色差", grade: "C", deduction: 1 }
    ]
  },
  {
    inspection_key: "ejector_burn",
    inspection_item: "顶白",
    inspection_criteria: ["无顶白"],
    category_level_1: "模具",
    category_level_2: "顶出系统",
    options: [
      { issue_item: "图示位置顶白", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "fiber_float",
    inspection_item: "浮纤",
    inspection_criteria: ["无外观浮纤"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "0.5米内，图示浮纤明显", grade: "B", deduction: 3 },
      { issue_item: "0.5米内，图示轻微浮纤", grade: "C", deduction: 1 }
    ]
  },
  {
    inspection_key: "short_shot",
    inspection_item: "缺料",
    inspection_criteria: ["无缺料（成型不满）"],
    category_level_1: "产品",
    category_level_2: "形状",
    options: [
      { issue_item: "图示位置不易成型", grade: "C", deduction: 1 }
    ]
  },
  {
    inspection_key: "part_removal",
    inspection_item: "取出 制品/流道",
    inspection_criteria: ["观察制件及流道顶出至限位后的状态，应符合客户取件方式，是否满足机械手取件要求或容易取出（参照式样书取件要求）"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "不能机械手取件及料把", grade: "A", deduction: 5 },
      { issue_item: "手工取件或料把紧，不顺畅", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "sprue_fitting",
    inspection_item: "浇道研配",
    inspection_criteria: ["浇道无毛刺"],
    category_level_1: "模具",
    category_level_2: "模具研配",
    options: [
      { issue_item: "浇道有毛刺", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "sprue_polishing",
    inspection_item: "浇道抛光",
    inspection_criteria: ["浇道抛光无加工痕迹，600#砂纸以上"],
    category_level_1: "模具",
    category_level_2: "浇注系统",
    options: [
      { issue_item: "浇道加工痕迹", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "demolding_scratch",
    inspection_item: "脱模拉伤",
    inspection_criteria: ["产品无拉伤（产品的外观面、内部面、筋位等）"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "图示位置拉伤", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "sticking_mold",
    inspection_item: "脱模粘模",
    inspection_criteria: ["无粘模"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "图示位置粘模", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "demolding_crack",
    inspection_item: "脱模断裂",
    inspection_criteria: ["无裂纹或断裂"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "图示位置断裂", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "texture_debris",
    inspection_item: "制品防粘腔皮纹位置脱模情况",
    inspection_criteria: ["是否落料渣"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "残留料渣，影响后续成型", grade: "B", deduction: 5 }
    ]
  },
  {
    inspection_key: "gate_scraping",
    inspection_item: "脱模铲胶",
    inspection_criteria: ["无铲胶"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "图示位置铲胶（铲料近似较大毛刺）", grade: "A", deduction: 5 },
      { issue_item: "图示位置轻微铲胶", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "process_window",
    inspection_item: "成型/工艺范围",
    inspection_criteria: [
      "缺陷是否容易调整，并描述主要问题.",
      "工艺关键点调整正常保压分别增加5BAR、10BAR、15BAR、20BAR压力，查看产品是否存产品无顶白、毛刺、拖伤、粘模等问题，模具运动通畅，无起刺卡滞问题。并将产品照片连同记录表拍照提交系统。"
    ],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "正常工艺缺陷不易调整，工艺参数窄。（要用图片说明问题点)", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "dimensional_accuracy",
    inspection_item: "成型尺寸",
    inspection_criteria: ["有尺寸要求时标准尺寸加减0.5mm是否容易调整"],
    category_level_1: "产品",
    category_level_2: "尺寸",
    options: [
      { issue_item: "正常工艺时尺寸偏大。", grade: "B", deduction: 3 },
      { issue_item: "正常工艺尺寸偏小。", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "warpage",
    inspection_item: "变形",
    inspection_criteria: ["变形量小于0.5%(变形量超出图纸要求）"],
    category_level_1: "产品",
    category_level_2: "变形",
    options: [
      { issue_item: "图示位置变形。", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "part_weight",
    inspection_item: "重量",
    inspection_criteria: ["根据式样书要求判定"],
    category_level_1: "产品",
    category_level_2: "重量",
    options: [
      { issue_item: "要求（      ）g ，  实际（    ）g.", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "clamping_force",
    inspection_item: "锁模力",
    inspection_criteria: ["按式样书客户注塑机吨位的90%锁模力，是否能满足客户要求"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "要求锁模力（   ），实际锁模力（   ）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "cycle_time",
    inspection_item: "周期",
    inspection_criteria: ["根据式样书要求判定"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "要求(  ）S,实际（ ）S。影响周期的主要问题（   ）。", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "dry_cycle",
    inspection_item: "空运行",
    inspection_criteria: ["运行无异常现象"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "不具备空运行条件", grade: "A", deduction: 5 },
      { issue_item: "空运行起刺 卡死（带问题图片）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "others",
    inspection_item: "其他",
    inspection_criteria: ["无"],
    category_level_1: "模具",
    category_level_2: "量产性",
    options: [
      { issue_item: "已标准化外的其他问题", grade: "A", deduction: 5 }
    ]
  }
]

export const hisenseMoldInspectionItems = HISENSE_MOLD_TRIAL_ISSUE_TEMPLATE.map(item => {
  return {
    ...item,
    deduction: null,
    grade: null,
    id: null,
    is_old_issue: false,
    issue_code: null,
    issue_description: null,
    issue_images: [],
    issue_files: [],
    issue_item: null,
    issue_type: "mold_insp",
    judgement: null,
    judgement_by: null,
    judgement_at: null,
    trial_session_id: null,
  }
})

export const HISENSE_SAMPLE_TRIAL_ISSUE_TEMPLATE = [
  {
    inspection_key: "size",
    inspection_item: "尺寸",
    inspection_criteria: ["尺寸满足图纸公差要求。（无明确公差要求，需经客户确认）"],
    category_level_1: "产品",
    category_level_2: "尺寸",
    options: [
      { issue_item: "尺寸报告需确认", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "wall_thickness",
    inspection_item: "壁厚",
    inspection_criteria: ["未注壁厚公差±0.1（部分客户产品为±0.05，优先执行客户标准）"],
    category_level_1: "产品",
    category_level_2: "壁厚",
    options: [
      { issue_item: "公差超出标准", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "shape",
    inspection_item: "形状",
    inspection_criteria: ["符合图纸或模型，无错漏。 1.产品模型未更新。 2.设计或制造错误。"],
    category_level_1: "产品",
    category_level_2: "形状",
    options: [
      { issue_item: "漏形状", grade: "B", deduction: 3 },
      { issue_item: "形状错误", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "character",
    inspection_item: "字符",
    inspection_criteria: ["符合图纸或模型，无错漏。"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "样件字符不符合模型/图纸", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "overall_fitting_burr",
    inspection_item: "整体研配毛刺",
    inspection_criteria: ["参照《样件检验手册》执行"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "整体研配严重毛刺", grade: "A", deduction: 5 },
      { issue_item: "整体研配轻微毛刺", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "insert_burr",
    inspection_item: "镶件毛刺",
    inspection_criteria: ["参照《样件检验手册》执行"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "镶件严重毛刺", grade: "A", deduction: 5 },
      { issue_item: "镶件轻微毛刺", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "appearance_surface_step",
    inspection_item: "外观面段差",
    inspection_criteria: ["参照《样件检验手册》执行"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "严重段差（大于0.1）", grade: "A", deduction: 5 },
      { issue_item: "轻微段差（0.1以内）", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "non_appearance_surface_step",
    inspection_item: "非外观面段差",
    inspection_criteria: ["参照《样件检验手册》执行"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "非外观段差", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "cavity_polishing",
    inspection_item: "腔抛光",
    inspection_criteria: [
      "无漏抛光",
      "无抛光过切/变形",
      "抛光粗糙度满足要求，对照《模具制作式样书》抛光等级和模具模型染色规定检验判定"
    ],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "型腔漏抛光", grade: "A", deduction: 5 },
      { issue_item: "型腔抛光过切/变形", grade: "A", deduction: 5 },
      { issue_item: "型腔抛光粗糙度未达到要求", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "rib_column_polishing",
    inspection_item: "筋柱抛光",
    inspection_criteria: ["无出模拉伤和加工痕迹，＞600#砂纸水平"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "筋柱严重拉伤/有加工痕迹", grade: "A", deduction: 5 },
      { issue_item: "筋柱轻微拉伤", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "orange_peel_texture",
    inspection_item: "橘皮纹",
    inspection_criteria: ["距离0.5米多个角度目测无橘皮纹"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "外观高光面严重橘皮纹", grade: "A", deduction: 5 },
      { issue_item: "外观高光面轻微橘皮纹", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "scratch_and_knock",
    inspection_item: "磕碰划伤",
    inspection_criteria: ["无碰伤、挤伤、划伤"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "磕碰划伤", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "sand_hole_pitting",
    inspection_item: "砂眼麻点",
    inspection_criteria: ["无砂眼麻点。1.积碳砂眼。2.材料砂眼。3.抛光砂眼"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "砂眼麻点", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "whitening",
    inspection_item: "白化",
    inspection_criteria: ["形状无白化"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "白化", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "pull_scratch",
    inspection_item: "拉伤",
    inspection_criteria: ["无拉伤"],
    category_level_1: "模具",
    category_level_2: "精细化",
    options: [
      { issue_item: "明显拉伤", grade: "B", deduction: 3 },
      { issue_item: "轻微拉伤", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "texture",
    inspection_item: "皮纹",
    inspection_criteria: [
      "皮纹一致性。距离0.5米多个角度目测无差异",
      "皮纹样式符合标准皮纹样板",
      "皮纹范围符合图纸标注要求，参照设计《皮纹腐蚀通知单》标准执行"
    ],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "皮纹明显不一致", grade: "B", deduction: 3 },
      { issue_item: "皮纹样式不符合标准皮纹样板", grade: "B", deduction: 3 },
      { issue_item: "皮纹范围不符合图纸标注要求", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "non_appearance_texture",
    inspection_item: "非外观皮纹",
    inspection_criteria: ["皮纹范围符合图纸标注要求，参照设计《皮纹腐蚀通知单》标准执行"],
    category_level_1: "模具",
    category_level_2: "外观",
    options: [
      { issue_item: "皮纹范围不符合图纸标注要求", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "appearance_surface_color_diff",
    inspection_item: "外观面色差",
    inspection_criteria: ["无明显色差、亮斑、暗斑等缺陷"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "明显色差、亮暗斑", grade: "B", deduction: 3 },
      { issue_item: "轻微色差、亮暗斑", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "replaceable_version_confirmation",
    inspection_item: "可换版本确认",
    inspection_criteria: ["该项主要作用是多版本不同时间试模，检验记录，提示哪些版本检了，哪些未检。所有版本全部检验完判定ok。"],
    category_level_1: "其他",
    category_level_2: "其他",
    options: [
      { issue_item: "可换版本样品送样不全", grade: "/", deduction: 0 },
    ]
  },
  {
    inspection_key: "product_appearance_surface_welding",
    inspection_item: "产品外观面烧焊",
    inspection_criteria: ["产品外观面无砂眼/亮斑/裂纹/色差/形状不良等缺陷，检查完成后在烧焊加工单判定是否合格。"],
    category_level_1: "产品",
    category_level_2: "外观",
    options: [
      { issue_item: "有产品外观面无砂眼/亮斑/裂纹/色差/形状不良等缺陷，判定不合格。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "sample_inspection_report_others",
    inspection_item: "可换版本确认",
    inspection_criteria: ["无"],
    category_level_1: "其他",
    category_level_2: "其他",
    options: [
      { issue_item: "已标准化外的其他问题", grade: "/", deduction: 0 },
    ]
  },

]

export const hisenseSampleInspectionItems = HISENSE_SAMPLE_TRIAL_ISSUE_TEMPLATE.map(item => {
  return {
    ...item,
    deduction: null,
    grade: null,
    id: null,
    is_old_issue: false,
    issue_code: null,
    issue_description: null,
    issue_images: [],
    issue_files: [],
    issue_item: null,
    issue_type: "sample_insp",
    judgement: null,
    judgement_by: null,
    judgement_at: null,
    trial_session_id: null,
  }
})

export const HISENSE_HOME_APP_MOLD_DISMANTLING_TRIAL_ISSUE_TEMPLATE = [
  // {
  //   inspection_key: "home_hot_runner",
  //   inspection_item: "热流道",
  //   inspection_criteria: [
  //     `以下项目按照式样书检验确认:
  //     热流道样式、
  //     接线插座及底座型号、    
  //     接线符合式样书、
  //     电磁阀电压、
  //     电磁阀接线方式、
  //     热流道接线盒上要有对应的接线小标牌(见客户标准)`,
  //     "电磁阀电压、驱动方式、快换接头眼观符合式样书",
  //     "热流道嘴头与模具浇口处直径配合符合设计要求，无漏胶现象",
  //     "热电偶型号符合式样书",
  //     "热流道观察孔、排水槽是否需要并加工",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "热流道样式、接线插座及底座型号、接线、电磁阀电压、电磁阀接线方式与式样书不符，或热流道接线盒上没有对应的接线小标牌", grade: "A", deduction: 5 },
  //     { issue_item: "电磁阀电压、驱动方式、快换接头眼观与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "热流道嘴头与模具浇口处直径配合不符合设计要求，有漏胶现象", grade: "A", deduction: 5 },
  //     { issue_item: "热电偶型号与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "热流道观察孔、排水槽需要但未加工", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_lift_safety",
  //   inspection_item: "起吊安全",
  //   inspection_criteria: [
  //     "模具所有吊环眼观拧到底、吊环标识正确，AO/B0上吊环旋转轨迹上无干涉。按照设计要求整套模具起吊平衡。",
  //     "模具是否需要吊模块，吊模块上吊孔标识已做",
  //     "模芯等工件吊装螺纹深度大于2.5D，吊环孔底孔无超差。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "模具所有吊环眼观拧到底、吊环标识不正确", grade: "A", deduction: 5 },
  //     { issue_item: "吊模块上吊孔标识未做", grade: "C", deduction: 1 },
  //     { issue_item: "吊环孔底孔有超差", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_position",
  //   inspection_item: "定位",
  //   inspection_criteria: [
  //     "所有模具都要有精定位（客户特殊要求除外）",
  //     "滑块压板、斜顶导向块、斜顶导滑座销钉孔及销钉无缺漏",
  //     "配合面摩擦均匀，无局部黑印",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "模具没有精定位", grade: "B", deduction: 3 },
  //     { issue_item: "滑块压板、斜顶导向块、斜顶导滑座销钉孔或销钉有缺漏", grade: "B", deduction: 3 },
  //     { issue_item: "配合面摩擦不均匀，有局部黑印", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_ejector_pin",
  //   inspection_item: "顶杆",
  //   inspection_criteria: [
  //     "顶出块顶杆要有止转机构",
  //     "顶杆、顶管配合段是直径的3倍，其余做避让",
  //     "方顶杆摩擦痕迹均匀，无线切割落料痕、无弯曲。",
  //     "圆顶杆摩擦痕迹均匀、无弯曲。",
  //     "顶出块摩擦痕迹均匀，无局部线形摩擦痕迹，有油槽（白电一般不要油槽）。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "顶出块顶杆没有止转机构", grade: "A", deduction: 5 },
  //     { issue_item: "顶杆、顶管配合段不是直径的3倍，其余未做避让", grade: "B", deduction: 3 },
  //     { issue_item: "方顶杆摩擦痕迹不均匀，有线切割落料痕、有弯曲。", grade: "B", deduction: 3 },
  //     { issue_item: "圆顶杆摩擦痕迹不均匀、有弯曲。", grade: "B", deduction: 3 },
  //     { issue_item: "顶出块摩擦痕迹不均匀，有局部线形摩擦痕迹，非白点但没有油槽。", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_return_pin",
  //   inspection_item: "复位杆",
  //   inspection_criteria: [
  //     "复位杆下有树脂弹簧的，复位杆要有3mm活动空间（客户特殊要求不要树脂弹簧除外）不要树脂弹簧的复位杆挂台要和B2板平",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "有树脂弹簧，复位杆没有3mm活动空间", grade: "B", deduction: 3 },
  //     { issue_item: "没有树脂弹簧，复位杆挂台没有和B2板平", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_main_guide_pin",
  //   inspection_item: "大导柱",
  //   inspection_criteria: [
  //     "大导柱、导套样式及材料符合式样书（需检测硬度拍照）",
  //     "大小导套侧面紧固螺钉紧固到底",
  //     "大导套要有排气槽",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "大导柱、导套样式或材料与样式书不符", grade: "A", deduction: 5 },
  //     { issue_item: "大小导套侧面紧固螺钉不紧固", grade: "B", deduction: 3 },
  //     { issue_item: "大导套没有排气槽", grade: "C", deduction: 1 },
  //   ]
  // },
  // {
  //   inspection_key: "home_stripper_plate_guide_pin",
  //   inspection_item: "推板导柱",
  //   inspection_criteria: [
  //     "推板导柱固定在B4板时，要紧配",
  //     "推板导柱或导套要有润滑结构，要符合设计标准",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "推板导柱固定在B4板时，没有紧配", grade: "A", deduction: 5 },
  //     { issue_item: "推板导柱或导套没有润滑结构，不符合设计标准", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_exhaust",
  //   inspection_item: "排气",
  //   inspection_criteria: [
  //     "内分型面有排气槽的要有排气引出孔与外界通",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "没有排气引出孔与外界通", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_water_channel",
  //   inspection_item: "水路",
  //   inspection_criteria: [
  //     "密封圈槽符合模型",
  //     "耐高温密封圈和普通密封圈没有用错",
  //     "隔水板材料正确、安装方向正确、无缺漏，松手钳检验隔水板无松动，长度尺寸到达水井底部，水井内手电检验无铁屑。",
  //     "隔水板无松动，水井内手电检验无铁屑。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "密封圈槽与模型不符", grade: "A", deduction: 5 },
  //     { issue_item: "耐高温密封圈和普通密封圈用错", grade: "A", deduction: 5 },
  //     { issue_item: "隔水板材料不正确、安装方向错误、有缺漏，松手钳检验隔水板有松动，长度尺寸不到水井底部，水井内手电检验有铁屑。", grade: "B", deduction: 3 },
  //     { issue_item: "隔水板有松动，水井内手电检验有铁屑。", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_slide_block",
  //   inspection_item: "滑块",
  //   inspection_criteria: [
  //     "滑块斜导柱插入之前，大导柱要先进入大导套。",
  //     "滑块前置弹簧结构的，漏在弹簧孔以外的弹簧长度大于弹簧孔深度的2/3时要有弹簧导杆",
  //     "滑块上斜导柱孔入口部倒R3",
  //     "滑块压板、导向块、耐磨板、斜导柱材料符合式样书，硬度符合标准。",
  //     "滑块背面耐磨板螺钉已安装到位，油槽样式一致。",
  //     "斜导柱摩擦均匀、无起刺、无弯曲，手试无晃动。",
  //     "滑块封料面边缘无挤伤，成型面无磕碰、划伤，无明显的砂轮研配痕迹。",
  //     "导轨尺寸测量与滑块间隙单边≤0.02mm，左右用手摆动无明显的晃动。",
  //     "滑块压板与滑块支腿间隙尺寸测量≤0.05mm。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "滑块斜导柱插入之前，大导柱未先进入大导套。", grade: "A", deduction: 5 },
  //     { issue_item: "滑块前置弹簧结构的，漏在弹簧孔以外的弹簧长度大于弹簧孔深度的2/3时没有弹簧导杆", grade: "A", deduction: 5 },
  //     { issue_item: "滑块上斜导柱孔入口部没有倒R3", grade: "C", deduction: 1 },
  //     { issue_item: "滑块压板、导向块、耐磨板、斜导柱材料与式样书不符，硬度不符合标准。", grade: "A", deduction: 5 },
  //     { issue_item: "滑块背面耐磨板螺钉未安装到位，油槽样式不一致。", grade: "B", deduction: 3 },
  //     { issue_item: "斜导柱摩擦不均匀、起刺、有弯曲，手试有晃动。", grade: "C", deduction: 1 },
  //     { issue_item: "滑块封料面边缘有挤伤，成型面有磕碰、划伤，有明显的砂轮研配痕迹。", grade: "B", deduction: 3 },
  //     { issue_item: "导轨尺寸测量与滑块间隙单边>0.02mm，左右用手摆动有明显的晃动。", grade: "A", deduction: 5 },
  //     { issue_item: "滑块压板与滑块支腿间隙尺寸测量>0.05mm", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_insulation_board",
  //   inspection_item: "隔热板",
  //   inspection_criteria: [
  //     "按模型确认是否有隔热板",
  //     "A1/B5板上常卸零件安装孔隔热板有让位",
  //     "除5mm整块隔热板外，其余形式的隔热板已整体加工扫平。",
  //     "有隔热板同时有芯轴压板的，芯轴压板要和隔热板平。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "没有预期的隔热板", grade: "B", deduction: 3 },
  //     { issue_item: "A1/B5板上常卸零件安装孔隔热板没有让位", grade: "B", deduction: 3 },
  //     { issue_item: "隔热板未整体加工扫平", grade: "B", deduction: 3 },
  //     { issue_item: "芯轴压板没有和隔热板平", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_mold_clamping",
  //   inspection_item: "码模",
  //   inspection_criteria: [
  //     "压肩形式符合式样书",
  //     "码模厚度符合式样书",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "压肩形式与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "码模厚度与式样书不符", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_pouring_system",
  //   inspection_item: "浇注",
  //   inspection_criteria: [
  //     "定位圈直径符合式样书",
  //     "定位圈内孔要和热流道嘴头配合",
  //     "模具浇口套球头表面是否完好 SR尺寸符合式样书",
  //     "机嘴处主浇口小端直径符合式样书",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "定位圈直径与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "定位圈内孔没有和热流道嘴头配合", grade: "B", deduction: 3 },
  //     { issue_item: "模具浇口套球头表面不完好 SR尺寸与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "机嘴处主浇口小端直径与式样书不符", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_nameplate",
  //   inspection_item: "标牌",
  //   inspection_criteria: [
  //     "各标牌槽位置、大小要符合客户标准。",
  //     "标牌种类、数量符合客户标准，标牌内容符合图纸；水路标牌上进出水标识的位置和模具完全相符，标牌大小要和槽一致。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "各标牌槽位置、大小不符合客户标准。", grade: "B", deduction: 3 },
  //     { issue_item: "标牌种类、数量不符合客户标准，标牌内容与图纸不符；水路标牌上进出水标识的位置和模具不相符，标牌大小要和槽不一致。", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_mold_hardness",
  //   inspection_item: "模具硬度",
  //   inspection_criteria: [
  //     "式样书要求氮化的工件是否已氮化",
  //     "冷流道浇口硬度HRC50~54度",
  //     "需氮化的斜顶杆已做氮化处理。",
  //     "侧抽已氮化、封料面无挤伤、滑动面摩擦痕迹均匀，无局部黑点。",
  //     "模具型腔、型芯、滑动部件硬度符合设计要求（检测硬度拍照留底）",
  //     "承压板、耐磨板样式及材料和硬度符合式样书（检测硬度拍照留底）",
  //     "承压板样式、材料和硬度符合式样书",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "式样书要求氮化的工件未氮化", grade: "A", deduction: 5 },
  //     { issue_item: "冷流道浇口不符合硬度HRC50~54度", grade: "B", deduction: 3 },
  //     { issue_item: "需氮化的斜顶杆未做氮化处理", grade: "B", deduction: 3 },
  //     { issue_item: "侧抽未氮化、封料面有挤伤、滑动面摩擦痕迹不均匀，有局部黑点。", grade: "B", deduction: 3 },
  //     { issue_item: "模具型腔、型芯、滑动部件硬度不符合设计要求", grade: "A", deduction: 5 },
  //     { issue_item: "承压板、耐磨板样式及材料和硬度与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "定承压板样式、材料和硬度与式样书不符", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_mark",
  //   inspection_item: "标识",
  //   inspection_criteria: [
  //     "家电模具A1板上要设计up箭头",
  //     "所有水路、油路、气路等标识符合设计标准",
  //     "模板上相关产品信息刻印符合模型要求",
  //     "可换版本号及零件编号数控刻印，按模型检查编号。",
  //     "各零部件刻有模具号和零件号，零件号和模型一致。",
  //     "成型面上产品图号符合式样书",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "家电模具A1板上未设计up箭头", grade: "C", deduction: 1 },
  //     { issue_item: "所有水路、油路、气路等标识不符合设计标准", grade: "B", deduction: 3 },
  //     { issue_item: "模板上相关产品信息刻印不符合模型要求", grade: "B", deduction: 3 },
  //     { issue_item: "可换版本号及零件编号数控刻印，未按模型检查编号。", grade: "B", deduction: 3 },
  //     { issue_item: "各零部件未刻模具号和零件号，零件号和模型不一致。", grade: "C", deduction: 1 },
  //     { issue_item: "成型面上产品图号与式样书不符", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_chamfer",
  //   inspection_item: "倒角",
  //   inspection_criteria: [
  //     "模架所有非封料棱边均倒C2~cC3角，无过大或过小的现象",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "模架有非封料棱边未倒C2~cC3角，有过大或过小的现象", grade: "C", deduction: 1 },
  //   ]
  // },
  // {
  //   inspection_key: "home_hydraulic_cylinder",
  //   inspection_item: "油缸",
  //   inspection_criteria: [
  //     "油缸内无铁屑、密封圈无破损。",
  //     "油缸连接块XY方向已加工1mm避空。",
  //     "油缸杆加\"U\"止转块",
  //     "油缸品牌、型号符合式样书",
  //     "侧抽研配摩擦面痕迹无起刺发黑现象",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "油缸内有铁屑、密封圈有破损。", grade: "A", deduction: 5 },
  //     { issue_item: "油缸连接块XY方向未加工1mm避空。", grade: "A", deduction: 5 },
  //     { issue_item: "油缸杆未加\"U\"止转块", grade: "B", deduction: 3 },
  //     { issue_item: "油缸品牌、型号与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "侧抽研配摩擦面痕迹有起刺发黑现象", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_lubrication",
  //   inspection_item: "润滑结构",
  //   inspection_criteria: [
  //     "需加油槽的部件、油槽深度0.3~0.5mm之间，油槽不得与边及孔相通",
  //     "压板、导轨已加油槽，自润滑无需油槽，碳柱面积符合设计标准。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "油槽深度超出0.3~0.5mm范围，油槽与边及孔相通", grade: "B", deduction: 3 },
  //     { issue_item: "压板、导轨未加油槽，碳柱面积不符合设计标准", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_angled_lifter",
  //   inspection_item: "斜顶",
  //   inspection_criteria: [
  //     "斜顶杆摩擦痕迹均匀，无线切割落料痕（含拨块槽），油槽面积在滑动范围内。",
  //     "斜顶导向块槽实测公差0~+0.02之间",
  //     "斜顶与型芯研配配间隙符合标准",
  //     "斜顶万向座的铜片要有碳润滑",
  //     "斜顶杆拨块滑动面有油槽，摩擦均匀，头部及倒角未与BO、BC干涉",
  //     "斜顶杆导向块带螺纹销钉已安装、斜顶固定座低于固定板0.05-0.1mm",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "斜顶杆摩擦痕迹不均匀，有线切割落料痕，油槽面积不在滑动范围内。", grade: "B", deduction: 3 },
  //     { issue_item: "斜顶导向块槽实测不在公差0~+0.02之间", grade: "A", deduction: 5 },
  //     { issue_item: "斜顶与型芯研配配间隙不符合标准", grade: "A", deduction: 5 },
  //     { issue_item: "斜顶万向座的铜片没有碳润滑", grade: "B", deduction: 3 },
  //     { issue_item: "斜顶杆拨块滑动面有油槽，摩擦不均匀，头部及倒角与BO、BC干涉", grade: "A", deduction: 5 },
  //     { issue_item: "斜顶杆导向块带螺纹销钉未安装、斜顶固定座未低于固定板0.05-0.1mm", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_support_pin",
  //   inspection_item: "垃圾钉",
  //   inspection_criteria: [
  //     "垃圾钉、立柱、顶出限位螺丝已紧固",
  //     "垃圾钉全数对碰、痕迹清晰。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "垃圾钉、立柱、顶出限位螺丝未紧固", grade: "B", deduction: 3 },
  //     { issue_item: "垃圾钉未全数对碰、痕迹不清晰。", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_forced_return",
  //   inspection_item: "强回位",
  //   inspection_criteria: [
  //     "模具回位方式符合式样书",
  //     "模具强回位螺纹尺寸符合式样书",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "模具回位方式与样式书不符", grade: "A", deduction: 5 },
  //     { issue_item: "模具强回位螺纹尺寸与样式书不符", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_assembly_specification",
  //   inspection_item: "装配规范",
  //   inspection_criteria: [
  //     "流道抛光",
  //     "研模结束后，将砂轮痕迹顺平、油平，保证模具外观研配面无明显的粗砂轮痕迹及划伤",
  //     "模具所有零部件不得有任何烧焊痕迹。",
  //     "各耐磨板承压板螺钉孔是否有偏心能安装到位",
  //     "垫铜皮工件已更换",
  //     "孔道吹气通畅、手电观察孔内无铁屑（T1前确认）。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "流道未抛光", grade: "C", deduction: 1 },
  //     { issue_item: "研模结束后，未将砂轮痕迹顺平、油平，模具外观研配面有明显的粗砂轮痕迹及划伤", grade: "B", deduction: 3 },
  //     { issue_item: "模具所有零部件有烧焊痕迹", grade: "B", deduction: 3 },
  //     { issue_item: "各耐磨板承压板螺钉孔有偏心，不能安装到位", grade: "B", deduction: 3 },
  //     { issue_item: "垫铜皮工件未更换", grade: "A", deduction: 5 },
  //     { issue_item: "孔道吹气通畅、手电观察孔内有铁屑", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_small_standard_part",
  //   inspection_item: "小型标准件",
  //   inspection_criteria: [
  //     "丝堵材质符合客户要求（蒸汽模具丝堵要不锈钢材质）",
  //     "各种螺钉螺纹未打磨、内六角无损伤，同一零件的螺钉长度一致，符合1.5D的标准。",
  //     "日期章等章是否转动，且与模具上的孔紧配，高度与型芯平齐或符合模型。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "模具所有丝堵材质不符合客户要求", grade: "B", deduction: 3 },
  //     { issue_item: "各种螺钉螺纹有打磨、内六角有损伤，同一零件的螺钉长度不一致，不符合1.5D的标准。", grade: "B", deduction: 3 },
  //     { issue_item: "日期章等章有转动，与模具上的孔不紧配，高度与型芯不平齐，不符合模型。", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_peripheral_standard_part",
  //   inspection_item: "外围标准件",
  //   inspection_criteria: [
  //     "行程开关型号及数量符合式样书",
  //     "气路、油路、水路接口（含热流道）型号符合式样书",
  //     "计数器槽形状、尺寸符合模型，并有计数器调节撞块。",
  //     "计数器型号符合式样书",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "行程开关型号及数量与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "气路、油路、水路接口（含热流道）型号与式样书不符", grade: "A", deduction: 5 },
  //     { issue_item: "计数器槽形状、尺寸与模型不符，无计数器调节撞块", grade: "B", deduction: 3 },
  //     { issue_item: "计数器型号与式样书不符", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_customer_standard",
  //   inspection_item: "客户标准",
  //   inspection_criteria: [
  //     "参考客户标准进行确认",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "与客户标准不符", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_pry_angle",
  //   inspection_item: "撬模角",
  //   inspection_criteria: [
  //     "撬模角是否已加工（符合客户要求）",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "撬模角未加工", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_mold_weighing",
  //   inspection_item: "模具称重",
  //   inspection_criteria: [
  //     "T1拆检时模具称重，重量记录到EX本表",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "重量未记录到EX本表", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_spare_replaceable_part",
  //   inspection_item: "成型备件可换件",
  //   inspection_criteria: [
  //     "成型备件可换件要求研配并试模验证（拆检重点确认）",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "成型备件可换件没有研配，没有试模验证", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_ejector_plate_preload_screw",
  //   inspection_item: "推出板预压螺钉",
  //   inspection_criteria: [
  //     "弹簧复位的推出板应设计预压螺钉（19.7.16增加）",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "弹簧复位的推出板未设计预压螺钉", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_angled_lifter_grinding_fit",
  //   inspection_item: "斜顶研配",
  //   inspection_criteria: [
  //     "斜顶研配后，自由状态下检查蓝丹周圈刚刚粘丹，斜顶与成形面平，用手可以推出。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "斜顶未与成形面平，不能用手可以推出。", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_clamping_base_plate_R_corner",
  //   inspection_item: "码模座板R角",
  //   inspection_criteria: [
  //     "与注塑机接触的两个座板，码模位置设计码模板台阶根部要有R6角，防止开裂（依据设计模型）",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "与注塑机接触的两个座板，码模位置设计码模板台阶根部没有R6角", grade: "B", deduction: 3 },
  //   ]
  // },
  // {
  //   inspection_key: "home_mold_engraving",
  //   inspection_item: "模具刻印",
  //   inspection_criteria: [
  //     "分型面的零部件不允许有手工刻印的标记，必须是采用设备加工标识（数控加工、刻字机刻印、腐蚀加工）",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "分型面的零部件有手工刻印非采用设备加工标识", grade: "C", deduction: 1 },
  //   ]
  // },
  // {
  //   inspection_key: "home_oil_cylinder_motion_interference",
  //   inspection_item: "油缸运动干涉",
  //   inspection_criteria: [
  //     "油缸与AO板重合位置A0板要有避空，确保合模不干涉油缸。",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "油缸与AO板重合位置A0板没有避空", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_mold_block_lifting_block_motion_interference",
  //   inspection_item: "模具垫块、吊模块运动干涉",
  //   inspection_criteria: [
  //     "模具垫块、吊模块与运动模板重合位置要设计避空，确保模具垫块、吊模块运动不与模板干涉",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "模具垫块、吊模块与运动模板重合位置没有避空", grade: "A", deduction: 5 },
  //   ]
  // },
  // {
  //   inspection_key: "home_hot_runner_exposed_wiring_protection",
  //   inspection_item: "热流道外漏接线防护",
  //   inspection_criteria: [
  //     "热流道有关外漏接线要增加外层防护保护（缠绕塑胶防护套）",
  //   ],
  //   category_level_1: "拆模检验",
  //   category_level_2: "家电",
  //   options: [
  //     { issue_item: "热流道有关外漏接线没有外层防护保护", grade: "A", deduction: 5 },
  //   ]
  // },
  {
    inspection_key: "home_hot_runner",
    inspection_item: "热流道",
    inspection_criteria: [
      `以下项目按照式样书检验确认:
      热流道样式、
      接线插座及底座型号、    
      接线符合式样书、
      电磁阀电压、
      电磁阀接线方式、
      热流道接线盒上要有对应的接线小标牌(见客户标准)`,
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "热流道样式、接线插座及底座型号、接线、电磁阀电压、电磁阀接线方式与式样书不符，或热流道接线盒上没有对应的接线小标牌", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hot_runner_2",
    inspection_item: "热流道",
    inspection_criteria: [
      "电磁阀电压、驱动方式、快换接头眼观符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "电磁阀电压、驱动方式、快换接头眼观与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hot_runner_3",
    inspection_item: "热流道",
    inspection_criteria: [
      "热流道嘴头与模具浇口处直径配合符合设计要求，无漏胶现象",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "热流道嘴头与模具浇口处直径配合不符合设计要求，有漏胶现象", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hot_runner_4",
    inspection_item: "热流道",
    inspection_criteria: [
      "热电偶型号符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "热电偶型号与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hot_runner_5",
    inspection_item: "热流道",
    inspection_criteria: [
      "热流道观察孔、排水槽是否需要并加工",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "热流道观察孔、排水槽需要但未加工", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_lift_safety",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "模具所有吊环眼观拧到底、吊环标识正确，AO/B0上吊环旋转轨迹上无干涉。按照设计要求整套模具起吊平衡。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具所有吊环眼观拧到底、吊环标识不正确", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_lift_safety_2",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "模具是否需要吊模块，吊模块上吊孔标识已做",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "吊模块上吊孔标识未做", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_lift_safety_3",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "模芯等工件吊装螺纹深度大于2.5D，吊环孔底孔无超差。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具所有吊环眼观拧到底、吊环标识不正确", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_position",
    inspection_item: "定位",
    inspection_criteria: [
      "所有模具都要有精定位（客户特殊要求除外）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具没有精定位", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_position_2",
    inspection_item: "定位",
    inspection_criteria: [
      "滑块压板、斜顶导向块、斜顶导滑座销钉孔及销钉无缺漏",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块压板、斜顶导向块、斜顶导滑座销钉孔或销钉有缺漏", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_position_3",
    inspection_item: "定位",
    inspection_criteria: [
      "配合面摩擦均匀，无局部黑印",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "配合面摩擦不均匀，有局部黑印", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_ejector_pin",
    inspection_item: "顶杆",
    inspection_criteria: [
      "顶出块顶杆要有止转机构",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "顶出块顶杆没有止转机构", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_ejector_pin_2",
    inspection_item: "顶杆",
    inspection_criteria: [
      "顶杆、顶管配合段是直径的3倍，其余做避让",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "顶杆、顶管配合段不是直径的3倍，其余未做避让", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_ejector_pin_3",
    inspection_item: "顶杆",
    inspection_criteria: [
      "方顶杆摩擦痕迹均匀，无线切割落料痕、无弯曲。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "方顶杆摩擦痕迹不均匀，有线切割落料痕、有弯曲。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_ejector_pin_4",
    inspection_item: "顶杆",
    inspection_criteria: [
      "圆顶杆摩擦痕迹均匀、无弯曲。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "圆顶杆摩擦痕迹不均匀、有弯曲。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_ejector_pin_5",
    inspection_item: "顶杆",
    inspection_criteria: [
      "顶出块摩擦痕迹均匀，无局部线形摩擦痕迹，有油槽（白电一般不要油槽）。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "顶出块摩擦痕迹不均匀，有局部线形摩擦痕迹，非白点但没有油槽。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_return_pin",
    inspection_item: "复位杆",
    inspection_criteria: [
      "复位杆下有树脂弹簧的，复位杆要有3mm活动空间（客户特殊要求不要树脂弹簧除外）不要树脂弹簧的复位杆挂台要和B2板平",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "有树脂弹簧，复位杆没有3mm活动空间", grade: "B", deduction: 3 },
      { issue_item: "没有树脂弹簧，复位杆挂台没有和B2板平", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_main_guide_pin",
    inspection_item: "大导柱",
    inspection_criteria: [
      "大导柱、导套样式及材料符合式样书（需检测硬度拍照）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "大导柱、导套样式或材料与样式书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_main_guide_pin_2",
    inspection_item: "大导柱",
    inspection_criteria: [
      "大小导套侧面紧固螺钉紧固到底",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "大小导套侧面紧固螺钉不紧固", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_main_guide_pin_3",
    inspection_item: "大导柱",
    inspection_criteria: [
      "大导套要有排气槽",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "大导套没有排气槽", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_stripper_plate_guide_pin",
    inspection_item: "推板导柱",
    inspection_criteria: [
      "推板导柱固定在B4板时，要紧配",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "推板导柱固定在B4板时，没有紧配", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_stripper_plate_guide_pin_2",
    inspection_item: "推板导柱",
    inspection_criteria: [
      "推板导柱或导套要有润滑结构，要符合设计标准",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "推板导柱或导套没有润滑结构，不符合设计标准", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_exhaust",
    inspection_item: "排气",
    inspection_criteria: [
      "内分型面有排气槽的要有排气引出孔与外界通",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "没有排气引出孔与外界通", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_water_channel",
    inspection_item: "水路",
    inspection_criteria: [
      "密封圈槽符合模型",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "密封圈槽与模型不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_water_channel_2",
    inspection_item: "水路",
    inspection_criteria: [
      "耐高温密封圈和普通密封圈没有用错",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "耐高温密封圈和普通密封圈用错", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_water_channel_3",
    inspection_item: "水路",
    inspection_criteria: [
      "隔水板材料正确、安装方向正确、无缺漏，松手钳检验隔水板无松动，长度尺寸到达水井底部，水井内手电检验无铁屑。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "隔水板材料不正确、安装方向错误、有缺漏，松手钳检验隔水板有松动，长度尺寸不到水井底部，水井内手电检验有铁屑。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_water_channel_4",
    inspection_item: "水路",
    inspection_criteria: [
      "隔水板无松动，水井内手电检验无铁屑。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "隔水板有松动，水井内手电检验有铁屑。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_slide_block",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块斜导柱插入之前，大导柱要先进入大导套。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块斜导柱插入之前，大导柱未先进入大导套。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_slide_block_2",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块前置弹簧结构的，漏在弹簧孔以外的弹簧长度大于弹簧孔深度的2/3时要有弹簧导杆",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块前置弹簧结构的，漏在弹簧孔以外的弹簧长度大于弹簧孔深度的2/3时没有弹簧导杆", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_slide_block_3",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块上斜导柱孔入口部倒R3",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块上斜导柱孔入口部没有倒R3", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_slide_block_4",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块压板、导向块、耐磨板、斜导柱材料符合式样书，硬度符合标准。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块压板、导向块、耐磨板、斜导柱材料与式样书不符，硬度不符合标准。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_slide_block_5",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块背面耐磨板螺钉已安装到位，油槽样式一致。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块背面耐磨板螺钉未安装到位，油槽样式不一致。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_slide_block_6",
    inspection_item: "滑块",
    inspection_criteria: [
      "斜导柱摩擦均匀、无起刺、无弯曲，手试无晃动。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜导柱摩擦不均匀、起刺、有弯曲，手试有晃动。", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_slide_block_7",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块封料面边缘无挤伤，成型面无磕碰、划伤，无明显的砂轮研配痕迹。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块封料面边缘有挤伤，成型面有磕碰、划伤，有明显的砂轮研配痕迹。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_slide_block_8",
    inspection_item: "滑块",
    inspection_criteria: [
      "导轨尺寸测量与滑块间隙单边≤0.02mm，左右用手摆动无明显的晃动。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "导轨尺寸测量与滑块间隙单边>0.02mm，左右用手摆动有明显的晃动。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_slide_block_9",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块压板与滑块支腿间隙尺寸测量≤0.05mm。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "滑块压板与滑块支腿间隙尺寸测量>0.05mm", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_insulation_board",
    inspection_item: "隔热板",
    inspection_criteria: [
      "按模型确认是否有隔热板",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "没有预期的隔热板", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_insulation_board_2",
    inspection_item: "隔热板",
    inspection_criteria: [
      "A1/B5板上常卸零件安装孔隔热板有让位",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "A1/B5板上常卸零件安装孔隔热板没有让位", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_insulation_board_3",
    inspection_item: "隔热板",
    inspection_criteria: [
      "除5mm整块隔热板外，其余形式的隔热板已整体加工扫平。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "隔热板未整体加工扫平", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_insulation_board_4",
    inspection_item: "隔热板",
    inspection_criteria: [
      "有隔热板同时有芯轴压板的，芯轴压板要和隔热板平。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "芯轴压板没有和隔热板平", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mold_clamping",
    inspection_item: "码模",
    inspection_criteria: [
      "压肩形式符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "压肩形式与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_mold_clamping_2",
    inspection_item: "码模",
    inspection_criteria: [
      "码模厚度符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "码模厚度与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_pouring_system",
    inspection_item: "浇注",
    inspection_criteria: [
      "定位圈直径符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "定位圈直径与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_pouring_system_2",
    inspection_item: "浇注",
    inspection_criteria: [
      "定位圈内孔要和热流道嘴头配合",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "定位圈内孔没有和热流道嘴头配合", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_pouring_system_3",
    inspection_item: "浇注",
    inspection_criteria: [
      "模具浇口套球头表面是否完好 SR尺寸符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具浇口套球头表面不完好 SR尺寸与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_pouring_system_4",
    inspection_item: "浇注",
    inspection_criteria: [
      "机嘴处主浇口小端直径符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "机嘴处主浇口小端直径与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_nameplate",
    inspection_item: "标牌",
    inspection_criteria: [
      "各标牌槽位置、大小要符合客户标准。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "各标牌槽位置、大小不符合客户标准。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_nameplate_2",
    inspection_item: "标牌",
    inspection_criteria: [
      "标牌种类、数量符合客户标准，标牌内容符合图纸；水路标牌上进出水标识的位置和模具完全相符，标牌大小要和槽一致。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "标牌种类、数量不符合客户标准，标牌内容与图纸不符；水路标牌上进出水标识的位置和模具不相符，标牌大小要和槽不一致。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mold_hardness",
    inspection_item: "模具硬度",
    inspection_criteria: [
      "式样书要求氮化的工件是否已氮化",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "式样书要求氮化的工件未氮化", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_mold_hardness_2",
    inspection_item: "模具硬度",
    inspection_criteria: [
      "冷流道浇口硬度HRC50~54度",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "冷流道浇口不符合硬度HRC50~54度", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mold_hardness_3",
    inspection_item: "模具硬度",
    inspection_criteria: [
      "需氮化的斜顶杆已做氮化处理。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "需氮化的斜顶杆未做氮化处理", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mold_hardness_4",
    inspection_item: "模具硬度",
    inspection_criteria: [
      "侧抽已氮化、封料面无挤伤、滑动面摩擦痕迹均匀，无局部黑点。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "侧抽未氮化、封料面有挤伤、滑动面摩擦痕迹不均匀，有局部黑点。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mold_hardness_5",
    inspection_item: "模具硬度",
    inspection_criteria: [
      "模具型腔、型芯、滑动部件硬度符合设计要求（检测硬度拍照留底）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具型腔、型芯、滑动部件硬度不符合设计要求", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_mold_hardness_6",
    inspection_item: "模具硬度",
    inspection_criteria: [
      "承压板、耐磨板样式及材料和硬度符合式样书（检测硬度拍照留底）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "承压板、耐磨板样式及材料和硬度与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_mold_hardness_7",
    inspection_item: "模具硬度",
    inspection_criteria: [
      // "承压板样式、材料和硬度符合式样书",
      "精定位、楔契块、导滑块/导轨材质与硬度的检测确认（拍照）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      // { issue_item: "定承压板样式、材料和硬度与式样书不符", grade: "A", deduction: 5 },
      { issue_item: "精定位、楔契块、导滑块/导轨材质与硬度检测不通过", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_mark",
    inspection_item: "标识",
    inspection_criteria: [
      "家电模具A1板上要设计up箭头",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "家电模具A1板上未设计up箭头", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_mark_2",
    inspection_item: "标识",
    inspection_criteria: [
      "所有水路、油路、气路等标识符合设计标准",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "所有水路、油路、气路等标识不符合设计标准", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mark_3",
    inspection_item: "标识",
    inspection_criteria: [
      "模板上相关产品信息刻印符合模型要求",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模板上相关产品信息刻印不符合模型要求", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mark_4",
    inspection_item: "标识",
    inspection_criteria: [
      "可换版本号及零件编号数控刻印，按模型检查编号。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "可换版本号及零件编号数控刻印，未按模型检查编号。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mark_5",
    inspection_item: "标识",
    inspection_criteria: [
      "各零部件刻有模具号和零件号，零件号和模型一致。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "各零部件未刻模具号和零件号，零件号和模型不一致。", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_mark_6",
    inspection_item: "标识",
    inspection_criteria: [
      "成型面上产品图号符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "成型面上产品图号与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_chamfer",
    inspection_item: "倒角",
    inspection_criteria: [
      "模架所有非封料棱边均倒C2~cC3角，无过大或过小的现象",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模架有非封料棱边未倒C2~cC3角，有过大或过小的现象", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_hydraulic_cylinder",
    inspection_item: "油缸",
    inspection_criteria: [
      "油缸内无铁屑、密封圈无破损。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "油缸内有铁屑、密封圈有破损。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hydraulic_cylinder_2",
    inspection_item: "油缸",
    inspection_criteria: [
      "油缸连接块XY方向已加工1mm避空。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "油缸连接块XY方向未加工1mm避空。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hydraulic_cylinder_3",
    inspection_item: "油缸",
    inspection_criteria: [
      "油缸杆加\"U\"止转块",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "油缸杆未加\"U\"止转块", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_hydraulic_cylinder_4",
    inspection_item: "油缸",
    inspection_criteria: [
      "油缸品牌、型号符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "油缸品牌、型号与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hydraulic_cylinder_5",
    inspection_item: "油缸",
    inspection_criteria: [
      "侧抽研配摩擦面痕迹无起刺发黑现象",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "侧抽研配摩擦面痕迹有起刺发黑现象", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_lubrication",
    inspection_item: "润滑结构",
    inspection_criteria: [
      "需加油槽的部件、油槽深度0.3~0.5mm之间，油槽不得与边及孔相通",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "油槽深度超出0.3~0.5mm范围，油槽与边及孔相通", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_lubrication_2",
    inspection_item: "润滑结构",
    inspection_criteria: [
      "压板、导轨已加油槽，自润滑无需油槽，碳柱面积符合设计标准。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "压板、导轨未加油槽，碳柱面积不符合设计标准", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_angled_lifter",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶杆摩擦痕迹均匀，无线切割落料痕（含拨块槽），油槽面积在滑动范围内。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜顶杆摩擦痕迹不均匀，有线切割落料痕，油槽面积不在滑动范围内。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_angled_lifter_2",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶导向块槽实测公差0~+0.02之间",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜顶导向块槽实测不在公差0~+0.02之间", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_angled_lifter_3",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶与型芯研配配间隙符合标准",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜顶与型芯研配配间隙不符合标准", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_angled_lifter_4",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶万向座的铜片要有碳润滑",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜顶万向座的铜片没有碳润滑", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_angled_lifter_5",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶杆拨块滑动面有油槽，摩擦均匀，头部及倒角未与BO、BC干涉",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜顶杆拨块滑动面有油槽，摩擦不均匀，头部及倒角与BO、BC干涉", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_angled_lifter_6",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶杆导向块带螺纹销钉已安装、斜顶固定座低于固定板0.05-0.1mm",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜顶杆导向块带螺纹销钉未安装、斜顶固定座未低于固定板0.05-0.1mm", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_support_pin",
    inspection_item: "垃圾钉",
    inspection_criteria: [
      "垃圾钉、立柱、顶出限位螺丝已紧固",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "垃圾钉、立柱、顶出限位螺丝未紧固", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_support_pin_2",
    inspection_item: "垃圾钉",
    inspection_criteria: [
      "垃圾钉全数对碰、痕迹清晰。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "垃圾钉未全数对碰、痕迹不清晰。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_forced_return",
    inspection_item: "强回位",
    inspection_criteria: [
      "模具回位方式符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具回位方式与样式书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_forced_return_2",
    inspection_item: "强回位",
    inspection_criteria: [
      "模具强回位螺纹尺寸符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具强回位螺纹尺寸与样式书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_assembly_specification",
    inspection_item: "装配规范",
    inspection_criteria: [
      "流道抛光",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "流道未抛光", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_assembly_specification_2",
    inspection_item: "装配规范",
    inspection_criteria: [
      "研模结束后，将砂轮痕迹顺平、油平，保证模具外观研配面无明显的粗砂轮痕迹及划伤",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "研模结束后，未将砂轮痕迹顺平、油平，模具外观研配面有明显的粗砂轮痕迹及划伤", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_assembly_specification_3",
    inspection_item: "装配规范",
    inspection_criteria: [
      "模具所有零部件不得有任何烧焊痕迹。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具所有零部件有烧焊痕迹", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_assembly_specification_4",
    inspection_item: "装配规范",
    inspection_criteria: [
      "各耐磨板承压板螺钉孔是否有偏心能安装到位",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "各耐磨板承压板螺钉孔有偏心，不能安装到位", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_assembly_specification_5",
    inspection_item: "装配规范",
    inspection_criteria: [
      "垫铜皮工件已更换",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "垫铜皮工件未更换", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_assembly_specification_6",
    inspection_item: "装配规范",
    inspection_criteria: [
      "孔道吹气通畅、手电观察孔内无铁屑（T1前确认）。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "孔道吹气通畅、手电观察孔内有铁屑", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_small_standard_part",
    inspection_item: "小型标准件",
    inspection_criteria: [
      "丝堵材质符合客户要求（蒸汽模具丝堵要不锈钢材质）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具所有丝堵材质不符合客户要求", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_small_standard_part_2",
    inspection_item: "小型标准件",
    inspection_criteria: [
      "各种螺钉螺纹未打磨、内六角无损伤，同一零件的螺钉长度一致，符合1.5D的标准。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "各种螺钉螺纹有打磨、内六角有损伤，同一零件的螺钉长度不一致，不符合1.5D的标准。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_small_standard_part_3",
    inspection_item: "小型标准件",
    inspection_criteria: [
      "日期章等章是否转动，且与模具上的孔紧配，高度与型芯平齐或符合模型。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "日期章等章有转动，与模具上的孔不紧配，高度与型芯不平齐，不符合模型。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_peripheral_standard_part",
    inspection_item: "外围标准件",
    inspection_criteria: [
      "行程开关型号及数量符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "行程开关型号及数量与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_peripheral_standard_part_2",
    inspection_item: "外围标准件",
    inspection_criteria: [
      "气路、油路、水路接口（含热流道）型号符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "气路、油路、水路接口（含热流道）型号与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_peripheral_standard_part_3",
    inspection_item: "外围标准件",
    inspection_criteria: [
      "计数器槽形状、尺寸符合模型，并有计数器调节撞块。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "计数器槽形状、尺寸与模型不符，无计数器调节撞块", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_peripheral_standard_part_4",
    inspection_item: "外围标准件",
    inspection_criteria: [
      "计数器型号符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "计数器型号与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_customer_standard",
    inspection_item: "客户标准",
    inspection_criteria: [
      "参考客户标准进行确认",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "与客户标准不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_pry_angle",
    inspection_item: "撬模角",
    inspection_criteria: [
      "撬模角是否已加工（符合客户要求）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "撬模角未加工", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mold_weighing",
    inspection_item: "模具称重",
    inspection_criteria: [
      "T1拆检时模具称重，重量记录到EX本表",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "重量未记录到EX本表", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_spare_replaceable_part",
    inspection_item: "成型备件可换件",
    inspection_criteria: [
      "成型备件可换件要求研配并试模验证（拆检重点确认）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "成型备件可换件没有研配，没有试模验证", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_ejector_plate_preload_screw",
    inspection_item: "推出板预压螺钉",
    inspection_criteria: [
      "弹簧复位的推出板应设计预压螺钉（19.7.16增加）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "弹簧复位的推出板未设计预压螺钉", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_angled_lifter_grinding_fit",
    inspection_item: "斜顶研配",
    inspection_criteria: [
      "斜顶研配后，自由状态下检查蓝丹周圈刚刚粘丹，斜顶与成形面平，用手可以推出。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "斜顶未与成形面平，不能用手可以推出。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_clamping_base_plate_R_corner",
    inspection_item: "码模座板R角",
    inspection_criteria: [
      "与注塑机接触的两个座板，码模位置设计码模板台阶根部要有R6角，防止开裂（依据设计模型）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "与注塑机接触的两个座板，码模位置设计码模板台阶根部没有R6角", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "home_mold_engraving",
    inspection_item: "模具刻印",
    inspection_criteria: [
      "分型面的零部件不允许有手工刻印的标记，必须是采用设备加工标识（数控加工、刻字机刻印、腐蚀加工）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "分型面的零部件有手工刻印非采用设备加工标识", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "home_oil_cylinder_motion_interference",
    inspection_item: "油缸运动干涉",
    inspection_criteria: [
      "油缸与AO板重合位置A0板要有避空，确保合模不干涉油缸。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "油缸与AO板重合位置A0板没有避空", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_mold_block_lifting_block_motion_interference",
    inspection_item: "模具垫块、吊模块运动干涉",
    inspection_criteria: [
      "模具垫块、吊模块与运动模板重合位置要设计避空，确保模具垫块、吊模块运动不与模板干涉",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "模具垫块、吊模块与运动模板重合位置没有避空", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "home_hot_runner_exposed_wiring_protection",
    inspection_item: "热流道外漏接线防护",
    inspection_criteria: [
      "热流道有关外漏接线要增加外层防护保护（缠绕塑胶防护套）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "家电",
    options: [
      { issue_item: "热流道有关外漏接线没有外层防护保护", grade: "A", deduction: 5 },
    ]
  },

]

export const hisenseHomeAppMoldDismantlingInspectionItems = HISENSE_HOME_APP_MOLD_DISMANTLING_TRIAL_ISSUE_TEMPLATE.map(item => {
  return {
    ...item,
    deduction: null,
    grade: null,
    id: null,
    is_old_issue: false,
    issue_code: null,
    issue_description: null,
    issue_images: [],
    issue_files: [],
    issue_item: null,
    issue_type: "disassembly_insp",
    judgement: null,
    judgement_by: null,
    judgement_at: null,
    trial_session_id: null,
  }
})

export const HISENSE_AUTO_MOLD_DISMANTLING_TRIAL_ISSUE_TEMPLATE = [
//   {
//     inspection_key: "auto_clamp_peripheral",
//     inspection_item: "合模外围",
//     inspection_criteria: [
//       "模架天地侧起吊吊环能拧到底，吊环标识正确。",
//       "天地侧起吊吊环旋转轨迹内，不能干涉周边零件。",
//       "模具整模、半模、单板起吊平衡（如果进行吊装平衡测试要拍照留底避免后期重复工作）",
//       "大小导套侧面止付螺丝要拧到底",
//       "大导套要有排气槽",
//       "模架上水路、油路、气路等刻印标识齐全。",
//       "水路接口（含集水器、分水器）符合式样书",
//       "天侧及操作侧无进出水口，放在非操作侧，如有违背需反馈确认。",
//       "油缸杆要加\"U\"止转块",
//       "芯轴压板和模板同高，有隔热板的和隔热板同高。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "模架天地侧起吊吊环不能拧到底", grade: "A", deduction: 5 },
//       { issue_item: "吊环标识不正确", grade: "A", deduction: 5 },
//       { issue_item: "天地侧起吊吊环旋转轨迹影响周边零件", grade: "B", deduction: 3 },
//       { issue_item: "模具整模、半模、单板起吊不平衡", grade: "A", deduction: 5 },
//       { issue_item: "大小导套侧面止付螺丝不能拧到底", grade: "A", deduction: 5 },
//       { issue_item: "大导套要没有排气槽", grade: "A", deduction: 5 },
//       { issue_item: "模架上水路、油路、气路等刻印标识不齐全", grade: "B", deduction: 3 },
//       { issue_item: "水路接口不符合式样书", grade: "B", deduction: 3 },
//       { issue_item: "油缸杆没有加\"U\"止转块", grade: "B", deduction: 3 },
//       { issue_item: "芯轴压板和模板不同高", grade: "A", deduction: 5 },
//       { issue_item: "隔热板不同高", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_after_mold_split",
//     inspection_item: "分模后",
//     inspection_criteria: [
//       "对所有水路，进行水流量测试（制作水流量报告，如有疑问同项目确认）",
//       "有外置弹簧的需要加保护套",
//       "天侧滑块要有限位机构",
//       "滑块上斜导柱孔孔入口部倒R3",
//       "模具型芯有热流道浇口刻印（G1、G2、………)",
//       "分型面研配痕迹均匀，无发黑发亮的研配点，无磕碰划伤。",
//       "插穿面无明显研配黑点",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "水路测试问题", grade: "A", deduction: 5 },
//       { issue_item: "有外置弹簧的没有加保护套", grade: "B", deduction: 3 },
//       { issue_item: "天侧滑块没有限位机构", grade: "B", deduction: 3 },
//       { issue_item: "滑块上斜导柱孔孔入口部不符合倒R3", grade: "B", deduction: 3 },
//       { issue_item: "模具型芯没有热流道浇口刻印", grade: "B", deduction: 3 },
//       { issue_item: "分型面研配痕迹不均匀", grade: "B", deduction: 3 },
//       { issue_item: "有发黑发亮的研配点", grade: "B", deduction: 3 },
//       { issue_item: "有磕碰划伤", grade: "B", deduction: 3 },
//       { issue_item: "插穿面有明显研配黑点", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_mold_dismantling_process",
//     inspection_item: "拆模过程中",
//     inspection_criteria: [
//       "滑块前置弹簧裸露段大于直径的3倍时要加导向杆",
//       "滑块各配合面均匀，无研配黑点，配合尖角处无倒角。",
//       "滑块下耐磨板无起刺、背面耐磨板配合均匀，斜度吻合。",
//       "滑块与导轨的配合间隙单边0.02",
//       "滑块与压板间隙0.03mm，滑块压板紧固后，滑块动作流畅、不晃动。",
//       "滑动面运动摩擦痕迹均匀，无局部黑点。",
//       "侧抽研配摩擦面无起刺发黑发亮现象",
//       "斜顶油槽范围覆盖所有滑动段（方顶杆 原顶杆除外）",
//       "斜顶头部以下和方顶杆导向部分磨避空单边0.05mm",
//       "隔热板上有拆卸零件的螺钉头避空。",
//       "垃圾钉全数对碰痕迹清晰。",
//       "支撑柱与方铁高度在公差在+0.05至+0.15间",
//       "各销钉松紧适中，没有过松或起刺现象。",
//       "顶出块顶杆有止转机构",
//       "复位杆下有树脂弹簧的，复位杆要有3mm活动空间（客户特殊要求不要树脂弹簧除外）不要树脂弹簧的复位杆挂台要和B2板平",
//       "隔水板方向安装正确，在模板上有方向标识，紧配无松动、无缺漏（抽检隔水片）。",
//       "需加油槽的部件、油槽深度0.3~0.5mm之间，油槽不得与边及孔相通。",
//       "内分型面及镶件有排气槽的，要有排气引出孔或引出槽与外界通气。",
//       "各零部件清晰的刻有模具编号和零件编号，零件号和模型一致。",
//       "模具外观研配面无明显的砂轮痕迹及划伤。砂轮痕迹用320#油石顺平，",
//       "模具所有零部件不得有任何烧焊痕迹",
//       "各工件无垫铜/铁皮现象",
//       "要求氮化的工件均已氮化",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "滑块前置弹簧裸露段大于直径的3倍时没有加导向杆", grade: "B", deduction: 3 },
//       { issue_item: "滑块各配合面不均匀，有研配黑点，配合尖角处无倒角", grade: "B", deduction: 3 },
//       { issue_item: "滑块下耐磨板有起刺、背面耐磨板配合不均匀，斜度不吻合", grade: "B", deduction: 3 },
//       { issue_item: "滑块与导轨的配合间隙单边不符合0.02", grade: "B", deduction: 3 },
//       { issue_item: "滑块与压板间隙不满足0.03mm，滑块压板紧固后，滑块动作不流畅、有晃动。", grade: "A", deduction: 5 },
//       { issue_item: "滑动面运动摩擦痕迹不均匀，有局部黑点", grade: "A", deduction: 5 },
//       { issue_item: "侧抽研配摩擦面有起刺发黑发亮现象", grade: "A", deduction: 5 },
//       { issue_item: "斜顶油槽范围未覆盖所有滑动段", grade: "B", deduction: 3 },
//       { issue_item: "斜顶头部以下和方顶杆导向部分磨避空单边不满足0.05mm", grade: "B", deduction: 3 },
//       { issue_item: "隔热板上有拆卸零件的螺钉头没有避空。", grade: "B", deduction: 3 },
//       { issue_item: "垃圾钉对碰痕迹不清晰。", grade: "B", deduction: 3 },
//       { issue_item: "支撑柱与方铁高度在公差不在+0.05至+0.15间", grade: "A", deduction: 5 },
//       { issue_item: "各销钉松紧有过松或起刺现象。", grade: "B", deduction: 3 },
//       { issue_item: "顶出块顶杆没有止转机构", grade: "B", deduction: 3 },
//       { issue_item: "复位杆下有树脂弹簧的，复位杆要没有3mm活动空间；不要树脂弹簧的复位杆挂台没有和B2板平", grade: "B", deduction: 3 },
//       { issue_item: "隔水板方向安装不正确，在模板上没有方向标识，紧配有松动、有缺漏", grade: "B", deduction: 3 },
//       { issue_item: "需加油槽的部件、油槽深度不在0.3~0.5mm之间，油槽与边及孔相通", grade: "A", deduction: 5 },
//       { issue_item: "内分型面及镶件有排气槽的，没有排气引出孔或引出槽与外界通气", grade: "B", deduction: 3 },
//       { issue_item: "零部件未清晰的刻有模具编号和零件编号，零件号和模型不一致", grade: "A", deduction: 5 },
//       { issue_item: "模具外观研配面有明显的砂轮痕迹及划伤。砂轮痕迹未用320#油石顺平", grade: "A", deduction: 5 },
//       { issue_item: "模具有零部件有烧焊痕迹", grade: "A", deduction: 5 },
//       { issue_item: "工件有垫铜/铁皮现象", grade: "A", deduction: 5 },
//       { issue_item: "要求氮化的工件未氮化", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_hot_runner",
//     inspection_item: "热流道",
//     inspection_criteria: [
//       `以下项目按照式样书检验确认:
// 热流道样式、
// 接线插座及底座型号、    
// 接线符合式样书、
// 电磁阀电压、
// 电磁阀接线方式、
// 热流道接线盒上要有对应的接线小标牌(见客户标准)`,
//       "热流道接线盒是否沉入模板或加保护块",
//       "热流道嘴头与模具浇口处直径配合符合设计要求，无漏胶现象.",
//       "热电偶型号符合式样书",
//       "热流道观察孔、排水槽是否需要并加工",
//       "热流道水路，油路是否有出厂用水嘴，是否需要连接到集水器或集油器上（需确认）",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "热流道样式、接线插座及底座型号、接线、电磁阀电压、电磁阀接线方式与式样书不符，或热流道接线盒上没有对应的接线小标牌", grade: "B", deduction: 5 },
//       { issue_item: "热流道接线盒没有沉入模板，未加保护块", grade: "C", deduction: 1 },
//       { issue_item: "热流道嘴头与模具浇口处直径配合不符合设计要求，有漏胶现象", grade: "B", deduction: 3 },
//       { issue_item: "热电偶型号与式样书不符", grade: "B", deduction: 3 },
//       { issue_item: "热流道观察孔、排水槽未加工", grade: "C", deduction: 1 },
//       { issue_item: "热流道水路，油路没有出厂用水嘴，需要但没有连接到集水器或集油器上", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_lift_safety",
//     inspection_item: "起吊安全",
//     inspection_criteria: [
//       "所有模具四面都要有吊环孔（客户特殊要求除外）",
//       "点检A1 B4 板正面是否有设计吊装吊环.",
//       "前后模分型面是否有半模翻模吊环（特殊情况同设计确认）",
//       "模具是否需要吊模块，吊模块上吊孔标识已做。",
//       "模芯等工件吊装螺纹深度大于2.5D，吊环底孔无超差。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "模具四面没有吊环孔", grade: "B", deduction: 3 },
//       { issue_item: "点检A1 B4 板正面没有设计吊装吊环", grade: "B", deduction: 3 },
//       { issue_item: "前后模分型面没有半模翻模吊环", grade: "B", deduction: 3 },
//       { issue_item: "吊模块上吊孔标识未做", grade: "B", deduction: 3 },
//       { issue_item: "模芯等工件吊装螺纹深度未大于2.5D，吊环底孔超差", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_design_check_item",
//     inspection_item: "设计点检项",
//     inspection_criteria: [
//       "所有模具都要有精定位（客户特殊要求除外）",
//       "异形工件要有二次加工基准边",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "模具没有精定位", grade: "B", deduction: 3 },
//       { issue_item: "异形工件没有二次加工基准边", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_return_pin",
//     inspection_item: "复位杆",
//     inspection_criteria: [
//       "复位杆与其挡块对碰面积大于复位杆截面积的50%。",
//       "复位杆挡块硬度HRC48~52度（需检测硬度拍照）",
//       "复位杆孔是否按标准避空单边0.2~0.5mm。",
//       "有复位弹簧的模具，弹簧要顶在推出固定板上，要设计有预压螺丝。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "复位杆与其挡块对碰面积没有大于复位杆截面积的50%", grade: "B", deduction: 3 },
//       { issue_item: "复位杆挡块硬度不满足HRC48~52度", grade: "B", deduction: 3 },
//       { issue_item: "复位杆孔没有按标准避空单边0.2~0.5mm。", grade: "B", deduction: 3 },
//       { issue_item: "有复位弹簧的模具，弹簧没有顶在推出固定板上，没有设计预压螺丝", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_main_guide_pin",
//     inspection_item: "大导柱",
//     inspection_criteria: [
//       "大导柱、导套样式及材料符合式样书（需检测硬度拍照）",
//       "大导柱与安装孔要紧配",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "大导柱、导套样式及材料与式样书不符", grade: "A", deduction: 5 },
//       { issue_item: "大导柱与安装孔不紧配", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_support_bushing",
//     inspection_item: "中托司",
//     inspection_criteria: [
//       "中托司导套与B2板紧配，与B3板滑配",
//       "中托司固定在B4板时，要紧配",
//       "中托司要有润滑结构",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "中托司导套与B2板不紧配，与B3板无滑配", grade: "B", deduction: 3 },
//       { issue_item: "中托司固定在B4板时，没有紧配", grade: "B", deduction: 3 },
//       { issue_item: "中托司没有润滑结构", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_water_channel",
//     inspection_item: "水路",
//     inspection_criteria: [
//       "水嘴沉孔符合标准（没有特殊要求情况下，默认φ30*25深，两个孔中心小于35mm的做通）",
//       "密封圈槽符合标准，使用的密封圈槽与密封圈规格向对应。（密封圈选用是否符合要求，耐高温或普通）",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "水嘴沉孔不符合标准", grade: "A", deduction: 5 },
//       { issue_item: "密封圈槽不符合标准", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_slide_block",
//     inspection_item: "滑块",
//     inspection_criteria: [
//       "斜导柱无松动、无起刺，长度不可超过大导柱，斜度与斜导柱孔吻合。",
//       "滑块压板、导向块、耐磨板、斜导柱材料符合式样书，硬度符合标准。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "斜导柱无松动、无起刺，长度超过大导柱，斜度与斜导柱孔不吻合。", grade: "A", deduction: 5 },
//       { issue_item: "滑块压板、导向块、耐磨板、斜导柱材料与式样书不符，硬度不符合标准。", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_insulation_board",
//     inspection_item: "隔热板",
//     inspection_criteria: [
//       "隔热板距码模板边的距离要让过倒角，但最大不得超过10mm",
//       "模具外部隔热板已安装，固定螺钉齐全并紧固",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "隔热板距码模板边的距离没有让过倒角，或超过10mm", grade: "C", deduction: 1 },
//       { issue_item: "模具外部隔热板未安装，固定螺钉不齐全或不紧固", grade: "C", deduction: 1 },
//     ]
//   },
//   {
//     inspection_key: "auto_mold_clamping",
//     inspection_item: "码模",
//     inspection_criteria: [
//       "压肩形式符合式样书",
//       "码模厚度符合式样书",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "压肩形式与式样书不符", grade: "B", deduction: 3 },
//       { issue_item: "码模厚度与式样书不符", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_pouring_system",
//     inspection_item: "浇注",
//     inspection_criteria: [
//       "定位圈直径符合式样书：（记录）",
//       "模具浇口套球头表面是否完好 SR尺寸符合式样书",
//       "机嘴处主浇口小端直径符合式样书",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "定位圈直径与式样书不符", grade: "A", deduction: 5 },
//       { issue_item: "模具浇口套球头表面不完好 SR尺寸与式样书不符", grade: "A", deduction: 5 },
//       { issue_item: "机嘴处主浇口小端直径与式样书不符", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_nameplate",
//     inspection_item: "标牌",
//     inspection_criteria: [
//       "各标牌槽位置、大小要符合客户标准，标牌大小要和槽一致。",
//       "标牌种类、数量符合客户标准，标牌内容符合图纸；水路标牌上进出水标识的位置和模具完全相符。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "各标牌槽位置、大小不符合客户标准。标牌大小要和槽不一致", grade: "C", deduction: 1 },
//       { issue_item: "标牌种类、数量不符合客户标准，标牌内容与图纸不符；水路标牌上进出水标识的位置和模具不相符", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_hardness",
//     inspection_item: "硬度",
//     inspection_criteria: [
//       "冷流道浇口硬度HRC50~54度",
//       "需氮化的斜顶杆已做氮化处理",
//       "模具型腔、型芯、滑动部件硬度符合设计要求（检测硬度拍照留底）",
//       "型腔、型芯、滑块材料符合要求，查看材质证明",
//       "承压板硬度符合式样书",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "冷流道浇口硬度不满足HRC50~54度", grade: "A", deduction: 5 },
//       { issue_item: "需氮化的斜顶杆未做氮化处理", grade: "A", deduction: 5 },
//       { issue_item: "模具型腔、型芯、滑动部件硬度不符合设计要求", grade: "A", deduction: 5 },
//       { issue_item: "型腔、型芯、滑块材料不符合要求，无材质证明", grade: "A", deduction: 5 },
//       { issue_item: "承压板硬度与式样书不符", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_mark",
//     inspection_item: "标识",
//     inspection_criteria: [
//       "模板上相关产品信息刻印符合模型要求（可换版本号应对照可换说明书检查编号）",
//       "模板顶出、重量、警示、装配编号、模具编号刻印符合要求",
//       "各类标识排查无遗漏",
//       "各钢印字码臃肿已修平",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "模板上相关产品信息刻印不符合模型要求", grade: "A", deduction: 5 },
//       { issue_item: "模板顶出、重量、警示、装配编号、模具编号刻印不符合要求", grade: "B", deduction: 3 },
//       { issue_item: "各类标识排查有遗漏", grade: "C", deduction: 1 },
//       { issue_item: "各钢印字码臃肿未修平", grade: "C", deduction: 1 },
//     ]
//   },
//   {
//     inspection_key: "auto_chamfer",
//     inspection_item: "倒角",
//     inspection_criteria: [
//       "撬模角无缺漏，尺寸按30*30*5设计（客户特殊要求除外）",
//       "模架基准倒角正确；",
//       "模架所有非封料棱边均倒C2~C3角，无过大或过小的现象",
//       "各非成型孔、边倒c1~c2角（参考倒角排查表）",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "撬模角有缺漏，尺寸未按30*30*5设计", grade: "C", deduction: 1 },
//       { issue_item: "模架基准倒角不正确", grade: "C", deduction: 1 },
//       { issue_item: "模架非封料棱边未倒C2~C3角，有过大或过小的现象", grade: "C", deduction: 1 },
//       { issue_item: "各钢印各非成型孔、边未倒c1~c2角", grade: "C", deduction: 1 },
//     ]
//   },
//   {
//     inspection_key: "auto_counter",
//     inspection_item: "计数器",
//     inspection_criteria: [
//       "计数器槽形状、尺寸符合模型，并有计数器调节撞块。",
//       "计数器型号符合式样书",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "计数器槽形状、尺寸不符合模型，没有计数器调节撞块。", grade: "C", deduction: 1 },
//       { issue_item: "计数器型号与式样书不符", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_limit_switch",
//     inspection_item: "行程开关",
//     inspection_criteria: [
//       "限位开关型号/数量符合设计要求",
//       "行程开关是否需要沉入模板",
//       "限位开关插座及接线盒符合标准",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "限位开关型号/数量不符合设计要求", grade: "A", deduction: 5 },
//       { issue_item: "行程开关需要但未沉入模板", grade: "C", deduction: 1 },
//       { issue_item: "限位开关插座及接线盒不符合标准", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_hydraulic_cylinder",
//     inspection_item: "油缸",
//     inspection_criteria: [
//       "油路接口（含热流道油路）型号符合式样书：",
//       "油缸品牌符合式样书。油缸铁屑汽车模具T3后T4前检查结束。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "油路接口（含热流道油路）型号与式样书不符", grade: "B", deduction: 3 },
//       { issue_item: "油缸品牌与式样书不符", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_lubrication",
//     inspection_item: "润滑",
//     inspection_criteria: [
//       "铜加碳的工件，碳点面积不少于所在平面面积的25%，碳点不能矮于铜面，或缺碳现象。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "铜加碳的工件，碳点面积少于所在平面面积的25%，或碳点矮于铜面，或有缺碳现象", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_angled_lifter",
//     inspection_item: "斜顶",
//     inspection_criteria: [
//       "斜顶与型芯研配配间隙符合标准",
//       "斜顶万向座的铜片要有碳润滑",
//       "斜顶研配后，分型面与斜顶平，斜顶周圈刚刚粘丹，斜顶尾部用手能推出。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "斜顶与型芯研配配间隙不符合标准", grade: "B", deduction: 3 },
//       { issue_item: "斜顶万向座的铜片没有碳润滑", grade: "B", deduction: 3 },
//       { issue_item: "斜顶研配后，分型面与斜顶不平，或斜顶周圈没有刚刚粘丹，或斜顶尾部不能用手推出", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_ejection",
//     inspection_item: "顶出",
//     inspection_criteria: [
//       "垃圾钉、顶出限位块螺丝已紧固",
//       "模具回位方式符合式样书",
//       "模具强回位螺纹尺寸符合式样书",
//       "顶出限位块检查有无漏设计",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "垃圾钉、顶出限位块螺丝未紧固", grade: "B", deduction: 3 },
//       { issue_item: "模具回位方式与式样书不符", grade: "B", deduction: 3 },
//       { issue_item: "模具强回位螺纹尺寸与式样书不符", grade: "B", deduction: 3 },
//       { issue_item: "顶出限位块检查有漏设计", grade: "C", deduction: 1 },
//     ]
//   },
//   {
//     inspection_key: "auto_parting_surface",
//     inspection_item: "分型面",
//     inspection_criteria: [
//       "虎口耐模板红丹80%，无过盈",
//       "所有螺钉安装后矮于平面1mm以上",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "虎口耐模板红丹不符合80%，有过盈", grade: "B", deduction: 3 },
//       { issue_item: "有螺钉安装后没有矮于平面1mm以上", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_polishing",
//     inspection_item: "抛光",
//     inspection_criteria: [
//       "流道抛光",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "流道未抛光", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_grinding_matching_check_item",
//     inspection_item: "研配点检项",
//     inspection_criteria: [
//       "各压线板为5mm厚铁板（热流道、限位开关等走线）",
//       "集水器、油缸等跨动静模两部分是要有让位或垫高块。",
//       "丝堵材质符合客户要求（蒸汽模具丝堵要不锈钢材质）",
//       "成型面异形的浇口套要有止转",
//       "多腔的模具要刻腔号",
//       "所有镶件都要有排气，含镶针.没有排气的由项目经理确认",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "压线板非5mm厚铁板", grade: "C", deduction: 1 },
//       { issue_item: "集水器、油缸等跨动静模两部分没有让位或垫高块。", grade: "A", deduction: 5 },
//       { issue_item: "丝堵材质不符合客户要求", grade: "A", deduction: 5 },
//       { issue_item: "成型面异形的浇口套没有止转", grade: "A", deduction: 5 },
//       { issue_item: "多腔的模具没有刻腔号", grade: "B", deduction: 3 },
//       { issue_item: "有镶件无排气，或未含镶针，或没有排气的未经项目经理确认", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_three_plate_mold",
//     inspection_item: "三板模",
//     inspection_criteria: [
//       "三板模锁模块螺丝要锁在B0和A1上",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "三板模锁模块螺丝没有锁在B0和A1上", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_ejector_plate_preload_screw",
//     inspection_item: "推出板预压螺钉",
//     inspection_criteria: [
//       "弹簧复位的推出板应设计预压螺钉（19.7.16增加）",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "弹簧复位的推出板未设计预压螺钉", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_mold_weighing",
//     inspection_item: "模具称重",
//     inspection_criteria: [
//       "T1拆检时模具称重，重量记录到EX本表",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "重量未记录到EX本表", grade: "B", deduction: 3 },
//     ]
//   },
//   {
//     inspection_key: "auto_mold_engraving",
//     inspection_item: "模具刻印",
//     inspection_criteria: [
//       "分型面的零部件不允许有手工刻印的标记，必须是采用设备加工标识（数控加工、刻字机刻印、腐蚀加工）",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "分型面的零部件有手工刻印非采用设备加工标识", grade: "C", deduction: 1 },
//     ]
//   },
//   {
//     inspection_key: "auto_oil_cylinder_motion_interference",
//     inspection_item: "油缸运动干涉",
//     inspection_criteria: [
//       "油缸与AO板重合位置A0板要有避空，确保合模不干涉油缸。",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "油缸与AO板重合位置A0板没有避空", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_mold_block_lifting_block_motion_interference",
//     inspection_item: "模具垫块、吊模块运动干涉",
//     inspection_criteria: [
//       "模具垫块、吊模块与运动模板重合位置要设计避空，确保模具垫块、吊模块运动不与模板干涉",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "模具垫块、吊模块与运动模板重合位置没有避空", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_hot_runner_exposed_wiring_protection",
//     inspection_item: "热流道外漏接线防护",
//     inspection_criteria: [
//       "热流道有关外漏接线要增加外层防护保护（缠绕塑胶防护套）",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "热流道有关外漏接线没有外层防护保护", grade: "A", deduction: 5 },
//     ]
//   },
//   {
//     inspection_key: "auto_texture_grain",
//     inspection_item: "皮纹",
//     inspection_criteria: [
//       "皮纹范围是否划线标识加工，有无漏抛光及抛光不合格（尤其是边缘部位）",
//       "皮纹件做酸蚀检测零件有无材质线及加工痕迹",
//     ],
//     category_level_1: "拆模检验",
//     category_level_2: "汽车",
//     options: [
//       { issue_item: "皮纹范围没有划线标识加工，或有漏抛光、抛光不合格", grade: "A", deduction: 5 },
//       { issue_item: "皮纹件做酸蚀检测零件有材质线及加工痕迹", grade: "A", deduction: 5 },
//     ]
//   },
  {
    inspection_key: "auto_clamp_peripheral",
    inspection_item: "合模外围",
    inspection_criteria: [
      "模架天地侧起吊吊环能拧到底，吊环标识正确。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模架天地侧起吊吊环不能拧到底", grade: "A", deduction: 5 },
      { issue_item: "吊环标识不正确", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_2",
    inspection_item: "合模外围",
    inspection_criteria: [
      "天地侧起吊吊环旋转轨迹内，不能干涉周边零件。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "天地侧起吊吊环旋转轨迹影响周边零件", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_3",
    inspection_item: "合模外围",
    inspection_criteria: [
      "模具整模、半模、单板起吊平衡（如果进行吊装平衡测试要拍照留底避免后期重复工作）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具整模、半模、单板起吊不平衡", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_4",
    inspection_item: "合模外围",
    inspection_criteria: [
      "大小导套侧面止付螺丝要拧到底",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "大小导套侧面止付螺丝不能拧到底", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_5",
    inspection_item: "合模外围",
    inspection_criteria: [
      "大导套要有排气槽",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "大导套要没有排气槽", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_6",
    inspection_item: "合模外围",
    inspection_criteria: [
      "模架上水路、油路、气路等刻印标识齐全。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模架上水路、油路、气路等刻印标识不齐全", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_7",
    inspection_item: "合模外围",
    inspection_criteria: [
      "水路接口（含集水器、分水器）符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "水路接口不符合式样书", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_8",
    inspection_item: "合模外围",
    inspection_criteria: [
      "天侧及操作侧无进出水口，放在非操作侧，如有违背需反馈确认。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "油缸杆没有加\"U\"止转块", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_9",
    inspection_item: "合模外围",
    inspection_criteria: [
      "油缸杆要加\"U\"止转块",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "芯轴压板和模板不同高", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_clamp_peripheral_10",
    inspection_item: "合模外围",
    inspection_criteria: [
      "芯轴压板和模板同高，有隔热板的和隔热板同高。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "隔热板不同高", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_after_mold_split",
    inspection_item: "分模后",
    inspection_criteria: [
      "对所有水路，进行水流量测试（制作水流量报告，如有疑问同项目确认）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "水路测试问题", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_after_mold_split_2",
    inspection_item: "分模后",
    inspection_criteria: [
      "有外置弹簧的需要加保护套",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "有外置弹簧的没有加保护套", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_after_mold_split_3",
    inspection_item: "分模后",
    inspection_criteria: [
      "天侧滑块要有限位机构",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "天侧滑块没有限位机构", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_after_mold_split_4",
    inspection_item: "分模后",
    inspection_criteria: [
      "滑块上斜导柱孔孔入口部倒R3",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑块上斜导柱孔孔入口部不符合倒R3", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_after_mold_split_5",
    inspection_item: "分模后",
    inspection_criteria: [
      "模具型芯有热流道浇口刻印（G1、G2、………)",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具型芯没有热流道浇口刻印", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_after_mold_split_6",
    inspection_item: "分模后",
    inspection_criteria: [
      "分型面研配痕迹均匀，无发黑发亮的研配点，无磕碰划伤。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "分型面研配痕迹不均匀", grade: "B", deduction: 3 },
      { issue_item: "有发黑发亮的研配点", grade: "B", deduction: 3 },
      { issue_item: "有磕碰划伤", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_after_mold_split_7",
    inspection_item: "分模后",
    inspection_criteria: [
      "插穿面无明显研配黑点",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "插穿面有明显研配黑点", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "滑块前置弹簧裸露段大于直径的3倍时要加导向杆",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑块前置弹簧裸露段大于直径的3倍时没有加导向杆", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_2",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "滑块各配合面均匀，无研配黑点，配合尖角处无倒角。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑块各配合面不均匀，有研配黑点，配合尖角处无倒角", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_3",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "滑块下耐磨板无起刺、背面耐磨板配合均匀，斜度吻合。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑块下耐磨板有起刺、背面耐磨板配合不均匀，斜度不吻合", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_4",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "滑块与导轨的配合间隙单边0.02",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑块与导轨的配合间隙单边不符合0.02", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_5",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "滑块与压板间隙0.03mm，滑块压板紧固后，滑块动作流畅、不晃动。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑块与压板间隙不满足0.03mm，滑块压板紧固后，滑块动作不流畅、有晃动。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_6",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "滑动面运动摩擦痕迹均匀，无局部黑点。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑动面运动摩擦痕迹不均匀，有局部黑点", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_7",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "侧抽研配摩擦面无起刺发黑发亮现象",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "侧抽研配摩擦面有起刺发黑发亮现象", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_8",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "斜顶油槽范围覆盖所有滑动段（方顶杆 原顶杆除外）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "斜顶油槽范围未覆盖所有滑动段", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_9",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "斜顶头部以下和方顶杆导向部分磨避空单边0.05mm",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "斜顶头部以下和方顶杆导向部分磨避空单边不满足0.05mm", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_10",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "隔热板上有拆卸零件的螺钉头避空。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "隔热板上有拆卸零件的螺钉头没有避空。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_11",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "垃圾钉全数对碰痕迹清晰。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "垃圾钉对碰痕迹不清晰。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_12",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "支撑柱与方铁高度在公差在+0.05至+0.15间",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "支撑柱与方铁高度在公差不在+0.05至+0.15间", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_13",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "各销钉松紧适中，没有过松或起刺现象。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "各销钉松紧有过松或起刺现象。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_14",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "顶出块顶杆有止转机构",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "顶出块顶杆没有止转机构", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_15",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "复位杆下有树脂弹簧的，复位杆要有3mm活动空间（客户特殊要求不要树脂弹簧除外）不要树脂弹簧的复位杆挂台要和B2板平",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "复位杆下有树脂弹簧的，复位杆要没有3mm活动空间；不要树脂弹簧的复位杆挂台没有和B2板平", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_16",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "隔水板方向安装正确，在模板上有方向标识，紧配无松动、无缺漏（抽检隔水片）。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "隔水板方向安装不正确，在模板上没有方向标识，紧配有松动、有缺漏", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_17",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "需加油槽的部件、油槽深度0.3~0.5mm之间，油槽不得与边及孔相通。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "需加油槽的部件、油槽深度不在0.3~0.5mm之间，油槽与边及孔相通", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_18",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "内分型面及镶件有排气槽的，要有排气引出孔或引出槽与外界通气。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "内分型面及镶件有排气槽的，没有排气引出孔或引出槽与外界通气", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_19",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "各零部件清晰的刻有模具编号和零件编号，零件号和模型一致。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "零部件未清晰的刻有模具编号和零件编号，零件号和模型不一致", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_20",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "模具外观研配面无明显的砂轮痕迹及划伤。砂轮痕迹用320#油石顺平，",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具外观研配面有明显的砂轮痕迹及划伤。砂轮痕迹未用320#油石顺平", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_21",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "模具所有零部件不得有任何烧焊痕迹",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具有零部件有烧焊痕迹", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_22",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "各工件无垫铜/铁皮现象",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "工件有垫铜/铁皮现象", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_dismantling_process_23",
    inspection_item: "拆模过程中",
    inspection_criteria: [
      "要求氮化的工件均已氮化",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "要求氮化的工件未氮化", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hot_runner",
    inspection_item: "热流道",
    inspection_criteria: [
      `以下项目按照式样书检验确认:
热流道样式、
接线插座及底座型号、    
接线符合式样书、
电磁阀电压、
电磁阀接线方式、
热流道接线盒上要有对应的接线小标牌(见客户标准)`,
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "热流道样式、接线插座及底座型号、接线、电磁阀电压、电磁阀接线方式与式样书不符，或热流道接线盒上没有对应的接线小标牌", grade: "B", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hot_runner_2",
    inspection_item: "热流道",
    inspection_criteria: [
      "热流道接线盒是否沉入模板或加保护块",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "热流道接线盒没有沉入模板，未加保护块", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_hot_runner_3",
    inspection_item: "热流道",
    inspection_criteria: [
      "热流道嘴头与模具浇口处直径配合符合设计要求，无漏胶现象.",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "热流道嘴头与模具浇口处直径配合不符合设计要求，有漏胶现象", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_hot_runner_4",
    inspection_item: "热流道",
    inspection_criteria: [
      "热电偶型号符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "热电偶型号与式样书不符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_hot_runner_5",
    inspection_item: "热流道",
    inspection_criteria: [
      "热流道观察孔、排水槽是否需要并加工",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "热流道观察孔、排水槽未加工", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_hot_runner_6",
    inspection_item: "热流道",
    inspection_criteria: [
      "热流道水路，油路是否有出厂用水嘴，是否需要连接到集水器或集油器上（需确认）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "热流道水路，油路没有出厂用水嘴，需要但没有连接到集水器或集油器上", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_lift_safety",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "所有模具四面都要有吊环孔（客户特殊要求除外）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具四面没有吊环孔", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_lift_safety_2",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "点检A1 B4 板正面是否有设计吊装吊环.",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "点检A1 B4 板正面没有设计吊装吊环", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_lift_safety_3",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "前后模分型面是否有半模翻模吊环（特殊情况同设计确认）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "前后模分型面没有半模翻模吊环", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_lift_safety_4",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "模具是否需要吊模块，吊模块上吊孔标识已做。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "吊模块上吊孔标识未做", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_lift_safety_5",
    inspection_item: "起吊安全",
    inspection_criteria: [
      "模芯等工件吊装螺纹深度大于2.5D，吊环底孔无超差。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模芯等工件吊装螺纹深度未大于2.5D，吊环底孔超差", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_design_check_item",
    inspection_item: "设计点检项",
    inspection_criteria: [
      "所有模具都要有精定位（客户特殊要求除外）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具没有精定位", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_design_check_item_2",
    inspection_item: "设计点检项",
    inspection_criteria: [
      "异形工件要有二次加工基准边",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "异形工件没有二次加工基准边", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_return_pin",
    inspection_item: "复位杆",
    inspection_criteria: [
      "复位杆与其挡块对碰面积大于复位杆截面积的50%。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "复位杆与其挡块对碰面积没有大于复位杆截面积的50%", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_return_pin_2",
    inspection_item: "复位杆",
    inspection_criteria: [
      "复位杆挡块硬度HRC48~52度（需检测硬度拍照）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "复位杆挡块硬度不满足HRC48~52度", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_return_pin_3",
    inspection_item: "复位杆",
    inspection_criteria: [
      "复位杆孔是否按标准避空单边0.2~0.5mm。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "复位杆孔没有按标准避空单边0.2~0.5mm。", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_return_pin_4",
    inspection_item: "复位杆",
    inspection_criteria: [
      "有复位弹簧的模具，弹簧要顶在推出固定板上，要设计有预压螺丝。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "有复位弹簧的模具，弹簧没有顶在推出固定板上，没有设计预压螺丝", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_main_guide_pin",
    inspection_item: "大导柱",
    inspection_criteria: [
      "大导柱、导套样式及材料符合式样书（需检测硬度拍照）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "大导柱、导套样式及材料与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_main_guide_pin_2",
    inspection_item: "大导柱",
    inspection_criteria: [
      "大导柱与安装孔要紧配",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "大导柱与安装孔不紧配", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_support_bushing",
    inspection_item: "中托司",
    inspection_criteria: [
      "中托司导套与B2板紧配，与B3板滑配",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "中托司导套与B2板不紧配，与B3板无滑配", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_support_bushing_2",
    inspection_item: "中托司",
    inspection_criteria: [
      "中托司固定在B4板时，要紧配",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "中托司固定在B4板时，没有紧配", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_support_bushing_3",
    inspection_item: "中托司",
    inspection_criteria: [
      "中托司要有润滑结构",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "中托司没有润滑结构", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_water_channel",
    inspection_item: "水路",
    inspection_criteria: [
      "水嘴沉孔符合标准（没有特殊要求情况下，默认φ30*25深，两个孔中心小于35mm的做通）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "水嘴沉孔不符合标准", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_water_channel_2",
    inspection_item: "水路",
    inspection_criteria: [
      "密封圈槽符合标准，使用的密封圈槽与密封圈规格向对应。（密封圈选用是否符合要求，耐高温或普通）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "密封圈槽不符合标准", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_slide_block",
    inspection_item: "滑块",
    inspection_criteria: [
      "斜导柱无松动、无起刺，长度不可超过大导柱，斜度与斜导柱孔吻合。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "斜导柱无松动、无起刺，长度超过大导柱，斜度与斜导柱孔不吻合。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_slide_block_2",
    inspection_item: "滑块",
    inspection_criteria: [
      "滑块压板、导向块、耐磨板、斜导柱材料符合式样书，硬度符合标准。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "滑块压板、导向块、耐磨板、斜导柱材料与式样书不符，硬度不符合标准。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_insulation_board",
    inspection_item: "隔热板",
    inspection_criteria: [
      "隔热板距码模板边的距离要让过倒角，但最大不得超过10mm",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "隔热板距码模板边的距离没有让过倒角，或超过10mm", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_insulation_board_2",
    inspection_item: "隔热板",
    inspection_criteria: [
      "模具外部隔热板已安装，固定螺钉齐全并紧固",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具外部隔热板未安装，固定螺钉不齐全或不紧固", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_mold_clamping",
    inspection_item: "码模",
    inspection_criteria: [
      "压肩形式符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "压肩形式与式样书不符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_clamping_2",
    inspection_item: "码模",
    inspection_criteria: [
      "码模厚度符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "码模厚度与式样书不符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_pouring_system",
    inspection_item: "浇注",
    inspection_criteria: [
      "定位圈直径符合式样书：（记录）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "定位圈直径与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_pouring_system_2",
    inspection_item: "浇注",
    inspection_criteria: [
      "模具浇口套球头表面是否完好 SR尺寸符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具浇口套球头表面不完好 SR尺寸与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_pouring_system_3",
    inspection_item: "浇注",
    inspection_criteria: [
      "机嘴处主浇口小端直径符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "机嘴处主浇口小端直径与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_nameplate",
    inspection_item: "标牌",
    inspection_criteria: [
      "各标牌槽位置、大小要符合客户标准，标牌大小要和槽一致。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "各标牌槽位置、大小不符合客户标准。标牌大小要和槽不一致", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_nameplate_2",
    inspection_item: "标牌",
    inspection_criteria: [
      "标牌种类、数量符合客户标准，标牌内容符合图纸；水路标牌上进出水标识的位置和模具完全相符。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "标牌种类、数量不符合客户标准，标牌内容与图纸不符；水路标牌上进出水标识的位置和模具不相符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_hardness",
    inspection_item: "硬度",
    inspection_criteria: [
      "冷流道浇口硬度HRC50~54度",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "冷流道浇口硬度不满足HRC50~54度", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hardness_2",
    inspection_item: "硬度",
    inspection_criteria: [
      "需氮化的斜顶杆已做氮化处理",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "需氮化的斜顶杆未做氮化处理", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hardness_3",
    inspection_item: "硬度",
    inspection_criteria: [
      "模具型腔、型芯、滑动部件硬度符合设计要求（检测硬度拍照留底）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具型腔、型芯、滑动部件硬度不符合设计要求", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hardness_4",
    inspection_item: "硬度",
    inspection_criteria: [
      "型腔、型芯、滑块材料符合要求，查看材质证明",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "型腔、型芯、滑块材料不符合要求，无材质证明", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hardness_5",
    inspection_item: "硬度",
    inspection_criteria: [
      // "承压板硬度符合式样书",
      "精定位、楔契块、导滑块/导轨材质与硬度的检测确认（拍照）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "精定位、楔契块、导滑块/导轨材质与硬度的检测不通过", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mark",
    inspection_item: "标识",
    inspection_criteria: [
      "模板上相关产品信息刻印符合模型要求（可换版本号应对照可换说明书检查编号）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模板上相关产品信息刻印不符合模型要求", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mark_2",
    inspection_item: "标识",
    inspection_criteria: [
      "模板顶出、重量、警示、装配编号、模具编号刻印符合要求",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模板顶出、重量、警示、装配编号、模具编号刻印不符合要求", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mark_3",
    inspection_item: "标识",
    inspection_criteria: [
      "各类标识排查无遗漏",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "各类标识排查有遗漏", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_mark_4",
    inspection_item: "标识",
    inspection_criteria: [
      "各钢印字码臃肿已修平",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "各钢印字码臃肿未修平", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_chamfer",
    inspection_item: "倒角",
    inspection_criteria: [
      "撬模角无缺漏，尺寸按30*30*5设计（客户特殊要求除外）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "撬模角有缺漏，尺寸未按30*30*5设计", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_chamfer_2",
    inspection_item: "倒角",
    inspection_criteria: [
      "模架基准倒角正确；",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模架基准倒角不正确", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_chamfer_3",
    inspection_item: "倒角",
    inspection_criteria: [
      "模架所有非封料棱边均倒C2~C3角，无过大或过小的现象",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模架非封料棱边未倒C2~C3角，有过大或过小的现象", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_chamfer_4",
    inspection_item: "倒角",
    inspection_criteria: [
      "各非成型孔、边倒c1~c2角（参考倒角排查表）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "各钢印各非成型孔、边未倒c1~c2角", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_counter",
    inspection_item: "计数器",
    inspection_criteria: [
      "计数器槽形状、尺寸符合模型，并有计数器调节撞块。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "计数器槽形状、尺寸不符合模型，没有计数器调节撞块。", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_counter_2",
    inspection_item: "计数器",
    inspection_criteria: [
      "计数器型号符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "计数器型号与式样书不符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_limit_switch",
    inspection_item: "行程开关",
    inspection_criteria: [
      "限位开关型号/数量符合设计要求，限位开关出线口安装防护帽",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "限位开关型号/数量不符合设计要求，限位开关出线口未安装防护帽", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_limit_switch_2",
    inspection_item: "行程开关",
    inspection_criteria: [
      "行程开关是否需要沉入模板",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "行程开关需要但未沉入模板", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_limit_switch_3",
    inspection_item: "行程开关",
    inspection_criteria: [
      "限位开关插座及接线盒符合标准，限位开关跨板线路必须用快拆的结构",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "限位开关插座及接线盒不符合标准，限位开关跨板线路没有用快拆的结构", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hydraulic_cylinder",
    inspection_item: "油缸",
    inspection_criteria: [
      "油路接口（含热流道油路）型号符合式样书：",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "油路接口（含热流道油路）型号与式样书不符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_hydraulic_cylinder_2",
    inspection_item: "油缸",
    inspection_criteria: [
      "油缸品牌符合式样书。油缸铁屑汽车模具T3后T4前检查结束。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "油缸品牌与式样书不符", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_lubrication",
    inspection_item: "润滑",
    inspection_criteria: [
      "铜加碳的工件，碳点面积不少于所在平面面积的25%，碳点不能矮于铜面，或缺碳现象。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "铜加碳的工件，碳点面积少于所在平面面积的25%，或碳点矮于铜面，或有缺碳现象", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_angled_lifter",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶与型芯研配配间隙符合标准",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "斜顶与型芯研配配间隙不符合标准", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_angled_lifter_2",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶万向座的铜片要有碳润滑",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "斜顶万向座的铜片没有碳润滑", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_angled_lifter_3",
    inspection_item: "斜顶",
    inspection_criteria: [
      "斜顶研配后，分型面与斜顶平，斜顶周圈刚刚粘丹，斜顶尾部用手能推出。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "斜顶研配后，分型面与斜顶不平，或斜顶周圈没有刚刚粘丹，或斜顶尾部不能用手推出", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_ejection",
    inspection_item: "顶出",
    inspection_criteria: [
      "垃圾钉、顶出限位块螺丝已紧固",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "垃圾钉、顶出限位块螺丝未紧固", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_ejection_2",
    inspection_item: "顶出",
    inspection_criteria: [
      "模具回位方式符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具回位方式与式样书不符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_ejection_3",
    inspection_item: "顶出",
    inspection_criteria: [
      "模具强回位螺纹尺寸符合式样书",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具强回位螺纹尺寸与式样书不符", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_ejection_4",
    inspection_item: "顶出",
    inspection_criteria: [
      "顶出限位块检查有无漏设计",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "顶出限位块检查有漏设计", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_parting_surface",
    inspection_item: "分型面",
    inspection_criteria: [
      "虎口耐模板红丹80%，无过盈",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "虎口耐模板红丹不符合80%，有过盈", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_parting_surface_2",
    inspection_item: "分型面",
    inspection_criteria: [
      "所有螺钉安装后矮于平面1mm以上",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "有螺钉安装后没有矮于平面1mm以上", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_polishing",
    inspection_item: "抛光",
    inspection_criteria: [
      "流道抛光",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "流道未抛光", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_grinding_matching_check_item",
    inspection_item: "研配点检项",
    inspection_criteria: [
      "各压线板为5mm厚铁板（热流道、限位开关等走线）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "压线板非5mm厚铁板", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_grinding_matching_check_item_2",
    inspection_item: "研配点检项",
    inspection_criteria: [
      "集水器、油缸等跨动静模两部分是要有让位或垫高块。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "集水器、油缸等跨动静模两部分没有让位或垫高块。", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_grinding_matching_check_item_3",
    inspection_item: "研配点检项",
    inspection_criteria: [
      "丝堵材质符合客户要求（蒸汽模具丝堵要不锈钢材质）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "丝堵材质不符合客户要求", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_grinding_matching_check_item_4",
    inspection_item: "研配点检项",
    inspection_criteria: [
      "成型面异形的浇口套要有止转",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "成型面异形的浇口套没有止转", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_grinding_matching_check_item_5",
    inspection_item: "研配点检项",
    inspection_criteria: [
      "多腔的模具要刻腔号",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "多腔的模具没有刻腔号", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_grinding_matching_check_item_6",
    inspection_item: "研配点检项",
    inspection_criteria: [
      "所有镶件都要有排气，含镶针.没有排气的由项目经理确认",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "有镶件无排气，或未含镶针，或没有排气的未经项目经理确认", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_three_plate_mold",
    inspection_item: "三板模",
    inspection_criteria: [
      "三板模锁模块螺丝要锁在B0和A1上",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "三板模锁模块螺丝没有锁在B0和A1上", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_ejector_plate_preload_screw",
    inspection_item: "推出板预压螺钉",
    inspection_criteria: [
      "弹簧复位的推出板应设计预压螺钉（19.7.16增加）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "弹簧复位的推出板未设计预压螺钉", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_weighing",
    inspection_item: "模具称重",
    inspection_criteria: [
      "T1拆检时模具称重，重量记录到EX本表",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "重量未记录到EX本表", grade: "B", deduction: 3 },
    ]
  },
  {
    inspection_key: "auto_mold_engraving",
    inspection_item: "模具刻印",
    inspection_criteria: [
      "分型面的零部件不允许有手工刻印的标记，必须是采用设备加工标识（数控加工、刻字机刻印、腐蚀加工）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "分型面的零部件有手工刻印非采用设备加工标识", grade: "C", deduction: 1 },
    ]
  },
  {
    inspection_key: "auto_oil_cylinder_motion_interference",
    inspection_item: "油缸运动干涉",
    inspection_criteria: [
      "油缸与AO板重合位置A0板要有避空，确保合模不干涉油缸。",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "油缸与AO板重合位置A0板没有避空", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_mold_block_lifting_block_motion_interference",
    inspection_item: "模具垫块、吊模块运动干涉",
    inspection_criteria: [
      "模具垫块、吊模块与运动模板重合位置要设计避空，确保模具垫块、吊模块运动不与模板干涉",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "模具垫块、吊模块与运动模板重合位置没有避空", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_hot_runner_exposed_wiring_protection",
    inspection_item: "热流道外漏接线防护",
    inspection_criteria: [
      "热流道有关外漏接线要增加外层防护保护（缠绕塑胶防护套）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "热流道有关外漏接线没有外层防护保护", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_texture_grain",
    inspection_item: "皮纹",
    inspection_criteria: [
      "皮纹范围是否划线标识加工，有无漏抛光及抛光不合格（尤其是边缘部位）",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "皮纹范围没有划线标识加工，或有漏抛光、抛光不合格", grade: "A", deduction: 5 },
    ]
  },
  {
    inspection_key: "auto_texture_grain_2",
    inspection_item: "皮纹",
    inspection_criteria: [
      "皮纹件做酸蚀检测零件有无材质线及加工痕迹",
    ],
    category_level_1: "拆模检验",
    category_level_2: "汽车",
    options: [
      { issue_item: "皮纹件做酸蚀检测零件有材质线及加工痕迹", grade: "A", deduction: 5 },
    ]
  },

]

export const hisenseAutoMoldDismantlingInspectionItems = HISENSE_AUTO_MOLD_DISMANTLING_TRIAL_ISSUE_TEMPLATE.map(item => {
  return {
    ...item,
    deduction: null,
    grade: null,
    id: null,
    is_old_issue: false,
    issue_code: null,
    issue_description: null,
    issue_images: [],
    issue_files: [],
    issue_item: null,
    issue_type: "disassembly_insp",
    judgement: null,
    judgement_by: null,
    judgement_at: null,
    trial_session_id: null,
  }
})

export const issueItem = {
  id: null,
  trial_session_id: null,
  judgement: null,
  judgement_by: null,
  judgement_at: null,
  issue_item: null,
  issue_description: null,
  issue_images: [],
  issue_files: [],
  inspection_key: null,
  inspection_item: null,
  inspection_criteria: null,
  category_level_1: null,
  category_level_2: null,
  options: null,
  grade: null,
  deduction: null,
  mold_no: null,
  trial_version: null,
}







// 科龙模板数据

export const KL_MOLD_TRIAL_ISSUE_TEMPLATE = [
  {
    inspection_key: "kl_mold_appearance_1",
    inspection_item: "模具外观",
    inspection_criteria: ["模具油缸、顶针板有限位开关"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "油缸、顶针板无行程开关", grade: "A+", deduction: 10 },
      { issue_item: "油缸、顶针板无设计行程开关或设计不合理（未设计或未加工）", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_2",
    inspection_item: "模具外观",
    inspection_criteria: ["模具顶出导向及定位锁安装齐全"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "弹簧、边锁不齐", grade: "C", deduction: 2 },
    ]
  },
  {
    inspection_key: "kl_mold_appearance_3",
    inspection_item: "安全防护",
    inspection_criteria: ["模具安全防护装置安装齐全，无隐患"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "弹簧保护套、防护块未装", grade: "A+", deduction: 10 }
      // { issue_item: "弹簧保护套、防护块未装", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_4",
    inspection_item: "安全防护",
    inspection_criteria: ["模具支撑、紧固可靠"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "硬块、螺钉、模脚不齐", grade: "A+", deduction: 10 },
      // { issue_item: "硬块、螺钉、模脚不齐", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_5",
    inspection_item: "安全防护",
    inspection_criteria: ["模脚设计无干涉，无叉模、倾倒安全隐患"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模脚设计不合理，有倾倒安全隐患", grade: "A+", deduction: 10 },
      // { issue_item: "模脚设计不合理，有倾倒安全隐患", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_6",
    inspection_item: "模具外观",
    inspection_criteria: ["模具外观字码符合客户标准"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模胚字码遗漏或错误", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_7",
    inspection_item: "模具外观",
    inspection_criteria: ["模具计数器已安装并工作正常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "计数器未安装或失效", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_8",
    inspection_item: "模具外观",
    inspection_criteria: ["电子开关工作正常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行程开关失效或装反", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_9",
    inspection_item: "模具外观",
    inspection_criteria: ["铭牌及计数器槽按照客户标准加工"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具铭牌、计数器槽未加工（未设计或未加工）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_10",
    inspection_item: "模具外观",
    inspection_criteria: ["日期章无松动、调到指定天/月"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品日期章松动/未调到试模当天/月", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_11",
    inspection_item: "模具外观",
    inspection_criteria: ["水管无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "软水管连接干涉", grade: "A", deduction: 5 },
      { issue_item: "软水管未按设计标准装配连接", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_appearance_12",
    inspection_item: "模具外观",
    inspection_criteria: ["油管无干涉，油管插头无拔插干涉问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "油管干涉", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_lifting_1",
    inspection_item: "模具吊装",
    inspection_criteria: ["模具起吊平衡，倾斜角度5°以内"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "吊装不平衡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_lifting_2",
    inspection_item: "安全防护",
    inspection_criteria: ["吊环能够拧到底，与周边无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "吊环、吊模方安装干涉", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_lifting_3",
    inspection_item: "模具吊装",
    inspection_criteria: ["模具码模槽正确，与其他结构无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具码模阻挡/干涉", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_lifting_4",
    inspection_item: "模具吊装",
    inspection_criteria: ["模板厚度符合客户标准"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模板厚度与客户标准不符", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_lifting_5",
    inspection_item: "模具吊装",
    inspection_criteria: ["模具定位环尺寸满足本厂试模要求"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "定位环不匹配", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_opening_closing_1",
    inspection_item: "模具开合",
    inspection_criteria: ["20%-60%的速度，40%-90%的压力开合模无异常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具导向不顺畅、擦烧，开合模异响", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_opening_closing_2",
    inspection_item: "模具开合",
    inspection_criteria: ["行位滑动顺畅，配合松紧适度"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位滑动动作不顺畅", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_opening_closing_3",
    inspection_item: "模具开合",
    inspection_criteria: ["抽芯机构稳定，定位可靠，无异响"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "抽芯机构动作不顺畅", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_opening_closing_4",
    inspection_item: "模具开合",
    inspection_criteria: ["斜顶/外部拉钩动作正常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "斜顶/外部拉钩断裂或拉钩失效", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_opening_closing_5",
    inspection_item: "模具开合",
    inspection_criteria: ["模具导套有开排气，配合顺畅"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具导柱吸真空", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_control_1",
    inspection_item: "热流道控制",
    inspection_criteria: ["热咀加热20分钟内全部达到预定值"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "热咀不加热、升温慢", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_control_2",
    inspection_item: "热流道控制",
    inspection_criteria: ["热咀温度变化范围±5℃以内"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "温控不稳定，温度不统一", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_control_3",
    inspection_item: "热流道控制",
    inspection_criteria: ["热咀无黑纹"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "浇口黑纹/黄纹", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_control_4",
    inspection_item: "热流道控制",
    inspection_criteria: ["热咀接线方法和插头符合客户标准"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "热咀接驳不正确", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_control_5",
    inspection_item: "热流道控制",
    inspection_criteria: ["热流道铭牌安装正常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "热流道铭牌未安装", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_control_6",
    inspection_item: "热流道控制",
    inspection_criteria: ["热咀插头安装方便与周边无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "热流道插头插拔困难/干涉", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_1",
    inspection_item: "热流道动作",
    inspection_criteria: ["模具未射胶前动作顺畅无异常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "阀针动作卡滞", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_2",
    inspection_item: "热流道动作",
    inspection_criteria: ["模具封针压力足够，封胶良好"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "阀针封胶不良、披锋", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_3",
    inspection_item: "热流道动作",
    inspection_criteria: ["热咀气路接驳方便"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "气源/信号线接驳干涉", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_4",
    inspection_item: "热流道动作",
    inspection_criteria: ["热咀气路无漏气问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "气阀漏气", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_5",
    inspection_item: "热流道动作",
    inspection_criteria: ["热咀冷却套研配紧密无缝隙"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "浇口套披锋", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_6",
    inspection_item: "热流道动作",
    inspection_criteria: ["热咀浇口套胶位正常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "热咀浇口套胶位嘴头过高或漏开流道", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_7",
    inspection_item: "热流道动作",
    inspection_criteria: ["热咀阀针冷却良好，无粘附现象"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "热咀冷却差，阀针粘胶", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_hot_runner_action_8",
    inspection_item: "热流道动作",
    inspection_criteria: ["热流道温度控制稳定，无流涎"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "浇注口流涎", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_cold_runner_1",
    inspection_item: "冷流道模具",
    inspection_criteria: ["流道研配良好末端排气通畅"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "流道末端未开排气", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_cold_runner_2",
    inspection_item: "冷流道模具",
    inspection_criteria: ["流道裁切便捷，切口美观"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "流道裁切困难", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_cold_runner_3",
    inspection_item: "冷流道模具",
    inspection_criteria: ["流道顶出顺畅满足自动化生产"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "流道不能自动掉、弹飞、顶翻", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_cold_runner_4",
    inspection_item: "冷流道模具",
    inspection_criteria: ["流道冷却正常无顶穿"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "流道冷却不良顶穿", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_cold_runner_5",
    inspection_item: "冷流道模具",
    inspection_criteria: ["流道无机加工纹，无粘模现象"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "流道粘模、省模不良", grade: "A", deduction: 5 },
      { issue_item: "流道粘模、出模角度小", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_cold_runner_6",
    inspection_item: "冷流道模具",
    inspection_criteria: ["多冷流道有要求连接的连接正常"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "多个冷流道之间不能正常连接", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_cold_runner_7",
    inspection_item: "冷流道模具",
    inspection_criteria: ["冷流道浇口正常连通产品"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "冷流道浇口未开通", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_1",
    inspection_item: "模具动作",
    inspection_criteria: ["行位有设计限位并已安装正确"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位限位不准确、无限位", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_2",
    inspection_item: "模具动作",
    inspection_criteria: ["行位行程量不小于产品倒扣量"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位行程不够，干涉产品脱模", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_3",
    inspection_item: "模具动作",
    inspection_criteria: ["行位动作顺畅，无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位动作卡滞、干涉", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_4",
    inspection_item: "模具动作",
    inspection_criteria: ["前模抽芯有设计限位并已安装正确"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "前模抽芯行程不准确、无限位", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_5",
    inspection_item: "模具动作",
    inspection_criteria: ["后模抽芯有设计限位并已安装正确"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "后模抽芯行程不准确、无限位", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_6",
    inspection_item: "模具动作",
    inspection_criteria: ["后模行位有设计限位并已安装正确"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "后模行位行程不准、无限位", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_7",
    inspection_item: "模具动作",
    inspection_criteria: ["前模抽芯动作顺畅，无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "前模抽芯卡滞、干涉", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_8",
    inspection_item: "模具动作",
    inspection_criteria: ["后模抽芯动作顺畅，无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "后模抽芯卡滞、干涉", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_9",
    inspection_item: "模具动作",
    inspection_criteria: ["模具开合动作符合设计要求"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具开合顺序错误、合模时大导柱晚于斜导柱进入导向位置", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_action_10",
    inspection_item: "模具动作",
    inspection_criteria: ["模具弹块组配顺畅，动作稳定"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "弹块动作卡滞", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_1",
    inspection_item: "模具顶出",
    inspection_criteria: ["20%-60%的速度，40%-60%的压力回退无异响，回位顺畅"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶针/斜顶顶出/回退不顺畅/异响", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_2",
    inspection_item: "模具顶出",
    inspection_criteria: ["20%-60%的速度，40%-60%的压力顶出无异响，顶出顺畅"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶针/斜顶烧死不能顶出/回退", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_3",
    inspection_item: "模具顶出",
    inspection_criteria: ["顶针板回退顺畅到设定位置"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶针回退高出胶位面不到底", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_4",
    inspection_item: "模具顶出",
    inspection_criteria: ["顶针板顶出行程足够，满足取件要求"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶出行程不足", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_5",
    inspection_item: "模具顶出",
    inspection_criteria: ["注塑机顶出中心与模具中心一致"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "中托司未装", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_6",
    inspection_item: "模具顶出",
    inspection_criteria: ["模具顶棍安装便利，无安全隐患"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶棍安装不方便/模具KO孔与机台不符", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_7",
    inspection_item: "模具顶出",
    inspection_criteria: ["模具顶针强度足够，研配良好"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具顶针断裂", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_ejection_8",
    inspection_item: "模具顶出",
    inspection_criteria: ["模具顶出动作顺畅无干涉，空运行300次动作合格"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶针顶出干涉", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_water_circuit_1",
    inspection_item: "模具水路",
    inspection_criteria: ["模具水路完好，无泄漏问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具漏水", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_water_circuit_2",
    inspection_item: "模具水路",
    inspection_criteria: ["模具水路正确，无流量小问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "运水不通畅、一进多出", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_water_circuit_3",
    inspection_item: "模具水路",
    inspection_criteria: ["模具运行过程中镶件无水滴渗出"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具镶件渗水", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_water_circuit_4",
    inspection_item: "模具水路",
    inspection_criteria: ["模具水咀安装齐全"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "水咀安装不齐", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_water_circuit_5",
    inspection_item: "模具水路",
    inspection_criteria: ["模具运水接驳方便无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "运水接驳困难", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_water_circuit_6",
    inspection_item: "模具水路",
    inspection_criteria: ["模具管路运动无干涉"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "管路无固定，运动干涉", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_water_circuit_7",
    inspection_item: "模具水路",
    inspection_criteria: ["模具水路字码正确符合客户标准"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "字码标识遗漏或错误", grade: "C", deduction: 2 },
      { issue_item: "喷管/铍铜/浇口套运水未区分标识", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_1",
    inspection_item: "模具填充",
    inspection_criteria: ["多型腔模具填充98%时，100g以上产品重量差在5g以内，100g以下产品重量差5%以内。单型腔或异形腔模具末端填充一致。"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "多腔流动不平衡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_2",
    inspection_item: "模具填充",
    inspection_criteria: ["胶料流动末端，料峰夹角120°以上"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "单腔填充不平衡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_3",
    inspection_item: "模具填充",
    inspection_criteria: ["胶料流动均匀，无气体包裹问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品包气、烧焦", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_4",
    inspection_item: "模具填充",
    inspection_criteria: ["浇口料流顺畅，水口位置正确无气痕"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "浇口气痕难调节(太阳斑）", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_5",
    inspection_item: "模具填充",
    inspection_criteria: ["型腔料流顺畅，外观面位置无气痕"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品其他表面气痕难调节", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_6",
    inspection_item: "模具填充",
    inspection_criteria: ["高光件无熔接线；普通外观件0.5m内目视不明显，无手感；冰箱类（抽屉/面板）透明件熔接线位置-深浅-长短能否满足客户要求"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "外观面有熔接线", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_7",
    inspection_item: "模具填充",
    inspection_criteria: ["产品壁厚均匀或过渡均匀，无明显台阶、无偏腔壁厚不均匀"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观面应力痕（厚薄印）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_8",
    inspection_item: "模具填充",
    inspection_criteria: ["胶料流动正常，无料花"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观面料花难调节", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_9",
    inspection_item: "模具填充",
    inspection_criteria: ["产品外观颜色均匀，无色差、无阴阳色"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观色差、阴阳色难调节", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_10",
    inspection_item: "模具填充",
    inspection_criteria: ["产品壁厚均匀，填充无气泡"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品内部有气泡", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_11",
    inspection_item: "模具填充",
    inspection_criteria: ["模具填充顺畅，无缺胶，短射现象"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品包气缺胶", grade: "B", deduction: 3 },
      { issue_item: "产品异常壁厚缺胶", grade: "A", deduction: 5 },
      { issue_item: "其他原因缺胶（损公、积碳等）", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_1",
    inspection_item: "模具脱模",
    inspection_criteria: ["模具前模脱模角度足够无离型现象"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品粘前模", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_2",
    inspection_item: "模具脱模",
    inspection_criteria: ["模具后模脱模角度足够，省模B2以上"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品粘后模", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_3",
    inspection_item: "模具脱模",
    inspection_criteria: ["模具斜顶脱模角度足够，省模B2以上"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品粘斜顶", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_4",
    inspection_item: "模具脱模",
    inspection_criteria: ["模具行位脱模角度足够，省模B2以上"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品粘行位", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_5",
    inspection_item: "模具脱模",
    inspection_criteria: ["产品脱模顺畅，无吸真空现象"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品吸真空或吹气不均衡、吹爆/气顶出气不均衡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_6",
    inspection_item: "模具脱模",
    inspection_criteria: ["模具顶针排布均匀合理，顶出平衡"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶出不平衡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_7",
    inspection_item: "模具脱模",
    inspection_criteria: ["产品有自动脱模要求，能够自动跌落）"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品顶出后不能自动掉落", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_8",
    inspection_item: "模具脱模",
    inspection_criteria: ["扁顶/方顶不卡产品，取件顺畅"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具扁顶/方顶卡产品取件困难", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_9",
    inspection_item: "模具脱模",
    inspection_criteria: ["满足机械手取件需求"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "无法满足机械手取件需求", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_10",
    inspection_item: "模具脱模",
    inspection_criteria: ["产品有要求定位/固定，不能自动跌落"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品开模/顶出自动跌落，无法取件", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_11",
    inspection_item: "模具脱模",
    inspection_criteria: ["产品脱模无拉白"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品脱模拉白", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_12",
    inspection_item: "模具脱模",
    inspection_criteria: ["产品顶出顶针/斜顶无铲胶"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶针/斜顶铲胶", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_13",
    inspection_item: "模具脱模",
    inspection_criteria: ["产品开模内滑块/弹滑块无铲胶"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "内滑块/弹滑块铲胶", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_demolding_14",
    inspection_item: "模具脱模",
    inspection_criteria: ["模具开模行程足够，取件空间充足"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具取件干涉", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_white_mark_1",
    inspection_item: "产品顶白",
    inspection_criteria: ["工艺条件正常后，连续5模保压加10%-20%产品无顶白和粘腔问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "未达到工艺条件已顶白、开裂、暗裂", grade: "A+", deduction: 10 },
      { issue_item: "达到工艺条件，加压5%-10%顶白", grade: "A", deduction: 5 },
      { issue_item: "达到工艺条件，加压10%-20%顶白", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_process_range_1",
    inspection_item: "工艺范围",
    inspection_criteria: ["产品缺陷容易调整，注塑工艺范围宽泛"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "关键点调整范围±5%为极窄", grade: "A+", deduction: 10 },
      { issue_item: "关键点调整范围±10%为一般", grade: "A", deduction: 5 },
      { issue_item: "关键点调整范围±20%为正常", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_mold_cycle_time_1",
    inspection_item: "注塑周期",
    inspection_criteria: ["注塑周期能够满足客户量产需求"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品注保时间长", grade: "A", deduction: 5 },
      { issue_item: "塑化时间过长", grade: "C", deduction: 2 },
      { issue_item: "冷却时间长", grade: "A+", deduction: 10 },
      { issue_item: "取件时间长", grade: "B", deduction: 3 },
      { issue_item: "因模具结构问题、产品吸真空问题需开、合模慢速时间长", grade: "A", deduction: 5 },
      { issue_item: "未提供式样书周期判定无依据", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_clamping_force_1",
    inspection_item: "锁模力",
    inspection_criteria: ["注塑机锁模力满足客户要求吨位"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "额定锁模力不能满足量产需求", grade: "A+", deduction: 10 },
      { issue_item: "试模机台与额定机台不匹配", grade: "A", deduction: 5 },
      { issue_item: "模具结构不匹配额定机台", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_cooling_1",
    inspection_item: "模具冷却",
    inspection_criteria: ["模具前模冷却均匀，无局部过热问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "前模局部过热", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_cooling_2",
    inspection_item: "模具冷却",
    inspection_criteria: ["模具后模冷却均匀，无局部过热问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "后模局部过热", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_cooling_3",
    inspection_item: "模具冷却",
    inspection_criteria: ["模具行位冷却均匀，无局部过热问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位局部过热", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_cooling_4",
    inspection_item: "模具冷却",
    inspection_criteria: ["模具斜顶冷却均匀，无局部过热问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "斜顶局部过热", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_1",
    inspection_item: "模具研配",
    inspection_criteria: ["模具主分型面蓝丹均匀，无线状封胶"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "主分型面蓝丹不均", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_2",
    inspection_item: "模具研配",
    inspection_criteria: ["模具主分型面硬块蓝丹接触90%以上"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "承压块、行位背面耐磨块蓝丹不均", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_3",
    inspection_item: "模具研配",
    inspection_criteria: ["模具分型面擦穿位无摩擦痕、起刺"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "分型面擦烧", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_4",
    inspection_item: "模具研配",
    inspection_criteria: ["模具定位面擦穿位无摩擦痕、起刺"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "定位面擦烧", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_5",
    inspection_item: "模具研配",
    inspection_criteria: ["模具行位滑动面无摩擦痕、起刺"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位、反铲擦烧", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_6",
    inspection_item: "模具研配",
    inspection_criteria: ["模具行位斜导柱无摩擦痕、起刺"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位斜导柱孔及导柱擦烧", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_7",
    inspection_item: "模具研配",
    inspection_criteria: ["模具推块研配良好，顶出无卡顿"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "推块封胶面擦烧", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_8",
    inspection_item: "模具研配",
    inspection_criteria: ["模具斜顶滑动面无摩擦痕、起刺"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "斜顶封胶面擦烧", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_9",
    inspection_item: "模具研配",
    inspection_criteria: ["模具无定位圆顶能够转动"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "顶针研配过紧", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_fitting_10",
    inspection_item: "模具研配",
    inspection_criteria: ["推块顶出无跳动，卡滞"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "推块研配过紧", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_fastening_1",
    inspection_item: "模具紧固",
    inspection_criteria: ["行位斜导柱固定牢靠，不能晃动"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "斜导柱松动", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_fastening_2",
    inspection_item: "模具紧固",
    inspection_criteria: ["斜顶研配良好，固定牢靠，不能晃动"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "斜顶松动、转动", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_mold_fastening_3",
    inspection_item: "模具紧固",
    inspection_criteria: ["推块与推杆之间固定牢靠，不能晃动"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "推块松动、转动", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fastening_4",
    inspection_item: "模具紧固",
    inspection_criteria: ["在斜面上的圆顶有止转，不能转动"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "斜面顶针无定位", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fastening_5",
    inspection_item: "模具紧固",
    inspection_criteria: ["行位固定可靠，导向顺滑，无晃动"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "行位松动", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_fastening_6",
    inspection_item: "模具紧固",
    inspection_criteria: ["模具镶件强度足够，固定牢靠"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "镶件漏装或掉落", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_sink_mark_1",
    inspection_item: "缩痕",
    inspection_criteria: ["外观产品无缩痕"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观缩痕难调节", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_deformation_1",
    inspection_item: "变形",
    inspection_criteria: ["变形量小于长度的0.5%(变形量超出图纸或客户要求）"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "正常工艺变形超出标准", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_weight_1",
    inspection_item: "重量",
    inspection_criteria: ["根据式样书要求判定"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "超重", grade: "A+", deduction: 10 },
      { issue_item: "超轻", grade: "A", deduction: 5 },
      { issue_item: "未提供式样书重量判定无依据", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_dimension_1",
    inspection_item: "产品尺寸",
    inspection_criteria: ["产品外观装配有尺寸要求时标准尺寸加减0.5mm是否容易调整"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "正常工艺外观尺寸偏大", grade: "A+", deduction: 10 },
      { issue_item: "正常工艺外观尺寸偏小", grade: "A+", deduction: 10 },
      { issue_item: "正常工艺外观尺寸大小头难调整", grade: "A+", deduction: 10 },
      { issue_item: "未提供图纸尺寸判定无依据", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_mass_production_1",
    inspection_item: "量产性",
    inspection_criteria: ["量产验证制品防粘腔皮纹位置脱模无料渣、无冷料，脱模无铲胶"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "皮纹落料渣、有冷料", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_mold_mass_production_2",
    inspection_item: "量产性",
    inspection_criteria: ["空运行300次动作正常，定位面、封胶面无擦烧"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "空运行分型面擦烧", grade: "A+", deduction: 10 },
      { issue_item: "空运行定位面擦烧", grade: "A+", deduction: 10 },
      { issue_item: "空运行行位、反铲擦烧", grade: "A+", deduction: 10 },
      { issue_item: "空运行行位斜导柱孔及导柱擦烧", grade: "A+", deduction: 10 },
      { issue_item: "空运行推块封胶面擦烧", grade: "A+", deduction: 10 },
      { issue_item: "空运行斜顶封胶面擦烧", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_other_1",
    inspection_item: "其他",
    inspection_criteria: ["影响量产性的其他问题"],
    category_level_1: "试模检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "影响量产性的其他问题", grade: "A+", deduction: 10 }
    ]
  }
]

export const kelongMoldInspectionItems = KL_MOLD_TRIAL_ISSUE_TEMPLATE.map(item => {
  return {
    ...item,
    deduction: null,
    grade: null,
    id: null,
    is_old_issue: false,
    issue_code: null,
    issue_description: null,
    issue_images: [],
    issue_files: [],
    issue_item: null,
    issue_type: "mold_insp",
    judgement: null,
    judgement_by: null,
    judgement_at: null,
    trial_session_id: null,
  }
})


export const KELONG_SAMPLE_TRIAL_ISSUE_TEMPLATE = [
  {
    inspection_key: "kl_product_polishing_1",
    inspection_item: "产品抛光",
    inspection_criteria: ["产品外观面无机加工纹，省模良好"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品表面有机加工纹", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_polishing_2",
    inspection_item: "产品抛光",
    inspection_criteria: ["模具无越级抛光，表面无材料纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品表面有橘皮纹", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_product_polishing_3",
    inspection_item: "产品抛光",
    inspection_criteria: ["抛光外观以45°-90°方向，300mm距离目测产品表面平整，光亮"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品表面抛光不顺滑", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_polishing_4",
    inspection_item: "产品抛光",
    inspection_criteria: ["钢材外观成型面平整致密无孔洞"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观面有麻点", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_polishing_5",
    inspection_item: "产品抛光",
    inspection_criteria: ["产品分型面周圈无圆口或者塌陷"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品分型面圆口、塌陷", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_polishing_6",
    inspection_item: "产品抛光",
    inspection_criteria: ["产品周圈无摩擦痕和拖伤"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品周圈有拖伤、拖花", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_product_clean_1",
    inspection_item: "产品洁净",
    inspection_criteria: ["产品前模镶件位置无油污及油印"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品前模镶件有油污", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_clean_2",
    inspection_item: "产品洁净",
    inspection_criteria: ["产品后模镶件位置无油污及油印"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品后模镶件有油污", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_product_clean_3",
    inspection_item: "产品洁净",
    inspection_criteria: ["产品行位位置无油污及油印"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品行位有油污", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_clean_4",
    inspection_item: "产品洁净",
    inspection_criteria: ["产品顶针、斜顶、方顶无油污或者油印"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品顶针有油污", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_sink_mark_1",
    inspection_item: "产品缩痕",
    inspection_criteria: ["以45°-90°方向，300mm距离目测产品外观面无收缩引起的折光痕"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观面缩痕", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_sink_mark_2",
    inspection_item: "产品缩痕",
    inspection_criteria: ["产品非外观面缩痕手摸无凹陷感"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品非外观面缩痕", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_product_flow_mark_1",
    inspection_item: "产品流痕",
    inspection_criteria: ["产品外观面无胶料冲刷痕迹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观冲花", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_flow_mark_2",
    inspection_item: "产品流痕",
    inspection_criteria: ["加纤材料外观无明显的浮纤纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观浮纤纹", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_product_flow_mark_3",
    inspection_item: "产品流痕",
    inspection_criteria: ["产品外观面无气体冲刷形成的雾状痕"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观气痕", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_flow_mark_4",
    inspection_item: "产品流痕",
    inspection_criteria: ["产品外观面无应力集中导致的高亮痕"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观应力痕", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_flow_mark_5",
    inspection_item: "产品流痕",
    inspection_criteria: ["产品外观无进浇口冲刷形成的波浪纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观橘皮纹", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flow_mark_6",
    inspection_item: "产品流痕",
    inspection_criteria: ["产品外观洁净无杂色混合"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观混色", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_1",
    inspection_item: "产品披锋",
    inspection_criteria: ["产品外观面披锋高度不得超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观面披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_2",
    inspection_item: "产品披锋",
    inspection_criteria: ["非外观面披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品非主分型面披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_3",
    inspection_item: "产品披锋",
    inspection_criteria: ["流道分型面披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "浇口套披锋", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_4",
    inspection_item: "产品披锋",
    inspection_criteria: ["封胶良好披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "阀针封胶不良、披锋", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_5",
    inspection_item: "产品披锋",
    inspection_criteria: ["热咀冷却套披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "流道分型面披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_6",
    inspection_item: "产品披锋",
    inspection_criteria: ["行位面披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品行位披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_7",
    inspection_item: "产品披锋",
    inspection_criteria: ["斜顶面披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品斜顶位披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_8",
    inspection_item: "产品披锋",
    inspection_criteria: ["圆顶面披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品圆顶披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_9",
    inspection_item: "产品披锋",
    inspection_criteria: ["方顶、扁顶面披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品方顶、扁顶披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_flash_10",
    inspection_item: "产品披锋",
    inspection_criteria: ["镶件面披锋高度不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品镶件位披锋超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_ejection_white_1",
    inspection_item: "产品顶白",
    inspection_criteria: ["产品表面无顶针挤压产生的白化纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品顶针顶白", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_ejection_white_2",
    inspection_item: "产品顶白",
    inspection_criteria: ["产品表面无斜顶挤压产生的白化纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品斜顶顶白", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_ejection_white_3",
    inspection_item: "产品顶白",
    inspection_criteria: ["透明产品表面顶针挤压产生的裂纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品顶裂", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_ejection_white_4",
    inspection_item: "产品顶白",
    inspection_criteria: ["产品无顶穿、顶高问题"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品顶针顶穿", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_scrape_1",
    inspection_item: "产品铲胶",
    inspection_criteria: ["产品圆顶印段差高于胶位面0-0.05mm，顶出无起皮现象"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具圆顶铲胶", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_scrape_2",
    inspection_item: "产品铲胶",
    inspection_criteria: ["产品方顶印段差高于胶位面0-0.05mm，顶出无起皮现象"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具方顶铲胶", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_scrape_3",
    inspection_item: "产品铲胶",
    inspection_criteria: ["产品斜顶印段差高于胶位面0-0.05mm，顶出无起皮现象"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具斜顶铲胶", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_scrape_4",
    inspection_item: "产品铲胶",
    inspection_criteria: ["产品推块印段差高于胶位面0-0.05mm，顶出无起皮现象"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具推块铲胶", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_texture_mark_1",
    inspection_item: "晒纹/晒字",
    inspection_criteria: ["产品纹路清晰无拖伤、发亮问题"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品纹面拖花或发亮", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_texture_mark_2",
    inspection_item: "晒纹/晒字",
    inspection_criteria: ["产品晒字内容符合图纸要求"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "晒字内容错误", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_texture_mark_3",
    inspection_item: "晒纹/晒字",
    inspection_criteria: ["产品按照客户图档晒字、晒纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品纹面或晒字未做", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_texture_mark_4",
    inspection_item: "晒纹/晒字",
    inspection_criteria: ["产品晒字位置与图档位置吻合"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "晒字位置错误", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_crack_1",
    inspection_item: "产品裂痕",
    inspection_criteria: ["产品骨位省模良好，无开裂、拉白"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品骨位拉白、拉裂", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_crack_2",
    inspection_item: "产品裂痕",
    inspection_criteria: ["产品扣位省模良好，无开裂、拉白"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品扣位拉白、拉裂", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_crack_3",
    inspection_item: "产品裂痕",
    inspection_criteria: ["产品外形省模良好，无开裂、拉白"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外形拉白、拉裂", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_crack_4",
    inspection_item: "产品裂痕",
    inspection_criteria: ["透明产品收缩无应力集中，闪光纹"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "透明件角落暗裂纹", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_step_1",
    inspection_item: "产品段差",
    inspection_criteria: ["产品外观面段差不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观面段差超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_step_2",
    inspection_item: "产品段差",
    inspection_criteria: ["流道分型面段差不超过0.1mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "流道分型面段差超差", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_product_step_3",
    inspection_item: "产品段差",
    inspection_criteria: ["产品非主分型面段差不超过0.1mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品非主分型面段差超差", grade: "A", deduction: 5 }
    ]
  },
  {
    inspection_key: "kl_product_step_4",
    inspection_item: "产品段差",
    inspection_criteria: ["产品行位分型面段差不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品行位段差超差", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_step_5",
    inspection_item: "产品段差",
    inspection_criteria: ["产品斜顶面段差不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品斜顶位段差超差", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_step_6",
    inspection_item: "产品段差",
    inspection_criteria: ["产品圆顶面段差不超过0.05mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品圆顶段差超差", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_step_7",
    inspection_item: "产品段差",
    inspection_criteria: ["产品方顶、扁顶面段差不超过0.1mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品方顶、扁顶段差超差", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_step_8",
    inspection_item: "产品段差",
    inspection_criteria: ["产品镶件分型面段差不超过0.1mm"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品镶件位段差超差", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_1",
    inspection_item: "模具填充",
    inspection_criteria: ["多型腔模具填充98%时，100g以上产品重量差在2g以内，100g以下产品重量差5%以内。单型腔或异形腔模具末端填充一致。"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "多腔流动不平衡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_2",
    inspection_item: "模具填充",
    inspection_criteria: ["胶料流动末端，料峰夹角120°以上"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "单腔填充不平衡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_3",
    inspection_item: "模具填充",
    inspection_criteria: ["胶料流动均匀，无气体包裹问题"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品包气、烧焦", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_4",
    inspection_item: "模具填充",
    inspection_criteria: ["产品壁厚均匀，填充无气泡"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品内部有气泡", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_5",
    inspection_item: "模具填充",
    inspection_criteria: ["产品流动顺畅，水口位置正确无气痕"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品气痕难调节", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_mold_filling_6",
    inspection_item: "模具填充",
    inspection_criteria: ["模具填充顺畅，无缺胶，短射现象"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "模具局部填充困难", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_weld_line_1",
    inspection_item: "产品熔接痕",
    inspection_criteria: ["以45°-90°方向，300mm距离目测无熔接痕"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品外观面有熔接痕", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_weld_line_2",
    inspection_item: "产品熔接痕",
    inspection_criteria: ["产品扣位中部无熔接痕"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品扣位中部有熔接痕", grade: "B", deduction: 3 }
    ]
  },
  {
    inspection_key: "kl_product_weld_line_3",
    inspection_item: "产品熔接痕",
    inspection_criteria: ["熔接痕位置强度足够，手压不易裂"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品熔接痕位置易开裂", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_weld_line_4",
    inspection_item: "产品熔接痕",
    inspection_criteria: ["产品非外观面熔接痕手摸无凹陷感"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品非外观面容接痕有凹陷感", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_deformation_1",
    inspection_item: "产品变形",
    inspection_criteria: ["产品平整，整体变形量小于5‰（LX0.005mm）"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品翘曲变形", grade: "B", deduction: 3 },
      { issue_item: "产品扭曲变形", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_feature_1",
    inspection_item: "产品特征",
    inspection_criteria: ["产品与客户实体一致，无多余结构"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品有多余结构", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_feature_2",
    inspection_item: "产品特征",
    inspection_criteria: ["产品与客户实体一致，无缺失结构"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品结构漏做", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_feature_3",
    inspection_item: "产品特征",
    inspection_criteria: ["产品结构位置与客户实体一致"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品特征位置错误", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_feature_4",
    inspection_item: "产品特征",
    inspection_criteria: ["产品柱位内孔与外缘中心一致"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品柱位孔不同心", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_product_weight_1",
    inspection_item: "产品重量",
    inspection_criteria: ["A类客户（VESTEL、rubbermaid、宜家）±2%范围内，B类客户（Arcelik、其他）±5%范围内，内单（Hisense）-2%范围内"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "A类客户产品超重", grade: "A+", deduction: 10 },
      { issue_item: "A类客户产品偏轻", grade: "A", deduction: 5 },
      { issue_item: "B类客户产品超重", grade: "A", deduction: 5 },
      { issue_item: "B类客户产品偏轻", grade: "C", deduction: 2 }
    ]
  },
  {
    inspection_key: "kl_product_dimension_1",
    inspection_item: "产品尺寸",
    inspection_criteria: ["产品尺寸全部不符合2D图档标注的重要尺寸\n产品尺寸95%不符合2D图档标注的尺寸"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "产品尺寸超公差", grade: "A+", deduction: 10 }
    ]
  },
  {
    inspection_key: "kl_trial_condition_1",
    inspection_item: "试模条件",
    inspection_criteria: ["额定生产周期(S)\n额定设备吨位(T)"],
    category_level_1: "样件检验",
    category_level_2: "塑模",
    options: [
      { issue_item: "试模生产周期(S)\n试模设备吨位(T)", grade: "A+", deduction: 10 }
    ]
  }
]

export const kelongSampleInspectionItems = KELONG_SAMPLE_TRIAL_ISSUE_TEMPLATE.map(item => {
  return {
    ...item,
    deduction: null,
    grade: null,
    id: null,
    is_old_issue: false,
    issue_code: null,
    issue_description: null,
    issue_images: [],
    issue_files: [],
    issue_item: null,
    issue_type: "sample_insp",
    judgement: null,
    judgement_by: null,
    judgement_at: null,
    trial_session_id: null,
  }
})


export const KELONG_DISASSEMBLY_TRIAL_ISSUE_TEMPLATE = [
  // 单件拆检内容
  {
    inspection_key: "factory_spare_parts_check",
    inspection_item: "出厂备件检查",
    inspection_criteria: ["拆检时，依据出厂备件清单检查出厂备件，常规备件、热流道和薄钢备件齐套。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "备件与清单不符或缺少", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "customer_special_requirement",
    inspection_item: "客户特殊要求检查",
    inspection_criteria: ["拆检时，查看零件表面处理（涂层、晒纹的有品牌、厂家等有特殊表面处理要求等）凭证，是否满足要求。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "特殊表面处理不符合要求或缺少凭证", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "part_marking_check",
    inspection_item: "零件字码检查",
    inspection_criteria: ["所有零件字码是否按照公司规定雕刻。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "零件字码未按规定雕刻", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "gate_bush_1",
    inspection_item: "浇口套",
    inspection_criteria: ["浇口套要求SKD61，硬度符合要求（HRC48~52）。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "浇口套材质或硬度不符合要求", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "gate_bush_2",
    inspection_item: "浇口套",
    inspection_criteria: ["浇口套外观符合要求（无碰伤，无塌口，无圆角等）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "浇口套外观存在碰伤、塌口或圆角", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "runner_1",
    inspection_item: "流道",
    inspection_criteria: ["主流道、分流道要求抛光（打磨320号砂纸后抛光Ra1.6）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "流道抛光不达标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "runner_2",
    inspection_item: "流道",
    inspection_criteria: ["主流道和分流道接口处要求有R过渡（R=1~2mm）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "流道接口处无R过渡或过渡不当", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "runner_3",
    inspection_item: "流道",
    inspection_criteria: ["主流道、分流道外观符合要求（边口无碰伤，无塌口，无过切，无倒扣等现象）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "流道边口存在碰伤、塌口、过切或倒扣", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "gate_1",
    inspection_item: "入水口",
    inspection_criteria: ["入水口符合抛光要求（320号砂纸上光）。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "入水口抛光不达标", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "gate_2",
    inspection_item: "入水口",
    inspection_criteria: ["入水口（潜水，侧水口等）棱角分明，无手工修磨现象和无焊斑。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "入水口棱角不分明或有手工修磨、焊斑", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "gate_3",
    inspection_item: "入水口",
    inspection_criteria: ["模具定位圈直径、唧嘴球径SR符合式样书"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "定位圈直径或唧嘴球径SR不符", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "hot_runner_1",
    inspection_item: "热流道",
    inspection_criteria: ["热流道样式、 接线插座及底座型号、 接线符合式样书、 电磁阀电压、 电磁阀接线方式、 热流道接线盒上要有对应的接线小标牌(见客户标准)"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "热流道相关配置（样式、接线、标牌等）不符合式样书或客户标准", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "hot_runner_2",
    inspection_item: "热流道",
    inspection_criteria: ["电磁阀电压、驱动方式、快换接头眼观符合式样书"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "电磁阀参数或快换接头不符合式样书", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "hot_runner_3",
    inspection_item: "热流道",
    inspection_criteria: ["热电偶型号符合式样书；热流道观察孔、排水槽是否需要并加工"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "热电偶型号不符或观察孔/排水槽未按要求加工", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "ejector_pin_1",
    inspection_item: "顶针（扁顶司筒、推杆）",
    inspection_criteria: ["所有的顶针要求从镶件型面上插入并用手进行来回抽动顺滑，但是不能恍动恍动虚位≤0.03mm（一个一个检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "顶针抽动不顺畅或虚位超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "ejector_pin_2",
    inspection_item: "顶针（扁顶司筒、推杆）",
    inspection_criteria: ["所有在异型面上的顶针都有止转。（一个一个检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "异型面顶针缺少止转", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "ejector_pin_3",
    inspection_item: "顶针（扁顶司筒、推杆）",
    inspection_criteria: ["所有顶针头在顶针固定板上高度的虚位≤0.05mm。（一个一个检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "顶针头虚位超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "ejector_pin_4",
    inspection_item: "顶针（扁顶司筒、推杆）",
    inspection_criteria: ["所有的顶针需符合硬度要求（顶针：材质内部HRC48~52，表面HV0.3 950；   扁顶：材质内部HRC48~52，表面HV0.3 950）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "顶针或扁顶硬度/材质不符合要求", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "ejector_pin_5",
    inspection_item: "顶针（扁顶司筒、推杆）",
    inspection_criteria: ["所有的顶针、扁顶、推杆表面无手工打磨痕迹、无擦伤，烧伤，顶部封胶处无碰伤，圆口"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "顶针/扁顶/推杆表面存在打磨痕、擦伤、烧伤或封胶处碰伤/圆口", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "pull_rod_1",
    inspection_item: "拉料杆",
    inspection_criteria: ["拉料杆水口位置需要去机纹。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "拉料杆水口位置有机纹未去除", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "pull_rod_2",
    inspection_item: "拉料杆",
    inspection_criteria: ["拉料杆处的顶杆封胶处边口无碰伤，无塌口，无圆角。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "拉料杆封胶处边口存在碰伤、塌口或圆角", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "lifter_base_1",
    inspection_item: "斜顶掌底座",
    inspection_criteria: ["所有的斜顶掌底滑动顺畅，无晃动恍动虚位≤0.05mm，无松摆现象（一个一个检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶掌底滑动不顺畅或虚位超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "lifter_base_2",
    inspection_item: "斜顶掌底座",
    inspection_criteria: ["所有的斜顶掌底底部都有耐磨硬块（一个一个检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶掌底底部缺少耐磨硬块", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "lifter_base_3",
    inspection_item: "斜顶掌底座",
    inspection_criteria: ["所有掌底材质、硬度符合要求。（实测材质：          硬度：           ）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "掌底材质或硬度不符合要求", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "lifter_base_4",
    inspection_item: "斜顶掌底座",
    inspection_criteria: ["所有斜顶掌底符合外观要求，无碰伤，无塌口。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶掌底存在碰伤或塌口", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "lifter_base_5",
    inspection_item: "斜顶掌底座",
    inspection_criteria: ["非标准件的斜顶掌底滑动导向配合部分要求磨削Ra0.8。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "非标准件掌底滑动面粗糙度不达标", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "lifter_base_6",
    inspection_item: "斜顶掌底座",
    inspection_criteria: ["所有斜顶掌底的利边，螺钉过孔都倒角C0.5~C1（一个一个检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "掌底利边或螺钉过孔未按要求倒角", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "push_block_1",
    inspection_item: "推块",
    inspection_criteria: ["推块材质和硬度符合要求。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "推块材质或硬度不符合要求", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "push_block_2",
    inspection_item: "推块",
    inspection_criteria: ["推块大面方向两侧要求有避空面"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "推块大面两侧无避空面", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "push_block_3",
    inspection_item: "推块",
    inspection_criteria: ["所有推块符合外观要求（无焊疤、打磨等痕迹）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "推块表面存在焊疤或打磨痕迹", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "lifter_1",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["垂直滑动的斜顶要求对斜顶抬高后（高度为斜顶长度的一半）进行自由落体运动到底，斜顶顶面与型面位置高度差为±0.05mm"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "垂直滑动斜顶自由落体后高度差超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "lifter_2",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["水平滑动的斜顶要求用手推压到底，斜顶顶面与型面位置高度差为0~0.1mm"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "水平滑动斜顶推压后高度差超标", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "lifter_3",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["所有斜顶表面有油槽，无烧焊，烧伤，人工打磨等痕迹（一根一根检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶表面无油槽或存在烧焊/烧伤/打磨痕迹", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "lifter_4",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["所有的斜顶有铜套，与铜套的双边间隙≤0.05mm（一根一根检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶与铜套间隙超标", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "lifter_5",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["所有斜顶滑动配合面粗糙度符合要求Ra0.8"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶滑动面粗糙度不达标", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "lifter_6",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["所有的斜顶材质及硬度都符合要求HRC48~52（一个一个检查）。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶材质或硬度不符合要求", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "lifter_7",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["所有的斜顶底部的牙孔的底孔直径和深度符合要求"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶底部牙孔直径或深度不符", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "lifter_8",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["所有的斜顶头部要有限位结构"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶头部无限位结构", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "lifter_9",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["所有的斜顶能用手来回抽动到底，但是不能恍动,恍动虚位≤0.05mm"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶抽动不能到底或虚位超标", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "slider_1",
    inspection_item: "滑块",
    inspection_criteria: ["天侧滑块要有双保险设计机构（弹簧机构+限位夹），防止弹簧失效而碰伤模具。其他保险机构按客户技术要求（滑块底下有限位夹或弹珠限位结构）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "天侧滑块无双保险机构或不符合客户技术要求", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "slider_2",
    inspection_item: "滑块",
    inspection_criteria: ["滑块材质及硬度符合要求。（实测硬度：              ）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "滑块材质或硬度不符合要求", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "slider_3",
    inspection_item: "滑块",
    inspection_criteria: ["斜导柱紧固在斜导柱座上，无晃动和前后松动现象"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜导柱松动或未紧固", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "slider_4",
    inspection_item: "滑块",
    inspection_criteria: ["滑块下面有顶出，需要强复位机构或者行程开关；"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "滑块下顶出缺少强复位机构或行程开关", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "slider_5",
    inspection_item: "滑块",
    inspection_criteria: ["所有滑块两侧与动模接触的位置要求有油槽（仅限外罩、抽屉模具）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "滑块与动模接触位无油槽（限适用模具）", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "slider_6",
    inspection_item: "滑块",
    inspection_criteria: ["滑块除胶位面及封胶面以外其他的型边都要求倒角C1~C1。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "滑块型边未按要求倒角", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "slider_7",
    inspection_item: "滑块",
    inspection_criteria: ["滑块封料面边缘无挤伤，成型面无磕碰、划伤，无明显的砂轮研配痕迹。导轨尺寸测量与滑块间隙单边≤0.02mm，左右用手摆动无明显的晃动"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "滑块封料面或成型面有缺陷，或导轨间隙超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "slider_8",
    inspection_item: "滑块",
    inspection_criteria: ["滑块斜导柱插入之前，大导柱要先进入大导套。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "合模时大导柱未先于斜导柱进入导套", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "insert_1",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["产品需要抛光的，则模具型面需平整、无凹坑、裂纹、锈迹等其他影响外观的缺陷，抛光质量按规范检测。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "模具型面不平整或有缺陷，抛光质量不达标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "insert_2",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["零件材质及硬度符合图纸要求。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "镶件材质或硬度不符合图纸", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "insert_3",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["所有密封圈孔深度需符合图纸要求（密封圈红色硅胶），密封圈与运水孔无偏向，偏向要求在0.5mm以内并不允许过切崩孔现象"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "密封圈孔深度/位置偏差超标或过切崩孔", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "insert_4",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["模具日期章需选必须选用锁螺丝结构，试模时指针调到当月"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "日期章未使用锁螺丝结构或指针未调当月", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "insert_5",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["如果产品有多腔，型腔号T1前按要求晒字"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "多腔模具型腔号晒字不符合要求", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "insert_6",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["动、定模镶件排气槽整齐规范，深度不超过塑料材料的溢边值(对照产品检，符合客户要求)。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "排气槽不规范或深度超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "insert_7",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["分型面干净、整洁，无打磨痕迹和烧焊痕迹。（150#油石打磨清除痕迹）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "分型面有打磨或烧焊痕迹", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "insert_8",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["对分型面、封胶面以及胶位面以外的型边要求进行倒角C1~C2。（螺丝孔、沉头孔、过孔均要求倒角等）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "型边或孔位未按要求倒角", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "insert_9",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["分型边无圆口，无塌口，无扣倒等影响分型面质量的缺陷"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "分型边存在圆口、塌口或倒扣", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "insert_10",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["非胶位型面堵水，运水堵塞使用止水栓；胶位型面堵水，运水堵塞使用钢粒并要求表面平整，无凹陷。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "运水堵塞方式不当或表面不平整", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "insert_11",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["各个零件都刻有零件代号和图纸一一对应"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "零件代号缺失或与图纸不对应", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "insert_12",
    inspection_item: "动模镶件/定模镶件",
    inspection_criteria: ["所有在新模加工过程中出现异常质量的零件（试模代用品零件），拆模检时必须检查到位。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "异常质量零件（试模代用品）漏检", grade: "C", deduction: 2 }]
  },
  {
    inspection_key: "guide_1",
    inspection_item: "硬块/压条导向件",
    inspection_criteria: ["所有导向块、压条的底面与侧面垂直度要求⊥±2´"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "导向块/压条底面与侧面垂直度超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "guide_2",
    inspection_item: "硬块/压条导向件",
    inspection_criteria: ["所有硬块、导向件、压条材质及硬度符合图纸要求HRC48-52。（实测硬度：       ）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "硬块/导向件/压条材质或硬度不符合图纸", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "guide_3",
    inspection_item: "硬块/压条导向件",
    inspection_criteria: ["所有硬块、导向件、压条要求开有油槽并整齐清晰"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "硬块/导向件/压条无油槽或不清晰", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_1",
    inspection_item: "模板",
    inspection_criteria: ["各模板（整板）材质及硬度符合图纸要求。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "模板材质或硬度不符合图纸", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "mold_plate_2",
    inspection_item: "模板",
    inspection_criteria: ["标准水嘴需符合图纸要求(台阶沉头孔与直接模胚面攻牙接水嘴的区别)。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "水嘴不符合图纸要求", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "mold_plate_3",
    inspection_item: "模板",
    inspection_criteria: ["所有密封圈孔深度需符合图纸要求，密封圈与运水孔无偏向，偏向要求在0.5mm以内并不允许过切崩孔现象"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "密封圈孔深度/位置偏差超标或过切崩孔", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "mold_plate_4",
    inspection_item: "模板",
    inspection_criteria: ["模板所有边角位、螺牙孔、过孔等（除胶位、封胶位外）均已采用机加倒角C1~C2。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "模板边角位或孔位未按要求倒角", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "mold_plate_5",
    inspection_item: "模板",
    inspection_criteria: ["各模板外观符合要求（外观干净，无刮痕、无任何油污和锈迹等）码模厚度符合式样书要求"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "模板外观不洁或有缺陷，或码模厚度不符", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_6",
    inspection_item: "模板",
    inspection_criteria: ["模具上的“in”“out”编号已经刻印好，并跟3D实体要求一一对应；各标牌槽位置、大小要符合客户标准；铭牌种类、数量、信息内容符合客户标准和图纸；"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "水路编号、标牌槽或铭牌不符合要求", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_7",
    inspection_item: "模板",
    inspection_criteria: ["所有支撑柱都紧紧固定在模板上，高度一致，并比方铁高0.1~0.2mm"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "支撑柱固定不良或高度不一致/超差", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_8",
    inspection_item: "模板",
    inspection_criteria: ["如有气阀辅助顶出，气路通畅，紧配的气阀不松动，活动的气阀回位后平整"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "气阀气路不通、松动或回位不平整", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_9",
    inspection_item: "模板",
    inspection_criteria: ["如有气阀辅助顶出，气路入口处有清晰标识并有白色接头"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "气路入口无标识或非白色接头", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_10",
    inspection_item: "模板",
    inspection_criteria: ["导柱、导套、中导柱导套的外观符合要求（无擦伤、无打磨、无机纹等）大导套要有排气槽"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "导柱/导套外观有缺陷或大导套无排气槽", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_11",
    inspection_item: "模板",
    inspection_criteria: ["精定位、边锁块无擦伤、无打磨、无机纹等"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "精定位或边锁块有擦伤/打磨/机纹", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "mold_plate_12",
    inspection_item: "模板",
    inspection_criteria: ["隔热板要求使用蓝色环氧板"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "隔热板材质不是蓝色环氧板", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "frame_external_1",
    inspection_item: "模架外部件",
    inspection_criteria: ["水路、油路密封性无泄漏、渗漏现象（静止观察十五分钟）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "水路或油路存在泄漏或渗漏", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "frame_external_2",
    inspection_item: "模架外部件",
    inspection_criteria: ["吊环装拆不与电气阀等外部配件产生干涉性"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "吊环装拆与外部配件干涉", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "frame_external_3",
    inspection_item: "模架外部件",
    inspection_criteria: ["水管、油缸、油管装拆不与外部配件产生干涉性"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "水管/油缸/油管装拆与外部配件干涉", grade: "B", deduction: 3 }]
  },
  {
    inspection_key: "frame_external_4",
    inspection_item: "模架外部件",
    inspection_criteria: ["顺序器、行程控制器的完整性、可靠性，无碰伤、漏装螺钉现象"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "顺序器/行程控制器不完整、不可靠或碰伤/漏螺钉", grade: "B", deduction: 3 }]
  },
  // 组合拆检内容
  {
    inspection_key: "assembly_ejector",
    inspection_item: "顶针（扁顶司筒、推杆）",
    inspection_criteria: ["组合顶针与后模部分，采用吊车对顶针进行自由落体运动到底，顶针顶面与型面位置高度差为0~0.1mm"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "组合顶针自由落体后高度差超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "assembly_lifter_base",
    inspection_item: "斜顶掌底座",
    inspection_criteria: ["所有斜顶掌底螺钉与斜顶紧固不松动。"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "斜顶掌底螺钉松动", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "assembly_push_block",
    inspection_item: "推块",
    inspection_criteria: ["所有的推杆与铜套的配合能用手来回顺滑抽动，但是不能恍动，恍动虚位≤0.05mm（一个一个检查）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "推杆与铜套配合不顺畅或虚位超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "assembly_lifter",
    inspection_item: "斜顶（直顶、方顶）",
    inspection_criteria: ["组合斜顶与后模部分，采用吊车对斜顶进行自由落体运动到底，斜顶顶面与型面位置高度差为0~0.1mm"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "组合斜顶自由落体后高度差超标", grade: "A", deduction: 5 }]
  },
  {
    inspection_key: "assembly_slider",
    inspection_item: "滑块",
    inspection_criteria: ["滑块与压条组装后在模板上用手来回推动，但是不能恍动（恍动虚位≤0.05mm）"],
    category_level_1: "拆模检验",
    category_level_2: "塑膜",
    options: [{ issue_item: "滑块与压条组装后推动不顺畅或虚位超标", grade: "A", deduction: 5 }]
  }
]

export const kelongDisassemblyInspectionItems = KELONG_DISASSEMBLY_TRIAL_ISSUE_TEMPLATE.map(item => {
  return {
    ...item,
    deduction: null,
    grade: null,
    id: null,
    is_old_issue: false,
    issue_code: null,
    issue_description: null,
    issue_images: [],
    issue_files: [],
    issue_item: null,
    issue_type: "disassembly_insp",
    judgement: null,
    judgement_by: null,
    judgement_at: null,
    trial_session_id: null,
  }
})