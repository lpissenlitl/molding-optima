<template>
  <div>
    <query-optimize-list
      ref="queryOptimizeList"
      :query-detail="query"
      @queryStart="list_loading = true"
      @queryFinish="onQueryFinish"
    >
    </query-optimize-list>
    <div class="row-toolbutton">
      <div style="float:left">
        <change-table-size :table-style="table_style" />
      </div>
      <div style="float:right">
        <el-button-group>
          <el-button 
            size="mini" 
            type="danger" 
            icon="el-icon-delete"
            @click="deleteProcessOptimize" 
          >
            删除记录
          </el-button>
          <el-button
            size="mini"
            type="success"
            icon="el-icon-download"
            @click="exportListToExcel"
          >
            导出列表
          </el-button>
          <el-button
            size="mini"
            type="primary"
            icon="el-icon-setting"
            @click="show_table_setting = true"
          >
            配置表格
          </el-button>
        </el-button-group>
      </div>
    </div>
    <div style="height: 8px" />
    <el-table
      v-loading="list_loading"
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      style="width: 100%"
      :data="list_data.items"
      :height="table_style.height"
      :row-style="table_style.row_style"
      :cell-style="table_style.cell_style"
      :header-cell-style="table_style.header_style"
      @row-dblclick="rowDoubleClicked"
      @selection-change="onSelectionChange"
    >
      <el-table-column
        type="selection"
        width="40"
        :selectable="setRowSelectable"
      >
      </el-table-column>
      <el-table-column
        type="index"
        label="序号"
        width="55"
        align="center"
      >
      </el-table-column>
      <template v-for="column, index in table_columns">
        <el-table-column
          v-if="column.visible"
          :key="index"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width"
          :header-align="column.header_align"
          :align="column.align"
          :sortable="column.sortable"
          :show-overflow-tooltip="column.tooltip"
        >
          <template #default="scope">
            <span v-if="column.prop === 'process_no'">
              <el-link
                type="primary"
                @click="updateProcessOptimization(scope.row)"
              >
                {{ scope.row[column.prop] }}
              </el-link>
            </span>
            <span v-else>
              {{ scope.row[column.prop] }}
            </span>
          </template>
        </el-table-column>
      </template>
    </el-table>
    <div class="pagination">
      <el-pagination
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="query.page_no"
        :page-sizes="$store.state.app.pageSizeArray"
        :page-size="query.page_size"
        :total="list_data.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
    <process-optimize-detail
      :view-context="view_context"
      :show-update.sync="show_update"
      @close="refreshView"
    >
    </process-optimize-detail>
    <table-setting
      :table-data="table_columns"
      :show-dialog.sync="show_table_setting"
      @close="refreshTable"
    >
    </table-setting>
  </div>
</template>

<script>
import { processIndexMethod, exportListData } from "@/api"
import { UserModule } from "@/store/modules/user"
import { getReportDownloadUrl } from "@/utils/assert"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import QueryOptimizeList from "./subView/queryOptimizeList.vue"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import ProcessOptimizeDetail from "./detail.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"

