<template>
  <BaseSearchForm
    :query="query_params"
    :items="search_items"
    @search="handleSearch"
    @reset="handleReset"
  >
    <!-- 自定义日期范围 -->
    <template #date-range="{ query }">
      <el-form-item label="工艺录入日期">
        <el-date-picker
          v-model="query.start_date"
          type="date"
          placeholder="选择日期"
          format="yyyy-MM-dd"
          value-format="yyyy-MM-dd"
        />
        -
        <el-date-picker
          v-model="query.end_date"
          type="date"
          placeholder="选择日期"
          format="yyyy-MM-dd"
          value-format="yyyy-MM-dd"
        />
      </el-form-item>
    </template>
  </BaseSearchForm>
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
      status: null,
      mold_no: null,
      machine_model: null,
      polymer_abbreviation: null,
      start_date: null,
      end_date: null,
    })
  }
)

const emit = defineEmits<{
  (e: 'search'): void
  (e: 'reset'): void
}>()

// 复用父组件传入的 query 引用（BaseSearchForm 双向修改会同步到父组件）
const query_params = props.queryDetail

// 搜索项配置
const search_items: SearchItem[] = [
  { label: "工艺状态", prop: "status", type: "select", options: [] },
  { label: "模具编号", prop: "mold_no", type: "autocomplete", query: { table: "mold", column: "mold_no" } },
  { label: "注塑机型号", prop: "machine_model", type: "autocomplete", query: { table: "injection_molding_machine", column: "model" } },
  { label: "塑料简称", prop: "polymer_abbreviation", type: "autocomplete", query: { table: "polymer", column: "abbreviation" } },
  // 日期范围占位符
  { slot_name: "date-range", label: "", prop: "", type: "slot" },
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