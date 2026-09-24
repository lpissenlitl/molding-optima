<!--
  RoundTimeline - 调机过程时间线（左侧）

  职责：展示工艺优化的所有轮次，支持点击切换 active_round
  数据：form.rounds 数组 + form.active_round_id

  每轮次节点信息：
    - 轮次号 / 类型（初始/优化/手动）/ 创建时间 / 缺陷摘要
-->
<template>
  <div class="round-timeline">
    <div class="round-timeline__header">
      <span class="round-timeline__title">调机过程</span>
      <el-tag size="small" type="info">{{ rounds?.length ?? 0 }} 轮</el-tag>
    </div>

    <el-empty
      v-if="!rounds || rounds.length === 0"
      description="尚未生成工艺参数"
      :image-size="60"
    />

    <ul v-else class="round-list">
      <li
        v-for="(round, idx) in rounds"
        :key="round.id"
        class="round-item"
        :class="{ 'is-active': round.id === activeId }"
        @click="$emit('update:activeId', round.id)"
      >
        <div class="round-item__dot" :class="`round-item__dot--${round.type}`" />
        <div class="round-item__content">
          <div class="round-item__title">
            第 {{ rounds.length - idx }} 轮
            <el-tag size="small" :type="TYPE_TAG[round.type]">{{ TYPE_LABEL[round.type] }}</el-tag>
          </div>
          <div class="round-item__time">{{ round.created_at }}</div>
          <div v-if="round.summary" class="round-item__summary">{{ round.summary }}</div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
/**
 * RoundTimeline - 调机过程时间线
 *
 * Props：rounds 数组（每轮次含 id/type/created_at/summary）
 * Emits：update:activeId（v-model:activeId 接收当前激活轮次）
 */
defineProps<{
  rounds?: Array<{
    id: number | string
    type: 'initial' | 'optimized' | 'manual'
    created_at: string
    summary?: string
  }>
  activeId?: number | string | null
}>()

defineEmits<{
  (e: 'update:activeId', id: number | string): void
}>()

const TYPE_LABEL: Record<string, string> = {
  initial: '初始',
  optimized: '优化',
  manual: '手动',
}

const TYPE_TAG: Record<string, 'success' | 'warning' | 'info'> = {
  initial: 'success',
  optimized: 'warning',
  manual: 'info',
}
</script>

<style lang="scss" scoped>
.round-timeline {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-bottom: 1px solid var(--color-border-extra-light, #ebeef5);
  }

  &__title {
    font-weight: 600;
    font-size: 14px;
  }
}

.round-list {
  list-style: none;
  margin: 0;
  padding: 8px 0;
}

.round-item {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background-color 0.2s, border-color 0.2s;

  &:hover {
    background-color: var(--color-bg-overlay, #f5f7fa);
  }

  &.is-active {
    background-color: var(--el-color-primary-light-9, #ecf5ff);
    border-left-color: var(--el-color-primary);
  }

  &__dot {
    width: 10px;
    height: 10px;
    margin-top: 6px;
    border-radius: 50%;
    flex-shrink: 0;
    background-color: var(--el-color-info);

    &--initial { background-color: var(--el-color-success); }
    &--optimized { background-color: var(--el-color-warning); }
    &--manual { background-color: var(--el-color-info); }
  }

  &__content {
    flex: 1;
    min-width: 0;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
    font-size: 13px;
  }

  &__time {
    font-size: 12px;
    color: var(--el-text-color-secondary, #909399);
    margin-top: 2px;
  }

  &__summary {
    font-size: 12px;
    color: var(--el-text-color-regular, #606266);
    margin-top: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
