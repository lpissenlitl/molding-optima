<template>
  <el-dialog
    class="setting-dialog"
    :model-value="is_visible"
    :modal="true"
    :append-to-body="true"
    :close-on-click-modal="false"
    :lock-scroll="true"
    width="600px"
    title="表格列设置"
    @close="handleClose"
  >
    <el-table
      :data="table_list"
      style="width: 100%"
      border
      size="small"
    >
      <el-table-column label="显示" width="80" align="center">
        <template #default="scope">
          <el-checkbox v-model="scope.row.visible" />
        </template>
      </el-table-column>
      <el-table-column
        label="字段名称"
        min-width="380"
        header-align="center"
      >
        <template #default="scope">
          <span>{{ scope.row.label }}</span>
        </template>
      </el-table-column>
      <el-table-column label="列宽" align="center" width="120">
        <template #default="scope">
          <el-input v-model="scope.row.width" size="small">
            <template #suffix>px</template>
          </el-input>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button size="small" @click="handleClose">取消</el-button>
      <el-button type="primary" size="small" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * TableSetting - 表格列设置弹窗
 *
 * @description 列显隐切换、列宽编辑、拖拽排序（基于 Sortable.js）
 * @author MoldingX Team
 *
 * 用法：v-model:show="..."
 */
import { ref, computed, watch, nextTick } from 'vue'
import Sortable from 'sortablejs'

const props = withDefaults(
  defineProps<{
    /** v-model:show 绑定 */
    modelValue?: boolean
    /** 列定义数组 */
    tableData?: Record<string, any>[]
  }>(),
  {
    modelValue: false,
    tableData: () => [],
  }
)

const emit = defineEmits<{
  /** v-model 事件 */
  (e: 'update:modelValue', val: boolean): void
  /** 关闭回调 */
  (e: 'close'): void
}>()

/** 弹窗可见性 */
const is_visible = computed(() => props.modelValue)

// 本地编辑副本
const table_list = ref<Record<string, any>[]>([])

/**
 * 同步父组件 props.tableData 到本地副本
 *
 * 关键设计：使用 in-place mutation（splice + push），保证 table_list 与
 * 父组件数组保持一致的数据来源（虽是不同数组，但内容相同）。
 * 用户编辑时只动 table_list，确认时通过 syncBackToParent 一次性回写到父组件。
 */
watch(
  () => props.tableData ?? [],
  (src) => {
    const need_sync =
      table_list.value.length !== src.length ||
      !src.every((col: any, i: number) => col?.id === table_list.value[i]?.id)
    if (need_sync) {
      table_list.value.splice(0, table_list.value.length)
      src.forEach((col: any) => table_list.value.push({ ...col }))
      nextTick(() => initSortable())
    }
  },
  { immediate: true, deep: true }
)

/**
 * 初始化 Sortable.js 拖拽排序
 * 监听 tbody 行拖动结束事件，splice 移动数据项
 */
function initSortable() {
  const tbody = document.querySelector('.setting-dialog .el-dialog__body tbody') as HTMLElement | null
  if (!tbody) return

  Sortable.create(tbody, {
    draggable: '.el-table__row',
    onEnd({ newIndex, oldIndex }: { newIndex?: number; oldIndex?: number }) {
      if (newIndex === undefined || oldIndex === undefined) return
      const moved = table_list.value.splice(oldIndex, 1)[0]
      table_list.value.splice(newIndex, 0, moved)
    },
  })
}

/**
 * 将本地编辑结果同步回 props.tableData（父组件数组引用）
 * 使用 Object.assign 进行 in-place mutation，Vue 响应式可正确追踪此次变更
 */
function syncBackToParent() {
  const parent = props.tableData
  if (!parent) return
  table_list.value.forEach((col, i) => {
    if (i < parent.length) {
      Object.assign(parent[i], col)
    }
  })
}

/** 点击「确定」：回写父组件 + 关闭 */
function handleConfirm() {
  syncBackToParent()
  emit('close')
  emit('update:modelValue', false)
}

/** 点击「取消」/「X」/遮罩：仅关闭 */
function handleClose() {
  emit('update:modelValue', false)
}
</script>

<style lang="scss" scoped>
.setting-dialog {
  :deep(.el-dialog__body) {
    padding-top: 10px;
    padding-bottom: 10px;
  }
}
</style>
