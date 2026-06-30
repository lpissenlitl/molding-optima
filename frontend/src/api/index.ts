/**
 * molding-optima 前端 API 入口
 *
 * 按模块拆分，所有请求走 /api/ 前缀
 * 后端路由参考 molding-optima/backend/_moldx/urls.py
 */
import request from '@/utils/request'

// ==================== 身份/用户/角色/公司 ====================

export const companyList = (params?: any) =>
  request({ url: '/api/companies/', method: 'get', params })

export const userList = (params?: any) =>
  request({ url: '/api/users/', method: 'get', params })

export const userCreate = (data: any) =>
  request({ url: '/api/users/', method: 'post', data })

export const userUpdate = (id: number, data: any) =>
  request({ url: `/api/users/${id}/`, method: 'put', data })

export const userDelete = (id: number) =>
  request({ url: `/api/users/${id}/`, method: 'delete' })

export const roleList = (params?: any) =>
  request({ url: '/api/roles/', method: 'get', params })

export const organizationList = (params?: any) =>
  request({ url: '/api/organizations/', method: 'get', params })

// ==================== 主数据：模具/注塑机/材料/填充物 ====================

export const moldList = (params?: any) =>
  request({ url: '/api/molds/', method: 'get', params })

export const moldCreate = (data: any) =>
  request({ url: '/api/molds/', method: 'post', data })

export const moldDetail = (id: number) =>
  request({ url: `/api/molds/${id}/`, method: 'get' })

export const moldUpdate = (id: number, data: any) =>
  request({ url: `/api/molds/${id}/`, method: 'put', data })

export const moldDelete = (id: number) =>
  request({ url: `/api/molds/${id}/`, method: 'delete' })

export const injectionMachineList = (params?: any) =>
  request({ url: '/api/injection-machines/', method: 'get', params })

export const injectionMachineCreate = (data: any) =>
  request({ url: '/api/injection-machines/', method: 'post', data })

export const injectionMachineDetail = (id: number) =>
  request({ url: `/api/injection-machines/${id}/`, method: 'get' })

export const polymerList = (params?: any) =>
  request({ url: '/api/polymers/', method: 'get', params })

export const polymerCreate = (data: any) =>
  request({ url: '/api/polymers/', method: 'post', data })

export const polymerDetail = (id: number) =>
  request({ url: `/api/polymers/${id}/`, method: 'get' })

export const fillerList = (params?: any) =>
  request({ url: '/api/fillers/', method: 'get', params })

export const fillerCreate = (data: any) =>
  request({ url: '/api/fillers/', method: 'post', data })

// ==================== 工艺管理（核心）====================

// ==================== 工艺参数（对齐 molding-expert url 4-16）====================

export const processParameterList = (params?: any) =>
  request({ url: '/api/processes/parameter/', method: 'get', params })

export const processParameterCreate = (data: any) =>
  request({ url: '/api/processes/parameter/frontend/', method: 'post', data })

export const processParameterDetail = (id: number) =>
  request({ url: `/api/processes/parameter/${id}/`, method: 'get' })

export const processParameterUpdate = (id: number, data: any) =>
  request({ url: `/api/processes/parameter/${id}/`, method: 'put', data })

export const processParameterDelete = (id: number) =>
  request({ url: `/api/processes/parameter/${id}/`, method: 'delete' })

export const processParameterBatchDelete = (ids: number[]) =>
  request({ url: '/api/processes/parameter/batch_delete/', method: 'post', data: { ids } })

// ==================== 工艺优化/调优 ====================

export const processTransplant = (data: { source_parameter_id: number; target_machine_spec: any }) =>
  request({ url: '/api/processes/parameter/transplant/', method: 'post', data })

export const processOptimization = (conditionId: number) =>
  request({ url: `/api/processes/optimization/${conditionId}/`, method: 'get' })

export const processOptimizationCreate = (data: { condition_id: number; target_defect?: string }) =>
  request({ url: `/api/processes/optimization/${data.condition_id || 0}/`, method: 'post', data })

export const processExpertSuggestion = (data: { condition_id: number; defect_feedback: any }) =>
  request({ url: '/api/processes/expert/suggestion/', method: 'post', data })

export const processExpertDefectTemplate = () =>
  request({ url: '/api/processes/expert/defect-template/', method: 'get' })

// ==================== 规则管理 ====================

