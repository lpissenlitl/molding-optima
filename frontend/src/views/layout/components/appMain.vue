<!--
  AppMain：layout 内容区
  - 渲染 router-view（业务页面通过 router 嵌套进来）
  - 路由切换淡入淡出（fade-only，不用带 translateX 的语义）
    祖先：加了 transform 会导致子节点 position: fixed 失效（路由切换 200ms 内 .form-actions 会跳变）
  - 路由级 loading：点击瞬间同步显示骨架屏，afterEach 后切回 router-view
-->
<template>
  <!-- 路由级 loading：点击瞬间立即触发，覆盖整个内容区 -->
  <div v-if="isRouteLoading" class="route-loading-overlay">
    <el-skeleton :rows="5" animated class="route-loading__skeleton">
      <template #template>
        <el-skeleton-item variant="h1" style="width: 35%;" />
        <el-skeleton-item
          v-for="i in 4"
          :key="`r-${i}`"
          variant="text"
          :style="{ width: `${70 + (i * 6)}%`, marginTop: '14px' }"
        />
        <div style="display: flex; gap: 14px; margin-top: 22px;">
          <el-skeleton-item variant="button" style="width: 96px;" />
          <el-skeleton-item variant="button" style="width: 96px;" />
          <el-skeleton-item variant="button" style="width: 96px;" />
        </div>
      </template>
    </el-skeleton>
  </div>

  <router-view v-else v-slot="{ Component, route }">
    <transition name="fade-only" mode="out-in">
      <component :is="Component" :key="route.fullPath" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
import { isRouteLoading } from '@/router/route-loading'
</script>

<style scoped lang="scss">
.fade-only-enter-active,
.fade-only-leave-active {
  transition: opacity 0.15s ease;
}

.fade-only-enter-from,
.fade-only-leave-to {
  opacity: 0;
}

.route-loading-overlay {
  width: 100%;
  height: 100%;
  min-height: 400px;
  background-color: var(--color-bg-page, #f5f7fa);
  padding: 16px 4px;
}

.route-loading__skeleton {
  max-width: 800px;
  margin: 0 auto;
}
</style>