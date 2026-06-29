/**
 * molding-optima 前端 API 入口
 *
 * 按模块拆分，所有请求走 /api/ 前缀
 * 后端路由参考 molding-optima/backend/_moldx/urls.py
 */
import request from '@/utils/request'

// ==================== 认证 ====================

export const login = (params: { username: string; password: string; ua: string }) =>
  request({ url: '/api/login/', method: 'post', data: params })

export const logout = () =>
  request({ url: '/api/logout/', method: 'post' })

export const getProfile = () =>
  request({ url: '/api/profile/', method: 'get' })

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

export const processConditionList = (params?: any) =>
  request({ url: '/api/conditions/', method: 'get', params })

export const processConditionCreate = (data: any) =>
  request({ url: '/api/conditions/', method: 'post', data })

export const processConditionDetail = (id: number) =>
  request({ url: `/api/conditions/${id}/`, method: 'get' })

export const processConditionUpdate = (id: number, data: any) =>
  request({ url: `/api/conditions/${id}/`, method: 'put', data })

export const processConditionDelete = (id: number) =>
  request({ url: `/api/conditions/${id}/`, method: 'delete' })

export const processConditionWithParameter = (data: any) =>
  request({ url: '/api/conditions/with-parameter/', method: 'post', data })

export const processParameterList = (params?: any) =>
  request({ url: '/api/parameters/', method: 'get', params })

export const processParameterCreate = (data: any) =>
  request({ url: '/api/parameters/create/', method: 'post', data })

export const processParameterDetail = (id: number) =>
  request({ url: `/api/parameters/${id}/`, method: 'get' })

export const processParameterUpdate = (id: number, data: any) =>
  request({ url: `/api/parameters/${id}/`, method: 'put', data })

export const processParameterDelete = (id: number) =>
  request({ url: `/api/parameters/${id}/`, method: 'delete' })

export const processParameterBatchDelete = (ids: number[]) =>
  request({ url: '/api/parameters/batch-delete/', method: 'post', data: { ids } })

// ==================== 工艺优化/调优 ====================

export const processTransplant = (data: { source_parameter_id: number; target_machine_spec: any }) =>
  request({ url: '/api/transplant/', method: 'post', data })

export const processOptimization = (conditionId: number) =>
  request({ url: `/api/optimization/${conditionId}/`, method: 'get' })

export const processOptimizationCreate = (data: { condition_id: number; target_defect?: string }) =>
  request({ url: '/api/optimization/0/', method: 'post', data })

export const processExpertSuggestion = (data: { condition_id: number; defect_feedback: any }) =>
  request({ url: '/api/expert/suggestion/', method: 'post', data })

export const processExpertDefectTemplate = () =>
  request({ url: '/api/expert/defect-template/', method: 'get' })

// ==================== 规则管理 ====================

export const ruleKeywordList = (params?: any) =>
  request({ url: '/api/rules/keywords/', method: 'get', params })

export const ruleKeywordCreate = (data: any) =>
  request({ url: '/api/rules/keywords/', method: 'post', data })

export const ruleMethodList = (params?: any) =>
  request({ url: '/api/rules/methods/', method: 'get', params })

export const ruleMethodCreate = (data: any) =>
  request({ url: '/api/rules/methods/', method: 'post', data })

export const ruleByDefect = (defectName: string) =>
  request({ url: '/api/rules/by-defect/', method: 'get', params: { defect_name: defectName } })

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
