/**
 * 路由守卫（Vue 3 + Pinia 版本）
 *
 * 设计要点：
 * - 用 userStore.is_logged_in 判断登录态（Pinia 持久化）
 * - 白名单（/login、/404）无需登录
 * - 未登录访问业务页 → 跳 /login?redirect=原路径
 * - 已登录访问 /login → 跳首页
 * - 路由切换时显示 NProgress 顶部进度条（告诉用户"系统在工作"）
 *
 * 后续扩展点：
 * - SSO token 自动登录
 * - 路由进入时 fetchInfo 加载用户角色/权限
 * - 动态路由注入（基于角色过滤菜单）
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

router.beforeEach(async (to, from, next) => {
  // 启动顶部进度条
  NProgress.start()

  const userStore = useUserStore()
  const hasLogin = userStore.is_logged_in

  // ========== 已登录 ==========
  if (hasLogin) {
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
