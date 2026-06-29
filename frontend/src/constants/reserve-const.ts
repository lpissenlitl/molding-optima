import { moldInfoForm } from "./mold-const"
import { polymerInfoForm } from "./polymer-const"
import { machineInfoForm } from "./machine-const"

/* 预约信息 */
export const basicInfoForm = {
  // 模具信息
  mold_no: null,
  mold_name: null,
  mold_type: null,
  category: null,
  structure: null,
  shot_count: null,
  cavity_layout: null,
  cavity_count: null,
  target_cycle_time: null,
  recommended_tonnage: null,
  total_injection_weight: null,
  // 项目信息
  initiator: null,
  project_manager: null,
  fitter: null,
  // 预约信息
  trial_stage: 0,
  trial_iteration: 0,
  trial_version: "T0",
  is_tf_trial: null,
  customer_attended: null,
  special_process: null,
  is_dry_run_completed: null,
  dry_run_count: null,
  trial_shot_count: null,
  planned_mold_handover_at: null,
  preferred_trial_start_at: null,
  estimated_trial_duration_hours: 4,
  trial_location: "内部",
  outsourcing_reason: null,
}

/* 试模目的 */
export const trialPurposeForm = {
  trial_aim_selections: [
    { label: "正常验证", value: false },
    { label: "设计验证", value: false },
    { label: "研配验证", value: false },
    { label: "皮纹验证", value: false },
    { label: "热流道验证", value: false },
    { label: "产品设变", value: false },
    { label: "客户验收", value: false },
    { label: "客户参加试模", value: false },
    { label: "", value: false }
  ],
  check_item_selections: [
    { label: "动作", value: false },
    { label: "试飞边", value: false },
    { label: "外观", value: false },
    { label: "困气", value: false },
    { label: "缩水", value: false },
    { label: "取件", value: false },
    { label: "客改制品", value: false },
    { label: "粘膜", value: false },
    { label: "", value: false }
  ],
  modify_content: null
}

/* 科龙试模目的 */
export const kelonTrialPurposeForm = {
  trial_aim_selections: [
    { label: "内改", value: false },
    { label: "新模首样", value: false },
    { label: "客改", value: false },
    { label: "客户打样", value: false },
    { label: "验模", value: false },
    { label: "", value: false }
  ],
  check_item_selections: [
    { label: "动作", value: false },
    { label: "试飞边", value: false },
    { label: "外观", value: false },
    { label: "困气", value: false },
    { label: "缩水", value: false },
    { label: "取件", value: false },
    { label: "客改制品", value: false },
    { label: "粘膜", value: false },
    { label: "", value: false }
  ],
  modify_content: null
}


/* 物料需求信息 */
export const materialReqForm = {
  // 物料属性
  category: null,
  material_name: null,
  color: null,
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
  percentage: null,
}

/* 样件明细信息 */
export const sampleItemForm = {
  // 试模信息
  mold_no: null,
  trial_version: null,
  product_code: null,
  parts_per_shot: null,
  // 物料信息
  material_id: null,
  material_code: null,
  sap_material_code: null,
  material_grade: null,
  polymer_id: null,
  polymer_abbreviation: null,
  polymer_grade: null,
  // 样件信息
  sample_weight: null,
  trial_quantity: null,
  shipped_quantity: null,
  received_quantity: null,
  // 包装信息
  outer_packaging: null,
  inner_packaging: null,
  // 配送信息
  transport_method: null,
  delivery_location: null,
  remarks: null,
}

/* 每次注塑的物料需求信息 */
export const shotFormulationForm = {
  unit_index: 0,
  poly_info: structuredClone(polymerInfoForm),
  resin_req: structuredClone(materialReqForm),
}

/* 试模用料方案内容 */
export const materialPlanForm = {
  remarks: null,
  shot_sequence: [
    structuredClone(shotFormulationForm)
  ],
  sample_items: []
}

/* 制定用料方案 */
export const materialPlanningForm = { 
  active_plan_index: "0",
  material_plans: [
    structuredClone(materialPlanForm)
  ],
  additives: [],
  inserts: []
}

/* 试模用料需求 */
export const materialRequiringForm = {
  material_requisitions: [
    {
      id: null,
      reservation_id: null,
      source: null,
      status: "pending",
      requisition_code: null,
      mold_no: null,
      trial_version: null,
      lines: []
    }
  ]
}

