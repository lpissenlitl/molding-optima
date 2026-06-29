<template>
  <div>
    <query-mold-list
      ref="queryMoldList"
      :query-detail="query"
      @queryStart="listLoading = true"
      @queryFinish="onQueryFinish"
    >
    </query-mold-list>

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
          size="mini"
          type="primary"
          icon="el-icon-plus"
          @click="addMold"
          :disabled="!$store.state.user.userinfo.permissions.includes('add_mold')"
        >
          新增模具
        </el-button>

        <el-button
          size="mini"
          type="primary"
          icon="el-icon-document-copy"
          style="margin: 0"
          @click="copyMold"
          :disabled="!$store.state.user.userinfo.permissions.includes('add_mold')"
        >
          复制模具
        </el-button>

        <el-upload 
          style="display:inline-block" 
          action="" 
          :show-file-list="false" 
          :http-request="uploadMoldFromExcel"
        >
          <el-button 
            type="primary" 
            size="mini" 
            icon="el-icon-folder-opened"
            :disabled="!$store.state.user.userinfo.permissions.includes('add_mold')"
          >
            导入模具
          </el-button>
        </el-upload>

        <el-button
          size="mini" 
          type="success"
          icon="el-icon-document"
          @click="exportMoldToExcel" 
        >
          导出模具
        </el-button>

        <el-button 
          size="mini" 
          type="danger" 
          icon="el-icon-delete"
          @click="deleteMold" 
          style="margin: 0"
          :disabled="!$store.state.user.userinfo.permissions.includes('delete_mold')"
        >
          删除模具
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
        align="center"
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
            <span v-if="column.prop === 'mold_no'">
              <el-link
                type="primary" 
                @click="editMold(scope.row)"
              >
                {{ scope.row[column.prop] }}
              </el-link>
            </span>

            <span v-else-if="column.prop === 'moldflow'">
              <el-link 
                type="primary" 
                size="mini"
                @click="checkMoldflow(scope.row)"
              >
                <span v-if="scope.row.moldflow">
                  查看
                </span>
                <span v-else>
                  上传
                </span>
              </el-link>
            </span>
            <span v-else-if="column.prop === 'adaption'">
              <el-link 
                type="primary" 
                size="mini"
                @click="checkAdaption(scope.row)"
              >                
                <span v-if="scope.row.adaption">
                  查看
                </span>
                <span v-else>
                  适配
                </span>
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

    <mold-detail
      :id="mold_detail.id"
      :view-type="viewType"
      :excel-data="excelData"
      :show-update.sync="showMoldDetail"
      @close="refreshView"
    >
    </mold-detail>

    <table-setting
      :table-data="columns_setting"
      :show-dialog.sync="showTableSetting"
      @close="refreshTable"
    >
    </table-setting>
  </div>
</template>

<script>
import { projectMethod, importMold, importBatch, exportMoldById } from "@/api"
import { AppModule } from "@/store/modules/app"
import { UserModule } from "@/store/modules/user"
import { ProjectsInfoModule } from "@/store/modules/projects"
import { getFullReportUrl } from "@/utils/assert"
import QueryMoldList from "@/views/moldMag/subView/queryMoldList.vue"
import MoldDetail from "@/views/moldMag/detail.vue"
import TableSetting from "@/components/tableSetting/tableSetting"

