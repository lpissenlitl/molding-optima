/**
 * 路由守卫（Vue 3 + Pinia）
 *
 * 流程：
 * - 未登录访问业务页 → 跳 /login?redirect=原路径
 * - 未登录访问白名单 → 放行
 * - 已登录访问 /login → 跳首页
 * - 已登录 token 过期 → 跳 /login
 * - 其余已登录路径 → 放行
 *
 * token 过期校验与 request.ts 后端 101001 拦截器形成双保险：
 * 本地拦截覆盖"切到无 API 页面 / 浏览器后退"等无网络往返的场景。
 */
import router from '@/router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// 不显示右上角的加载 spinner
NProgress.configure({ showSpinner: false })

// 无需登录即可访问的路径
const whiteList = ['/login', '/404']

/**
 * 判断 token 是否过期（本地粗判）
 *
 * - token_expires_at 为空 → 不算过期（让未登录分支处理）
 * - 时间戳解析失败 → 算过期（保守策略，避免误用失效 token）
 */
function isTokenExpired(tokenExpiresAt: string): boolean {
  if (!tokenExpiresAt) return false
  const expiresAt = new Date(tokenExpiresAt).getTime()
  if (Number.isNaN(expiresAt)) return true  // 解析失败 → 保守处理
  return expiresAt <= Date.now()
}

router.beforeEach((to, from, next) => {
  // 启动顶部进度条
  NProgress.start()

  const userStore = useUserStore()
  const hasLogin = userStore.is_logged_in

  // 已登录分支
  if (hasLogin) {
    // token 过期：清空 store + 跳登录页
    if (isTokenExpired(userStore.token_expires_at)) {
      ElMessage({
        message: '登录已过期，请重新登录',
        type: 'warning',
        duration: 2000,
      })
      userStore.clear()
      next(`/login?redirect=${to.path}`)
      return
    }

    // 已登录访问登录页 → 跳首页
    if (to.path === '/login') {
      next({ path: '/' })
      return
    }

    next()
    return
  }

  // 未登录分支
  if (whiteList.includes(to.path)) {
    next()
    return
  }

  // 业务页：跳登录页（带 redirect，登录后跳回原路径）
  next(`/login?redirect=${to.path}`)
})

router.afterEach(() => {
  NProgress.done()
})
