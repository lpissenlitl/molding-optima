/**
 * molding-optima axios 请求封装
 *
 * - 认证：使用 X-Auth-Token header（与后端 @require_login 装饰器对齐）
 * - token 来源：useUserStore().token（Pinia persist，零 cookie 依赖）
 * - 后端响应格式：{ status, msg, data }
 * - 请求使用相对路径，由 vite.config.ts devServer.proxy 自动转发到 :8200
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

const service = axios.create({
  timeout: 30000,
})

// 请求拦截器：自动注入 X-Auth-Token
service.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    if (userStore.token) {
      // 与后端 identity/decorators.py 中 _authenticate_request 对齐
      ;(config.headers as Record<string, string>)['X-Auth-Token'] = userStore.token
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：统一错误处理 + 认证错误自动跳登录页 + token 滑动续期同步
// 与后端 identity/exceptions.py 中 BizErrorCode 严格对齐
// ⚠️ 只放真正的认证错误码，混进业务错误会导致业务错误被误判跳登录页
//   历史上 1004(ERROR_DATA_NOT_FOUND) / 1005(ERROR_DATA_FOUND) / 1007(ERROR_FOLDER_NAME_NOT_ALLOWED)
//   / 1009(不存在) 都被错误列入，现在仅保留 101001
const UNAUTHORIZED_STATUS = [101001]  // ERROR_USER_TOKEN_NOT_EXISTS（token 缺失/无效/过期）

service.interceptors.response.use(
  response => {
    // ============================
    // Token 滑动续期同步
    // ============================
    // 后端 ApiMiddleware 会在每次鉴权成功的响应里带上 X-Token-Expires-At 头
    // （值为 ISO 8601 字符串）。这里读取并同步到 store，让路由守卫的
    // "本地过期判断" 能感知到后端的滑动窗口续期，避免活跃用户突然被踢。
    //
    // 注意：
    // - axios 会把 header 名规范化为小写，所以用 'x-token-expires-at' 读取
    // - 仅在值变化时赋值（避免 Pinia 持久化无谓写入）
    // - pinia 还未初始化时跳过（如 ssr 场景）
    const newExpiresAt = response.headers?.['x-token-expires-at']
    if (newExpiresAt) {
      try {
        const userStore = useUserStore()
        if (userStore.token_expires_at !== newExpiresAt) {
          userStore.token_expires_at = newExpiresAt
        }
      } catch {
        // pinia 还未初始化时跳过
      }
    }
    return response.data
  },
  error => {
    const data = error.response?.data
    const hasResponse = !!error.response

    // ============================
    // 连接失败（后端未启 / 网络断开 / DNS 失败）
    // 特点：error.request 存在但 error.response 不存在（请求发出但没收到响应）
    // ============================
    if (!hasResponse && error.request) {
      const isTimeout = error.code === 'ECONNABORTED'
      const msg = isTimeout
        ? '请求超时，请稍后重试'
        : '无法连接服务器，请检查后端服务是否运行'

      // 联动 app store：把状态指示器变红（让用户一眼看到服务不可达）
      // 避免 "Network Error" 这种误导性提示
      try {
        const appStore = useAppStore()
        appStore.setStatus('down')
      } catch {
        // pinia 还未初始化时跳过（如 ssr 场景）
      }

      ElMessage({
        message: msg,
        type: 'error',  // 红色，比 warning 更醒目
        duration: 3000,
      })
      return Promise.reject(error)
    }

    // ============================
    // 业务错误（后端返回 4xx/5xx）
    // 特点：有 error.response，data 含 {status, msg, ...}
    // ============================
    const msg = data?.msg || error.message || '请求失败'

    ElMessage({
      message: msg,
      type: 'warning',
      duration: 3000,
    })

    // 未授权：清空 user store + 跳登录页
    // 用 router.push 而非 window.location.replace：
    //   1. 避免整页刷新（丢失 Pinia 状态、Vue 状态）
    //   2. 跳转到 /login 后路由守卫会看到 is_logged_in === false，不再二次跳转
    //   3. 带 redirect 参数，登录后跳回原路径
    if (data && UNAUTHORIZED_STATUS.indexOf(data.status) !== -1) {
      const currentPath = window.location.pathname
      if (currentPath !== '/login') {
        const userStore = useUserStore()
        userStore.clear()
        router.push({
          path: '/login',
          query: { redirect: currentPath },
        })
      }
    }

    return Promise.reject(error)
  }
)

export default service
