import router from "./router"
import NProgress from "nprogress"
import "nprogress/nprogress.css"
import { getUserId } from "@/utils/auth"
import { Route } from "vue-router"
import { UserModule } from "@/store/modules/user"
import { Message } from "element-ui"

NProgress.configure({ showSpinner: false })

const whiteList = ["/login"]

router.beforeEach(async (to: Route, from: Route, next: any) => {
  NProgress.start()

  const ssoToken = to.query.token
  if (ssoToken) {
    try {
      await UserModule.GetSSOLogin(ssoToken)
      const { token, ...restQuery } = to.query
      next({ path: to.path, query: restQuery, replace: true })
      return
    } catch (e) {
      console.log(e)
      Message.error("登录失败，请重新登录")
      next(`/login?redirect=${to.fullPath}`)
      NProgress.done()
      return
    }
  }

  if (getUserId()) {
    if (to.path === "/login") {
      next({ path: "/" })
      NProgress.done() // If current page is dashboard will not trigger afterEach hook, so manually handle it
    } else {
      // debugger
      if (UserModule.roles.length === 0) {
        UserModule.GetInfo().then(() => {
          next()
        }).catch((err) => {
          UserModule.FedLogOut().then(() => {
            next({ path: "/login" })
          })
        })
      } else {
        next()
      }
    }
  } else {
    if (whiteList.indexOf(to.path) !== -1) {
      next()
    } else {
      next(`/login?redirect=${to.path}`) // Redirect to login page
    }
  }
})

router.afterEach(() => {
  NProgress.done()
})