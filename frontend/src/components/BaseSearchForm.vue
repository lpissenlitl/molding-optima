<!--
  BaseSearchForm - 通用搜索表单（Element Plus 适配版）

  与 molding-expert 版本的设计一致：配置驱动 + 可展开收起
  - 业务组件（如 MoldSearchForm / ProjectSearchForm）只声明 search_items 配置
  - 公共组件负责渲染

  Element Plus 适配要点（vs molding-expert 的 Element UI 版本）：
  - size 映射：Element UI small ≈ Element Plus default（32px，都是中等档）
  - 业务参考 admin/user 的搜索栏（size="default"）
  - icon：用 AppIcon（mdi:*）替代 el-icon-*（Element Plus 已废弃）
  - value-format：YYYY-MM-DD（Element Plus 大写，Element UI 是 yyyy-MM-dd）
  - handleClear：直接赋值（Vue 3 reactive 自动追踪，无需 $set）
-->
<template>
  <div class="search-container">
    <el-form
      class="search-form"
      :class="{ 'uniform-mode': !!controlWidth, 'label-fixed': labelWidth !== 'auto' }"
      :style="formStyle"
      :inline="true"
      :model="query"
      :size="size"
      :label-width="labelWidth"
    >
      <!-- 筛选项（根据 level 和展开状态控制显示） -->
      <template v-for="(item, index) in visibleItems">
        <!-- 自定义插槽：直接渲染，避免嵌套 el-form-item 导致间距异常 -->
        <div v-if="item.slot_name" :key="'slot-' + index" class="slot-item-wrapper">
          <slot
            :name="item.slot_name"
            :item="item"
            :query="query"
          />
        </div>

        <el-form-item
          v-else
          :key="index"
          :label="item.label"
          :prop="item.prop"
          :size="size"
        >
          <!-- 自动完成输入框 -->
          <el-autocomplete
            v-if="item.type === 'autocomplete'"
            v-model.trim="query[item.prop]"
            :placeholder="item.placeholder || `输入${item.label}`"
            :size="size"
            clearable
            @clear="handleClear(item.prop)"
            :debounce="0"
            :fetch-suggestions="getSuggestions(item.query)"
          />

          <!-- 下拉选择框 -->
          <el-select
            v-else-if="item.type === 'select'"
            v-model="query[item.prop]"
            :placeholder="item.placeholder || '全部'"
            :size="size"
            clearable
            @clear="handleClear(item.prop)"
          >
            <el-option
              v-for="option in item.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>

          <!-- 普通输入框 -->
          <el-input
            v-else-if="item.type === 'input'"
            v-model.trim="query[item.prop]"
            :placeholder="item.placeholder || `输入${item.label}`"
            :size="size"
            clearable
            @clear="handleClear(item.prop)"
          />

          <!-- 日期选择器 -->
          <el-date-picker
            v-else-if="item.type === 'date'"
            v-model="query[item.prop]"
            type="date"
            :placeholder="item.placeholder || '选择日期'"
            :size="size"
            value-format="YYYY-MM-DD"
            clearable
            @clear="handleClear(item.prop)"
          />
        </el-form-item>
      </template>

      <!-- 操作按钮 -->
      <el-form-item class="search-actions" :size="size">
        <el-button
          type="primary"
          :size="size"
          @click="handleSearch"
        >
          <AppIcon icon="mdi:magnify" :size="14" style="margin-right: 4px;" />
          搜索
        </el-button>
        <el-button
          :size="size"
          @click="handleReset"
        >
          <AppIcon icon="mdi:refresh" :size="14" style="margin-right: 4px;" />
          重置
        </el-button>

        <!-- 展开/收起按钮（仅在有高级项时显示） -->
        <el-button
          v-if="hasAdvancedItems"
          text
          :size="size"
          @click="toggleExpand"
        >
          <AppIcon
            :icon="is_expanded ? 'mdi:chevron-up' : 'mdi:chevron-down'"
            :size="14"
            style="margin-right: 2px;"
          />
          {{ is_expanded ? '收起' : '展开' }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { querySuggestions as buildQuerySuggestions } from '@/utils/form-helper'
import type { SearchItem } from '@/types/search-item'

const props = withDefaults(
  defineProps<{
    /**
     * 查询对象（双向绑定）
     * BaseSearchForm 内部直接修改此对象（依赖 Vue 3 reactive 自动追踪）
     */
    query: Record<string, any>

    /**
     * 筛选项配置数组
     */
    items?: SearchItem[]

    /**
     * 是否支持展开/收起功能
     */
    expandable?: boolean

    /**
     * 尺寸（Element Plus：large / default / small）
     */
    size?: string

    /**
     * 控件宽度策略
     * - 不传：A 紧凑型（input 160px / select 120px）
     * - 传数字（如 200）：B 整齐型
     * - 传字符串：自定义单位
     */
    controlWidth?: number | string | null

    /**
     * label 宽度
     * - 'auto'（默认）：label 宽度自适应
     * - 传具体值（如 '6rem' / '80px'）：label 等宽 + 右对齐
     */
    labelWidth?: string
  }>(),
  {
    items: () => [],
    expandable: false,
    size: 'default',
    controlWidth: null,
    labelWidth: 'auto'
  }
)

const emit = defineEmits<{
  (e: 'search', query: Record<string, any>): void
  (e: 'reset', query: Record<string, any>): void
  (e: 'expand-change', expanded: boolean): void
}>()

// data
const is_expanded = ref(false)
// setup() 在 created 之前执行，直接在顶层快照初始值即可
const default_query = ref<Record<string, any>>(JSON.parse(JSON.stringify(props.query)))

// computed
const formStyle = computed(() => {
  if (!props.controlWidth) return null
  const w = typeof props.controlWidth === 'number' ? `${props.controlWidth}px` : props.controlWidth
  return { '--uniform-width': w } as Record<string, string>
})

const hasAdvancedItems = computed(() => {
  if (!props.expandable) return false
  return props.items.some(item => item.level === 'advanced')
})

const visibleItems = computed(() => {
  if (!props.expandable) return props.items
  return props.items.filter(item => item.level !== 'advanced' || is_expanded.value)
})

// methods
function handleClear(prop: string): void {
  props.query[prop] = null
}

function toggleExpand(): void {
  is_expanded.value = !is_expanded.value
  emit('expand-change', is_expanded.value)
}

/**
 * 获取自动补全建议函数
 * 支持级联筛选：配置 filter_ref 时，从 query 动态读取关联字段的当前值
 */
function getSuggestions(item_query: SearchItem['query']) {
  if (!item_query) return () => {}
  if (!item_query.filter_ref) {
    return buildQuerySuggestions(item_query)
  }

  // 有级联配置：每次触发时动态解析关联字段的当前值
  return (input: string, cb: (suggestions: any[]) => void) => {
    const params: Record<string, any> = { ...item_query }
    const filter_ref = item_query.filter_ref
    const source = filter_ref ? props.query[filter_ref] : undefined
    if (item_query.filter_columns) {
      params.filter_columns = Object.fromEntries(
        Object.entries(item_query.filter_columns).map(
          ([key, ref_prop]) => [key, source?.[ref_prop] ?? null]
        )
      )
    }
    delete params.filter_ref
    buildQuerySuggestions(params)(input, cb)
  }
}

function handleSearch(): void {
  emit('search', props.query)
}

/**
 * 重置到初始默认值（而非全部置空）
 */
function handleReset(): void {
  Object.keys(props.query).forEach(key => {
    props.query[key] = default_query.value[key] !== undefined ? default_query.value[key] : null
  })
  emit('reset', props.query)
}
</script>

<style lang="scss" scoped>
/* ============================================================================
 * 搜索区域样式（参考 molding-expert 全局 .search-container / .search-form）
 *
 * Vue 3 + Element Plus 适配说明：
 * - :deep() 必须单层穿透，不能嵌套（嵌套不生效）
 * - el-form--inline .el-form-item 合并为一条选择器
 * - 操作按钮区不设 margin-left: auto（窄容器下会被强制换行）
 * - 接受小容器下自然换行（业务方可减少 basic 项或调窄 input）
 * ========================================================================== */
.search-container {
  padding: 12px 16px;
  margin-bottom: 0px;
  background: linear-gradient(to bottom, #fafbfc, #ffffff);
  border: 1px solid var(--color-border-extra-light, #ebeef5);
  border-radius: 4px;
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 2px 8px rgba(37, 67, 115, 0.08);
  }
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  align-items: center;
  row-gap: 12px;
  column-gap: 20px;

  // el-form-item 间距：使用 gap 统一控制（避免在 inline-flex 上覆盖 margin 不生效）
  // Element Plus 的 el-form-item 默认 margin-right: 32px，需要重置
  :deep(.el-form--inline .el-form-item) {
    margin-bottom: 0;       // 统一由 row-gap 控制
    margin-right: 0;        // 统一由 column-gap 控制
    display: inline-flex;
    align-items: center;
  }

  /* 插槽项：与同级 el-form-item 保持一致间距 */
  :deep(.slot-item-wrapper) {
    display: inline-flex;
    align-items: center;

    > .el-form-item {
      margin-bottom: 0;
    }
  }

  /* ============================================================================
   * 表单控件默认宽度（参考 molding-expert custom.scss 274-284）
   *
   * 两种布局模式：
   * - A 紧凑型（默认）：input 160 / select 120，节省横向空间
   * - B 整齐型（control-width 启用）：所有控件等宽，视觉对齐
   *
   * 通过 CSS 选择器统一控制，避免逐个加 inline style 与 Element Plus 的
   * --el-input-width / --el-select-width CSS 变量冲突。
   *
   * 业务方如需自定义某个字段宽度，可在 el-form-item 上加 inline style 覆盖。
   * ========================================================================== */

  /* A 紧凑型：默认（区分 input/select 宽度） */
  :deep(.el-form-item .el-input),
  :deep(.el-form-item .el-autocomplete),
  :deep(.el-form-item .el-date-editor) {
    width: 160px;
  }

  :deep(.el-form-item .el-select) {
    width: 120px;
  }

  /* B 整齐型：所有控件等宽（由 --uniform-width 变量控制） */
  &.uniform-mode {
    :deep(.el-form-item .el-input),
    :deep(.el-form-item .el-select),
    :deep(.el-form-item .el-autocomplete),
    :deep(.el-form-item .el-date-editor) {
      width: var(--uniform-width, 160px);
    }
  }

  /* B 模式增强：label 等宽 + 右对齐（视觉更整齐） */
  &.label-fixed {
    :deep(.el-form-item .el-form-item__label) {
      justify-content: flex-end;
    }
  }
}

/* 操作按钮区：与 form-item 同样的 flex 行为，不强制推到右侧
 * - 不设 margin-left: auto（避免窄容器下被挤到下一行）
 * - 不设 border-left（避免换行后出现奇怪的分割线）
 * - 视觉上跟随最后一个筛选项，自然 wrap */
:deep(.search-actions) {
  display: inline-flex;
  gap: 8px;
  align-items: center;

  .el-button {
    min-width: 5.5rem;
    font-weight: 500;
  }
}
</style>
