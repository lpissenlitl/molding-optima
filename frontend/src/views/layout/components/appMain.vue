<!--
  AppMain：layout 内容区
  - 渲染 router-view（业务页面通过 router 嵌套进来）
  - 加 transition 包裹：路由切换时旧页面淡出 → 新页面淡入（fade 200ms）
-->
<template>
  <router-view v-slot="{ Component, route }">
    <transition name="fade-transform" mode="out-in">
      <component :is="Component" :key="route.fullPath" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
// 空组件：仅作为 router-view 容器 + transition 包装
</script>

<style scoped lang="scss">
/*
 * 路由切换过渡动画
 * - fade-transform：透明度 + 位移
 * - duration 200ms（与 molding-expert 风格一致）
 * - mode="out-in"：旧页面先消失，新页面再出现（避免重叠闪烁）
 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.2s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(10px);
}
</style>
