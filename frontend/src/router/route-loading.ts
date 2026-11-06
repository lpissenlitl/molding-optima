/**
 * 路由级 loading 状态（手动控制，替代 Suspense）
 * - 背景：Vue Router 4 异步路由组件在 dev 模式首次访问需 Vite transform 全链路（约 0.5-1.5s），用户体感"卡死"；期望点击立即跳转、加载在跳转后异步进行
 * - 为什么不用 Suspense：Router 4 的异步组件解析在内部 await，与 Suspense 的 fallback 协议有时序问题，实测包裹后 1-2s 空白期内看不到任何反馈
 * - 为什么用模块级 ref：permission.ts 与 appMain.vue 不在同一组件树，无法 provide/inject；store 太重，模块级 ref 简单直接，SPA 单页应用无 SSR 状态污染风险
 * - 同步时序：permission.ts beforeEach 同步 startRouteLoading() → Vue 调度 reactive 更新（microtask）→ 视觉上 loading 立即出现；afterEach 同步 stopRouteLoading() → 旧 loading 隐藏 + 新组件渲染
 */
import { ref } from 'vue'

/** 路由切换中：true = 显示 loading 占位，false = 显示业务页面 */
export const isRouteLoading = ref(false)

/** 设置 loading 状态（由 permission.ts 的导航守卫调用） */
export function startRouteLoading() {
  isRouteLoading.value = true
}

export function stopRouteLoading() {
  isRouteLoading.value = false
}