import router from './router';
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';
import { Message } from 'element-ui';
import { getUserId } from '@/utils/auth';
import { Route } from 'vue-router';
import { UserModule } from '@/store/modules/user';
import { login_token, login_token_em, login_uuid } from '@/api/login';

NProgress.configure({ showSpinner: false });

const whiteList = [ '/login' ];

router.beforeEach((to: Route, from: Route, next: any) => {
  NProgress.start();

  let token_position = `${to.fullPath}`.indexOf("?token=")
  let token_em_position = `${to.fullPath}`.indexOf("?token_em=")
  // 伊之密单点登录/api/custom/open/sso/getUserinfoByUui?uuid=
  let uuid_yizumi = `${to.fullPath}`.indexOf("?uuid=")
  if(uuid_yizumi !== -1) {
    loginWithUuid(to, from, next, uuid_yizumi)
  } 
  if(token_position !== -1) {
    loginWithTokenEm(to, from, next, token_position)
  } else if (token_em_position !== -1) {
    loginWithTokenEm(to, from, next, token_em_position)
  } else {
    if (getUserId()) {
      if (to.path === '/login') {
        next({ path: '/' });
        NProgress.done(); // If current page is dashboard will not trigger afterEach hook, so manually handle it
      } else {
        // debugger
        if (UserModule.roles.length === 0) {
          UserModule.GetInfo().then(() => {
            next();
          }).catch((err) => {
            UserModule.FedLogOut().then(() => {
              // Message.error(err || '验证失败,请重新登录');
              next({ path: '/login' })
            });
          });
        } else {
          next();
        }
      }
    } else {
      let num = `${to.fullPath}`.indexOf("?id=")
      if (whiteList.indexOf(to.path) !== -1) {
        next();
      } else if(num === -1) {
        next(`/login?redirect=${to.path}`); // Redirect to login page
      } else {
        // 转化之后的格式是：/login?redirect=%2Freservation%2Fdetail%3Fid%3D111
        // direct_path是%3Fid%3D111
        next(`/login?redirect=${to.path + localStorage.getItem("direct_path")}`); // Redirect to reservation detail page
      } 
    }
  }
});

router.afterEach(() => {
  NProgress.done();
});

function loginWithUuid(to: Route, from: Route, next: any, token_position:any){

  let token = `${to.fullPath}`.substring(token_position+6, )
  login_uuid({"token":token}).then((res)=>{
    // 三种情况
    // 1.如果验证token正确,则进入模具列表
    // 2.用户不存在
    // 3.验证码已失效
    if(res.status === 0 && res.data.code === 200 && res.data.msg === "success" && res.data.error_message === "用户不存在"){
      Message.error(res.data.error_message);
    }
    if (res.status === 0 && res.data.user) {
      UserModule.setLoginData(res.data.user)
      next({ path: '/mold/list' });
      NProgress.done(); // If current page is dashboard will not trigger afterEach hook, so manually handle it
    }
    if(res.status === 0 && res.data.code === 40101004 ){
      Message.error(res.data.msg);
    }
  })
}

// 第一步:对方系统调用登录api,获取token
// 第二步:访问 http://localhost:8080/mold/list/?token=262fdd64-1923-43fb-be57-ceda897d3938
// 第三步:从MES进来,免登录页面,带token的,验证token,转入模具列表;如果无效,转入登录界面
function loginWithToken(to: Route, from: Route, next: any, token_position:any){

  let token = `${to.fullPath}`.substring(token_position+7, )
  login_token_em({"token":token}).then((res)=>{
    // 如果验证token不正确,转至MES登录页面
    if(!res.data){
      window.location.href ="https://iiot2.yizumi.com" // "http://kunpeng.yizumi.com:82"
    }
    // 如果验证token正确,则进入模具列表
    if (res.status === 0) {
    UserModule.setLoginData(res.data)

    next({ path: '/mold/list' });
    NProgress.done(); // If current page is dashboard will not trigger afterEach hook, so manually handle it
    }
  })
}


// 第一步:对方访问 http://localhost:8080/mold/list/?token_em=262fdd64-1923-43fb-be57-ceda897d3938
// 第二步:系统调用对方api,验证token_em是否有效
// 第三步:如果有效,免登录页面,转入模具列表;如果无效,转入登录界面
function loginWithTokenEm(to: Route, from: Route, next: any, token_em_position:any){

  let token = `${to.fullPath}`.substring(token_em_position+7, )
  login_token_em({"token":token}).then((res)=>{
    // 如果验证token_em不正确,转至MES登录页面
    if (res.status === 0) {
    if(res.data.result === false){
      window.location.href ="https://iiot2.yizumi.com" // "http://kunpeng.yizumi.com:82"
    } else {
    // 如果验证token正确,则进入模具列表
    UserModule.setLoginData(res.data.user)

    next({ path: '/mold/list' });
    NProgress.done(); // If current page is dashboard will not trigger afterEach hook, so manually handle it
    }
  }
})
}

// 检查用户权限
export function checkUserPermission(permission_des: string) {
  let allow_permissions: string[] = UserModule.permissions
  if (permission_des) {
    if (allow_permissions.includes(permission_des)) {
      return true
    } else {
      return false
    }
  }
  return false
}