/* ---------- staged ---------- */
export const fillerInfoForm = {
  name: null,
  percentage: null
}

export const colorantInfoForm  = {
  type: null,
  percentage: null
}

export const shotFormulationMaterialForm = {
  id: null,
  material_code: null,
  sap_material_code: null,
  material_name: null,
  material_grade: null,
  quantity: null,
}

export const auxiliaryInfoForm = {
  id: null,
  equipment_name: null,
  equipment_type: null,
  specification: null,
  total_count: null,
  apply_quantity: 1,
  apply_remarks: null,
}

export const auxiliaryRequiringForm = {
  auxiliaries: [
    structuredClone(auxiliaryInfoForm)
  ],
  // equipments: [
  //   { label: "模温机", value: false },
  //   { label: "油压站", value: false },
  //   { label: "抽真空", value: false },
  //   { label: "急冷急热", value: false },
  //   { label: "IMD工艺", value: false },
  //   { label: "IML工艺", value: false },
  //   { label: "氮气注塑", value: false },
  //   { label: "增压气泵", value: false },
  //   { label: "射胶延时继电器", value: false },
  //   { label: "抽芯", value: false },
  // ],
  // temp_ctrl_box_num: null,
  // temp_ctrl_mode: null,
  remarks: null,
}

export const trialAttentionForm = {
  notations: [
    { select: false, contents: "1. 模具开模顺序见结构简图，模具分几次开模？", remarks: "" },
    { select: false, contents: "2. 油缸抽芯动作的先后顺序见示意图。", remarks: "" },
    { select: false, contents: "3. 行位底部有顶针，合模前顶针板必须完全复位。", remarks: "" },
    { select: false, contents: "4. 此模有嵌件，须注意嵌件的摆放位置是否正确。", remarks: "" },
    { select: false, contents: "5. 此模采用了二次顶出机构。", remarks: "" },
    { select: false, contents: "6. 此模有加速顶出机构。", remarks: "" },
    { select: false, contents: "7. 换款动作。", remarks: "" },
  ],
}

export const trialRequirementForm = {
  requirements: [
    { check: null, contents: "1. 码模是否在两侧？", remarks: "" },
    { check: null, contents: "2. 是否已提供热流道接线图？", remarks: "" },
    { check: null, contents: "3. 运水接驳是否有运水图及特殊提示？", remarks: "" },
    { check: null, contents: "4. 所有需要接驳感线的咭擎是否已调试好？", remarks: "" }
  ]
}

/* ---------- staged end ---------- */

/* 试模样件需求 */
export const sampleRequiringForm = { 
  send_reason: null,
  material_supply: null,
  packaging_requirement: null,
  plan_storage_at: null,
  remarks: null,
  sample_items: [],
}

/* 试模约机单数据 */
export const reservationForm = {
  id: null,
  status: null,
  source: null,
  priority: 0,
  external_id: null,
  basic_info: structuredClone(basicInfoForm),
  trial_purpose: structuredClone(trialPurposeForm),
  mold_info: structuredClone(moldInfoForm),
  machine_info: structuredClone(machineInfoForm),
  material_planning: structuredClone(materialPlanningForm),
  sample_requiring: structuredClone(sampleRequiringForm),
  auxiliary_requiring: structuredClone(auxiliaryRequiringForm),
  material_requiring: structuredClone(materialRequiringForm),
}

/* 科龙试模约机单数据 */
export const kelonReservationForm = {
  id: null,
  status: null,
  source: null,
  priority: 0,
  external_id: null,
  basic_info: structuredClone(basicInfoForm),
  trial_purpose: structuredClone(kelonTrialPurposeForm),
  mold_info: structuredClone(moldInfoForm),
  machine_info: structuredClone(machineInfoForm),
  material_planning: structuredClone(materialPlanningForm),
  sample_requiring: structuredClone(sampleRequiringForm),
  auxiliary_requiring: structuredClone(auxiliaryRequiringForm),
  material_requiring: structuredClone(materialRequiringForm),
}


function get_r_trial_time_options() {
  const r_trial_time_options: string[] = []
  for (let i = 0; i < 24; ++i) {
    const hour = Math.floor(i / 2)
    let str_hour = String(hour)
    if (hour < 10) {
      str_hour = "0" + String(hour)
    }
    let minu = "00"
    if (i % 2 === 1) {
      minu = "30"
    }
    r_trial_time_options.push(str_hour + ":" + minu)
  }
  return r_trial_time_options
}