export default {
  name: "MoldList",
  components: { QueryMoldList, MoldDetail, TableSetting },
  data() {
    return {
      query: {
        company_id : UserModule.company_id,

        mold_no: null,
        mold_type: null,
        mold_name: null,
        product_type: null,
        product_name: null,
        customer: null,
        project_engineer: null,
        design_engineer: null,
        production_engineer: null,
        order_date: null,

        page_no: 1 ,
        page_size: 100
      },
      mold_detail: {
        id: null, // 选中模具的id
      },
      viewType: null,
      excelData: null,
      listData: {},
      listLoading: false,
      multipleSelection: [],
      columns_setting: [
        { visible: true, label: "ID", prop: "id", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具编号", prop: "mold_no", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "模具类别", prop: "mold_type", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具名称", prop: "mold_name", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品类别", prop: "product_type", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模流数据", prop: "moldflow", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "注塑机适配", prop: "adaption", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "落单日期", prop: "order_date", width: 85, align: "center", header_align: "center", sortable: false, tooltip: false }
      ],
      tableHeaderStyle: { "background-color": "lightblue", "color": "#000", "font-size": "12px", "padding": "10px 0px" },
      tableRowStyle: { },
      tableCellStyle: { "padding": "7px 0px" },
      tableHeight: "45rem",
      showMoldDetail: false, // 新增&编辑模具信息
      showTableSetting: false, // 显示表格设置界面
      downloaded: 0,
    }
  },
  watch: {
    "columns_setting": {
      handler: function() {
        let custom_setting = AppModule.customSetting
        custom_setting.user_id = UserModule.id
        custom_setting.mold_list_columns_setting = this.columns_setting
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
      if (custom_setting && custom_setting.mold_list_columns_setting) {
        if (custom_setting.id == UserModule.id) {
          this.columns_setting = custom_setting.mold_list_columns_setting
        }
      }
    },
    getListData() {
      this.$refs.queryMoldList.queryListData()
    },
    onQueryFinish(moldList) {
      this.listData = moldList
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
    addMold() {
      this.$router.push("/mold/create")
    },
    copyMold() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请从模具列表中选择一条模具信息进行复制！")
        return
      }

      this.$confirm(`确认复制以下模具？\r\n ${ this.multipleSelection[0].mold_no }`, "复制模具", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        this.mold_detail.id = this.multipleSelection[0].id
        this.viewType = "copy"
        this.showMoldDetail = true
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消复制！"
        })
      })
    },
    uploadMoldFromExcel(data) {
      // 从excel导入模具
      let params = new FormData()
      params.append("file", data.file)
      importMold(params).then(res => {
        if (res.data.error_message.indexOf("模号已存在") != -1 || res.data.error_message == ""){
          this.mold_detail.id = null
          this.viewType = "upload"
          this.showMoldDetail = true
          this.excelData = res.data.mold          
        } 
        if (res.data.error_message !== "") {
          this.$message({
            showClose: true,
            message: res.data.error_message,
            type: "error", 
            duration: 3000,
            dangerouslyUseHTMLString: true
          })
        }
      })
      return 0
    },
    exportMoldToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请从模具列表中选择一条模具信息进行导出！")
        return
      }

      this.$confirm(`确认导出以下模具？\r\n ${ this.multipleSelection[0].mold_no }`, "导出模具", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        exportMoldById(this.multipleSelection[0].id)
          .then(res => {
            if (res.status === 0 && res.data.url) {
              this.$message({ message: "导出成功。", type: "success" })
              window.location.href = getFullReportUrl(res.data.url)
            }
          })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消导出！"
        })
      })
    },
    uploadTemplate(data) {
      // 修改模具导入的模板
      let params = new FormData()
      params.append("file", data.file)
      importBatch(params, "report", UserModule.company_id)
        .then(res => {
          if (res.status === 0) {
            this.$message({ message:"上传成功",type:"success" })
          } else {
            this.$message({ message:"上传失败",type:"error" })
          }
        })
      // .finally(()=> this.uploadingID = null)
      return 0
    },
    deleteMold() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }

      let delete_mold = ""
      let mold_no_list = []
      let mold_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        mold_no_list.push(this.multipleSelection[i].mold_no)
        mold_id_list.push(this.multipleSelection[i].id)
      }
      delete_mold = mold_no_list.join("、")

      this.$confirm(`确认删除以下模具？\r\n ${ delete_mold }`, "删除模具", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        projectMethod.multipleDel({
          "project_id_list": mold_id_list
        }).then((res) => {
          if (res.status === 0) {
            this.$message({ type: "success", message: "删除成功!" })
            this.getListData()
          }
        })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消删除！",
        })
      })
    },
    exportListToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }

      let mold_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        mold_id_list.push(this.multipleSelection[i].id)
      }
      projectMethod.multipleHandle({
        "project_id_list": mold_id_list,
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
      this.mold_detail = {
        id: null,
      }
      this.viewType = null
      this.excelData = null
      this.showTableSetting = false
      
      this.getListData()
    },
    sortList(sort) {
      // 排序
      this.query.$orderby = sort.prop
      this.getListData()
    },
    setRowSelectable(row, index) {
      return true
    },
    handleSelectionChange(val) {
      this.multipleSelection = val
    },
    editMold(row) {
      //编辑模具信息
      this.mold_detail.id = row.id
      this.viewType = "edit"
      this.showMoldDetail = true
    },
    rowDoubleClicked(row) {
      //双击查看模具详情，给子组件传入模号
      this.editMold(row)
    },
    refreshView() {
      this.mold_detail = {
        id: null,
      }
      this.viewType = null
      this.excelData = null
      this.showMoldDetail = false

      this.getListData()
    },
    checkAdaption(row){
      projectMethod.getDetail(row.id)
        .then(res => {
          if (res.status === 0) {
            ProjectsInfoModule.PushProject(res.data)
            this.$router.push({
              path:"/mold/aptation",
              query:{
                project_id: row.id,
              }
            })
          }
        })
    },

    checkMoldflow(row){
      // 存储到本地
      projectMethod.getDetail(row.id)
        .then(res => {
          if (res.status === 0) {
            ProjectsInfoModule.PushProject(res.data)
            this.$router.push({ path: "/mold/data" })
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

<style lang="scss" scope>
</style>
