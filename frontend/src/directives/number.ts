import { formatNumber } from "@/utils/number"

export default {
  bind(el: any, binding: any, vnode: any) {
    // 获取 input 元素
    const inputEl = el.tagName === "INPUT" ? el : el.querySelector("input")
    if (!inputEl) return

    // 🔧 自动降级 type="number"
    if (inputEl.type === "number") {
      console.warn(
        "[v-number] 检测到 type=\"number\"，已自动切换为 type=\"text\"。\n" +
        "原因：浏览器不支持对 number 类型操作光标位置。\n" +
        "建议：显式使用 type=\"text\" 并添加 inputmode=\"decimal\"。"
      )
      inputEl.type = "text"
      if (!inputEl.hasAttribute("inputmode")) {
        inputEl.inputMode = "decimal"
      }
    }

    const getOptions = () => {
      let fixed = 2
      let allowNegative = false

      const val = binding.value

      // 情况1: 对象配置 { fixed, allowNegative }
      if (val !== null && typeof val === "object") {
        fixed = val.fixed ?? 2
        allowNegative = val.allowNegative ?? false
      }
      // 情况2: 直接传数字（如 v-number="0"）
      else if (typeof val === "number") {
        fixed = val
        // allowNegative 保持默认 false
      }
      // 情况3: 使用修饰符 v-number:3（兼容旧写法）
      else if (typeof binding.arg === "string") {
        const num = parseInt(binding.arg, 10)
        if (!isNaN(num)) fixed = num
      }

      // 确保 fixed 是非负整数
      fixed = Math.max(0, Math.floor(fixed))

      return { fixed, allowNegative }
    }

    const handleInput = (e: any) => {
      const target = e.target
      const originalValue = target.value
      const selStart = target.selectionStart || 0

      const options = getOptions()
      const formatted = formatNumber(originalValue, options.fixed, options.allowNegative, false)
      const formatLength = formatted === null ? 0 : formatted.length
      if (formatted !== originalValue) {
        target.value = formatted

        requestAnimationFrame(() => {
          const newCursor = selStart === originalValue.length
            ? formatLength
            : Math.min(selStart, formatLength)
          target.setSelectionRange(newCursor, newCursor)
        })

        // 触发 Vue 更新
        if (vnode.componentInstance) {
          vnode.componentInstance.$emit("input", formatted)
        } else {
          target.dispatchEvent(new Event("input", { bubbles: true }))
        }
      }
    }

    // 可选：失焦时补零（如不需要，删除 handleBlur 和监听）
    const handleBlur = () => {
      const options = getOptions()
      const current = inputEl.value
      const formatted = formatNumber(current, options.fixed, options.allowNegative, true)
      if (formatted !== current) {
        inputEl.value = formatted
        if (vnode.componentInstance) {
          vnode.componentInstance.$emit("input", formatted)
        } else {
          inputEl.dispatchEvent(new Event("input", { bubbles: true }))
        }
      }
    }

    inputEl.addEventListener("input", handleInput)
    // inputEl.addEventListener("blur", handleBlur)

    el._vNumberHandlers = { handleInput, /* handleBlur */ }
  },

  unbind(el: any) {
    const inputEl = el.tagName === "INPUT" ? el : el.querySelector("input")
    const handlers = el._vNumberHandlers
    if (inputEl && handlers) {
      inputEl.removeEventListener("input", handlers.handleInput)
      // inputEl.removeEventListener("blur", handlers.handleBlur)
    }
  }
}