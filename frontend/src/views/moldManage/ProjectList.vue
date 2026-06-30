<template>
  <div>
    <project-search-form
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
            @click="toAddProject"
            :disabled="!$hasPermission('add_project')"
          >
            新增项目
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
      @row-dblclick="editProject"
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
          <span v-if="column.prop === 'project_code'">
            <el-link
              type="primary"
              @click="editProject(scope.row)"
              :disabled="!$hasPermission('review_project')"
            >
              {{ scope.row[column.prop] }}
            </el-link>
          </span>
          <span v-else-if="column.prop === 'source'">
            <span 
              v-if="scope.row.source === 'sync'"
              class="el-icon-warning"
              style="color: orange;"
            >
              🟡 系统同步
            </span>
            <span v-else-if="scope.row.source === 'manual'">
              手动创建
            </span>
            <span v-else>—</span>
          </span>
          <span v-else-if="column.prop === 'mold_no'">
            <span v-if="scope.row.mold_id">
              {{ scope.row[column.prop] }}
            </span>
            <el-button
              v-else
              type="primary"
              size="mini"
              @click="toBindMold(scope.row)"
            >
              绑定
            </el-button>
          </span>
          <span v-else-if="column.map">
            {{ column.map[scope.row[column.prop]] || scope.row[column.prop] }}
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
            @click="editProject(scope.row)"
            plain
            :disabled="!$hasPermission('review_project')"
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteProject(scope.row)"
            plain
            :disabled="!$hasPermission('delete_project')"
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
      :title="view_context.title"
      :with-header="true"
      :visible.sync="show_project_info"
      direction="rtl"
      size="90%"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>{{ view_context.title }}</span>
        </div>
      </template>
      <project-form 
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
import { projectMethod, exportListData } from "@/api"
import { getReportDownloadUrl } from "@/utils/assert"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import { calculateTableHeight } from "@/utils/table-size"
import { projectStatusMap } from "@/constants/project-const"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"
import ProjectSearchForm from "./components/ProjectSearchForm.vue"
import ProjectForm from "./ProjectForm.vue"

export default {
  name: "ProjectList",
  components: {
    ChangeTableSize,
    TableSetting,
    ProjectSearchForm,
    ProjectForm,
  },
  data() {
    return {
      query: {
        projec_code: null,
        status: null,
        project_name: null,
        mold_no: null,
        initiator: null,
        application_industry: null,

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
        { visible: true, label: "项目编号", prop: "project_code", width: 180, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "项目状态", prop: "status", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false, map: projectStatusMap },
        { visible: true, label: "项目名称", prop: "project_name", width: 180, align: "center", header_align: "center", sortable: false, tooltip: true },
        { visible: true, label: "关联模具", prop: "mold_no", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "客户名称", prop: "initiator", width: 240, align: "left", header_align: "center", sortable: false, tooltip: true },
        { visible: true, label: "应用行业", prop: "application_industry", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "量产地", prop: "manufacturing_location", width: 130, align: "center", header_align: "center", sortable: false, tooltip: true },
        { visible: true, label: "项目经理", prop: "project_manager", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "合同日期", prop: "contract_date", width: 160, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "创建日期", prop: "created_at", width: 180, align: "center", header_align: "center", sortable: true, tooltip: false },
      ],
      table_size: "normal",
      show_project_info: false,
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
      handler: function () {
        saveColumnsSetting("project_list_col_config", this.table_columns)
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
      let table_columns = loadColumnsSetting("project_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    async getListData() {
      this.list_data = true
      const res = await projectMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    toAddProject() {
      this.$router.push("/mold/project/create")
    },
    editProject(row) {
      //编辑项目信息
      this.view_context = {
        id: row.id,
        is_dialog: true,
        title: "更新项目信息",
        mode: "edit"
      }
      this.show_project_info = true
      this.show_table_setting = false
    },
    async deleteProject(row = null) {
      try {
        await this.$confirm(`确认删除以下项目？\r\n ${ row.mold_no }`, "删除项目", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await projectMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
          this.getListData()
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    async exportListToExcel() {
      return this.$message("此按钮功能暂不开放")
      if (this.selected_rows.length == 0) {
        return this.$message("无选中项。")
      }
      const ids = this.selected_rows.map(item => item.id)
      const res = await exportListData({ resource: "project_list", ids })
      if (res.status === 0 && res.data.url) {
        window.location.href = getReportDownloadUrl(res.data.url)
      }
    },
    toBindMold(project) {
      // 跳转到模具创建界面
      this.$router.push({
        path: "/mold/create",
        query: { project_id: project.id }
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
      this.show_project_info = false
      this.show_table_setting = false

      this.getListData()
    }
  }
}
</script>

<style lang="scss" scoped>

</style>