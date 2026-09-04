<!--
  ProjectSearchForm - 项目搜索表单（配置驱动）

  设计思路（与 mold 模块的 MoldSearchForm 一致）：
  - 复用 BaseSearchForm 组件（公共）
  - 本组件只声明本模块的搜索字段配置（search_items）
  - 通过 query-detail prop 接收父组件的 query 对象
  - 通过 @search / @reset 事件回调

  这种"配置驱动"的设计让 mold / project / equipment / polymer 等模块
  可以共用同一套搜索表单 UI，业务模块只关心"我有哪些搜索字段"。

  风格：Options API（与 MoldSearchForm 完全一致，便于双系统代码复用）
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
import BaseSearchForm from '@/components/BaseSearchForm.vue'
import { projectStatusOptions, projectSourceOptions } from '@/constants/project-const'

export default {
  name: 'ProjectSearchForm',
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        project_code: null,
        project_name: null,
        status: null,
        source: null,
        initiator: null,
        project_manager: null,
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [
        // 基础项（始终显示，与 MoldSearchForm 风格一致：4 字 label）
        { label: '项目编号', prop: 'project_code', type: 'input', level: 'basic' },
        { label: '项目名称', prop: 'project_name', type: 'input', level: 'basic' },
        { label: '项目状态', prop: 'status', type: 'select', level: 'basic', options: projectStatusOptions },
        { label: '项目来源', prop: 'source', type: 'select', level: 'basic', options: projectSourceOptions },
        // 高级项（需要展开）
        { label: '客户名称', prop: 'initiator', type: 'input', level: 'advanced' },
        { label: '项目经理', prop: 'project_manager', type: 'input', level: 'advanced' },
      ]
    }
  },
  methods: {
    /**
     * 处理搜索
     */
    handleSearch() {
      this.$emit('search')
    },

    /**
     * 处理重置
     */
    handleReset() {
      this.$emit('reset')
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
