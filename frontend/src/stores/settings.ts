import { defineStore } from 'pinia'

/**
 * Settings Store — 用户级系统设置
 *
 * 设计原则：
 * - 与 app store 区分：app 是系统级（品牌/版本），settings 是用户级（个人偏好）
 * - 用户偏好持久化（localStorage），下次登录自动恢复
 * - 主题/字号在 main.ts 启动时立即应用，避免 FOUC 闪烁
 *
 * P0 范围（当前）：
 * - theme：light / dark / high-contrast（适配车间/办公室/夜班）
 * - fontSize：default / large（戴手套远距离可读）
 * - sidebarDefaultCollapsed：boolean（最大化主区域）
 *
 * P1 后续（暂不实现）：
 * - 单位制（℃/℉、MPa/bar/psi）
 * - 语言（zh-CN/en-US）
 * - 列表页大小 / 小数精度
 * - 报警声音
 */

export type Theme = 'light' | 'dark' | 'high-contrast'
export type FontSize = 'default' | 'large'

export interface SettingsState {
  /** 主题：light / dark / high-contrast */
  theme: Theme
  /** 字号：default / large */
  fontSize: FontSize
  /** 侧边栏默认是否折叠（仅桌面端生效）*/
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
    /** 重置所有设置为默认值 */
    reset() {
      this.theme = 'light'
      this.fontSize = 'default'
      this.sidebarDefaultCollapsed = false
    },
  },

  // 持久化整个设置（用户级偏好，下次登录保留）
  persist: {
    key: 'molding-optima:settings',
  },
})