function get_cooling_water_runner_options() {
  const cooling_water_runner_options : string[] = []
  for (let i = 1;i <= 100; i++) {
    cooling_water_runner_options.push(i + "")
  }
  return cooling_water_runner_options
}

export const cooling_water_runner_options = get_cooling_water_runner_options()
export const r_trial_time_options = get_r_trial_time_options()

import { arrayToMap } from "@/utils/array-utils"

// 约机状态
export const reservationStatusOptions = [
  { label: "草稿待完成", value: "draft" },
  { label: "约机已提交", value: "submitted" },
  { label: "约机已排程", value: "scheduled" },
  { label: "约机已取消", value: "cancelled" }
]

export const reservationStatusMap = arrayToMap(reservationStatusOptions)

export const exportedStatusOptions = [
  { value: false, label: "未导出" },
  { value: true, label: "已导出" },
]

export const exportedStatusMap = Object.fromEntries(
  exportedStatusOptions.map(item => [item.value, item.label])
)

export const trialStageOptions = [
  { label: "T0", value: 0 },
  { label: "T1", value: 1 },
  { label: "T2", value: 2 },
  { label: "T3", value: 3 },
  { label: "T4", value: 4 },
  { label: "T5", value: 5 },
  { label: "T6", value: 6 },
  { label: "T7", value: 7 },
  { label: "T8", value: 8 },
  { label: "T9", value: 9 },
  { label: "T10", value: 10 },
  { label: "T11", value: 11 },
  { label: "T12", value: 12 },
  { label: "T13", value: 13 },
  { label: "T14", value: 14 },
  { label: "T15", value: 15 },
  { label: "T16", value: 16 },
  { label: "T17", value: 17 },
  { label: "T18", value: 18 },
  { label: "T19", value: 19 },
  { label: "T20", value: 20 }
]

export const trialIterationOptions = [
  { label: "0", value: 0 }, 
  { label: "1", value: 1 }, 
  { label: "2", value: 2 },
  { label: "3", value: 3 },
  { label: "4", value: 4 },
  { label: "5", value: 5 },
  { label: "6", value: 6 },
  { label: "7", value: 7 },
  { label: "8", value: 8 },
  { label: "9", value: 9 }
]

export const dryRunCountOptions = [
  { label: "0", value: 0 },
  { label: "300", value: 300 },
  { label: "1000", value: 1000 },
]

export const booleanOptions = [
  { label: "是", value: true },
  { label: "否", value: false }
]

export const trialPlaceOptions = [
  { label: "内部", value: "内部" },
  { label: "委外", value: "委外" }
]

export const specialProcessOptions = [
  { label: "无", value: "无" },
  { label: "蒸汽", value: "蒸汽" },
  { label: "氮气", value: "氮气" },
  { label: "电加热", value: "电加热" },
  { label: "油加热", value: "油加热" }
]

export const outsourceReasonOptions = [
  { label: "客户要求第一套影响", value: "客户要求第一套影响" },
  { label: "内部计划太多排不上", value: "内部计划太多排不上" },
  { label: "胶量不够，射胶压力不够", value: "胶量不够，射胶压力不够" },
  { label: "立式机、平衡炮筒台双色、天侧副炮", value: "立式机、平衡炮筒台双色、天侧副炮" },
  { label: "机械手行程不够", value: "机械手行程不够" },
  { label: "吹氮气", value: "吹氮气" },
  { label: "客户指定机台", value: "客户指定机台" },
  { label: "锁模力不够", value: "锁模力不够" },
  { label: "1500T以上模具及其它", value: "1500T以上模具及其它" },
]

export const tkTrialAimOptions = [
  { label: "客看试模", value: false },
  { label: "T0交板", value: false },
  { label: "啤板", value: false },
  { label: "自检模", value: false },
  { label: "C-RUN", value: false },
  { label: "换款", value: false },
  { label: "修模验证", value: false },
  { label: "改模验证", value: false },
  { label: "试产验证", value: false },
  { label: "生产送样", value: false },
  { label: "预验收", value: false },
]

