<template>
  <BaseSearchForm
    :query="query_params"
    :items="search_items"
    :expandable="true"
    @search="handleSearch"
    @reset="handleReset"
  />
</template>

<script>
import BaseSearchForm from "@/components/BaseSearchForm.vue"
import { moldCategoryOptions, moldStructureOptions } from "@/constants/mold-const"

export default {
  name: "MoldSearchForm",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        mold_no: null,
        mold_name: null,
        category: null,
        structure: null,
        cavity_layout: null,
        manufacturing_method: null,
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [
        // 基础项
        { 
          label: "模具编号", 
          prop: "mold_no", 
          type: "autocomplete", 
          level: "basic",
          query: { table: "mold", column: "mold_no" } 
        },
        { 
          label: "模具名称", 
          prop: "mold_name", 
          type: "autocomplete", 
          level: "basic",
          query: { table: "mold", column: "mold_name" } 
        },
        { 
          label: "模具类别", 
          prop: "category", 
          type: "select", 
          level: "basic",
          options: moldCategoryOptions 
        },
        { 
          label: "模具结构", 
          prop: "structure", 
          type: "select", 
          level: "basic",
          options: moldStructureOptions 
        },
        { 
          label: "模腔布局", 
          prop: "cavity_layout", 
          type: "autocomplete", 
          level: "basic",
          query: { table: "mold", column: "cavity_layout" } 
        },
        { 
          label: "制作方式", 
          prop: "manufacturing_method", 
          type: "autocomplete", 
          level: "basic",
          query: { table: "project", column: "manufacturing_method" } 
        },
      ]
    }
  },
  methods: {
    /**
     * 处理搜索
     */
    handleSearch() {
      this.$emit("search")
    },
    
    /**
     * 处理重置
     */
    handleReset() {
      this.$emit("reset")
    }
  }
}
</script>

<style lang="scss" scoped>

</style>
