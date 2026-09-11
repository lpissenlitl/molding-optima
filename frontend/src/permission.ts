/**
 * 路由守卫（Vue 3 + Pinia 版本）
 *
 * 设计要点：
 * - 用 userStore.is_logged_in 判断登录态（Pinia 持久化）
 * - 白名单（/login、/404）无需登录
 * - 未登录访问业务页 → 跳 /login?redirect=原路径
 * - 已登录访问 /login → 跳首页
 * - 已登录但 token 已过期（基于 token_expires_at 本地判断） → 跳 /login?redirect=原路径
 * - 路由切换时显示 NProgress 顶部进度条（告诉用户"系统在工作"）
 *
 * 双保险机制：
 * 1. 本地校验（路由守卫）：基于 token_expires_at，无网络成本，覆盖所有路由切换场景
 * 2. 后端兜底（request.ts 拦截器）：遇到 101001 (ERROR_USER_TOKEN_NOT_EXISTS) 才跳登录页
 *    处理"本地时间偏差"或"服务端主动吊销 token"的场景
 *
 * 后续扩展点：
 * - SSO token 自动登录
 * - 路由进入时 fetchInfo 加载用户角色/权限
 * - 动态路由注入（基于角色过滤菜单）
 * - token 自动续期（剩余 < 1h 主动调 refresh）
 */
import router from '@/router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// 不显示右上角的加载 spinner（与 molding-expert 风格一致）
NProgress.configure({ showSpinner: false })

// 无需登录即可访问的路径
const whiteList = ['/login', '/404']

/**
 * 判断 token 是否过期（基于本地时间与 token_expires_at 比较）
 *
 * - token_expires_at 为空：未登录状态或异常状态，不算过期（让未登录分支处理）
 * - 时间戳解析失败：按过期处理（保守策略，避免误用失效 token）
 *
 * 注意：客户端时间不准会影响判断，但后端 101001 拦截器仍兜底。
 */
function isTokenExpired(tokenExpiresAt: string): boolean {
  if (!tokenExpiresAt) return false
  const expiresAt = new Date(tokenExpiresAt).getTime()
  if (Number.isNaN(expiresAt)) return true  // 解析失败 → 保守处理
  return expiresAt <= Date.now()
}

router.beforeEach(async (to, from, next) => {
  // 启动顶部进度条
  NProgress.start()

  const userStore = useUserStore()
  const hasLogin = userStore.is_logged_in

  // ========== 已登录 ==========
  if (hasLogin) {
    // ---- token 过期检查（本地校验，双保险的"主动防线"）----
    // 覆盖场景：
    //  - 路由切到无 API 的纯静态页面（Dashboard / 占位业务模块）
    //  - 浏览器后退/前进
    //  - 刷新页面（Pinia 持久化后守卫重新跑）
    if (isTokenExpired(userStore.token_expires_at)) {
      ElMessage({
        message: '登录已过期，请重新登录',
        type: 'warning',
        duration: 2000,
      })
      userStore.clear()
      next(`/login?redirect=${to.path}`)
      NProgress.done()
      return
    }

    // 已登录访问登录页 → 跳首页
    if (to.path === '/login') {
      next({ path: '/' })
      NProgress.done() // 手动结束（next 跳转不会触发 afterEach）
      return
    }

    // TODO: 后续可在此处加：
    //   - 路由进入时 fetchInfo 加载完整用户信息
    //   - 基于角色 meta.perm 的路由级权限校验
    //   - 动态菜单注入
    next()
    return
  }

  // ========== 未登录 ==========
  if (whiteList.includes(to.path)) {
    // 白名单直接放行
    next()
    return
  }

  // 其他路径 → 跳登录页（带 redirect 参数，登录后跳回）
  next(`/login?redirect=${to.path}`)
  NProgress.done() // 手动结束
})

router.afterEach(() => {
  // 路由切换完成，结束进度条
  NProgress.done()
})