export const hisenseTrialAimOptions = [
  { label: "客看试模", value: false },
  { label: "正常验证", value: false },
  { label: "设计验证", value: false },
  { label: "研配验证", value: false },
  { label: "皮纹验证", value: false },
  { label: "热流道验证", value: false },
  { label: "产品设变", value: false },
  { label: "客户验收", value: false },
]

// 寄件原因
export const sendReasonOptions = [
  { label: "客户要求", value: "客户要求" }, // en: customer request
  { label: "样件质量问题", value: "样件质量问题" }, // en: sample quality issue
  { label: "样件数量异常", value: "样件数量异常" }, // en: abnormal sample quantity
  { label: "内部检讨发件", value: "内部检讨发件" }, // en: internal review dispatch
]

// 供料方式
export const materialSupplyOptions = [
  { label: "客供", value: "客供" }, // en: external supply
  { label: "自购", value: "自购" }, // en: self supply
]

// 包装要求
export const packagingRequirementOptions = [
  { label: "不制作包装箱", value: "不制作包装箱" }, // en: no packaging box
  { label: "按标准制作", value: "按标准制作" }, // en: make according to standard
  { label: "有特殊要求", value: "有特殊要" }, // en: special requirements (write in remarks)
]

// 外包装要求
export const outerPackagingOptions = [
  { value: "12\"×12\"×7\"", label: "12\"×12\"×7\"" },
  { value: "20\"×16\"×11\"", label: "20\"×16\"×11\"" },
  { value: "20\"×20\"×17\"", label: "20\"×20\"×17\"" },
  { value: "30\"×30\"×17\"", label: "30\"×30\"×17\"" },
  { value: "12.6\"×8.7\"×6.9\"", label: "12.6\"×8.7\"×6.9\"" },
  { value: "25\"×25\"×17\"", label: "25\"×25\"×17\"" },
  { value: "35\"×25\"×17\"", label: "35\"×25\"×17\"" },
  { value: "40\"×35\"×34\"", label: "40\"×35\"×34\"" },
]

// 内包装要求
export const innerPackagingOptions = [
  { value: "PE胶带", label: "PE胶带" },
  { value: "珍珠棉袋", label: "珍珠棉袋" },
  { value: "发泡胶", label: "发泡胶" },
  { value: "气泡袋", label: "气泡袋" },
  { value: "保护胶纸", label: "保护胶纸" },
]


// 运输方式
export const transportMethodOptions = [
  { label: "国际海运", value: "国际海运" }, // en: international sea
  { label: "国际火车", value: "国际火车" }, // en: international train
  { label: "国际空运", value: "国际空运" }, // en: international air
  { label: "国际快递", value: "国际快递" }, // en: international express
  { label: "国内包车", value: "国内包车" }, // en: domestic car
  { label: "国内空运", value: "国内空运" }, // en: domestic air
  { label: "国内快递", value: "国内快递" }, // en: domestic express
  { label: "国内陆运", value: "国内陆运" }, // en: domestic land
  { label: "随模发送", value: "随模发送" }, // en: send with mold
]

export const sampleStatusOptions = [
  { value: "常规", label: "常规" },
  { value: "透明", label: "透明" },
  { value: "寄客户", label: "寄客户" },
]

export const tempControlOptions = [
  { value: "热水", label: "热水" },
  { value: "常温水", label: "常温水" },
  { value: "冻水", label: "冻水" },
  { value: "热油", label: "热油" },
  { value: "发热管", label: "发热管" },
]

export const liftHolesOptions = [
  { value: "M12", label: "M12" },
  { value: "M16", label: "M16" },
  { value: "M20", label: "M20" },
  { value: "M24", label: "M24" },
  { value: "M30", label: "M30" },
  { value: "M36", label: "M36" },
  { value: "M42", label: "M42" },
  { value: "M48", label: "M48" },
  { value: "M64", label: "M64" },
]
export const closedPinOptions = [
  { value: "气压驱动", label: "气压驱动" },
  { value: "油压驱动", label: "油压驱动" },
]

export const losedPinOptions = [
  { value: "气压驱动", label: "气压驱动" },
  { value: "油压驱动", label: "油压驱动" },
]

export const treadOptions = [
  { value: "M16", label: "M16" },
  { value: "M24", label: "M24" },
]
export const resetOptions = [
  { value: "弹回", label: "弹回" },
  { value: "拉回", label: "拉回" },
  { value: "压回", label: "压回" },
]
export const flangeOptions = [
  { value: "0", label: "0" },
  { value: "100", label: "100" },
  { value: "125", label: "125" },
  { value: "150", label: "150" },
  { value: "200", label: "200" },
  { value: "250", label: "250" },
]

