import { formatNumber } from "@/utils/number"

export default {
  mounted(el: any, binding: any, vnode: any) {
    // 拿到 el 内部所有 input 元素（兼容 el-select / el-input 等包装组件）
    // el-select 内部可能有多个 input（如隐藏的 multiple 勾选框）—— 跳过 type="hidden" / type="checkbox" / type="radio"
    const getInputEls = (): HTMLInputElement[] => {
      const inputs: HTMLInputElement[] = []
      if (el.tagName === "INPUT") {
        if (el.type !== "hidden" && el.type !== "checkbox" && el.type !== "radio") {
          inputs.push(el)
        }
      } else {
        const found = el.querySelectorAll("input")
        for (const input of Array.from(found) as HTMLInputElement[]) {
          if (input.type !== "hidden" && input.type !== "checkbox" && input.type !== "radio") {
            inputs.push(input)
          }
        }
      }
      return inputs
    }

    const setup = (inputEl: HTMLInputElement) => {
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

      // 🐛 修复递归：formatted === null 表示“空/全无效字符”状态
      // - 此状态下若进入 if 块，target.value = null 会被浏览器转成 “null” 字符串
      // - 下面的 dispatchEvent 会再触发一轮 handleInput
      // - 新一轮 originalValue = "null"、formatted 仍为 null，二者仍不相等 -> 无限递归
      // - 直接 return，交由 Vue v-model 处理清空状态
      if (formatted === null) {
        // ⚠️ el-select 场景下，浏览器显示的字符需要手动清空（v-model 已先于本函数写入）
        // 用 patching 标志位防止 setSelectionRange/dispatchEvent 触发再次进入 handleInput
        if (!target._vNumberPatching && originalValue !== '') {
          target._vNumberPatching = true
          target.value = ''
          target.dispatchEvent(new Event('input', { bubbles: true }))
          // 下一帧解除标志（必须在派发的 input 事件处理完之后）
          requestAnimationFrame(() => { target._vNumberPatching = false })
        }
        return
      }

      const formatLength = formatted.length
      if (formatted !== originalValue) {
        target.value = formatted

        requestAnimationFrame(() => {
          const newCursor = selStart === originalValue.length
            ? formatLength
            : Math.min(selStart, formatLength)
          target.setSelectionRange(newCursor, newCursor)
        })

        // 触发 Vue 更新
        if (vnode.component) {
          vnode.component.$emit("input", formatted)
        } else {
          target.dispatchEvent(new Event("input", { bubbles: true }))
        }
      }
    }

    // 可选：失焦时补零（如不需要，删除 handleBlur 和监听）
    const handleBlur = (e: any) => {
      const inputEl = e.target
      const options = getOptions()
      const current = inputEl.value
      const formatted = formatNumber(current, options.fixed, options.allowNegative, true)
      if (formatted !== current) {
        inputEl.value = formatted
        if (vnode.component) {
          vnode.component.$emit("input", formatted)
        } else {
          inputEl.dispatchEvent(new Event("input", { bubbles: true }))
        }
      }
    }

    const handlers: Array<{ el: HTMLInputElement; handleInput: any }> = []
    for (const inputEl of getInputEls()) {
      setup(inputEl)
      const handleInputForEl = (e: Event) => handleInput(e as any)
      inputEl.addEventListener("input", handleInputForEl)
      // inputEl.addEventListener("blur", handleBlur)
      handlers.push({ el: inputEl, handleInput: handleInputForEl })
    }

    el._vNumberHandlers = handlers
  },

  unmounted(el: any) {
    const handlers = el._vNumberHandlers as Array<{ el: HTMLInputElement; handleInput: any }> | undefined
    if (handlers) {
      for (const { el: inputEl, handleInput } of handlers) {
        inputEl.removeEventListener("input", handleInput)
        // inputEl.removeEventListener("blur", handleBlur)
      }
    }
  }
}