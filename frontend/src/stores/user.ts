/**
 * User Store — 当前登录用户
 *
 * - 字段全用 snake_case（对齐后端，零转换）
 * - 持久化整个 store（含 token），刷新页面不丢登录态
 * - getters 用 snake_case，actions 用 camelCase
 *
 * 后端对齐：backend/identity/services/user_service.py:213-227
 */
import { defineStore } from 'pinia'
import {
  login as loginApi,
  logout as logoutApi,
  getInfo as getInfoApi,
  SSOLogin as SSOLoginApi,
  resetMyPassword as resetMyPasswordApi,
} from '@/api/login'

export interface LoginPayload {
  username: string
  password: string
  ua: string
}

export interface SSOLoginPayload {
  token: string
}

export interface UpdatePasswordPayload {
  old_password: string
  new_password: string
}

export interface ResetPasswordPayload {
  password: string
}

export interface UserInfo {
  id: number
  username: string
  engineer_name: string
  email: string
  phone: string
  is_active: boolean
  is_staff: boolean
  is_tenant_admin: boolean
  is_superuser: boolean
  company_id: number
  company_name: string
  organization_id: number
  organization_name: string
  extra_accessible_orgs: number[]
  roles: number[]
  permissions: string[]
  token: string
  /** token 过期时间（ISO 8601），路由守卫做本地过期判断 */
  token_expires_at: string
  login_count: number
  last_login_at: string
  expires_at: string
}

export const EMPTY_USER_INFO: UserInfo = {
  id: 0,
  username: '',
  engineer_name: '',
  email: '',
  phone: '',
  is_active: false,
  is_staff: false,
  is_tenant_admin: false,
  is_superuser: false,
  company_id: 0,
  company_name: '',
  organization_id: 0,
  organization_name: '',
  extra_accessible_orgs: [],
  roles: [],
  permissions: [],
  token: '',
  token_expires_at: '',
  login_count: 0,
  last_login_at: '',
  expires_at: '',
}

export const useUserStore = defineStore('user', {
  state: (): UserInfo => ({ ...EMPTY_USER_INFO }),

  getters: {
    is_logged_in: (state) => !!state.token,
    /** 显示名：engineer_name → username → 未登录 */
    display_name: (state) => state.engineer_name || state.username || '未登录',
    /** 是否管理员（超管或租户管理员）*/
    is_admin: (state) => state.is_superuser || state.is_tenant_admin,
    /** 是否有指定权限码（管理员默认拥有所有权限）*/
    has_permission: (state) => (perm: string) => {
      if (state.is_superuser || state.is_tenant_admin) return true
      return state.permissions?.includes(perm) || false
    },
    has_role: (state) => (role_id: number) => state.roles?.includes(role_id) || false,
  },

  actions: {
    /** 用户名密码登录；成功后 token 写入 store，持久化由 Pinia plugin 自动完成 */
    async login(payload: LoginPayload): Promise<void> {
      const res = await loginApi({
        username: payload.username,
        password: payload.password,
        ua: payload.ua || navigator.userAgent,
      })
      this.applyUser(res.data)
    },

    /** SSO 登录 */
    async ssoLogin(payload: SSOLoginPayload): Promise<void> {
      const res = await SSOLoginApi(payload.token)
      this.applyUser(res.data)
    },

    /** 拉取当前用户完整信息（基于现有 token 刷新） */
    async fetchInfo(): Promise<void> {
      const res = await getInfoApi()
      // 保留现有 token，仅刷新其他字段
      this.applyUser({ ...res.data, token: this.token })
    },

    /** 用户自己改密码 */
    async updatePassword(payload: UpdatePasswordPayload): Promise<void> {
      await resetMyPasswordApi(payload)
    },

    /**
     * 用户登出
     * - 通知后端吊销 token（best-effort，失败也不阻塞清空）
     */
    async logout(): Promise<void> {
      try {
        await logoutApi()
      } catch {
        /* 忽略登出失败（token 可能已过期） */
      }
      this.clear()
    },

    /** 注入用户信息（被 login/ssoLogin/fetchInfo 调用） */
    applyUser(info: Partial<UserInfo>): void {
      Object.assign(this, info)
    },

    clear(): void {
      Object.assign(this, EMPTY_USER_INFO)
    },
  },

  persist: {
    key: 'molding-optima:user',
  },
})