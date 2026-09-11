/**
 * 创建一个用于校验 Element Plus 表单并自动聚焦到第一个错误字段的函数。
 * 适用于 Vue 2 或 Vue 3（需传入组件实例 vm）。
 *
 * @param vm - 当前 Vue 组件实例（用于调用 $nextTick）
 * @returns 返回一个异步校验函数
 */
export function createValidateAndFocus(vm: any) {
  /**
   * 校验指定的 el-form 表单，并在失败时自动聚焦到第一个出错的可交互元素。
   *
   * @param formRef - el-form 的 ref 引用（必须是通过 ref="xxx" 获取的真实 DOM 组件实例）
   * @param options - 配置选项
   * @param options.scrollToError - 是否自动滚动到错误字段，默认 true
   * @param options.scrollOffset - 滚动时向上偏移的像素值（用于避开固定头部等），默认 100
   * @returns Promise<boolean> - 校验是否通过
   */
  return function (
    formRef: any,
    options: { scrollToError?: boolean; scrollOffset?: number } = {}
  ): Promise<boolean> {
    const { scrollToError = true, scrollOffset = 100 } = options

    // 如果表单引用无效或没有 validate 方法，视为校验通过（避免报错）
    if (!formRef || typeof formRef.validate !== "function") {
      return Promise.resolve(true)
    }

    return new Promise((resolve) => {
      // 调用 Element Plus 的表单校验方法
      formRef.validate((valid: boolean) => {
        if (valid) {
          resolve(true)
          return
        }

        // 等待 DOM 更新，确保 .is-error 类已添加到出错的表单项
        vm.$nextTick(() => {
          // 查找第一个带有 .is-error 类的 el-form-item
          const firstErrorItem = formRef.$el.querySelector(".el-form-item.is-error")
          if (!firstErrorItem) {
            // 理论上不会发生，但做兜底处理
            resolve(false)
            return
          }

          // 在该表单项中查找可聚焦的输入元素
          // 支持：普通 input、textarea、el-select、el-autocomplete、日期/时间选择器等
          const focusable = firstErrorItem.querySelector(
            [
              "input:not([type=\"hidden\"]):not(:disabled)", // 普通输入框（排除隐藏和禁用）
              "textarea:not(:disabled)",                     // 多行文本
              ".el-select__input",                          // 下拉选择器的隐藏 input
              ".el-autocomplete__input",                    // 自动完成输入框
              ".el-date-editor input"                       // 日期/时间选择器的触发 input
            ].join(", ")
          ) as HTMLElement | null

          if (focusable) {
            // 聚焦到该元素（会自动唤起键盘或下拉面板）
            focusable.focus()

            // 可选：平滑滚动到该元素位置
            if (scrollToError && typeof focusable.scrollIntoView === "function") {
              focusable.scrollIntoView({ behavior: "smooth", block: "center" })

              // 如果页面有固定头部（如 navbar），向上微调避免遮挡
              if (scrollOffset > 0) {
                window.scrollBy(0, -scrollOffset)
              }
            }
          }

          resolve(false)
        })
      })
    })
  }
}

/**
 * FormItem 辅助函数
 *
 * 与 form-types.ts 配合使用：
 *   - 不抽 BaseFormItem 组件，但共享 helper 函数
 *   - 业务方在模板里写 v-else-if 链，调用 helper 生成 placeholder / disabled / precision
 *
 * 设计哲学：
 *   - 数据抽象（FormItem）抽 ✅
 *   - 渲染抽象（BaseFormItem）不抽 ❌
 *   - 辅助函数（helper）抽 ✅
 */
import type { FormItem } from './form-types'
import { getCurrentInstance } from 'vue'

/**
 * 自动生成 placeholder
 *
 * 规则：
 *   - item.placeholder 存在 → 返回它（优先级最高）
 *   - select / date / autocomplete → "请选择/选择日期/请输入 + label"
 *   - radio → 返回空（radio 不需要 placeholder）
 *   - 其他（input/textarea/number/integer）→ "请输入 + label"
 *
 * @example
 *   getPlaceholder({ type: 'input', label: '项目名称' }) // "请输入项目名称"
 *   getPlaceholder({ type: 'select', label: '流道类别' }) // "请选择流道类别"
 */