export const addictiveOptions = [
  { value: "10%GF", label: "10%GF" },
  { value: "15%GF", label: "15%GF" },
  { value: "20%GF", label: "20%GF" },
  { value: "30%GF", label: "30%GF" },
  { value: "50%GF", label: "50%GF" },
  { value: "60%GF", label: "60%GF" },
  { value: "20%Talc", label: "20%Talc" },
  { value: "40%Talc", label: "40%Talc" },
  { value: "20%CaCO3", label: "20%CaCO3" },
]
export const colorOptions = [
  { value: "黑色", label: "黑色" },
  { value: "白色", label: "白色" },
  { value: "透明", label: "透明" },
  { value: "灰色", label: "灰色" },
  { value: "蓝色", label: "蓝色" },
  { value: "红色", label: "红色" },
  { value: "黄色", label: "黄色" },
  { value: "紫色", label: "紫色" },
]

export const machineTypeOptions = [
  { value: "单色", label: "单色" },
  { value: "双色", label: "双色" },
  { value: "三色", label: "三色" },
  { value: "四色", label: "四色" },
  { value: "五色", label: "五色" },
  { value: "六色", label: "六色" },
  { value: "七色", label: "七色" },
]

export const moldTypeOptions = [
  { value: "单腔模具", label: "单腔模具" },
  { value: "多腔模具", label: "多腔模具" },
  { value: "家族模具", label: "家族模具" }
]

export const moldTypeNumber = {
  单色: 1,
  双色: 2,
  三色: 3,
  四色: 4,
  五色: 5,
  六色: 6,
  七色: 7,
}

export const departmentOptions = [

  { value: 1, label: "制作一部" },
  { value: 2, label: "制作二部" },
  { value: 3, label: "制作三部" },
  { value: 4, label: "制作四部" },
  { value: 5, label: "制作五部" },
  { value: 6, label: "制作六部" },
  { value: 7, label: "CE事业单位一" },
  { value: 8, label: "CE事业单位二" },
  { value: 9, label: "包装事业单位一" },
  { value: 10, label: "精密医疗模具一部" },
]

export const level3factor1 = [
  [1],
  [1],
  [1],
  [2],
  [2],
  [2],
  [3],
  [3],
  [3]
]

export const level3factor2 = [
  [1, 1],
  [1, 2],
  [1, 3],
  [2, 1],
  [2, 2],
  [2, 3],
  [3, 1],
  [3, 2],
  [3, 3]
]

export const level3factor3 = [
  [1, 1, 1],
  [1, 2, 2],
  [1, 3, 3],
  [2, 1, 2],
  [2, 2, 3],
  [2, 3, 1],
  [3, 1, 3],
  [3, 2, 1],
  [3, 3, 2]
]

export const level3factor4 = [
  [1, 1, 1, 1],
  [1, 2, 2, 2],
  [1, 3, 3, 3],
  [2, 1, 2, 3],
  [2, 2, 3, 1],
  [2, 3, 1, 2],
  [3, 1, 3, 2],
  [3, 2, 1, 3],
  [3, 3, 2, 1]
]

export const level3factor5 = [
  [1, 1, 1, 1, 1],
  [1, 2, 2, 2, 2],
  [1, 3, 3, 3, 3],
  [2, 1, 1, 2, 2],
  [2, 2, 2, 3, 3],
  [2, 3, 3, 1, 1],
  [3, 1, 2, 1, 3],
  [3, 2, 3, 2, 1],
  [3, 3, 1, 3, 2],
  [1, 1, 3, 3, 2],
  [1, 2, 1, 1, 3],
  [1, 3, 2, 3, 1],
  [2, 1, 2, 3, 1],
  [2, 2, 3, 1, 2],
  [2, 3, 1, 2, 3],
  [3, 1, 3, 2, 3],
  [3, 2, 1, 3, 1],
  [3, 3, 2, 1, 2]
]

