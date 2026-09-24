<template>
  <BaseSearchForm
    :query="query_params"
    :items="search_items"
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
      location: null,
      brand: null,
      model: null,
      device_no: null,
      asset_no: null,
      machine_type: null,
      drive_system: null,
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
  { label: "品牌", prop: "brand", type: "autocomplete", query: { table: "injection_molding_machine", column: "brand" } },
  { label: "型号", prop: "model", type: "autocomplete", query: { table: "injection_molding_machine", column: "model" } },
  { label: "设备位置", prop: "location", type: "autocomplete", query: { table: "injection_molding_machine", column: "location" } },
  { label: "设备类型", prop: "machine_type", type: "autocomplete", query: { table: "injection_molding_machine", column: "machine_type" } },
  { label: "驱动系统", prop: "drive_system", type: "autocomplete", query: { table: "injection_molding_machine", column: "drive_system" } },
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