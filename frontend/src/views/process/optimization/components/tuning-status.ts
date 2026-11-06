/** 调机轮次的展示文案与标签色（列表页与历史抽屉共用，避免两处各写一份而漂移） */

/** 参数来源 → 文案（与后端 ProcessParameter.PARAMETER_SOURCE_CHOICES 对齐） */
export const PARAM_SOURCE_LABEL: Record<string, string> = {
  unknown: '未标记',
  manual: '手工录入',
  import: '外部导入',
  algorithm_init: '算法初始化',
  system_inferred: '系统推理',
  manual_adjusted: '人工调整',
  equipment_sync: '设备同步',
  template_copy: '模板复制',
  ai_recommended: 'AI 推荐',
}

/** 效果评价 → 文案（未评价不走此表） */
export const RESULT_LABEL: Record<string, string> = {
  effective: '改善',
  unchanged: '无变化',
  ineffective: '变差',
  qualified: '合格',
  unqualified: '不合格',
}

/** 效果评价 → 标签色 */
export const RESULT_TAG_TYPE: Record<string, 'success' | 'warning' | 'danger'> = {
  effective: 'success',
  unchanged: 'warning',
  ineffective: 'danger',
  qualified: 'success',
  unqualified: 'danger',
}

/** 参数来源文案（空值 → 未标记） */
export function sourceLabel(s?: string | null): string {
  if (!s) return '未标记'
  return PARAM_SOURCE_LABEL[s] ?? s
}

/** 效果评价文案（空值 → 未评价） */
export function resultLabel(v?: string | null): string {
  return v ? (RESULT_LABEL[v] ?? v) : '未评价'
}

/** 效果评价标签色（空值 → info） */
export function resultTagType(v?: string | null): 'success' | 'warning' | 'danger' | 'info' {
  return v ? (RESULT_TAG_TYPE[v] ?? 'info') : 'info'
}

/** 归档状态文案：已归档 = 该轮参数不可改写（历史事实） */
export function sealedLabel(sealed?: boolean | null): string {
  return sealed ? '已归档' : '待评价'
}
