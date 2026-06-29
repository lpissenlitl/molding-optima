/**
 * molding-optima axios 请求封装
 *
 * - 后端默认运行在 http://127.0.0.1:8765
 * - 认证：使用 X-Auth-Token header
 * - 后端响应格式：{ status, msg, data }
 */
import axios from "axios"
import { Message, MessageBox } from "element-ui"
import { getToken, removeToken } from "@/utils/auth"

// 后端地址（开发环境）
const BASE_URL = process.env.VUE_APP_BASE_API || "http://127.0.0.1:8765"

const service = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    if (getToken()) {
      config.headers["X-Auth-Token"] = getToken()
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
const UNAUTHORIZED_STATUS = [101001, 1004, 1005, 1007, 1009]

service.interceptors.response.use(
  response => response.data,
  error => {
    const data = error.response?.data
    const msg = data?.msg || error.message

    Message({
      message: msg,
      type: "warning",
      duration: 3000,
    })

    if (data && UNAUTHORIZED_STATUS.indexOf(data.status) !== -1) {
      if (window.location.href.indexOf("/login") === -1) {
        removeToken()
        window.location.replace("/login")
      }
    }

    return Promise.reject(error)
  }
)

export default service
