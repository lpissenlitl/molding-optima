import Vue from "vue"

// ==================== 基础依赖 ====================
import App from "@/App.vue"
import store from "@/store"
import router from "@/router"

// ==================== 副作用导入（按执行顺序）====================
import "@/permission"                    // 路由权限控制
import "normalize.css"                   // CSS重置
import "@/styles/index.scss"             // 全局样式
import "@/icons/components"              // SVG图标注册
import "@/register-service-worker"       // PWA服务工作者

// ==================== UI框架 ====================
import ElementUI from "element-ui"
Vue.use(ElementUI)

// ==================== 第三方插件 ====================
import SvgIcon from "vue-svgicon"
Vue.use(SvgIcon, {
  tagName: "svg-icon",
  defaultWidth: "1em",
  defaultHeight: "1em",
})

import Print from "vue-print-nb"
Vue.use(Print)

import uploader from "vue-simple-uploader"
Vue.use(uploader)

// ==================== ECharts（按需引入）====================
import "echarts/lib/chart/bar"
import "echarts/lib/component/tooltip"
import "echarts-gl"

// ==================== 自定义插件 ====================
import {
  GlobalMethodsPlugin,
  ComponentsPlugin,
  DirectivesPlugin
} from "@/plugins"

Vue.use(GlobalMethodsPlugin)
Vue.use(ComponentsPlugin)
Vue.use(DirectivesPlugin)

// ==================== 应用配置 ====================
Vue.config.productionTip = false

// ==================== 创建Vue实例 ====================
new Vue({
  router,
  store,
  render: (h) => h(App),
}).$mount("#app")