export function getPlaceholder(item: FormItem): string {
  if (item.placeholder) return item.placeholder
  const label = item.label || ''
  switch (item.type) {
    case 'select':
    case 'number-select':
      return `请选择${label}`
    case 'date':
      return `选择日期`
    case 'autocomplete':
      return `请输入${label}`
    case 'radio':
      return '' // radio 不需要 placeholder
    case 'divider':
      return '' // divider 不需要 placeholder
    default:
      return `请输入${label}`
  }
}

/**
 * 解析 disabled（支持函数）
 *
 * 业务方可以传布尔或函数：
 *   { disabled: true }                          // 始终禁用
 *   { disabled: () => isEdit.value }             // 编辑模式禁用
 *   { disabled: (item) => item.prop === 'code' } // 动态判断
 *
 * @example
 *   getDisabled({ disabled: true })   // true
 *   getDisabled({ disabled: () => false }) // false
 */
export function getDisabled(item: FormItem): boolean {
  if (typeof item.disabled === 'function') {
    return Boolean((item.disabled as (i: FormItem) => boolean)(item))
  }
  return Boolean(item.disabled)
}

/**
 * 获取数值类型的小数位数
 *
 * 规则：
 *   - integer → 默认 0
 *   - number → 默认 2
 *   - item.precision 存在 → 返回它（优先级最高）
 *
 * 配合 v-number 指令使用：
 *   <el-input v-number="getPrecision(item)" />
 *
 * @example
 *   getPrecision({ type: 'integer' })   // 0
 *   getPrecision({ type: 'number' })    // 2
 *   getPrecision({ type: 'number', precision: 4 })  // 4
 */
export function getPrecision(item: FormItem): number {
  if (typeof item.precision === 'number') return item.precision
  return item.type === 'integer' ? 0 : 2
}

/**
 * 解析 autocomplete 的 fetch-suggestions 函数（辅助函数）
 *
 * 支持 query 两种形式：
 *   - object（如 { table, column }）：调用全局 mixin `$querySuggestions` 拉取后端建议
 *   - function：自定义查询函数（直接返回）
 *
 * 注意：
 *   - 在 <script setup> 中调用，通过 `getCurrentInstance().proxy` 访问 mixin
 *   - mixin 返回的函数会调用后端 `/selection-options` 接口（见 `data-fetcher.ts`）
 *   - 业务方在 FormItem.query 中定义数据源：
 *
 * @example
 *   ```ts
 *   // FormItem 定义
 *   {
 *     label: '塑料厂商',
 *     prop: 'manufacturer',
 *     type: 'autocomplete',
 *     query: { table: 'polymer', column: 'manufacturer' },
 *   }
 *
 *   // 模板里使用
 *   <el-autocomplete
 *     v-model="polymer_info[item.prop!]"
 *     :fetch-suggestions="querySuggestions(item.query)"
 *   />
 *   ```
 *
 * @param query - FormItem.query：object | function
 * @param options - 可选的 select options（用于后端返回 value 映射为 label）
 * @returns 返回符合 `el-autocomplete` `:fetch-suggestions` 签名的函数 (input, cb) => cb(suggestions)
 */
export function querySuggestions(
  query:
    | string
    | object
    | ((input: string, cb: (suggestions: any[]) => void) => void)
    | null
    | undefined,
  options?: any[]
) {
  // function 形式：直接返回（业务方自定义查询逻辑）
  if (typeof query === 'function') {
    return query
  }

  // string 形式（预留，当前未使用）：不返回后端建议，返回空函数
  if (typeof query === 'string') {
    return (_input: string, _cb: (suggestions: any[]) => void) => {
      _cb([])
    }
  }

  // object 形式（如 { table, column }）：从全局 mixin 调用后端接口
  if (typeof query === 'object' && query !== null) {
    // 在 <script setup> 中，getCurrentInstance() 返回的 instance 仅用于访问 mixin，
    // 不保留引用（Vue 文档明确推荐用法）。
    const instance = getCurrentInstance()
    const mixinFn = (instance?.proxy as any)?.$querySuggestions
    if (typeof mixinFn === 'function') {
      return mixinFn(query, options ?? null)
    }
  }

  // 兜底：返回空函数（避免 el-autocomplete 报错）
  return (_input: string, _cb: (suggestions: any[]) => void) => {
    _cb([])
  }
}