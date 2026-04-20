import request from '@/utils/request';

export const login = (name: string, password: string, ua: string) =>
  request({
    url: '/admin/login/',
    method: 'post',
    data: {
      name,
      password,
      ua
    },
  });

export const login_token = (params: any) =>
  request({
    url: '/admin/login/',
    method: 'get',
    params
  });

export const login_token_em = (params: any) =>
  request({
    url: '/admin/login_em/',
    method: 'get',
    params
  });

export const login_uuid = (params: any) =>
  request({
    url: '/admin/login_uuid/',
    method: 'get',
    params
  });

export const getInfo = () =>
  request({
    url: `/admin/user_info/`,
    method: 'get',
  });

export const logout = () =>
  request({
    url: '/user/logout/',
    method: 'post',
  });

//修改个人密码
export function resetMyPassword(data: object) {
  return request({
    url: `/admin/reset_password/`,
    method: 'put',
    data
  })
}

//重置密码
export function resetPassword(id: Number, data: object) {
  return request({
    url: `/admin/reset_password/${id}/`,
    method: 'put',
    data
  })
}