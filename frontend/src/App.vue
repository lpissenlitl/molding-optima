<template>
  <div class="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 根组件：路由出口
</script>

<style scoped>
.app {
  min-height: 100vh;
  /*
   * 注意：根容器不要设置 min-width: 1024px。
   *
   * “后台最低 1024px、低于此值不重排”是工业后台表格页的产品决策，
   * 已由 layout.vue 的 .layout { min-width: 1024px } 承担（只作用于后台路由）。
   *
   * 若在这里重复设置，会作用到所有路由 —— 独立页面（登录页 / 404）
   * 在窄视口下会被强制撑到 1024px 宽，产生横向滚动条且布局被压缩。
   */
}
</style>