/** molding-optima 前端 API 入口：按模块拆分（基础类 → identity → masterdata → process → 通用），所有请求走 /api/ 前缀，后端路由参考 backend/_moldx/urls.py */

import request from '@/utils/request'
import type { ProcessParameterFlat } from '@/views/process/optimization/components/parameterTransform'
import type { TuningResult } from '@/types/optimization'


// ==================== 基础类（BaseRequest 通用 CRUD）====================

/** HTTP 方法类型 */
type HttpMethod = 'get' | 'post' | 'put' | 'delete'

/**
 * 通用 CRUD 请求基类（适用标准 REST 资源：5 种基本操作 + 2 种批量操作）
 *
 * URL 拼接规则（核心约束）：
 * - list / create       → {baseUrl}                       e.g. GET  /api/companies/
 * - detail              → {baseUrl}{id}/                 e.g. GET  /api/companies/123/
 * - 批量操作             → {baseUrl}actions/batch-{verb}/  e.g. DEL  /api/companies/actions/batch-delete/
 *   所有资源统一走 {baseUrl}actions/batch-delete/，不再有例外；新增通用 batch action 加在 batchDelete 同区段
 *
 * 泛型：TQuery = list 查询参数类型，TPayload = create/update 提交数据类型（默认 any）
 *
 * 注：response 返回类型不固定为 Promise<T>，由 request 工具推导 —— axios + 自定义 response 拦截器存在
 *   类型伪冲突（request.ts 已返回 response.data，axios 类型仍包装为 AxiosResponseResult），
 *   需强类型请用函数式 API（见 @/api/rule）
 *
 * 不适用（请用函数式 API）：路径不以上规则的（如 /api/processes/records/{id}/parameter-list/）、
 *   后端要求 PATCH 或自定义 Content-Type、强类型 + 复杂 payload 的资源
 */

class BaseRequest<TQuery = any, TPayload = any> {
  readonly url: string

  constructor(url: string) {
    this.url = url
  }

  /** 列表查询 GET {baseUrl} */
  get(params?: TQuery) {
    return request({
      url: this.url,
      method: 'get',
      params,
    })
  }

  /** 详情 GET {baseUrl}{id}/ */
  getDetail(id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'get',
    })
  }

  /** 创建 POST {baseUrl} */
  add(data: TPayload) {
    return request({
      url: this.url,
      method: 'post',
      data,
    })
  }

  /** 更新 PUT {baseUrl}{id}/ */
  edit(data: TPayload, id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'put',
      data,
    })
  }

  /** 删除 DELETE {baseUrl}{id}/ */
  delete(id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'delete',
    })
  }

  /** 批量删除：DELETE {baseUrl}actions/batch-delete/ */

  batchDelete(params: object) {
    return request({
      url: `${this.url}actions/batch-delete/`,
      method: 'delete',
      data: params,
    })
  }
}


// ---- 身份/权限（identity）：公司 / 组织 / 角色 / 用户，标准 CRUD（BaseRequest 实例）----


export const companyMethod = new BaseRequest('/api/companies/')
export const organizationMethod = new BaseRequest('/api/organizations/')
export const roleMethod = new BaseRequest('/api/roles/')
export const userMethod = new BaseRequest('/api/users/')


// ---- 业务专属函数（按子模块聚合）----

// 公司：状态切换 / 接管 / 释放
export function enableCompany(id: number) {
  return request({
    url: `/api/companies/${id}/enable/`,
    method: 'put',
  })
}
export function disableCompany(id: number) {
  return request({
    url: `/api/companies/${id}/disable/`,
    method: 'put',
  })
}
export function assumeCompany(id: number) {
  return request({
    url: `/api/companies/${id}/assume/`,
    method: 'put',
  })
}
export function releaseCompany(id: number) {
  return request({
    url: `/api/companies/${id}/release/`,
    method: 'put',
  })
}

// 组织：树形结构
/** 获取组织树形结构（?tree=true） */
export const getOrganizationTree = (params?: any) =>
  request({ url: '/api/organizations/', method: 'get', params: { tree: true, ...params } })

/** 调整组织架构：用户拖拽组织节点后，提交受影响兄弟节点的新位置 */

export interface OrganizationStructureItem {
  id: number
  parent_id: number | null
  sort_order: number
  path: string
}
export function reorderOrganizations(orgList: OrganizationStructureItem[]) {
  return request({
    url: '/api/organizations/actions/reorder/',
    method: 'put',
    data: { org_list: orgList },
  })
}

// 角色：启用/禁用 + 权限树
export function enableRole(id: number) {
  return request({
    url: `/api/roles/${id}/enable/`,
    method: 'put',
  })
}
export function disableRole(id: number) {
  return request({
    url: `/api/roles/${id}/disable/`,
    method: 'put',
  })
}
export function getPermissionTree() {
  return request({
    url: '/api/roles/permissions/tree/',
    method: 'get',
  })
}

