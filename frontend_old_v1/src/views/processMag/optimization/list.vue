<template>
  <div>
    <query-optimize-list
      ref="queryOptimizeList"
      :query-detail="query"
      @queryStart="listLoading = true"
      @queryFinish="onQueryFinish"
    >
    </query-optimize-list>
    <div class="row-toolbutton">
      <div style="float:left">
        <el-button-group>
          <el-button
            size="mini"
            @click="changeTableSize('small')"
          >
            small
          </el-button>
          <el-button
            size="mini"
            @click="changeTableSize('normal')"
          >
            normal
          </el-button>
          <el-button
            size="mini"
            @click="changeTableSize('large')"
          >
            large
          </el-button>
        </el-button-group>
      </div>
      <div style="float:right">
        <el-button-group>
          <el-button
            size="mini"
            type="primary"
            icon="el-icon-plus"
            @click="addProcessOptimize"
          >
            优化工艺
          </el-button>
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
            @click="setTableView"
          >
            配置表格
          </el-button>
        </el-button-group>
      </div>
    </div>
    <div style="height: 8px" />
    <el-table
      v-loading="listLoading"
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      style="width: 100%"
      :data="listData.items"
      :height="tableHeight"
      :row-style="tableRowStyle"
      :cell-style="tableCellStyle"
      :header-cell-style="tableHeaderStyle"
      @sort-change="sortList"
      @row-dblclick="rowDoubleClicked"
      @selection-change="handleSelectionChange"
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
        width="45"
        align="center"
      >
      </el-table-column>
      <template v-for="column, index in columns_setting">
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
          <template slot-scope="scope">
            <span v-if="column.prop === 'product_serial'">
              {{ scope.row[column.prop] }}
            </span>
            <span v-else-if="column.prop === 'process_optimization'">
              <el-link
                type="primary" 
                @click="editProcessOptimization(scope.row)"
              >
                查看
              </el-link>
            </span>
            <span v-else-if="column.prop === 'report'">
              <el-link
                type="primary" 
                @click="exportProcessOptimization(scope.row)"
              >
                导出
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
        :total="listData.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
    <process-optimize-detail
      :id="process_detail.id"
      :view-type="viewType"
      :show-update.sync="showProcessOptimizeDetail"
      @close="refreshView"
    >
    </process-optimize-detail>
    <table-setting
      :table-data="columns_setting"
      :show-dialog.sync="showTableSetting"
      @close="refreshTable"
    >
    </table-setting>
  </div>
</template>

<script>
import { processIndexMethod } from "@/api"
import { AppModule } from "@/store/modules/app"
import { UserModule } from "@/store/modules/user"
import { getFullReportUrl } from "@/utils/assert"
import QueryOptimizeList from "./subView/queryOptimizeList.vue"
import ProcessOptimizeDetail from "./detail.vue"
import TableSetting from "@/components/tableSetting/tableSetting"

