/**
 * BaseSearchForm 筛选项类型（供业务子表单复用）
 *
 * 字段说明见 BaseSearchForm.vue 的 items prop 注释
 */
export interface SearchItem {
  label: string
  prop: string
  type: 'autocomplete' | 'select' | 'input' | 'date' | 'slot'
  level?: 'basic' | 'advanced'
  placeholder?: string
  options?: Array<{ label: string; value: any }>
  query?: Record<string, any> & {
    filter_ref?: string
    filter_columns?: Record<string, string>
  }
  slot_name?: string
}