export const projectInfoForm = {
  // --- 核心标识 ---
  id: null,
  project_code: "",
  project_name: "",

  // --- 发起方信息 ---
  initiator: "",
  initiation_reference: "",
  manufacturing_location: "",
  application_industry: "",
  manufacturing_method: "自制",

  // --- 项目分类与评级 ---
  is_premium: false, // BooleanField，默认 false
  importance_level: null, // 可选：'high' | 'medium' | 'low'

  // --- 项目成员 ---
  project_manager: "",
  sales_manager: "",
  project_engineer: "",
  technical_manager: "",
  design_leader: "",
  process_engineer: "",
  fitter: "",

  // --- 合同与计划节点 ---
  contract_date: null,
  contract_t1_date: null,
  contract_factory_delivery_date: null,
  standard_trial_count: null,
  target_new_cycle_days: null,
  target_rework_cycle_days: null,

  // --- 试模相关 ---
  trial_plan_start_date: null,
  trial_plan_end_date: null,

  // --- 实际发生时间 ---
  project_kickoff_date: null,
  work_start_date: null,
  financial_settlement_date: null,

  // --- 状态与协作 ---
  status: null, // 如 'ongoing', 'suspended', 'completed'
  review_status: null, // 如 'pending', 'approved', 'rejected', 'revision_required'
  trial_machine: "",

  // --- 其他 ---
  remarks: "",

  // --- 系统集成字段 ---
  origin_system: "",
  reference_id: "",
  sync_status: "",
  sync_time: null,

  // --- 关联字段（前端可能用不到，但可保留）---
  created_by: null
}

import { arrayToMap } from "@/utils/array-utils"

// 应用行业
export const applicationIndustryOptions = [
  { label: "汽车", value: "汽车" },               // en: automotive
  { label: "家电", value: "家电" },               // en: home_appliance
  { label: "医疗", value: "医疗" },               // en: medical
  { label: "消费电子", value: "消费电子" },       // en: consumer_electronics
  { label: "光伏", value: "光伏" },               // en: photovoltaic
  { label: "包装", value: "包装" },               // en: packaging
  { label: "其他", value: "其他" }                // en: other
]

// 制作方式
export const manufacturingMethodOptions = [
  { label: "自制", value: "自制" },
  { label: "外协", value: "外协" }
]

export const projectStatusOptions = [
  { label: "草稿", value: "draft" },
  { label: "进行中", value: "active" },
  { label: "进行中", value: "ongoing" },
  { label: "暂停", value: "suspended" },
  { label: "完成", value: "completed" }
]

export const projectStatusMap = arrayToMap(projectStatusOptions)

export const reviewStatusOptions = [
  { label: "待评审", value: "待评审" },
  { label: "通过", value: "通过" },
  { label: "不通过", value: "不通过" }
]

export const premiumOptions = [
  { label: "是", value: true },
  { label: "否", value: false }
]

export const importanceLevelOptions = [
  { label: "高", value: "高" },
  { label: "中", value: "中" },
  { label: "低", value: "低" }
]
