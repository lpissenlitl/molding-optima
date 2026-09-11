<!--
  ProcessSearchForm - 工艺条件搜索表单

  实际查询的是 ProcessCondition 表（包含模具/机器/材料上下文）。
  - 状态：使用中 / 已归档（后端 ProcessCondition.STATUS_CHOICES）
  - 起源：手工新建 / AI 推荐 / 实验设计 等（后端 ProcessCondition.ORIGIN_CHOICES）
  - 模具/注塑机/材料：通过 autocomplete 远程拉取候选

  数据流：
    父组件 :query-detail="query" @search @reset
    queryDetail 字段更新 → 父组件 fetchList()
-->
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
/**
 * 工艺条件搜索表单（Vue 3 Composition API 版）
 *
 * - props.queryDetail 由父组件提供，作为初始查询条件
 * - 实际双向绑定通过 BaseSearchForm 内部完成
 * - 通过 emit('search') / emit('reset') 通知父组件触发查询
 */
import BaseSearchForm from '@/components/BaseSearchForm.vue'

// ============================================================================
// Props / Emits
// ============================================================================

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

// ============================================================================
// 状态选项
// ============================================================================

const STATUS_OPTIONS = [
  { label: '使用中', value: 'active' },
  { label: '已归档', value: 'archived' },
]

const ORIGIN_OPTIONS = [
  { label: '手工新建', value: 'manual_creation' },
  { label: '基于模板', value: 'template_based' },
  { label: 'AI 推荐启动', value: 'ai_recommendation' },
  { label: '实验设计（DOE）', value: 'doe_experiment' },
  { label: '历史工艺导入', value: 'legacy_import' },
  { label: '设备参数捕获', value: 'equipment_capture' },
  { label: '工艺移植', value: 'process_transplant' },
]

// ============================================================================
// 搜索项配置
// ============================================================================

// BaseSearchForm 通过 v-model="query[prop]" 直接绑定父组件的 reactive 对象
// 所以这里直接传 props.queryDetail，不做包装
const search_items = [
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
  { slot_name: 'date-range' },
]

// ============================================================================
// 事件
// ============================================================================

function emitSearch() {
  emit('search')
}

function emitReset() {
  emit('reset')
}
</script>

<style lang="scss" scoped>
</style>
