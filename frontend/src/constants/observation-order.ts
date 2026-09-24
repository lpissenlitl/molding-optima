/**
 * 实测观察项配置（工艺优化轮次反馈用）
 *
 * 字段语义：
 * - key：参数标识（snake_case，与 CycleObservation.param_key 对应）
 * - label：UI 展示名（中文）
 * - unit_type：物理量类型（用于从 machine_info 查机器特定单位；
 *                              缺时回退 STANDARD_UNITS）
 *
 * 单位解析优先级（resolveUnit 单位）：
 *   1. 机器传入的 machine_unit[item.unit_type]（机器界面用的单位）
 *   2. STANDARD_UNITS[item.unit_type]（标准单位兜底）
 *
 * 行顺序：常用在前（重量），工程类在后。顺序与"调机员关注度"对齐，
 * 固定不变便于肌肉记忆。
 *
 * 与设计字段的区别：
 * - actual_product_weight：实测（操作员称重），对比 GatingSystemForm 的
 *   total_product_weight（设计值）评估密度/缩水
 * - 其他实测项独立于工艺设定参数（无 set vs actual 映射）
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

  // 暂未启用：未接入监控的设备可手填，但算法尚未覆盖
  // { key: 'holding_time',          label: '实际保压时间', unit_type: 'time' },
  // { key: 'vp_switch_position',    label: 'V/P 切换位置', unit_type: 'length' },
  // { key: 'cushion',               label: '储料量',       unit_type: 'length' },
  // { key: 'plasticizing_time',     label: '储料时间',     unit_type: 'time' },
] as const

/** 从 param_key 反查默认 label / 单位类型（O(1)）*/
export const OBSERVATION_LOOKUP: Record<string, { label: string; unit_type: string }> =
  Object.fromEntries(OBSERVATION_ITEMS.map(i => [i.key, { label: i.label, unit_type: i.unit_type }]))