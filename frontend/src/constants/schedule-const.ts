export const scheduleForm = {
  id: null,
  reservation_no: "RES-2025-001",
  status: "pending",
  project: null,
  inj_mac_model: null,
  inj_mac_device_no: null,
  mold_no: null,
  applicant: null,
  planner: null,
  scheduled_start_at: null,
  scheduled_end_at: null,
  remarks: null,
  planned_ready_at: null,
  planned_mold_mount_start_at: null,
  planned_mold_mount_end_at: null,
  trial_scenarios_plan: [{
    planned_mold_mount_start_at: null,
    planned_mold_mount_end_at: null,
    planned_debug_start_at: null,
    planned_debug_end_at: null,
    planned_production_start_at: null,
    planned_production_end_at: null,
    planned_mold_unmount_start_at: null,
    planned_mold_unmount_end_at: null,
    remarks: null,
  }],
  planned_mold_unmount_start_at: null,
  planned_mold_unmount_end_at: null,
  trial_location: null,
  outsourcing_reason: null,
}

export const planDetailedForm = {
  id: null,
  scheduled_start_at: null,
  scheduled_end_at: null,
  planned_ready_at: null,
  planned_mold_mount_start_at: null,
  planned_mold_mount_end_at: null,
  trial_scenarios_plan: [{
    planned_debug_start_at: null,
    planned_debug_end_at: null,
    planned_production_start_at: null,
    planned_production_end_at: null,
    remarks: null,
  }],
  planned_mold_unmount_start_at: null,
  planned_mold_unmount_end_at: null,
}

export const scheduleStatusOptions = [
  { label: "约机待排程", value: "proposed" },
  { label: "约机已取消", value: "cancelled" },
  { label: "约机已删除", value: "deleted" },
  { label: "计划已排程", value: "scheduled" },
  { label: "计划已确认", value: "confirmed" },
  { label: "计划已取消", value: "rejected" },
  { label: "试模已完备", value: "ready" },
  { label: "试模进行中", value: "trial_started" },
  { label: "试模已完成", value: "trial_completed" },
  { label: "委外试模", value: "outsourcing" },
]

// 自动生成映射表
export const scheduleStatusMap = Object.fromEntries(
  scheduleStatusOptions.map(item => [item.value, item.label])
)

export const exportedStatusOptions = [
  { value: false, label: "未导出" },
  { value: true, label: "已导出" },
]

export const exportedStatusMap = Object.fromEntries(
  exportedStatusOptions.map(item => [item.value, item.label])
)

// 计划锁定状态
export const lockedStatus = [
  "confirmed",
  "ready",
  "trial_started",
  "trial_completed",
  "outsourcing",
]

// 激活状态
export const activeStatus = [
  "proposed", 
  "scheduled", 
  ...lockedStatus
]

// 计划未确认状态
export const unconfirmedStatus = [
  ...activeStatus,
  "rejected" 
]

// 计划确认状态
export const confirmedStatus = [
  ...lockedStatus
]

export const lockedStatusOptions = [
  { label: "计划已排程", value: "scheduled" },
  { label: "计划已确认", value: "confirmed" },
  { label: "试模已完备", value: "ready" },
  { label: "试模进行中", value: "trial_started" },
  { label: "试模已完成", value: "trial_completed" },
  { label: "委外试模", value: "outsourcing" },
]

// 非激活状态
export const inactiveStatus = [
  "cancelled", 
  "rejected",
]

// 视为已试模完备的计划表状态
export const readiedStatus = [
  "ready", 
  "trial_started",
]

// 状态配置
export const scheduleStatusConfig = {
  proposed: { label: "待排程", type: "info" },
  scheduled: { label: "已排程", type: "primary" },
  committed: { label: "计划试模", type: "success" },
  detailed: { label: "计划细化", type: "success" },
  confirmed: { label: "等待完备", type: "success" },
  ready: { label: "已完备", type: "success" },
  trial_started: { label: "转至试模", type: "success" },
  trial_completed: { label: "试模完成", type: "success" },
  outsourcing: { label: "委外试模", type: "warning" },
  rejected: { label: "机台不足", type: "danger" },
  cancelled: { label: "已取消", type: "danger" },
}

//模具审批流程中各角色
export const enum MoldApprovalRole { 
  applicant = "审批发起人",
  inspector = "检验员",
  assembly_room_director = "装配室主任",
  project_manager = "项目经理",
  department_head = "申请部门部长",
  qa_department_head = "品质保证部部长",
}

// ====================== 委外试模申请 ======================
// 申请单状态选项
export const outsourcingApplicationStatusOptions = [
  { label: "草稿", value: "draft" },
  { label: "已提交", value: "submitted" },
  { label: "审批中", value: "in_review" },
  { label: "已批准", value: "approved" },
  { label: "已驳回", value: "rejected" },
  { label: "已取消", value: "cancelled" },
]

// 申请单状态映射表
export const outsourcingApplicationStatusMap = Object.fromEntries(
  outsourcingApplicationStatusOptions.map(item => [item.value, item.label])
)

// 申请单状态标签样式（使用系统功能色变量）
export const outsourcingApplicationStatusTypeMap = {
  draft: { label: "草稿", type: "info" },
  submitted: { label: "已提交", type: "primary" },
  in_review: { label: "审批中", type: "primary" },
  approved: { label: "已批准", type: "success" },
  rejected: { label: "已驳回", type: "danger" },
  cancelled: { label: "已取消", type: "info" },
}

// 审批流程角色
export const enum OutsourcingApprovalRole {
  trial_team = "试模组",
  project_team = "项目组",
  manufacturing = "制造审批",
  manufacturing_director = "制造部长",
  qa_director = "品保部长",
}

