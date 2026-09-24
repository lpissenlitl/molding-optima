<!--
  RuleMethodGraph.vue - 模糊规则流程图预览

  业务说明：
    - 把"前置条件 + 结论动作"以节点化思维可视化展示
    - 采用「聚合节点（AND-gate）」模式，替代笛卡尔积全连接
    - 节点点击 → 通知父组件滚动到对应行 + 高亮闪烁

  视觉设计：
    - 三列布局：左 IF 条件列 / 中 AND 聚合节点 / 右 THEN 动作列
    - 节点 = 圆角白底卡片 + 主题色左边框 + 阴影
    - AND 节点 = 蓝绿渐变胶囊 + 圆形 icon，明确标识"规则核心"
    - 连线策略：所有条件 → AND 节点（汇聚），AND 节点 → 所有动作（发散）

  数据流：
    - props: conditions[] / actions[] / keywords[]
    - emit: node-click({ type, index })
-->
<template>
  <el-card
    header="流程图预览"
    shadow="never"
    :class="['rule-graph-card', layoutClass]"
    ref="cardRef"
  >
    <div v-if="conditions.length === 0 && actions.length === 0" class="empty-placeholder">
      <AppIcon icon="mdi:graph-outline" :size="48" style="color: #c0c4cc;" />
      <div class="empty-tip">添加条件 / 动作后，流程图将在此实时呈现</div>
    </div>

    <div v-else ref="rootRef" class="rule-graph">
      <!-- ============ 条件列 ============ -->
      <div class="node-column node-column--conditions">
        <div class="column-label">前置条件 (IF)</div>
        <div
          v-for="(cond, i) in conditions"
          :key="`c-${i}`"
          :ref="el => setConditionRef(el, i)"
          :class="['graph-node', nodeClass(cond, 'condition')]"
          @click="$emit('node-click', { type: 'condition', index: i })"
        >
          <AppIcon :icon="iconForCondition(cond)" :size="20" />
          <div class="node-body">
            <div class="node-title">{{ aliasOf(cond.keyword) || '(未选)' }}</div>
            <div class="node-meta">{{ cond.level || '?' }}</div>
          </div>
        </div>
      </div>

      <!-- ============ 中间：AND 聚合节点 ============ -->
      <div class="rule-core-wrapper">
        <div ref="ruleCoreNode" class="rule-core">
          <div class="rule-core-circle">
            <AppIcon icon="mdi:set-center" :size="20" />
          </div>
          <div class="rule-core-text">AND</div>
          <div class="rule-core-sub">RULE</div>
        </div>
      </div>

      <!-- ============ 动作列 ============ -->
      <div class="node-column node-column--actions">
        <div class="column-label">结论动作 (THEN)</div>
        <div
          v-for="(act, i) in actions"
          :key="`a-${i}`"
          :ref="el => setActionRef(el, i)"
          :class="['graph-node', nodeClass(act, 'action')]"
          @click="$emit('node-click', { type: 'action', index: i })"
        >
          <AppIcon :icon="iconForAction(act)" :size="20" />
          <div class="node-body">
            <div class="node-title">{{ aliasOf(act.keyword) || '(未选)' }}</div>
            <div class="node-meta">{{ actionLabel(act.action) }} {{ act.value || '?' }}</div>
          </div>
        </div>
      </div>

      <!-- ============ 连线层 ============ -->
      <svg
        class="graph-edges"
        v-if="svgSize.width > 0 && svgSize.height > 0"
        :width="svgSize.width"
        :height="svgSize.height"
      >
        <defs>
          <!-- 箭头 marker：使用 userSpaceOnUse 使箭头尺寸不受 stroke-width 影响 -->
          <marker
            id="arrow-head"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="5"
            orient="auto"
            markerUnits="userSpaceOnUse"
          >
            <path d="M0 0 L 10 5 L 0 10 z" fill="#67c23a" />
          </marker>
        </defs>
        <!-- 条件 → AND 节点（输入汇聚，蓝色无箭头） -->
        <path
          v-for="(edge, i) in inputEdges"
          :key="`in-${i}`"
          :d="edge.d"
          stroke="#409eff"
          stroke-width="2"
          stroke-opacity="0.85"
          fill="none"
          stroke-linecap="round"
        />
        <!-- AND 节点 → 动作（输出发散，绿色有箭头） -->
        <path
          v-for="(edge, i) in outputEdges"
          :key="`out-${i}`"
          :d="edge.d"
          stroke="#67c23a"
          stroke-width="2"
          stroke-opacity="1"
          fill="none"
          stroke-linecap="round"
          marker-end="url(#arrow-head)"
        />
      </svg>
    </div>
  </el-card>
</template>

