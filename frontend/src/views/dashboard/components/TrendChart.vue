<!--
  DashboardTrendChart.vue - 近 30 天工艺创建趋势（折线图）

  设计要点：
  - ECharts 5 按需加载（gzip 后约 80KB，比全量引入省 ~700KB）
  - 接收 props.data（DashboardSeries 类型）{dates: string[], counts: number[]}
  - 自动 resize（监听窗口 + 父容器尺寸变化）
  - 加载/空数据优雅降级
  - 项目主题色（#254373）作为线条主色
-->
<template>
  <div ref="chartRef" class="trend-chart" v-loading="loading" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GridComponent, TooltipComponent, TitleComponent, CanvasRenderer])

/**
 * Dashboard 趋势数据（与后端 statistics_service.py 对齐）
 */
export interface DashboardTrend {
  dates: string[]
  counts: number[]
}

const props = defineProps<{
  data: DashboardTrend
  loading?: boolean
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

/** 主色（与项目 theme 一致） */
const THEME_COLOR = '#254373'

function buildOption() {
  return {
    grid: {
      left: 36,
      right: 16,
      top: 24,
      bottom: 28,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#dcdfe6' } },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#ebeef5',
      textStyle: { color: '#303133', fontSize: 12 },
    },
    xAxis: {
      type: 'category',
      data: props.data.dates,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: {
        color: '#909399',
        fontSize: 10,
        // 每 5 个显示一个，避免拥挤
        interval: Math.floor((props.data.dates.length - 1) / 6),
      },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#f5f7fa' } },
      axisLabel: { color: '#909399', fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'line',
        data: props.data.counts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        lineStyle: { color: THEME_COLOR, width: 2 },
        itemStyle: { color: THEME_COLOR, borderColor: '#fff', borderWidth: 2 },
        emphasis: {
          focus: 'series',
          scale: 1.5,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37, 67, 115, 0.20)' },
            { offset: 1, color: 'rgba(37, 67, 115, 0.02)' },
          ]),
        },
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
.trend-chart {
  width: 100%;
  height: 100%;
  min-height: 240px;
}
</style>