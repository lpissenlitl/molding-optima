/** 工艺条件状态枚举（前端唯一来源） */

/** 状态中文标签 */
export const CONDITION_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  active: '使用中',
  archived: '已归档',
}

/** 状态标签配色（el-tag 的 type） */
export type ConditionStatusTagType = 'success' | 'info' | 'warning'

export const CONDITION_STATUS_TAG_TYPES: Record<string, ConditionStatusTagType> = {
  draft: 'warning',
  active: 'success',
  archived: 'info',
}

/** 状态筛选项（搜索表单下拉） */
export const CONDITION_STATUS_OPTIONS = [
  { label: '草稿', value: 'draft' },
  { label: '使用中', value: 'active' },
  { label: '已归档', value: 'archived' },
]

/** 取状态中文标签，未知值原样返回（不臆造） */
export function conditionStatusLabel(s?: string | null): string {
  if (!s) return ''
  return CONDITION_STATUS_LABELS[s] ?? s
}

/** 取状态标签配色，未知值按 info 处理 */
export function conditionStatusTagType(s?: string | null): ConditionStatusTagType {
  return CONDITION_STATUS_TAG_TYPES[s ?? ''] ?? 'info'
}
