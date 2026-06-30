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
import { projectStatusOptions } from "@/constants/project-const"

export default {
  name: "ProjectSearchForm",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        project_code: null,
        mold_no: null,
        project_name: null,
        initiator: null,
        application_industry: null,
        status: null,
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [ 
        { 
          label: "项目编号", 
          prop: "project_code", 
          type: "autocomplete", 
          query: { table: "project", column: "project_code" } 
        },
        { 
          label: "项目状态", 
          prop: "status", 
          type: "select", 
          options: projectStatusOptions 
        },
        { 
          label: "项目名称", 
          prop: "project_name", 
          type: "autocomplete", 
          query: { table: "project", column: "project_name" } 
        },
        { 
          label: "模具编号", 
          prop: "mold_no", 
          type: "autocomplete", 
          query: { table: "mold", column: "mold_no" } 
        },
        { 
          label: "客户名称", 
          prop: "initiator", 
          type: "autocomplete", 
          query: { table: "project", column: "initiator" } 
        },
        { 
          label: "应用行业", 
          prop: "application_industry", 
          type: "autocomplete", 
          query: { table: "project", column: "application_industry" } 
        },
      ]
    }
  },
  methods: {
    handleSearch() {
      // 触发父组件的搜索事件
      this.$emit("search")
    },
    handleReset() {
      // 触发父组件的重置事件
      this.$emit("reset")
    }
  }
}
</script>

<style lang="scss" scoped>

</style>
