// 浇口信息
export const gateForm = {
  gate_shape: null,
  gate_type: null,
  gate_count: null,
  location_description: null,
  // --- 矩形 --
  length: null,
  width: null,
  // --- 圆形 --
  diameter: null,
  // --- 梯形 ---
  top_length: null,
  bottom_length: null,
  height: null,
  // --- 环形 ---
  outer_diameter: null,
  inner_diameter: null,
  gap: null
}

// 型腔信息
export const cavityForm = {
  id: null,
  cavity_count_per_shot: 1,
  product_name: null,
  product_code: null,
  max_flow_length: null,
  ave_wall_thickness: null,
  min_wall_thickness: null,
  max_wall_thickness: null,
  projected_area_per_cavity: null,
  estimated_weight_per_cavity: null,
  // --- 浇口 ---
  gates: [structuredClone(gateForm)]
}

// 浇注系统信息
export const gatingSystemForm = {
  id: null,
  // --- 流道类型 ---
  runner_type: "热流道",
  total_product_weight: null,
  // --- 热流道系统（热流道 & 热转冷） ---
  hot_runner_supplier: null,
  hot_runner_system_type: null,
  valve_actuation_type: null,
  hot_runner_manifold_zones: null,
  hot_runner_nozzle_count: null,
  
  has_sequencing_control: false,
  sequencing_control_method: null,
  // --- 主流道衬套（冷流道 & 热转冷） ---
  runner_weight: null,
  runner_length: null,
  sprue_bushing_outer_dia: null,
  sprue_bushing_bore_dia: null,
  sprue_bushing_radius: null,
  sprue_bushing_angle: null,
  sprue_bushing_material: null,
  sprue_bushing_standard: null,
  // --- 工艺相关参数 ---
  estimated_shot_weight: null,
  estimated_runner_weight: null,
  projected_area: null,
  // --- 型腔 ---
  cavities: [structuredClone(cavityForm)]
}

// 冷却系统信息
export const coolingSystemForm = {
  id: null,
  // --- 型腔信息 ---
  cooling_cavity_type: null,
  cooling_cavity_circuit_count: null,
  cooling_cavity_layout: null,
  cooling_cavity_pipe_diameter: null,
  cooling_cavity_fitting_type: null,
  cooling_cavity_fitting_count: null,
  cooling_cavity_fitting_labels: null,
  cooling_cavity_fitting_seal_method: null,
  // --- 型芯信息 ---
  cooling_core_type: null,
  cooling_core_circuit_count: null,
  cooling_core_layout: null,
  cooling_core_pipe_diameter: null,
  cooling_core_fitting_type: null,
  cooling_core_fitting_count: null,
  cooling_core_fitting_labels: null,
  cooling_core_fitting_seal_method: null,
}

// 顶出系统信息
export const ejectionSystemForm = {
  id: null,

  ejection_type: null,
  reset_method: null,
  ejector_rod_hole_type: null,
  ejector_rod_hole_diameter: null,
  ejector_rod_hole_depth: null,
  ejector_rod_hole_spacing_x: null,
  ejector_rod_hole_spacing_y: null,
  ejection_stroke: null,
  has_pre_ejection: null,
  pre_ejection_stroke: null,
  estimated_ejection_force: null,
}

// 模具信息
export const moldInfoForm = {
  id: null,
  project_id: null,
  // --- 状态信息 ---
  status: "active",
  // --- 基本信息 ---
  mold_no: null,
  mold_name: null,
  mold_type: null,
  category: null,
  structure: null,
  shot_count: 1,
  cavity_layout: null,
  cavity_count: null,
  target_cycle_time: null,
  recommended_tonnage: null,
  total_injection_weight: null,
  // --- 辅助装置 ---
  mechanism: null,
  special_processes: null,
  // --- 产品分类 ---
  product_category: null,
  product_subcategory: null,  
  product_model: null,
  product_description: null,
  // --- 模具外形尺寸&重量 ---
  mold_length: null,
  mold_width: null,
  mold_thickness: null,
  mold_weight: null,
  // --- 浇注系统 ---
  gating_systems: [structuredClone(gatingSystemForm)],
  // --- 冷却系统 ---
  cooling_system: structuredClone(coolingSystemForm),
  // --- 顶出系统 ---
  ejection_system: structuredClone(ejectionSystemForm),
  // --- 吊装结构 ---
  handling_type: null,
  handling_thread_size: null,
  handling_thread_depth: null,
  handling_point_count: null,
  handling_position: null,
  // --- 定位圈 ---
  locating_ring_outer_dia: null,
  locating_ring_inner_dia: null,
  locating_ring_height: null,
  locating_ring_material: null,
  locating_ring_standard: null,
  mov_half_locating_ring_outer_dia: null,
  mov_half_locating_ring_inner_dia: null,
  mov_half_locating_ring_height: null,
  // --- 导向与定位结构 ---
  guide_pin_diameter: null,
  guide_pin_count: null,
  has_precision_locator: null,
  locator_type: null,
  locator_position: null,
  // --- 开模与锁模 ---
  part_removal_action: null,
  runner_separation_distance: null,
  recommended_opening_stroke: null,
  min_clamping_force: null,
}

