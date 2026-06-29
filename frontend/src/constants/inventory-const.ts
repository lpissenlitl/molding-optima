export const materialForm = {
  id: null,
  material_code: "",
  material_name: "",
  specification: "",
  category: "原料",
  unit: "",
  color: null,
  
  material_source: "自购",
  material_grade: null,
  sap_material_code: null,
  mold_no: null,
  polymer_id: null,
  filler: null,
  colorant: null,
  
  customer_company: null,
  is_old_rule: null,
  is_active: true,
  remarks: null,
  purchase_cycle: null,
}

export const matstockForm = {
  ...materialForm,
  material_id: null,
  warehouse: "总仓",
  on_hand_quantity: 0, // 初始库存，可为空
  receive_quantity: 0, // 新增入库数量
}

export const purchaseForm = {
  // --- 模具信息 ---
  mold_id: null,
  mold_no: null,
  // --- 项目信息 ---
  project_manager: null,
  // --- 约机信息 ---
  reservation_id: null,
  trial_version: null,
  preferred_trial_start_at: null,
  is_tf_trial: null,
  // --- 注塑机信息 ---
  machine_id: null,
  device_no: null,
  // --- 标准工时/用料
  trial_quantity: null,
  screw_clearing_weight: null,
  // --- 物料信息 ---
  material_id: null,
  material_source: null,
  material_code: null,
  sap_material_code: null,
  unit: null,
  purchase_cycle: null,
  category: null,
  material_name: null,
  filler: null,
  material_grade: null,
  color: null,
  customer_company: null,
  // --- 样件需求 ---
  sample_weight: null,
  sample_count: null,
  // --- 库存&采购 --
  status: "pending",
  all_on_hand_quantity: null,
  purchase_quantity: null,
  remarks: null,
  purchase_code: null,
  is_maintained_in_sap: null,
  is_received: null,
}

export const maintainedStatusOptions = [
  { value: "ignored", label: "无需维护" },
  { value: false, label: "未维护" },
  { value: true, label: "已维护" },
  // { value: null, label: "未维护" },
]

export const maintainedStatusMap = Object.fromEntries(
  maintainedStatusOptions.map(item => [item.value, item.label])
)

export const receivedStatusOptions = [
  { value: false, label: "未到货" },
  { value: true, label: "已到货" },
  // { value: null, label: "未到货" },
]

export const receivedStatusMap = Object.fromEntries(
  receivedStatusOptions.map(item => [item.value, item.label])
)

export const exportedStatusOptions = [
  { value: false, label: "未导出" },
  { value: true, label: "已导出" },
  // { value: null, label: "未导出" },
]

export const exportedStatusMap = Object.fromEntries(
  exportedStatusOptions.map(item => [item.value, item.label])
)

export const requisitionForm = {
  id: null,
  status: "pending",
  reservation_id: null,
  mold_id: null,
  mold_no: null,
  trial_version: null,
  lines: []
}

export const packagingMatForm = {
  id: null,
  status: null,
  reservation_id: null,
  mold_no: null,
  trial_version: null,
  first_mold_no: null,
  initiator: null,
  category: null,
  pre_trial_version: null,
  transport_method: null,
  sample_quantity: null,
  new_sample_quantity: null,
  preferred_trial_start_at: null,
  packaging_requirement: null,
  table_data: []
}

export const categoryOptions = [
  { label: "原料", value: "原料" },
  { label: "色母", value: "色母" },
  { label: "嵌件", value: "嵌件" },
  { label: "包装", value: "包装" }
]

export const unitOptions = [
  { value: "kg", label: "kg" },
  { value: "g", label: "g" },
  { value: "pcs", label: "pcs" },
  { value: "m", label: "m" },
  { value: "cm", label: "cm" },
  { value: "mm", label: "mm" },
  { value: "m²", label: "m²" },
  { value: "cm²", label: "cm²" }
]

export const matReqStatusOptions = [
  { value: "pending", label: "待确认就位" },
  { value: "approved", label: "已审批" },
  { value: "rejected", label: "拒绝" },
  { value: "completed", label: "已完成" },
  { value: "stock_sufficient", label: "库存充足" },
  { value: "stock_insufficient", label: "库存不足" },
]

export const matReqStatusMap = Object.fromEntries(
  matReqStatusOptions.map(item => [item.value, item.label])
)


export const matPurchaseStatusOptions = [
  { value: "ignored", label: "无需审核" },
  { value: "pending", label: "待审核" },
  { value: "approved", label: "审核通过" },
  { value: "rejected", label: "审核拒绝" },
  // { value: "exported", label: "已导出" },
]

