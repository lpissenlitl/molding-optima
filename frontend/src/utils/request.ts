/**
 * molding-optima axios 请求封装
 *
 * - 认证：使用 X-Auth-Token header（与后端 @require_login 装饰器对齐）
 * - token 来源：useUserStore().token（Pinia persist，零 cookie 依赖）
 * - 后端响应格式：{ status, msg, data }
 * - 请求使用相对路径，由 vite.config.ts devServer.proxy 自动转发到 :8200
 *
 * 错误处理（参考 vue-vben-admin 风格）：
 * - 拦截器默认 toast 所有错误——这是用户视角的统一防线
 * - 调用方可在 config 上传 `errorMessageMode: 'none'` 关闭默认 toast，
 *   用于表单内联展示、后台静默等场景。
 * - 调用方只需走成功路径（业务逻辑），catch 中只 console，不重复 toast。
 * - 后端是 msg owner：拦截器直接 toast responseData.msg，信任后端文案。
 */
import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

// 扩展 axios config 类型：支持 errorMessageMode
declare module 'axios' {
  export interface AxiosRequestConfig {
    /**
     * 错误提示模式
     * - 'message'（默认）：拦截器 toast 调用 ElMessage
     * - 'none'：关闭默认 toast，调用方自行处理（表单内联 / 静默等）
     * - 'modal'：预留弹窗模式（暂未启用）
     */
    errorMessageMode?: 'message' | 'none' | 'modal'
  }
}

const service = axios.create({
  timeout: 30000,
})

// 请求拦截器：自动注入 X-Auth-Token
service.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    if (userStore.token) {
      ;(config.headers as Record<string, string>)['X-Auth-Token'] = userStore.token
    }
    return config
  },
  error => Promise.reject(error)
)

// ⚠️ UNAUTHORIZED_STATUS 只放真正的认证错误码，混进业务码会被误判跳登录页
const UNAUTHORIZED_STATUS = [101001]  // ERROR_USER_TOKEN_NOT_EXISTS
// msg 兜底正则：防 status 字段类型丢失时漏判
const UNAUTHORIZED_MSG_REGEX = /请重新登录|Authorization token is missing|Authorization token is invalid|登录已过期|登录.*失效|登录.*过期/

service.interceptors.response.use(
  response => {
    // Token 滑动续期同步：后端在响应头 X-Token-Expires-At 返回最新过期时间
    // （axios 把 header 名规范化为小写），与 store 差异赋值，避免 Pinia 重复写持久化
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

    // ---------- 识别错误类型 ----------
    const isTimeout = error.code === 'ECONNABORTED'
    const isNetworkError = !error.response && !!error.request
    const isBizError = !isNetworkError && !isTimeout && !!data && typeof data.msg === 'string'

    // ---------- 默认 toast（可被 errorMessageMode='none' 关闭）----------
    // 调用方可传 errorMessageMode: 'none' 关闭默认 toast，自己处理（如表单内联）
    const errorMessageMode = (error.config as AxiosRequestConfig | undefined)?.errorMessageMode ?? 'message'
    if (errorMessageMode !== 'none') {
      // 系统错误用固定友好文案；BizException 直接 toast 后端 msg（信任后端文案，不剥前缀）
      const userMsg = isBizError
        ? data.msg
        : isTimeout
          ? '请求超时，请稍后重试'
          : isNetworkError
            ? '无法连接服务器，请检查后端服务是否运行'
            : '服务异常，请稍后重试'
      ElMessage({ message: userMsg, type: 'error', duration: 3 * 1000 })
    }

    // ---------- console 详细（开发者调试）----------
    console.error('[request] 调用失败:', error)

    // ---------- 联动 app store 状态指示器 ----------
    if (isNetworkError) {
      try {
        const appStore = useAppStore()
        appStore.setStatus('down')
      } catch {
        // pinia 还未初始化时跳过
      }
    }

    // ---------- 未授权：清空 user store + 跳登录页 ----------
    if (data) {
      const statusMatched = UNAUTHORIZED_STATUS.indexOf(data.status) !== -1
      const msgMatched = typeof data.msg === 'string'
        && UNAUTHORIZED_MSG_REGEX.test(data.msg)
      if (statusMatched || msgMatched) {
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
    }

    // ---------- 标准化 err ----------
    // 调用方需要 err.responseData 拿原始数据（如表单内联展示）；调用方不需重复 toast
    const normalizedError: any = error
    normalizedError.isTimeout = isTimeout
    normalizedError.isNetworkError = isNetworkError
    normalizedError.isBizError = isBizError
    normalizedError.isSystemError = !isBizError
    normalizedError.responseData = data
    return Promise.reject(normalizedError)
  }
)

export default service