// 用户：启用/禁用 + 重置密码
export function enableUser(id: number) {
  return request({
    url: `/api/users/${id}/enable/`,
    method: 'put',
  })
}
export function disableUser(id: number) {
  return request({
    url: `/api/users/${id}/disable/`,
    method: 'put',
  })
}
export function resetPassword(id: number, data: object) {
  return request({
    url: `/api/users/${id}/reset-password/`,
    method: 'put',
    data,
  })
}


// ---- 主数据（masterdata）：项目 / 模具 / 聚合物 / 填充物 / 注塑机 / 辅机，标准 CRUD（BaseRequest 实例）----


export const projectMethod = new BaseRequest('/api/projects/')
export const moldMethod = new BaseRequest('/api/molds/')
export const polymerMethod = new BaseRequest('/api/polymers/')
export const fillerMethod = new BaseRequest('/api/fillers/')
export const machineMethod = new BaseRequest('/api/injection-machines/')
export const auxiliaryMethod = new BaseRequest('/api/auxiliary-equipments/')

 
// ==================== 工艺管理（process）====================
// URL 段：records (业务级) / conditions / parameters (数据级) / algorithms (触发器) / rules/ (keywords / methods / libraries / expert-rules)
// 业务级 vs 数据级：records 携 condition+latest parameter 一起返回（id=condition_id）；conditions / parameters 仅当前对象（id=对应对象 id，condition_id 走 query）
// 规则的复杂接口（带强类型 / 详细 payload）见 `@/api/rule`；参数版本树端点暂未挂出，view + service 保留


// ---- 业务级 / 数据级 入口（BaseRequest 实例）----

export const processRecordMethod = new BaseRequest('/api/processes/records/')
export const processConditionMethod = new BaseRequest('/api/processes/conditions/')
export const processParameterMethod = new BaseRequest('/api/processes/parameters/')


// ---- records 业务子资源（GET-only）----

/** 获取某 condition 下的所有 parameter 列表 */
export const processRecordParameterList = (conditionId: number) =>
  request({ url: `/api/processes/records/${conditionId}/parameter-list/`, method: 'get' })

/** 获取某 condition 下的 parameter 版本树 */
export const processRecordParameterTree = (conditionId: number) =>
  request({ url: `/api/processes/records/${conditionId}/parameter-tree/`, method: 'get' })

/** 获取某 condition 下的调机历史（时间线）：一个 parameter = 一轮调机，响应 {condition, count, history[]}，后端按 created_at 倒序（最新一轮在数组头部） */

export const processRecordHistory = (conditionId: number) =>
  request({ url: `/api/processes/records/${conditionId}/history/`, method: 'get' })

/** 工艺条件详情（**扁平** condition 结构：mold_info / machine_info / polymer_info 在顶层，不是 {condition: {...}} 包装） */

export const processConditionDetail = (conditionId: number) =>
  request({ url: `/api/processes/conditions/${conditionId}/`, method: 'get' })

// ---- 调机轮次回显（智能调机页「继续调机」数据源）----

/** 单轮调机的试模反馈（后端 TuningRecord → 前端回显结构） */

export interface TuningRoundFeedback {
  /** 前端评价枚举：qualified/unqualified/effective/unchanged/ineffective/null */
  tuning_result: TuningResult
  /** 库内原始状态：improved / worse / unchanged / qualified / unqualified / pending */
  result: string | null
  /** 该轮试模看到的缺陷（每项含 keyword_id / keyword_name / level / position / position_3d） */
  defect_feedbacks: any[]
  /** 结果详情文本 */
  result_detail: string | null
  /** 该轮自身的算法建议（Recommendation 锚在该轮参数上） */
  suggestion?: {
    source_type: string
    groups: any[]
    /** 是否被采纳（训练标签：标签=变差时后端置 False） */
    adopted?: boolean | null
  }
}

/** 单轮调机（一个 parameter = 一轮）；tuning 与该轮参数配对，不跨轮 */

export interface TuningRoundItem {
  id: number
  seq_idx: number | null
  param_source?: string | null
  /** 工艺参数编号（业务编号，非数据库主键）；历史数据可能为空 */
  parameter_no?: string | null
  created_at?: string | null
  /** 归档标记：该轮已落库评价 ⇒ 参数锁死（只读）。判据由后端给出，前端不自行推算 */
  sealed?: boolean
  /** 该轮自身的试模反馈 */
  tuning?: TuningRoundFeedback
  [k: string]: any
}


// ---- algorithms 段（业务专属 API）----

/** 工艺参数移植：把 source parameter 移植到 target machine */
export const processTransplant = (data: { source_parameter_id: number; target_machine_spec: any }) =>
  request({ url: '/api/processes/algorithms/transplant/', method: 'post', data })