// 模具类型
export const moldTypeOptions = [
  { label: "注塑模具", value: "注塑模具" }, // en: injection
  { label: "冲压模具", value: "冲压模具" }, // en: stamping
  // { label: "压铸模具", value: "压铸模具" }, // en: die_casting
  // { label: "吹塑模具", value: "吹塑模具" }, // en: blow_molding
  // { label: "挤出模具", value: "挤出模具" }, // en: extrusion
  // { label: "压缩成型模具", value: "压缩成型模具" }, // en: compression
  // { label: "传递模", value: "传递模" }, // en: transfer
  // { label: "滚塑模具", value: "滚塑模具" }, // en: rotational
  // { label: "热成型模具", value: "热成型模具" }, // en: thermoforming
  // { label: "发泡模具", value: "发泡模具" }, // en: foam
  // { label: "硅胶模具", value: "硅胶模具" }, // en: silicone
  // { label: "其他", value: "其他" } // en: others
]

// 模具类别
export const moldCategoryOptions = [
  { label: "汽车", value: "汽车" }, // en: automotive
  { label: "家电", value: "家电" }, // en: home_appliance
  { label: "黑电", value: "黑电" }, // en: white_goods
  { label: "白电", value: "白电" }, // en: brown_goods
  { label: "医疗", value: "医疗" }, // en: medical
  { label: "消费电子", value: "消费电子" }, // en: consumer_electronics
  { label: "包装", value: "包装" }, // en: packaging
  { label: "工业零部件", value: "工业零部件" }, // en: industrial_component
  { label: "连接器/接插件", value: "连接器/接插件" }, // en: connector
  { label: "光学镜片", value: "光学镜片" }, // en: optical_lens
  { label: "日用品", value: "日用品" }, // en: daily_necessities
  { label: "其他", value: "其他" } // en: others
]

// 开合结构
export const moldStructureOptions = [
  { label: "两板模", value: "两板模" }, // en: two_plate
  { label: "三板模", value: "三板模" }, // en: three_plate
  { label: "热流道模", value: "热流道模" }, // en: hot_runner
  { label: "冷流道模", value: "冷流道模" }, // en: cold_runner
  { label: "叠层模", value: "叠层模" }, // en: stack_mold
  { label: "家族模", value: "家族模" }, // en: family_mold
  { label: "镶件模", value: "镶件模" }, // en: insert_mold
  { label: "脱螺纹模", value: "脱螺纹模" }, // en: unscrewing_mold
  { label: "气体辅助成型模", value: "气体辅助成型模" }, // en: gas_assist
  { label: "其他", value: "其他" } // en: others
]

// 成型次数
export const shotCountOptions = [
  { label: "1次", value: 1 },
  { label: "2次", value: 2 },
  { label: "3次", value: 3 },
  { label: "4次", value: 4 },
  { label: "5次", value: 5 },
]

// 推荐成型吨位
export const recommendedTonnageOptions = [
  { label: "260T", value: 260 },
  { label: "470T", value: 470 },
  { label: "900T", value: 900 },
  { label: "1000T", value: 1000 },
  { label: "2000T", value: 2000 },
  { label: "4000T", value: 4000 },
]

// 取件方式
export const partRemovalActionOptions = [
  { label: "手工取件", value: "手工取件" }, // en: manual
  { label: "机械手取件", value: "机械手取件" }, // en: robot
  { label: "自动掉落", value: "自动掉落" } // en: drop
]

// 精定位类型
export const locatorTypeOptions = [
  { label: "锥形锁", value: "锥形锁" }, // en: taper_lock
  { label: "边锁", value: "边锁" }, // en: side_lock
  { label: "楔形锁", value: "楔形锁" } // en: heel_block
]

// 流道类别
export const runnerTypeOptions = [
  { value: "热流道", label: "热流道" }, // en: hot_runner
  { value: "冷流道", label: "冷流道" }, // en: cold_runner
  { value: "热转冷", label: "热转冷" } // en: hot_to_cold_runner
]

