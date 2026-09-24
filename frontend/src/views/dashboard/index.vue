<!--
  Dashboard 数据总览（2026-09-23 重构）
  - 横向铺满 / 高信息密度 / 紧凑
  - 12 个并发 API（Promise.allSettled，部分失败不阻塞）
-->
<template>
  <div class="dashboard" v-loading="loading_all">
    <!-- ========== 标题区 ========== -->
    <header class="dashboard__header">
      <div class="dashboard__title-block">
        <h1 class="dashboard__title">
          <AppIcon :icon="greeting_icon" class="dashboard__greeting-icon" />
          {{ greeting }}, {{ display_name || '工程师' }}
        </h1>
        <p class="dashboard__subtitle">{{ today_cn }}</p>
      </div>
      <!-- 实时时钟（与系统时间同步） -->
      <div class="dashboard__clock">
        <div class="dashboard__clock-time">{{ clock_time }}</div>
      </div>
    </header>

    <!-- ========== 大 KPI 行（数据驱动） ========== -->
    <section class="dashboard__kpi">
      <div
        v-for="kpi in kpi_cards"
        :key="kpi.key"
        class="kpi-card"
        :class="[`kpi-card--${kpi.variant}`, { 'is-loaded': !kpi.loading }]"
      >
        <div class="kpi-card__head">
          <span v-if="kpi.indicator === 'dot'" class="kpi-card__dot" />
          <span v-else class="kpi-card__arrow">↑</span>
          <span class="kpi-card__label">{{ kpi.label }}</span>
          <AppIcon :icon="kpi.icon" class="kpi-card__head-icon" />
        </div>
        <div class="kpi-card__value">{{ kpi.loading ? '-' : kpi.value }}</div>
        <div class="kpi-card__sub">{{ kpi.sub }}</div>
      </div>
    </section>

    <!-- ========== 图表行（双栏：趋势 + 起源分布） ========== -->
    <section class="dashboard__charts">
      <el-row :gutter="14">
        <!-- 左：近 30 天工艺创建趋势 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
          <div class="widget widget--chart">
            <div class="widget__header">
              <span class="widget__title">近 30 天工艺创建趋势</span>
            </div>
            <div class="widget__body widget__body--chart">
              <TrendChart
                v-if="trend_data.dates.length > 0 || trends.loading"
                :data="trend_data"
                :loading="trends.loading"
              />
              <div v-else class="widget__empty">暂无趋势数据</div>
            </div>
          </div>
        </el-col>

        <!-- 右：起源类型分布 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
          <div class="widget widget--chart widget--chart-small">
            <div class="widget__header">
              <span class="widget__title">起源类型分布</span>
            </div>
            <div class="widget__body widget__body--chart">
              <OriginPie
                v-if="origin_data.length > 0 || trends.loading"
                :data="origin_data"
                :loading="trends.loading"
              />
              <div v-else class="widget__empty">暂无起源分布数据</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </section>

    <!-- ========== 双栏 widget ========== -->
    <section class="dashboard__panels">
      <el-row :gutter="14">
        <!-- 左：最近活动（时间线） -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
          <div class="widget widget--activity">
            <div class="widget__header">
              <span class="widget__title">最近活动</span>
              <el-link type="primary" :underline="false" @click="go('/process/parameter')">
                查看全部
              </el-link>
            </div>
            <div class="widget__body" v-loading="loading_recent">
              <el-timeline v-if="recent_activities.length > 0" class="activity-timeline">
                <el-timeline-item
                  v-for="item in recent_activities"
                  :key="item.id"
                  :timestamp="formatTime(item.updated_at)"
                  placement="top"
                  size="normal"
                  :type="activityType(item)"
                >
                  <div class="activity-item" @click="goActivity(item)">
                    <div class="activity-item__title">
                      {{ item.condition_no || `ID ${item.id}` }}
                      <el-tag
                        v-if="item.status"
                        size="small"
                        :type="item.status === 'active' ? 'success' : 'info'"
                        effect="plain"
                        class="activity-item__status"
                      >
                        {{ statusLabel(item.status) }}
                      </el-tag>
                    </div>
                    <div class="activity-item__meta">
                      {{ item.mold_no || '-' }} · {{ item.polymer_abbreviation || '-' }}
                      <span v-if="(item.parameters_count || 0) > 0" class="activity-item__count">
                        · {{ item.parameters_count }} 轮
                      </span>
                    </div>
                  </div>
                </el-timeline-item>
              </el-timeline>
              <div v-else class="widget__empty">暂无活动</div>
            </div>
          </div>
        </el-col>

        <!-- 右：调机进行中 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
          <div class="widget widget--tuning">
            <div class="widget__header">
              <span class="widget__title">调机进行中</span>
              <el-link type="primary" :underline="false" @click="go('/process/optimization-records')">
                查看全部
              </el-link>
            </div>
            <div class="widget__body" v-loading="loading_active">
              <ul v-if="active_optimizations.length > 0" class="tuning-list">
                <li
                  v-for="item in active_optimizations"
                  :key="item.id"
                  class="tuning-item"
                  @click="goOptimization(item)"
                >
                  <div class="tuning-item__head">
                    <span class="tuning-item__no">{{ item.condition_no || `ID ${item.id}` }}</span>
                    <span class="tuning-item__rounds">{{ item.parameters_count }} 轮</span>
                  </div>
                  <div class="tuning-item__meta">
                    {{ item.mold_no || '-' }} · {{ item.polymer_abbreviation || '-' }}
                  </div>
                  <div class="tuning-item__time">{{ formatTime(item.updated_at) }}</div>
                </li>
              </ul>
              <div v-else class="widget__empty">暂无调机迭代</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </section>

    <!-- ========== 快捷入口（单行工具栏） ========== -->
    <section class="dashboard__quick">
      <span class="quick-label">快捷入口</span>
      <div class="quick-actions">
        <button
          v-for="action in quick_actions"
          :key="action.label"
          type="button"
          class="quick-action"
          @click="go(action.path)"
        >
          <AppIcon :icon="action.icon" class="quick-action__icon" />
          <span class="quick-action__label">{{ action.label }}</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * Dashboard 数据流：12 个并发 API + 后端响应统一格式（见 session-handoff）
 * 响应格式：{ status, msg, timestamp, data: ... }
 * 拦截器返回 response.data → 业务统一用 res.data 访问
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import {
  processParameterMethod,
  dashboardStatistics,
} from '@/api'
import { useUserStore } from '@/stores/user'
import TrendChart from './components/TrendChart.vue'
import type { DashboardTrend } from './components/TrendChart.vue'
import OriginPie from './components/OriginPie.vue'
import type { DashboardOriginItem } from './components/OriginPie.vue'

