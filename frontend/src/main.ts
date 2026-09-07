import { createApp, watch } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import '@/styles/tokens.scss'
import '@/styles/themes.scss'
import '@/styles/element-plus.scss'
import '@/styles/reset.scss'
import '@/styles/utilities/custom-tag.scss'
import '@/styles/utilities/custom-form.scss'
import ComponentsPlugin from '@/plugins/components'
import GlobalMethodsPlugin from '@/plugins/global-methods'
import DirectivesPlugin from '@/plugins/directives'

import App from './App.vue'
import router from '@/router'
import '@/permission' // 路由守卫（登录态、未授权跳转）

// =============================================================================
// 同步应用主题与字号（在 mount 之前，避免 FOUC 闪烁）
// 直接读 localStorage 是因为此时 Pinia 还没初始化，store 不能用
// =============================================================================
function applySettingsFromStorage() {
  try {
    const raw = localStorage.getItem('molding-optima:settings')
    if (!raw) return
    const settings = JSON.parse(raw)
    if (settings.theme) {
      document.documentElement.dataset.theme = settings.theme
    }
    if (settings.fontSize) {
      document.documentElement.dataset.fontSize = settings.fontSize
    }
  } catch {
    // localStorage 读取失败，忽略（用默认主题）
  }
}
applySettingsFromStorage()

const app = createApp(App)

// =============================================================================
// 状态管理：Pinia + 持久化
// =============================================================================
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// =============================================================================
// 主题与字号：监听 store 变化，实时同步到 <html data-*> 属性
// =============================================================================
import { useSettingsStore } from '@/stores/settings'

// Pinia 已激活后再订阅（避免 race condition）
const settingsStore = useSettingsStore()

// 主题切换：同步到 <html data-theme>
watch(
  () => settingsStore.theme,
  (theme) => {
    document.documentElement.dataset.theme = theme
  },
  { immediate: false } // initial 已由 applySettingsFromStorage 处理
)

// 字号切换：同步到 <html data-font-size>
watch(
  () => settingsStore.fontSize,
  (fontSize) => {
    document.documentElement.dataset.fontSize = fontSize
  },
  { immediate: false }
)

// UI 框架：Element Plus（中文 locale）
app.use(ElementPlus, { locale: zhCn })

// 路由
app.use(router)

// 全局组件插件（AppIcon）
app.use(ComponentsPlugin)

// 全局方法插件（$hasPermission / $querySuggestions / $dayjs 等）
// mold 视图依赖这些全局方法，必须在挂载前注册
app.use(GlobalMethodsPlugin)

// 全局指令插件（v-number / v-el-drag-dialog）
// 必须在挂载前注册，模板里的 v-number 才能生效
app.use(DirectivesPlugin)

app.mount('#app')