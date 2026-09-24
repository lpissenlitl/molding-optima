/**
 * 工艺条件相关类型定义（从 ProcessCondition.vue 提取）
 *
 * 设计原则：
 * - 所有 interface 使用 export，方便子组件 + composable 引用
 * - 字段语义与后端 schema 对齐（参考 _dev_refs 中的设计文档）
 * - 用 [key: string]: any 兼容后端可能扩展的字段
 */
import type { InjectionKey } from 'vue'

// ============================================================================
// 模型摘要
// ============================================================================

/**
 * 浇口特征（对应后端 Gate 模型）
 * - 与 preconditionForm gate_* 字段对齐
 * - 字段语义: 圆形/矩形 不同字段；通过 gate_shape 区分渲染
 */
export interface GateSummary {
  id?: number
  /** 浇口形状：圆形 / 矩形 / 梯形 / 环形 */
  gate_shape?: string
  /** 浇口类型：针阀式 / 直浇口 / 点浇口 / ... */
  gate_type?: string
  /** 浇口数量 */
  gate_count?: number | null
  /** 浇口位置描述 */
  location_description?: string
  // 矩形类尺寸
  length?: number | null
  width?: number | null
  // 圆形类尺寸
  diameter?: number | null
  // 梯形类尺寸
  top_length?: number | null
  bottom_length?: number | null
  height?: number | null
  // 环形类尺寸
  outer_diameter?: number | null
  inner_diameter?: number | null
  gap?: number | null
}

/**
 * 型腔摘要（对应后端 Cavity 模型）
 * - 每个 cavity 对应"一类制品",product 字段描述制品信息
 * - gates 是反向关联的浇口列表（1:N）
 */
export interface CavitySummary {
  id?: number
  cavity_count_per_shot?: number | null
  // 制品信息
  product_name?: string
  product_code?: string
  // 制品关键工艺参数
  max_flow_length?: number | null
  ave_wall_thickness?: number | null
  min_wall_thickness?: number | null
  max_wall_thickness?: number | null
  projected_area_per_cavity?: number | null
  estimated_weight_per_cavity?: number | null
  // 可计算特征
  flow_ratio?: number | null
  thickness_variation?: number | null
  // 浇口(1:N,通过反向关联获取)
  gates?: Array<GateSummary>
}

/**
 * 浇注系统摘要（对应后端 GatingSystem 模型）
 * - 每个 GatingSystem 对应一次注射(shot_index)
 * - 包含 cavities（1:N）→ 制品 + 浇口
 */
export interface GatingSystemSummary {
  id?: number
  runner_type?: string
  estimated_shot_weight?: number | null
  estimated_runner_weight?: number | null
  runner_weight?: number | null
  runner_length?: number | null
  projected_area?: number | null
  total_product_weight?: number | null
  // 热流道细节（仅热流道/热转冷时使用）
  hot_runner_supplier?: string
  hot_runner_system_type?: string
  hot_runner_manifold_zones?: number | null
  hot_runner_nozzle_count?: number | null
  has_sequencing_control?: boolean | null
  valve_actuation_type?: string
  // 型腔列表
  cavities?: Array<CavitySummary>
}

/**
 * 注塑机射台摘要（对应后端 InjectionUnit 模型）
 * - 每个 InjectionUnit 对应一个射台(injection_index)
 * - 新增 unit_code 字段（对应 preconditionForm machine_serial_no）
 */
export interface InjectionUnitSummary {
  /** 射台编号 */
  unit_code?: string
  pressure_unit?: string
  nozzle_type?: string
  screw_type?: string
  screw_diameter?: number | null
  max_injection_stroke?: number | null
  max_injection_volume?: number | null
  max_injection_weight?: number | null
}

// ============================================================================
// 完整模型（detail API 返回，含嵌套关联）
// ============================================================================

export interface MoldInfo {
  id: number
  mold_no: string
  mold_name?: string
  product_category?: string
  product_subcategory?: string
  cavity_layout?: string
  shot_count?: number
  gating_systems?: Array<GatingSystemSummary>
  [key: string]: any
}

export interface MachineInfo {
  id: number
  model: string
  brand?: string
  device_no?: string
  location?: string
  unit_count?: number
  max_clamping_force?: number | null
  injection_units?: Array<InjectionUnitSummary>
  [key: string]: any
}

export interface PolymerInfo {
  id: number
  abbreviation: string
  grade?: string
  manufacturer?: string
  /** 推荐熔体温度（℃），对齐 preconditionForm recommend_melt_temperature */
  recommend_melt_temperature?: number | null
  [key: string]: any
}

/**
 * 工艺条件主对象（前后端交互的核心结构）
 *
 * 索引说明：
 * - 后端 shot_index / injection_index / product_index 是 0 索引
 * - UI 显示 1 索引（用户友好），由 useConditionDerived 自动转换
 */
export interface Condition {
  id?: number | null
  condition_no?: string | null
  status?: string | null
  origin_type?: string | null
  mold_id?: number | null
  shot_index?: number | null
  /** 制品索引(0 索引,多 cavity 时用于切换显示哪个制品) */
  product_index?: number | null
  injection_machine_id?: number | null
  injection_index?: number | null
  polymer_id?: number | null
  process_context?: Record<string, any>
  mold_info?: MoldInfo | null
  machine_info?: MachineInfo | null
  polymer_info?: PolymerInfo | null
  [key: string]: any
}

// ============================================================================
// Vue Injection Keys（provide/inject 跨组件共享 condition）
// ============================================================================

/**
 * 工艺条件 InjectionKey
 *
 * 用法：
 * ```ts
 * // 父组件（ProcessCondition.vue）
 * import { provide } from 'vue'
 * provide(ConditionKey, condition)
 *
 * // 子组件（MoldSection / MachineSection / PolymerSection）
 * import { inject } from 'vue'
 * const condition = inject(ConditionKey)!
 * ```
 *
 * 设计动机：
 * - 子组件需要直接 mutate condition.xxx（如选择模具后写 mold_id）
 * - 用 InjectionKey 比 props/emit 更简洁：避免 prop drilling 和 emit 转发
 * - 用 InjectionKey 强类型：避免字符串 key 拼错、保证类型推断
 */
export const ConditionKey: InjectionKey<Condition> = Symbol('condition')
