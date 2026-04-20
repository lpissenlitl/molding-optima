<template>
  <div>
    <el-table
      :data="table_data"
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      :cell-style="tableCellStyle"
      :header-cell-style="tableHeaderStyle"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="40"
      >
      </el-table-column>
      <el-table-column prop="defect_name" label="缺陷" align="center"></el-table-column>
      <el-table-column prop="product_small_type" label="制品类别" align="center">
      </el-table-column>
      <el-table-column prop="polymer_abbreviation" label="塑料简称" align="center">
      </el-table-column>
      <el-table-column prop="rule_description" label="规则详情" min-width="250" align="left">
      </el-table-column>
      <el-table-column prop="rule_explanation" label="规则解释" min-width="280" align="left">
      </el-table-column>
      <el-table-column prop="rule_type" label="规则类型" align="center">
      </el-table-column>
      <el-table-column prop="subrule_no" label="规则库编号" align="center">
      </el-table-column>
    </el-table>
    <div style="display: flex;justify-content: center; align-items: center;padding:10px 20px;">
      <el-button 
        type="success"
        size="small"
        @click="executeRule()"
      >
        执行该子规则
      </el-button>
      <el-button 
        type="primary"
        size="small"
        @click="executeRule()"
      >
        关闭
      </el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: "CheckDetails",
  props: {
    tabData: {
      type: Array,
      default: []
    }
  },
  data() {
    return {
      table_data: this.tabData,
      tableHeaderStyle: {
        "background-color": "lightblue",
        color: "#000",
        "font-size": "12px",
        padding: "8px 0px",
      },
      tableCellStyle: { padding: "7px 0px" },
      multipleSelection:[]
    };
  },
  methods: {
    handleSelectionChange(val) {
      this.multipleSelection = val
    },
    executeRule(){
      this.$emit("execute", this.multipleSelection)
    },
  },
  watch: {
    tabData() {
      this.table_data = this.tabData
    }
  }
};
</script>

<style>
</style>