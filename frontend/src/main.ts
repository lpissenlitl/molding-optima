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

// 抑制 element-plus deprecation warning（仅 DEV）。
// 项目 element-plus ^2.5.6（实际 2.14.5），3.x 未发布，warning 里"3.0.0"是预埋的未来弃用提示。
// 2.x 范围内永远合法，仅过滤"is about to be deprecated in version"提示，保留其他 warning。
// 升级 element-plus 3.x 时移除本块（届时 type="text" 等会真的非法）。
if (import.meta.env.DEV) {
  const _origWarn = console.warn
  console.warn = function (...args: unknown[]) {
    const first = args[0]
    const msg = first instanceof Error ? first.message : String(first ?? '')
    if (msg.includes('is about to be deprecated in version')) return
    _origWarn.apply(console, args as never)
  }
}

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