export const ruleKeywordList = (params?: any) =>
  request({ url: '/api/processes/rules/keywords/', method: 'get', params })

export const ruleKeywordCreate = (data: any) =>
  request({ url: '/api/processes/rules/keywords/', method: 'post', data })

export const ruleMethodList = (params?: any) =>
  request({ url: '/api/processes/rules/methods/', method: 'get', params })

export const ruleMethodCreate = (data: any) =>
  request({ url: '/api/processes/rules/methods/', method: 'post', data })

export const ruleByDefect = (defectName: string) =>
  request({ url: '/api/processes/rules/by-defect/', method: 'get', params: { defect_name: defectName } })

// ==================== 搜索建议 ====================

export const getSelectionOptions = (params: any) =>
  request({ url: '/api/selection-options/', method: 'get', params })

// ==================== 报表导出 ====================

export const processExport = (processConditionIds: number[], includeSnapshots = false) =>
  request({
    url: '/api/process/export/',
    method: 'post',
    data: { process_condition_ids: processConditionIds, include_snapshots: includeSnapshots },
  })

export const processReport = (processConditionId: number, format = 'pdf') =>
  request({
    url: '/api/process/report/',
    method: 'post',
    data: { process_condition_id: processConditionId, format },
  })


// ==================== BaseRequest 通用 CRUD 类（参考 molding-expert）====================

class BaseRequest {
  url: string
  constructor(url: string) {
    this.url = url
  }
  add(data: object) {
    return request({
      url: `${this.url}`,
      method: 'post',
      data,
    })
  }
  getDetail(id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'get',
    })
  }
  edit(data: object, id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'put',
      data,
    })
  }
  delete(id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'delete',
    })
  }
  get(params: object) {
    return request({
      url: `${this.url}`,
      method: 'get',
      params,
    })
  }
  multipleDelete(params: object) {
    return request({
      url: `${this.url}actions/batch-delete/`,
      method: 'delete',
      data: params,
    })
  }
  multipleUpdate(params: object) {
    return request({
      url: `${this.url}actions/batch-update/`,
      method: 'put',
      data: params,
    })
  }
  editAction(data: object, id: number, actionName: string, method: 'get' | 'post' | 'put' | 'delete' = 'put') {
    return request({
      url: `${this.url}${id}/actions/${actionName}/`,
      method,
      data,
    })
  }
}


// ==================== 身份/权限（公司/组织/角色/用户）====================

export const companyMethod = new BaseRequest('/api/companies/')

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

export const organizationMethod = new BaseRequest('/api/organizations/')

export const roleMethod = new BaseRequest('/api/roles/')

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

export const userMethod = new BaseRequest('/api/users/')

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


// ==================== 主数据（BaseRequest 风格）====================

export const projectMethod = new BaseRequest('/api/projects/')
export const moldMethod = new BaseRequest('/api/molds/')
export const polymerMethod = new BaseRequest('/api/polymers/')
export const fillerMethod = new BaseRequest('/api/fillers/')
export const machineMethod = new BaseRequest('/api/injection-machines/')
export const auxiliaryMethod = new BaseRequest('/api/auxiliary-equipments/')


// ==================== 工艺管理（BaseRequest 风格）====================

export const processParameterMethod = new BaseRequest('/api/processes/parameter/')


// ==================== 工艺前端 API（molding-optima 老的设计，与 molding-expert 不一致；保留过渡期使用）====================

export function getProcessParameterFrontend(id: number) {
  return request({
    url: `/api/processes/parameter/${id}/frontend/`,
    method: 'get',
  })
}

export function saveProcessParameterFrontend(data: object) {
  return request({
    url: '/api/processes/parameter/save-frontend/',
    method: 'post',
    data,
  })
}

export function updateProcessParameterFrontend(id: number, data: object) {
  return request({
    url: `/api/processes/parameter/${id}/update-frontend/`,
    method: 'put',
    data,
  })
}

export function transplantProcessParameter(data: object) {
  return request({
    url: '/api/processes/parameter/transplant/',
    method: 'post',
    data,
  })
}


// ==================== 通用工具 ====================

export function exportListData(params: object) {
  return request({
    url: '/api/reports/export-list/',
    method: 'post',
    data: params,
  })
}

export function importMethod(params: object) {
  return request({
    url: '/api/report/import/',
    method: 'post',
    headers: { 'Content-Type': 'multipart/form-data' },
    data: params,
  })
}
