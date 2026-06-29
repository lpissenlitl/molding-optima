<template>
  <div>
    <query-injection-machine-list
      ref="queryInjectionMachineList"
      :query-detail="query"
      @queryStart="listLoading = true"
      @queryFinish="onQueryFinish"
    >
    </query-injection-machine-list>
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
        <!-- <el-button-group> -->
        <el-button
          type="primary"
          size="mini"
          icon="el-icon-plus"
          @click="addMachine"
          :disabled="!$store.state.user.userinfo.permissions.includes('add_machine')"
        >
          添加机器
        </el-button>
        <el-button
          size="mini"
          type="primary"
          icon="el-icon-document-copy"
          style="margin: 0"
          @click="copyMachine"
          :disabled="!$store.state.user.userinfo.permissions.includes('add_machine')"
        >
          复制机器
        </el-button>
        <el-upload 
          style="display:inline-block" 
          action="" 
          :show-file-list="false" 
          :http-request="uploadMachineFromExcel"
        >
          <el-button 
            type="primary" 
            size="mini" 
            icon="el-icon-folder-opened"
            :disabled="!$store.state.user.userinfo.permissions.includes('add_machine')"
          >
            导入机器
          </el-button>
        </el-upload>
        <el-button
          size="mini" 
          type="success"
          icon="el-icon-document"
          @click="exportMachineToExcel" 
        >
          导出机器
        </el-button>
        <el-button
          type="danger"
          size="mini"
          icon="el-icon-delete"
          @click="deleteMachine"
          style="margin: 0"
          :disabled="!$store.state.user.userinfo.permissions.includes('delete_machine')"
        >
          删除机器
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
          @click="setTableView"
          icon="el-icon-setting"
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
      :height="tableHeight"
      :row-style="tableRowStyle"
      :cell-style="tableCellStyle"
      :header-cell-style="tableHeaderStyle"
      :data="listData.items"
      @sort-change="sortList"
      @row-dblclick="rowDoubleClicked"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="40"
        align="center"
      >
      </el-table-column>
      <el-table-column
        type="index"
        label="序号"
        width="45"
        align="center"
      >
      </el-table-column>
      <el-table-column
        v-for="column, index in columns_setting.filter(column => column.visible)"
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
          <div v-if="column.prop === 'trademark'">
            <el-button 
              type="text" 
              size="mini"            
              @click="editMachine(scope.row)"
            >
              {{ scope.row[column.prop] }}
            </el-button>
          </div>
          <div v-else>
            {{ scope.row[column.prop] }}
          </div>
        </template>
      </el-table-column>
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
    <el-dialog 
      v-el-drag-dialog
      width="80%"
      center
      :visible.sync="show_dialog" 
      :modal="true"
      :append-to-body="true"
      :close-on-click-modal="false"
      :lock-scroll="true"
    >
      <div slot="title" class="header-title">
        <div style="font-size:25px; font-weight:bold">
          {{ current_item.title }}
        </div>
      </div>
      <create-injection-machine 
        ref="machineCreate"
        :id="current_item.id"
        :view-type="current_item.view_type"
        :excel-data="current_item.excel_data"
        @close="refreshView"
      >
      </create-injection-machine>
    </el-dialog>
    <table-setting
      :table-data="columns_setting"
      :show-dialog.sync="showTableSetting"
      @close="refreshTable"
    >
    </table-setting>
  </div>
</template>

<script>
import { machineMethod, importMachine, importBatch, exportMachineById } from "@/api"
import { AppModule } from "@/store/modules/app"
import { UserModule } from "@/store/modules/user"
import { getFullReportUrl } from "@/utils/assert"
import QueryInjectionMachineList from "./components/QueryInjectionMachineList.vue"
import CreateInjectionMachine from "./CreateInjectionMachine.vue"
import TableSetting from "@/components/tableSetting/tableSetting"

