<!--
  BaseTable 业务表格封装组件（Vue 3 Composition API 版）

  设计参考：molding-expert/molding-expert-web/src/components/BaseTable.vue
  适配 molding-optima 的 Vue 3 + Pinia + TypeScript 技术栈

  功能范围（精简版）：
    - el-table 动态列定义（columns 驱动）
    - 列筛选（ColumnFilter 集成，filterable: true 的列自动接入）
    - 表格密度切换（小/中/大）
    - 分页（el-pagination）
    - 用户偏好持久化（density, pageSize, columns 显隐）
    - 行双击、选择变化事件透传
    - 响应式 toolbar（可选）：窗口宽度小于断点时折叠次要按钮到下拉

  使用方式：
    BaseTable
      :data="list_data.items"
      :total="list_data.total"
      :query="query"
      :columns.sync="table_columns"
      view-name="user_list"
      :loading="list_loading"
      :responsive-toolbar="true"
      @size-change="..."
      @current-change="..."
      @row-dblclick="editUser"

    slot #toolbar       — 主按钮插槽（始终显示）
    slot #toolbar-more  — 次要按钮插槽（仅在 responsiveToolbar=true 且移动端时折叠）
    slot #cell-xxx      — 各列自定义单元格插槽
    slot #append-columns — 业务定制的尾随列（通常用于行操作列）

  响应式 toolbar：
    - :responsive-toolbar="true" 启用后，窗口宽度小于 mobileBreakpoint（默认 768）时，
      #toolbar-more 插槽会被收集到“更多”下拉中，避免按钮过多导致换行错乱。
    - 主按钮请放 #toolbar，次要按钮放 #toolbar-more。
    - 启用后才会监听 resize，桌面端场景无额外开销。

  注意：列显隐偏好持久化依赖 viewName，必须传入
-->
<template>
  <div class="base-table">
    <!-- Toolbar：左侧密度切换 + 右侧工具栏插槽 -->
    <div class="row-toolbutton">
      <div>
        <slot name="toolbar-prefix">
          <el-button-group v-if="showDensityChanger">
            <el-button
              :type="currentTableSize === 'small' ? 'primary' : ''"
              @click="currentTableSize = 'small'"
            >
              小
            </el-button>
            <el-button
              :type="currentTableSize === 'default' ? 'primary' : ''"
              @click="currentTableSize = 'default'"
            >
              中
            </el-button>
            <el-button
              :type="currentTableSize === 'large' ? 'primary' : ''"
              @click="currentTableSize = 'large'"
            >
              大
            </el-button>
          </el-button-group>
        </slot>
      </div>
      <div class="toolbar-buttons">
        <slot name="toolbar" />
        <!--
          responsiveToolbar + isMobile 启用时，把 toolbar-more 折叠成 popover。
          - 桌面端：直接展开 toolbar-more 插槽（与 toolbar 同一行）。
          - 移动端：收集到“更多”下拉中，避免按钮过多导致换行错乱。
        -->
        <slot v-if="!shouldFoldToolbar" name="toolbar-more" />
        <el-popover
          v-else-if="$slots['toolbar-more']"
          placement="bottom-end"
          :width="200"
          trigger="click"
          popper-class="toolbar-more-popover"
          :show-arrow="false"
        >
          <template #reference>
            <el-button>
              <AppIcon icon="mdi:dots-horizontal" style="margin-right: 4px; font-size: 14px;" />
              更多
            </el-button>
          </template>
          <div class="toolbar-more-list">
            <slot name="toolbar-more" />
          </div>
        </el-popover>
      </div>
    </div>

    <!-- 主表格 -->
    <el-table
      :class="[`table-size-${currentTableSize}`]"
      v-loading="loading"
      :size="currentTableSize"
      :stripe="stripe"
      :border="border"
      :fit="fit"
      :highlight-current-row="highlightCurrentRow"
      style="width: 100%;"
      :data="filteredItems"
      :height="resolvedHeight"
      @row-dblclick="onRowDblclick"
      @selection-change="(rows: any[]) => $emit('selection-change', rows)"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="showSelection"
        type="selection"
        width="50"
        align="center"
        fixed="left"
      />
      <!-- 序号列 -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="序号"
        width="60"
        align="center"
        fixed="left"
      />

      <!-- 动态列 -->
      <el-table-column
        v-for="column in visibleColumns"
        :key="column.prop"
        :prop="column.prop"
        :label="column.label"
        :width="column.width"
        :min-width="resolveMinWidth(column)"
        :header-align="column.header_align || column.align || 'center'"
        :align="column.align"
        :sortable="column.sortable"
        :show-overflow-tooltip="column.tooltip"
        :fixed="column.fixed || false"
      >
        <template #header>
          <ColumnFilter
            v-if="column.filterable && enableColumnFilter"
            :label="column.label"
            :values="resolveColumnFormatValues(column)"
            :all-values="getColumnUniqueValuesFor(column.prop)"
            :format-label="resolveColumnFormatLabel(column)"
            @confirm="(payload: any) => handleColumnFilterChange(column.prop, payload)"
            @clear="() => handleColumnFilterClear(column.prop)"
          />
          <span v-else>{{ column.label }}</span>
        </template>
        <template #default="scope">
          <slot
            :name="`cell-${column.prop}`"
            :row="scope.row"
            :column="column"
            :$index="scope.$index"
          >
            {{ formatCell(scope.row, column) }}
          </slot>
        </template>
      </el-table-column>

      <!-- 业务定制的尾随列（如行操作列） -->
      <slot name="append-columns" />
    </el-table>

    <!-- 分页 -->
    <div v-if="showPagination" class="pagination">
      <el-pagination
        :layout="paginationLayout"
        :page-sizes="resolvedPageSizes"
        :page-size="query.page_size"
        :current-page="query.page_no"
        :total="total"
        :background="showBackground"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * BaseTable 列定义类型
 *
 * 最小必填：prop + label
 * 常用可选：minWidth / width / align / sortable / tooltip / filterable / visible
 * 进阶可选：formatLabel(value) => string、map: Record<string, any>
 */
