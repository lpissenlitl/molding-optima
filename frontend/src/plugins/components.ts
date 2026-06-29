/**
 * 全局组件插件
 * 注册所有需要在整个应用中使用的组件
 */
import Vue from "vue"

// Iconify 图标组件
import { Icon } from "@iconify/vue2"

// ECharts 图表组件
import ECharts from "vue-echarts"

/**
 * 安装插件
 */
export default function installComponents(VueConstructor: typeof Vue) {
  // Iconify 图标
  VueConstructor.component("AppIcon", Icon)
  
  // ECharts 图表
  VueConstructor.component("VChart", ECharts)
}
