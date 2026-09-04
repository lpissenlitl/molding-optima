/**
 * User Store — 当前登录用户
 *
 * 设计原则：
 * - 字段全用 snake_case（对齐后端，零转换）
 * - 持久化整个 store（含 token），刷新页面不丢登录态
 * - 暴露核心动作：login / logout / fetchInfo / ssoLogin
 * - getters 用 snake_case，actions 用 camelCase
 *
 * 字段命名参考：frontend/CODING_STANDARDS.md v1.0
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

// ============================================================================
// 类型定义（snake_case，对齐后端）
// ============================================================================

/** 登录入参（对齐后端 LoginSchema）*/
export interface LoginPayload {
  username: string
  password: string
  ua: string                       // User-Agent
}

/** SSO 登录入参 */
export interface SSOLoginPayload {
  token: string
}

/** 修改密码入参（用户自己改）*/
export interface UpdatePasswordPayload {
  old_password: string
  new_password: string
}

/** 重置密码入参（管理员重置其他用户）*/
export interface ResetPasswordPayload {
  password: string
}

/** 完整用户信息（与后端 login 返回字段对齐）*/
export interface UserInfo {
  // 身份
  id: number
  username: string
  engineer_name: string            // 工程师姓名（业务字段）

  // 联系信息
  email: string
  phone: string

  // 状态标志（对齐后端 User 模型）
  is_active: boolean
  is_staff: boolean
  is_tenant_admin: boolean
  is_superuser: boolean

  // 组织关系
  company_id: number
  company_name: string
  organization_id: number
  organization_name: string
  extra_accessible_orgs: number[]

  // 权限
  roles: number[]                  // 角色 ID 列表
  permissions: string[]            // 权限码列表

  // 会话
  token: string

  // 审计字段
  login_count: number
  last_login_at: string
  expires_at: string
}

/** 空用户（初始 state、登出后状态）*/
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
  login_count: 0,
  last_login_at: '',
  expires_at: '',
}

// ============================================================================
// Store
// ============================================================================

export const useUserStore = defineStore('user', {
  state: (): UserInfo => ({ ...EMPTY_USER_INFO }),

  getters: {
    /** 是否已登录（核心判断）*/
    is_logged_in: (state) => !!state.token,

    /** 显示名：engineer_name → username → 未登录 */
    display_name: (state) =>
      state.engineer_name || state.username || '未登录',

    /** 是否管理员（超管或租户管理员）*/
    is_admin: (state) => state.is_superuser || state.is_tenant_admin,

    /** 是否有指定权限码（管理员默认拥有所有权限）*/
    has_permission: (state) => (perm: string) => {
      if (state.is_superuser || state.is_tenant_admin) return true
      return state.permissions?.includes(perm) || false
    },

    /** 是否有指定角色 ID */
    has_role: (state) => (role_id: number) => {
      return state.roles?.includes(role_id) || false
    },
  },

  actions: {
    /**
     * 用户名密码登录
     * @param payload 登录入参
     * 成功后 token 写入 store；持久化由 Pinia plugin 自动完成
     */
    async login(payload: LoginPayload): Promise<void> {
      const res = await loginApi({
        username: payload.username,
        password: payload.password,
        ua: payload.ua || navigator.userAgent,
      })
      
      // 后端返回 { status, msg, data: UserInfo & { token } }
      this.applyUser(res.data)
    },

    /**
     * SSO 登录（预留接口）
     * @param payload SSO token
     */
    async ssoLogin(payload: SSOLoginPayload): Promise<void> {
      const res = await SSOLoginApi(payload.token)
      this.applyUser(res.data)
    },

    /**
     * 拉取当前用户完整信息（基于现有 token 刷新）
     */
    async fetchInfo(): Promise<void> {
      const res = await getInfoApi()
      // 保留现有 token，仅刷新其他字段
      const token = this.token
      this.applyUser({ ...res.data, token })
    },

    /**
     * 用户自己改密码（需要登录态）
     */
    async updatePassword(payload: UpdatePasswordPayload): Promise<void> {
      await resetMyPasswordApi(payload)
    },

    /**
     * 用户登出
     * - 通知后端吊销 token（best-effort，失败也不阻塞清空）
     * - 清空 store
     */
    async logout(): Promise<void> {
      try {
        await logoutApi()
      } catch {
        // 忽略登出失败（token 可能已过期）
      }
      this.clear()
    },

    /**
     * 注入用户信息（内部使用，被 login/ssoLogin/fetchInfo 调用）
     * @param info 用户信息（含 token）
     */
    applyUser(info: Partial<UserInfo>): void {
      Object.assign(this, info)
    },

    /**
     * 清空 store（登出后调用）
     */
    clear(): void {
      Object.assign(this, EMPTY_USER_INFO)
    },
  },

  // 持久化整个 user 信息（含 token）
  persist: {
    key: 'molding-optima:user',
  },
})
