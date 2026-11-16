<!-- PreviousSuggestion - 调整建议（锚在该轮工艺参数上） -->
<template>
  <div class="previous-suggestion">
    <!-- 空状态：本轮暂无调整建议（首轮 / 算法未返回） -->
    <div v-if="!hasContent" class="previous-suggestion__empty">
      <AppIcon icon="mdi:lightbulb-on-outline" />
      <span>暂无调整建议（首轮或等待算法返回）</span>
    </div>

    <!-- 多模态内容：按 group 分类展示 -->
    <template v-else>
      <!-- 汇总行：本轮实际应用了几项 / 有几条建议没被采用 -->
      <div class="previous-suggestion__summary">
        <AppIcon
          :icon="adoptedCount > 0 ? 'mdi:check-circle-outline' : 'mdi:alert-circle-outline'"
        />
        <span>{{ summaryText }}</span>
        <span v-if="devMode" class="previous-suggestion__devtag">开发模式 · 全量</span>
      </div>

      <div
        v-for="(group, gi) in visibleGroups"
        :key="gi"
        class="previous-suggestion__group"
      >
        <div class="previous-suggestion__category">
          <AppIcon v-if="group.icon" :icon="group.icon" />
          <span>{{ group.category }}</span>
        </div>

        <ul class="previous-suggestion__items">
          <li
            v-for="(item, ii) in group.items"
            :key="ii"
            class="previous-suggestion__item"
            :class="[
              'previous-suggestion__item--with-icon',
              { 'previous-suggestion__item--muted': isNotAdopted(item) },
            ]"
          >
            <AppIcon
              v-if="item.direction"
              :icon="directionIcon(item.direction)"
              :class="['previous-suggestion__direction', `previous-suggestion__direction--${item.direction}`]"
            />
            <span class="previous-suggestion__description">{{ item.description }}</span>
            <!-- 裁决状态：已应用 / 未采用（具体原因走 title） -->
            <span
              v-if="item.decision_status"
              class="previous-suggestion__status"
              :class="`previous-suggestion__status--${item.decision_status}`"
              :title="item.decision_reason || ''"
            >{{ statusLabel(item) }}</span>
            <!-- 实际落地值与建议值不一致时才提示（一致时文案里已含目标值） -->
            <span
              v-if="appliedText(item)"
              class="previous-suggestion__applied"
            >{{ appliedText(item) }}</span>
            <!-- 依据规则：独占一行放在文案下方；规则串逐条换行，避免长串挤压文案 -->
            <span
              v-if="item.rule_refs && item.rule_refs.length"
              class="previous-suggestion__rules"
            >
              <span class="previous-suggestion__rules-label">依据规则:</span>
              <span
                v-for="(ref, ri) in item.rule_refs"
                :key="ri"
                class="previous-suggestion__rule"
              >{{ formatRuleRef(ref) }}</span>
            </span>
          </li>
        </ul>
      </div>

      <!-- 未采用建议的展开开关（默认视图；开发模式恒展开） -->
      <button
        v-if="!devMode && notAdoptedCount > 0"
        type="button"
        class="previous-suggestion__toggle"
        @click="expanded = !expanded"
      >{{ expanded ? '收起未采用的建议' : `另有 ${notAdoptedCount} 条建议本轮未采用 ›` }}</button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Suggestion, SuggestionDirection, SuggestionItem } from '@/types/optimization'

const props = defineProps<{
  suggestion?: Suggestion | null
}>()

/** 是否有内容可展示（用 computed 而非 function：模板中 v-if 取函数引用恒为 false，会跳过空状态分支） */
const hasContent = computed(() => {
  const sug = props.suggestion
  if (!sug || !sug.groups || sug.groups.length === 0) return false
  return sug.groups.some(g => g.items && g.items.length > 0)
})

/**
 * 开发模式：`?dev=1` ⇒ 全量展示建议（已采用 + 未采用），并逐条标状态。
 * 默认关闭 ⇒ 工艺员只看到本轮真正落地的调整。
 */
const devMode = ref(false)
onMounted(() => {
  devMode.value = new URLSearchParams(window.location.search).get('dev') === '1'
})

/** 默认视图下手动展开「未采用」的建议 */
const expanded = ref(false)

/** 全部建议项（跨 group 拉平，供计数用） */
const allItems = computed<SuggestionItem[]>(() =>
  (props.suggestion?.groups ?? []).flatMap(g => g.items ?? [])
)

/** 本轮被采用（已落地）的建议条数 */
const adoptedCount = computed(() =>
  allItems.value.filter(i => i.decision_status === 'adopted').length
)

/** 本轮未采用的建议条数（让位 + 暂缓） */
const notAdoptedCount = computed(() =>
  allItems.value.filter(i => !!i.decision_status && i.decision_status !== 'adopted').length
)

/** 汇总行文案：说清楚「这一轮到底动了什么」 */
const summaryText = computed(() => {
  if (adoptedCount.value > 0) {
    return notAdoptedCount.value > 0
      ? `本轮已应用 ${adoptedCount.value} 项调整（另有 ${notAdoptedCount.value} 条建议未采用）`
      : `本轮已应用 ${adoptedCount.value} 项调整`
  }
  if (notAdoptedCount.value > 0) {
    return `本轮未落地任何调整（${notAdoptedCount.value} 条建议均未采用）`
  }
  return '本轮没有调整建议'
})

