<!--
  PolymerSearchForm - 聚合物搜索表单（配置驱动）

  设计思路（与 mold / project 模块保持一致）：
  - 复用 BaseSearchForm 组件（公共）
  - 本组件只声明本模块的搜索字段配置（search_items）
  - 通过 query-detail prop 接收父组件的 query 对象
  - 通过 @search / @reset 事件回调

  风格：Composition API（Vue 3 + <script setup>，2026-09 统一升级）

  字段策略：
  - 全部使用 autocomplete 类型，从后端拉取历史输入建议
  - 7 个搜索字段（厂商 / 简称 / 牌号 / 类别 / 数据来源 / 等级代码 / 供应商代码）
  - level: 'basic'（全部为基础字段，不过度展开）
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
      manufacturer: null,
      abbreviation: null,
      grade: null,
      category: null,
      data_source: null,
      level_code: null,
      vendor_code: null,
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
  // --- 基础项（始终显示） ---
  { label: "塑料厂商", prop: "manufacturer", type: "autocomplete", level: "basic", query: { table: "polymer", column: "manufacturer" } },
  { label: "塑料简称", prop: "abbreviation", type: "autocomplete", level: "basic", query: { table: "polymer", column: "abbreviation" } },
  { label: "塑料牌号", prop: "grade", type: "autocomplete", level: "basic", query: { table: "polymer", column: "grade" } },
  { label: "塑料类别", prop: "category", type: "autocomplete", level: "basic", query: { table: "polymer", column: "category" } },
  { label: "数据来源", prop: "data_source", type: "autocomplete", level: "basic", query: { table: "polymer", column: "data_source" } },
  { label: "等级代码", prop: "level_code", type: "autocomplete", level: "basic", query: { table: "polymer", column: "level_code" } },
  { label: "供应商代码", prop: "vendor_code", type: "autocomplete", level: "basic", query: { table: "polymer", column: "vendor_code" } },
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