<!--
  Dashboard：登录后的看板首页
  - 占位内容，用于验证 layout 的视觉效果
  - 4 个数据卡片 + 2 列面板（最近工艺 / 快捷入口）
  - 响应式：md 以下两列变单列、4 卡片变 2x2
-->
<template>
  <div class="dashboard">
    <header class="dashboard__header">
      <h1 class="dashboard__greeting">👋 欢迎回来，工程师</h1>
      <p class="dashboard__date">今天是 2026 年 9 月 2 日</p>
    </header>

    <!-- 数据卡片 -->
    <section class="dashboard__stats">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <div class="stat-card__icon" :style="{ background: stat.color }">
          <AppIcon :icon="stat.icon" />
        </div>
        <div class="stat-card__body">
          <div class="stat-card__value">{{ stat.value }}</div>
          <div class="stat-card__label">{{ stat.label }}</div>
        </div>
      </div>
    </section>

    <!-- 双面板 -->
    <section class="dashboard__panels">
      <div class="panel">
        <h2 class="panel__title">最近工艺参数</h2>
        <ul class="panel__list">
          <li v-for="item in recentProcesses" :key="item.id" class="panel__item">
            <span class="panel__item-name">{{ item.name }}</span>
            <span class="panel__item-meta">{{ item.date }}</span>
          </li>
        </ul>
      </div>

      <div class="panel">
        <h2 class="panel__title">快捷入口</h2>
        <div class="quick-actions">
          <button v-for="action in quickActions" :key="action.label" class="quick-action">
            <AppIcon :icon="action.icon" />
            <span>{{ action.label }}</span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
// 占位数据：后续从后端 API 获取
const stats = [
  { label: '模具数', value: 24, icon: 'mdi:cube-outline', color: '#254373' },
  { label: '材料数', value: 18, icon: 'mdi:flask-outline', color: '#10b981' },
  { label: '设备数', value: 12, icon: 'mdi:robot-industrial', color: '#f59e0b' },
  { label: '活跃工艺', value: 7, icon: 'mdi:chart-line', color: '#ef4444' },
]

const recentProcesses = [
  { id: 1, name: 'ABS 模具 A-001 注塑工艺', date: '2026-09-01' },
  { id: 2, name: 'PA66 + 30%GF 工艺优化', date: '2026-08-31' },
  { id: 3, name: 'PC 透明件试模参数', date: '2026-08-30' },
  { id: 4, name: 'POM 齿轮件调模记录', date: '2026-08-29' },
  { id: 5, name: 'PP 薄壁件工艺', date: '2026-08-28' },
]

const quickActions = [
  { label: '新建工艺参数', icon: 'mdi:plus-circle' },
  { label: '查看模具库', icon: 'mdi:cube-outline' },
  { label: '规则管理', icon: 'mdi:format-list-checks' },
]
</script>

<style scoped lang="scss">
.dashboard {
  max-width: 1280px;
  margin: 0 auto;

  &__header {
    margin-bottom: 24px;
  }

  &__greeting {
    margin: 0 0 8px;
    font-size: 24px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  &__date {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 14px;
  }

  &__stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;

    @include breakpoint-down(md) {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  &__panels {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 16px;

    @include breakpoint-down(md) {
      grid-template-columns: 1fr;
    }
  }
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }

  &__icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 24px;
    flex-shrink: 0;
  }

  &__value {
    font-size: 24px;
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.2;
  }

  &__label {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-top: 2px;
  }
}

.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  &__title {
    margin: 0 0 16px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  &__list {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  &__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--color-border-light);
    font-size: 14px;

    &:last-child {
      border-bottom: none;
    }
  }

  &__item-name {
    color: var(--color-text-primary);
  }

  &__item-meta {
    color: var(--color-text-secondary);
    font-size: 12px;
  }
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: 6px;
  color: var(--color-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;

  &:hover {
    background: var(--theme-primary-light-9);
    border-color: var(--theme-primary);
    color: var(--theme-primary);
  }
}
</style>