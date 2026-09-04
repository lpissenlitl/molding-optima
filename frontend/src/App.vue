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
   * 兜底：低于 1024px 时 body 出现水平滚动条，
   * 避免 router-view 内的内容被压缩到 < 1024px 变难看。
   * layout.vue 里也有同样的 min-width，这里作为补充兜底。
   */
  min-width: 1024px;
}
</style>