<script setup lang="ts">
/**
 * 模糊规则流程图预览（Vue 3 Composition API 版）
 *
 * 关键设计：
 * 1. 节点类型判断：根据 keyword.category 决定颜色 + 图标
 * 2. 连线策略（聚合节点版）：
 *    - 输入段：所有条件 → 中间 AND 节点（汇聚，蓝色无箭头）
 *    - 输出段：中间 AND 节点 → 所有动作（发散，绿色有箭头）
 *    - 避免笛卡尔积交叉，可读性远优于全连接
 * 3. 连线坐标：根据节点 DOM 位置实时计算（响应式）
 * 4. 节点点击：emit('node-click') 让父组件处理滚动 + 高亮
 */
import { ref, onMounted, onBeforeUnmount, nextTick, watch as watchRef, computed } from 'vue'
import type { RuleKeyword } from '@/types/rule'

// ============================================================================
// Props / Emits
// ============================================================================

const props = defineProps<{
  conditions: Array<{ keyword: string; level: string }>
  actions: Array<{ keyword: string; action: string; value: string }>
  keywords: RuleKeyword[]
}>()

defineEmits<{
  (e: 'node-click', payload: { type: 'condition' | 'action'; index: number }): void
}>()

// ============================================================================
// 节点元数据（颜色 + 图标 + 类型判断）
// ============================================================================

/** 根据 keyword_name 在 keywords 中查 category */
function categoryOf(keywordName: string): string {
  return props.keywords.find(k => k.keyword_name === keywordName)?.category || 'parameter'
}

/** 节点样式类（决定左边框颜色） */
function nodeClass(item: any, type: 'condition' | 'action'): string {
  const cat = categoryOf(item.keyword)
  if (type === 'action') return 'node-action'
  if (cat === 'defect') return 'node-defect'
  if (cat === 'defect_position') return 'node-defect-position'
  return 'node-parameter'
}

/** 条件节点图标 */
function iconForCondition(cond: { keyword: string }): string {
  const cat = categoryOf(cond.keyword)
  if (cat === 'defect') return 'mdi:alert-circle'
  if (cat === 'defect_position') return 'mdi:map-marker-alert'
  return 'mdi:tune-vertical'
}

/** 动作节点图标 */
function iconForAction(_act: { keyword: string }): string {
  return 'mdi:tools'
}

/** keyword_name → keyword_alias */
function aliasOf(keywordName: string): string {
  return props.keywords.find(k => k.keyword_name === keywordName)?.keyword_alias || ''
}

/** action 映射中文 */
function actionLabel(action: string): string {
  const map: Record<string, string> = {
    add: '增加', reduce: '减小', adjust: '弹窗', set: '设定',
  }
  return map[action] || action
}

// ============================================================================
// 连线计算
// ============================================================================

interface EdgePath {
  d: string
}

/**
 * 连线列表（分两段：输入线 + 输出线）
 * - inputEdges：条件 → AND 节点（蓝色、无箭头，输入汇聚）
 * - outputEdges：AND 节点 → 动作（绿色、有箭头，输出发散）
 */
const inputEdges = ref<EdgePath[]>([])
const outputEdges = ref<EdgePath[]>([])

const rootRef = ref<HTMLElement | null>(null)
const cardRef = ref<any>(null)
/** 中间 AND 聚合节点 ref */
const ruleCoreNode = ref<HTMLElement | null>(null)
const conditionRefs = ref<HTMLElement[]>([])
const actionRefs = ref<HTMLElement[]>([])

/**
 * SVG 容器的尺寸（动态跟随 rootRef）
 * - 用于 SVG width/height 属性
 * - 避免 SVG 坐标系与 path 坐标不一致
 */
const svgSize = ref<{ width: number; height: number }>({ width: 0, height: 0 })

/**
 * 容器实际宽度（动态测量）
 *
 * 与 ResizeObserver 联动，依据宽度切换：
 *   - ≥ 480px：layout-wide（条件列 : 动作列 = 2 : 1）
 *   - 360~480px：layout-compact（条件列 : 动作列 = 1 : 1）
 *   - < 360px：layout-stacked（上下布局）
 */
const containerWidth = ref(0)

const layoutClass = computed(() => {
  const w = containerWidth.value
  if (w === 0) return ''
  if (w >= 480) return 'layout-wide'
  if (w >= 360) return 'layout-compact'
  return 'layout-stacked'
})

function setConditionRef(el: any, i: number) {
  if (el) conditionRefs.value[i] = el as HTMLElement
  else if (i in conditionRefs.value) conditionRefs.value[i] = null as any
}
function setActionRef(el: any, i: number) {
  if (el) actionRefs.value[i] = el as HTMLElement
  else if (i in actionRefs.value) actionRefs.value[i] = null as any
}

