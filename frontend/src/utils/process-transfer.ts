/**
 * 将前端 structured setting_process_form 转换为后端所需的扁平字段对象
 * 字段命名与后端 schemas.py 保持一致（使用缩写命名如 inj_spd_1）
 * @param {Object} setting_process - 来自 settingProcessForm 的数据
 * @returns {Object} 扁平化的后端参数对象
 */
export function transformSettingProcessToBackend(setting_process: any) {
  const result: { [key: string]: any } = {}

  // --- 注射参数 (injection) ---
  const injection = setting_process.injection
  if (injection) {
    result.inj_stg = injection.stage

    // 顺序必须与 table_data 中的 label 顺序一致: ["压力", "速度", "位置"]
    const prefixes = ["inj_pres_", "inj_spd_", "inj_pos_"]

    injection.table_data.forEach((row: any, row_index: number) => {
      const prefix = prefixes[row_index]
      if (!prefix) return

      for (let i = 1; i <= injection.stage; i++) {
        const value = row.sections[i - 1]
        result[`${prefix}${i}`] = value != null ? parseFloat(value) : null
      }
    })

    result.inj_t = injection.injection_time != null ? parseFloat(injection.injection_time) : null
    result.inj_dly_t = injection.delay_time != null ? parseFloat(injection.delay_time) : null
  }

  // --- VP 切换参数 (vp_switch) ---
  const vp_switch = setting_process.vp_switch
  if (vp_switch) {
    result.vps_mode = vp_switch.mode != null ? parseInt(vp_switch.mode) : null
    result.vps_pos = vp_switch.position != null ? parseFloat(vp_switch.position) : null
    result.vps_t = vp_switch.time != null ? parseFloat(vp_switch.time) : null
    result.vps_pres = vp_switch.pressure != null ? parseFloat(vp_switch.pressure) : null
    result.vps_spd = vp_switch.velocity != null ? parseFloat(vp_switch.velocity) : null
  }

  // --- 保压参数 (holding) ---
  const holding = setting_process.holding
  if (holding) {
    result.hold_stg = holding.stage

    const holding_prefixes = ["hold_pres_", "hold_spd_", "hold_t_"] // 压力、速度、时间

    holding.table_data.forEach((row: any, row_index: number) => {
      const prefix = holding_prefixes[row_index]
      if (!prefix) return

      for (let i = 1; i <= holding.stage; i++) {
        const value = row.sections[i - 1]
        result[`${prefix}${i}`] = value != null ? parseFloat(value) : null
      }
    })
  }

  // --- 冷却参数 ---
  const cooling_time = setting_process.cooling_time || setting_process.injection?.cooling_time
  if (cooling_time != null) {
    result.cool_t = parseFloat(cooling_time)
  }

  // --- 熔胶参数 (metering) ---
  const metering = setting_process.metering
  if (metering) {
    result.met_stg = metering.stage

    const metering_prefixes = ["met_pres_", "met_rot_spd_", "met_back_pres_", "met_pos_"] // 压力、螺杆转速、背压、位置

    metering.table_data.forEach((row: any, row_index: number) => {
      const prefix = metering_prefixes[row_index]
      if (!prefix) return

      for (let i = 1; i <= metering.stage; i++) {
        const value = row.sections[i - 1]
        result[`${prefix}${i}`] = value != null ? parseFloat(value) : null
      }
    })

    // 松退参数
    const decompress_table_data = metering.decompress_table_data
    if (decompress_table_data && decompress_table_data.length >= 2) {
      const decomp_before = decompress_table_data[0] // 储前
      const decomp_after = decompress_table_data[1]  // 储后

      // 储前
      result.pre_met_decomp_mode = metering.pre_decompress_mode != null ? parseInt(metering.pre_decompress_mode) : null
      result.pre_met_decomp_pres = decomp_before.pressure != null ? parseFloat(decomp_before.pressure) : null
      result.pre_met_decomp_spd = decomp_before.velocity != null ? parseFloat(decomp_before.velocity) : null
      result.pre_met_decomp_t = decomp_before.time != null ? parseFloat(decomp_before.time) : null
      result.pre_met_decomp_dist = decomp_before.distance != null ? parseFloat(decomp_before.distance) : null

      // 储后
      result.pst_met_decomp_mode = metering.post_decompress_mode != null ? parseInt(metering.post_decompress_mode) : null
      result.pst_met_decomp_pres = decomp_after.pressure != null ? parseFloat(decomp_after.pressure) : null
      result.pst_met_decomp_spd = decomp_after.velocity != null ? parseFloat(decomp_after.velocity) : null
      result.pst_met_decomp_t = decomp_after.time != null ? parseFloat(decomp_after.time) : null
      result.pst_met_decomp_dist = decomp_after.distance != null ? parseFloat(decomp_after.distance) : null
    }

    result.met_lim_t = metering.delay_time != null ? parseFloat(metering.delay_time) : null
    result.met_end_pos = metering.ending_position != null ? parseFloat(metering.ending_position) : null
  }

  // --- 料筒温度 (barrel_temperature) ---
  const barrel_temperature = setting_process.barrel_temperature
  if (barrel_temperature) {
    result.brl_temp_stg = barrel_temperature.stage

    const temp_row = barrel_temperature.table_data[0]
    if (temp_row) {
      // noz_temp = nozzle temperature (第 0 段)
      result.noz_temp = temp_row.sections[0] != null ? parseFloat(temp_row.sections[0]) : null

      // brl_temp_1 ~ brl_temp_9 对应 sections[1] 到 sections[9]
      for (let i = 1; i <= 9; i++) {
        const value = temp_row.sections[i]
        result[`brl_temp_${i}`] = value != null ? parseFloat(value) : null
      }
    }
  }

  return result
}

