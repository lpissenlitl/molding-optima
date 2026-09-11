<!--
  AuxiliarySearchForm - 辅助装置搜索表单（配置驱动）

  设计思路（与 mold / project / polymer 模块保持一致）：
  - 复用 BaseSearchForm 组件（公共）
  - 本组件只声明本模块的搜索字段配置（search_items）
  - 通过 query-detail prop 接收父组件的 query 对象
  - 通过 @search / @reset 事件回调

  风格：Options API（与 InjectionSearchForm / PolymerSearchForm 完全一致）

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

<script>
import BaseSearchForm from "@/components/BaseSearchForm.vue"

export default {
  name: "AuxiliarySearchForm",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        equipment_name: null,
        equipment_type: null,
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [
        { label: "设备名称", prop: "equipment_name", type: "autocomplete", level: "basic", query: { table: "auxiliary_equipment", column: "equipment_name" } },
        { label: "设备类型", prop: "equipment_type", type: "autocomplete", level: "basic", query: { table: "auxiliary_equipment", column: "equipment_type" } },
      ],
    }
  },
  methods: {
    handleSearch() {
      this.$emit("search")
    },
    handleReset() {
      this.$emit("reset")
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