export const level3factor6 = [
  [1, 1, 1, 1, 1, 1],
  [1, 2, 2, 2, 2, 2],
  [1, 3, 3, 3, 3, 3],
  [2, 1, 1, 2, 2, 3],
  [2, 2, 2, 3, 3, 1],
  [2, 3, 3, 1, 1, 2],
  [3, 1, 2, 1, 3, 2],
  [3, 2, 3, 2, 1, 3],
  [3, 3, 1, 3, 2, 1],
  [1, 1, 3, 3, 2, 2],
  [1, 2, 1, 1, 3, 3],
  [1, 3, 2, 3, 1, 1],
  [2, 1, 2, 3, 1, 3],
  [2, 2, 3, 1, 2, 1],
  [2, 3, 1, 2, 3, 2],
  [3, 1, 3, 2, 3, 1],
  [3, 2, 1, 3, 1, 2],
  [3, 3, 2, 1, 2, 3]
]

export const level3factor7 = [
  [1, 1, 1, 1, 1, 1, 1],
  [1, 2, 2, 2, 2, 2, 2],
  [1, 3, 3, 3, 3, 3, 3],
  [2, 1, 1, 2, 2, 3, 3],
  [2, 2, 2, 3, 3, 1, 1],
  [2, 3, 3, 1, 1, 2, 2],
  [3, 1, 2, 1, 3, 2, 3],
  [3, 2, 3, 2, 1, 3, 1],
  [3, 3, 1, 3, 2, 1, 2],
  [1, 1, 3, 3, 2, 2, 1],
  [1, 2, 1, 1, 3, 3, 2],
  [1, 3, 2, 3, 1, 1, 3],
  [2, 1, 2, 3, 1, 3, 2],
  [2, 2, 3, 1, 2, 1, 3],
  [2, 3, 1, 2, 3, 2, 1],
  [3, 1, 3, 2, 3, 1, 2],
  [3, 2, 1, 3, 1, 2, 3],
  [3, 3, 2, 1, 2, 3, 1]
]

export const level3factor8 = [
  [1 ,1 ,1 ,1 ,1 ,1 ,1 ,1],
  [1 ,1 ,1 ,1 ,2 ,2 ,2 ,2],
  [1 ,1 ,1 ,1 ,3 ,3 ,3 ,3],
  [1 ,2 ,2 ,2 ,1 ,1 ,1 ,2],
  [1 ,2 ,2 ,2 ,2 ,2 ,2 ,3],
  [1 ,2 ,2 ,2 ,3 ,3 ,3 ,1],
  [1 ,3 ,3 ,3 ,1 ,1 ,1 ,3],
  [1 ,3 ,3 ,3 ,2 ,2 ,2 ,1],
  [1 ,3 ,3 ,3 ,3 ,3 ,3 ,2],
  [2, 1, 2, 3, 1, 2, 3, 1],
  [2, 1, 2, 3, 2, 3, 1, 2],
  [2, 1, 2, 3, 3, 1, 2, 3],
  [2, 2, 3, 1, 1, 2, 3, 2],
  [2, 2, 3, 1, 2, 3, 1, 3],
  [2, 2, 3, 1, 3, 1, 2, 1],
  [2, 3, 1, 2, 1, 2, 3, 3],
  [2, 3, 1, 2, 2, 3, 1, 1],
  [2, 3 ,1, 2, 3, 1, 2, 2],
  [3, 1, 3, 2, 1, 3, 2, 1],
  [3, 1, 3, 2, 2, 1, 3, 2],
  [3, 1, 3, 2, 3, 2, 1, 3],
  [3, 2, 1, 3, 1, 3, 2, 2],
  [3, 2, 1, 3, 2, 1, 3, 3],
  [3, 2, 1, 3, 3, 2, 1, 1],
  [3, 3, 2, 1, 1, 3, 2, 3],
  [3, 3, 2, 1, 2, 1, 3, 1],
  [3, 3, 2, 1, 3, 2, 1, 2]
]

// commonMethods.js

import { MessageBox, Message } from "element-ui"
import { datetimeToday, dateToDatetime } from "@/utils/datetime"

interface Row {
    [key: string]: any;
  }
  
  interface ReservationMethod {
    edit(update_info: any, id: number): Promise<any>;
  }
  
  interface ListDataMethod {
    (): void;
  }
  
