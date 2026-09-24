/**
 * sessionStorage 工具集（与 storage.ts 的 localStorage 工具成对）
 *
 * 与 localStorage 的差别：
 * - 生命周期绑定到「浏览器 tab session」：关闭 tab 后自动清空
 * - 同一 tab 内多页签切换仍共享，新开 tab / 窗口则独立
 * - 适合「长时间操作的中途切页面不丢数据，但关闭浏览器后不需要保留」的场景
 *
 * 用法：与 localStorage 工具完全一致，仅函数名以 Session 区分
 * 版本号由 vite.config.ts 的 __APP_VERSION__ 注入（来源：package.json）
 */

// -- 辅助：生成带版本的 key -----------------------------------
/**
 * 生成带软件版本号的 sessionStorage key
 * 版本号让软件升级时旧 key 自然失效（schema 变了也不会用错数据）
 */
export function createSessionStorageKey(baseKey: string): string {
  return `app_${baseKey}_${__APP_VERSION__}`
}

// -- 核心：安全读写 -----------------------------------------
/**
 * 安全地将任意 JSON-可序列化的数据保存到 sessionStorage
 * - 自动 stringify，支持 number / boolean / object / array 等
 * - 写入失败（容量满、隐私模式、SSR 无 sessionStorage）静默 warn
 */
export function setSessionStorage<T = any>(key: string, data: T): void {
  if (data === undefined) {
    console.warn(`[SessionStorage] Skipping save of undefined for key: "${key}"`)
    return
  }
  try {
    sessionStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    console.warn(`[SessionStorage] Failed to save key "${key}":`, error)
  }
}

/**
 * 从 sessionStorage 读取并解析数据
 * - 返回指定类型；不存在 / 解析失败 / 非 JSON 时返回 null（不抛错）
 */
export function getSessionStorage<T = any>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch (error) {
    console.warn(`[SessionStorage] Failed to parse key "${key}":`, error)
    return null
  }
}

/**
 * 从 sessionStorage 删除指定 key
 */
export function removeSessionStorage(key: string): void {
  try {
    sessionStorage.removeItem(key)
  } catch (error) {
    console.warn(`[SessionStorage] Failed to remove key "${key}":`, error)
  }
}

/**
 * 清空所有以指定前缀开头的 sessionStorage 项
 */
export function clearSessionStorageByPrefix(prefix: string): void {
  try {
    Object.keys(sessionStorage)
      .filter(key => key.startsWith(prefix))
      .forEach(key => sessionStorage.removeItem(key))
  } catch (error) {
    console.warn(`[SessionStorage] Failed to clear by prefix "${prefix}":`, error)
  }
}

/**
 * 清空当前会话（当前 tab）的全部 sessionStorage
 */
export function clearSessionStorage(): void {
  try {
    sessionStorage.clear()
  } catch (error) {
    console.warn(`[SessionStorage] Failed to clear sessionStorage:`, error)
  }
}
