/** 工艺优化模块类型定义：RoundForm=单轮调机数据（工艺参数+反馈），DefectFeedbackData=本轮缺陷反馈，CycleObservation=本轮实测观察（重量/压力/时间等），Suggestion=上一轮调整建议（多模态内容） */


import type { settingProcessForm } from '@/constants/process-const'

// RoundForm（单轮调机数据）


/** 轮次类型 */
export type RoundType = 'initial' | 'optimized' | 'manual'

/**
 * 单轮调机数据
 * - parameter：当前轮次的工艺参数（嵌套，详见 constants/process-const.ts 的 settingProcessForm）；
 *   提交调优前需经 parameterTransform.ts 的 parameterToFlat 翻译为 flat dict
 * - feedback：当前轮次的反馈（缺陷 / 模温机 / 热流道...）
 * - type：该轮是如何产生的（初始 / 优化算法 / 手动调整）
 */
export interface RoundForm {
  id: number
  type: RoundType
  created_at: string
  parameter: typeof settingProcessForm
  feedback: {
    /**
     * 缺陷反馈列表（数组）
     * - 后端算法会根据优先级处理多个缺陷
     * - "DEFECTFREE"（无缺陷）已下线为可选类型：产品合格与否改由 tuning_result 的
     *   qualified/unqualified 表达；历史数据里的 DEFECTFREE 仍可正常回显
     * - 空数组 [] 表示本轮未记录缺陷（可与"合格"评价共存）
     */
    defect?: DefectFeedbackData[]
    /** 调机效果评价（对该轮工艺参数的整体评价）*/
    tuning_result?: TuningResult
    /** 实测观察（制品实际重量 + 7 项注塑机周期实测）*/
    observations?: CycleObservation[]
    // 未来扩展：mold_temp（模温机反馈）、hot_runner（热流道反馈）
    [key: string]: any
  }
  [key: string]: any
}

// CycleObservation（本轮实测观察）


/**
 * 调机效果评价（对【该轮工艺参数】的整体评价，即该轮参数自身的试模标签）
 *
 * 首轮无对比基准：qualified（合格）/ unqualified（不合格）
 * 第 2 轮起：qualified（合格）/ effective（改善）/ unchanged（无变化）/ ineffective（变差）
 *
 * 落库：写入该轮自己的 TuningRecord.result
 * ineffective 还会把该轮 Recommendation.is_adopted 置 False（训练标签）
 */
export type TuningResult =
  | 'effective'
  | 'unchanged'
  | 'ineffective'
  | 'qualified'
  | 'unqualified'
  | null

/**
 * 实测观察项
 *
 * 数据约束：
 * - param_key：必填（与 constants/observation-order.ts 的 OBSERVATION_ITEMS 对齐）
 * - value：单值字段，机器采集或人工填写都存在这里（用户视角就是一个数）
 * - label：不在记录里存储，由 param_key 查 OBSERVATION_ITEMS 得到
 * - 单位：运行时按 param_key 解析（机器单位 > STANDARD_UNITS 兜底）
 *
 * 与工艺设定值的区别：设定侧是分段参数（注射一段/二段压力），实测侧是单值（峰值压力=整周期最高点），二者无 set vs actual 映射，是独立的数据类
 */
export interface CycleObservation {
  param_key:
    | 'actual_product_weight' // 制品实际重量（实测，对比 GatingSystemForm.total_product_weight 设计值）
    | 'peak_pressure'         // 峰值压力
    | 'injection_time'        // 实际注射时间
    | 'cycle_time'            // 周期时间

    // 暂未启用（算法覆盖后启用）：holding_time 实际保压时间 / vp_switch_position V/P 切换位置 / cushion 储料量 / plasticizing_time 储料时间
  value: number | null
}

// DefectFeedbackData（本轮缺陷反馈）


/**
 * 缺陷反馈数据
 *
 * 数据约束：
 * - keyword_id / keyword_name：可空（用户未选时为 null；后端匹配走 keyword_name）
 * - level：当 keyword_name='DEFECTFREE' 时存 null；其他情况按 fuzzy_level 选词
 *   （DEFECTFREE 已下线为可选类型，此约束仅用于兼容历史数据）
 * - position：缺陷位置（产品区域描述，如 "DL飞边3"）；DEFECTFREE 时存空字符串
 * - position_3d：可选的 3D 模型点选坐标（用于精细化位置，不取代 position 的段号语义）
 *
 * 整体为 null 表示用户跳过（与“无缺陷”语义不同）；非 null 即有效反馈
 */
export interface DefectFeedbackData {
  keyword_id: number | null
  keyword_name: string | null
  level: string | null
  position: string
  /** 3D 模型点选坐标（可选，与 position 并存而非取代） */
  position_3d?: { x: number; y: number; z: number } | null
}

// Suggestion（上一轮调整建议，多模态内容）


/** 调整方向（用于 UI 提示，无需翻译）*/
export type SuggestionDirection = 'increase' | 'decrease' | 'hold' | 'check'

/** 单条建议项 */
export interface SuggestionItem {
  /** 建议文本：'降低 一段注射压力：70 → 60'（后端已拼好中文文案）*/
  description: string
  /** 调整方向（可选）：UI 用图标提示 */
  direction?: SuggestionDirection
  /** 关联规则 ID（可选）：用于引用追溯 */
  rule_refs?: string[]
  /** 业务字段名（可选）：'inj_pres_1'（用于高亮 / 跳转参数表）*/
  param?: string
  /** 调整前的当前值（可选）*/
  current_value?: number | null
  /** 调整后的推荐值（可选）*/
  recommended_value?: number | null
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
 * 调整建议（锚在该轮工艺参数上的算法建议）
 * - 数据来源：算法响应（infer 返回 suggestion）或历史轮次回显（后端 Recommendation 重建）
 * - 展示位置：本轮详情区的「调整建议」区块（按轮次各持一份，不跨轮共享）
 * - 锚点语义：Recommendation 挂在它所属的 parameter 上，故建议属于该轮、显示在该轮
 * - groups 可包含任意数量的类别，每组 items 可包含任意数量的建议
 * - 字段全为可选，UI 按有则展示、无则隐藏原则渲染
 * - 后端数据缺失时不展示整个组件（不影响核心缺陷录入）
 */
export interface Suggestion {
  /** 建议所属的轮次 ID（锚点语义：建议挂在它所属的那一轮参数上）*/
  source_round_id?: number
  /** 是否被采纳（训练标签；该轮标签=变差时后端自动置 False）*/
  adopted?: boolean | null
  /** 多组建议（按类别） */
  groups: SuggestionGroup[]
}