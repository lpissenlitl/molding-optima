/**
 * molding-optima 登录认证相关 API
 *
 * 参考 molding-expert/molding-expert-web/src/api/login.ts
 */
import request from "@/utils/request"

// 登录
export const login = (params: { username: string; password: string; ua: string }) => {
  return request({
    url: "/api/login/",
    method: "post",
    data: params,
  })
}

// SSO 登录
export const SSOLogin = (token: string) => {
  return request({
    url: "/api/sso-login/",
    method: "post",
    data: { token },
  })
}

// 登出
export const logout = () => {
  return request({
    url: "/api/logout/",
    method: "post",
  })
}

// 获取当前登录用户信息
export const getInfo = () => {
  return request({
    url: "/api/profile/",
    method: "get",
  })
}

// 用户修改自己的密码
export function resetMyPassword(data: object) {
  return request({
    url: "/api/profile/reset-password/",
    method: "put",
    data,
  })
}