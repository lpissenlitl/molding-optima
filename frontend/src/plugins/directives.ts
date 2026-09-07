/**
 * 全局指令插件（Vue 3 + app.directive）
 *
 * 用途：把所有自定义指令注册到 Vue 3 app。
 *
 * 历史版本：本文件早期是 Vue 2 风格（VueConstructor.directive + import Vue from "vue"）。
 * 在 Vue 3 中无效：
 *   - `vue` 包没有 default export → `import Vue from "vue"` 得到 undefined
 *   - 全局指令 API 从 `Vue.directive()` 改到 `app.directive()`
 * 现改为 Vue 3 风格，可正常注册。
 */
import type { App } from "vue"

// 可拖拽对话框
import elDragDialog from "@/directives/el-drag-dialog"

// 数字输入指令
import numberDirective from "@/directives/number"

/**
 * 安装全局指令
 *
 * 注意：el-drag-dialog 仍是 Vue 2 风格的 `bind` 钩子，
 * 本次不重写（独立任务），用 as any 绕过类型检查，运行时 Vue 3 会自动映射。
 */
export default function installDirectives(app: App) {
  app.directive("el-drag-dialog", elDragDialog as any)
  app.directive("number", numberDirective)
}