/**
 * 表单配置类型定义
 *
 * 设计目标：
 * - 把 flat items 配置的类型与算法解耦（算法在 form-layout.ts）
 * - 业务方 import 一处即可定义 card / items 结构
 * - 业务方专注字段顺序 + 列宽，模板自动渲染控件
 *
 * 适用场景：
 * - 基于 Element Plus el-col span 系统的响应式表单布局
 * - 任意业务模块的"卡片分组 + 字段平铺"表单
 *
 * @example
 * ```ts
 * import type { FormItem, FormCard } from '@/utils/form-types'
 * import { groupIntoRows } from '@/utils/form-layout'
 *
 * const cards: FormCard[] = [
 *   {
 *     title: '项目信息',
 *     items: [
 *       { label: '项目编号', prop: 'project_code', type: 'input', disabled: () => isEdit.value },
 *       { label: '项目名称', prop: 'project_name', type: 'input', span: 16,
 *         rules: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] },
 *     ],
 *   },
 * ]
 *
 * const cardRows = computed(() =>
 *   cards.map((card) => ({
 *     title: card.title,
 *     rows: groupIntoRows(card.items, { columns: 4 }),
 *   }))
 * )
 * ```
 */

/**
 * 字段含义：
 *   label       显示文本（divider 类型必填，其他类型必填）
 *   prop        字段名（必填，绑定 form[prop]；divider 不需要）
 *   type        input/select/date/textarea/number/integer/radio/number-select/autocomplete/divider（必填）
  *                 number-select：select + 数字输入场景（如管道直径 8mm、定位圈外径 100mm）
  *                 行为：select with allow-create + filterable + v-number
 *   span        el-col 列宽（默认 6 = 4 列布局中的 1 列；divider 不适用）
 *                 可选值：6（1 列）/12（2 列）/18（3 列）/24（满列）
 *   options     select / radio 选项数组（type=select 或 radio 时必填）
 *                 - select/radio 有 options：使用 options 渲染
 *                 - radio 无 options：默认渲染“是/否” radio-button
 *   placeholder 占位文本（可选；推荐用 helper.getPlaceholder 自动生成）
 *   disabled    禁用（布尔或函数；用于“项目编号在编辑模式禁用”等场景）
 *   rules       Element Plus 验证规则数组（可选；动态汇总到顶层 rules）
 *   rows        textarea 行数（type=textarea 时可选，默认 4）
 *   default     字段默认值（可选；用于 form 初始化）
 *   unit        后缀单位（type=number/integer 可选；显示在输入框右侧 suffix）
 *   min / max   数值范围（type=number/integer 可选）
 *   precision   小数位数（type=number 默认 2，type=integer 默认 0）
 *   query       自动补全数据源（type=autocomplete 必填）
 *                 - string：后端查询 endpoint（如 '/api/molds/tonnage-suggestions'）
 *                 - function：自定义查询函数（(queryString, cb) => cb(suggestions)）
 */
export interface FormItem {
  label?: string
  prop?: string
  type:
    | 'input'
    | 'select'
    | 'date'
    | 'textarea'
    | 'number'
    | 'integer'
    | 'radio'
    | 'number-select'
    | 'autocomplete'
    | 'divider'
  span?: number
  options?: Array<{ value: string | number | boolean; label: string }>
  placeholder?: string
  disabled?: boolean | ((item: FormItem) => boolean)
  rules?: any[]
  rows?: number
  default?: any
  unit?: string
  min?: number
  max?: number
  precision?: number
  query?: string | ((queryString: string, cb: (suggestions: any[]) => void) => void)
}

/**
 * 表单卡片（按业务/视觉分组的字段集合）
 * - title：卡片标题（对应 el-card header）
 * - items：flat 字段数组（顺序即渲染顺序）
 */
export interface FormCard {
  title: string
  items: FormItem[]
}