/**
 * 计算连线坐标（两段：输入 + 输出）
 *
 * 布局自适应：
 *   - 大屏（flex-direction: row）：连线从条件节点右边 → AND 节点左边（水平贝塞尔）
 *                              AND 节点右边 → 动作节点左边（水平贝塞尔）
 *   - 小屏（flex-direction: column）：连线从条件节点底边 → AND 节点顶边（垂直贝塞尔）
 *                              AND 节点底边 → 动作节点顶边（垂直贝塞尔）
 */
function computeEdges(): { input: EdgePath[]; output: EdgePath[] } {
  const rootEl = rootRef.value
  if (!rootEl) return { input: [], output: [] }
  const rootRect = rootEl.getBoundingClientRect()
  const rootStyle = window.getComputedStyle(rootEl)
  const isVertical = rootStyle.flexDirection.startsWith('column')
  const input: EdgePath[] = []
  const output: EdgePath[] = []

  const coreEl = ruleCoreNode.value
  if (!coreEl) return { input, output }
  const coreRect = coreEl.getBoundingClientRect()

  // 过滤掉 null ref（v-for 数组缩短时的中间状态）
  const conds = conditionRefs.value.filter(Boolean) as HTMLElement[]
  const acts = actionRefs.value.filter(Boolean) as HTMLElement[]

  // path 起止点偏移：避免「贴脸」在节点边缘
  // - input 起点（从条件节点右边）：往外偏移 6px
  // - input 终点（到 AND 节点左边）：往内偏移 8px（避免穿插 AND 节点）
  // - output 起点（从 AND 节点右边）：往外偏移 6px
  // - output 终点（到动作节点左边）：往内偏移 12px（为箭头预留空间）
  const INPUT_GAP_OUT = 6
  const INPUT_GAP_IN = 8
  const OUTPUT_GAP_OUT = 6
  const OUTPUT_GAP_IN = 12

  if (isVertical) {
    // 上下布局：所有点用中线
    const coreCx = coreRect.left + coreRect.width / 2 - rootRect.left
    const coreTopY = coreRect.top - rootRect.top
    const coreBotY = coreRect.bottom - rootRect.top

    // 1) 条件底边中点 → AND 节点顶边中点（输入汇聚）
    for (const condEl of conds) {
      const condRect = condEl.getBoundingClientRect()
      const startX = condRect.left + condRect.width / 2 - rootRect.left
      const startY = condRect.bottom - rootRect.top + INPUT_GAP_OUT
      const endX = coreCx
      const endY = coreTopY - INPUT_GAP_IN
      const midY = (startY + endY) / 2
      input.push({
        d: `M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`,
      })
    }

    // 2) AND 节点底边中点 → 动作顶边中点（输出发散）
    for (const actEl of acts) {
      const actRect = actEl.getBoundingClientRect()
      const startX = coreCx
      const startY = coreBotY + OUTPUT_GAP_OUT
      const endX = actRect.left + actRect.width / 2 - rootRect.left
      const endY = actRect.top - rootRect.top - OUTPUT_GAP_IN
      const midY = (startY + endY) / 2
      output.push({
        d: `M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`,
      })
    }
  } else {
    // 左右布局：所有点用中线
    const coreCy = coreRect.top + coreRect.height / 2 - rootRect.top
    const coreLeftX = coreRect.left - rootRect.left
    const coreRightX = coreRect.right - rootRect.left

    // 1) 条件右边中点 → AND 节点左边中点（输入汇聚）
    for (const condEl of conds) {
      const condRect = condEl.getBoundingClientRect()
      const startX = condRect.right - rootRect.left + INPUT_GAP_OUT
      const startY = condRect.top + condRect.height / 2 - rootRect.top
      const endX = coreLeftX - INPUT_GAP_IN
      const endY = coreCy
      const midX = (startX + endX) / 2
      input.push({
        d: `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`,
      })
    }

    // 2) AND 节点右边中点 → 动作左边中点（输出发散）
    for (const actEl of acts) {
      const actRect = actEl.getBoundingClientRect()
      const startX = coreRightX + OUTPUT_GAP_OUT
      const startY = coreCy
      const endX = actRect.left - rootRect.left - OUTPUT_GAP_IN
      const endY = actRect.top + actRect.height / 2 - rootRect.top
      const midX = (startX + endX) / 2
      output.push({
        d: `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`,
      })
    }
  }
  return { input, output }
}

// ============================================================================
// 响应式：条件/动作变化 → 重算连线
// ============================================================================

let resizeObserver: ResizeObserver | null = null