// ============================================================================
// 路由 + 用户
// ============================================================================

const router = useRouter()
const userStore = useUserStore()

const display_name = computed(() => userStore.display_name)

// 时段感知问候语 + 对应图标（接系统小时数）
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 5)  return '夜深了'
  if (h < 11) return '早上好'
  if (h < 13) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})
const greeting_icon = computed(() => {
  const h = new Date().getHours()
  if (h < 5)  return 'mdi:weather-night'
  if (h < 11) return 'mdi:weather-sunny'
  if (h < 18) return 'mdi:weather-sunset'
  return 'mdi:weather-night'
})

// 实时时钟（与系统时间同步，每秒跳动）
const clock_time = ref('')
function tickClock() {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  clock_time.value = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
let clock_timer: number | null = null

const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})
const today_cn = computed(() => {
  const d = new Date()
  const weeks = ['日', '一', '二', '三', '四', '五', '六']
  return `${today.value} 周${weeks[d.getDay()]}`
})

function go(path: string) {
  router.push(path)
}

// ============================================================================
// 指标状态（统一管理 11 个指标的 loading + value）
// ============================================================================

interface StatItem {
  key: string
  label: string
  value: number
  loading: boolean
  icon?: string
  color?: string
}

// 大 KPI 3 个
const stat_active = ref<StatItem>({ key: 'active', label: '进行中工艺', value: 0, loading: true })
const stat_today = ref<StatItem>({ key: 'today', label: '今日新增', value: 0, loading: true })
const stat_pending = ref<StatItem>({ key: 'pending', label: '待调机迭代', value: 0, loading: true })

// 3 大 KPI 卡片配置（数据驱动）
type KpiVariant = 'success' | 'primary' | 'warning'
type KpiIndicator = 'dot' | 'arrow'

interface KpiCardConfig {
  key: string
  label: string
  icon: string
  variant: KpiVariant
  indicator: KpiIndicator
  sub: string
  value: number
  loading: boolean
}

