<template>
  <div>
    <mold-search-form
      :query-detail="query"
      @search="getListData"
    />
    <div class="row-toolbutton">
      <div>
        <change-table-size 
          :size="table_size" 
          @update="val => table_size = val"
        />
      </div>
      <div>
        <el-button-group>
          <el-button
            size="mini"
            type="primary"
            icon="el-icon-plus"
            @click="toAddMold"
            :disabled="!$hasPermission('add_mold')"
          >
            新增模具
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
    <el-table
      :class="[`table-size-${table_size}`]"
      v-loading="list_loading"
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      style="width: 100%;"
      :data="list_data.items"
      :height="tableHeight"
      @row-dblclick="editMold"
      @selection-change="(val) => { selected_rows = val }"
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
        width="55"
        align="center"
      >
      </el-table-column>
      <el-table-column
        v-for="column, index in table_columns.filter(column => column.visible)"
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
          <span v-if="column.prop === 'mold_no'">
            <el-link
              type="primary" 
              @click="editMold(scope.row)"
              :disabled="!$hasPermission('review_mold')"
            >
              {{ scope.row[column.prop] }}
            </el-link>
          </span>
          <span v-else-if="column.prop === 'reservation'">
            <el-button 
              type="primary"
              size="mini"
              round
              @click="toAddReservation(scope.row)"
              :disabled="!$hasPermission('add_reservation')"
            >
              预约
            </el-button>
          </span>
          <span v-else-if="column.prop === 'moldflow_data'">
            <el-link 
              type="primary" 
              @click="toMoldflowReport(scope.row)"
              :disabled="!$hasPermission('review_moldflow')"
            >
              查看
            </el-link>
          </span>
          <span v-else-if="column.prop === 'trial_data'">
            <el-link
              type="primary" 
              @click="toTrialData(scope.row)"
              :disabled="!$hasPermission('trial_view')"
            >
              查看
            </el-link>
          </span>
          <span v-else-if="column.prop === 'trial_resume'">
            <el-link
              type="primary" 
              @click="toTrialResume(scope.row)"
              :disabled="!$hasPermission('review_trial_resume')"
            >
              查看
            </el-link>
          </span>
          <span v-else-if="column.prop === 'issue_resume'">
            <el-link
              type="primary" 
              @click="toIssueResume(scope.row)"
              :disabled="!$hasPermission('review_problem_resume')"
            >
              查看
            </el-link>
          </span>
          <span v-else>
            {{ scope.row[column.prop] }}
          </span>
        </template>
      </el-table-column>
      <el-table-column
        fixed="right"
        label="操作"
        width="180"
        align="center"
      >
        <template #default="scope">
          <el-button
            type="primary"
            size="mini"
            @click="editMold(scope.row)"
            plain
            :disabled="!$hasPermission('review_mold')"
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteMold(scope.row)"
            plain
            :disabled="!$hasPermission('delete_mold')"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination">
      <el-pagination
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="$store.state.app.pageSizeArray"
        :page-size="query.page_size"
        :current-page="query.page_no"
        :total="list_data.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
    <el-drawer
      direction="rtl"
      size="90%"
      :title="view_context.title"
      :with-header="true"
      :visible.sync="show_mold_info"
      :wrapper-closable="true"
      :show-close="false"
      :destroy-on-close="true"
    >
      <template #title>
        <div class="custom-drawer-header">
          <el-button 
            type="text" 
            icon="el-icon-arrow-left"
            @click="show_mold_info = false"
          >
            返回
          </el-button>
          <span class="drawer-title">{{ view_context.title }}</span>
        </div>
      </template>
      <mold-form 
        @close="refreshView"
        :view-context="view_context"
      />
    </el-drawer>
    <table-setting
      :table-data="table_columns"
      :show-dialog.sync="show_table_setting"
      @close="refreshView"
    >
    </table-setting> 
  </div>
</template>

<script>
import { moldMethod, exportListData } from "@/api"
import { getReportDownloadUrl } from "@/utils/assert"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import { calculateTableHeight } from "@/utils/table-size"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"
import MoldSearchForm from "./components/MoldSearchForm.vue"
import MoldForm from "./MoldForm.vue"

