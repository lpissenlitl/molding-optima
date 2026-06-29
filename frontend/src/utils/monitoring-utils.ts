/**
 * 监控系统业务特定工具函数
 * 
 * 注意：通用工具函数（debounce、throttle、deepClone、formatDate 等）
 * 请使用全局 utils 中的实现
 */

import { DEVICE_STATUS, ALARM_STATUS } from "@/constants/monitoring-const"

/**
 * 格式化时间差（秒转为可读格式）
 * @param seconds 秒数
 * @returns 格式化后的时间字符串，如 "2小时30分"、"5分30秒"、"45秒"
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return "-"
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

/**
 * 计算 OEE 等级
 * @param oee OEE 值（0-100）
 * @returns 等级：high | medium | low | none
 */
export function getOeeLevel(oee: number | null | undefined): "high" | "medium" | "low" | "none" {
  if (typeof oee !== "number" || isNaN(oee)) return "none"
  if (oee >= 90) return "high"
  if (oee >= 70) return "medium"
  return "low"
}

/**
 * 根据数值获取颜色级别
 * @param value 数值
 * @param thresholds 阈值配置
 * @returns 等级：high | medium | low | none
 */
export function getValueLevel(
  value: number | null | undefined,
  thresholds: { high: number; medium: number } = { high: 90, medium: 70 }
): "high" | "medium" | "low" | "none" {
  if (typeof value !== "number" || isNaN(value)) return "none"
  if (value >= thresholds.high) return "high"
  if (value >= thresholds.medium) return "medium"
  return "low"
}

/**
 * 获取设备状态样式类名
 * @param status 设备状态
 * @returns CSS 类名
 */
export function getDeviceStatusClass(status: string): string {
  const statusMap: Record<string, string> = {
    [DEVICE_STATUS.RUNNING]: "status-running",
    [DEVICE_STATUS.STANDBY]: "status-standby",
    [DEVICE_STATUS.ALARM]: "status-alarm",
    [DEVICE_STATUS.OFFLINE]: "status-offline"
  }
  return statusMap[status] || ""
}

/**
 * 获取告警状态类型（用于 Element UI Tag 组件）
 * @param status 告警状态
 * @returns Element UI Tag type：success | warning | danger | info
 */
export function getAlarmStatusType(status: string): "success" | "warning" | "danger" | "info" {
  const typeMap: Record<string, "success" | "warning" | "danger" | "info"> = {
    [ALARM_STATUS.PENDING]: "danger",
    [ALARM_STATUS.RECOVERED]: "warning",
    [ALARM_STATUS.CONFIRMED]: "success"
  }
  return typeMap[status] || "info"
}

/**
 * 检查是否为有效数值
 * @param value 待检查的值
 * @returns 是否为有效数值
 */
export function isValidNumber(value: any): boolean {
  return typeof value === "number" && !isNaN(value) && isFinite(value)
}

/**
 * 对象属性求和
 * @param obj 对象
 * @param properties 需要求和的属性名数组
 * @returns 求和结果
 */
export function sumProperties(obj: Record<string, any>, properties: string[]): number {
  return properties.reduce((sum, prop) => {
    const value = obj[prop]
    return sum + (isValidNumber(value) ? value : 0)
  }, 0)
}

/**
 * 获取百分比
 * @param part 部分值
 * @param total 总值
 * @returns 百分比（0-100的整数）
 */
export function getPercentage(part: number | null | undefined, total: number | null | undefined): number {
  if (!isValidNumber(part) || !isValidNumber(total) || (total as number) === 0) return 0
  return Math.round(((part as number) / (total as number)) * 100)
}