export default {
  name: "ProcessOptimizeList",
  components: { QueryOptimizeList, ProcessOptimizeDetail, TableSetting },
  data() {
    return {
      query: {
        company_id : UserModule.company_id,
        status: 1,

        mold_no: null,
        gate_type: null,
        product_type: null,
        product_name: null,
        machine_data_source: null,
        machine_trademark: null,
        start_date: null,
        end_date: null,
        
        page_no: 1 ,
        page_size: 100,
      },
      process_detail: {
        id: null,
      },
      viewType: null,
      listData: {},
      listLoading: false,
      multipleSelection: [],
      columns_setting: [
        { visible: true, label: "ID", prop: "id", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具编号", prop: "mold_no", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "制品编号", prop: "product_no", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
        // { visible: true, label: "来源", prop: "status", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "记录", prop: "process_optimization", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "调机报告", prop: "report", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品类别", prop: "product_type", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "制品名称", prop: "product_name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true },
        { visible: true, label: "型腔数", prop: "cavity_num", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "注塑机型号", prop: "machine_trademark", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "设备编码", prop: "machine_serial_no", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料简称", prop: "polymer_abbreviation", width: 90, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "流道长度", prop: "runner_length", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "流道重量", prop: "runner_weight", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "浇口类别", prop: "gate_type", width: 70, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "浇口数量", prop: "gate_num", width: 70, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "浇口形状", prop: "gate_shape", width: 70, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品总重量", prop: "product_total_weight", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品平均壁厚", prop: "product_ave_thickness", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品最大壁厚", prop: "product_max_thickness", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品流长", prop: "product_max_length", width: 70, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "创建日期", prop: "created_at", width: 130, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      tableHeaderStyle: { "background-color": "lightblue", "color": "#000", "font-size": "12px", "padding": "10px 0px" },
      tableRowStyle: { },
      tableCellStyle: { "padding": "7px 0px" },
      tableHeight: "45rem",
      showProcessOptimizeDetail: false,
      showTableSetting: false,
    }
  },
  watch: {
    "columns_setting": {
      handler: function() {
        let custom_setting = AppModule.customSetting
        custom_setting.user_id = UserModule.id
        custom_setting.process_optimize_list_columns_setting = this.columns_setting
        localStorage.setItem("custom_setting", JSON.stringify(custom_setting))
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
      let custom_setting = AppModule.customSetting
      if (custom_setting && custom_setting.process_optimize_list_columns_setting) {
        if (custom_setting.id == UserModule.id) {
          this.columns_setting = custom_setting.process_optimize_list_columns_setting
        }
      }
    },
    getListData() {
      this.$refs.queryOptimizeList.queryListData()
    },
    onQueryFinish(optimizeList) {
      this.listData = optimizeList
      this.listLoading = false
    },
    changeTableSize(size) {
      if (size === "small") {
        this.tableCellStyle = { "padding": "1px 0px" }
      } else if (size === "normal") {
        this.tableCellStyle = { "padding": "7px 0px" }
      } else if (size === "large") {
        this.tableCellStyle = { "padding": "12px 0px" }
      } else {
        
      }
    },
    addProcessOptimize() {
      this.$router.push({
        path: "/process/optimize/create",
      })
    },
    deleteProcessOptimize() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项。")
        return
      }
      let delete_process = ""
      let process_no_list = []
      let process_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        process_no_list.push(this.multipleSelection[i].process_no)
        process_id_list.push(this.multipleSelection[i].id)
      }
      delete_process = process_no_list.join("、")
      this.$confirm(`确认删除以下工艺记录？\r\n ${ delete_process }`, "删除工艺", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        processIndexMethod.multipleDel({
          "process_id_list": process_id_list
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
    exportListToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项。")
        return
      }
      let process_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        process_id_list.push(this.multipleSelection[i].id)
      }
      processIndexMethod.multipleHandle({
        "process_id_list": process_id_list,
        "flag": "export_list"
      }).then(res => {
        if (res.status === 0 && res.data.url) {
          window.location.href = getFullReportUrl(res.data.url)
        }
      })
    },
    setTableView() {
      this.showTableSetting = true
    },
    refreshTable() {
      this.process_detail.id = null
      this.viewType = null
      this.showTableSetting = false

      this.getListData()
    },
    sortList(sort) {
      this.query.$orderby = sort.prop
      this.getListData()
    },
    setRowSelectable(row, index) {
      // if (this.$store.state.user.userinfo.permissions.includes('project_delete')) {
      //   return true;
      // } else {
      //   return false;
      // }
      return true
    },
    handleSelectionChange(val) {
      this.multipleSelection = val
    },
    editProcessOptimization(row) {
      this.process_detail.id = row.id
      this.viewType = "edit"
      this.showProcessOptimizeDetail = true
    },
    exportProcessOptimization(row){
      processIndexMethod.multipleHandle({
        "process_id_list": [row.id],
        "flag": "export_report"
      }).then(res => {
        if (res.status === 0 && res.data.url) {
          window.location.href = getFullReportUrl(res.data.url)
        }
      })
    },
    rowDoubleClicked(row) {
      this.editProcessOptimization(row)
    },
    refreshView() {
      this.process_detail.id = null
      this.viewType = null
      this.showProcessOptimizeDetail = false

      this.getListData()
    },
    handleSizeChange(val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange(val) {
      this.query.page_no = val
      this.getListData()
    },
  }
}
</script>

<style>

</style>
