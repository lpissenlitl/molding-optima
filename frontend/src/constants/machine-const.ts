export const auxiliaryForm = {
  id: null,
  equipment_name: null,
  device_no: null,
  total_count: null,
  avaliable_count: null,
  remarks: null,
}

export const injectionUnitForm = {
  id: null,
  unit_code: null,
  // 喷嘴参数
  nozzle_type: null,
  nozzle_hole_diameter: null,
  nozzle_sphere_radius: null,
  nozzle_protrusion: null,
  nozzle_contact_force: null,
  // 螺杆、料筒、油缸参数
  screw_type: null,
  screw_diameter: null,
  screw_length_to_diameter_ratio: null,
  screw_cross_sectional_area: null,
  screw_compression_ratio: null,
  screw_enhancement_ratio: null,
  plasticizing_capacity: null,
  max_injection_stroke: null,
  max_injection_volume: null,
  max_injection_weight: null,
  barrel_heating_power: null,
  // 设备界面最大可设定段数
  max_injection_stages: null,
  max_holding_stages: null,
  max_metering_stages: null,
  max_temperature_control_zones: null,
  // 设备界面单位
  pressure_unit: "MPa",
  speed_unit: "mm/s",
  position_unit: "mm",
  time_unit: "s",
  back_pressure_unit: "MPa",
  screw_rotation_unit: "rpm",
  temperature_unit: "℃",
  // 成型参数（标准单位）
  max_injection_pressure: null,
  max_injection_speed: null,
  max_holding_pressure: null,
  max_holding_speed: null,
  max_metering_pressure: null,
  max_screw_rotation_speed: null,
  max_metering_back_pressure: null,
  max_decompression_pressure: null,
  max_decompression_speed: null,
  // 设备界面最大可设定成型参数
  max_set_injection_pressure: null,
  max_set_injection_speed: null,
  max_set_holding_pressure: null,
  max_set_holding_speed: null,
  max_set_metering_pressure: null,
  max_set_screw_rotation_speed: null,
  max_set_metering_back_pressure: null,
  max_set_decompression_pressure: null,
  max_set_decompression_speed: null,
}

export const machineInfoForm = {
  id: null,
  // 基本信息
  device_no: null,
  brand: null,
  manufacturer: null,
  model: null,
  location: null,
  machine_type: null,
  drive_system: null,
  unit_count: 1,
  asset_no: null,
  // 设备通讯
  controller_model: null,
  controller_version: null,
  // 设备通讯
  is_comm_enabled: null,
  communication_protocol: null,
  communication_ip: null,
  last_comm_time: null,
  // 操作界面单位
  pressure_unit: "MPa",
  speed_unit: "mm/s",
  position_unit: "mm",
  time_unit: "s",
  back_pressure_unit: "MPa",
  screw_rotation_unit: "rpm",
  temperature_unit: "℃",
  clamping_force_unit: "Ton",
  // 注射单元
  injection_units: [structuredClone(injectionUnitForm)],
  // 模板参数
  // 定模板
  fixed_platen_width: null,
  fixed_platen_height: null,
  fixed_platen_thickness: null,
  locating_hole_diameter: null,
  // 动模板
  moving_platen_width: null,
  moving_platen_height: null,
  moving_platen_thickness: null,
  // 拉杆（哥林柱）
  tie_bar_spacing_width: null,
  tie_bar_spacing_height: null,
  tie_bar_diameter: null,
  tie_bar_count: null,
  // 模板间距（物理极限）
  min_platen_spacing: null,
  max_platen_spacing: null,
  // 容模参数（工程推荐）
  min_mold_length: null,
  max_mold_length: null,
  min_mold_width: null,
  max_mold_width: null,
  min_mold_thickness: null,
  max_mold_thickness: null,
  max_opening_stroke: null,
  // 锁模性能
  clamping_type: null,
  max_clamping_force: null,
  // 顶出系统
  ejection_type: null,
  ejection_mode: null,
  ejection_stroke: null,
  ejection_force: null,
  // 尺寸信息
  size_length: null,
  size_width: null,
  size_height: null,
  machine_weight: null,
  // 能耗参数
  motor_power: null,
  heater_power: null,
  rated_power: null,
  // 日期
  commissioning_date: null,
  manufacture_date: null,
}

