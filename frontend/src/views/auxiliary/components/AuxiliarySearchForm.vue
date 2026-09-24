<!--
  AuxiliarySearchForm - 辅助装置搜索表单（配置驱动）

  设计思路（与 mold / project / polymer 模块保持一致）：
  - 复用 BaseSearchForm 组件（公共）
  - 本组件只声明本模块的搜索字段配置（search_items）
  - 通过 query-detail prop 接收父组件的 query 对象
  - 通过 @search / @reset 事件回调

  风格：Composition API（Vue 3 + <script setup>，2026-09 统一升级）

  字段策略：
  - 全部使用 autocomplete 类型，从后端拉取历史输入建议
  - 2 个搜索字段（设备名称 / 设备类型）
  - 均为基础字段，不过度展开
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