
// 试模完备状态
export const readinessStatusOptions = [
  { label: "进行中", value: "in_progress" },
  { label: "受阻", value: "blocked" },
  { label: "已就绪", value: "ready" }
]

export const readinessStatusMap = Object.fromEntries(
  readinessStatusOptions.map(item => [item.value, item.label])
)

export const initialChecklist = [
  {
    serial_no: 1,
    inspection_key: "safety",
    inspection_item: "安全",
    inspection_criteria: [
      "《模具仕样书》→确认模具整体重量（吨）。",
      "《模具起吊标准》→选用吊环规格和起吊方式。",
      "《模具仕样书》→确认安装动、静模定位圈。"
    ],
    judgment: null, // 'OK' | 'NG' | 'NA'
    critical: true,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 2,
    inspection_key: "circuit",
    inspection_item: "水-油-气路系统",
    inspection_criteria: [
      "高压气-清洗剂，按模型横向-竖向、反复吹洗深孔。",
      "设计模型:1in→1out,2in→2out...方式连接。",
      "1in→1out,2in→out...测试水路：流量。",
      "1in→1out,2in→out...测试水路：密封。"
    ],
    judgment: null,
    critical: true,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 3,
    inspection_key: "hotrunner",
    inspection_item: "热流道系统",
    inspection_criteria: [
      "模具热流道通电插口（加热圈、热电偶）接线方式和温控柜系统插头接线方式匹配。",
      "通电→加热→升温→控温(200°以上5分钟),温控柜温度数值显示恒定。",
      "阀针式：控温→按动电磁阀开关→阀针运动→阀针长度和直径→封胶。"
    ],
    judgment: null,
    critical: true,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 4,
    inspection_key: "ejection",
    inspection_item: "顶出系统",
    inspection_criteria: [
      "扁顶杆、方顶杆、斜顶杆有效配合段下，运动行程有避空。",
      "顶杆固定板运动到顶出限位块，斜顶和滑座组合运动行程有避空。",
      "测试→顶出→斜顶止转-顶块止转→回位垃圾钉、限位钉贴合。"
    ],
    judgment: null,
    critical: true,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 5,
    inspection_key: "slide",
    inspection_item: "抽芯、滑块系统",
    inspection_criteria: [
      "压板间隙符合≤0.03mm标准要求。",
      "导轨间隙符合单边≤0.02mm标准要求。",
      "限位面有效性符合零碰零的要求。",
      "高压气、油压机→测试运动→顺畅。"
    ],
    judgment: null,
    critical: true,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 6,
    inspection_key: "limit",
    inspection_item: "限位系统",
    inspection_criteria: [
      "机械限位装置→安装→限位有效→量产可靠。",
      "行程开关→设计要求安装、连接→电筒测试→接口与设备匹配。"
    ],
    judgment: null,
    critical: true,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 7,
    inspection_key: "texture",
    inspection_item: "皮纹腐蚀",
    inspection_criteria: [
      "功能性皮纹（非外观皮纹），工件质量检验EXCEL系统已全部确认合格。",
      "外观类皮纹工件质量检验EXCEL系统已全部确认合格。"
    ],
    judgment: null,
    critical: true,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 8,
    inspection_key: "nitrogen",
    inspection_item: "氮化工件",
    inspection_criteria: [
      "氮化工件质量检验Excel系统已全部确认合格。"
    ],
    judgment: null,
    critical: false,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 9,
    inspection_key: "polish",
    inspection_item: "抛光",
    inspection_criteria: [
      "零件→部件，经过抛光组，班长或组长确认。"
    ],
    judgment: null,
    critical: false,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 10,
    inspection_key: "lapping",
    inspection_item: "研模",
    inspection_criteria: [
      "飞模，经过研模班长或组长确认。"
    ],
    judgment: null,
    critical: false,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  },
  {
    serial_no: 11,
    inspection_key: "peripheral",
    inspection_item: "模具外围",
    inspection_criteria: [
      "T1或T2前模具外围部件安装→符合模型→《模具仕样书》→客户标准。"
    ],
    judgment: null,
    critical: false,
    confirmed_by: null,
    confirmed_at: null,
    remarks: null
  }
]

export const initialConfirmItems = [
  {
    "content": "动作顺畅",
    "judgment": null,
  },
  {
    "content": "水路通畅",
    "judgment": null,
  },
  {
    "content": "汽车模具水流量符合标准（T1)",
    "judgment": null,
  },
  {
    "content": "气路油路电路通畅",
    "judgment": null,
  },
  {
    "content": "安全装置可靠",
    "judgment": null,
  },
]

