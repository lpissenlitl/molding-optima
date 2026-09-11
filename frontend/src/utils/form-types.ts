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
 *                 示例：[{ required: true, message: '请输入', trigger: 'blur' }]
 *                 详细形式：覆盖 required 简化形式（如需 pattern / validator）
 *   required    是否必填（简化形式；FormFieldRenderer 渲染时自动给 el-form-item 加红色星号）
 *                 - true: el-form-item 显示必填星号 + 触发空值验证（与 rules: [{required:true,...}] 等效）
 *                 - undefined/false: 非必填
 *                 注意：required 只是视觉提示，真正的规则需配合 rules 属性才能产生错误提示
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
  /**
   * 是否必填（简化形式，2026-09-08 引入）
   * - 由 FormFieldRenderer 渲染时传给 el-form-item 的 required 属性
   * - 视觉上显示红色星号
   * - 真正的验证需要 rules：[{ required: true, message: '...', trigger: '...' }]
   * - 仅 required=true 时 el-form-item 不会自动产生验证错误提示
   */
  required?: boolean
  /**
   * select 是否允许创建新选项（默认 true，2026-09-08 引入）
   * - false: 只能从 options 中选（如注射次数、模具结构等硬编码分类）
   * - true: 允许用户输入自定义值（如规格、备注等场景）
   * - 设计原则：硬编码分类应显式设 false，避免误创建无意义的数据
   */
  allowCreate?: boolean
  rows?: number
  default?: any
  unit?: string
  min?: number
  max?: number
  precision?: number
  /**
   * 自动补全数据源（type=autocomplete 必填）
   * - object（如 { table, column }）：传给后端 `/selection-options` 接口的参数（默认）
   * - function：自定义查询函数（(queryString, cb) => cb(suggestions)）
   * - string：后端查询 endpoint（预留，暂未使用）
   *
   * 推荐使用 object 形式，配合 helper `querySuggestions(item.query)` 自动调用全局 mixin。
   */
  query?: string | object | ((queryString: string, cb: (suggestions: any[]) => void) => void)
  /**
   * 动态单位（2026-09-09 引入）
   * - 用于从模型另一字段读取单位作为后缀显示
   * - 例如 dynamicUnit: 'pressure_unit' 表示后缀显示 injectionUnit[pressure_unit] 的值
   * - 与 unit 互斥：有 unit 时优先用 unit；都没有时不显示后缀
   * - 用例：HMI 可设定范围字段随单位系统字段联动
   */
  dynamicUnit?: string
  /**
   * divider 分组说明文字（2026-09-09 引入）
   * - 仅 divider 类型生效：在 divider 下方渲染 el-alert 提示
   * - 用于向使用者解释该分组的语义（如“为什么有设备参数 vs 面板参数”）
   */
  description?: string
  /**
   * divider 是否需要“强调样式”（2026-09-09 引入）
   * - 仅 divider 类型生效：true 时用浅色背景 + 左边框包裹该分组
   * - 用于突出显示“参数难获取”或“使用频率高”的分组
   * - 视觉上与普通 divider 分组区分，引导用户注意
   */
  notice?: boolean
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