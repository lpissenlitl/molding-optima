/**
 * 路由守卫
 *
 * 流程：
 * - 未登录访问业务页 → 跳 /login?redirect=原路径
 * - 未登录访问白名单 → 放行
 * - 已登录访问 /login → 跳首页
 * - 已登录 token 过期 → 跳 /login
 *
 * token 过期校验与 request.ts 后端 101001 拦截器形成双保险：
 * 本地拦截覆盖"切到无 API 页面 / 浏览器后退"等无网络往返的场景。
 */
import router from '@/router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { startRouteLoading, stopRouteLoading } from '@/router/route-loading'

NProgress.configure({ showSpinner: false })
const whiteList = ['/login', '/404']

/**
 * token 是否过期（本地粗判，与后端 101001 拦截器配合）
 * - 解析失败 → 算过期（保守策略，避免误用失效 token）
 */
function isTokenExpired(tokenExpiresAt: string): boolean {
  if (!tokenExpiresAt) return false
  const expiresAt = new Date(tokenExpiresAt).getTime()
  if (Number.isNaN(expiresAt)) return true
  return expiresAt <= Date.now()
}

router.beforeEach((to, from, next) => {
  NProgress.start()
  // 同步触发：Vue microtask 后用户立即看到 loading（解决"点击 1-2s 没反应"）
  startRouteLoading()

  const userStore = useUserStore()
  const hasLogin = userStore.is_logged_in

  if (hasLogin) {
    if (isTokenExpired(userStore.token_expires_at)) {
      ElMessage({ message: '登录已过期，请重新登录', type: 'warning', duration: 2000 })
      userStore.clear()
      next(`/login?redirect=${to.path}`)
      return
    }
    if (to.path === '/login') {
      next({ path: '/' })
      return
    }
    next()
    return
  }

  if (whiteList.includes(to.path)) {
    next()
    return
  }
  next(`/login?redirect=${to.path}`)
})

router.afterEach(() => {
  NProgress.done()
  stopRouteLoading()
})