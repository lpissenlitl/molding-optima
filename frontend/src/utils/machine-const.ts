export const injectionUnitForm = {
  title: "部件1",
  name: "1",
  id: null,
  serial_no: null,
  // 喷嘴参数
  nozzle_type: null,
  nozzle_protrusion: null,
  nozzle_hole_diameter: null,
  nozzle_sphere_diameter: null,
  nozzle_force: null,
  // 螺杆、料筒、油缸参数
  screw_type: null,
  screw_diameter: null,
  screw_length: null,
  screw_length_diameter_ratio: null,
  screw_compression_ratio: null,
  plasticizing_capacity: null,
  // barrel_heating_sections: null,
  barrel_heating_power: null,
  max_injection_volume: null,
  max_injection_weight: null,
  max_injection_stroke: null,
  // 
  cylinder_numer:null,
  cylinder_diameter: null,
  use_small_size: null,
  piston_rod_diameter: null,
  cylinder_area: null,
  intensification_ratio: null,
  // 成型参数
  max_injection_pressure: null,
  max_injection_velocity: null,
  max_holding_pressure: null,
  max_holding_velocity: null,
  max_metering_pressure: null,
  max_screw_rotation_speed: null,
  max_metering_back_pressure: null,
  max_decompression_pressure: null,
  max_decompression_velocity: null,

  max_injection_rate: null,
  max_holding_rate: null,
  max_decompression_rate: null,
  max_screw_linear_velocity: null,
  screw_area: null,
  screw_circumference: null,

  max_ejector_forward_velocity: null,
  max_ejector_backward_velocity: null,
  max_mold_opening_velocity: null,
  max_mold_clamping_velocity: null,
  // 注塑机界面最大可设定参数
  max_set_ejector_forward_velocity: null,
  max_set_ejector_backward_velocity: null,
  max_set_mold_opening_velocity: null,
  max_set_mold_clamping_velocity: null,
  max_set_injection_pressure: null,
  max_set_injection_velocity: null,
  max_set_holding_pressure: null,
  max_set_holding_velocity: null,
  max_set_metering_pressure: null,
  max_set_screw_rotation_speed: null,
  max_set_metering_back_pressure: null,
  max_set_decompression_pressure: null,
  max_set_decompression_velocity: null,

  max_opening_and_clamping_stage: null,
  max_ejector_stage: null,
}

export const injectionMachineForm = {
  company_id: null,
  id: null,
  // --- 基本信息 ---
  manufacturer: null,
  trademark: null,
  machine_type: "单色注塑机",
  manufacturing_date: null,
  data_source: "",
  asset_no: null,
  serial_no: null,
  internal_id: null,
  communication_interface: 0,
  agreement: "",
  // 操作界面单位
  pressure_unit: "MPa",
  backpressure_unit: "MPa",
  velocity_unit: "mm/s",
  temperature_unit: "℃",
  time_unit: "s",
  position_unit: "mm",
  clamping_force_unit: "Ton",
  screw_rotation_unit: "rpm",
  power_unit: "KW",
  // --- 注射单元 ---
  injection_units: [
    structuredClone(injectionUnitForm)
  ],
  // 模版参数
  platen_size_horizon: null,
  platen_size_vertical: null,
  min_mold_size_horizon: null,
  min_mold_size_vertical: null,
  max_mold_size_horizon: null,
  max_mold_size_vertical: null,
  min_mold_thickness: null,
  max_mold_thickness: null,
  min_platen_opening: null,
  max_platen_opening: null,
  locate_ring_diameter: null,
  // 拉杆参数
  pull_rod_size: null,
  pull_rod_diameter: null,
  pull_rod_distance_horizon: null,
  pull_rod_distance_vertical: null,
  // 开合模参数
  clamping_method: null,
  max_clamping_force: null,
  max_mold_open_stroke: null,
  // 顶出参数
  max_ejection_force: null,
  max_ejection_stroke: null,
  ejection_hole_num: null,
  max_thimble_forward_speed: null,
  max_thimble_back_speed: null,
  // 动力/电热
  hydraulic_system_pressure: null,
  motor_power: null,
  heater_power: null,
  temp_control_zone_num: null,
  main_power: null,
  power_method: null,
  propulsion_axis: null,
  // 其他
  machine_weight: null,
  size_length: null,
  size_width: null,
  size_height: null,
  hopper_capacity: null,
  core_pulling: null,
  needle_core: null,
  response_time: null,
  enhancement_ratio: null,
  manufacture_date: null,
  manufacture_no: null,
  remark: null
}

export const machineDatasourceOptions = [
  { data_source: 0, provider: "内部" },
  // { data_source: 1, provider: 'TKP' },
  // { data_source: 2, provider: '联兴' },
  // { data_source: 3, provider: '良锋' },
  // { data_source: 4, provider: '双宇' },
  // { data_source: 5, provider: '普天' },
  // { data_source: 6, provider: '运兴' },
  // { data_source: 7, provider: '周永盛' },
  // { data_source: 8, provider: '精美' },
]

// 注塑机类别
export const machineTypeOptions = [
  { value: "单色", label: "单色注塑机" },
  { value: "双色", label: "双色注塑机" },
  // { value: "三色", label: "三色注塑机" },
  // { value: "四色", label: "四色注塑机" },
  // { value: "五色", label: "五色注塑机" },
  // { value: "六色", label: "六色注塑机" },
  // { value: "七色", label: "七色注塑机" },
]