export interface BaseTableColumn {
  /** 字段名（必填） */
  prop: string
  /** 列名（必填） */
  label: string
  /** 是否可见（默认 true，false 时隐藏） */
  visible?: boolean
  /** 固定列宽（与 minWidth 互斥，el-table 原生行为：width 优先于 minWidth） */
  width?: number | string
  /** 最小列宽（推荐，自动伸展） */
  minWidth?: number | string
  /** 内容对齐 */
  align?: 'left' | 'center' | 'right'
  /** 表头对齐（默认与 align 一致） */
  header_align?: 'left' | 'center' | 'right'
  /** 是否可排序 */
  sortable?: boolean
  /** 内容溢出显示 tooltip */
  tooltip?: boolean
  /** 是否启用列筛选（点击列头漏斗图标弹筛选框） */
  filterable?: boolean
  /** 固定列位置 */
  fixed?: 'left' | 'right' | boolean
  /** 自定义格式化（label 映射） */
  map?: Record<string | number, any>
  /** 自定义格式化函数（优先级高于 map） */
  formatLabel?: (value: any) => string
}

import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import ColumnFilter from './ColumnFilter.vue'
import { loadTablePreference, saveTablePreference } from '@/utils/columns-setting'
import { calculateTableHeight } from '@/utils/table-size'

// ============================================================================
// Props
// ============================================================================

