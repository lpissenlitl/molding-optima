/** 工艺条件相关类型定义（从 ProcessCondition.vue 提取） */
import type { InjectionKey } from 'vue'

// 模型摘要

/** 浇口特征（对应后端 Gate 模型） */
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

/** 型腔摘要（对应后端 Cavity 模型） */
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

/** 浇注系统摘要（对应后端 GatingSystem 模型） */
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

/** 注塑机射台摘要（对应后端 InjectionUnit 模型） */
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

// 完整模型（detail API 返回，含嵌套关联）

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

/** 工艺条件主对象（前后端交互的核心结构） */
export interface Condition {
  id?: number | null
  condition_no?: string | null
  status?: string | null
  origin_type?: string | null
  /** 模具 id —— 【仅提交态】顶层平铺字段，由 buildPayload 从 mold_info.id 推导。 */
  mold_id?: number | null
  shot_index?: number | null
  /** 制品索引(0 索引,多 cavity 时用于切换显示哪个制品) */
  product_index?: number | null
  /** 注塑机 id —— 【仅提交态】顶层平铺字段，由 buildPayload 从 machine_info.id 推导。 */
  injection_machine_id?: number | null
  injection_index?: number | null
  /** 材料 id —— 【仅提交态】顶层平铺字段，由 buildPayload 从 polymer_info.id 推导。 */
  polymer_id?: number | null
  /** 塑料简称 —— 【仅前端校验用】PolymerSection 输入框当前值的镜像（校验目标必须落在 el-form 的 model 上）；由 PolymerSection 的 watch(polymerAbbreviation) 单向写入，buildPayload 不挑此字段，不提交后端。 */
  polymer_abbreviation?: string | null
  process_context?: Record<string, any>
  mold_info?: MoldInfo | null
  machine_info?: MachineInfo | null
  polymer_info?: PolymerInfo | null
  [key: string]: any
}

// Vue Injection Keys（provide/inject 跨组件共享 condition）

/** 工艺条件 InjectionKey */
export const ConditionKey: InjectionKey<Condition> = Symbol('condition')