/** 可见分组：开发模式全量；默认视图只留「已采用 + 无状态（旧数据）」 */
const visibleGroups = computed(() => {
  const groups = props.suggestion?.groups ?? []
  if (devMode.value) return groups
  return groups
    .map(g => ({
      ...g,
      items: (g.items ?? []).filter(item => {
        if (!item.decision_status) return true
        if (item.decision_status === 'adopted') return true
        return expanded.value
      }),
    }))
    .filter(g => g.items.length > 0)
})

/** 未采用项置灰 */
function isNotAdopted(item: SuggestionItem): boolean {
  return !!item.decision_status && item.decision_status !== 'adopted'
}

/** 状态徽标文案（具体原因走 title 提示） */
function statusLabel(item: SuggestionItem): string {
  if (item.decision_status === 'adopted') return '已应用'
  if (item.decision_status === 'deferred') return '未采用·暂缓'
  return '未采用'
}

/**
 * 实际落地值与建议值不一致时才提示。
 * 一致时 description 里已含目标值，重复展示反而噪声。
 */
function appliedText(item: SuggestionItem): string {
  if (item.decision_status !== 'adopted') return ''
  if (item.applied_value == null || item.recommended_value == null) return ''
  if (Math.abs(item.applied_value - item.recommended_value) <= 1e-9) return ''
  return `实际落地 ${formatNumber(item.applied_value)}`
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(2)))
}

/** 调整方向 → iconify 图标 */
function directionIcon(dir: SuggestionDirection): string {
  const map: Record<SuggestionDirection, string> = {
    increase: 'mdi:arrow-up',
    decrease: 'mdi:arrow-down',
    hold: 'mdi:minus',
    check: 'mdi:magnify',
  }
  return map[dir] || 'mdi:circle-small'
}

/** 规则引用格式化 */
function formatRuleRef(ref: string): string {
  return ref
}
</script>

<style lang="scss" scoped>
/* 浅色背景 + 左侧 3px 强调条（温和警示感，与“调整建议”语义匹配）
   不带 title（由父级 round-detail-block__title 提供）
   类层级 ≤ 2：.previous-suggestion > .previous-suggestion__group / __item / __category */
.previous-suggestion {
  padding: 10px 14px;
  background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  border-left: 3px solid #e6a23c;
  border-radius: 4px;

  &__empty {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #909399;
  }

  &__summary {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 6px;
    font-size: 12px;
    color: #b88230;
  }

  &__devtag {
    padding: 0 5px;
    border: 1px solid #c0c4cc;
    border-radius: 2px;
    font-size: 11px;
    color: #909399;
  }

  &__status {
    flex-shrink: 0;
    padding: 0 5px;
    border-radius: 2px;
    font-size: 11px;
    line-height: 18px;

    &--adopted {
      background: #f0f9eb;
      border: 1px solid #c2e7b0;
      color: #67c23a;
    }

    &--yielded,
    &--deferred {
      background: #f4f4f5;
      border: 1px solid #e4e7ed;
      color: #909399;
    }
  }

  &__applied {
    flex-shrink: 0;
    font-size: 11px;
    color: #67c23a;
  }

  &__item--muted {
    opacity: 0.55;
  }

  &__toggle {
    margin-top: 6px;
    padding: 0;
    background: none;
    border: none;
    font-size: 12px;
    color: #409eff;
    cursor: pointer;

    &:hover {
      text-decoration: underline;
    }
  }

  &__group {
    margin-top: 8px;
    &:first-child {
      margin-top: 0;
    }
  }

  &__category {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
    color: #b88230;
    margin-bottom: 4px;
  }

  &__items {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  &__item {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    column-gap: 6px;
    padding: 2px 0;
    font-size: 13px;
    color: #303133;
  }

  &__direction {
    flex-shrink: 0;
    font-size: 14px;
    line-height: 1;

    &--increase {
      color: #67c23a;  /* 绿：偏少→建议 */
    }
    &--decrease {
      color: #f56c6c;  /* 红：偏大→建议 */
    }
    &--hold {
      color: #909399;  /* 灰：保持 */
    }
    &--check {
      color: #409eff;  /* 蓝：检查 */
    }
  }

  &__description {
    flex: 1;
    min-width: 0;
  }

  &__rules {
    /* 独占一行：flex-basis 100% 强制换行，不再与文案抢同一行宽度 */
    flex: 0 0 100%;
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
    margin-top: 2px;
    font-size: 11px;
    color: #909399;
    line-height: 1.5;
  }

  &__rules-label {
    font-weight: 600;
  }

  &__rule {
    /* 规则串无空格断点，需允许任意位置断行 */
    overflow-wrap: anywhere;
  }

  /* 有方向图标时，依据规则行与描述文字左对齐（图标宽 14px + 列间距 6px） */
  &__item--with-icon &__rules {
    padding-left: 20px;
  }
}
</style>