export const matPurchaseStatusMap = Object.fromEntries(
  matPurchaseStatusOptions.map(item => [item.value, item.label])
)

export const packagingMatStatusOptions = [
  { value: "draft", label: "草稿" },
  { value: "saved", label: "已保存" },
]

export const packagingMatStatusMap = Object.fromEntries(
  packagingMatStatusOptions.map(item => [item.value, item.label])
)

export const colorAbbreviationOptions = [
  { label: "NC", value: "NC" },
  { label: "BK", value: "BK" },
  { label: "WH", value: "WH" },
  { label: "GY", value: "GY" },
  { label: "RE", value: "RE" },
  { label: "YL", value: "YL" },
  { label: "GR", value: "GR" },
  { label: "BL", value: "BL" },
  { label: "TC", value: "TC" },
]

export const matSrcOptions = [
  { label: "自购", value: "自购" },
  { label: "客供", value: "客供" },
]

export const IsOldRuleOptions = [
  { value: true, label: "是" },
  { value: false, label: "否" },
]

export const isActiveOptions = [
  { value: true, label: "是" },
  { value: false, label: "否" },
]


export function generateOldMaterialCode(
  substr_index: number, 
  original_material_source: string,
  original_material_name: string,
  original_filler_abbreviation_list: string,
  original_spec_or_color_code: string,
  original_color: string,
  original_old_material_code: string,
) {
/**
 * 生成旧物料号
 * @param {number} substr_index 旧物料号生成规则子串索引
 * 将结果保存到original_old_material_code中
 * 
 * 旧物料号生成规则：
 *    1:   YLS‘Z’-‘物料名称’[+‘填充物’]-‘牌号’-’颜色’
 *    2:   YLS‘K’-‘物料名称’-‘牌号’-’颜色’
**/
  if (  !original_material_source || 
        !original_material_name || 
        !original_color) return original_old_material_code
  if (original_old_material_code) { // 已有旧物料号,如果其他字段变化则旧物料号对应的子串修改
    if (original_material_source === "Z") { 
      const pattern = /^YLS([\w]+)-([^+]+)([^-]*)-([^-]*)-([^-]+)$/
      const match = original_old_material_code.match(pattern)
      if (!match) return original_old_material_code
      let material_source = match[1]
      let material_name = match[2]
      let filler_abbreviation_list_str = match[3]
      let spec_or_color_code = match[4]
      let color = match[5]
      switch (substr_index) {
        case 0:
          material_source = original_material_source
          break
        case 1:
          material_name = original_material_name
          break
        case 2:
          filler_abbreviation_list_str = original_filler_abbreviation_list === null || original_filler_abbreviation_list.length === 0 ? 
            "" : 
            [...original_filler_abbreviation_list].sort().map(item => "+" + item).join("")
          break
        case 3:
          spec_or_color_code = original_spec_or_color_code
          break
        case 4:
          color = original_color
      }
      original_old_material_code = `YLS${material_source}-${material_name}${filler_abbreviation_list_str}-${spec_or_color_code}-${color}`
    } else if (original_material_source === "K") {
      if (substr_index === 2) return original_old_material_code
      const pattern = /^YLS([\w]+)-([^-]+)-([^-]*)-([^-]+)$/
      const match = original_old_material_code.match(pattern)
      if (!match) return original_old_material_code
      let material_source = match[1]
      let material_name = match[2]
      let spec_or_color_code = match[3]
      let color = match[4]
      switch (substr_index) {
        case 0:
          material_source = original_material_source
          break
        case 1:
          material_name = original_material_name
          break
        case 3:
          spec_or_color_code = original_spec_or_color_code
          break
        case 4:
          color = original_color
      }
      original_old_material_code = `YLS${material_source}-${material_name}-${spec_or_color_code}-${color}`
    }
  } else { // 新物料号生成
    if (original_material_source === "Z") {
      const filler_abbreviation_list_str = original_filler_abbreviation_list === null || original_filler_abbreviation_list.length === 0 ? 
        "" : 
        [...original_filler_abbreviation_list].sort().map(item => "+" + item).join("")
        
      original_old_material_code = `YLS${original_material_source}-${original_material_name}${filler_abbreviation_list_str}-${original_spec_or_color_code}-${original_color}`
    } else if (original_material_source === "K") {
      original_old_material_code = `YLS${original_material_source}-${original_material_name}-${original_spec_or_color_code}-${original_color}`
    }
  }
  return original_old_material_code
}