<!--
  SidebarLogo：layout 顶部 Logo 区
  - 展开：图标 + 文字
  - 折叠：仅图标（节省空间）
-->
<template>
  <div :class="['sidebar-logo', { 'sidebar-logo--collapsed': collapsed }]">
    <AppIcon icon="mdi:cube-outline" class="sidebar-logo__icon" />
    <span v-if="!collapsed" class="sidebar-logo__title">Molding Optima</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  collapsed?: boolean
}>()
</script>

<style scoped lang="scss">
.sidebar-logo {
  height: 56px;
  background: var(--sidebar-logo-bg);  // 主题切换
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-shrink: 0;
  overflow: hidden;
  transition: padding 0.28s ease;

  &--collapsed {
    gap: 0;
    padding: 0;
  }

  &__icon {
    font-size: 24px;
    color: #fff;
    flex-shrink: 0;
  }

  &__title {
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
    white-space: nowrap;
    overflow: hidden;
  }
}
</style>