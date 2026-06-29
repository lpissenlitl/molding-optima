/**
 * Element UI 主题色动态更新工具
 * 
 * 由于 SCSS 变量在编译时确定，无法直接读取 CSS 变量
 * 这个工具可以在运行时动态更新 Element UI 的主题色
 * 
 * @author MoldingX Team
 * @version 1.0.0
 * @since 2026-06-10
 */

/**
 * 更新 Element UI 主题色
 * 
 * @param primaryColor - 主主题色
 * @param successColor - 成功色
 * @param warningColor - 警告色
 * @param dangerColor - 危险色
 * @param infoColor - 信息色
 */
export function updateElementTheme(
  primaryColor: string,
  successColor?: string,
  warningColor?: string,
  dangerColor?: string,
  infoColor?: string
): void {
  const root = document.documentElement
  
  // 更新 CSS 变量
  root.style.setProperty("--el-color-primary", primaryColor)
  if (successColor) root.style.setProperty("--el-color-success", successColor)
  if (warningColor) root.style.setProperty("--el-color-warning", warningColor)
  if (dangerColor) root.style.setProperty("--el-color-danger", dangerColor)
  if (infoColor) root.style.setProperty("--el-color-info", infoColor)
  
  // 生成浅色变体（用于 hover、active 等状态）
  const primaryLight = lightenColor(primaryColor, 10)
  const primaryDark = darkenColor(primaryColor, 10)
  
  root.style.setProperty("--el-color-primary-light-3", primaryLight)
  root.style.setProperty("--el-color-primary-dark-2", primaryDark)
}

/**
 * 从 tokens.scss 读取主题色并应用
 */
export function applyThemeFromTokens(): void {
  const root = document.documentElement
  const styles = getComputedStyle(root)
  
  const primaryColor = styles.getPropertyValue("--theme-primary").trim()
  const successColor = styles.getPropertyValue("--color-success").trim()
  const warningColor = styles.getPropertyValue("--color-warning").trim()
  const dangerColor = styles.getPropertyValue("--color-danger").trim()
  const infoColor = styles.getPropertyValue("--color-info").trim()
  
  updateElementTheme(primaryColor, successColor, warningColor, dangerColor, infoColor)
}

/**
 * 颜色变亮
 * 
 * @param color - 十六进制颜色
 * @param percent - 变亮百分比（0-100）
 * @returns 变亮后的颜色
 */
function lightenColor(color: string, percent: number): string {
  const num = parseInt(color.replace("#", ""), 16)
  const amt = Math.round(2.55 * percent)
  const R = (num >> 16) + amt
  const G = (num >> 8 & 0x00FF) + amt
  const B = (num & 0x0000FF) + amt
  
  return "#" + (
    0x1000000 +
    (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
    (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
    (B < 255 ? (B < 1 ? 0 : B) : 255)
  ).toString(16).slice(1)
}

/**
 * 颜色变暗
 * 
 * @param color - 十六进制颜色
 * @param percent - 变暗百分比（0-100）
 * @returns 变暗后的颜色
 */
function darkenColor(color: string, percent: number): string {
  const num = parseInt(color.replace("#", ""), 16)
  const amt = Math.round(2.55 * percent)
  const R = (num >> 16) - amt
  const G = (num >> 8 & 0x00FF) - amt
  const B = (num & 0x0000FF) - amt
  
  return "#" + (
    0x1000000 +
    (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
    (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
    (B < 255 ? (B < 1 ? 0 : B) : 255)
  ).toString(16).slice(1)
}
