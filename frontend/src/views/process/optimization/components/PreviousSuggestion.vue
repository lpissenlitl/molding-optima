<!--
  PreviousSuggestion - 上一轮调整建议（多模态卡片）

  职责：展示上一轮算法/工艺员给出的调整建议，供本轮试模参考
  数据：suggestion（来自上一轮 infer 响应，可能为 null）
  位置：OptimizationCreate 中独立的 round-detail-block，位于"工艺参数"和
       "缺陷反馈"之间（不在 DefectFeedback 内部）

  设计约束：
  - 不带 title / header（由父级 round-detail-block__title 提供"上一轮调整建议"）
  - 类层级 ≤ 2：.previous-suggestion > .previous-suggestion__group / __item
  - 浅色背景 + 左侧强调条（与 SettingProcess 风格呼应，但不引入新 CSS 类深度）
  - 多模态内容：按 group 分类，每组可包含任意条建议
  - 空状态：suggestion=null 或 groups 为空时显示占位文本
-->
<template>
  <div class="previous-suggestion">
    <!-- 空状态：上一轮暂无调整建议（首轮 / 算法未返回） -->
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
          >
            <AppIcon
              v-if="item.direction"
              :icon="directionIcon(item.direction)"
              :class="['previous-suggestion__direction', `previous-suggestion__direction--${item.direction}`]"
            />
            <span class="previous-suggestion__description">{{ item.description }}</span>
            <span
              v-if="item.rule_refs && item.rule_refs.length"
              class="previous-suggestion__rules"
            >
              依据规则: {{ item.rule_refs.map(formatRuleRef).join(' · ') }}
            </span>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * PreviousSuggestion - 上一轮调整建议
 *
 * Props：suggestion（来自上一轮的 infer 响应）
 *
 * 注意：此组件只负责展示，不修改父级数据
 */
import type { Suggestion, SuggestionDirection } from '@/types/optimization'

defineProps<{
  suggestion?: Suggestion | null
}>()

/** 是否展示内容（不是空对象） */
function hasContent(sug: Suggestion | null | undefined): boolean {
  if (!sug || !sug.groups || sug.groups.length === 0) return false
  // 至少有一个 group 至少有一个 item
  return sug.groups.some(g => g.items && g.items.length > 0)
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

/** 规则引用格式化（'M001' → 'M001'；后续可加链接） */
function formatRuleRef(ref: string): string {
  return ref
}
</script>

<style lang="scss" scoped>
/*
 * 浅色背景 + 左侧 3px 强调条（温和警示感，与"调整建议"语义匹配）
 * 不带 title（由父级 round-detail-block__title 提供）
 * 类层级 ≤ 2：.previous-suggestion > .previous-suggestion__group / __item / __category
 */
.previous-suggestion {
  padding: 10px 14px;
  background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  border-left: 3px solid #e6a23c;
  border-radius: 4px;

  /* 空状态（首轮 / 算法未返回） */
  &__empty {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #909399;
  }

  /* 每个 group 之间留白 */
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
    gap: 6px;
    align-items: baseline;
    padding: 2px 0;
    font-size: 13px;
    color: #303133;
  }

  /* 调整方向图标（↑↓→等）*/
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

  /* 规则引用（依据规则: M001 · M003） */
  &__rules {
    font-size: 11px;
    color: #909399;
    margin-left: 4px;
    flex-shrink: 0;
  }
}
</style>