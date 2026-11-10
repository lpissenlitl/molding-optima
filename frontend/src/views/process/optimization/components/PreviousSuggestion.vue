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
      <div
        v-for="(group, gi) in suggestion!.groups"
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
            :class="{ 'previous-suggestion__item--with-icon': !!item.direction }"
          >
            <AppIcon
              v-if="item.direction"
              :icon="directionIcon(item.direction)"
              :class="['previous-suggestion__direction', `previous-suggestion__direction--${item.direction}`]"
            />
            <span class="previous-suggestion__description">{{ item.description }}</span>
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
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Suggestion, SuggestionDirection } from '@/types/optimization'

const props = defineProps<{
  suggestion?: Suggestion | null
}>()

/** 是否有内容可展示（用 computed 而非 function：模板中 v-if 取函数引用恒为 false，会跳过空状态分支） */
const hasContent = computed(() => {
  const sug = props.suggestion
  if (!sug || !sug.groups || sug.groups.length === 0) return false
  return sug.groups.some(g => g.items && g.items.length > 0)
})

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