// 全局组件插件（Vue 3 版）
// 集中管理需要在整个应用中使用的组件

import type { App } from 'vue'

// Iconify 图标组件（工业领域图标）
import { Icon } from '@iconify/vue'

/**
 * 安装全局组件
 */
export default {
  install(app: App) {
    // Iconify 图标（模板中可直接使用 <AppIcon icon="mdi:factory" />）
    app.component('AppIcon', Icon)
  },
}