// 冷流道浇口类别
export const gateTypeOptions = [
  { label: "直浇口", value: "直浇口" }, // en: sprue_gate
  { label: "侧浇口", value: "侧浇口" }, // en: edge_gate
  { label: "点浇口", value: "点浇口" }, // en: pin_point_gate
  { label: "搭接式浇口", value: "搭接式浇口" }, // en: overlap_gate
  { label: "护耳浇口", value: "护耳浇口" }, // en: tab_gate
  { label: "薄片浇口", value: "薄片浇口" }, // en: film_gate
  { label: "扇形浇口", value: "扇形浇口" }, // en: fan_gate
  { label: "环形浇口", value: "环形浇口" }, // en: ring_gate
  { label: "盘形浇口", value: "盘形浇口" }, // en: disk_gate
  { label: "伞形浇口", value: "伞形浇口" }, // en: diaphragm_gate
  { label: "潜伏式浇口", value: "潜伏式浇口" }, // en: submarine_gate
  { label: "弧形浇口", value: "弧形浇口" } // en: curved_gate
]

// 热流道浇口类别
export const hotNozzleTypeOptions = [
  { label: "开放式", value: "开放式" }, // en: open_nozzle
  { label: "尖点式", value: "尖点式" }, // en: sharp_tip_nozzle
  { label: "针阀式", value: "针阀式" } // en: valve_gate_nozzle
]

//时序控制方式
export const sequencingControlMethodOptions = [
  { label: "液压", value: "液压" }, // en: hydraulic
  { label: "气动", value: "气动" }, // en: pneumatic
  { label: "电控", value: "电控" } // en: electric
]

// 吊模孔规格
export const hangingMoldHoleSpeOptions = [
  { value: "M12", label: "M12" },
  { value: "M16", label: "M16" },
  { value: "M20", label: "M20" },
  { value: "M24", label: "M24" },
  { value: "M30", label: "M30" },
  { value: "M36", label: "M36" },
  { value: "M42", label: "M42" },
  { value: "M48", label: "M48" },
  { value: "M64", label: "M64" }
]

// 浇口套外径 D1
export const sprueBushingOuterDiaOptions = [
  { label: "20mm", value: 20 },
  { label: "25mm", value: 25 },
  { label: "30mm", value: 30 },
  { label: "35mm", value: 35 },
  { label: "40mm", value: 40 },
  { label: "50mm", value: 50 },
  { label: "60mm", value: 60 },
  { label: "70mm", value: 70 },
  { label: "80mm", value: 80 }
]

// 浇口套孔径 D2
export const sprueBushingBoreDiaOptions  = [
  { label: "3mm", value: 3 },
  { label: "3.5mm", value: 3.5 },
  { label: "4mm", value: 4 },
  { label: "5mm", value: 5 },
  { label: "6mm" ,value: 6 },
  { label: "8mm", value: 8 },
  { label: "10mm", value: 10 },  
  { label: "12mm", value: 12 },
  { label: "14mm", value: 14 },
  { label: "16mm", value: 16 }
]

// 浇口套球半径 R
export const sprueBushingRadiusOptions = [
  { label: "12.5mm", value: 12.5 }, // en: r12_5
  { label: "15.5mm", value: 15.5 }, // en: r15_5
  { label: "20mm", value: 20 },     // en: r20
  { label: "25mm", value: 25 },     // en: r25
  { label: "40mm", value: 40 },     // en: r40
  { label: "90mm", value: 90 }      // en: r90
]

// 浇口形状
export const gateShapeOptions = [
  { label: "矩形", value: "矩形" },
  { label: "圆形", value: "圆形" },
  { label: "环形", value: "环形" },
  { label: "其他", value: "其他" }
]

// 冷却类型
export const coolingTypeOptions = [
  { value: "水冷", label: "水冷" },                     // en: water_cooling
  { value: "油冷", label: "油冷" },                     // en: oil_cooling
]

// 冷却管道直径（单位：mm）
export const coolingChannelDiameterOptions = [
  { label: "6mm", value: 6 },
  { label: "8mm", value: 8 },     // 默认推荐
  { label: "10mm", value: 10 },
  { label: "12mm", value: 12 },
  { label: "14mm", value: 14 },
  { label: "16mm", value: 16 }
]

