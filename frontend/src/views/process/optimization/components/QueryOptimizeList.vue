<template>
  <BaseSearchForm
    :query="query"
    :items="search_items"
    @search="handleSearch"
    @reset="handleReset"
  >
    <!-- 工艺优化日期 -->
    <template #optimize-date="{ query }">
      <el-form-item label="工艺优化日期">
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
import { processIndexMethod } from "@/api"

export default {
  name: "QueryOptimizeList",
  components: { BaseSearchForm },
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        mold_no: null,
        mold_type: null,
        product_type: null,
        product_name: null,
        mac_manufacturer: null,
        mac_trademark: null,
        mac_serial_no: null,
        mac_data_source: null,
        
        start_date: null,
        end_date: null,
      })
    }
  },
  data() {
    return {
      query: this.queryDetail,
      search_items: [
        { label: "模具编号", prop: "mold_no", type: "autocomplete", query: { table: "process", column: "mold_no" } },
        { label: "模具类别", prop: "mold_type", type: "autocomplete", query: { table: "process", column: "mold_type" } },
        { label: "制品类别", prop: "product_type", type: "autocomplete", query: { table: "process", column: "product_type" } },
        { label: "制品名称", prop: "product_name", type: "autocomplete", query: { table: "process", column: "product_name" } },
        { label: "注塑机品牌", prop: "mac_manufacturer", type: "autocomplete", query: {
          table: "machine", column: "manufacturer",
          filter_ref: "query",
          filter_columns: { data_source: "mac_data_source" }
        } },
        { label: "注塑机型号", prop: "mac_trademark", type: "autocomplete", query: {
          table: "machine", column: "trademark",
          filter_ref: "query",
          filter_columns: { data_source: "mac_data_source", manufacturer: "mac_manufacturer" }
        } },
        { label: "注塑机编号", prop: "mac_serial_no", type: "autocomplete", query: {
          table: "machine", column: "serial_no",
          filter_ref: "query",
          filter_columns: { data_source: "mac_data_source", manufacturer: "mac_manufacturer", trademark: "mac_trademark" }
        } },
        { label: "注塑机位置", prop: "mac_data_source", type: "autocomplete", query: { table: "machine", column: "data_source" } },
        // 日期范围占位符
        { slot_name: "optimize-date" },
      ],
      list_data: {
        items: [],
        total: 0
      },
    }
  },
  methods: {
    handleSearch() {
      this.queryListData()
    },
    handleReset() {
      this.query.page_no = 1
      this.queryListData()
    },
    queryListData() {
      this.$emit("queryStart")
      processIndexMethod.get(this.query)
        .then((res) => {
          if (res.status === 0) {
            this.list_data = res.data
          }
        })
        .finally(() => {
          this.$emit("queryFinish", this.list_data)
        })
    },
  }
}
</script>

<style lang="scss" scoped>

</style>