/**
 * 将后端扁平参数对象转换为前端 structured setting_process_form 格式
 * 字段命名与后端 schemas.py 保持一致（使用缩写命名如 inj_spd_1）
 * sections 数组长度严格等于 max_stage，未使用位置填充 null
 * @param {Object} backend_data - 后端返回的扁平参数对象
 * @returns {Object} 结构化的前端表单数据
 */
export function transformBackendToSettingProcess(backend_data: any) {
  const data = backend_data || {}

  const parseNumber = (value: any): number | null => {
    if (value == null || value === "") return null
    const num = parseFloat(value)
    return isNaN(num) ? null : num
  }

  // 提取并填充段数据（使用 1-based 索引）
  const extractAndPadSections = (
    prefix: string,
    stage: number,
    max_stage: number
  ): (number | null)[] => {
    const sections: (number | null)[] = []
    for (let i = 1; i <= stage; i++) {
      sections.push(parseNumber(data[`${prefix}${i}`]))
    }
    while (sections.length < max_stage) {
      sections.push(null)
    }
    return sections
  }

  // 构建料筒温度 sections（nozzle 在 sections[0]）
  const constructBarrelTemperatureSections = (
    stage: number,
    max_stage: number
  ): (number | null)[] => {
    const sections: (number | null)[] = new Array(max_stage).fill(null)
    sections[0] = parseNumber(data.noz_temp) // nozzle
    for (let i = 1; i < stage; i++) {
      sections[i] = parseNumber(data[`brl_temp_${i}`])
    }
    return sections
  }

  const inj_stages = data.inj_stg != null ? parseInt(data.inj_stg, 10) : 1
  const hold_stages = data.hold_stg != null ? parseInt(data.hold_stg, 10) : 1
  const met_stages = data.met_stg != null ? parseInt(data.met_stg, 10) : 1
  const brl_temp_stages = data.brl_temp_stg != null ? parseInt(data.brl_temp_stg, 10) : 1

  return {
    injection: {
      max_stage: 6,
      stage: inj_stages,
      table_data: [
        { label: "压力", unit: "MPa", sections: extractAndPadSections("inj_pres_", inj_stages, 6) },
        { label: "速度", unit: "mm/s", sections: extractAndPadSections("inj_spd_", inj_stages, 6) },
        { label: "位置", unit: "mm", sections: extractAndPadSections("inj_pos_", inj_stages, 6) }
      ],
      injection_time: parseNumber(data.inj_t),
      delay_time: parseNumber(data.inj_dly_t),
      cooling_time: parseNumber(data.cool_t)
    },

    vp_switch: {
      mode: data.vps_mode != null ? parseInt(data.vps_mode, 10) : null,
      position: parseNumber(data.vps_pos),
      time: parseNumber(data.vps_t),
      pressure: parseNumber(data.vps_pres),
      velocity: parseNumber(data.vps_spd)
    },

    holding: {
      max_stage: 5,
      stage: hold_stages,
      table_data: [
        { label: "压力", unit: "MPa", sections: extractAndPadSections("hold_pres_", hold_stages, 5) },
        { label: "速度", unit: "mm/s", sections: extractAndPadSections("hold_spd_", hold_stages, 5) },
        { label: "时间", unit: "s", sections: extractAndPadSections("hold_t_", hold_stages, 5) }
      ]
    },

    metering: {
      max_stage: 4,
      stage: met_stages,
      table_data: [
        { label: "压力", unit: "MPa", sections: extractAndPadSections("met_pres_", met_stages, 4) },
        { label: "螺杆转速", unit: "rpm", sections: extractAndPadSections("met_rot_spd_", met_stages, 4) },
        { label: "背压", unit: "MPa", sections: extractAndPadSections("met_back_pres_", met_stages, 4) },
        { label: "位置", unit: "mm", sections: extractAndPadSections("met_pos_", met_stages, 4) }
      ],
      pre_decompress_mode: data.pre_met_decomp_mode != null ? parseInt(data.pre_met_decomp_mode, 10) : null,
      post_decompress_mode: data.pst_met_decomp_mode != null ? parseInt(data.pst_met_decomp_mode, 10) : null,
      decompress_table_data: [
        {
          label: "储前",
          pressure: parseNumber(data.pre_met_decomp_pres),
          velocity: parseNumber(data.pre_met_decomp_spd),
          time: parseNumber(data.pre_met_decomp_t),
          distance: parseNumber(data.pre_met_decomp_dist)
        },
        {
          label: "储后",
          pressure: parseNumber(data.pst_met_decomp_pres),
          velocity: parseNumber(data.pst_met_decomp_spd),
          time: parseNumber(data.pst_met_decomp_t),
          distance: parseNumber(data.pst_met_decomp_dist)
        }
      ],
      delay_time: parseNumber(data.met_lim_t),
      ending_position: parseNumber(data.met_end_pos)
    },

    barrel_temperature: {
      max_stage: 10,
      stage: brl_temp_stages,
      table_data: [
        {
          label: "温度", unit: "℃",
          sections: constructBarrelTemperatureSections(brl_temp_stages, 10)
        }
      ]
    }
  }
}


