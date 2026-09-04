<!--
  Placeholder：占位页面
  - 用于业务模块尚未迁移的场景
  - 显示模块名 + "待开发"提示
  - props 接收 moduleName 和 meta 信息
-->
<template>
  <div class="placeholder">
    <AppIcon icon="mdi:tools" class="placeholder__icon" />
    <h2 class="placeholder__title">{{ moduleName }}</h2>
    <p class="placeholder__desc">该模块正在迁移中，敬请期待</p>
    <div v-if="meta.path" class="placeholder__path">当前路径：{{ meta.path }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const moduleName = computed(() => route.meta?.title || '未知模块')
const meta = computed(() => ({ path: route.path }))
</script>

<style scoped lang="scss">
.placeholder {
  background: #fff;
  border-radius: 8px;
  padding: 80px 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  &__icon {
    font-size: 64px;
    color: var(--theme-primary);
    opacity: 0.4;
  }

  &__title {
    margin: 16px 0 8px;
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  &__desc {
    margin: 0 0 24px;
    color: var(--color-text-secondary);
    font-size: 14px;
  }

  &__path {
    display: inline-block;
    padding: 4px 12px;
    background: var(--color-bg-page);
    border-radius: 4px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-family: 'Consolas', 'Monaco', monospace;
  }
}
</style>