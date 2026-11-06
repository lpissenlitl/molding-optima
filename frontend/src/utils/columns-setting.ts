/** 表格列偏好持久化工具：保存/恢复列显隐、密度、每页大小等偏好；key 形如 molding-optima:table-pref:<user_id>:<view_name>；基于 Pinia + localStorage，不依赖 Vuex */

import { useUserStore } from '@/stores/user'

/** 获取当前偏好 key（按用户隔离，不同用户各持一份） */

function getPrefKey(viewName: string): string {
  const userStore = useUserStore()
  const userId = userStore.id || 'anonymous'
  return `molding-optima:table-pref:${userId}:${viewName}`
}

/**
 * 加载指定视图的表格偏好
 * 返回：{ density?: 'small' | 'default' | 'large', pageSize?: number, columns?: Array<{ prop, visible, width, minWidth, ... }> }
 */

export function loadTablePreference(viewName: string): {
  density?: 'small' | 'default' | 'large'
  pageSize?: number
  columns?: any[]
} | null {
  if (!viewName) return null
  const key = getPrefKey(viewName)
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    // 兼容旧值 'normal'（element-plus 实际值是 'default'）
    if (parsed && parsed.density === 'normal') {
      parsed.density = 'default'
    }
    return parsed
  } catch {
    // JSON 解析失败或 localStorage 不可用
    return null
  }
}

/** 保存指定视图的表格偏好（增量更新，浅合并）：partial 会与已有偏好浅合并 */

export function saveTablePreference(
  viewName: string,
  partial: {
    density?: 'small' | 'default' | 'large'
    pageSize?: number
    columns?: any[]
  }
): void {
  if (!viewName) return
  const key = getPrefKey(viewName)
  try {
    const existing = loadTablePreference(viewName) || {}
    const merged = { ...existing, ...partial }
    localStorage.setItem(key, JSON.stringify(merged))
  } catch {
    // localStorage 写入失败（如容量满、隐私模式），静默忽略
  }
}

// 兼容旧 API（与 molding-expert 对齐）：老代码可能调用 loadColumnsSetting/saveColumnsSetting

export function loadColumnsSetting(viewName: string): any {
  return loadTablePreference(viewName)
}

export function saveColumnsSetting(viewName: string, config: any): void {
  saveTablePreference(viewName, config)
}