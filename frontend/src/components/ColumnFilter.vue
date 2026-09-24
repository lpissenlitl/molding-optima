<template>
  <div class="column-header">
    <span>{{ label }}</span>
    <div class="filter-area">
      <el-popover
        v-model="visible"
        placement="bottom-end"
        trigger="click"
        :width="260"
        popper-class="column-filter-popover"
      >
        <div class="filter-content">
          <!-- 标题和清空按钮 -->
          <div class="filter-header">
            <span>{{ title || `筛选${label}` }}</span>
            <el-button type="text"
              size="small"
              @click="handleClear"
              :disabled="includeList.length === 0 && excludeList.length === 0"
            >
              清空
            </el-button>
          </div>

          <!-- 搜索框（选项过多时显示） -->
          <el-input
            v-if="showSearch && all_values.length > 6"
            v-model="search_keyword"
            placeholder="搜索..."
            size="small"
            clearable
            class="filter-search"
          >
            <template #prefix>
              <AppIcon icon="mdi:magnify" />
            </template>
          </el-input>

          <!-- 全选/反选 -->
          <div v-if="all_values.length > 2" class="filter-actions">
            <el-button type="text" size="small" @click="handleSelectAll">
              全选
            </el-button>
            <el-button type="text" size="small" @click="handleInvert">
              反选
            </el-button>
          </div>

          <!-- 复选框列表：勾选 = 包含 -->
          <el-checkbox-group
            v-model="checked_values"
            @change="handleChange"
            class="filter-checkbox-group"
          >
            <el-checkbox
              v-for="value in filteredValues"
              :key="value"
              :label="value"
            >
              {{ formatLabel ? formatLabel(value) : value }}
            </el-checkbox>
          </el-checkbox-group>

          <!-- 空状态提示（避免数据为空时中间一大块空白） -->
          <div v-if="filteredValues.length === 0" class="filter-empty">
            <AppIcon icon="mdi:alert-outline" />
            <span>暂无可筛选项</span>
          </div>

          <!-- 底部按钮 -->
          <div class="filter-footer">
            <el-button size="small" @click="handleCancel">
              取消
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="handleConfirm"
            >
              确定
            </el-button>
          </div>
        </div>

        <!-- 筛选图标：Excel 风格（漏斗 + 下拉三角） -->
        <!-- 注意：触发器用 #reference slot 写法，避免 el-popover 的 ElOnlyChild 检查报多根节点警告 -->
        <template #reference>
          <div
            class="filter-trigger"
            :class="{ active: hasActive }"
            :style="iconStyle"
            role="button"
            aria-label="筛选"
          >
            <svg
              viewBox="0 0 16 16"
              width="16"
              height="16"
              :class="iconClass"
              aria-hidden="true"
            >
              <!-- 漏斗主体 -->
              <path
                d="M1 3.5 L5.5 8 v5 l4 -2 V8 L14 3.5 Z"
                fill="currentColor"
              />
              <!-- 下拉小三角 -->
              <path
                d="M11 11.5 L13.5 13 L11 14.5"
                stroke="currentColor"
                stroke-width="1.2"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
        </template>
      </el-popover>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

/**
 * ColumnFilter 列筛选组件
 *
 * 设计要点：
 *   - BaseTable 通过 enableColumnFilter 接入，对 filterable: true 的列自动渲染
 *   - 支持 include（正向筛选）模式；exclude 字段保留向后兼容但当前 UI 未启用排除项
 *   - SVG 漏斗图标 + active 高亮（借鉴 molding-expert-web ColumnFilter 设计）
 *   - 通过 value_map 保留原始类型，避免 bool/number 被字符串化导致后端匹配失败
 *   - 向后兼容旧 props `values`（视为 include）、`exclude: true`（视为所有 values 为排除）
 *
 * 三态选择扩展点（molding-expert-web 完整版）：
 *   - 当前 UI 只有 '' (不参与) ↔ 'in' (包含) 两态
 *   - 内部状态结构已支持三态 ('in' / 'ex' / '')，后续可加 UI 入口
 */

// props
const props = withDefaults(
  defineProps<{
    // 列标签
    label: string
    // 自定义标题
    title?: string
    // 当前包含筛选的值（向后兼容旧 props）
    values?: any[]
    // 排除筛选的值（向后兼容旧 props）
    // - Array: 直接作为 exclude 列表
    // - true: 配合 values，把所有 values 视为排除（向后兼容旧 exclude=true 语义）
    exclude?: any[] | boolean
    // 所有可选值
    all_values?: any[]
    // 是否显示搜索框
    showSearch?: boolean
    // 自定义图标类名
    iconClass?: string
    // 自定义图标样式
    iconStyle?: Record<string, any> | null
    // 格式化标签的函数
    formatLabel?: ((value: any) => string) | null
  }>(),
  {
    title: '',
    values: () => [],
    exclude: false,
    all_values: () => [],
    showSearch: true,
    iconClass: '',
    iconStyle: null,
    formatLabel: null,
  }
)