function processValueConversion(
  input: any = null,
  curr_injt: any = null,
  conv_injt: any = null,
  conv_type: any = null
) {
  if (!input) return null

  if (["injection_pressure", "pressure"].includes(conv_type)) {
    // 注射压力数值转换
    if (curr_injt.max_set_injection_pressure 
            && curr_injt.max_injection_pressure
            && conv_injt.max_set_injection_pressure 
            && conv_injt.max_injection_pressure) {
      return (input * (conv_injt.max_set_injection_pressure / curr_injt.max_set_injection_pressure) 
                * (curr_injt.max_injection_pressure / conv_injt.max_injection_pressure)).toFixed(2)
    }
  } else if (["injection_velocity", "velocity"].includes(conv_type)) {
    // 注射速度数值转换
    if (curr_injt.max_set_injection_velocity 
            && curr_injt.max_injection_velocity
            && conv_injt.max_set_injection_velocity 
            && conv_injt.max_injection_velocity) {
      return (input * (conv_injt.max_set_injection_velocity / curr_injt.max_set_injection_velocity) 
                * (curr_injt.max_injection_velocity / conv_injt.max_injection_velocity)).toFixed(2)
    }
  } else if (["injection_distance", "position", "metering_position", "decom_position", "ending_position"].includes(conv_type)) {
    // 注射位置计算
    if (curr_injt.screw_diameter 
            && conv_injt.screw_diameter) {
      return (input * (curr_injt.screw_diameter * curr_injt.screw_diameter) 
                / (conv_injt.screw_diameter * conv_injt.screw_diameter)).toFixed(2)
    }
  } else if (conv_type == "holding_pressure") {
    // 保压压力数值转换
    if (curr_injt.max_set_holding_pressure 
            && curr_injt.max_holding_pressure
            && conv_injt.max_set_holding_pressure 
            && conv_injt.max_holding_pressure) {
      return (input * (conv_injt.max_set_holding_pressure / curr_injt.max_set_holding_pressure) 
                * (curr_injt.max_holding_pressure / conv_injt.max_holding_pressure)).toFixed(2)
    } 
  } else if (conv_type == "metering_pressure") {
    // 计量压力数值转换
    if (curr_injt.max_set_metering_pressure 
            && curr_injt.max_metering_pressure
            && conv_injt.max_set_metering_pressure 
            && conv_injt.max_metering_pressure) {
      return (input * (conv_injt.max_set_metering_pressure / curr_injt.max_set_metering_pressure) 
                * (curr_injt.max_metering_pressure / conv_injt.max_metering_pressure)).toFixed(2)
    }
  } else if (conv_type == "metering_screw_rotation") {
    // 计量螺杆转速
    if (curr_injt.screw_diameter 
            && curr_injt.max_set_screw_rotation_speed 
            && curr_injt.max_set_screw_rotation_speed
            && conv_injt.screw_diameter
            && conv_injt.max_screw_rotation_speed 
            && conv_injt.max_screw_rotation_speed) {
      return (input * (curr_injt.screw_diameter / conv_injt.screw_diameter)
                * (conv_injt.max_set_screw_rotation_speed / curr_injt.max_set_screw_rotation_speed) 
                * (curr_injt.max_screw_rotation_speed / conv_injt.max_screw_rotation_speed)).toFixed(2)
    }
  } else if (conv_type == "metering_back_pressure") {
    // 计量压力数值转换
    if (curr_injt.max_set_metering_back_pressure 
            && curr_injt.max_metering_back_pressure
            && conv_injt.max_set_metering_back_pressure 
            && conv_injt.max_metering_back_pressure) {
      return (input * (conv_injt.max_set_metering_back_pressure / curr_injt.max_set_metering_back_pressure) 
                * (curr_injt.max_metering_back_pressure / conv_injt.max_metering_back_pressure)).toFixed(2)
    }
  } else if (conv_type == "decom_pressure") {
    // 储料压力数值转换
    if (curr_injt.max_set_decompression_pressure 
            && curr_injt.max_decompression_pressure
            && conv_injt.max_set_decompression_pressure 
            && conv_injt.max_decompression_pressure) {
      return (input * (conv_injt.max_set_decompression_pressure / curr_injt.max_set_decompression_pressure) 
                * (curr_injt.max_decompression_pressure / conv_injt.max_decompression_pressure)).toFixed(2)
    }
  } else if (conv_type == "decom_velocity") {
    // 储料速度数值转换
    if (curr_injt.max_set_decompression_velocity 
            && curr_injt.max_decompression_velocity
            && conv_injt.max_set_decompression_velocity 
            && conv_injt.max_decompression_velocity) {
      return (input * (conv_injt.max_set_decompression_velocity / curr_injt.max_set_decompression_velocity) 
                * (curr_injt.max_decompression_velocity / conv_injt.max_decompression_velocity)).toFixed(2)
    } 
  }

  return null
}