//冷却管连接器类型、水路接口类型
export const coolingFittingTypeOptions = [
  { label: "快插式", value: "快插式" },       // en: quick_disconnect
  { label: "BSPP 螺纹", value: "BSPP 螺纹" }, // en: bspp_thread
  { label: "NPT 螺纹", value: "NPT 螺纹" },   // en: npt_thread
  { label: "直通螺纹", value: "直通螺纹" },   // en: straight_thread
  { label: "其他", value: "其他" }            // en: other
]

// 顶出类型
export const ejectionTypeOptions = [
  { label: "液压顶出", value: "液压顶出" },             // en: Hydraulic Ejection — Most common; hydraulic cylinder drives ejector plate from rear side (standard on most machines)
  { label: "机械顶出", value: "机械顶出" },             // en: Mechanical Ejection — Uses mold opening stroke to trigger ejection via cams or levers; no independent power source, common on small machines
  { label: "伺服电动顶出", value: "伺服电动顶出" },     // en: Servo-Electric Ejection — Servo motor with ball screw drives precise, programmable ejection; used in all-electric or high-end hybrid machines
  { label: "气动顶出", value: "气动顶出" },             // en: Pneumatic Ejection — Air cylinder drives ejection; rare, used only for light-duty applications (e.g., thin-wall packaging)
  { label: "无顶出装置", value: "无顶出装置" },         // en: No Ejection System — Machine lacks built-in ejection; manual part removal required (common on micro or custom machines)
  { label: "其他", value: "其他" }                      // en: Other — Fallback for non-standard or custom ejection systems

]

// 复位方式
export const resetMethodOptions = [
  { label: "弹簧复位", value: "弹簧复位" },       // en: spring_return
  { label: "强回位螺丝", value: "强回位螺丝" },   // en: return_screw
  { label: "油缸复位", value: "油缸复位" },       // en: hydraulic_return
  { label: "强压回", value: "强压回" }            // en: forced_return
]

// 吊装类型
export const liftingTypeOptions = [
  { label: "吊环螺钉", value: "吊环螺钉" },       // en: eye_bolt
  { label: "沉头吊装孔", value: "沉头吊装孔" },   // en: countersunk_lifting_hole
  { label: "通孔吊装", value: "通孔吊装" },       // en: through_hole_lifting
  { label: "吊装槽", value: "吊装槽" }            // en: lifting_slot
]

// 吊环规格（按螺纹公称直径）
export const liftingEyeBoltOptions = [
  { label: "M8", value: "M8" },     // en: m8
  { label: "M10", value: "M10" },   // en: m10
  { label: "M12", value: "M12" },   // en: m12
  { label: "M16", value: "M16" },   // en: m16
  { label: "M20", value: "M20" },   // en: m20
  { label: "M24", value: "M24" },   // en: m24
  { label: "M30", value: "M30" },   // en: m30
  { label: "M36", value: "M36" },
  { label: "M40", value: "M40" },
  { label: "M42", value: "M42" },
  { label: "M48", value: "M48" },
  { label: "M56", value: "M56" },
  { label: "M64", value: "M64" }
]

// 定位圈外径（标准值）
export const locatingRingOuterDiaOptions = [
  { label: "100mm", value: 100 },
  { label: "120mm", value: 120 },
  { label: "125mm", value: 125 },
  { label: "160mm", value: 160 },
  { label: "200mm", value: 200 }
]

// 动模定位圈外径（标准值）
export const movingLocatingRingOuterDiaOptions = [
  { label: "100mm", value: 100 },
  { label: "120mm", value: 120 },
  { label: "125mm", value: 125 },
  { label: "160mm", value: 160 },
  { label: "200mm", value: 200 }
]

// 辅助装置信息
export const assistEquipmentOptions = [
  { label: "模温机", value: "模温机" },
  { label: "油压站", value: "油压站" },
  { label: "抽真空", value: "抽真空" },
  { label: "急冷急热", value: "急冷急热" },
  { label: "IMD工艺", value: "IMD工艺" },
  { label: "IML工艺", value: "IML工艺" },
  { label: "氮气注塑", value: "氮气注塑" },
  { label: "增压气泵", value: "增压气泵" },
  { label: "射胶延时继电器", value: "射胶延时继电器" },
  { label: "抽芯", value: "抽芯" },
]

// 模温控制
export const moldTempControlOptions = [
  { label: "常温水", value: "常温水" }, // en: ambient_water
  { label: "冻水", value: "冻水" },     // en: chilled_water
  { label: "热水", value: "热水" },     // en: hot_water
  { label: "热油", value: "热油" },     // en: hot_oil
  { label: "发热管", value: "发热管" }  // en: cartridge_heater
]
