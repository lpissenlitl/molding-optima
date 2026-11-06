/**
 * 实测观察项配置（工艺优化轮次反馈用）
 * - key=参数标识（snake_case，对应 CycleObservation.param_key）、label=中文展示名
 * - unit_type=物理量类型，单位解析优先级：机器传入的 machine_unit → STANDARD_UNITS 兜底
 * - 行顺序：常用在前（重量）、工程类在后，与「调机员关注度」对齐并固定不变
 * - actual_product_weight 是实测值（对比 GatingSystemForm 的 total_product_weight 设计值评估密度/缩水）
 */


/** 标准单位（兜底，机器无对应单位时使用）*/
export const STANDARD_UNITS = {
  weight: 'g',
  pressure: 'MPa',
  time: 's',
  length: 'mm',
} as const

/** 实测观察项（4 项）*/
export const OBSERVATION_ITEMS = [
  { key: 'actual_product_weight', label: '制品实际重量', unit_type: 'weight' },
  { key: 'peak_pressure',         label: '峰值压力',     unit_type: 'pressure' },
  { key: 'injection_time',        label: '实际注射时间', unit_type: 'time' },
  { key: 'cycle_time',            label: '周期时间',     unit_type: 'time' },

  // 暂未启用（未接入监控的设备可手填，但算法尚未覆盖）
  // holding_time 实际保压时间 / vp_switch_position V/P 切换位置 / cushion 储料量 / plasticizing_time 储料时间

] as const

/** 从 param_key 反查默认 label / 单位类型（O(1)）*/
export const OBSERVATION_LOOKUP: Record<string, { label: string; unit_type: string }> =
  Object.fromEntries(OBSERVATION_ITEMS.map(i => [i.key, { label: i.label, unit_type: i.unit_type }]))