// 注塑机制造商（公司实体）
export const injectionMachineManufacturerOptions = [
  { label: "宁波海天塑机集团有限公司", value: "宁波海天塑机集团有限公司" },
  { label: "伊之密股份有限公司", value: "伊之密股份有限公司" },
  { label: "震雄集团", value: "震雄集团" },
  { label: "广东博创智能装备股份有限公司", value: "广东博创智能装备股份有限公司" },
  { label: "Arburg GmbH + Co KG", value: "Arburg GmbH + Co KG" },
  { label: "Engel Austria GmbH", value: "Engel Austria GmbH" },
  { label: "克劳斯玛菲集团（中化国际旗下）", value: "克劳斯玛菲集团（中化国际旗下）" },
  { label: "Fanuc Corporation", value: "Fanuc Corporation" },
  { label: "Nissei Plastic Industrial Co., Ltd.", value: "Nissei Plastic Industrial Co., Ltd." },
  { label: "Japan Steel Works, Ltd. (JSW)", value: "Japan Steel Works, Ltd. (JSW)" },
  { label: "Shibaura Machine Co., Ltd.", value: "Shibaura Machine Co., Ltd." }, // 原东芝机械
  { label: "Mitsubishi Heavy Industries, Ltd.", value: "Mitsubishi Heavy Industries, Ltd." },
  { label: "Sumitomo Heavy Industries, Ltd.", value: "Sumitomo Heavy Industries, Ltd." },
  { label: "宁波华大塑机有限公司", value: "宁波华大塑机有限公司" },
  { label: "广东宏大机械设备有限公司", value: "广东宏大机械设备有限公司" },
  { label: "韩国海泰精密机械", value: "韩国海泰精密机械" },
  { label: "广东力马机械有限公司", value: "广东力马机械有限公司" },
  { label: "柳州塑料机械总厂", value: "柳州塑料机械总厂" },
  { label: "宁波申达塑机有限公司", value: "宁波申达塑机有限公司" },
  { label: "浙江三元注塑机有限公司", value: "浙江三元注塑机有限公司" },
]

// 注塑机品牌（含子品牌）
export const injectionMachineBrandOptions = [
  { label: "海天", value: "海天" },               // Haitian — 主力液压机
  { label: "长飞亚", value: "长飞亚" },           // Zhafir — 海天旗下高端全电机
  { label: "伊之密", value: "伊之密" },           // Yizumi
  { label: "震雄", value: "震雄" },               // Chen Hsong
  { label: "震德", value: "震德" },               // Chen De
  { label: "博创", value: "博创" },               // Borche
  { label: "阿博格", value: "阿博格" },           // Arburg（德国）
  { label: "恩格尔", value: "恩格尔" },           // Engel（奥地利）
  { label: "克劳斯玛菲", value: "克劳斯玛菲" },   // KraussMaffei（德国，现属中化国际）
  { label: "德玛格", value: "德玛格" },           // Demag（原属克劳斯玛菲，现整合）
  { label: "发那科", value: "发那科" },           // Fanuc（日本）
  { label: "日精", value: "日精" },               // Nissei（日本）
  { label: "日钢", value: "日钢" },               // Nisshinbo / JSW（日本）
  { label: "东芝", value: "东芝" },               // Toshiba Machine（现为 Shibaura Machine）
  { label: "三菱", value: "三菱" },               // Mitsubishi Heavy Industries
  { label: "住友", value: "住友" },               // Sumitomo (SHI) Demag（日德合资）
  { label: "华大", value: "华大" },               // Huada（宁波华大）
  { label: "宏大", value: "宏大" },               // Hongda
  { label: "海泰", value: "海泰" },               // Haitai（韩国）
  { label: "力马", value: "力马" },               // Limac（广东力马）
  { label: "申达", value: "申达" },               // Shenda
  { label: "三元", value: "三元" },               // Sanyuan
  { label: "海星", value: "海星" },               // Haixing
  { label: "柳塑", value: "柳塑" },               // Liuzhou Plastic Machinery
]