const kpi_cards = computed<KpiCardConfig[]>(() => [
  {
    key: 'active',
    label: '进行中工艺',
    icon: 'mdi:lightbulb-on-outline',
    variant: 'success',
    indicator: 'dot',
    sub: '持续跟进',
    value: stat_active.value.value,
    loading: stat_active.value.loading,
  },
  {
    key: 'today',
    label: '今日新增',
    icon: 'mdi:calendar-today',
    variant: 'primary',
    indicator: 'arrow',
    sub: '当日创建',
    value: stat_today.value.value,
    loading: stat_today.value.loading,
  },
  {
    key: 'pending',
    label: '待调机迭代',
    icon: 'mdi:repeat-variant',
    variant: 'warning',
    indicator: 'dot',
    sub: '≥2 轮调机',
    value: stat_pending.value.value,
    loading: stat_pending.value.loading,
  },
])

// ============================================================================
// 快捷入口（6 个高频操作）
// ============================================================================

const quick_actions = [
  { label: '新建工艺', icon: 'mdi:plus-circle-outline', path: '/process/parameter/new' },
  { label: '工艺优化', icon: 'mdi:lightbulb-on-outline', path: '/process/optimization' },
  { label: '优化记录', icon: 'mdi:history', path: '/process/optimization-records' },
  { label: '规则中心', icon: 'mdi:format-list-checks', path: '/process/rules' },
  { label: '模具库', icon: 'mdi:cube-outline', path: '/mold/list' },
  { label: '材料库', icon: 'mdi:flask-outline', path: '/material/polymer/list' },
]

// ============================================================================
// 列表数据（最近活动 + 调机进行中）
// ============================================================================

interface ProcessItem {
  id: number
  condition_no?: string
  status?: string
  mold_no?: string
  polymer_abbreviation?: string
  parameters_count?: number
  updated_at?: string
}

const recent_activities = ref<ProcessItem[]>([])
const active_optimizations = ref<ProcessItem[]>([])
const loading_recent = ref(true)
const loading_active = ref(true)

const loading_all = ref(true)

// 图表数据（dashboardStatistics 单接口一次返回）
const trend_data = ref<DashboardTrend>({ dates: [], counts: [] })
const origin_data = ref<DashboardOriginItem[]>([])
const trends = ref({ loading: true })

const STATUS_MAP: Record<string, string> = {
  active: '使用中',
  archived: '已归档',
}
function statusLabel(s: string) {
  return STATUS_MAP[s] ?? s
}

