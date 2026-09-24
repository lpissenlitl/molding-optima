<!--
  DashboardOriginPie.vue - 起源类型分布（环形图）

  设计要点：
  - ECharts 5 按需加载（仅引入饼图 + 提示框 + 图例 + 标题）
  - 接收 props.data：{name, value, origin_type}[]（与后端对齐）
  - 环形图（radius: 50%/70%）+ 中间显示总数
  - 项目主题色板（7 种工艺起源：蓝/绿/橙/紫/青/红/灰）
-->
<template>
  <div ref="chartRef" class="origin-pie" v-loading="loading" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([PieChart, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

/**
 * Dashboard 起源分布项（与后端 statistics_service.py 对齐）
 */
export interface DashboardOriginItem {
  name: string
  value: number
  origin_type?: string
}

const props = defineProps<{
  data: DashboardOriginItem[]
  loading?: boolean
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

/** 主题色板（与项目现有 dashboard 配色一致） */
const COLORS = [
  '#254373', // 主色（深蓝）
  '#10b981', // emerald
  '#f59e0b', // amber
  '#7c3aed', // violet
  '#0ea5e9', // sky
  '#ef4444', // red
  '#94a3b8', // slate（中性灰，备用）
]

function total(): number {
  return props.data.reduce((sum, it) => sum + (it.value || 0), 0)
}

function buildOption() {
  const totalVal = total()
  return {
    color: COLORS,
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const pct = totalVal > 0 ? ((params.value / totalVal) * 100).toFixed(1) : '0.0'
        return `<div style="font-size:12px;">
          <div style="font-weight:600;margin-bottom:4px;">${params.name}</div>
          <div>数量：<b>${params.value}</b></div>
          <div>占比：<b>${pct}%</b></div>
        </div>`
      },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#ebeef5',
      textStyle: { color: '#303133' },
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
      left: 'center',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12,
      textStyle: { color: '#606266', fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: ['52%', '72%'],
        center: ['50%', '46%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: 600,
            formatter: (params: any) => {
              const pct = totalVal > 0 ? ((params.value / totalVal) * 100).toFixed(0) : '0'
              return `${params.name}\n${pct}%`
            },
          },
          scaleSize: 6,
        },
        labelLine: { show: false },
        data: props.data,
      },
      {
        // 中心总数显示（嵌套透明环）
        type: 'pie',
        radius: ['0%', '50%'],
        center: ['50%', '46%'],
        silent: true,
        label: {
          show: true,
          position: 'center',
          formatter: () => `{total|${totalVal}}\n{label|工艺总数}`,
          rich: {
            total: {
              fontSize: 22,
              fontWeight: 700,
              color: '#303133',
              fontFamily: 'Courier New, Consolas, monospace',
              lineHeight: 28,
            },
            label: {
              fontSize: 11,
              color: '#909399',
              padding: [4, 0, 0, 0],
            },
          },
        },
        itemStyle: { color: 'transparent' },
        data: [{ value: 1 }],
      },
    ],
  }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value, undefined, { renderer: 'canvas' })
  }
  chart.setOption(buildOption(), { notMerge: true })
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  nextTick(() => {
    renderChart()
    window.addEventListener('resize', handleResize)
    if (chartRef.value) {
      resizeObserver = new ResizeObserver(handleResize)
      resizeObserver.observe(chartRef.value)
    }
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})

watch(
  () => [props.data, props.loading],
  () => nextTick(renderChart),
  { deep: true },
)
</script>

<style scoped lang="scss">
.origin-pie {
  width: 100%;
  height: 100%;
  min-height: 240px;
}
</style>