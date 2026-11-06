<!-- TuningHistoryDrawer - 调机历史抽屉：左侧轮次列表 + 右侧全量只读详情 -->
<template>
  <el-drawer
    :model-value="visible"
    :title="title"
    size="88%"
    direction="rtl"
    :close-on-click-modal="false"
    @update:model-value="handleVisibleChange"
  >
    <div v-loading="loading" class="history-drawer">
      <el-empty
        v-if="!loading && ordered_items.length === 0"
        description="该工艺条件下暂无调机记录"
      />

      <div v-else class="history-drawer__body">
        <!-- 左：轮次列表（后端按 created_at 倒序返回，这里按 seq_idx 正序，第 1 轮在前） -->
        <aside class="history-drawer__rounds">
          <div class="history-drawer__rounds-header">
            <span class="history-drawer__rounds-title">调机轮次</span>
            <el-tag size="small" type="info">{{ ordered_items.length }} 轮</el-tag>
          </div>
          <el-scrollbar class="history-drawer__rounds-scroll">
            <ul class="round-list">
              <li
                v-for="(item, idx) in ordered_items"
                :key="item.id ?? idx"
                class="round-item"
                :class="{ 'is-active': item.id === active_id }"
                @click="select_round(item)"
              >
                <div class="round-item__title">
                  第 {{ item.seq_idx ?? idx + 1 }} 轮
                  <el-tag size="small" type="info">{{ sourceLabel(item.param_source) }}</el-tag>
                </div>
                <div class="round-item__meta">
                  <el-tag size="small" :type="resultTagType(item.tuning?.tuning_result)">
                    {{ resultLabel(item.tuning?.tuning_result) }}
                  </el-tag>
                  <el-tag v-if="item.sealed" size="small" type="info" effect="plain">
                    <AppIcon icon="mdi:lock-outline" style="margin-right: 2px;" />
                    已归档
                  </el-tag>
                  <span class="round-item__time">{{ formatDate(item.created_at) }}</span>
                </div>
              </li>
            </ul>
          </el-scrollbar>
        </aside>

        <main class="history-drawer__detail">
          <el-empty
            v-if="!current_item"
            description="请选择左侧轮次查看详情"
            :image-size="60"
          />

          <template v-else>
            <el-descriptions class="round-meta" :column="4" border size="small">
              <el-descriptions-item label="轮次">
                第 {{ current_item.seq_idx ?? '-' }} 轮
              </el-descriptions-item>
              <!-- 工艺编号：有值才展示。数据库主键（parameter_id）不面向用户展示 ——
                   它只是内部标识，对调机追溯无意义。 -->
              <el-descriptions-item v-if="current_item.parameter_no" label="工艺编号">
                {{ current_item.parameter_no }}
              </el-descriptions-item>
              <el-descriptions-item label="参数来源">
                {{ sourceLabel(current_item.param_source) }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(current_item.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="归档状态" :span="4">
                <el-tag size="small" :type="current_item.sealed ? 'info' : 'warning'">
                  {{ sealedLabel(current_item.sealed) }}
                </el-tag>
                <span class="round-meta__hint">
                  {{
                    current_item.sealed
                      ? '该轮参数是当时实际使用的工艺，属历史事实，不可修改；如需调整请在智能调机页「以此轮为基线开新轮」'
                      : '该轮尚未落库试模评价，参数仍可调整'
                  }}
                </span>
              </el-descriptions-item>
            </el-descriptions>

            <section class="detail-block">
              <div class="detail-block__title">
                <AppIcon icon="mdi:alert-circle-outline" />
                试模反馈
              </div>
              <div class="feedback">
                <div class="feedback__row">
                  <span class="feedback__label">效果评价</span>
                  <el-tag size="small" :type="resultTagType(current_item.tuning?.tuning_result)">
                    {{ resultLabel(current_item.tuning?.tuning_result) }}
                  </el-tag>
                </div>
                <div v-if="current_item.tuning?.defect_feedbacks?.length" class="feedback__row">
                  <span class="feedback__label">缺陷</span>
                  <div class="feedback__defects">
                    <el-tag
                      v-for="(d, di) in current_item.tuning.defect_feedbacks"
                      :key="di"
                      size="small"
                      type="danger"
                      effect="plain"
                    >
                      {{ d?.keyword_name ?? '未知缺陷' }}{{ d?.level ? ` / ${d.level}` : '' }}{{ d?.position ? ` / ${d.position}` : '' }}
                    </el-tag>
                  </div>
                </div>
                <div v-if="current_item.tuning?.result_detail" class="feedback__row">
                  <span class="feedback__label">结果详情</span>
                  <span class="feedback__detail">{{ current_item.tuning.result_detail }}</span>
                </div>
                <div v-if="!current_item.tuning?.tuning_result" class="feedback__row">
                  <span class="feedback__label">试模反馈</span>
                  <span class="feedback__detail">该轮尚未记录试模结果</span>
                </div>
              </div>
            </section>

            <section class="detail-block">
              <div class="detail-block__title">
                <AppIcon icon="mdi:lightbulb-on-outline" />
                调整建议
              </div>
              <PreviousSuggestion :suggestion="current_suggestion" />
            </section>

            <section v-if="current_parameter" class="detail-block">
              <div class="detail-block__title">
                <AppIcon icon="mdi:cog-outline" />
                工艺参数
                <el-tag size="small" type="info">只读</el-tag>
              </div>
              <!-- original-process 传同一对象：历史数据无「变更」概念，避免整表误高亮 -->
              <TuningParameterPanel
                :setting-process="current_parameter"
                :original-process="current_parameter"
                readonly
              />
            </section>
          </template>
        </main>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { TuningRoundItem } from '@/api/index'
import type { Suggestion } from '@/types/optimization'
import TuningParameterPanel from './TuningParameterPanel.vue'
import PreviousSuggestion from './PreviousSuggestion.vue'
import { parameterFromFlat } from './parameterTransform'
import { sourceLabel, resultLabel, resultTagType, sealedLabel } from './tuning-status'

const props = defineProps<{
  /** 抽屉显隐（父组件 v-model:visible 绑定） */
  visible: boolean
  /** 抽屉标题（一般是工艺编号） */
  title?: string
  loading?: boolean
  /** 调机历史（一个 parameter = 一轮调机） */
  items: TuningRoundItem[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const active_id = ref<number | null>(null)

/** 轮次按 seq_idx 正序（第 1 轮在前），与智能调机页时间线的读法一致 */
const ordered_items = computed<TuningRoundItem[]>(() =>
  [...props.items].sort((a, b) => (a.seq_idx ?? 0) - (b.seq_idx ?? 0)),
)

const current_item = computed<TuningRoundItem | null>(
  () => ordered_items.value.find((i) => i.id === active_id.value) ?? null,
)

/** 当前轮的完整工艺参数（flat → 嵌套；模板翻译全站唯一实现在 parameterTransform） */
const current_parameter = computed(() => {
  const item = current_item.value
  if (!item) return null
  return parameterFromFlat(item as any)
})

/** 当前轮自身的算法建议（Recommendation 锚在该轮参数上） */
const current_suggestion = computed<Suggestion | null>(() => {
  const item = current_item.value
  const sug = item?.tuning?.suggestion
  if (!item || !sug || !Array.isArray(sug.groups)) return null
  return {
    source_round_id: item.id,
    adopted: sug.adopted ?? null,
    groups: sug.groups,
  }
})

// 数据到位后默认停在最新一轮；已选轮次若从列表消失则重选
watch(
  () => props.items,
  (items) => {
    const ordered = [...items].sort((a, b) => (a.seq_idx ?? 0) - (b.seq_idx ?? 0))
    if (ordered.length === 0) {
      active_id.value = null
      return
    }
    if (active_id.value == null || !ordered.some((i) => i.id === active_id.value)) {
      active_id.value = ordered[ordered.length - 1].id
    }
  },
  { immediate: true },
)

function select_round(item: TuningRoundItem) {
  active_id.value = item.id
}

function handleVisibleChange(value: boolean) {
  emit('update:visible', value)
}

/** ISO 时间 → 本地化时间 */
function formatDate(s?: string | null): string {
  if (!s) return '-'
  try {
    const d = new Date(s)
    if (isNaN(d.getTime())) return s
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} `
      + `${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return s
  }
}
</script>

<style lang="scss" scoped>
.history-drawer {
  &__body {
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
    gap: 16px;
    align-items: start;
  }

  /* 左侧轮次列表：粘性定位，列表自身滚动，右侧详情随页面滚动 */
  &__rounds {
    position: sticky;
    top: 0;
    max-height: calc(100vh - 170px);
    display: flex;
    flex-direction: column;
    border: 1px solid var(--color-border-extra-light, #ebeef5);
    border-radius: 4px;
    background: #fff;
    overflow: hidden;
  }

  &__rounds-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-bottom: 1px solid var(--color-border-extra-light, #ebeef5);
  }

  &__rounds-title {
    font-weight: 600;
    font-size: 14px;
  }

  &__rounds-scroll {
    flex: 1;
    min-height: 0;
  }

  &__detail {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.round-list {
  list-style: none;
  margin: 0;
  padding: 8px 0;
}

.round-item {
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

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
    font-size: 13px;
  }

  &__meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
  }

  &__time {
    font-size: 12px;
    color: var(--el-text-color-secondary, #909399);
  }
}

.round-meta {
  &__hint {
    margin-left: 8px;
    font-size: 12px;
    color: var(--el-text-color-secondary, #909399);
  }
}

.detail-block {
  background: #fff;
  border: 1px solid var(--color-border-extra-light, #ebeef5);
  border-radius: 4px;
  padding: 12px 16px 16px;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: var(--color-bg-overlay, #f5f7fa);
    border-bottom: 1px solid var(--color-border-extra-light, #ebeef5);
    font-weight: 600;
    font-size: 14px;
    margin: -12px -16px 12px;
  }
}

.feedback {
  display: flex;
  flex-direction: column;
  gap: 8px;

  &__row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }

  &__label {
    width: 72px;
    flex-shrink: 0;
    font-size: 13px;
    color: var(--el-text-color-secondary, #909399);
  }

  &__defects {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  &__detail {
    font-size: 13px;
    color: var(--el-text-color-regular, #606266);
    white-space: pre-wrap;
  }
}
</style>