interface Props {
  /** 当前页数据 */
  data?: any[]
  /** 总条数 */
  total?: number
  /** 分页参数（含 page_no / page_size） */
  query: { page_no: number; page_size: number; [key: string]: any }
  /** 列定义数组（必填，推荐 .sync） */
  columns: BaseTableColumn[]
  /** 表格 loading */
  loading?: boolean
  /** 用户偏好存储 key（如 'user_list'）。提供后自动持久化 columns / density / pageSize */
  viewName?: string
  /** 表格密度（推荐 .sync 双向绑定） */
  tableSize?: 'small' | 'default' | 'large'
  /** 自定义高度（传值则关闭自适应） */
  height?: number | string | null
  /** 自适应高度下限 */
  minHeight?: number
  /** 自适应高度 - 顶部偏移 */
  heightOffset?: number
  /** 斑马纹 */
  stripe?: boolean
  /** 边框 */
  border?: boolean
  /** 列宽是否自撑开 */
  fit?: boolean
  /** 高亮当前行 */
  highlightCurrentRow?: boolean
  /** 显示序号列 */
  showIndex?: boolean
  /** 显示选择列 */
  showSelection?: boolean
  /** 显示密度切换按钮 */
  showDensityChanger?: boolean
  /** 显示分页 */
  showPagination?: boolean
  /** 显示背景 */
  showBackground?: boolean
  /** 启用列筛选 */
  enableColumnFilter?: boolean
  /** 分页大小选项 */
  pageSizes?: number[]
  /** 分页布局 */
  paginationLayout?: string
  /**
   * 外部数据库唯一值（{ prop: [values, ...] }）
   * 优先级最高：覆盖当前页数据，保证列筛选弹窗中能看到数据库中所有可选项
   */
  externalUniqueValues?: Record<string, any[]>
  /**
   * 启用 toolbar 响应式折叠
   * - false：工具栏始终平铺（推荐：列表页、业务后台）
   * - true：移动端检测启用后，#toolbar-more 插槽会被收集到“更多 ▾”下拉中
   *
   * 业务调用：
   *   <template #toolbar>...</template>
   *   <template #toolbar-more>...</template>
   */
  responsiveToolbar?: boolean
  /**
   * 移动端断点（像素）。窗口宽度 < 该值时视为移动端
   */
  mobileBreakpoint?: number
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  total: 0,
  loading: false,
  viewName: '',
  tableSize: 'default',
  height: null,
  minHeight: 500,
  heightOffset: 220,
  stripe: true,
  border: true,
  fit: true,
  highlightCurrentRow: true,
  showIndex: true,
  showSelection: true,
  showDensityChanger: true,
  showPagination: true,
  showBackground: true,
  enableColumnFilter: true,
  pageSizes: () => [],
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
  externalUniqueValues: () => ({}),
  responsiveToolbar: false,
  mobileBreakpoint: 768,
})

const emit = defineEmits<{
  (e: 'update:columns', val: BaseTableColumn[]): void
  (e: 'update:tableSize', val: 'small' | 'default' | 'large'): void
  (e: 'size-change', val: number): void
  (e: 'current-change', val: number): void
  (e: 'filter-change', payload: {
    prop: string
    include: any[]
    exclude: any[]
    column_filters: Record<string, { include: any[]; exclude: any[] }>
  }): void
  (e: 'filter-clear', payload: {
    prop: string
    column_filters: Record<string, { include: any[]; exclude: any[] }>
  }): void
  (e: 'row-dblclick', row: any, column: any, event: any): void
  (e: 'selection-change', rows: any[]): void
}>()

// ============================================================================
// 内部状态
// ============================================================================

/** 列筛选状态：{ prop: { include, exclude } } */
const column_filters = ref<Record<string, { include: any[]; exclude: any[] }>>({})

/** 内部维护密度（防止直接修改 prop） */
const internal_table_size = ref(props.tableSize)

/**
 * 响应式断点检测（仅在 responsiveToolbar=true 时启用）
 * - 在 setup 阶段安全初始化（typeof window 防御 SSR）
 * - resize 事件监听尺寸变化
 */
const isMobile = ref(false)
function checkMobile() {
  if (typeof window === 'undefined') return
  isMobile.value = window.innerWidth < props.mobileBreakpoint
}

/** 是否折叠 toolbar-more（responsiveToolbar 开启 + 当前为移动端） */
const shouldFoldToolbar = computed(() => props.responsiveToolbar && isMobile.value)

// ============================================================================
// Computed
// ============================================================================

/** 密度双向绑定 */
const currentTableSize = computed({
  get: () => internal_table_size.value,
  set: (val) => {
    internal_table_size.value = val
    emit('update:tableSize', val)
  },
})

/** 自适应高度 */
const tableHeight = computed(() => calculateTableHeight(props.minHeight, props.heightOffset))

/** 表格最终高度（height 优先） */
const resolvedHeight = computed(() => props.height || tableHeight.value)

/** 可见列（visible !== false） */
const visibleColumns = computed(() =>
  props.columns.filter((c) => c && c.visible !== false)
)

/** 所有可筛列的 prop 列表 */
const filterableProps = computed(() =>
  visibleColumns.value.filter((c) => c.filterable).map((c) => c.prop)
)

/** 分页大小选项（默认 10/20/50/100） */
const resolvedPageSizes = computed(() => {
  if (props.pageSizes && props.pageSizes.length > 0) return props.pageSizes
  return [10, 20, 50, 100]
})

