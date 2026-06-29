
const dateFormat = require("dateformat")

export function dateToday() {
  return dateFormat((new Date()), "yyyy-mm-dd")
}

export function datetimeToday() {
  return dateFormat((new Date()), "yyyy-mm-dd HH:MM:ss")
}
export function datetimeTodayStr() {
  return dateFormat((new Date()), "yyyymmddHHMMss")
}
export function dateToDatetime(date: string) {
  return dateFormat(date, "yyyy-mm-dd HH:MM:ss")
}

export function datetimeToDate(datetime: string) {
  return dateFormat(datetime, "yyyy-mm-dd")
}

export function dateAfterDays(dateStr: string, days: number = 0) {
  const targetDate = getDateTime(dateStr)
  targetDate.setDate(targetDate.getDate() + days)
  return dateFormat(targetDate, "yyyy-mm-dd")
}

export function getDateTime(dateStr: string) {
  const st = dateStr 
  const a = st.split(" ") 
  const b = a[0].split("-") 
  const year = Number(b[0])
  const month = Number(b[1])
  const day = Number(b[2])
  let hour = 0
  let minute = 0
  let second = 0
  if (a.length > 1) {
    const c = a[1].split(":") 
    hour = Number(c[0])
    minute = Number(c[1])
    second = Number(c[2])
  }
  const date = new Date(year, month - 1, day, hour, minute, second)
  return date 
}

export function calDateTimeBetHours(befDate: string, aftDate: string) {

  const date1 = getDateTime(befDate) 
  const date2 = getDateTime(aftDate) 

  const s1 = date1.getTime()
  const s2 = date2.getTime()

  const total = (s2 - s1) / 1000
  const hours = total / (60 * 60)

  return hours
}


interface FormatDateTimeOptions {
  precision?: "date" | "hour" | "minute" | "second"
  locale?: string
  use24Hour?: boolean
}
export function formatDateTime(date: string | Date, options: FormatDateTimeOptions = {}) {
  if (!date) return ""

  const {
    precision = "minute",
    locale = "zh-CN",
    use24Hour = true
  } = options

  const d = date instanceof Date ? date : new Date(date)
  if (isNaN(d.getTime())) return "" // invalid date

  // Base format options
  const baseOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: !use24Hour,
  }

  // Build final options dynamically without using delete
  const formatOptions: Intl.DateTimeFormatOptions = {
    year: baseOptions.year,
    month: baseOptions.month,
    day: baseOptions.day,
  }

  if (precision === "hour" || precision === "minute" || precision === "second") {
    formatOptions.hour = baseOptions.hour
  }
  if (precision === "minute" || precision === "second") {
    formatOptions.minute = baseOptions.minute
  }
  if (precision === "second") {
    formatOptions.second = baseOptions.second
  }

  const formatter = new Intl.DateTimeFormat(locale, formatOptions)
  let result = formatter.format(d)

  if (locale === "zh-CN") {
    result = result.replace(/\//g, "-")
  }

  return result
}