export const moldReadinessStatusOptions = [
  { label: "待检查", value: "inspection_pending" },
  { label: "检查中", value: "inspection_in_progress" },
  { label: "发起试模申请", value: "trial_request_submitted" },
  { label: "试模审批中", value: "trial_request_in_review" },
  { label: "试模已批准", value: "trial_request_approved" },
  { label: "试模已驳回", value: "trial_request_rejected" },
  { label: "已计划移交", value: "handover_planned" },
  { label: "移交完成", value: "handover_completed" },
  { label: "已完备", value: "ready" }
]

export const moldRequirementForm = {
  id: null,
  readiness_checklist_id: null,
  mold_no: null,
  mold_name: null,
  schedule_no: null,
  trial_version: null,
  // --- 状态 ---
  status: "inspection_pending",
  // --- 模具自检 ---
  inspection_items: structuredClone(initialChecklist),
  confirm_items: structuredClone(initialConfirmItems),
  inspection_result: null,
  mold_photos: {
    cavity: {},
    core: {} 
  },
  checked_at: null,
  checked_by_name: null,
  // --- 模具移交 ---
  planned_mold_handover_at: null,
  actual_mold_handover_at: null,
  handover_by: null,
  // --- 模具就位 ---
  responsible_user_name: null,
  is_ready: false,
  ready_at: null,
  ready_by: null,
  remarks: null,
} 

export const injectionReadinessStatusOptions = [
  { label: "待确认", value: "pending" },
  { label: "时间冲突", value: "conflict" },
  { label: "保养中", value: "maintenance" },
  { label: "故障", value: "broken" },
  { label: "已完备", value: "ready" }
]

export const injectionMachineRequirementForm = {
  id: null,
  readiness_checklist_id: null,
  mold_no: null,
  mold_name: null,
  schedule_no: null,
  trial_version: null,
  // --- 状态 ---
  status: "pending",
  // --- 注塑机信息 ---
  model: null,
  device_no: null,
  conflicts: [],
  // --- 注塑机就位 ---
  responsible_user_name: null,
  is_ready: false,
  ready_at: null,
  ready_by: null,
  remarks: null,
}

export const materialReadinessStatusOptions = [
  { label: "待确认", value: "pending" },
  { label: "缺料", value: "shortage" },
  { label: "采购中", value: "procurement" },
  { label: "运输中", value: "in_transit" },
  { label: "已到货", value: "received" },
  { label: "齐备", value: "ready" }
]

export const materialRequirementForm = { 
  id: null,
  readiness_checklist_id: null,
  mold_no: null,
  mold_name: null,
  schedule_no: null,
  // --- 状态 ---
  status: "pending",
  // --- 物料需求 ---
  material_requiring: {},
  // --- 烘料信息 ---
  drying_info: {
    is_drying: false,
    drying_machine: null,
    drying_amount: null,
    drying_start_time: null,
    drying_end_time: null,
    is_drying_completed: false,
  },
  // --- 物料就为 ---
  is_ready: false,
  ready_at: null,
  ready_by: null,
  remarks: null,
}

export const auxiliaryReadinessStatusOptions = [
  { label: "待确认", value: "pending" },
  { label: "数量不足", value: "shortage" },
  { label: "齐备", value: "ready" }
]

export const auxiliaryRequirementForm = {
  id: null,
  mold_no: null,
  mold_name: null,
  schedule_no: null,
  trial_version: null,
  // --- 状态 ---
  status: "pending",
  // --- 注塑机信息 ---
  auxiliary_requiring: {},
  // --- 注塑机就位 ---
  responsible_user_name: null,
  is_ready: false,
  ready_at: null,
  ready_by: null,
  remarks: null,
}

export const readinessStatusLabelMap = {
  // 模具 (Mold)
  inspection_pending: "待检查",
  inspection_in_progress: "检查中",
  trial_request_submitted: "发起试模申请",
  trial_request_in_review: "试模审批中",
  trial_request_approved: "试模已批准",
  trial_request_rejected: "试模已驳回",
  handover_planned: "已计划移交",
  handover_completed: "移交完成",

  // 注塑机 (Injection Machine)
  pending: "待确认",
  conflict: "时间冲突",
  maintenance: "保养中",
  broken: "故障",

  // 物料 (Material)
  shortage: "数量不足",        // 统一用“数量不足”覆盖“缺料”
  position_confirmed: "物料已就位",
  procurement: "采购中",
  in_transit: "运输中",
  received: "已到货",

  // 辅机 (Auxiliary)
  // pending 和 shortage 已定义，无需重复

  // 通用状态
  ready: "已完备"
}