/**
 * 应用列筛选后的列表（纯前端过滤）
 *
 * 筛选语义（同一列内可同时设置 include 与 exclude）：
 * - include 非空：行值必须在 include 列表中
 * - exclude 非空：行值不能在 exclude 列表中
 * - 两者同时：行值 = 在 include AND 不在 exclude
 * - 两者都空：本列不参与筛选
 *
 * 空值匹配：row 值为 null/undefined/"" 均视为空值，与后端 `isnull | empty` 匹配
 */
const filteredItems = computed(() => {
  const items = props.data || []
  const activeFilters = Object.keys(column_filters.value).filter((prop) => {
    const cfg = column_filters.value[prop]
    if (!cfg) return false
    const include = Array.isArray(cfg.include) ? cfg.include : []
    const exclude = Array.isArray(cfg.exclude) ? cfg.exclude : []
    return include.length > 0 || exclude.length > 0
  })

  if (activeFilters.length === 0) return items

  return items.filter((row) => {
    if (!row) return false
    return activeFilters.every((prop) => {
      const cfg = column_filters.value[prop]
      if (!cfg) return true
      const include = Array.isArray(cfg.include) ? cfg.include : []
      const exclude = Array.isArray(cfg.exclude) ? cfg.exclude : []
      const includeSet = include.length > 0 ? new Set(include) : null
      const excludeSet = exclude.length > 0 ? new Set(exclude) : null
      const v = row[prop]
      const isEmpty = v === null || v === undefined || v === ''
      const includeHasEmpty = includeSet ? includeSet.has('') : false
      const excludeHasEmpty = excludeSet ? excludeSet.has('') : false

      if (includeSet && includeSet.size > 0) {
        const matches = includeSet.has(v) || (includeHasEmpty && isEmpty)
        if (!matches) return false
      }
      if (excludeSet && excludeSet.size > 0) {
        const excluded = excludeSet.has(v) || (excludeHasEmpty && isEmpty)
        if (excluded) return false
      }
      return true
    })
  })
})

// ============================================================================
// Watch
// ============================================================================

/** prop tableSize 变更 → 同步到 internal */
watch(
  () => props.tableSize,
  (val) => {
    internal_table_size.value = val
  }
)

/** 表格密度变化 → 自动持久化 */
watch(internal_table_size, (val) => {
  if (props.viewName) {
    saveTablePreference(props.viewName, { density: val })
  }
})

/** 分页大小变化 → 自动持久化 */
watch(
  () => props.query.page_size,
  (val) => {
    if (props.viewName && typeof val === 'number') {
      saveTablePreference(props.viewName, { pageSize: val })
    }
  }
)

/** 列定义变化 → 自动持久化 */
watch(
  () => props.columns,
  (val) => {
    if (props.viewName) {
      saveTablePreference(props.viewName, { columns: val })
    }
  },
  { deep: true }
)

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  if (props.responsiveToolbar) {
    checkMobile()
    window.addEventListener('resize', checkMobile)
  }
  applyStoredPreferences()
})

onBeforeUnmount(() => {
  if (props.responsiveToolbar) {
    window.removeEventListener('resize', checkMobile)
  }
})

/** responsiveToolbar 由 false → true 动态开启时需要补上监听 */
watch(
  () => props.responsiveToolbar,
  (val) => {
    if (val) {
      checkMobile()
      window.addEventListener('resize', checkMobile)
    } else {
      window.removeEventListener('resize', checkMobile)
    }
  }
)

// ============================================================================
// Methods
// ============================================================================

/**
 * 按列 prop 实时计算列筛选可选项值
 *
 * 数据源优先级：
 * 1. externalUniqueValues（外部传入的数据库全量唯一值，最优先）
 * 2. props.data（当前页数据）
 * 3. column_filters 中历史已选值（保证取消筛选后仍能看到曾经选过的选项）
 */
function getColumnUniqueValuesFor(prop: string): any[] {
  if (!props.enableColumnFilter) return []
  const items = props.data || []
  const map = new Map<string, any>()

  const tryAdd = (v: any) => {
    if (v === null || v === undefined) return
    const s = v === '' ? '' : String(v)
    if (!map.has(s)) {
      map.set(s, v)
    } else {
      // 已有但为字符串、新值为 bool/number → 升级为原始类型
      const existing = map.get(s)
      if (typeof existing === 'string' && (typeof v === 'boolean' || typeof v === 'number')) {
        map.set(s, v)
      }
    }
  }

  // 1. 外部数据库唯一值
  const external = props.externalUniqueValues?.[prop]
  if (Array.isArray(external)) {
    external.forEach(tryAdd)
  }

  // 2. 当前页数据
  items.forEach((row: any) => {
    if (row) tryAdd(row[prop])
  })

  // 3. 当前列筛选中历史已选值（兜底）
  const cfg = column_filters.value[prop]
  if (cfg) {
    const include = Array.isArray(cfg.include) ? cfg.include : []
    const exclude = Array.isArray(cfg.exclude) ? cfg.exclude : []
    ;[...include, ...exclude].forEach(tryAdd)
  }

  return Array.from(map.values()).sort((a, b) => {
    // 空值排最后
    if (a === '' && b !== '') return 1
    if (b === '' && a !== '') return -1
    if (typeof a === 'number' && typeof b === 'number') return a - b
    return String(a).localeCompare(String(b), 'zh-CN')
  })
}