// 注塑机类型
export const machineTypeOptions = [
  { label: "液压注塑机", value: "液压注塑机" },         // en: Hydraulic Injection Molding Machine
  { label: "全电动注塑机", value: "全电动注塑机" },     // en: All-Electric Injection Molding Machine
  { label: "混合动力注塑机", value: "混合动力注塑机" }, // en: Hybrid (Electro-Hydraulic) Injection Molding Machine
  { label: "多组分注塑机", value: "多组分注塑机" },     // en: Multi-component / Multi-shot Injection Molding Machine
  { label: "立式注塑机", value: "立式注塑机" },         // en: Vertical Injection Molding Machine
  { label: "卧式注塑机", value: "卧式注塑机" },         // en: Horizontal Injection Molding Machine
  { label: "转盘式注塑机", value: "转盘式注塑机" },     // en: Rotary Table / Turntable Injection Molding Machine
  { label: "滑板式注塑机", value: "滑板式注塑机" },     // en: Slide Plate / Shuttle Injection Molding Machine
  { label: "粉末注塑机", value: "粉末注塑机" },         // en: Powder Injection Molding (PIM) Machine
  { label: "微发泡注塑机", value: "微发泡注塑机" },     // en: MuCell / Microcellular Foam Injection Molding Machine
  { label: "高速薄壁注塑机", value: "高速薄壁注塑机" }, // en: High-Speed Thin-Wall Injection Molding Machine
  { label: "大型二板注塑机", value: "大型二板注塑机" }, // en: Large Two-Platen Injection Molding Machine
  { label: "三板注塑机", value: "三板注塑机" },         // en: Three-Platen Injection Molding Machine
]

// 注塑机运行状态
export const machineStatusOptions = [
  { label: "待机", value: "standby" },           // 空闲、通电但未运行
  { label: "试模", value: "mold_trial" },        // 调试模具阶段
  { label: "生产", value: "production" },        // 正常批量生产
  { label: "修机", value: "maintenance" },       // 设备维修中
  { label: "停机", value: "stopped" },           // 主动或计划停机（非故障）
  { label: "故障", value: "fault" },             // 设备报警/异常停机
  { label: "换模", value: "mold_change" },       // 更换模具中（SMED场景）
  { label: "暖机", value: "warm_up" },           // 开机预热、升温阶段
  { label: "清机", value: "cleaning" },          // 清理料筒、螺杆或模具
  { label: "待料", value: "waiting_material" },  // 因缺原料暂停
  { label: "待人", value: "waiting_operator" },  // 等待操作员干预
  { label: "计划停机", value: "scheduled_downtime" }, // 如班次结束、保养计划
]

// 注塑机射台数量
export const injectionUnitCountOptions = [
  { label: "单射台", value: 1 },
  { label: "双射台", value: 2 },
  { label: "三射台", value: 3 }
]

// 注塑机驱动系统类型
export const driveSystemOptions = [
  { label: "全液压驱动", value: "全液压驱动" },     // en: Hydraulic Drive — 传统油压系统，成本低、锁模力大
  { label: "全电动驱动", value: "全电动驱动" },     // en: All-Electric Drive — 伺服电机驱动，高精度、节能、洁净
  { label: "电液复合驱动", value: "电液复合驱动" }  // en: Electro-Hydraulic Drive — 部分动作电驱，部分液压（部分厂商特有表述）
]

// 注塑机控制器型号
export const controllerModelOptions = [
  { label: "KEBA", value: "KEBA" },                         // en: KEBA — 奥地利品牌，广泛用于全电动及高端液压机
  { label: "西门子", value: "西门子" },                     // en: Siemens — 常用于定制化或大型设备
  { label: "三菱", value: "三菱" },                         // en: Mitsubishi Electric — 日系设备常用
  { label: "发那科", value: "发那科" },                     // en: Fanuc — 多用于日系全电机
  { label: "海天专用控制器", value: "海天专用控制器" },     // en: Haitian Proprietary Controller — 海天/长飞亚自研系统
  { label: "伊之密专用控制器", value: "伊之密专用控制器" }, // en: Yizumi Proprietary Controller
  { label: "震雄专用控制器", value: "震雄专用控制器" },     // en: Chen Hsong Proprietary Controller
  { label: "力士乐", value: "力士乐" },                     // en: Bosch Rexroth — 液压系统集成常用
  { label: "欧姆龙", value: "欧姆龙" },                     // en: Omron — 中小型设备PLC方案
  { label: "台达", value: "台达" },                         // en: Delta — 国产设备常用
  { label: "其他", value: "其他" }                          // en: Other — 兜底选项
]

