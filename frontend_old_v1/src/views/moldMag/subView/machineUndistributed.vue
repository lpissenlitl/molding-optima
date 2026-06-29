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
      <el-table-column type="selection" width="40"> </el-table-column>
      <el-table-column type="index" label="序号" width="45" align="center">
      </el-table-column>
      <template v-for="(column, index) in columns_setting">
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
    <div class="pagination">
      <el-pagination
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="query.page_no"
        :page-sizes="$store.state.app.pageSizeArray"
        :page-size="query.page_size"
        :total="listData.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
  </div>
</template>

<script>
export default {
  name: "MachineUndistributed",
  props: {
    macColumnsSetting: {
      type: Array,
      default: () => {
        [];
      },
    },
    macTableHeaderStyle: {
      type: Object,
      default: () => ({}),
    },
    macTableRowStyle: {
      type: Object,
      default: () => ({}),
    },
    macTableCellStyle: {
      type: Object,
      default: () => ({}),
    },
    tableHeight: {
      type: Number,
      default: 400,
    },
    queryDetail: {
      type: Object,
      default: () => ({}),
    },
    undistributedData: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      query: this.queryDetail,
      listData: this.undistributedData,
      listLoading: false,
      multipleSelection: [],
      columns_setting: this.macColumnsSetting,
      tableHeaderStyle: this.macTableHeaderStyle,
      tableRowStyle: this.macTableRowStyle,
      tableCellStyle: this.macTableCellStyle,
    };
  },
  mounted() {
  },
  methods: {
    getListData() {
      this.$emit("query-machine-list");
    },
    handleSizeChange(val) {
      this.query.page_size = val;
      this.getListData();
    },
    handleCurrentChange(val) {
      this.query.page_no = val;
      this.getListData();
    },
    handleSelectionChange(val) {
      this.multipleSelection = val;
    },
  },
  watch: {
    undistributedData() {
      this.listData = this.undistributedData;
    },
  },
};
</script>

<style>
</style>