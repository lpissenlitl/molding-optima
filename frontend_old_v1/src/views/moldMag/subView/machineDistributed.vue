<template>
  <div>
    <el-table
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      :data="listData.items"
      :height="tableHeight"
      :row-style="tableRowStyle"
      :cell-style="tableCellStyle"
      :header-cell-style="tableHeaderStyle"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="40"
      >
      </el-table-column>
      <el-table-column
        type="index"
        label="序号"
        width="45"
        align="center"
      >
      </el-table-column>
      <template v-for="column, index in columns_setting">
        <el-table-column
          v-if="column.visible"
          header-align="center"
          :key="index"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width"
          :align="column.align"
          :sortable="column.sortable"
          :show-overflow-tooltip="column.tooltip"
        >
        </el-table-column>
      </template>
    </el-table>
  </div>
</template>

<script>
export default {
  name: "MachineDistributed",
  props: {
    macColumnsSetting: {
      type: Array,
      default: () => {[]}
    },
    macTableHeaderStyle: {
      type: Object,
      default: () => ({})
    },
    macTableRowStyle: {
      type: Object,
      default: () => ({})
    },
    macTableCellStyle: {
      type: Object,
      default: () => ({})
    },
    tableHeight: {
      type: Number,
      default: 400
    },
    distributedData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      listData: this.distributedData,
      multipleSelection:[],
      columns_setting: this.macColumnsSetting,
      tableHeaderStyle: this.macTableHeaderStyle,
      tableRowStyle: this.macTableRowStyle,
      tableCellStyle: this.macTableCellStyle, 
    };
  },
  methods: {
    handleSelectionChange(val) {
      this.multipleSelection = val;
    },
  },
  watch: {
    distributedData() {
      this.listData = this.distributedData
    }
  }
};
</script>

<style>
</style>