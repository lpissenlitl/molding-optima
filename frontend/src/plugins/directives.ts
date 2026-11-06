/** 全局指令插件（Vue 3 + app.directive）：把所有自定义指令注册到 Vue 3 app */
import type { App } from "vue"

// 可拖拽对话框
import elDragDialog from "@/directives/el-drag-dialog"

// 数字输入指令
import numberDirective from "@/directives/number"

/**
 * 安装全局指令
 * 注意：el-drag-dialog 仍是 Vue 2 风格的 `bind` 钩子，用 as any 绕过类型检查，运行时 Vue 3 会自动映射
 */
export default function installDirectives(app: App) {
  app.directive("el-drag-dialog", elDragDialog as any)
  app.directive("number", numberDirective)
}