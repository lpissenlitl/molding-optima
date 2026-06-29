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

<script>
import BaseSearchForm from "@/components/BaseSearchForm.vue"
import { processParameterMethod } from "@/api"

export default {
  name: "ParameterSearchForm",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        status: null,
        mold_no: null,
        machine_model: null,
        polymer_abbreviation: null,
        start_date: null,
        end_date: null,
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [
        { 
          label: "工艺状态", 
          prop: "status", 
          type: "select", 
          options: [] 
        },
        { 
          label: "模具编号", 
          prop: "mold_no", 
          type: "autocomplete", 
          query: { table: "mold", column: "mold_no" } 
        },
        { 
          label: "注塑机型号", 
          prop: "machine_model", 
          type: "autocomplete", 
          query: { table: "injection_molding_machine", column: "model" } 
        },
        { 
          label: "塑料简称", 
          prop: "polymer_abbreviation", 
          type: "autocomplete", 
          query: { table: "polymer", column: "abbreviation" } 
        },
        // 日期范围占位符
        { slot_name: "date-range" }
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
