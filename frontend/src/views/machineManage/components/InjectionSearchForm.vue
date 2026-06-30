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
  name: "InjectionSearchForm",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({  
        location: null,
        brand: null,
        model: null,
        device_no: null,
        asset_no: null,
        machine_type: null,
        drive_system: null, 
      })
    }
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: this.queryDetail,
      search_items: [
        { 
          label: "品牌", 
          prop: "brand", 
          type: "autocomplete",
          query: { table: "injection_molding_machine", column: "brand" } 
        },
        { 
          label: "型号", 
          prop: "model", 
          type: "autocomplete",
          query: { table: "injection_molding_machine", column: "model" } 
        },
        { 
          label: "设备位置", 
          prop: "location", 
          type: "autocomplete",
          query: { table: "injection_molding_machine", column: "location" } 
        },
        { 
          label: "设备类型", 
          prop: "machine_type", 
          type: "autocomplete",
          query: { table: "injection_molding_machine", column: "machine_type" } 
        },
        { 
          label: "驱动系统", 
          prop: "drive_system", 
          type: "autocomplete",
          query: { table: "injection_molding_machine", column: "drive_system" } 
        }
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
