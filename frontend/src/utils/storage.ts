import settings from "@/settings"

// -- 辅助：生成带版本的 key -----------------------------------
/**
 * 生成带软件版本号的 localStorage key
 * 例如: createStorageKey('molds') => 'app_molds_v5.0.0'
 */
export function createStorageKey(baseKey: string): string {
  return `app_${baseKey}_${settings.version}`
}

// -- 核心：安全读写 -----------------------------------------
/**
 * 安全地将任意 JSON-可序列化的数据保存到 localStorage
 * 自动处理 stringify，支持 number / boolean / object / array 等
 */
export function setLocalStorage<T = any>(key: string, data: T): void {
  if (data === undefined) {
    console.warn(`[Storage] Skipping save of undefined for key: "${key}"`)
    return
  }
  try {
    localStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    console.warn(`[Storage] Failed to save key "${key}" to localStorage:`, error)
  }
}

/**
 * 从 localStorage 读取并解析数据，返回指定类型
 * 若 key 不存在或解析失败，返回 null（不会抛错）
 */
export function getLocalStorage<T = any>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch (error) {
    console.warn(`[Storage] Failed to parse key "${key}" from localStorage:`, error)
    return null
  }
}

/**
 * 从 localStorage 删除指定 key
 */
export function removeLocalStorage(key: string): void {
  localStorage.removeItem(key)
}

/**
 * 清空所有以指定前缀开头的 localStorage 项
 */
export function clearLocalStorageByPrefix(prefix: string): void {
  Object.keys(localStorage)
    .filter(key => key.startsWith(prefix))
    .forEach(key => localStorage.removeItem(key))
}

/**
 * 清空所有包含 "xxx" 的 localStorage 项
 */
export function clearLocalStorageByIncludes(includes: string): void {
  Object.keys(localStorage)
    .filter(key => key.includes(includes))
    .forEach(key => localStorage.removeItem(key))
}

/**
 * 清空所有 localStorage 项
 */
export function clearLocalStorage(): void {
  localStorage.clear()
}