<!--
  AppMain：layout 内容区
  - 渲染 router-view（业务页面通过 router 嵌套进来）
  - 加 transition 包裹：路由切换时旧页面淡出 → 新页面淡入（fade 150ms）

  重要：用 fade-only（仅 opacity），不用 fade-transform（opacity + translateX）
  - 原因：CSS 规范——祖先元素有 transform 时，后代 position: fixed 失效
    改用 translateX 会在 200ms transition 期间污染祖先 DOM
    导致 .form-actions（position: fixed）在路由切换时短暂失效
    视觉表现：button 一开始渲染在 form 末尾，200ms 后跳到视窗底部
  - 副作用：路由切换动画失去"侧滑"效果，只剩淡入淡出（视觉稍弱但更稳）
-->
<template>
  <router-view v-slot="{ Component, route }">
    <transition name="fade-only" mode="out-in">
      <component :is="Component" :key="route.fullPath" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
// 空组件：仅作为 router-view 容器 + transition 包装
</script>

<style scoped lang="scss">
/*
 * 路由切换过渡动画（fade-only）
 * - 仅透明度变化，不引入 transform
 * - duration 150ms（比 fade-transform 的 200ms 短，路由切换更利落）
 * - mode="out-in"：旧页面先消失，新页面再出现（避免重叠闪烁）
 */
.fade-only-enter-active,
.fade-only-leave-active {
  transition: opacity 0.15s ease;
}

.fade-only-enter-from,
.fade-only-leave-to {
  opacity: 0;
}
</style>
