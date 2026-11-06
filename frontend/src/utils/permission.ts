import { useUserStore } from '@/stores/user'
/**
 * 检查当前用户是否拥有指定权限
 * @param value 权限标识，可以是字符串 'add_mold' 或数组 ['add_mold', 'edit_mold']
 * @returns boolean
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
