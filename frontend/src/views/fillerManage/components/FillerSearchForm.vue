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
  name: "FillerSearchForm",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        name: null,
        abbreviation: null,
        category: null,
        shape: null,
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [
        { label: "名称", prop: "name", type: "autocomplete", query: { table: "filler", column: "name" } },
        { label: "缩写", prop: "abbreviation", type: "autocomplete", query: { table: "filler", column: "abbreviation" } },
        { label: "类别", prop: "category", type: "autocomplete", query: { table: "filler", column: "category" } },
        { label: "形状", prop: "shape", type: "autocomplete", query: { table: "filler", column: "shape" } },
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
