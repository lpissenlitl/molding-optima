<!--
  FillerSearchForm - 填充物搜索表单

  对齐 PolymerSearchForm 规范：
    - 始终展示（:expandable="false"）
    - 控件宽度 200px（:control-width="200"）
    - 4 个字段全部 level: 'basic'
    - Vue 3 + Element Plus（Composition API）
-->
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
import { ref } from 'vue'
import BaseSearchForm from '@/components/BaseSearchForm.vue'

const props = defineProps({
  queryDetail: {
    type: Object,
    default: () => ({
      name: null,
      abbreviation: null,
      category: null,
      shape: null,
    }),
  },
})

const emit = defineEmits<{
  (e: 'search'): void
  (e: 'reset'): void
}>()

const query_params = ref<any>({ ...props.queryDetail })

const search_items = [
  { label: '名称', prop: 'name', type: 'autocomplete', level: 'basic', query: { table: 'filler', column: 'name' } },
  { label: '缩写', prop: 'abbreviation', type: 'autocomplete', level: 'basic', query: { table: 'filler', column: 'abbreviation' } },
  { label: '类别', prop: 'category', type: 'autocomplete', level: 'basic', query: { table: 'filler', column: 'category' } },
  { label: '形状', prop: 'shape', type: 'autocomplete', level: 'basic', query: { table: 'filler', column: 'shape' } },
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