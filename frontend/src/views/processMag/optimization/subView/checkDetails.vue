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
      :span-method="organize_table"
    >
      <el-table-column prop="category" label="" align="center">
      </el-table-column>
      <el-table-column prop="desc" label="" align="center"> </el-table-column>
      <el-table-column prop="set_value" label="设定值" align="center">
      </el-table-column>
      <el-table-column prop="actual_value" label="实际值" align="center">
      </el-table-column>
      <el-table-column prop="range" label="范围" align="center">
      </el-table-column>
      <el-table-column prop="result" label="判断" align="center">
      </el-table-column>
    </el-table>
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
    };
  },
  methods: {
    organize_table({ row, column, rowIndex, columnIndex }) {
      if (rowIndex === 0 && columnIndex === 0) {
        return [3, 1]
      } else if (rowIndex > 0 && rowIndex < 3 && columnIndex === 0) {
        return [0, 0]
      } else if (rowIndex === 3 && columnIndex === 0) {
        return [2, 1]
      } else if (rowIndex > 3 && rowIndex < 5 && columnIndex === 0) {
        return [0, 0]
      } else if (rowIndex === 5 && columnIndex === 0) {
        return [2, 1]
      } else if (rowIndex > 5 && rowIndex < 7 && columnIndex === 0) {
        return [0, 0]
      }
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