function formatTime(s: string | undefined): string {
  if (!s) return '-'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 活动类型 → timeline 颜色
function activityType(item: ProcessItem) {
  if (item.status === 'archived') return 'info'
  if ((item.parameters_count || 0) > 1) return 'warning'
  return 'success'
}

function goActivity(item: ProcessItem) {
  router.push(`/process/parameter/${item.id}/detail`)
}

function goOptimization(_item: ProcessItem) {
  router.push('/process/optimization-records')
}

// ============================================================================
// 数据加载（11 个并发）
// ============================================================================

async function safeCall<T>(fn: () => Promise<any>, fallback: T): Promise<T> {
  try {
    const res: any = await fn()
    if (res?.status === 0) {
      return (res.data ?? fallback) as T
    }
    return fallback
  } catch (err) {
    console.error('[Dashboard] API 调用失败:', err)
    return fallback
  }
}

async function loadAll() {
  await Promise.allSettled([
    // 大 KPI 1：进行中工艺 total
    safeCall(() => processParameterMethod.get({ page_size: 1, status: 'active' }), { total: 0 })
      .then(r => (stat_active.value.value = r.total || 0))
      .finally(() => (stat_active.value.loading = false)),

    // 大 KPI 2：今日新增 total
    safeCall(
      () => processParameterMethod.get({ page_size: 1, start_date: today.value, end_date: today.value }),
      { total: 0 },
    )
      .then(r => (stat_today.value.value = r.total || 0))
      .finally(() => (stat_today.value.loading = false)),

    // 大 KPI 3：待调机迭代（active 中 parameters_count > 1 的数量）
    // 取足够多条 active 工艺（page_size=100），客户端筛 count > 1
    safeCall(
      () => processParameterMethod.get({ page_size: 100, status: 'active' }),
      { total: 0, items: [] },
    )
      .then(r => {
        const items = r.items || []
        stat_pending.value.value = items.filter((it: any) => (it.parameters_count || 0) > 1).length
      })
      .finally(() => (stat_pending.value.loading = false)),

    // 最近活动：5 条按更新时间倒序
    safeCall(
      () => processParameterMethod.get({ page_size: 5, sort: '-updated_at' }),
      { items: [] },
    )
      .then(r => {
        recent_activities.value = r.items || []
      })
      .finally(() => (loading_recent.value = false)),

    // 调机进行中：active 且 parameters_count > 0，按 parameters_count 倒序
    safeCall(
      () => processParameterMethod.get({
        page_size: 5,
        status: 'active',
        sort: '-parameters_count',
      }),
      { items: [] },
    )
      .then(r => {
        active_optimizations.value = (r.items || []).filter(
          (it: any) => (it.parameters_count || 0) > 0,
        )
      })
      .finally(() => (loading_active.value = false)),

    // 图表数据：dashboardStatistics 单接口一次拿 trend + origin_distribution
    safeCall<{ trend?: DashboardTrend; origin_distribution?: DashboardOriginItem[] }>(
      () => dashboardStatistics(),
      {},
    )
      .then(r => {
        trend_data.value = r.trend ?? { dates: [], counts: [] }
        origin_data.value = r.origin_distribution ?? []
      })
      .finally(() => (trends.value.loading = false)),
  ])
  loading_all.value = false
}

onMounted(() => {
  // 实时时钟：立即跳一次 + 每秒刷新
  tickClock()
  clock_timer = window.setInterval(tickClock, 1000)
  loadAll()
})

onBeforeUnmount(() => {
  if (clock_timer !== null) {
    window.clearInterval(clock_timer)
    clock_timer = null
  }
})
</script>

<style scoped lang="scss">
/*
 * Dashboard 总览页：看板风格、横向铺满、紧凑
 * 响应式断点：1440 / 1200 / 992 / 768
 */

.dashboard {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 4px 16px;

  /* ========== 顶部标题 ========== */
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    background: #fff;
    border: 1px solid var(--color-border-light, #ebeef5);
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    position: relative;
    overflow: hidden;

    // 顶部色条（项目主色，强标识）
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--theme-primary, #254373);
    }
  }

  &__title-block {
    flex: 1;
    min-width: 0;
  }

  &__title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    line-height: 1.2;
    display: flex;
    align-items: center;
  }

  &__greeting-icon {
    color: var(--theme-primary, #254373);
    font-size: 22px;
    margin-right: 8px;
    flex-shrink: 0;
  }

  &__subtitle {
    margin: 4px 0 0 30px;
    font-size: 12px;
    color: var(--color-text-secondary, #606266);
  }

  &__clock {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    flex-shrink: 0;
    text-align: right;
  }

  &__clock-time {
    font-size: 22px;
    font-weight: 600;
    color: var(--theme-primary, #254373);
    font-family: 'Courier New', Consolas, monospace;
    letter-spacing: 1px;
    line-height: 1.1;
  }

  /* ========== 图表行（双栏：趋势 + 起源分布） ========== */
  &__charts,
  &__panels {
    > .el-row {
      width: 100%;
    }
  }

  /* ========== 大 KPI 行 ========== */
  &__kpi {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;

    @media (max-width: 992px) {
      grid-template-columns: 1fr;
    }
  }

  /* ========== 快捷入口（单行工具栏） ========== */
  &__quick {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #fff;
    border-radius: 8px;
    padding: 10px 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    flex-wrap: wrap;
  }
}

/* ========== 大 KPI 卡片 ========== */
.kpi-card {
  position: relative;
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid var(--color-border-light, #ebeef5);
  border-left: 3px solid transparent;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  overflow: hidden;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    transform: translateY(-1px);
  }

  &__head {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--color-text-secondary, #606266);
    margin-bottom: 6px;
  }

  &__label {
    font-weight: 500;
  }

  &__head-icon {
    margin-left: auto;
    font-size: 14px;
    opacity: 0.5;
  }

  &__value {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.1;
    font-family: 'Courier New', Consolas, monospace;
    color: var(--color-text-primary, #303133);
    letter-spacing: -1px;
  }

  &__sub {
    font-size: 11px;
    color: var(--color-text-placeholder, #909399);
    margin-top: 6px;
    font-family: 'Courier New', Consolas, monospace;
  }

  /* 状态灯（实心圆点 + glow） */
  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 6px currentColor;
    flex-shrink: 0;
  }

  &__arrow {
    font-size: 14px;
    font-weight: 700;
    color: var(--el-color-primary, #254373);
    line-height: 1;
  }

  /* 主题变体 */
  &--success {
    border-left-color: var(--el-color-success, #67c23a);
    color: var(--el-color-success, #67c23a);
  }
  &--primary {
    border-left-color: var(--theme-primary, #254373);
    color: var(--theme-primary, #254373);
  }
  &--warning {
    border-left-color: var(--el-color-warning, #e6a23c);
    color: var(--el-color-warning, #e6a23c);
  }

  /* 加载中：value 显示 -，淡化 */
  &:not(.is-loaded) {
    .kpi-card__value {
      color: var(--color-text-placeholder, #c0c4cc);
    }
  }
}

/* ========== Widget（通用三栏卡片） ========== */
.widget {
  background: #fff;
  border-radius: 10px;
  border: 1px solid var(--color-border-light, #ebeef5);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  min-height: 280px;
  overflow: hidden;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--color-border-light, #ebeef5);
    background: linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0.01),
      transparent
    );
  }

  &__title {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
  }

  &__body {
    flex: 1;
    padding: 14px 16px;
    overflow: auto;
    min-height: 0;

    &--chart {
      padding: 8px 8px 4px;
    }
  }

  &__empty {
    text-align: center;
    color: var(--color-text-placeholder, #c0c4cc);
    font-size: 12px;
    padding: 32px 0;
  }

  /* 图表变体 */
  &--chart,
  &--chart-small {
    min-height: 320px;
  }

  &--chart-small {
    .widget__body--chart {
      max-width: 360px;
      margin: 0 auto;
    }
  }
}

/* ========== 活动 timeline ========== */
.activity-timeline {
  padding-top: 4px;

  :deep(.el-timeline-item__wrapper) {
    padding-bottom: 12px;
  }

  :deep(.el-timeline-item__timestamp) {
    font-size: 11px;
    color: var(--color-text-secondary, #606266);
    font-family: 'Courier New', Consolas, monospace;
    margin-bottom: 4px;
  }

  :deep(.el-timeline-item__node) {
    background-color: var(--el-color-success, #67c23a);
  }

  :deep(.el-timeline-item__node--warning) {
    background-color: var(--el-color-warning, #e6a23c);
  }

  :deep(.el-timeline-item__node--info) {
    background-color: var(--el-color-info, #909399);
  }
}

.activity-item {
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 4px;
  transition: background 0.15s;

  &:hover {
    background: var(--color-bg-page, #f5f7fa);
  }

  &__title {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-primary, #303133);
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  &__status {
    font-weight: 400;
  }

  &__meta {
    font-size: 11px;
    color: var(--color-text-secondary, #606266);
    font-family: 'Courier New', Consolas, monospace;
  }

  &__count {
    color: var(--el-color-warning, #e6a23c);
    font-weight: 500;
  }
}

/* ========== 调机列表 ========== */
.tuning-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tuning-item {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border-light, #ebeef5);
  cursor: pointer;
  transition: background 0.15s;
  border-radius: 4px;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: var(--color-bg-page, #f5f7fa);
  }

  &__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }

  &__no {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-primary, #303133);
    font-family: 'Courier New', Consolas, monospace;
  }

  &__rounds {
    font-size: 11px;
    color: var(--el-color-warning, #e6a23c);
    font-weight: 600;
    background: rgba(230, 162, 60, 0.08);
    padding: 2px 8px;
    border-radius: 10px;
  }

  &__meta {
    font-size: 11px;
    color: var(--color-text-secondary, #606266);
    margin-bottom: 2px;
  }

  &__time {
    font-size: 10px;
    color: var(--color-text-placeholder, #909399);
    font-family: 'Courier New', Consolas, monospace;
  }
}

/* ========== 快捷入口工具栏 ========== */
.quick-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary, #606266);
  white-space: nowrap;
}

.quick-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
}

.quick-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-bg-page, #f5f7fa);
  border: 1px solid var(--color-border-light, #ebeef5);
  border-radius: 6px;
  color: var(--color-text-primary, #303133);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;

  &__icon {
    font-size: 14px;
    color: var(--theme-primary, #254373);
  }

  &:hover {
    background: var(--theme-primary-light-9, rgba(37, 67, 115, 0.08));
    border-color: var(--theme-primary, #254373);
    color: var(--theme-primary, #254373);
    transform: translateY(-1px);
  }
}
</style>