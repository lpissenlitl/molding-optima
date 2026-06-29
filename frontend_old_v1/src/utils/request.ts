import axios from 'axios';
import { Message, MessageBox } from 'element-ui';
import { removeUserId, getToken } from '@/utils/auth';
import { UserModule } from '@/store/modules/user';
let url = ''
let ws_host = ''
if (process.env.NODE_ENV === 'development'){
  url = 'http://127.0.0.1:8200'
  ws_host = 'ws://127.0.0.1:8200'
} else if (process.env.NODE_ENV === 'production'){
  url = 'http://127.0.0.1:9167'
  ws_host = 'ws://47.103.1.182:9167'
}

url = 'http://127.0.0.1:8200'


const service = axios.create({
  //本地测试app，取消注释
  // baseURL: url,
  timeout: 10000 * 6,
  // withCredentials: true,
});

// Request interceptors
service.interceptors.request.use(
  (config) => {
    // Add X-Token header to every request, you can add other custom headers here
    if (getToken()) {
      config.headers['X-AUTH-TOKEN'] = getToken();
    }
    return config;
  },
  (error) => {
    Promise.reject(error);
  },
);

let ERROR_TOKEN = [1004, 1005, 1007, 1009]
// Response interceptors
service.interceptors.response.use(
  response => {
    /**
     * status为非0是抛错 可结合自己业务进行修改
     */
    return response.data
  },
  error => {
    if(error.response.data.msg){
      Message({
        message: error.response.data.msg,
        type: 'warning'
      })
    } else {
      Message({
        message: error.message,
        type: 'warning',
        duration: 5 * 1000
      })
    }

    if(ERROR_TOKEN.indexOf(error.response.data.status) !== -1){
      if (window.location.href.indexOf('/login') == -1){
        if(error.response.config.url !== "/admin/user_info/") {
          // user_info 走自己的逻辑
          removeUserId()
          window.location.replace('/login')
        }

      }
    }
    return Promise.reject(error)
  }
);

export default service;
export const WS_HOST = ws_host;
