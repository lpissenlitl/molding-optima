<template>
  <div>
    <query-polymer-list
      ref="queryPolymerList"
      :query-detail="query"
      @queryStart="listLoading = true"
      @queryFinish="onQueryFinish"
    >
    </query-polymer-list>
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
          @click="addPolymer"
          type="primary"
          icon="el-icon-plus"
          :disabled="!$store.state.user.userinfo.permissions.includes('add_polymer')"
        >
          添加材料
        </el-button>
        <el-button
          size="mini"
          type="primary"
          icon="el-icon-document-copy"
          style="margin: 0"
          @click="copyPolymer"
          :disabled="!$store.state.user.userinfo.permissions.includes('add_polymer')"
        >
          复制材料
        </el-button>
        <el-upload 
          style="display:inline-block" 
          action="" 
          :show-file-list="false" 
          :http-request="uploadPolymerFromExcel"
        >
          <el-button 
            type="primary" 
            size="mini" 
            icon="el-icon-folder-opened"
            :disabled="!$store.state.user.userinfo.permissions.includes('add_polymer')"
          >
            导入材料
          </el-button>
        </el-upload>
        <el-button
          size="mini" 
          type="success"
          icon="el-icon-document"
          @click="exportPolymerToExcel" 
        >
          导出材料
        </el-button>
        <el-button
          type="danger"
          size="mini"
          @click="deletePolymer"
          icon="el-icon-close"
          style="margin: 0"
          :disabled="!$store.state.user.userinfo.permissions.includes('delete_polymer')"
        >
          删除材料
        </el-button>
        <el-button
          size="mini"
          type="success"
          @click="exportListToExcel"
          icon="el-icon-download"
          style="margin: 0"
        >
          导出列表
        </el-button>
        <el-button
          size="mini"
          @click="checkPolymer"
          type="primary"
          style="margin: 0"
        >
          密度参考
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
    <el-table
      v-loading="listLoading"
      @sort-change="sortList"
      @row-dblclick="rowDoubleClicked"
      @selection-change="handleSelectionChange"
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
      <template
        v-for="column, index in columns_setting"
      >
        <el-table-column
          :key="index"
          v-if="column.visible"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width"
          :header-align="column.header_align"
          :align="column.align"
          :sortable="column.sortable"
          :show-overflow-tooltip="column.tooltip"
        >
          <template slot-scope="scope">
            <div v-if="column.prop === 'abbreviation'">
              <el-button 
                type="text" 
                size="mini"            
                @click="editPolymer(scope.row)"
              >
                {{ scope.row[column.prop] }}
              </el-button>
            </div>
            <div v-else>
              {{ scope.row[column.prop] }}
            </div>
          </template>
        </el-table-column>
      </template>
    </el-table>
    <div class="pagination">
      <el-pagination
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="query.page_no"
        :page-size="query.page_size"
        :page-sizes="$store.state.app.pageSizeArray"
        :total="listData.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
    <polymer-detail
      :id="polymer_detail.id"
      :view-type="viewType"
      :excel-data="excelData"
      :show-update.sync="showPolymerDetail"
      @close="refreshView"
    >
    </polymer-detail>
    <table-setting
      :table-data="columns_setting"
      :show-dialog.sync="showTableSetting"
      @close="refreshTable"
    >
    </table-setting>
    <el-drawer
      title="常见密度值"
      :visible.sync="showPolymer"
      direction="rtl"
      size="30%"      
    >
      <el-table 
        :data="tableData" 
        size="mini"
        stripe 
        border 
        fit 
        highlight-current-row
      >
        <el-table-column 
          prop="polymer" 
          label="塑料"
          width="180"
        >
        </el-table-column>
        <el-table-column 
          label="熔融密度(g/cm³)"
          prop="melt" 
        >  
          <template slot-scope="scope">
            <span v-html="scope.row.melt"></span>
          </template>
        </el-table-column>
        <el-table-column 
          label="固态密度(g/cm³)"
          prop="solid" 
        >  
          <template slot-scope="scope">
            <span v-html="scope.row.solid"></span>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script>
import { polymerMethod, importPolymer, exportPolymerById  } from "@/api"
import { AppModule } from "@/store/modules/app"
import { UserModule } from "@/store/modules/user"
import { getFullReportUrl } from "@/utils/assert"
import QueryPolymerList from "./subView/queryPolymerList.vue"
import PolymerDetail from "./detail.vue"
import TableSetting from "@/components/tableSetting/tableSetting"
import { densityRefer } from "@/utils/polymer-const"

