<!-- AuxiliarySearchForm - 辅助装置搜索表单（配置驱动）：复用 BaseSearchForm，本组件只声明本模块 search_items 字段配置，query-detail prop 接收父组件 query，@search/@reset 回调；2 个字段（设备名称/设备类型）全部用 autocomplete 类型拉取历史输入建议 -->

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

const props = withDefaults(
  defineProps<{
    queryDetail?: Record<string, any>
  }>(),
  {
    queryDetail: () => ({
      equipment_name: null,
      equipment_type: null,
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
  { label: "设备名称", prop: "equipment_name", type: "autocomplete", level: "basic", query: { table: "auxiliary_equipment", column: "equipment_name" } },
  { label: "设备类型", prop: "equipment_type", type: "autocomplete", level: "basic", query: { table: "auxiliary_equipment", column: "equipment_type" } },
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