/** 手动重算连线 + 更新 svgSize (nextTick 后调用) */
function recomputeEdges() {
  if (!rootRef.value || !ruleCoreNode.value) {
    inputEdges.value = []
    outputEdges.value = []
    svgSize.value = { width: 0, height: 0 }
    return
  }
  if (conditionRefs.value.filter(Boolean).length === 0 || actionRefs.value.filter(Boolean).length === 0) {
    inputEdges.value = []
    outputEdges.value = []
    return
  }

  // 同步更新 SVG 尺寸
  const rootRect = rootRef.value.getBoundingClientRect()
  svgSize.value = { width: rootRect.width, height: rootRect.height }

  const result = computeEdges()
  inputEdges.value = result.input
  outputEdges.value = result.output
}

onMounted(async () => {
  await nextTick()
  recomputeEdges()

  // 监听 el-card 实际宽度
  const cardEl = cardRef.value?.$el ?? cardRef.value
  if (cardEl && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      recomputeEdges()
    })
    resizeObserver.observe(cardEl)
  }

  // 初次后用 requestAnimationFrame 再算一次（保险）
  requestAnimationFrame(() => recomputeEdges())
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

// 监听 conditions / actions 数量变化
watchRef(
  () => [props.conditions.length, props.actions.length],
  async () => {
    await nextTick()
    recomputeEdges()
  },
)

// 监听节点内容变化
watchRef(
  () => [
    ...props.conditions.map(c => `${c.keyword}|${c.level}`),
    ...props.actions.map(a => `${a.keyword}|${a.action}|${a.value}`),
  ],
  async () => {
    await nextTick()
    recomputeEdges()
  },
)
</script>

<style lang="scss" scoped>
.rule-graph-card {
  :deep(.el-card__header) {
    padding: 12px 16px;
    font-weight: 600;
  }
}

.empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #fafbfc 100%);
  border-radius: 8px;
  min-height: 200px;

  .empty-tip {
    margin-top: 12px;
    color: #909399;
    font-size: 13px;
    text-align: center;
  }
}

.rule-graph {
  position: relative;
  display: flex;
  gap: 48px;                    /* 增大间距，给线和箭头过渡空间 */
  align-items: center;          /* 垂直居中 */
  justify-content: center;      /* 整体水平居中 */
  padding: 32px 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #fafbfc 100%);
  border-radius: 8px;
  min-height: 260px;
}

/*
 * 节点列默认 flex: 1（条件列、动作列等宽，与 AND 节点对称）
 */
.node-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 1;
}

/*
 * AND 聚合节点中间列：完全居中（垂直 + 水平）
 */
.rule-core-wrapper {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  z-index: 2;
}

/*
 * AND 聚合节点本身
 * - 胶囊（border-radius 50%）确保不管内容多少都保持正圆对称
 * - 蓝绿渐变背景表达「输入→输出」语义
 * - 中间圆形 icon + 文字表达「规则聚合」
 * - 阴影增加立体感
 */
.rule-core {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 96px;
  height: 96px;
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  border-radius: 50%;
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.3);
  color: #fff;
  user-select: none;
  flex-shrink: 0;
}

.rule-core-circle {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
}

.rule-core-text {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1.5px;
  line-height: 1;
}

.rule-core-sub {
  font-size: 9px;
  letter-spacing: 2px;
  opacity: 0.85;
  line-height: 1;
}

.column-label {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

/* ============ 响应式布局（三列等宽 · 紧凑 gap）============ */
.rule-graph-card.layout-wide .node-column--conditions { flex: 1; }
.rule-graph-card.layout-wide .node-column--actions    { flex: 1; }

.rule-graph-card.layout-compact .node-column--conditions { flex: 1; }
.rule-graph-card.layout-compact .node-column--actions    { flex: 1; }

.rule-graph-card.layout-stacked .rule-graph {
  flex-direction: column;
  gap: 32px;          /* 上下布局给垂直连线留空间 */
}
.rule-graph-card.layout-stacked .node-column--conditions,
.rule-graph-card.layout-stacked .node-column--actions {
  flex: 1 1 auto;
}

/* ============ 节点卡片 ============ */
.graph-node {
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  border-left: 4px solid;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
  }

  &.node-defect {
    border-left-color: #e6a23c;
    :deep(.el-icon) { color: #e6a23c; }
  }

  &.node-defect-position {
    border-left-color: #f56c6c;
    :deep(.el-icon) { color: #f56c6c; }
  }

  &.node-parameter {
    border-left-color: #409eff;
    :deep(.el-icon) { color: #409eff; }
  }

  &.node-action {
    border-left-color: #67c23a;
    :deep(.el-icon) { color: #67c23a; }
  }
}

.node-body {
  flex: 1;
  min-width: 0;
}

.node-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-meta {
  color: #909399;
  font-size: 12px;
  font-family: 'JetBrains Mono', 'Courier New', Consolas, monospace;
  margin-top: 2px;
}

/* ============ 连线层 ============ */
.graph-edges {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
</style>