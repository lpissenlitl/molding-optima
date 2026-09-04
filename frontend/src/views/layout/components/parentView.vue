<!--
  ParentView：容器型路由占位
  - 用于中间层路由（如 /process、/process/optimization）
  - 这些路由没有自己的页面，只作为菜单分组容器
  - 通过 <router-view> 渲染子路由
-->
<template>
  <router-view />
</template>

<script setup lang="ts">
// 空组件：仅作为 router-view 容器
</script>

<style scoped lang="scss"></style>