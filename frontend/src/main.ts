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
import '@/styles/utilities/subsection-block.scss'
import '@/styles/utilities/custom-drawer.scss'
import '@/styles/utilities/loading-placeholder.scss'
import ComponentsPlugin from '@/plugins/components'
import GlobalMethodsPlugin from '@/plugins/global-methods'
import DirectivesPlugin from '@/plugins/directives'

import App from './App.vue'
import router from '@/router'
import '@/permission'

/*
 * 过滤 element-plus 2.x deprecation warning（仅 DEV）。
 * - 项目 element-plus ^2.5.6（实际 2.14.5），3.x 未发布
 * - "is about to be deprecated in version 3.0.0" 是预埋的未来弃用提示，2.x 范围内永远合法
 * - 保留其他 warning（包括业务代码错误、Vue runtime warning）
 *
 * 不过滤 [Violation]：Chrome DevTools 的 violation 由 inspector 自身发出，不走页面 console 通道
 */
if (import.meta.env.DEV) {
  const _origWarn = console.warn
  console.warn = function (...args: unknown[]) {
    const first = args[0]
    const msg = first instanceof Error ? first.message : String(first ?? '')
    if (msg.includes('is about to be deprecated in version')) return
    _origWarn.apply(console, args as never)
  }
}

// mount 之前从 localStorage 同步主题/字号到 <html data-*>，避免 FOUC 闪烁
function applySettingsFromStorage() {
  try {
    const raw = localStorage.getItem('molding-optima:settings')
    if (!raw) return
    const settings = JSON.parse(raw)
    if (settings.theme) document.documentElement.dataset.theme = settings.theme
    if (settings.fontSize) document.documentElement.dataset.fontSize = settings.fontSize
  } catch {
    /* 用默认主题 */
  }
}
applySettingsFromStorage()

const app = createApp(App)

// Pinia + 持久化
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// 主题/字号变化时实时同步到 <html data-*>（initial 已由 applySettingsFromStorage 处理）
import { useSettingsStore } from '@/stores/settings'
const settingsStore = useSettingsStore()
watch(() => settingsStore.theme, (theme) => { document.documentElement.dataset.theme = theme }, { immediate: false })
watch(() => settingsStore.fontSize, (fontSize) => { document.documentElement.dataset.fontSize = fontSize }, { immediate: false })

app.use(ElementPlus, { locale: zhCn })
app.use(router)
app.use(ComponentsPlugin)            // AppIcon
app.use(GlobalMethodsPlugin)         // $hasPermission / $querySuggestions / $dayjs 等
app.use(DirectivesPlugin)            // v-number / v-el-drag-dialog

app.mount('#app')