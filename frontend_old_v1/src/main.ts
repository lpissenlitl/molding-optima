import Vue from 'vue';

import '@/permission';
import 'normalize.css';
import '@/styles/index.scss';
import '@/icons/components';
import '@/register-service-worker';

//本地存储相关设定
import {
  getLocalStorageValue, 
  getLocalStorageObject, 
  saveLocalStorageValue, 
  saveLocalStorageObject, 
  removeLocalStorage
} from './storage/storage'

Vue.prototype.$getLocalStorageValue = getLocalStorageValue;
Vue.prototype.$getLocalStorageObject = getLocalStorageObject;
Vue.prototype.$saveLocalStorageValue = saveLocalStorageValue;
Vue.prototype.$saveLocalStorageObject = saveLocalStorageObject;
Vue.prototype.$removeLocalStorage = removeLocalStorage;

import { checkNumberFormat } from '@/utils/validate'
Vue.prototype.checkNumberFormat = checkNumberFormat

import { checkUserPermission } from '@/permission'
Vue.prototype.checkUserPermission = checkUserPermission

Vue.prototype.bus = new Vue();

// 读外部领料接口时，把返回的xml数据转化成json格式
import x2js from 'x2js'
Vue.prototype.$x2js = new x2js()  // 创建x2js对象，挂到vue原型上

import ElementUI from 'element-ui';
Vue.use(ElementUI);

import SvgIcon from 'vue-svgicon';
Vue.use(SvgIcon, {
  tagName: 'svg-icon',
  defaultWidth: '1em',
  defaultHeight: '1em',
});

import Print from 'vue-print-nb'
Vue.use(Print); 

import uploader from 'vue-simple-uploader'
Vue.use(uploader)

// 手动引入 ECharts 各模块来减小打包体积
import 'echarts/lib/chart/bar'
import 'echarts/lib/component/tooltip'

// 如果需要配合 ECharts 扩展使用，只需要直接引入扩展包即可
// 以 ECharts-GL 为例：
// 需要安装依赖：npm install --save echarts-gl，并添加如下引用
import 'echarts-gl'
// 在 webpack 环境下指向 components/ECharts.vue
import ECharts from 'vue-echarts' 
Vue.component('VChart', ECharts)  // 注册组件后即可使用

// 可拖拽窗口
import elDragDialog from './directive/el-drag-dialog'
Vue.directive('el-drag-dialog', elDragDialog)

Vue.config.productionTip = false;

import App from '@/App.vue';
import store from '@/store';
import router from '@/router';

new Vue({
  router,
  store,
  render: (h) => h(App),
}).$mount('#app');