/**
 * 应用持久化的用户偏好（columns / density / pageSize）
 */
function applyStoredPreferences() {
  if (!props.viewName) return
  const pref = loadTablePreference(props.viewName)
  if (!pref) return

  // 1) 列配置：visible / 排序 / width
  if (Array.isArray(pref.columns) && pref.columns.length > 0) {
    const storedMap = new Map(pref.columns.map((s: BaseTableColumn) => [s.prop, s]))
    const merged = props.columns.map((col) => {
      const s = storedMap.get(col.prop) as BaseTableColumn | undefined
      return s ? { ...col, ...s } : { ...col }
    })
    const changed = merged.some((col, i) => {
      const c = props.columns[i]
      return Object.keys(col).some((k) => (col as any)[k] !== (c as any)[k])
    })
    if (changed) emit('update:columns', merged)
  }

  // 2) 表格密度
  if (pref.density && pref.density !== props.tableSize) {
    emit('update:tableSize', pref.density)
  }

  // 3) 每页大小
  if (
    typeof pref.pageSize === 'number' &&
    pref.pageSize > 0 &&
    pref.pageSize !== props.query.page_size
  ) {
    emit('size-change', pref.pageSize)
  }
}

/**
 * 默认单元格渲染：
 * - 若 column.formatLabel 提供：使用自定义函数
 * - 若 column.map 提供字典映射：使用 map[value]
 * - 都不提供则显示原始值
 */
function formatCell(row: any, column: BaseTableColumn): any {
  const value = row[column.prop]
  if (typeof column.formatLabel === 'function') {
    return value === '' ? '(空值)' : column.formatLabel(value)
  }
  if (column.map && typeof column.map === 'object') {
    if (value === null || value === undefined || value === '') return '(空值)'
    return column.map[value] !== undefined ? column.map[value] : value
  }
  return value
}

/**
 * 取列筛选项的 include 值
 */
function getColumnFilterInclude(prop: string): any[] {
  const cfg = column_filters.value[prop]
  if (!cfg) return []
  return Array.isArray(cfg.include) ? cfg.include : []
}

/**
 * 取列筛选项的 exclude 值
 */
function getColumnFilterExclude(prop: string): any[] {
  const cfg = column_filters.value[prop]
  if (!cfg) return []
  return Array.isArray(cfg.exclude) ? cfg.exclude : []
}

/**
 * 派生 FormatLabel：业务列设了 column.map 时，弹窗中展示为 label，后端传的是 value
 * 优先级：column.formatLabel > column.map
 *
 * 空值标识：空字符串 "" 统一显示为 "(空值)"
 */
function resolveColumnFormatLabel(column: BaseTableColumn): ((val: any) => string) | null {
  if (!column) return null
  if (typeof column.formatLabel === 'function') {
    return (val) => (val === '' ? '(空值)' : column.formatLabel!(val))
  }
  if (column.map && typeof column.map === 'object') {
    return (val) => {
      if (val === null || val === undefined || val === '') return '(空值)'
      return column.map![val] !== undefined ? column.map![val] : val
    }
  }
  return null
}

function resolveColumnFormatValues(column: BaseTableColumn): any[] {
  return getColumnFilterInclude(column.prop)
}

function resolveColumnFormatExclude(column: BaseTableColumn): any[] {
  return getColumnFilterExclude(column.prop)
}

/**
 * 列筛选确认事件
 *
 * payload 形态（与 molding-expert 对齐）：
 * - { include, exclude }：新格式
 * - 数组：旧格式（仅 include）
 * - { values, exclude }：过渡格式
 */