export default {
  name: "ProcessOptimizeList",
  components: { 
    QueryOptimizeList, 
    ChangeTableSize,
    ProcessOptimizeDetail, 
    TableSetting 
  },
  data() {
    return {
      query: {
        operation: "-created_at",
        company_id : UserModule.company_id,
        organization_id: UserModule.organization_id,
        deleted: 0,
        
        status: 1,
        type: "optimize",
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
        
        page_no: 1 ,
        page_size: 100,
      },
      list_data: {},
      list_loading: false,
      selected_rows: [],
      view_context: {
        id: null,
        is_dialog: null,
        dialog_title: null,
        mode: null,
        excel_data: null,
      },
      table_columns: [
        { visible: true, label: "工艺编号", prop: "process_no", width: 160, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具编号", prop: "mold_no", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具类别", prop: "mold_type", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具名称", prop: "mold_name", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "型腔数", prop: "cavity_num", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "注塑周期(s)", prop: "inject_cycle_require", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品类别", prop: "product_type", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "制品名称", prop: "product_name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true },
        { visible: true, label: "制品编号", prop: "product_no", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "总注射重量(g)", prop: "product_total_weight", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "注塑机品牌", prop: "mac_manufacturer", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机型号", prop: "mac_trademark", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机编号", prop: "mac_serial_no", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机位置", prop: "mac_data_source", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机类型", prop: "mac_machine_type", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料厂商", prop: "polys_manufacturer", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料简称", prop: "polys_abbreviation", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料牌号", prop: "polys_trademark", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料类别", prop: "polys_category", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "创建日期", prop: "created_at", width: 170, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      table_style: {
        height: "45rem",
        header_style: { "background-color": "lightblue", "color": "#000", "font-size": "var(--basic-font-size)", "padding": "10px 0px" },
        row_style: {},
        cell_style: { "padding": "7px 0px" },
      },
      show_update: false,
      show_table_setting: false,
    }
  },
  watch: {
    "table_columns": {
      handler: function() {
        saveColumnsSetting("process_optimize_list_col_config", this.table_columns)
      },
      deep: true
    },
  },
  created() {
    this.loadViewSetting()
  },
  mounted() {
    this.getListData()
  },
  methods: {
    loadViewSetting() {
      let table_columns = loadColumnsSetting("process_optimize_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    getListData() {
      this.$refs.queryOptimizeList.queryListData()
    },
    onQueryFinish(list_data) {
      this.list_data = list_data
      this.list_loading = false
    },
    deleteProcessOptimize() {
      if (this.selected_rows.length == 0) {
        this.$message("无选中项。")
        return
      }
      let process_no_list = []
      let process_id_list = []
      for (let i = 0; i < this.selected_rows.length; ++i) {
        process_no_list.push(this.selected_rows[i].process_no)
        process_id_list.push(this.selected_rows[i].id)
      }
      let delete_process = process_no_list.join("、")
      this.$confirm(`确认删除以下工艺记录？\r\n ${ delete_process }`, "删除工艺记录", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        processIndexMethod.multipleUpdate({
          "process_id_list": process_id_list,
          "operation": "delete"
        }).then((res) => {
          if (res.status === 0) {
            this.$message({ type: "success", message: "删除成功!" })
            this.getListData()
          }
        })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消删除。",
        })
      })
    },
    async exportListToExcel() {
      if (this.selected_rows.length == 0) {
        return this.$message("无选中项。")
      }
      const ids = this.selected_rows.map(item => item.id)
      const res = await exportListData({ resource: "process_list", ids })
      if (res.status === 0 && res.data.url) {
        window.location.href = getReportDownloadUrl(res.data.url)
      }
    },
    refreshTable() {
      this.process_detail.id = null
      this.viewType = null
      this.show_table_setting = false

      this.getListData()
    },
    sortList(sort) {
      this.query.$orderby = sort.prop
      this.getListData()
    },
    setRowSelectable(row, index) {
      // if (this.$hasPermission('project_delete')) {
      //   return true;
      // } else {
      //   return false;
      // }
      return true
    },
    onSelectionChange(val) {
      this.selected_rows = val
    },
    updateProcessOptimization(row) {
      this.view_context = {
        id: row.id,
        is_dialog: true,
        dialog_title: "更新工艺信息",
        mode: "edit"
      }
      this.show_update = true
      this.show_table_setting = false
    },
    rowDoubleClicked(row) {
      this.updateProcessOptimization(row)
    },
    handleSizeChange(val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange(val) {
      this.query.page_no = val
      this.getListData()
    },
    refreshView() {
      this.view_context = {
        id: null,
        is_dialog: null,
        dialog_title: null,
        mode: null,
        excel_data: null,
      }
      this.show_update = false
      this.show_table_setting = false

      this.getListData()
    },
  }
}
</script>

<style>

</style>