// 注塑机控制器版本
export const controllerVersionOptions = [
  // KEBA 系列
  { label: "KEBA KeMotion 1175", value: "KEBA KeMotion 1175" },       // en: KEBA KeMotion 1175 — 长飞亚/海天常用
  { label: "KEBA KeMotion 2800", value: "KEBA KeMotion 2800" },       // en: KEBA KeMotion 2800 — 新一代平台
  { label: "KEBA 映翰通定制版", value: "KEBA 映翰通定制版" },         // en: KEBA + InHand customized — 国内联网定制版

  // 西门子
  { label: "西门子 S7-1200", value: "西门子 S7-1200" },               // en: Siemens S7-1200
  { label: "西门子 S7-1500", value: "西门子 S7-1500" },               // en: Siemens S7-1500

  // 三菱
  { label: "三菱 MELSEC iQ-R", value: "三菱 MELSEC iQ-R" },           // en: Mitsubishi MELSEC iQ-R
  { label: "三菱 Q 系列", value: "三菱 Q 系列" },                     // en: Mitsubishi Q Series

  // 发那科
  { label: "发那科 R-30iB", value: "发那科 R-30iB" },                 // en: Fanuc R-30iB — 注塑/机器人通用
  { label: "发那科 α 系列", value: "发那科 α 系列" },                // en: Fanuc Alpha Series

  // 国产专用系统
  { label: "海天 HMI-2020", value: "海天 HMI-2020" },                 // en: Haitian HMI-2020
  { label: "伊之密 YZM-V3", value: "伊之密 YZM-V3" },                 // en: Yizumi YZM-V3
  { label: "震雄 CHS-8000", value: "震雄 CHS-8000" },                 // en: Chen Hsong CHS-8000

  // 其他
  { label: "未知", value: "未知" },                                   // en: Unknown
  { label: "其他", value: "其他" }                                    // en: Other
]

// 注塑机通讯能力
export const commAbilityOptions = [
  { label: "开通", value: true },
  { label: "未开通", value: false }
]

// 注塑机通讯协议
export const communicationProtocolOptions = [
  { label: "Euromap 63", value: "Euromap 63" },           // en: Euromap 63 — 最广泛使用的注塑机通信标准，基于串口（RS232/485）或以太网，用于与辅机、MES对接
  { label: "Euromap 77", value: "Euromap 77" },           // en: Euromap 77 — 基于 OPC UA 的新一代标准，支持更丰富的数据模型和安全机制，面向工业4.0
  { label: "OPC UA", value: "OPC UA" },                   // en: OPC Unified Architecture — 平台无关、安全可靠的工业通信协议，常用于高端设备或自定义集成
  { label: "Modbus RTU", value: "Modbus RTU" },           // en: Modbus RTU — 串行通信协议，常用于老式设备或简单数据采集（如温度、状态）
  { label: "Modbus TCP", value: "Modbus TCP" },           // en: Modbus TCP — 基于以太网的 Modbus，部署简单，广泛用于 SCADA 系统
  { label: "Profinet", value: "Profinet" },               // en: Profinet — 西门子主导的工业以太网协议，常见于德系设备（如克劳斯玛菲、恩格尔）
  { label: "EtherNet/IP", value: "EtherNet/IP" },         // en: EtherNet/IP — 罗克韦尔（Rockwell）主导，部分美系或合资设备使用
  { label: "CC-Link", value: "CC-Link" },                 // en: CC-Link — 三菱主导的现场总线，日系设备（如三菱、东芝/芝浦）常用
  { label: "KEBA 自定义协议", value: "KEBA 自定义协议" }, // en: KEBA Proprietary Protocol — 基于 TCP 或串口，部分长飞亚/海天设备使用
  { label: "海天专用协议", value: "海天专用协议" },       // en: Haitian Proprietary Protocol — 国产设备常见，通常基于 Modbus 扩展
  { label: "无通讯", value: "无通讯" },                   // en: No Communication — 设备不具备对外通信能力
  { label: "其他", value: "其他" }                        // en: Other — 兜底选项
]