export default {
  components: { QueryInjectionMachineList, CreateInjectionMachine, TableSetting },
  data() {
    return {
      query: {
        company_id: UserModule.company_id,

        data_source: null,
        trademark: "",
        serial_no: "",
        manufacturer: "",
        machine_type: null,
        power_method: null,
        propulsion_axis: null,

        page_no: 1,
        page_size: 100
      },
      current_item: {
        id: null,
        title: "新增机器",
        view_type: null,
        excel_data: null
      },
      viewType: null,
      excelData: null,
      listData: {},
      listLoading: false,
      multipleSelection: [],
      columns_setting: [
        { visible: true, label: "ID", prop: "id", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "注塑机品牌", prop: "manufacturer", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "注塑机型号", prop: "trademark", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "设备编码", prop: "serial_no", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "资产编号", prop: "asset_no", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "最大注射重量", prop: "max_injection_weight", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "最大注射速度", prop: "max_injection_velocity", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "最大注射行程", prop: "max_injection_stroke", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "最大注射压力", prop: "max_injection_pressure", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "最大保压压力", prop: "max_holding_pressure", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "最大螺杆转速", prop: "max_screw_rotation_speed", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "塑化能力", prop: "plasticizing_capacity", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "螺杆直径", prop: "screw_diameter", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "出厂日期", prop: "manufacture_date", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      tableHeaderStyle: { "background-color": "lightblue", "color": "#000", "font-size": "12px", "padding": "10px 0px" },
      tableRowStyle: { },
      tableCellStyle: { "padding": "7px 0px" },
      tableHeight: "45rem",
      show_dialog: false,
      showMachineDetail: false,
      showTableSetting: false, // 显示表格设置界面
      downloaded: 0
    }
  },
  watch: {
    "columns_setting": {
      handler: function() {
        let custom_setting = AppModule.customSetting
        custom_setting.user_id = UserModule.id
        custom_setting.mac_list_columns_setting = this.columns_setting
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
      if (custom_setting && custom_setting.mac_list_columns_setting) {
        if (custom_setting.id == UserModule.id) {
          this.columns_setting = custom_setting.mac_list_columns_setting
        }
      }
    },
    getListData() {
      this.$refs.queryInjectionMachineList.getListData()
    },
    onQueryFinish(machineList) {
      this.listData = machineList
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
    addMachine() {
      this.$router.push("/machine/injection/create")
    },
    copyMachine() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请从模具列表中选择一条机器信息进行复制！")
        return
      }

      this.$confirm(`确认复制以下机器？\r\n ${ this.multipleSelection[0].trademark }`, "复制机器", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.current_item.id = this.multipleSelection[0].id
        this.viewType = "copy"
        this.showMachineDetail = true
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消复制！",
        })
      })
    },
    uploadMachineFromExcel(data) {
      let params = new FormData()
      params.append("file", data.file)
      importMachine(params).then(res => {
        if (res.data.error_message !== "") {
          this.$message({
            showClose: true,
            message: res.data.error_message,
            type: "error", 
            duration: 0,
            dangerouslyUseHTMLString: true
          })
        }
        // 没有错误信息，才打开机器的模板
        else {
          this.current_item.id = null
          this.showMachineDetail = true
          this.viewType = "upload"
          this.excelData = res.data.machine
        }
      })
      return 0
    },
    exportMachineToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请从模具列表中选择一条机器信息进行导出！")
        return
      }

      this.$confirm(`确认导出以下机器？\r\n ${ this.multipleSelection[0].trademark }`, "导出机器", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        exportMachineById(this.multipleSelection[0].id)
          .then(res => {
            if (res.status === 0 && res.data.url) {
              this.$message({ message: "导出成功。", type: "success" })
              window.location.href = getFullReportUrl(res.data.url)
            }
          })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消导出",
        })
      })
    },
    uploadTemplate(data) {
      let params = new FormData()
      params.append("file", data.file)
      importBatch(params, "report", UserModule.company_id).then(res=>{
        if (res.status === 0){
          this.$message({ message:"上传成功",type:"success" })
        } else {
          this.$message({ message:"上传失败",type:"error" })
        }
      })
      // .finally(()=> this.uploadingID = null)
      return 0
    },
    deleteMachine() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }
      
      let delete_machine = ""
      let machine_trademark_list = []
      let machine_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        machine_trademark_list.push(this.multipleSelection[i].trademark)
        machine_id_list.push(this.multipleSelection[i].id)
      }
      delete_machine = machine_trademark_list.join("、")

      this.$confirm(`确认删除以下机器？\r\n ${ delete_machine }`, "删除模具", {
        confirmButtonText: "确定",        
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        machineMethod.multipleDel({
          "machine_id_list": machine_id_list
        }).then((res) => {
          if (res.status === 0){
            this.$message({ type: "success", message: "删除成功!" })
            this.getListData()
          }
        })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消删除"
        })
      })
    },
    exportListToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项。")
        return
      }

      let machine_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        machine_id_list.push(this.multipleSelection[i].id)
      }
      machineMethod.multipleHandle({
        "machine_id_list": machine_id_list,
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
      this.current_item.id = null
      this.viewType = null
      this.excelData = null
      this.showTableSetting = false

      this.getListData()
    },
    sortList(sort) {
      this.query.$orderby = sort.prop
      this.listLoading = true
      this.getListData()
    },
    handleSelectionChange(val) {
      this.multipleSelection = val
    },
    editMachine(row) {
      this.current_item.id = row.id
      this.viewType = "edit"
      this.showMachineDetail = true
    },
    rowDoubleClicked(row) {
      this.editMachine(row)
    },
    refreshView() {
      this.current_item.id = null
      this.viewType = null
      this.excelData = null
      this.showMachineDetail = false

      this.getListData()
    },
    handleSizeChange(val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange (val) {
      this.query.page_no = val
      this.getListData()
    },
  }
}
</script>
