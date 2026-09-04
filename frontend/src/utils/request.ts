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

// 响应拦截器：统一错误处理 + 401 自动登出
// 与后端 const.py 中未授权状态码对齐
const UNAUTHORIZED_STATUS = [101001, 1004, 1005, 1007, 1009]

service.interceptors.response.use(
  response => response.data,
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
    if (data && UNAUTHORIZED_STATUS.indexOf(data.status) !== -1) {
      if (window.location.href.indexOf('/login') === -1) {
        const userStore = useUserStore()
        userStore.clear()
        window.location.replace('/login')
      }
    }

    return Promise.reject(error)
  }
)

export default service
