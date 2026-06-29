<template>
  <el-dialog
    class="settingDialog"
    v-el-drag-dialog
    :visible.sync="show"
    :modal="true"
    :append-to-body="true"
    :close-on-click-modal="false"
    :lock-scroll="true"
    @opened="setDragTable"
    @close="refreshTableView"
  >
    <el-table
      :data="tableList"
      style="width: 100%"
      border
      size="mini"
    >
      <el-table-column
        label="显示"
        width="80"
        align="center"
      >
        <template slot-scope="scope">
          <el-checkbox v-model="tableList[scope.$index].visible"></el-checkbox>
        </template>
      </el-table-column>
      <el-table-column
        label="字段名称"
        min-width="380"
        header-align="center"
      >
        <template slot-scope="scope">
          <span>{{ tableList[scope.$index].label }}</span>
          <span></span>
        </template>
      </el-table-column>
      <el-table-column
        prop="address"
        label="列宽"
        align="center"
        width="120"
      >
        <template slot-scope="scope">
          <el-input
            size="mini"
            v-model="tableList[scope.$index].width"
          >
            <span slot="suffix">px</span>
          </el-input>
        </template>
      </el-table-column>
    </el-table>
  </el-dialog>
</template>

<script>
import Sortable from 'sortablejs'

export default {
  name: "TableSetting",
  data() {
    return {
      tableList: [],
      show: this.showDialog
    }
  },
  props: {
    showDialog: {
      type: Boolean,
      default: false
    },
    tableData: {
      type: Array,
      default: () => {
        return []
      }
    }
  },
  created() {

  },
  mounted() {
    this.initTableList();
  },
  methods: {
    initTableList() {
      this.tableList = []
      for (let i = 0; i < this.tableData.length; ++i) {
        this.tableList.push(this.tableData[i])
      }
      this.$set(this.tableList)
    },
    setDragTable() {
      this.rowDrop();
    },
    rowDrop() {
      // 此时找到的元素是要拖拽元素的父容器
      const tables = document.querySelector(".settingDialog .el-dialog__body");
      const tbody = tables.getElementsByTagName("tbody").item(0)
      let _this = this;
      Sortable.create(tbody, {
      // 指定父元素下可被拖拽的子元素
        draggable: ".el-table__row",
          onEnd ({ newIndex, oldIndex }) {
            const currRow = _this.tableData.splice(oldIndex, 1)[0];
            _this.tableData.splice(newIndex, 0, currRow);
          }
      });
    },
    refreshTableView() {
      this.$emit("close")
    }
  },
  watch: {
    showDialog() {
      this.show = this.showDialog
    },
  }
}
</script>

<style>

</style>