// 注塑机界面压力单位
export const pressureUnitOptions = [
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
export const speedUnitOptions = [
  { value: "mm/s",  label: "mm/s" },
  { value: "%",  label: "%" },
  { value: "inch/s",  label: "inch/s" },
  { value: "cm³/s",  label: "cm³/s" },
  { value: "inch³/s",  label: "inch³/s" },
]

// 注塑机界面位置单位
export const positionUnitOptions = [
  { value: "mm",  label: "mm" },
  { value: "inch",  label: "inch" },
  { value: "cm³",  label: "cm³" },
  { value: "inch³",  label: "inch³" },
]

// 注塑机界面时间单位
export const timeUnitOptions = [
  { value: "s",  label: "s" }
]

// 注塑机界面螺杆转速单位
export const screwRotationUnitOptions = [
  { value: "rpm",  label: "rpm" },
  { value: "mm/s",  label: "mm/s" },
  { value: "%",  label: "%" },
  { value: "cm/s",  label: "cm/s" },
  { value: "m/min",  label: "m/min" },
  { value: "m/s",  label: "m/s" },
  { value: "inch/s",  label: "inch/s" },
]

// 注塑机界面温度单位
export const temperatureUnitOptions = [
  { value: "℃",  label: "℃" },
  { value: "℉",  label: "℉" }
]

// 开合模/顶针速度单位
export const openingAndClampingMoldVeloUnitOptions = [
  { value: "mm/s",  label: "mm/s" },
  { value: "%",  label: "%" },
  { value: "inch/s",  label: "inch/s" }
]

// 注塑机界面锁模力单位
export const clampingForceUnitOptions = [
  { value: "Ton",  label: "Ton" },
  { value: "kN",  label: "kN" },
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

// 喷嘴类型（按行业通用术语整理，去重并标准化）
export const nozzleTypeOptions = [
  { label: "直通型", value: "直通型" },         // en: Open Nozzle — 无关闭机构，结构简单
  { label: "锁闭型", value: "锁闭型" },         // en: Shut-off Nozzle — 弹簧/液压自动关闭，防流涎
  { label: "针阀式", value: "针阀式" },         // en: Valve Gate Nozzle — 外部控制开闭，高精度
  { label: "倒锥式", value: "倒锥式" },         // en: Reverse Taper Nozzle — 增强密封，减少回流
  { label: "热流道喷嘴", value: "热流道喷嘴" }, // en: Hot Runner Nozzle — 集成加热，用于热流道系统
  { label: "其他", value: "其他" }              // en: Other — 兜底选项
]

// 注塑机喷嘴孔直径
export const nozzleHoleDiameterOptions = [
  { label: "2mm", value: 2 },
  { label: "2.5mm", value: 2.5 },
  { label: "3mm", value: 3 },
  { label: "3.5mm", value: 3.5 },
  { label: "4mm", value: 4 },
  { label: "4.5mm", value: 4.5 },
  { label: "5mm", value: 5 },
  { label: "6mm", value: 6 },
  { label: "8mm", value: 8 },
  { label: "10mm", value: 10 },  
  { label: "12mm", value: 12 },
  { label: "14mm", value: 14 } 
]

// 注塑机喷嘴球半径
export const nozzleSphereRadiusOptions = [
  { label: "12.5", value: 12.5 },
  { label: "15.5", value: 15.5 },
  { label: "20", value: 20 },
  { label: "25", value: 25 },
  { label: "40", value: 40 },
  { label: "90", value: 90 }
]

// 最大注射段数
export const maxInjectionStagesOptions = [
  { label: "1", value: 1 },
  { label: "2", value: 2 },
  { label: "3", value: 3 },
  { label: "4", value: 4 },
  { label: "5", value: 5 },
  { label: "6", value: 6 },
]

// 最大保压短时
export const maxHoldingStagesOptions = [
  { label: "1", value: 1 },
  { label: "2", value: 2 },
  { label: "3", value: 3 },
  { label: "4", value: 4 },
  { label: "5", value: 5 },
]

// 最大储料段数
export const maxMeteringStagesOptions = [
  { label: "1", value: 1 },
  { label: "2", value: 2 },
  { label: "3", value: 3 },
  { label: "4", value: 4 },
]

// 最大温控区域
export const maxTempZonesOptions = [
  { label: "1", value: 1 },
  { label: "2", value: 2 },
  { label: "3", value: 3 },
  { label: "4", value: 4 },
  { label: "5", value: 5 },
  { label: "6", value: 6 },
  { label: "7", value: 7 },
  { label: "8", value: 8 },
  { label: "9", value: 9 },
  { label: "10", value: 10 },
]

// 锁模类型（按行业通用术语整理，去重并标准化）
export const clampingTypeOptions = [
  { label: "肘杆式", value: "肘杆式" },                         // en: Toggle Clamping — Mechanical linkage amplifies clamping force; most common, energy-efficient
  { label: "直压式（全液压）", value: "直压式（全液压）" },       // en: Full Hydraulic Direct Clamping — Hydraulic cylinder directly drives platen; uniform force distribution, ideal for large or precision molds
  { label: "伺服直驱式（全电动）", value: "伺服直驱式（全电动）" }, // en: Servo-Electric Direct Clamping — Servo motor with ball screw/belt drive; high precision, oil-free, low noise
  { label: "其他", value: "其他" }                              // en: Other — Fallback option for uncommon or custom mechanisms
]

// 顶出类型（按驱动方式分类，行业通用术语，去重并标准化）
export const ejectionTypeOptions = [
  { label: "液压顶出", value: "液压顶出" },             // en: Hydraulic Ejection — Most common; hydraulic cylinder drives ejector plate from rear side (standard on most machines)
  { label: "机械顶出", value: "机械顶出" },             // en: Mechanical Ejection — Uses mold opening stroke to trigger ejection via cams or levers; no independent power source, common on small machines
  { label: "伺服电动顶出", value: "伺服电动顶出" },     // en: Servo-Electric Ejection — Servo motor with ball screw drives precise, programmable ejection; used in all-electric or high-end hybrid machines
  { label: "气动顶出", value: "气动顶出" },             // en: Pneumatic Ejection — Air cylinder drives ejection; rare, used only for light-duty applications (e.g., thin-wall packaging)
  { label: "无顶出装置", value: "无顶出装置" },         // en: No Ejection System — Machine lacks built-in ejection; manual part removal required (common on micro or custom machines)
  { label: "其他", value: "其他" }                      // en: Other — Fallback for non-standard or custom ejection systems
]

// 顶出模式（按顶出杆布局/结构形式分类，行业通用术语，去重并标准化）
export const ejectionModeOptions = [
  { label: "单中心顶出", value: "单中心顶出" },           // en: Single Center Ejection — One central ejector rod or plate; simple molds, low cost
  { label: "双侧对称顶出", value: "双侧对称顶出" },       // en: Dual-Side Symmetric Ejection — Ejector rods on left and right sides; better balance for medium-sized molds
  { label: "四角对称顶出", value: "四角对称顶出" },       // en: Four-Corner Symmetric Ejection — Ejector rods at four corners; optimal balance for large or precision molds
  { label: "多点分布顶出", value: "多点分布顶出" },       // en: Multi-Point Distributed Ejection — Custom layout with multiple ejector pins/plates; for complex geometry or large surface area
  { label: "无自动顶出", value: "无自动顶出" },           // en: No Automatic Ejection — Relies on manual removal or external robot; machine may have no ejector mechanism
  { label: "其他", value: "其他" }                        // en: Other — Fallback for special configurations
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


// 螺杆类型
export const screwTypeOptions = [
  { label: "通用型", value: "通用型" },
  { label: "渐变型", value: "渐变型" },
  { label: "突变型", value: "突变型" },
  { label: "屏障型", value: "屏障型" },
  { label: "精密型", value: "精密型" },
  { label: "混炼型", value: "混炼型" },
]