// 工艺参数转换
export function processTransplantOld(
  o_mac: any,
  o_injt_station: any,
  t_mac: any,
  t_injt_station: any,
) {
  // 读取参数
  const o_proc = o_injt_station.setting_process
  const o_injt = o_injt_station.injection_detail
  const t_proc = t_injt_station.setting_process
  const t_injt = t_injt_station.injection_detail

  /* 注射参数 */
  const inject_para_array = [
    "injection_pressure", // 注射压力
    "injection_velocity", // 注射速度
    "injection_distance", // 注射位置
  ]
  // 注射段数
  t_proc.injection.stage = o_proc.injection.stage
  for (let row = 0; row < 3; ++row)
    for (let col = 0; col < t_proc.injection.stage; ++col) {
      // 注射参数
      t_proc.injection.table_data[row].sections[col] = processValueConversion(
        o_proc.injection.table_data[row].sections[col], 
        o_injt,
        t_injt,
        inject_para_array[row]
      )
    }
    // 注射时间
  t_proc.injection.injection_time = o_proc.injection.injection_time
  // 注射延迟时间
  t_proc.injection.delay_time = o_proc.injection.delay_time
  // 冷却时间
  t_proc.injection.cooling_time = o_proc.injection.cooling_time

  /* vp切换参数 */
  // vp切换参数
  t_proc.vp_switch.mode = o_proc.vp_switch.mode
  // vp切换位置设定为最大螺杆行程的20%, 或者是由工程师自主设定
  t_proc.vp_switch.position = processValueConversion(
    o_proc.vp_switch.position,
    o_injt,
    t_injt,
    "position"
  )
  // vp切换时间
  t_proc.vp_switch.time = o_proc.vp_switch.time
  // vp切换压力
  t_proc.vp_switch.pressure = processValueConversion(
    o_proc.vp_switch.pressure,
    o_injt,
    t_injt,
    "pressure"
  )
  // vp切换速度
  t_proc.vp_switch.velocity = processValueConversion(
    o_proc.vp_switch.velocity, 
    o_injt,
    t_injt,
    "velocity"
  )

  /* 保压参数 */
  // 保压段数
  t_proc.holding.stage = o_proc.holding.stage
  for (let row = 0; row < 3; ++row)
    for (let col = 0; col < t_proc.holding.stage; ++col) {
      if (row == 0) {
        // 保压压力
        t_proc.holding.table_data[row].sections[col] = processValueConversion(
          o_proc.holding.table_data[row].sections[col], 
          o_injt,
          t_injt,
          "holding_pressure"
        )
      } else if (row == 1) {
        if (!t_injt.max_set_holding_velocity) return null
        // 保压速度 设定为注塑机最大可设定的30%
        t_proc.holding.table_data[row].sections[col] = (t_injt.max_set_holding_velocity * 0.3).toFixed(2)
      } else if (row == 2) {
        // 保压时间
        t_proc.holding.table_data[row].sections[col] = o_proc.holding.table_data[row].sections[col]
      }

    }

  /* 计量参数 */
  const metering_para_array = [
    "metering_pressure",
    "metering_screw_rotation",
    "metering_back_pressure",
    "metering_position"
  ]
  // 计量段数
  t_proc.metering.stage = o_proc.metering.stage
  for (let row = 0; row < 4; ++row)
    for (let col = 0; col < t_proc.metering.stage; ++col) {
      if (row == 0) {
        // 计量压力
        if (o_mac.drive_system == "电动机") {
          if (["液压机", "油压", "油电混", "电动/油压"].includes(t_mac.drive_system)) {
            if (!t_mac.max_metering_pressure) return null
            // 全电转液压时,需要设定计量压力,75%*最大计量压力
            t_proc.metering.table_data[row].sections[col] = (t_mac.max_metering_pressure * 0.75).toFixed(2)
          } else {
            // 全电机无计量压力
            t_proc.metering.table_data[row].sections[col] = null
          }
        } else {
          if (["液压机", "油压", "油电混", "电动/油压"].includes(t_mac.drive_system)) {
            // 液压转液压时,正常压力公式转换
            t_proc.metering.table_data[row].sections[col] = processValueConversion(
              o_proc.metering.table_data[row].sections[col], 
              o_injt,
              t_injt,
              metering_para_array[row]
            )
          } else {
            // 全电机无计量压力
            t_proc.metering.table_data[row].sections[col] = null
          }
        }
      } else {
        // 其它计量参数
        t_proc.metering.table_data[row].sections[col] = processValueConversion(
          o_proc.metering.table_data[row].sections[col], 
          o_injt,
          t_injt,
          metering_para_array[row]
        )
      }
    }
    
  // 计量前储料模式
  t_proc.metering.pre_decompress_mode = o_proc.metering.pre_decompress_mode
  // 计量后储料模式
  t_proc.metering.post_decompress_mode = o_proc.metering.post_decompress_mode
  for (let row = 0; row < 2; ++row) {
    // 储料压力
    t_proc.metering.decompress_table_data[row].pressure = processValueConversion(
      o_proc.metering.decompress_table_data[row].pressure, 
      o_injt,
      t_injt,
      "decom_pressure"
    )
    // 储料速度
    t_proc.metering.decompress_table_data[row].velocity = processValueConversion(
      o_proc.metering.decompress_table_data[row].velocity, 
      o_injt,
      t_injt,
      "decom_velocity"
    )
    // 储料位置
    t_proc.metering.decompress_table_data[row].distance = processValueConversion(
      o_proc.metering.decompress_table_data[row].distance, 
      o_injt,
      t_injt,
      "decom_position"
    )
    // 储料时间
    t_proc.metering.decompress_table_data[row].time = o_proc.metering.decompress_table_data[row].time
  }
  // 储料延迟
  t_proc.metering.delay_time = o_proc.metering.delay_time
  // 储料终止位置
  t_proc.metering.ending_position = processValueConversion(
    o_proc.metering.ending_position, 
    o_injt,
    t_injt,
    "ending_position"
  )

  /*  料筒温度 */
  if (Number(o_proc.barrel_temperature.stage) > Number(t_injt.max_stage)) {
    // 料筒温度段数
    t_proc.barrel_temperature.stage = t_injt.max_stage
    // 目标机台的料筒温度段数少于当前机台，需要进行线性拟合
    const last = Number(o_proc.barrel_temperature.stage) - 1
    const interval = Number(t_proc.barrel_temperature.stage) - 1 - 1
    const step = (o_proc.barrel_temperature.table_data[0].sections[1] - o_proc.barrel_temperature.table_data[0].sections[last]) / interval
    // 喷嘴温度
    t_proc.barrel_temperature.table_data[0].sections[0] = o_proc.barrel_temperature.table_data[0].sections[0]
    // 料筒温度
    for (let col = 1; col < 10; ++col) {
      if (col < t_injt.max_stage) {
        t_proc.barrel_temperature.table_data[0].sections[col] = o_proc.barrel_temperature.table_data[0].sections[1] - (col - 1) * step
      } else {
        t_proc.barrel_temperature.table_data[0].sections[col] = null
      }
    }
  } else {
    // 料筒温度段数
    t_proc.barrel_temperature.stage = o_proc.barrel_temperature.stage
    // 喷嘴&料筒温度
    for (let col = 0; col < 10; ++col) {
      if (col < t_proc.barrel_temperature.stage) {
        t_proc.barrel_temperature.table_data[0].sections[col] = o_proc.barrel_temperature.table_data[0].sections[col]
      } else {
        t_proc.barrel_temperature.table_data[0].sections[col] = null
      }
    }
  }
}


