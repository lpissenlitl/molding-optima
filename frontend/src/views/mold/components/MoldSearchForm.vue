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
import BaseSearchForm from "@/components/BaseSearchForm.vue"
import type { SearchItem } from "@/types/search-item"
import { moldCategoryOptions, moldStructureOptions } from "@/constants/mold-const"

const props = withDefaults(
  defineProps<{
    queryDetail?: Record<string, any>
  }>(),
  {
    queryDetail: () => ({
      mold_no: null,
      mold_name: null,
      category: null,
      structure: null,
      cavity_layout: null,
      manufacturing_method: null,
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
  { label: "模具编号", prop: "mold_no", type: "autocomplete", level: "basic", query: { table: "mold", column: "mold_no" } },
  { label: "模具名称", prop: "mold_name", type: "autocomplete", level: "basic", query: { table: "mold", column: "mold_name" } },
  { label: "模具类别", prop: "category", type: "select", level: "basic", options: moldCategoryOptions },
  { label: "模具结构", prop: "structure", type: "select", level: "basic", options: moldStructureOptions },
  { label: "模腔布局", prop: "cavity_layout", type: "autocomplete", level: "basic", query: { table: "mold", column: "cavity_layout" } },
  { label: "制作方式", prop: "manufacturing_method", type: "autocomplete", level: "basic", query: { table: "project", column: "manufacturing_method" } },
]

function handleSearch() {
  emit("search")
}

function handleReset() {
  emit("reset")
}
</script>

<style lang="scss" scoped>
</style>