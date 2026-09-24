/**
 * 工艺优化模块类型定义
 *
 * 数据形态：
 * - RoundForm：单轮调机数据（工艺参数 + 反馈）
 * - DefectFeedbackData：本轮缺陷反馈
 * - CycleObservation：本轮实测观察（重量/压力/时间等）
 * - Suggestion：上一轮调整建议（多模态内容）
 */

// ============================================================================
// RoundForm（单轮调机数据）
// ============================================================================

/** 轮次类型 */
export type RoundType = 'initial' | 'optimized' | 'manual'

/**
 * 单轮调机数据
 * - parameter：当前轮次的工艺参数（结构化，复用 settingProcessForm）
 * - feedback：当前轮次的反馈（缺陷 / 模温机 / 热流道...）
 * - type：该轮是如何产生的（初始 / 优化算法 / 手动调整）
 */
export interface RoundForm {
  id: number
  type: RoundType
  created_at: string
  parameter: any  // 结构化工艺参数，参见 constants/process-const.ts 的 settingProcessForm
  feedback: {
    /**
     * 缺陷反馈列表（数组）
     * - 后端算法会根据优先级处理多个缺陷
     * - 可包含 "DEFECTFREE"（无缺陷）作为合法项之一
     * - 空数组 [] 表示用户跳过（与"无缺陷"语义不同）
     */
    defect?: DefectFeedbackData[]
    /** 调机效果评价（对算法上一轮建议的整体反馈）*/
    tuning_result?: TuningResult
    /** 实测观察（制品实际重量 + 7 项注塑机周期实测）*/
    observations?: CycleObservation[]
    // mold_temp?: any    // 未来：模温机反馈
    // hot_runner?: any   // 未来：热流道反馈
    [key: string]: any
  }
  [key: string]: any
}

// ============================================================================
// CycleObservation（本轮实测观察）
// ============================================================================

/** 调机效果评价（对算法上一轮建议的整体反馈）*/
export type TuningResult = 'effective' | 'ineffective' | null

/**
 * 实测观察项。
 *
 * 数据约束：
 * - param_key：必填（与 constants/observation-order.ts 的 OBSERVATION_ITEMS 对齐）
 * - value：单值字段，机器采集或人工填写都存在这里（用户视角就是一个数）
 * - label：不在记录里存储，由 param_key 查 OBSERVATION_ITEMS 得到
 * - 单位：运行时按 param_key 解析（机器单位 > STANDARD_UNITS 兜底）
 *
 * 与工艺设定值的区别：
 * - 设定侧是分段参数（注射一段/二段压力），实测侧是单值（峰值压力=整周期最高点）
 * - 二者无 set vs actual 映射，是独立的数据类
 */
export interface CycleObservation {
  param_key:
    | 'actual_product_weight' // 制品实际重量（实测，对比 GatingSystemForm.total_product_weight 设计值）
    | 'peak_pressure'         // 峰值压力
    | 'injection_time'        // 实际注射时间
    | 'cycle_time'            // 周期时间

    // 暂未启用：constants/observation-order.ts 同步以一行注释保留，算法覆盖后启用
    // | 'holding_time'          // 实际保压时间
    // | 'vp_switch_position'    // V/P 切换位置
    // | 'cushion'               // 储料量
    // | 'plasticizing_time'     // 储料时间
  value: number | null
}

// ============================================================================
// DefectFeedbackData（本轮缺陷反馈）
// ============================================================================

/**
 * 缺陷反馈数据
 *
 * 数据约束：
 * - keyword_id / keyword_name：可空（用户未选时为 null；后端匹配走 keyword_name）
 * - level：当 keyword_name='DEFECTFREE' 时存 null；其他情况按 fuzzy_level 选词
 * - position：缺陷位置（产品区域描述，如 "DL飞边3"）；DEFECTFREE 时存空字符串
 * - position_3d：可选的 3D 模型点选坐标（用于精细化位置，不取代 position 的段号语义）
 *
 * 完整结构语义：
 * - 不为 null：用户填写了反馈（即使是"无缺陷"也属有效反馈）
 * - 为 null：用户跳过（与"无缺陷"语义不同——见 design 文档）
 */
export interface DefectFeedbackData {
  keyword_id: number | null
  keyword_name: string | null
  level: string | null
  position: string
  /** 3D 模型点选坐标（可选，与 position 并存而非取代） */
  position_3d?: { x: number; y: number; z: number } | null
}

// ============================================================================
// Suggestion（上一轮调整建议，多模态内容）
// ============================================================================

/** 调整方向（用于 UI 提示，无需翻译）*/
export type SuggestionDirection = 'increase' | 'decrease' | 'hold' | 'check'

/** 单条建议项 */
export interface SuggestionItem {
  /** 建议文本：'降低注射一段压力 5 MPa' */
  description: string
  /** 调整方向（可选）：UI 用图标提示 */
  direction?: SuggestionDirection
  /** 关联规则 ID（可选）：用于引用追溯 */
  rule_refs?: string[]
}

/** 同一类别的多个建议（如"工艺调整"包含多个参数调整）*/
export interface SuggestionGroup {
  /** 类别名：'工艺调整' / '模温调整' / '热流道调整' */
  category: string
  /** 类别图标（mdi iconify 名，可选）*/
  icon?: string
  /** 该类下的多条建议 */
  items: SuggestionItem[]
}

/**
 * 调整建议（来自上一轮调机的产出）
 *
 * 数据来源：上一轮调机的算法响应（infer 返回 suggestion）
 * 展示位置：本轮的 PreviousSuggestion 顶部（"上一轮调整建议"卡片）
 *
 * 灵活度：
 * - groups 可包含任意数量的类别
 * - 每组 items 可包含任意数量的建议
 * - 字段全为可选，UI 按有则展示、无则隐藏原则渲染
 * - 后端数据缺失时不展示整个组件（不影响核心缺陷录入）
 */
export interface Suggestion {
  /** 来源轮次 ID（用于追溯是上一轮还是更早）*/
  source_round_id?: number
  /** 本轮是否采纳（用于 UI 标识 ✓/✗/未确认）*/
  adopted?: boolean | null
  /** 多组建议（按类别） */
  groups: SuggestionGroup[]
}