// ========== 工具函数 ==========
const is_valid_number = (val: any): val is number => typeof val === "number" && !isNaN(val) && isFinite(val)

const get_drive_type_category = (drive_system: string): "electric" | "hydraulic" => {
  if (!drive_system) return "hydraulic"
  const electric_keywords = ["电动机", "全电"]
  const hydraulic_keywords = ["液压机", "油压", "油电混", "电动/油压"]
  if (electric_keywords.some(kw => drive_system.includes(kw))) return "electric"
  if (hydraulic_keywords.some(kw => drive_system.includes(kw))) return "hydraulic"
  return "hydraulic" // 默认
}

// 通用比例转换：适用于压力、速度等需双重归一化的参数
const convert_ratio_value = (
  input: number | null,
  curr_injt: any,
  conv_injt: any,
  max_set_key: string,
  max_key: string,
): string | null => {
  if (input == null || !is_valid_number(input)) return null
  
  const curr_max_set = curr_injt[max_set_key]
  const curr_max = curr_injt[max_key]
  const conv_max_set = conv_injt[max_set_key]
  const conv_max = conv_injt[max_key]

  if (!is_valid_number(curr_max_set) || !is_valid_number(curr_max) ||
      !is_valid_number(conv_max_set) || !is_valid_number(conv_max) ||
      curr_max_set === 0 || conv_max === 0) {
    return null
  }

  const ratio = (conv_max_set / curr_max_set) * (curr_max / conv_max)
  return (input * ratio).toFixed(2)
}

