/** 规则挖掘（候选规则审核流）类型定义：与后端 process/models/mining.py + process/services/mining_review.py 对齐 */

/**
 * 候选规则审核状态
 * - pending:   待审核
 * - approved:  已通过（已落地为生效规则）
 * - rejected:  已驳回
 */
export type MiningRuleStatus = 'pending' | 'approved' | 'rejected'

/**
 * 后件标签（试模结果）
 * - qualified:   合格
 * - unqualified: 不合格
 * - improved:    有改善
 * - worse:       变差
 */
export type MiningConsequent = 'qualified' | 'unqualified' | 'improved' | 'worse'

/**
 * 前件缺陷项（缺陷名 + 严重等级合成一项）
 * ⚠️ 缺陷名取**算法命名空间**英文名（SHORTSHOT / FLASH），不是业务字段名
 */
export interface MiningDefect {
  name: string
  level: string
}

/** 参数变更（前件） */
export interface MiningChange {
  /** 业务字段名（如 inj_pres_1）*/
  param: string
  direction: 'increase' | 'decrease'
  /** 变更前的值（用于算参数档位）*/
  before?: number | null
  /** 变更后的值（用于算调整幅度）*/
  after?: number | null
}

/** 落地预览中的一条生效规则（RuleMethod 内容）*/
export interface MiningLandingRule {
  rule_description: string
  rule_explanation?: string
  defect_label?: string | null
  defect_code?: string | null
  confidence: number
  priority: number
  is_active: boolean
}

/** 落地预览中被跳过的一项及原因 */
export interface MiningLandingSkip {
  reason: string
  detail?: string
}

/** 落地预览（不写库，仅展示「这条规则会变成什么」）*/
export interface MiningLandingPreview {
  /** 是否可以落地（存在至少一条可写入的规则）*/
  landable: boolean
  rules: MiningLandingRule[]
  skipped: MiningLandingSkip[]
}

/** 候选规则 */
export interface MiningRule {
  id: number
  rule_code: string
  rule_hash: string
  defects: MiningDefect[]
  /** 缺陷的可读文本（后端聚合，如 "SHORTSHOT(medium)"）*/
  defect_text: string
  changes: MiningChange[]
  consequent: MiningConsequent
  support: number
  confidence: number
  lift: number
  sample_count: number
  corpus_cursor?: string
  status: MiningRuleStatus
  reviewed_by?: string
  reviewed_at?: string | null
  review_note?: string
  landed_rule_method_id?: number | null
  landed_at?: string | null
  landed_description?: string
  landing_note?: string
  /** 证据样本 id（仅详情接口返回）*/
  evidence?: string[]
  /** 落地预览（仅详情接口返回）*/
  landing_preview?: MiningLandingPreview
  created_at?: string
  updated_at?: string
}