// 注塑机品牌
export const machineManufacturerOptions = [
  { value: "阿博格", label: "阿博格" },
  { value: "恩格尔", label: "恩格尔" },
  { value: "克劳斯玛菲", label: "克劳斯玛菲" },
  { value: "海天", label: "海天" },
  { value: "伊之密", label: "伊之密" },
  { value: "德玛格", label: "德玛格" },
  { value: "日精", label: "日精" },
  { value: "日钢", label: "日钢" },
  { value: "发那科", label: "发那科" },
  { value: "东芝", label: "东芝" },
  { value: "三菱", label: "三菱" },
  { value: "住友", label: "住友" },
  { value: "震雄", label: "震雄" },
  { value: "华大", label: "华大" },
  { value: "震德", label: "震德" },
  { value: "博创", label: "博创" },
  { value: "宏大", label: "宏大" },
  { value: "海泰", label: "海泰" },
  { value: "精力", label: "精力" },
  { value: "力马", label: "力马" },
  { value: "宏太", label: "宏太" },
  { value: "海星", label: "海星" },
  { value: "柳塑", label: "柳塑" },
  { value: "申达", label: "申达" },
  { value: "三元", label: "三元" },
  { value: "海明", label: "海明" },
  { value: "海雄", label: "海雄" },
]

// 注塑机类型（驱动方式）
export const machinePowerMethodOptions = [
  { value: "电动机", label: "电动机" },
  { value: "液压机", label: "液压机" },
]

// 注塑机类型（推进轴线）
export const machinePropulsionAxisOptions = [
  { value: "卧式", label: "卧式" },
  { value: "立式", label: "立式" },
  { value: "角式", label: "角式" },
]

// 注塑机界面压力单位
export const presUnitOptions = [
  { value: "MPa", label: "MPa" },
  { value: "kgf/cm²", label: "kgf/cm²" },
  { value: "bar", label: "bar" },
  { value: "PSI", label: "PSI" }
]

// 开合模/顶针压力单位
export const openingAndClampingMoldPresUnitOptions = [
  { value: "MPa", label: "MPa" },
  { value: "kgf/cm²", label: "kgf/cm²" },
  { value: "bar", label: "bar" },
  { value: "PSI", label: "PSI" },
  { value: "%", label: "%" },
]

// 注塑机界面速度单位
export const veloUnitOptions = [
  { value: "mm/s",  label: "mm/s" },
  { value: "%",  label: "%" },
  { value: "inch/s",  label: "inch/s" },
  { value: "cm³/s",  label: "cm³/s" },
  { value: "inch³/s",  label: "inch³/s" },
]

// 开合模/顶针速度单位
export const openingAndClampingMoldVeloUnitOptions = [
  { value: "mm/s",  label: "mm/s" },
  { value: "%",  label: "%" },
  { value: "inch/s",  label: "inch/s" }
]
// 注塑机界面温度单位
export const tempUnitOptions = [
  { value: "℃",  label: "℃" },
  { value: "℉",  label: "℉" }
]

// 注塑机界面时间单位
export const timeUnitOptions = [
  { value: "s",  label: "s" }
]

// 注塑机界面位置单位
export const posiUnitOptions = [
  { value: "mm",  label: "mm" },
  { value: "inch",  label: "inch" },
  { value: "cm³",  label: "cm³" },
  { value: "inch³",  label: "inch³" },
]

// 注塑机界面锁模力单位
export const clfcUnitOptions = [
  { value: "KN",  label: "KN" },
  { value: "Ton",  label: "Ton" }
]

// 注塑机界面螺杆转速单位
export const rotationUnitOptions = [
  { value: "rpm",  label: "rpm" },
  { value: "mm/s",  label: "mm/s" },
  { value: "%",  label: "%" },
  { value: "cm/s",  label: "cm/s" },
  { value: "m/min",  label: "m/min" },
  { value: "m/s",  label: "m/s" },
  { value: "inch/s",  label: "inch/s" },
]

// 注塑机界面功率单位
export const powerUnitOptions = [
  { value: "KW",  label: "KW" }
]

//最大注射重量单位
export const EjectionAmountUnitOptions = [
  { value: "cm³",  label: "cm³" },
  { value: "(PS)g",  label: "(PS)g" }
]
// 注塑机喷嘴孔直径
export const nozzleHoleDiameterOptions = [
  { label: "3", value: 3 },
  { label: "4", value: 4 },
  { label: "5", value: 5 },
  { label: "6", value: 6 },
  { label: "8", value: 8 },
  { label: "10", value: 10 },  
  { label: "12", value: 12 },
  { label: "14", value: 14 } 
]

// 注塑机喷嘴球半径
export const nozzleSphereDiameterOptions = [
  { label: "12.5", value: 12.5 },
  { label: "15.5", value: 15.5 },
  { label: "20", value: 20 },
  { label: "25", value: 25 },
  { label: "40", value: 40 },
  { label: "90", value: 90 }
]

// 辅机类别
export const auxiliaryTypeOptions = [
  { label: "干燥机", value: "干燥机" },
  { label: "热流道", value: "热流道" },
  { label: "模温机", value: "模温机" },
  { label: "色母机", value: "色母机" }
]

// 辅机厂商
export const auxiliaryManuOptions = [
  { label: "信易", value: "信易" }
]