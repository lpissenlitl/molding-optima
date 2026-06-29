/**
 * 全局指令插件
 * 注册所有自定义指令
 */
import Vue from "vue"

// 可拖拽对话框
import elDragDialog from "@/directives/el-drag-dialog"

// 数字输入指令
import numberDirective from "@/directives/number"

/**
 * 安装插件
 */
export default function installDirectives(VueConstructor: typeof Vue) {
  VueConstructor.directive("el-drag-dialog", elDragDialog)
  VueConstructor.directive("number", numberDirective)
}
