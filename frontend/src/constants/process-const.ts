
import { moldInfoForm, gatingSystemForm } from "@/constants/mold-const"
import { machineInfoForm, injectionUnitForm } from "@/constants/machine-const"
import { polymerInfoForm } from "@/constants/polymer-const"
import { initArray } from "@/utils/array-utils"


export const processConditionForm = {
  id: null,
  // --- 模具信息 ---
  mold_info: structuredClone(moldInfoForm),
  shot_index: 0,
  gating_system: structuredClone(gatingSystemForm),
  // --- 注射单元信息 ---
  machine_info: structuredClone(machineInfoForm),
  injection_index: 0,
  injection_unit: structuredClone(injectionUnitForm),
  // --- 材料信息 ---
  polymer_info: structuredClone(polymerInfoForm)
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
    cooling_time: null
  },
  vp_switch: {
    mode: 0,
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
    pre_decompress_mode: 0,
    post_decompress_mode: 1,
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

export const processParameterForm = {
  id: null,
  setting_process: structuredClone(settingProcessForm),
}

export const injectionProcessForm = {
  condition: structuredClone(processConditionForm),
  parameter: structuredClone(processParameterForm)
}