const emit = defineEmits<{
  (e: 'confirm', payload: { include: any[]; exclude: any[] }): void
  (e: 'cancel'): void
  (e: 'clear'): void
}>()

// data
const visible = ref(false)
const checked_values = ref<any[]>([])
const search_keyword = ref('')

// computed
/**
 * 从 props.values 提取 include 列表
 * 兼容 exclude=true 时把所有 values 视为排除
 */
const includeList = computed(() => {
  if (!Array.isArray(props.values)) return []
  if (props.exclude === true && props.values.length > 0) return []
  return [...props.values]
})

/**
 * 从 props.exclude 提取 exclude 列表
 */
const excludeList = computed(() => {
  if (Array.isArray(props.exclude)) return [...props.exclude]
  if (props.exclude === true && Array.isArray(props.values) && props.values.length > 0) {
    return [...props.values]
  }
  return []
})

/**
 * 是否有激活的筛选条件（用于图标高亮）
 */
const hasActive = computed(() => {
  return includeList.value.length > 0 || excludeList.value.length > 0
})

/**
 * 搜索过滤后的值列表
 */
const filteredValues = computed(() => {
  if (!search_keyword.value) return props.all_values
  const keyword = search_keyword.value.toLowerCase()
  return props.all_values.filter(value => {
    const displayValue = props.formatLabel
      ? props.formatLabel(value)
      : String(value)
    return displayValue.toLowerCase().includes(keyword)
  })
})

// watch
watch(visible, val => {
  if (val) {
    checked_values.value = [...includeList.value]
  }
})

watch(() => props.values, () => {
  if (visible.value) {
    checked_values.value = [...includeList.value]
  }
})

watch(() => props.exclude, () => {
  if (visible.value) {
    checked_values.value = [...includeList.value]
  }
})

// 初始化 checked_values 为当前 include
checked_values.value = [...includeList.value]

// methods
/**
 * 复选框变化（仅同步内部状态，不立即 emit）
 */
function handleChange() {
  // 让用户点确定才 emit，cancel 会还原
}

/**
 * 确认筛选
 * payload 形态：{ include: [v1, v2], exclude: [] }
 */
function handleConfirm() {
  visible.value = false
  emit('confirm', {
    include: [...checked_values.value],
    exclude: [...excludeList.value],
  })
}

/**
 * 取消操作（还原为 props 当前值）
 */
function handleCancel() {
  visible.value = false
  search_keyword.value = ''
  checked_values.value = [...includeList.value]
  emit('cancel')
}

/**
 * 清空筛选
 */
function handleClear() {
  checked_values.value = []
  visible.value = false
  search_keyword.value = ''
  emit('clear')
}

/**
 * 全选（仅作用于当前可见项，避免与搜索冲突）
 */
function handleSelectAll() {
  const visible = new Set(filteredValues.value)
  const kept = checked_values.value.filter(v => !visible.has(v))
  checked_values.value = [...kept, ...filteredValues.value]
}

/**
 * 反选（仅作用于当前可见项）
 */
function handleInvert() {
  const visibleSet = new Set(filteredValues.value)
  const kept = checked_values.value.filter(v => !visibleSet.has(v))
  const newlyChecked = filteredValues.value.filter(v => !checked_values.value.includes(v))
  checked_values.value = [...kept, ...newlyChecked]
}
</script>

<style scoped>
.column-header {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}
.column-header > span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: inherit;
  padding-right: 28px;
}

/* filter 区绝对定位浮在右上角，label 占满剩余空间 */
.column-header .filter-area {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
}

/* Excel/飞书风格列筛选下拉：紧凑、紧凑、紧凑 */
.filter-content {
  padding: 8px;
  min-width: 220px;
  max-width: 280px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding: 0 2px 6px;
  border-bottom: 1px solid #EBEEF5;
}

.filter-header span {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.filter-search {
  margin-bottom: 6px;
}

.filter-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  padding: 0 2px;
}

.filter-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: 260px;
  overflow-y: auto;
  padding: 0 2px;
}

/* 复选框行高紧凑 + label 字体适中（覆盖 element-plus 默认） */
:deep(.el-checkbox) {
  margin-right: 0;
  margin-bottom: 0;
  height: 28px;
  display: flex;
  align-items: center;
}
:deep(.el-checkbox__label) {
  font-size: 13px;
  padding-left: 6px;
}

/* 空状态占位（避免大块空白） */
.filter-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 18px 8px;
  color: #909399;
  font-size: 12px;
}
.filter-empty i {
  color: #e6a23c;
  font-size: 13px;
}

/* Excel 风格筛选图标：默认浅灰、active 蓝色 */
.filter-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  cursor: pointer;
  color: #c0c4cc;
  border-radius: 3px;
  transition: color 0.2s, background-color 0.2s;
  vertical-align: middle;
  user-select: none;
}

.filter-trigger:hover {
  color: #409eff;
  background-color: #ecf5ff;
}

.filter-trigger.active {
  color: #409eff;
  background-color: #ecf5ff;
}

.filter-trigger svg {
  display: block;
  pointer-events: none;
}

.filter-footer {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #EBEEF5;
}
</style>