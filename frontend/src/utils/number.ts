/**
 * 格式化数字字符串，适用于输入过滤和最终显示
 * @param input 输入值（任意类型）
 * @param fixed 小数位数，默认 2
 * @param allowNegative 是否允许负数，默认 false
 * @param strict 严格模式（用于 blur/提交）：补零、移除孤立小数点
 */
export function formatNumber(
  input: any,
  fixed: number = 2,
  allowNegative: boolean = false,
  strict: boolean = false
): string|null {
  const defaultBlankRet = null // null, "" 
  if (input == null || input === "") return defaultBlankRet

  let str = String(input).trim()

  // 处理负号
  let hasMinus = false
  if (str.startsWith("-")) {
    if (!allowNegative) {
      str = str.slice(1)
    } else {
      hasMinus = true
      str = str.slice(1)
      if (str === "") return strict ? "0" : "-"
    }
  }

  if (str === "") return strict ? "0" : defaultBlankRet

  // 特殊情况：纯小数点
  if (str === ".") str = "0."
  if (str === "-.") str = "-0."

  // 只保留数字和第一个小数点
  let clean = ""
  let dotSeen = false
  for (const char of str) {
    if (char === "." && !dotSeen) {
      clean += "."
      dotSeen = true
    } else if (/\d/.test(char)) {
      clean += char
    }
  }

  if (clean === "") return strict ? "0" : defaultBlankRet

  // 处理前导零（但保留 0.xxx）
  if (clean.startsWith("0") && clean.length > 1 && clean[1] !== ".") {
    clean = clean.replace(/^0+/, "")
    if (clean === "" || clean.startsWith(".")) clean = "0" + clean
  }

  // 限制小数位数（无论是否 strict）
  if (dotSeen && fixed >= 0) {
    const [intPart, decPart = ""] = clean.split(".")
    const truncatedDec = decPart.slice(0, fixed)

    if (strict) {
      const paddedDec = truncatedDec.padEnd(fixed, "0")
      clean = intPart + "." + paddedDec
    } else {
      // 非 strict：保留用户输入状态（如 "12."）
      if (truncatedDec === "" && str.endsWith(".")) {
        clean = intPart + "."
      } else {
        clean = intPart + (truncatedDec ? "." + truncatedDec : "")
      }
    }
  }

  // strict 模式下清理非法结尾
  if (strict) {
    if (clean === "." || clean === "-.") clean = "0"
    if (clean === "-") clean = "0"
    if (clean.endsWith(".")) clean = clean.slice(0, -1)
    if (!clean.includes(".") && fixed > 0) {
      clean += "." + "0".repeat(fixed)
    }
  }

  // 拼回负号
  if (hasMinus && clean !== "0") {
    clean = "-" + clean
  }

  return clean
}