function handleColumnFilterChange(prop: string, payload: any) {
  let include: any[] = []
  let exclude: any[] = []

  if (Array.isArray(payload)) {
    // 旧 payload：数组 → 仅 include
    include = [...payload]
    exclude = []
  } else if (payload && Array.isArray(payload.include)) {
    // 新 payload
    include = [...payload.include]
    exclude = Array.isArray(payload.exclude) ? [...payload.exclude] : []
  } else if (payload && Array.isArray(payload.values)) {
    // 过渡 payload
    if (payload.exclude) {
      include = []
      exclude = [...payload.values]
    } else {
      include = [...payload.values]
      exclude = []
    }
  }

  column_filters.value[prop] = { include, exclude }
  emit('filter-change', {
    prop,
    include,
    exclude,
    column_filters: { ...column_filters.value },
  })
}

function handleColumnFilterClear(prop: string) {
  column_filters.value[prop] = { include: [], exclude: [] }
  emit('filter-clear', {
    prop,
    column_filters: { ...column_filters.value },
  })
}

/** 分页事件由父组件处理（修改 query + 重发请求） */
function handleSizeChange(val: number) {
  emit('size-change', val)
}

function handleCurrentChange(val: number) {
  emit('current-change', val)
}

/** 行双击事件 */
function onRowDblclick(row: any, column: any, event: any) {
  emit('row-dblclick', row, column, event)
}

/**
 * 派生 min-width：
 * - 优先 column.minWidth
 * - 否则 undefined（让 el-table 按内容自动伸展）
 *
 * 同时，width 和 minWidth 并存时输出 dev-only 警告
 */
function resolveMinWidth(column: BaseTableColumn): number | string | undefined {
  if (!column) return undefined
  const hasWidth = typeof column.width === 'number'
  const hasMinWidth = typeof column.minWidth === 'number' || typeof column.minWidth === 'string'
  if (hasWidth && hasMinWidth && import.meta.env.DEV) {
    console.warn(
      `[BaseTable] 列 "${column.prop}" 同时设置了 width 和 minWidth，el-table 原生行为会忽略 minWidth。请只保留其一；新页面推荐使用 minWidth。`
    )
  }
  if (hasMinWidth) return column.minWidth
  return undefined
}
</script>

<style scoped lang="scss">
.base-table {
  width: 100%;
}

.row-toolbutton {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 0;
}

/*
 * .toolbar-buttons: 取代 el-button-group
 *
 * el-button-group 要求子元素全部是 el-button，一旦混入
 * el-upload / el-dropdown / el-popover 等 div 类组件，
 * 会破坏连接样式（圆角、border）→ 按钮错位。
 *
 * 该容器采用 inline-flex + gap: 0：
 * - 按钮独立圆角、不连接（兼容任意子组件）
 * - 按钮贴紧（视觉上与 el-button-group 近似）
 * - flex-wrap: wrap 宽窄屏自动换行兑底
 */
.toolbar-buttons {
  display: inline-flex;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
}

/*
 * 覆盖 el-button 默认的 & + & { margin-left: 12px }。
 * element-plus 为了独立按钮场景默认加了间距，但 button-group 内部会主动覆盖为 0。
 * 我们的 .toolbar-buttons 也能在容器内起到同样的作用——手动清除该间距。
 */
.toolbar-buttons :deep(.el-button + .el-button) {
  margin-left: 0;
}

/* “更多 ▾”下拉里的按钮纵向列表 */
.toolbar-more-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}

.toolbar-more-list :deep(.el-button) {
  width: 100%;
  justify-content: flex-start;
}

/* 分页：靠左显示，与 element-plus 官方 demo 一致 */
.pagination {
  display: flex;
  justify-content: flex-start;
  margin-top: 6px;
}

/* 表格密度：小/中/大 */
.table-size-small {
  :deep(.el-table__cell) {
    padding: 4px 0;
    font-size: 12px;
  }
}

.table-size-normal {
  :deep(.el-table__cell) {
    padding: 8px 0;
    font-size: 13px;
  }
}

.table-size-large {
  :deep(.el-table__cell) {
    padding: 12px 0;
    font-size: 14px;
  }
}

/*
 * popover teleport 到 body，scoped 不生效。
 * 需用 unscoped 块定义 popper-class 内的样式。
 */
.toolbar-more-popover.el-popover {
  padding: 8px;

  .toolbar-more-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 140px;
  }

  .toolbar-more-list .el-button {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>