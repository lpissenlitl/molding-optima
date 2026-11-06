/** 日期工具（统一用 dayjs 实现，函数签名与返回类型保持兼容）；注意 dayjs 的 format token 与 dateformat 不同：yyyy-mm-dd HH:MM:ss ↔ YYYY-MM-DD HH:mm:ss */

import dayjs from 'dayjs'

export function dateToday(): string {
  return dayjs().format('YYYY-MM-DD')
}

export function datetimeToday(): string {
  return dayjs().format('YYYY-MM-DD HH:mm:ss')
}

export function datetimeTodayStr(): string {
  return dayjs().format('YYYYMMDDHHmmss')
}

export function dateToDatetime(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

export function datetimeToDate(datetime: string): string {
  return dayjs(datetime).format('YYYY-MM-DD')
}

export function dateAfterDays(dateStr: string, days: number = 0): string {
  return dayjs(dateStr).add(days, 'day').format('YYYY-MM-DD')
}

/** 把日期/时间字符串解析为 Date 对象（保留是为了兼容旧调用方；新代码建议直接用 dayjs(dateStr).toDate()） */

export function getDateTime(dateStr: string): Date {
  return dayjs(dateStr).toDate()
}

export function calDateTimeBetHours(befDate: string, aftDate: string): number {
  const s1 = dayjs(befDate).valueOf()
  const s2 = dayjs(aftDate).valueOf()
  return (s2 - s1) / 1000 / (60 * 60)
}

interface FormatDateTimeOptions {
  precision?: 'date' | 'hour' | 'minute' | 'second'
  locale?: string
  use24Hour?: boolean
}

/** 通用日期格式化（基于 Intl.DateTimeFormat，不依赖任何第三方包） */

export function formatDateTime(
  date: string | Date,
  options: FormatDateTimeOptions = {}
): string {
  if (!date) return ''

  const {
    precision = 'minute',
    locale = 'zh-CN',
    use24Hour = true
  } = options

  const d = date instanceof Date ? date : new Date(date)
  if (isNaN(d.getTime())) return '' // invalid date

  // Base format options
  const baseOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: !use24Hour
  }

  // Build final options dynamically without using delete
  const formatOptions: Intl.DateTimeFormatOptions = {
    year: baseOptions.year,
    month: baseOptions.month,
    day: baseOptions.day
  }

  if (precision === 'hour' || precision === 'minute' || precision === 'second') {
    formatOptions.hour = baseOptions.hour
  }
  if (precision === 'minute' || precision === 'second') {
    formatOptions.minute = baseOptions.minute
  }
  if (precision === 'second') {
    formatOptions.second = baseOptions.second
  }

  const formatter = new Intl.DateTimeFormat(locale, formatOptions)
  let result = formatter.format(d)

  if (locale === 'zh-CN') {
    result = result.replace(/\//g, '-')
  }

  return result
}
