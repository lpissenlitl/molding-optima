import { defineStore } from 'pinia'

/**
 * Settings Store — 用户级系统设置
 *
 * 与 app store 区分：app 是系统级（品牌/版本），settings 是用户级（个人偏好）
 * 持久化 localStorage，下次登录自动恢复
 * 主题/字号在 main.ts 启动时立即应用，避免 FOUC 闪烁
 */

export type Theme = 'light' | 'dark' | 'high-contrast'
export type FontSize = 'default' | 'large'

export interface SettingsState {
  theme: Theme
  fontSize: FontSize
  sidebarDefaultCollapsed: boolean
}

export const THEME_OPTIONS: { value: Theme; label: string; hint: string }[] = [
  { value: 'light', label: '浅色', hint: '办公室、弱光环境' },
  { value: 'dark', label: '暗色', hint: '夜班、长时间作业' },
  { value: 'high-contrast', label: '高对比', hint: '车间强光、远距离可读' },
]

export const FONT_SIZE_OPTIONS: { value: FontSize; label: string; hint: string }[] = [
  { value: 'default', label: '标准', hint: '14px 基准字号' },
  { value: 'large', label: '大', hint: '16px 基准字号（车间远距离）' },
]

export const useSettingsStore = defineStore('settings', {
  state: (): SettingsState => ({
    theme: 'light',
    fontSize: 'default',
    sidebarDefaultCollapsed: false,
  }),

  actions: {
    setTheme(theme: Theme) {
      this.theme = theme
    },
    setFontSize(fontSize: FontSize) {
      this.fontSize = fontSize
    },
    setSidebarDefaultCollapsed(value: boolean) {
      this.sidebarDefaultCollapsed = value
    },
    reset() {
      this.theme = 'light'
      this.fontSize = 'default'
      this.sidebarDefaultCollapsed = false
    },
  },

  persist: {
    key: 'molding-optima:settings',
  },
})