// 螺杆面积比转换（位置类）
const convert_position_by_screw = (
  input: number | null,
  curr_injt: any,
  conv_injt: any
): string | null => {
  if (input == null || !is_valid_number(input)) return null
  
  const curr_d = curr_injt.screw_diameter
  const conv_d = conv_injt.screw_diameter

  if (!is_valid_number(curr_d) || !is_valid_number(conv_d) || conv_d === 0) {
    return null
  }

  return (input * (curr_d * curr_d) / (conv_d * conv_d)).toFixed(2)
}

// 螺杆转速特殊转换
const convert_screw_rotation = (
  input: number | null,
  curr_injt: any,
  conv_injt: any
): string | null => {
  if (input == null || !is_valid_number(input)) return null

  const { screw_diameter: curr_d, max_set_screw_rotation_speed: curr_max_set, max_screw_rotation_speed: curr_max } = curr_injt
  const { screw_diameter: conv_d, max_set_screw_rotation_speed: conv_max_set, max_screw_rotation_speed: conv_max } = conv_injt

  if (!is_valid_number(curr_d) || !is_valid_number(conv_d) || conv_d === 0 ||
      !is_valid_number(curr_max_set) || !is_valid_number(curr_max) ||
      !is_valid_number(conv_max_set) || !is_valid_number(conv_max) || conv_max === 0) {
    return null
  }

  const ratio = (curr_d / conv_d) * (conv_max_set / curr_max_set) * (curr_max / conv_max)
  return (input * ratio).toFixed(2)
}

