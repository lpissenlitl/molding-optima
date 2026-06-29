<template>
  <BaseSearchForm
    :query="query_params"
    :items="search_items"
    @search="handleSearch"
    @reset="handleReset"
  />
</template>

<script>
import BaseSearchForm from "@/components/BaseSearchForm.vue"

export default {
  name: "PolymerSearchForm",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        manufacturer: null,
        abbreviation: null,
        grade: null,
        category: null,
        data_source: null,
        level_code: null,
        vendor_code: null,
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [
        { label: "塑料厂商", prop: "manufacturer", type: "autocomplete", query: { table: "polymer", column: "manufacturer" } },
        { label: "塑料简称", prop: "abbreviation", type: "autocomplete", query: { table: "polymer", column: "abbreviation" } },
        { label: "塑料牌号", prop: "grade", type: "autocomplete", query: { table: "polymer", column: "grade" } },
        { label: "塑料类别", prop: "category", type: "autocomplete", query: { table: "polymer", column: "category" } },
        { label: "数据来源", prop: "data_source", type: "autocomplete", query: { table: "polymer", column: "data_source" } },
        { label: "等级代码", prop: "level_code", type: "autocomplete", query: { table: "polymer", column: "level_code" } },
        { label: "供应商代码", prop: "vendor_code", type: "autocomplete", query: { table: "polymer", column: "vendor_code" } },
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
