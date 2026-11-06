/** 规则挖掘审核流 API 封装：后端前缀 /api/processes/mining-rules/，四组端点（列表 / 详情 / 通过 / 驳回）全部要求管理员（后端 require_admin）；后端响应统一 {status,msg,data}，拦截器不剥离外层，调用方用 res.data 取业务数据 */

import request from '@/utils/request'
import type {
  PageResult,
} from '@/types/rule'
import type {
  MiningConsequent,
  MiningRule,
  MiningRuleStatus,
} from '@/types/mining'

// MiningRule（候选规则）

/** 候选规则列表（审核台） */
export function listMiningRules(params?: {
  page_no?: number
  page_size?: number
  /** 按审核态过滤 */
  status?: MiningRuleStatus
  /** 按后件过滤 */
  consequent?: MiningConsequent
  /** 规则编号模糊搜索 */
  keyword?: string
}): Promise<PageResult<MiningRule>> {
  return request({
    url: '/api/processes/mining-rules/',
    method: 'get',
    params,
  })
}

/** 候选规则详情（含挖掘指标、证据样本、落地预览） */
export function getMiningRule(id: number): Promise<MiningRule> {
  return request({
    url: `/api/processes/mining-rules/${id}/`,
    method: 'get',
  })
}

/** 通过候选规则 ⇒ 落地为生效规则（RuleMethod, source='rule_miner'） */
export function approveMiningRule(
  id: number,
  payload?: { note?: string },
): Promise<MiningRule> {
  return request({
    url: `/api/processes/mining-rules/${id}/approve/`,
    method: 'post',
    data: payload ?? {},
  })
}

/** 驳回候选规则（note 必填） */
export function rejectMiningRule(
  id: number,
  payload: { note: string },
): Promise<MiningRule> {
  return request({
    url: `/api/processes/mining-rules/${id}/reject/`,
    method: 'post',
    data: payload,
  })
}
