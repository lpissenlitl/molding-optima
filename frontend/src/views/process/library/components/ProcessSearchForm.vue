<!-- ProcessSearchForm - 工艺条件搜索表单（查 ProcessCondition 表，含模具/机器/材料上下文） -->
<template>
  <BaseSearchForm
    :query="queryDetail"
    :items="search_items"
    :control-width="200"
    @search="emitSearch"
    @reset="emitReset"
  >
    <!-- 日期范围（开始/结束） -->
    <template #date-range="{ query }">
      <el-form-item label="录入日期">
        <el-date-picker
          v-model="query.start_date"
          type="date"
          placeholder="开始日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
        <span style="margin: 0 8px;">至</span>
        <el-date-picker
          v-model="query.end_date"
          type="date"
          placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
    </template>
  </BaseSearchForm>
</template>

<script setup lang="ts">
/** 工艺条件搜索表单：props.queryDetail 由父组件提供作为初始查询条件，双向绑定通过 BaseSearchForm 内部完成；emit('search') / emit('reset') 通知父组件触发查询 */
import BaseSearchForm from '@/components/BaseSearchForm.vue'
import type { SearchItem } from '@/types/search-item'
import { CONDITION_STATUS_OPTIONS } from '@/views/process/shared/condition-status'

// Props / Emits

interface QueryDetail {
  status?: string | null
  origin_type?: string | null
  mold_no?: string | null
  machine_model?: string | null
  polymer_abbreviation?: string | null
  start_date?: string | null
  end_date?: string | null
  [key: string]: any
}

const props = defineProps<{
  queryDetail: QueryDetail
}>()

const emit = defineEmits<{
  (e: 'search'): void
  (e: 'reset'): void
}>()

// 状态选项

const STATUS_OPTIONS = CONDITION_STATUS_OPTIONS

const ORIGIN_OPTIONS = [
  { label: '手工新建', value: 'manual_creation' },
  { label: '基于模板', value: 'template_based' },
  { label: '实验设计（DOE）', value: 'doe_experiment' },
  { label: '历史工艺导入', value: 'legacy_import' },
  { label: '设备参数捕获', value: 'equipment_capture' },
  { label: '工艺移植', value: 'process_transplant' },
]

// 搜索项配置

// BaseSearchForm 通过 v-model="query[prop]" 直接绑定父组件的 reactive 对象
// 所以这里直接传 props.queryDetail，不做包装
const search_items: SearchItem[] = [
  {
    label: '状态',
    prop: 'status',
    type: 'select',
    level: 'basic',
    options: STATUS_OPTIONS,
  },
  {
    label: '起源类型',
    prop: 'origin_type',
    type: 'select',
    level: 'basic',
    options: ORIGIN_OPTIONS,
  },
  {
    label: '模具编号',
    prop: 'mold_no',
    type: 'autocomplete',
    level: 'basic',
    query: { table: 'mold', column: 'mold_no' },
  },
  {
    label: '设备型号',
    prop: 'machine_model',
    type: 'autocomplete',
    level: 'basic',
    query: { table: 'injection_molding_machine', column: 'model' },
  },
  {
    label: '塑料简称',
    prop: 'polymer_abbreviation',
    type: 'autocomplete',
    level: 'basic',
    query: { table: 'polymer', column: 'abbreviation' },
  },
  // 日期范围占位
  {
    label: '录入日期',
    prop: 'start_date',
    type: 'slot',
    level: 'basic',
    slot_name: 'date-range',
  },
]

// 事件

function emitSearch() {
  emit('search')
}

function emitReset() {
  emit('reset')
}
</script>

<style lang="scss" scoped>
</style>
