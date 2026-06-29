import { UserModule } from "@/store/modules/user"
/**
 * 检查当前用户是否拥有指定权限
 * @param {string|Array<string>} value 权限标识，可以是字符串 'add_mold' 或数组 ['add_mold', 'edit_mold']
 * @returns {boolean}
 */

export function hasPermission(value: string | Array<string>): boolean { 
  // 超级管理员拥有所有权限
  if (UserModule.is_superuser) {
    return true
  }

  // 租户管理员拥有除公司管理权限外所有权限
  if (UserModule.is_tenant_admin) {
    return true
  }

  // 获取当前用户权限列表
  const permissions: string[] = UserModule.permissions
  if (typeof value === "string") {
    return permissions.includes(value)
  } else if (Array.isArray(value)) {
    return value.some(permission => permissions.includes(permission))
  } else {
    return false
  }
}