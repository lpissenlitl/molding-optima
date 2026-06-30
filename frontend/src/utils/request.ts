/**
 * molding-optima axios 请求封装
 *
 * - 认证：使用 X-Auth-Token header
 * - 后端响应格式：{ status, msg, data }
 * - 请求使用相对路径，由 vue.config.js devServer.proxy 自动转发到后端
 * - BASE_URL 仅作为环境变量入口保留，当前未传入 axios.create
 */
import axios from "axios"
import { Message, MessageBox } from "element-ui"
import { getToken, removeToken } from "@/utils/auth"

// 后端地址（环境变量入口，当前通过 vue.config.js devServer.proxy 转发）
const BASE_URL = process.env.VUE_APP_BASE_API || "http://127.0.0.1:8200"

const service = axios.create({
  // baseURL: BASE_URL,
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
