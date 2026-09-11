/**
 * 全局方法插件（Vue 3 + app.config.globalProperties）
 *
 * 用途：把常用工具挂载到全局 this 上，使组件可以通过 this.$xxx 调用。
 * 历史版本：本文件早期是 Vue 2 风格（VueConstructor.prototype.$xxx），
 * 在 Vue 3 中无效。现改为 app.config.globalProperties，可继续以
 * `this.$xxx` 在 Options API 组件中调用（模板里也可用）。
 *
 * 注：
 * - 仅迁移 mold 视图实际用到的方法（最小可用版本）
 * - 其他组件若仍依赖旧 API，按需补全
 */
import type { App } from 'vue'

// 本地存储
import {
  createStorageKey,
  setLocalStorage,
  getLocalStorage,
  removeLocalStorage,
  clearLocalStorage
} from '@/utils/storage'

// 对象操作
import { assignExistingKeys } from '@/utils/assign'

// 格式化
import { formatNumber } from '@/utils/number'
import { formatDateTime } from '@/utils/datetime'

// 权限
import { hasPermission } from '@/utils/permission'

// 数据查询
import { querySuggestions } from '@/utils/data-fetcher'

// 日期库
import dayjs from 'dayjs'

// App Store（仅需 pageSizeArray，其它 AppStore 字段不挂在全局）
import { useAppStore } from '@/stores/app'

/**
 * 安装全局方法（Vue 3 风格）
 */
export default function installGlobalMethods(app: App) {
  // 存储相关
  app.config.globalProperties.$createStorageKey = createStorageKey
  app.config.globalProperties.$setLocalStorage = setLocalStorage
  app.config.globalProperties.$getLocalStorage = getLocalStorage
  app.config.globalProperties.$removeLocalStorage = removeLocalStorage
  app.config.globalProperties.$clearLocalStorage = clearLocalStorage

  // 对象操作
  app.config.globalProperties.$assignExistingKeys = assignExistingKeys

  // 格式化
  app.config.globalProperties.$formatNumber = formatNumber
  app.config.globalProperties.$formatDateTime = formatDateTime

  // 权限
  app.config.globalProperties.$hasPermission = hasPermission

  // 数据查询
  app.config.globalProperties.$querySuggestions = querySuggestions

  // 日期库
  app.config.globalProperties.$dayjs = dayjs

  // 分页大小选项（兼容旧 $store.state.app.pageSizeArray）
  // 代替旧 Vuex store/modules/app.ts，配置在 Pinia app store 中
  app.config.globalProperties.$pageSizeArray = useAppStore().pageSizeArray
}