export function handleConfirmMoldInfo(
  prop: string,
  row: Row,
  reservationMethod: ReservationMethod,
  getListData: ListDataMethod
): void {
  let msg = ""
  if (row[prop]) {
    // 在有值的情况下，考虑用户为什么要取消，提供修改和取消服务
    msg = "如果您需要重置日期，请点击重置，当前日期信息将会置为空。如果当前日期不准确，您需要手动修改日期，请输入日期，并点击修改。"
    MessageBox.prompt(msg, "提示", {
      confirmButtonText: "修改",
      cancelButtonText: "重置",
      inputValue: row[prop],
      inputPattern: /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/,
      inputErrorMessage: "日期格式不正确"
    }).then((value:any) => {
      const update_info = getUpdateInfo(prop, dateToDatetime(value))
      reservationMethod.edit(update_info, row.id)
        .then(res => {
          if (res.status === 0) {
            Message({
              type: "success",
              message: "更新成功！"
            })
            getListData()
          }
        })
    }).catch(() => {
      const update_info = getUpdateInfo(prop, null)
      reservationMethod.edit(update_info, row.id)
        .then(res => {
          if (res.status === 0) {
            Message({
              type: "info",
              message: "重置成功"
            })
            getListData()
          }
        })
    })
  } else {
    if (prop == "mold_arrive_at") {
      msg = "当前时间将被记录为模具实际到模时间，请确认是否继续？"
    } else if (prop == "mold_hold_at") {
      msg = "当前时间将被记录为模具实际挂模时间，请确认是否继续？"
    }
    MessageBox.confirm(msg, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    }).then(() => {
      const update_info = getUpdateInfo(prop, datetimeToday())
      reservationMethod.edit(update_info, row.id)
        .then(res => {
          if (res.status === 0) {
            Message({
              type: "success",
              message: "当前时间已记录！"
            })
            getListData()
          }
        })
    }).catch(() => {
      Message({
        type: "info",
        message: "已取消操作"
      })          
    })
  }
}
function getUpdateInfo(prop: string, value: string | null): any {
  if (prop === "mold_arrive_at") {
    return {
      reservation_index: {
        mold_arrive_at: value
      }
    }
  } else if (prop === "mold_hold_at") {
    return {
      reservation_index: {
        mold_hold_at: value
      }
    }
  }
  return {}
}


export const mockAdaptionInfo = {
  mold_info: {
    mold_no: "M2025-DUAL-001",
    mold_name: "双色车灯罩模具",
    cavity_layout: "1+1",
    category: "双色模",
    mold_length: 600,
    mold_width: 500,
    mold_thickness: 320,
    min_clamping_force: 90,
    recommended_opening_stroke: 450,
    ejection_stroke: 110,
    ejection_type: "液压",
    locating_ring_outer_dia: 100,
    runner_type: "热流道",
    gating_systems: [
      { sprue_bushing_radius: 15, sprue_bushing_bore_dia: 4.0 },
      { sprue_bushing_radius: 12, sprue_bushing_bore_dia: 3.5 }
    ]
  },
  machine_list: [
    {
      id: 1,
      device_no: "HTF-200D",
      model: "海天 HTF200 双色机",
      location: "注塑车间A-03",
      machine_type: "全电动双色机",
      min_mold_length: 400,
      max_mold_length: 800,
      min_mold_width: 300,
      max_mold_width: 700,
      min_mold_thickness: 200,
      max_mold_thickness: 400,
      max_clamping_force: 200,
      max_opening_stroke: 600,
      ejection_stroke: 120,
      ejection_type: "液压",
      locating_hole_diameter: 120,
      nozzle_type: "标准热流道",
      injection_units: [
        { nozzle_sphere_radius: 16, nozzle_hole_diameter: 4.2 },
        { nozzle_sphere_radius: 13, nozzle_hole_diameter: 3.6 }
      ]
    },
    {
      id: 2,
      device_no: "ZXC-150S",
      model: "震雄 ZXC150 单色机",
      location: "注塑车间B-01",
      machine_type: "液压单色机",
      min_mold_length: 300,
      max_mold_length: 600,
      min_mold_width: 250,
      max_mold_width: 550,
      min_mold_thickness: 180,
      max_mold_thickness: 350,
      max_clamping_force: 150,
      max_opening_stroke: 500,
      ejection_stroke: 100,
      ejection_type: "机械",
      locating_hole_diameter: 100,
      nozzle_type: "标准",
      injection_units: [
        { nozzle_sphere_radius: 15, nozzle_hole_diameter: 4.0 }
      ]
    }
  ]
}
