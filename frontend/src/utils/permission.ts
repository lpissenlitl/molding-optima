import { useUserStore } from '@/stores/user'
/**
 * 检查当前用户是否拥有指定权限
 *
 * 历史版本：本文件早期从 Vuex 的 UserModule 读取权限。
 * 2026-09 迁移到 Pinia（项目已统一状态管理），改用 useUserStore。
 * 函数签名保持兼容（string | string[] → boolean），调用方零修改。
 *
 * @param {string|Array<string>} value 权限标识，可以是字符串 'add_mold' 或数组 ['add_mold', 'edit_mold']
 * @returns {boolean}
 */
export function hasPermission(value: string | Array<string>): boolean {
  // 用户未登录时（store 初始状态），所有权限都未授予
  const userStore = useUserStore()

  // 超级管理员 / 租户管理员拥有所有权限
  if (userStore.is_superuser || userStore.is_tenant_admin) {
    return true
  }

  // 获取当前用户权限列表
  const permissions: string[] = userStore.permissions || []
  if (typeof value === "string") {
    return permissions.includes(value)
  } else if (Array.isArray(value)) {
    return (value as string[]).some(permission => permissions.includes(permission))
  } else {
    return false
  }
}