export default {
  components: { QueryPolymerList, PolymerDetail, TableSetting },
  data() {
    return {
      query: {
        company_id: UserModule.company_id,

        abbreviation: null,
        trademark: null,
        series: null,
        manufacturer: null,

        page_no: 1,
        page_size: 100,
      },
      polymer_detail: {
        id: null
      },
      viewType: null,
      excelData: null,
      listData: {},
      listLoading: false,
      multipleSelection: [],
      columns_setting: [
        { visible: true, label: "ID", prop: "id", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "制造厂商", prop: "manufacturer", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "塑料简称", prop: "abbreviation", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "塑料牌号", prop: "trademark", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "塑料类别", prop: "category", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "推荐成型温度", prop: "recommend_melt_temperature", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐模具温度", prop: "recommend_mold_temperature", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料降解温度", prop: "degradation_temperature", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "顶出温度", prop: "ejection_temperature", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐剪切线速度", prop: "recommend_shear_linear_speed", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐注射速率", prop: "recommend_injection_rate", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "干燥方式", prop: "dry_method", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "干燥温度", prop: "dry_temperature", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "干燥时间", prop: "dry_time", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      tableHeaderStyle: { "background-color": "lightblue", "color": "#000", "font-size": "12px", "padding": "10px 0px" },
      tableRowStyle: { },
      tableCellStyle: { "padding": "7px 0px" },
      tableHeight: "45rem",
      showPolymerDetail: false,
      showTableSetting: false, // 显示表格设置界面
      showPolymer: false,
      tableData:densityRefer,
    }
  },
  watch: {
    "columns_setting": {
      handler: function() {
        let custom_setting = AppModule.customSetting
        custom_setting.user_id = UserModule.id
        custom_setting.poly_list_columns_setting = this.columns_setting
        localStorage.setItem("custom_setting", JSON.stringify(custom_setting))
      },
      deep: true
    },
  },
  created() {
    this.loadViewSetting()
  },
  mounted() {
    // this.$nextTick(function() { 
    //   if (window.innerHeight - this.$el.offsetTop - 168 < 600) {
    //     this.tableHeight = 600
    //   } else {
    //     this.tableHeight = window.innerHeight - this.$el.offsetTop - 168
    //   }
    //   let _this = this
    //   window.onresize = function() {
    //     if (window.innerHeight - _this.$el.offsetTop - 168 < 600) {
    //       _this.tableHeight = 600
    //     } else {
    //       _this.tableHeight = window.innerHeight - _this.$el.offsetTop - 168
    //     }
    //   }
    // })

    this.getListData()
  },
  methods: {
    checkPolymer(){
      this.showPolymer = true
    },
    loadViewSetting() {
      let custom_setting = AppModule.customSetting
      if (custom_setting && custom_setting.poly_list_columns_setting) {
        if (custom_setting.id == UserModule.id) {
          this.columns_setting = custom_setting.poly_list_columns_setting
        }
      }
    },
    getListData() {
      this.$refs.queryPolymerList.queryListData()
    },
    onQueryFinish(polymerList) {
      this.listData = polymerList
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
    addPolymer() {
      this.$router.push("/polymer/create")
    },
    copyPolymer() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项。")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请从模具列表中选择一条材料信息进行复制！")
        return
      }

      this.$confirm(`确认复制以下材料？\r\n ${ this.multipleSelection[0].trademark }`, "复制材料", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.polymer_detail.id = this.multipleSelection[0].id
        this.viewType = "copy"
        this.showPolymerDetail = true
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消复制",
        })
      })
    },
    uploadPolymerFromExcel(data) {
      let params = new FormData()
      params.append("file", data.file)
      importPolymer(params).then(res => {
        this.showPolymerDetail = true
        this.viewType = "upload"
        this.excelData = res.data.polymer

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
    exportPolymerToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项。")
        return
      }
      if (this.multipleSelection.length > 1) {
        this.$message("请从模具列表中选择一条材料信息进行导出！")
        return
      }

      this.$confirm(`确认导出以下材料？\r\n ${ this.multipleSelection[0].trademark }`, "导出材料", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        exportPolymerById(this.multipleSelection[0].id)
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
    deletePolymer() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项！")
        return
      }
            
      let delete_polymer = ""
      let polymer_trademark_list = []
      let polymer_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        polymer_trademark_list.push(this.multipleSelection[i].trademark)
        polymer_id_list.push(this.multipleSelection[i].id)
      }
      delete_polymer = polymer_trademark_list.join("、")

      this.$confirm(`确认删除以下材料？\r\n ${ delete_polymer }`, "删除材料", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        polymerMethod.multipleDel({
          "polymer_id_list": polymer_id_list
        }).then((res) => {
          if (res.status === 0) {
            this.$message({ type: "success", message: "删除成功!" })
            this.getListData()
          }
        })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消删除",
        })
      })
    },
    exportListToExcel() {
      if (this.multipleSelection.length == 0) {
        this.$message("无选中项。")
        return
      }

      let polymer_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        polymer_id_list.push(this.multipleSelection[i].id)
      }
      polymerMethod.multipleHandle({
        "polymer_id_list": polymer_id_list,
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
      this.polymer_detail.id = null
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
    editPolymer(row) {
      this.polymer_detail.id = row.id
      this.viewType = "edit"
      this.showPolymerDetail = true
    },
    rowDoubleClicked(row) {
      this.editPolymer(row)
    },
    refreshView() {
      this.polymer_detail.id = null
      this.viewType = null
      this.excelData = null
      this.showPolymerDetail = false

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
  },
}
</script>
