/**
 * 规则中心类型定义
 *
 * 与后端 process/models/rules.py 字段对齐。
 * 4 个模型：
 * - RuleLibrary    规则库（卡片视图）
 * - RuleKeyword    关键词（Section 2 表格）
 * - RuleMethod     规则方法（详情页 Tab 1）
 * - ExpertRule     专家规则（详情页 Tab 2）
 */

// ============================================================================
// 通用
// ============================================================================

export type OwnerType = 'system' | 'tenant'

/**
 * RuleLibrary 库类型（决定库内允许的规则种类）
 * - expert: 专家规则库（仅允许 ExpertRule：工艺参数初始化系数）
 * - fuzzy: 模糊规则库（仅允许 RuleMethod：缺陷→参数调整规则）
 */
export type LibraryType = 'expert' | 'fuzzy'

export type KeywordType =
  | 'pressure'
  | 'speed'
  | 'time'
  | 'temperature'
  | 'position'
  | 'force'
  | 'length'
  | 'weight'

/**
 * RuleKeyword 业务分类（决定在 if-then 规则中的角色）
 * - parameter: 参数（IF/THEN 都行）
 * - defect: 缺陷（IF 条件）
 * - defect_position: 缺陷位置（IF 条件）
 */
export type Category = 'parameter' | 'defect' | 'defect_position'

/**
 * RuleKeyword 属性值（表达该关键词在工艺上下文中的属性维度）
 * - setpoint: 设定值（面板输入目标）
 * - actual: 实际值（设备通讯采集或手填实测）
 * - enum: 其它（不需要区分属性，用于缺陷/缺陷位置等）
 */
export type ParameterKind = 'setpoint' | 'actual' | 'enum'

/** 模糊级别（与后端 FUZZY_LEVELS 一致）*/
export type FuzzyLevel = 3 | 5 | 7 | 9

export type RuleSource = 'expert' | 'rule_miner' | 'llm'

/** 分页响应（与后端 PaginationResponse 一致） */
export interface PageResult<T> {
  total: number
  items: T[]
}

// ============================================================================
// RuleLibrary（规则库）
// ============================================================================

export interface RuleLibrary {
  id: number
  library_code: string
  library_no?: string | null
  library_name: string
  description?: string | null
  owner_type: OwnerType
  /** 库类型（决定库内允许的规则种类） */
  library_type: LibraryType
  priority: number
  is_active: boolean
  version: number
  /** 库下规则方法数量（仅详情 API 包含） */
  method_count?: number
  /** 库下专家规则数量（仅详情 API 包含） */
  expert_rule_count?: number
  created_at?: string
  updated_at?: string
  [key: string]: any
}

/** 新建规则库的请求体 */
export interface RuleLibraryCreatePayload {
  library_code: string
  library_name: string
  description?: string
  owner_type: OwnerType
  /** 库类型（必填）：专家规则库 / 模糊规则库 */
  library_type: LibraryType
  priority?: number
  is_active?: boolean
  version?: number
}

// ============================================================================
// RuleKeyword（关键词）
// ============================================================================

export interface RuleKeyword {
  id: number
  keyword_name: string
  keyword_alias: string
  range_min: number
  range_max: number
  action_range_min?: number | null
  action_range_max?: number | null
  action_max_val?: number | null
  fuzzy_level: FuzzyLevel
  step?: number | null
  keyword_type: KeywordType
  unit: string
  description?: string | null
  category: Category
  parameter_kind: ParameterKind
  created_at?: string
  updated_at?: string
  [key: string]: any
}

export interface RuleKeywordCreatePayload {
  keyword_name: string
  keyword_alias: string
  range_min: number
  range_max: number
  action_range_min?: number
  action_range_max?: number
  action_max_val?: number
  fuzzy_level?: FuzzyLevel
  step?: number
  keyword_type: KeywordType
  unit: string
  description?: string
  category: Category
  parameter_kind: ParameterKind
}

// ============================================================================
// RuleMethod（规则方法）
// ============================================================================

export interface RuleMethod {
  id: number
  rule_library_id: number
  rule_no?: string | null
  rule_description: string
  rule_explanation?: string | null
  polymer_abbreviation?: string | null
  product_category?: string | null
  defect_label?: string | null
  defect_code?: string | null
  priority: number
  confidence: number
  is_active: boolean
  source: RuleSource
  created_at?: string
  updated_at?: string
  [key: string]: any
}

export interface RuleMethodCreatePayload {
  rule_library_id: number
  rule_description: string
  rule_explanation?: string
  polymer_abbreviation?: string
  product_category?: string
  defect_label?: string
  defect_code?: string
  priority?: number
  confidence?: number
  is_active?: boolean
  source?: RuleSource
}

// ============================================================================
// ExpertRule（专家规则）
// ============================================================================

export interface ExpertRule {
  id: number
  rule_library_id: number
  rule_code: string
  rule_name: string
  /** 匹配条件（AND），空数组 = 默认规则 */
  conditions: Array<{
    field: string
    operator: string
    value: any
  }>
  /** 覆盖系数字典 */
  coefficients: Record<string, any>
  priority: number
  is_active: boolean
  created_at?: string
  updated_at?: string
  [key: string]: any
}

export interface ExpertRuleCreatePayload {
  rule_library_id: number
  rule_code: string
  rule_name: string
  conditions: ExpertRule['conditions']
  coefficients: ExpertRule['coefficients']
  priority?: number
  is_active?: boolean
}
