/**
 * axios 请求封装
 *
 * - 认证：X-Auth-Token header（与后端 @require_login 装饰器对齐），来源是 useUserStore().token
 * - 后端响应：{ status, msg, data }
 * - dev 用相对路径，由 vite devServer.proxy 自动转发到 :8200
 * - 错误处理：拦截器默认 toast 所有错误，调用方可传 errorMessageMode: 'none' 关闭默认 toast
 *   用于表单内联展示等场景
 * - 后端是 msg owner：拦截器直接 toast responseData.msg，信任后端文案
 */
import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

declare module 'axios' {
  export interface AxiosRequestConfig {
    /**
     * 错误提示模式
     * - 'message'（默认）：拦截器 toast
     * - 'none'：关闭默认 toast，调用方自行处理
     * - 'modal'：预留弹窗模式（暂未启用）
     */
    errorMessageMode?: 'message' | 'none' | 'modal'
  }
}

const service = axios.create({ timeout: 30000 })

// 自动注入 X-Auth-Token
service.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    if (userStore.token) {
      ;(config.headers as Record<string, string>)['X-Auth-Token'] = userStore.token
    }
    return config
  },
  error => Promise.reject(error),
)

// 只放真正的认证错误码，混进业务码会被误判跳登录页
const UNAUTHORIZED_STATUS = [101001] // ERROR_USER_TOKEN_NOT_EXISTS
// msg 兜底正则：防 status 字段类型丢失时漏判
const UNAUTHORIZED_MSG_REGEX = /请重新登录|Authorization token is missing|Authorization token is invalid|登录已过期|登录.*失效|登录.*过期/

service.interceptors.response.use(
  response => {
    // token 滑动续期：后端在响应头 X-Token-Expires-At 返回最新过期时间（header 名被 axios 规范化为小写）
    const newExpiresAt = response.headers?.['x-token-expires-at']
    if (newExpiresAt) {
      try {
        const userStore = useUserStore()
        if (userStore.token_expires_at !== newExpiresAt) {
          userStore.token_expires_at = newExpiresAt
        }
      } catch {
        /* pinia 还未初始化时跳过 */
      }
    }
    return response.data
  },
  error => {
    const data = error.response?.data
    const isTimeout = error.code === 'ECONNABORTED'
    const isNetworkError = !error.response && !!error.request
    const isBizError = !isNetworkError && !isTimeout && !!data && typeof data.msg === 'string'

    const errorMessageMode = (error.config as AxiosRequestConfig | undefined)?.errorMessageMode ?? 'message'
    if (errorMessageMode !== 'none') {
      // 系统错误用固定友好文案；BizException 直接 toast 后端 msg
      const userMsg = isBizError
        ? data.msg
        : isTimeout
          ? '请求超时，请稍后重试'
          : isNetworkError
            ? '无法连接服务器，请检查后端服务是否运行'
            : '服务异常，请稍后重试'
      ElMessage({ message: userMsg, type: 'error', duration: 3 * 1000 })
    }

    // 开发者调试：详细错误（toast 是用户视角，这里是开发者视角）
    console.error('[request] 调用失败:', error)

    // 联动 app store 状态指示器
    if (isNetworkError) {
      try {
        useAppStore().setStatus('down')
      } catch {
        /* pinia 还未初始化时跳过 */
      }
    }

    // 未授权：清空 user store + 跳登录页（双轨：status 码 + msg 正则兜底）
    if (data) {
      const statusMatched = UNAUTHORIZED_STATUS.indexOf(data.status) !== -1
      const msgMatched = typeof data.msg === 'string' && UNAUTHORIZED_MSG_REGEX.test(data.msg)
      if (statusMatched || msgMatched) {
        const currentPath = window.location.pathname
        if (currentPath !== '/login') {
          useUserStore().clear()
          router.push({ path: '/login', query: { redirect: currentPath } })
        }
      }
    }

    // 标准化 err：调用方需要 err.responseData 拿原始数据（如表单内联展示）
    const normalizedError: any = error
    normalizedError.isTimeout = isTimeout
    normalizedError.isNetworkError = isNetworkError
    normalizedError.isBizError = isBizError
    normalizedError.isSystemError = !isBizError
    normalizedError.responseData = data
    return Promise.reject(normalizedError)
  },
)

export default service