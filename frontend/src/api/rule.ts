/**
 * 规则中心 API 封装
 *
 * 后端路径前缀：/api/processes/
 * 路由表：
 * - GET/POST    /api/processes/rule-libraries/                          规则库列表/新建
 * - GET/PATCH/DELETE /api/processes/rule-libraries/<id>/                规则库详情/编辑/删除
 * - GET/POST    /api/processes/rule-libraries/<id>/methods/             库下规则方法
 * - GET/POST    /api/processes/rule-libraries/<id>/expert-rules/        库下专家规则
 * - GET/PATCH/DELETE /api/processes/expert-rules/<id>/                  专家规则详情
 *
 * 设计说明：
 * - 后端响应统一为 { status, msg, data: ... }
 * - request 拦截器只做认证和错误处理，不会剥离外层
 * - 调用方拿到的 res 是完整响应，使用 res.data 访问业务数据
 */
import request from '@/utils/request'
import type {
  PageResult,
  RuleLibrary,
  RuleLibraryCreatePayload,
  RuleKeyword,
  RuleKeywordCreatePayload,
  RuleMethod,
  RuleMethodCreatePayload,
  ExpertRule,
  ExpertRuleCreatePayload,
} from '@/types/rule'

// ============================================================================
// RuleLibrary
// ============================================================================

/** 规则库列表（卡片视图） */
export function listRuleLibraries(params?: {
  page_no?: number
  page_size?: number
  library_name?: string
  library_code?: string
  owner_type?: 'system' | 'tenant'
  library_type?: 'expert' | 'fuzzy'
  is_active?: boolean
}): Promise<PageResult<RuleLibrary>> {
  return request({
    url: '/api/processes/rule-libraries/',
    method: 'get',
    params,
  })
}

/** 规则库详情（带 method_count / expert_rule_count 统计） */
export function getRuleLibrary(id: number): Promise<RuleLibrary> {
  return request({
    url: `/api/processes/rule-libraries/${id}/`,
    method: 'get',
  })
}

/** 新建规则库 */
export function createRuleLibrary(payload: RuleLibraryCreatePayload): Promise<RuleLibrary> {
  return request({
    url: '/api/processes/rule-libraries/',
    method: 'post',
    data: payload,
  })
}

/** 更新规则库 */
export function updateRuleLibrary(id: number, payload: Partial<RuleLibraryCreatePayload>): Promise<RuleLibrary> {
  return request({
    url: `/api/processes/rule-libraries/${id}/`,
    method: 'patch',
    data: payload,
  })
}

/** 删除规则库（级联软删除） */
export function deleteRuleLibrary(id: number): Promise<void> {
  return request({
    url: `/api/processes/rule-libraries/${id}/`,
    method: 'delete',
  })
}

// ============================================================================
// RuleKeyword（关键词，租户全局）
// ============================================================================

/** 关键词列表 */
export function listRuleKeywords(params?: {
  page_no?: number
  page_size?: number
  name?: string
  keyword_type?: string
}): Promise<PageResult<RuleKeyword>> {
  return request({
    url: '/api/processes/rules/keywords/',
    method: 'get',
    params,
  })
}

/** 新建关键词 */
export function createRuleKeyword(payload: RuleKeywordCreatePayload): Promise<RuleKeyword> {
  return request({
    url: '/api/processes/rules/keywords/',
    method: 'post',
    data: payload,
  })
}

/** 更新关键词 */
export function updateRuleKeyword(id: number, payload: Partial<RuleKeywordCreatePayload>): Promise<RuleKeyword> {
  return request({
    url: `/api/processes/rules/keywords/${id}/`,
    method: 'put',
    data: payload,
  })
}

/** 删除关键词 */
export function deleteRuleKeyword(id: number): Promise<void> {
  return request({
    url: `/api/processes/rules/keywords/${id}/`,
    method: 'delete',
  })
}

// ============================================================================
// RuleMethod（规则方法，详情页 Tab 1）
// ============================================================================

/** 库下规则方法列表 */
export function listRuleMethods(libraryId: number, params?: {
  page_no?: number
  page_size?: number
  defect_label?: string
  defect_code?: string
  is_active?: boolean
}): Promise<PageResult<RuleMethod>> {
  return request({
    url: `/api/processes/rule-libraries/${libraryId}/methods/`,
    method: 'get',
    params,
  })
}

/** 规则方法详情 */
export function getRuleMethod(id: number): Promise<RuleMethod> {
  return request({
    url: `/api/processes/rule-methods/${id}/`,
    method: 'get',
  })
}

/** 新建规则方法 */
export function createRuleMethod(payload: RuleMethodCreatePayload): Promise<RuleMethod> {
  return request({
    url: `/api/processes/rule-libraries/${payload.rule_library_id}/methods/`,
    method: 'post',
    data: payload,
  })
}

/** 更新规则方法 */
export function updateRuleMethod(
  id: number,
  payload: Partial<RuleMethodCreatePayload>,
): Promise<RuleMethod> {
  return request({
    url: `/api/processes/rule-methods/${id}/`,
    method: 'patch',
    data: payload,
  })
}

/** 删除规则方法 */
export function deleteRuleMethod(id: number): Promise<void> {
  return request({
    url: `/api/processes/rule-methods/${id}/`,
    method: 'delete',
  })
}

// ============================================================================
// ExpertRule（专家规则，详情页 Tab 2）
// ============================================================================

/** 库下专家规则列表 */
export function listExpertRules(libraryId: number, params?: {
  page_no?: number
  page_size?: number
  rule_code?: string
  is_active?: boolean
}): Promise<PageResult<ExpertRule>> {
  return request({
    url: `/api/processes/rule-libraries/${libraryId}/expert-rules/`,
    method: 'get',
    params,
  })
}

/** 新建专家规则 */
export function createExpertRule(payload: ExpertRuleCreatePayload): Promise<ExpertRule> {
  return request({
    url: `/api/processes/rule-libraries/${payload.rule_library_id}/expert-rules/`,
    method: 'post',
    data: payload,
  })
}

/** 更新专家规则（PATCH，部分字段更新）*/
export function updateExpertRule(
  id: number,
  payload: Partial<ExpertRuleCreatePayload>,
): Promise<ExpertRule> {
  return request({
    url: `/api/processes/expert-rules/${id}/`,
    method: 'patch',
    data: payload,
  })
}

/** 删除专家规则 */
export function deleteExpertRule(id: number): Promise<void> {
  return request({
    url: `/api/processes/expert-rules/${id}/`,
    method: 'delete',
  })
}