// ========== 参数转换主函数 ==========
export function processTransplant(origin_process: any,target_process: any,): void {

  const o_proc = origin_process.parameter.setting_process
  const o_injt = origin_process.condition.injection_unit
  const t_proc = target_process.parameter.setting_process
  const t_injt = target_process.condition.injection_unit
  console.log("原机台参数：", o_proc, o_injt)
  const o_drive = get_drive_type_category(origin_process.condition.machine_info.drive_system)
  const t_drive = get_drive_type_category(target_process.condition.machine_info.drive_system)

  console.log("开始进行参数转换")
  // --- 注射参数 ---
  t_proc.injection.stage = Math.min(o_proc.injection.stage, t_proc.injection.max_stage)
  const injection_types = ["injection_pressure", "injection_speed", "injection_distance"] as const
  for (let row = 0; row < injection_types.length; row++) {
    for (let col = 0; col < t_proc.injection.stage; col++) {
      const src_val = o_proc.injection.table_data[row].sections[col]
      let converted: string | null = null

      if (injection_types[row] === "injection_pressure") {
        converted = convert_ratio_value(src_val, o_injt, t_injt,
          "max_set_injection_pressure", "max_injection_pressure",
        )
      } else if (injection_types[row] === "injection_speed") {
        converted = convert_ratio_value(src_val, o_injt, t_injt,
          "max_set_injection_speed", "max_injection_speed",
        )
      } else if (injection_types[row] === "injection_distance") {
        converted = convert_position_by_screw(src_val, o_injt, t_injt)
      }

      t_proc.injection.table_data[row].sections[col] = converted ? parseFloat(converted) : null
    }
  }
  t_proc.injection.injection_time = o_proc.injection.injection_time
  t_proc.injection.delay_time = o_proc.injection.delay_time
  t_proc.injection.cooling_time = o_proc.injection.cooling_time

  // --- VP 切换 ---
  console.log("开始进行VP切换参数转换")
  t_proc.vp_switch.mode = o_proc.vp_switch.mode
  t_proc.vp_switch.position = convert_position_by_screw(o_proc.vp_switch.position, o_injt, t_injt)
  t_proc.vp_switch.time = o_proc.vp_switch.time
  t_proc.vp_switch.pressure = convert_ratio_value(o_proc.vp_switch.pressure, o_injt, t_injt,
    "max_set_injection_pressure", "max_injection_pressure",
  ) ? parseFloat(convert_ratio_value(o_proc.vp_switch.pressure, o_injt, t_injt,
    "max_set_injection_pressure", "max_injection_pressure",
  )!) : null
  t_proc.vp_switch.velocity = convert_ratio_value(o_proc.vp_switch.velocity, o_injt, t_injt,
    "max_set_injection_speed", "max_injection_speed",
  ) ? parseFloat(convert_ratio_value(o_proc.vp_switch.velocity, o_injt, t_injt,
    "max_set_injection_speed", "max_injection_speed",
  )!) : null

  // --- 保压参数 ---
  console.log("开始进行保压参数转换")
  t_proc.holding.stage = Math.min(o_proc.holding.stage, t_proc.holding.max_stage)
  for (let col = 0; col < t_proc.holding.stage; col++) {
    // 压力
    t_proc.holding.table_data[0].sections[col] = convert_ratio_value(
      o_proc.holding.table_data[0].sections[col], o_injt, t_injt,
      "max_set_holding_pressure", "max_holding_pressure",
    ) ? parseFloat(convert_ratio_value(
      o_proc.holding.table_data[0].sections[col], o_injt, t_injt,
      "max_set_holding_pressure", "max_holding_pressure",
    )!) : null

    // 速度：固定为最大设定值的 30%
    const o_holding_speed = o_proc.holding.table_data[1].sections[col]
    if (o_holding_speed && is_valid_number(t_injt.max_set_holding_speed)) {
      t_proc.holding.table_data[1].sections[col] = (t_injt.max_set_holding_speed * 0.3).toFixed(2)
    } else {
      t_proc.holding.table_data[1].sections[col] = null
    }

    // 时间：直接复制
    t_proc.holding.table_data[2].sections[col] = o_proc.holding.table_data[2].sections[col]
  }

  // --- 计量参数 ---
  console.log("开始进行计量参数转换")
  t_proc.metering.stage = Math.min(o_proc.metering.stage, t_proc.metering.max_stage)
  for (let col = 0; col < t_proc.metering.stage; col++) {
    // 压力：根据驱动类型特殊处理
    if (o_drive === "electric" && t_drive === "hydraulic") {
      t_proc.metering.table_data[0].sections[col] = t_injt.max_metering_pressure ?
        (t_injt.max_metering_pressure * 0.75).toFixed(2) : null
    } else if (o_drive === "hydraulic" && t_drive === "hydraulic") {
      t_proc.metering.table_data[0].sections[col] = convert_ratio_value(
        o_proc.metering.table_data[0].sections[col], o_injt, t_injt,
        "max_set_metering_pressure", "max_metering_pressure",
      ) ? parseFloat(convert_ratio_value(
        o_proc.metering.table_data[0].sections[col], o_injt, t_injt,
        "max_set_metering_pressure", "max_metering_pressure",
      )!) : null
    } else {
      // 全电机无计量压力
      t_proc.metering.table_data[0].sections[col] = null
    }

    // 螺杆转速
    t_proc.metering.table_data[1].sections[col] = convert_screw_rotation(
      o_proc.metering.table_data[1].sections[col], o_injt, t_injt
    ) ? parseFloat(convert_screw_rotation(
      o_proc.metering.table_data[1].sections[col], o_injt, t_injt
    )!) : null

    // 背压
    t_proc.metering.table_data[2].sections[col] = convert_ratio_value(
      o_proc.metering.table_data[2].sections[col], o_injt, t_injt,
      "max_set_metering_back_pressure", "max_metering_back_pressure",
    ) ? parseFloat(convert_ratio_value(
      o_proc.metering.table_data[2].sections[col], o_injt, t_injt,
      "max_set_metering_back_pressure", "max_metering_back_pressure",
    )!) : null

    // 位置
    t_proc.metering.table_data[3].sections[col] = convert_position_by_screw(
      o_proc.metering.table_data[3].sections[col], o_injt, t_injt
    ) ? parseFloat(convert_position_by_screw(
      o_proc.metering.table_data[3].sections[col], o_injt, t_injt
    )!) : null
  }

  // --- 储料参数 ---
  t_proc.metering.pre_decompress_mode = o_proc.metering.pre_decompress_mode
  t_proc.metering.post_decompress_mode = o_proc.metering.post_decompress_mode

  for (let i = 0; i < 2; i++) {
    t_proc.metering.decompress_table_data[i].pressure = convert_ratio_value(
      o_proc.metering.decompress_table_data[i].pressure, o_injt, t_injt,
      "max_set_decompression_pressure", "max_decompression_pressure",
    ) ? parseFloat(convert_ratio_value(
      o_proc.metering.decompress_table_data[i].pressure, o_injt, t_injt,
      "max_set_decompression_pressure", "max_decompression_pressure",
    )!) : null

    t_proc.metering.decompress_table_data[i].velocity = convert_ratio_value(
      o_proc.metering.decompress_table_data[i].velocity, o_injt, t_injt,
      "max_set_decompression_speed", "max_decompression_speed",
    ) ? parseFloat(convert_ratio_value(
      o_proc.metering.decompress_table_data[i].velocity, o_injt, t_injt,
      "max_set_decompression_speed", "max_decompression_speed",
    )!) : null

    t_proc.metering.decompress_table_data[i].distance = convert_position_by_screw(
      o_proc.metering.decompress_table_data[i].distance, o_injt, t_injt
    ) ? parseFloat(convert_position_by_screw(
      o_proc.metering.decompress_table_data[i].distance, o_injt, t_injt
    )!) : null

    t_proc.metering.decompress_table_data[i].time = o_proc.metering.decompress_table_data[i].time
  }

  t_proc.metering.delay_time = o_proc.metering.delay_time
  t_proc.metering.ending_position = convert_position_by_screw(o_proc.metering.ending_position, o_injt, t_injt)

  // --- 料筒温度 ---
  console.log("开始进行料筒温度转换")
  const origin_temp_stage = o_proc.barrel_temperature.stage
  const target_max_stage = t_proc.barrel_temperature.max_stage
  t_proc.barrel_temperature.stage = Math.min(origin_temp_stage, target_max_stage)

  // 复制 nozzle 温度
  t_proc.barrel_temperature.table_data[0].sections[0] = o_proc.barrel_temperature.table_data[0].sections[0]

  if (origin_temp_stage <= target_max_stage) {
    // 直接复制，多余补 null
    for (let i = 1; i < target_max_stage; i++) {
      t_proc.barrel_temperature.table_data[0].sections[i] = i < origin_temp_stage
        ? o_proc.barrel_temperature.table_data[0].sections[i]
        : null
    }
  } else {
    // 需要线性插值（从第1段到最后一段）
    const start_temp = o_proc.barrel_temperature.table_data[0].sections[1] // BT1
    const end_temp = o_proc.barrel_temperature.table_data[0].sections[origin_temp_stage - 1] // 最后一段
    const segment_count = target_max_stage - 1 // 不含 nozzle

    for (let i = 1; i < target_max_stage; i++) {
      const ratio = (i - 1) / (segment_count - 1) // 0 ~ 1
      t_proc.barrel_temperature.table_data[0].sections[i] = start_temp + (end_temp - start_temp) * ratio
    }
  }

  // 补全剩余为 null（确保长度 = max_stage）
  for (let i = target_max_stage; i < 10; i++) {
    t_proc.barrel_temperature.table_data[0].sections[i] = null
  }
}