/** 工艺参数初始化（Mode B：基于 masterdata ID 算法生成 + 落库），返回 condition_id / parameter_id / seq_idx / process */

export const processInitializationFromMasterdata = (data: {
  mold_id: number
  polymer_id: number
  injection_machine_id: number
  shot_index?: number
  injection_index?: number
  process_set?: any
}) =>
  request({ url: '/api/processes/algorithms/initialize/', method: 'post', data })

/** 工艺优化 infer（调机迭代核心接口）：必填 condition_id / parent_seq_idx，返回 new_parameter / suggestion；入参 parameter 若用户在 settingProcessForm 改了参数，先由前端 parameterToFlat 翻译为 ProcessParameterFlat 再传入（对齐后端 ProcessParameterSchema），没改则传 undefined（service 从 ORM 反查 parent_param 作 baseline） */

export const processOptimizationInfer = (data: {
  condition_id: number
  parent_seq_idx: number
  parameter?: ProcessParameterFlat
  feedback?: {
    defect?: any[]
    observations?: any[]
    tuning_result?: TuningResult
  }
}) =>
  request({ url: '/api/processes/algorithms/optimize/', method: 'post', data })


// ---- 人工调机反馈（tuning 业务上属于 parameter）----

/** 提交人工调机反馈（TuningRecord 落库，幂等覆盖）：POST /api/processes/parameters/<parameter_id>/tuning-feedback/ */

export interface TuningFeedbackPayload {
  defect_feedbacks?: any[]
  observations?: any[]
  tuning_result?: 'effective' | 'unchanged' | 'ineffective' | 'qualified' | 'unqualified' | 'pending' | null
  result_detail?: string
  /**
   * 本轮实际使用的工艺参数（flat，parameterToFlat 翻译后传入）。
   * 「保存当前工艺」时一并提交 ⇒ 后端同一事务写回参数 + 评价，
   * 语义 = 「我用了这组参数，试模结果是 X」。
   * 省略则只写评价、不动参数。
   */
  parameter?: ProcessParameterFlat
}
export const tuningFeedback = (parameterId: number, payload: TuningFeedbackPayload) =>
  request({
    url: `/api/processes/parameters/${parameterId}/tuning-feedback/`,
    method: 'post',
    data: payload,
  })

/**
 * 以某一轮为基线新建一轮（POST /api/processes/parameters/<id>/clone-round/）
 *
 * 语义：已落库评价的轮次已归档、参数不可改写，但用户可以「回到某一轮重来」。
 * 源轮零改动，新轮未评价 ⇒ 参数可继续编辑。
 */
export const processParameterCloneRound = (parameterId: number) =>
  request({
    url: `/api/processes/parameters/${parameterId}/clone-round/`,
    method: 'post',
  })


// ---- 仪表板统计（analytic：近 30 天趋势 + 起源类型分布）----

/**
 * 仪表板统计聚合（近 30 天趋势 + 起源类型分布）
 * 后端一次性返回 dashboard 全部图表数据，避免前端 N+1 查询：
 * - trend：近 30 天每日新增工艺数（dates/counts）
 * - origin_distribution：按 origin_type 分组的工艺数（饼图用）
 * 响应：{status, msg, data: {trend: {...}, origin_distribution: [...]}}
 */

export const dashboardStatistics = () =>
  request({ url: '/api/analytic/process-statistics/', method: 'get' })


// ---- 报表导出 ----

/** 工艺参数导出模板 */
export type ProcessExportTemplate = 'compact' | 'default' | 'detail'

/** 工艺参数导出（Excel）：processConditionIds 为工艺条件 ID 列表，template 取 compact=精简总览 / default=标准工艺卡 / detail=追溯明细（含工艺上下文），includeSnapshots 控制是否附带「工艺条件快照」列 */

export const processExport = (
  processConditionIds: number[],
  template: ProcessExportTemplate = 'default',
  includeSnapshots = false,
) =>
  request({
    url: '/api/process/export/',
    method: 'post',
    data: {
      process_condition_ids: processConditionIds,
      template,
      include_snapshots: includeSnapshots,
    },
  })


// ---- 文件中心（filecenter）：标准 CRUD（BaseRequest 实例）----


export const fileMethod = new BaseRequest('/api/files/')

// 下载/预览 URL 构造不走 request 拦截器（需在 query 里手动带 token），已在 utils/assert.ts 提供 getFileDownloadUrl / getFilePreviewUrl



// ==================== 通用工具/横切 ====================

export const getSelectionOptions = (params: any) =>
  request({ url: '/api/selection-options/', method: 'get', params })

export function exportListData(params: object) {
  return request({
    url: '/api/reports/export-list/',
    method: 'post',
    data: params,
  })
}
