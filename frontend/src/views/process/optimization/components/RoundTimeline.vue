<!-- RoundTimeline - 调机过程时间线 -->
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
            第 {{ round.seq_idx ?? idx + 1 }} 轮
            <el-tag size="small" :type="TYPE_TAG[round.type]">{{ TYPE_LABEL[round.type] }}</el-tag>
            <AppIcon v-if="round.sealed" icon="mdi:lock-outline" class="round-item__lock" />
          </div>
          <!-- 占位 round（parameter_id 为 null）不显示时间：占位是页面初始化时建的，时间不准确 -->
          <div v-if="round.parameter_id" class="round-item__time">{{ formatLocalTime(round.created_at) }}</div>
          <div v-if="round.summary" class="round-item__summary">{{ round.summary }}</div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
defineProps<{
  rounds?: Array<{
    id: number | string
    type: 'initial' | 'optimized' | 'manual'
    created_at: string
    summary?: string
    /** 业务轮次号（后端 ProcessParameter.seq_idx）；未调过后端接口时为 null */
    seq_idx?: number | null
    /** 后端 ProcessParameter.id：占位 round 为 null（页面初始化时建的未提交 round） */
    parameter_id?: number | null
    /** 该轮是否已归档（已落库评价 ⇒ 参数锁死） */
    sealed?: boolean
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

/** 把 round.created_at（ISO 8601）按浏览器本地时区格式化（后端 DB 字面值与前端 UTC 串代表同一时刻） */
function formatLocalTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return dayjs(d).format('YYYY-MM-DD HH:mm:ss')
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
    background-color: #f5f9ff;
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

  /* 归档锁标记：该轮参数已锁定 */
  &__lock {
    font-size: 13px;
    color: var(--el-text-color-secondary, #909399);
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
