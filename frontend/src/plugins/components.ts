// 全局组件插件（Vue 3 版）
// 集中管理需要在整个应用中使用的组件

import type { App } from 'vue'

// Iconify 图标 - 离线按需注入 mdi 子集（避免 CDN 请求 + 避免全量打包）。
// 子集文件由 scripts/extract-mdi-used-icons.js 生成。
import { Icon, addCollection } from '@iconify/vue'
import { mdiUsedIcons } from '@/assets/icons/mdi-used'

addCollection(mdiUsedIcons as any)

/**
 * 安装全局组件
 */
export default {
  install(app: App) {
    // Iconify 图标（模板中可直接使用 <AppIcon icon="mdi:factory" />）
    app.component('AppIcon', Icon)
  },
}
