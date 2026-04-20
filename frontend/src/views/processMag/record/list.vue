<template>
  <div>
    <query-record-list
      ref="queryRecordList"
      :query-detail="query"
      @queryStart="listLoading = true"
      @queryFinish="onQueryFinish"
    >
    </query-record-list>
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
        <el-button
          size="mini"
          type="primary"
          icon="el-icon-plus"
          @click="addProcessRecord"
        >
          录入工艺
        </el-button>
        <el-button
          size="mini"
          type="primary"
          icon="el-icon-document-copy"
          style="margin: 0"
          @click="copyProcessRecord"
        >
          复制工艺
        </el-button>

        <el-button
          size="mini" 
          type="success"
          icon="el-icon-document"
          @click="exportProcessRecordToExcel" 
          style="margin: 0"
        >
          导出工艺
        </el-button>
        <el-button 
          size="mini" 
          type="danger" 
          icon="el-icon-delete"
          @click="deleteProcessRecord" 
          style="margin: 0"
        >
          删除记录
        </el-button>
        <el-button
          size="mini"
          type="success"
          icon="el-icon-download"
          @click="exportListToExcel"
          style="margin: 0"
        >
          导出列表
        </el-button>
        <el-button
          size="mini"
          type="primary"
          icon="el-icon-setting"
          @click="setTableView"
          style="margin: 0"
        >
          配置表格
        </el-button>
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
            <span v-if="column.prop === 'process_no'">
              <el-link
                type="primary"
                @click="editProcessRecord(scope.row)"
              >
                {{ scope.row[column.prop] }}
              </el-link>
            </span>
            <span v-else-if="column.prop === 'process_optimize'">
              <el-link
                type="primary"
                @click="toProcessOptimizeView(scope.row)"
              >
                优化
              </el-link>
            </span>
            <span v-else-if="column.prop === 'expert_optimize'">
              <el-link
                type="primary"
                @click="toExpertOptimizeView(scope.row)"
              >
                专家调优
              </el-link>
            </span>       
            <span v-else-if="column.prop === 'data_sources'">
              <span v-if="scope.row[column.prop]=='试模参数'">
                {{ scope.row["mold_trials_no"] }}
              </span>
              <span v-else>
                {{ scope.row[column.prop] }}
              </span>
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
    <process-record-detail
      :id="process_detail.id"
      :view-type="viewType"
      :excel-data="excelData"
      :show-update.sync="showProcessRecordDetail"
      @close="refreshView"
    >
    </process-record-detail>
    <table-setting
      :table-data="columns_setting"
      :show-dialog.sync="showTableSetting"
      @close="refreshTable"
    >
    </table-setting>
  </div>
</template>

<script>
import { processIndexMethod, importProcess, exportProcessById } from "@/api"
import { AppModule } from "@/store/modules/app"
import { UserModule } from "@/store/modules/user"
import { getFullReportUrl } from "@/utils/assert"
import QueryRecordList from "./subView/queryRecordList.vue"
import ProcessRecordDetail from "./detail.vue"
import TableSetting from "@/components/tableSetting/tableSetting"

export default {
  name: "ProcessRecordList",
  components: { QueryRecordList, ProcessRecordDetail, TableSetting },
  data() {
    return {
      query: {
        company_id: UserModule.company_id,
        status: 2,

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
      excelData: null,
      listData: {},
      listLoading: false,
      columns_setting: [
        { visible: true, label: "ID", prop: "id", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具编号", prop: "mold_no", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "工艺编号", prop: "process_no", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "数据来源", prop: "data_sources", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "工艺优化", prop: "process_optimize", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "专家调优", prop: "expert_optimize", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "制品编号", prop: "product_no", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
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
      showProcessRecordDetail: false,
      showTableSetting: false,
    }
  },
  watch: {
    "columns_setting": {
      handler: function() {
        let custom_setting = AppModule.customSetting
        custom_setting.user_id = UserModule.id
        custom_setting.process_record_list_columns_setting = this.columns_setting
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
      if (custom_setting && custom_setting.process_record_list_columns_setting) {
        if (custom_setting.id == UserModule.id) {
          this.columns_setting = custom_setting.process_record_list_columns_setting
        }
      }
    },
    getListData() {
      this.$refs.queryRecordList.queryListData()
    },
    onQueryFinish(recordList) {
      this.listData = recordList
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
    addProcessRecord() {
      this.$router.push({
        path: "/process/record/create",
      })
    },
    copyProcessRecord() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请从工艺列表中选择一条工艺信息进行复制！")
        return
      }

      this.$confirm(`确认复制以下工艺？\r\n ${ this.multipleSelection[0].process_no }`, "复制工艺", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.process_detail.id = this.multipleSelection[0].id
        this.viewType = "copy"
        this.showProcessRecordDetail = true
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消复制！",
        })
      })
    },
    uploadProcessRecordFromExcel(data) {
      let params = new FormData()
      params.append("file", data.file)
      importProcess(params).then(res => {
        this.process_detail.id = null
        this.viewType = "upload"
        this.showProcessRecordDetail = true
        this.excelData = res.data.process_record

        if (res.data.error_message !== "") {
          this.$message({
            showClose: true,
            message: res.data.error_message,
            type: "error", 
            duration: 0,
            dangerouslyUseHTMLString: true
          })
        }
      })
      return 0
    },
    exportProcessRecordToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项。")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请选中一条进行导出")
        return
      }

      this.$confirm(`确认导出以下工艺？\r\n ${ this.multipleSelection[0].process_no }`, "导出工艺", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        exportProcessById(this.multipleSelection[0].id)
          .then(res => {
            if (res.status === 0 && res.data.url) {
              this.$message({ message: "导出成功。", type: "success" })
              window.location.href = getFullReportUrl(res.data.url)
            }
          })
      }).catch((error) => {
        this.$message({
          type: "info",
          message: "已取消导出",
        })
      })
    },
    deleteProcessRecord() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
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

      this.$confirm(`确认删除以下工艺记录？\r\n ${ delete_process }`, "删除工艺记录", {
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
        this.$message("无选中项！")
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
      this.excelData = null
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
    editProcessRecord(row) {
      this.process_detail.id = row.id
      this.viewType = "edit"
      this.showProcessRecordDetail = true
    },
    rowDoubleClicked(row) {
      this.editProcessRecord(row)
    },
    refreshView() {
      this.process_detail.id = null
      this.viewType = null
      this.excelData = null
      this.showProcessRecordDetail = false

      this.getListData()
    },
    toProcessOptimizeView(row) {
      this.$router.push({
        path: "/process/optimize/create",
        query: {
          process_id: row.id
        }
      })
    },
    toExpertOptimizeView(row) {
      this.$router.push({
        path: "/process/optimize/expert_record",
        query: {
          process_id: row.id
        }
      })
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

