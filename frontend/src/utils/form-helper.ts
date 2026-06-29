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