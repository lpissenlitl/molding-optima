<!-- ParentView：容器型路由占位：用于 /process、/process/optimization 这类没有自有页面的中间层菜单分组路由，仅通过 <router-view> 渲染子路由 -->

<template>
  <router-view />
</template>

<script setup lang="ts">
// 空组件：仅作为 router-view 容器
</script>

<style scoped lang="scss"></style>