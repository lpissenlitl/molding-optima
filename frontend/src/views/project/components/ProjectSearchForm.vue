<!-- ProjectSearchForm - 项目搜索表单（配置驱动）：复用 BaseSearchForm，本组件只声明本模块 search_items 字段配置，query-detail prop 接收父组件 query，@search/@reset 回调；这种"配置驱动"的设计让 mold / project / equipment / polymer 等模块共用同一套搜索表单 UI，业务模块只关心"我有哪些搜索字段" -->

<template>
  <BaseSearchForm
    :query="query_params"
    :items="search_items"
    :expandable="false"
    :control-width="200"
    @search="handleSearch"
    @reset="handleReset"
  />
</template>

<script setup lang="ts">
import BaseSearchForm from '@/components/BaseSearchForm.vue'
import type { SearchItem } from '@/types/search-item'
import { projectStatusOptions, projectSourceOptions } from '@/constants/project-const'

const props = withDefaults(
  defineProps<{
    queryDetail?: Record<string, any>
  }>(),
  {
    queryDetail: () => ({
      project_code: null,
      project_name: null,
      status: null,
      source: null,
      initiator: null,
      project_manager: null,
    })
  }
)

const emit = defineEmits<{
  (e: 'search'): void
  (e: 'reset'): void
}>()

// 复用父组件传入的 query 引用（BaseSearchForm 双向修改会同步到父组件）
const query_params = props.queryDetail

const search_items: SearchItem[] = [
  // 基础项（始终显示，与 MoldSearchForm 风格一致：4 字 label）
  { label: '项目编号', prop: 'project_code', type: 'input', level: 'basic' },
  { label: '项目名称', prop: 'project_name', type: 'input', level: 'basic' },
  { label: '项目状态', prop: 'status', type: 'select', level: 'basic', options: projectStatusOptions },
  { label: '项目来源', prop: 'source', type: 'select', level: 'basic', options: projectSourceOptions },
  // 高级项（需要展开）
  { label: '客户名称', prop: 'initiator', type: 'input', level: 'advanced' },
  { label: '项目经理', prop: 'project_manager', type: 'input', level: 'advanced' },
]

function handleSearch() {
  emit('search')
}

function handleReset() {
  emit('reset')
}
</script>

<style lang="scss" scoped>
</style>