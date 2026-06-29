/**
 * 全局方法插件
 * 将所有工具方法挂载到 Vue.prototype
 */
import Vue from "vue"

// 本地存储
import {
  createStorageKey,
  setLocalStorage,
  getLocalStorage,
  removeLocalStorage,
  clearLocalStorage
} from "@/utils/storage"

// 对象操作
import { assignExistingKeys } from "@/utils/assign"

// 格式化
import { formatNumber } from "@/utils/number"
import { formatDateTime } from "@/utils/datetime"

// 权限
import { hasPermission } from "@/utils/permission"

// 数据查询
import { querySuggestions } from "@/utils/data-fetcher"

// 日期库
import dayjs from "dayjs"

// XML转换
import x2js from "x2js"

// 事件总线
const bus = new Vue()

/**
 * 安装插件
 */
export default function installGlobalMethods(VueConstructor: typeof Vue) {
  // 存储相关
  VueConstructor.prototype.$createStorageKey = createStorageKey
  VueConstructor.prototype.$setLocalStorage = setLocalStorage
  VueConstructor.prototype.$getLocalStorage = getLocalStorage
  VueConstructor.prototype.$removeLocalStorage = removeLocalStorage
  VueConstructor.prototype.$clearLocalStorage = clearLocalStorage

  // 对象操作
  VueConstructor.prototype.$assignExistingKeys = assignExistingKeys

  // 格式化
  VueConstructor.prototype.$formatNumber = formatNumber
  VueConstructor.prototype.$formatDateTime = formatDateTime

  // 权限
  VueConstructor.prototype.$hasPermission = hasPermission

  // 数据查询
  VueConstructor.prototype.$querySuggestions = querySuggestions

  // 日期库
  VueConstructor.prototype.$dayjs = dayjs

  // 事件总线
  VueConstructor.prototype.$bus = bus

  // XML转换
  VueConstructor.prototype.$x2js = new x2js()
}