export default {
  name: "MoldList",
  components: { 
    ChangeTableSize,
    TableSetting,
    MoldSearchForm,
    MoldForm,
  },
  data() {
    return {
      query: {
        mold_no: null,
        mold_name: null,
        category: null,
        structure: null,
        cavity_layout: null,
        
        page_no: 1,
        page_size: 100
      },
      list_data: {},
      list_loading: false,
      selected_rows: [],
      view_context: {
        id: null,
        is_dialog: null,
        title: null,
        mode: null,
        excel_data: null,
      },
      table_columns: [
        { visible: true, label: "模具编号", prop: "mold_no", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "模具名称", prop: "mold_name", width: 360, align: "left", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "模具类别", prop: "category", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制作方式", prop: "manufacturing_method", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "试模约机", prop: "reservation", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模流数据", prop: "moldflow_data", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "试模数据", prop: "trial_data", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "试模履历", prop: "trial_resume", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "问题履历", prop: "issue_resume", width: 90, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具结构", prop: "structure", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模腔布局", prop: "cavity_layout", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "产品大类", prop: "product_category", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "产品小类", prop: "product_model", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "注塑周期[s]", prop: "target_cycle_time", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "推荐成型吨位[Ton]", prop: "recommended_tonnage", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具长度[mm]", prop: "mold_length", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具宽度[mm]", prop: "mold_width", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具厚度[mm]", prop: "mold_thickness", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具重量[kg]", prop: "mold_weight", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "创建日期", prop: "created_at", width: 180, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      table_size: "normal",
      show_mold_info: false,
      show_table_setting: false,
    }
  },
  computed: { 
    tableHeight() {
      return calculateTableHeight(500, 220)
    },
  },
  watch: {
    "table_columns": {
      handler: function() {
        saveColumnsSetting("mold_list_col_config", this.table_columns)
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
      let table_columns = loadColumnsSetting("mold_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    async getListData() { 
      this.list_loading = true
      const res = await moldMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    toAddMold() {
      this.$router.push("/mold/create")
    },
    copyMold() {
      // if (this.selected_rows.length == 0) {
      //   this.$message("无选中项！")
      //   return
      // } else if (this.selected_rows.length > 1) {
      //   this.$message("请从模具列表中选择一条模具信息进行复制！")
      //   return
      // }

      // this.$confirm(
      //   `确认复制以下模具？\r\n ${ this.selected_rows[0].mold_no }`, 
      //   "复制模具信息", {
      //     confirmButtonText: "确定",
      //     cancelButtonText: "取消",
      //     type: "warning"
      //   }).then(() => {
      //   this.view_context = {
      //     id: this.selected_rows[0].id,
      //     is_dialog: true,
      //     title: "复制模具信息",
      //     mode: "copy"
      //   }
      //   this.show_mold_info = true
      // }).catch(() => {
      //   this.$message({
      //     type: "info",
      //     message: "已取消复制！"
      //   })
      // })
    },
    uploadMoldFromExcel(data) {
      // // 从 excel 导入模具
      // let params = new FormData()
      // params.append("file", data.file)
      // params.append("file_type", "mold_template")
      // importMethod(params).then(res => {
      //   this.view_context = {
      //     id: null,
      //     is_dialog: true,
      //     title: "从Excel导入数据",
      //     mode: "import",
      //     excel_data: res.data.mold
      //   }
      //   this.show_mold_info = true  
      //   if (res.data.error_message) {
      //     this.$message({
      //       showClose: true,
      //       message: res.data.error_message,
      //       type: "error", 
      //       dangerouslyUseHTMLString: true
      //     }) 
      //   }
      // })
      // return 0
    },
    exportMoldToExcel() {
      // if (this.selected_rows.length == 0) {
      //   this.$message("无选中项！")
      //   return
      // } else if (this.selected_rows.length > 1) {
      //   this.$message("请从模具列表中选择一条模具信息进行导出！")
      //   return
      // }

      // this.$confirm(`确认导出当前模具信息？\r\n ${ this.selected_rows[0].mold_no }`, "导出模具信息", {
      //   confirmButtonText: "确定",
      //   cancelButtonText: "取消",
      //   type: "warning"
      // }).then(() => {
      //   exportReport({
      //     "resource": "mold_info",
      //     "mold_id": this.selected_rows[0].id
      //   }).then(res => {
      //     if (res.status === 0 && res.data.url) {
      //       this.$message({ message: "导出模具信息成功。", type: "success" })
      //       window.location.href = getFullFileUrl(res.data.url)
      //     }
      //   })
      // }).catch(() => {
      //   this.$message({
      //     type: "info",
      //     message: "已取消导出！"
      //   })
      // })
    },
    async exportListToExcel() {
      return this.$message("此按钮功能暂不开放")
      if (this.selected_rows.length == 0) {
        return this.$message("无选中项。")
      }
      const ids = this.selected_rows.map(item => item.id)
      const res = await exportListData({ resource: "mold_list", ids })
      if (res.status === 0 && res.data.url) {
        window.location.href = getReportDownloadUrl(res.data.url)
      }
    },
    editMold(row) {
      //编辑模具信息
      this.view_context = {
        id: row.id,
        title: "更新模具信息",
        mode: "edit"
      }
      this.show_mold_info = true
      this.show_table_setting = false
    },
    async deleteMold(row) {
      try {
        await this.$confirm(`确认删除以下模具信息？\r\n ${ row.mold_no }`, "删除模具", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await moldMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
          this.getListData()
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    toMoldflowReport(row) {
      // 查看模流数据
      this.$router.push({ 
        path: "/mold/moldflow/report",
        query: {
          mold_id: row.id,
          mold_no: row.mold_no,
          category: row.category,
        } 
      })
    },
    toAddReservation(row) {
      // 预约试模约机
      this.$router.push({
        path: "/schedule/reservation/create",
        query: { 
          mold_id: row.id 
        }
      })
    },
    toTrialData(row) {
      // 查看试模数据
      this.$router.push({ 
        path: "/mold-trial/workflow",
        query: {
          mold_id: row.id
        }
      })
    },
    toTrialResume(row) {
      // 查看试模履历
      this.$router.push({ 
        path: "/mold/resume/trial",
        query: {
          mold_id: row.id,
        }
      })
    },
    toIssueResume(row) {
      // 查看问题点履历
      this.$router.push({ 
        path: "/mold/resume/issue",
        query: {
          mold_id: row.id,
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
    refreshView() {
      this.view_context = {
        id: null,
        is_dialog: null,
        title: null,
        mode: null,
        excel_data: null,
      }
      this.show_mold_info = false
      this.show_table_setting = false

      this.getListData()
    },
  }
}
</script>

<style lang="scss" scope>

</style>
