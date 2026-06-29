<template>
  <div>
    <parameter-search-form
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
            @click="toProcessParameter"
          >
            录入工艺
          </el-button>
          <!-- <el-button
            size="mini"
            type="primary"
            icon="el-icon-document-copy"
            @click="copyProcessRecord"
          >
            复制工艺
          </el-button>
          <el-button
            size="mini" 
            type="success"
            icon="el-icon-document"
            @click="exportProcessRecordToExcel" 
          >
            导出工艺
          </el-button> -->
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
      style="width: 100%"
      :data="list_data.items"
      :height="tableHeight"
      @row-dblclick="editParameter"
      @selection-change="(val) => { selected_rows = val }"
    >
      <el-table-column
        type="selection"
        width="40"
        :selectable="isRowSelectable"
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
          <span v-if="column.prop === 'condition_code'">
            <el-link
              type="primary"
              @click="editParameter(scope.row)"
            >
              {{ scope.row[column.prop] }}
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
            @click="editParameter(scope.row)"
            plain
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteParameter(scope.row)"
            plain
          >
            删除
          </el-button>
        </template>
      </el-table-column>
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
    <el-drawer
      :title="view_context.title"
      :visible.sync="show_parameter_info"
      direction="rtl"
      size="90%"
    >
      <process-parameter-form
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
import { processParameterMethod, exportListData } from "@/api"
import { getReportDownloadUrl } from "@/utils/assert"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import { calculateTableHeight } from "@/utils/table-size"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"
import ParameterSearchForm from "./components/ParameterSearchForm.vue"
import ProcessParameterForm from "@/views/processManage/parameter/ProcessParameterCreate.vue"

export default {
  name: "ProcessParameterList",
  components: { 
    ChangeTableSize,
    TableSetting,
    ParameterSearchForm, 
    ProcessParameterForm, 
  },
  data() {
    return {
      query: {
        origin_type: "manual_creation",
        status: null,
        mold_no: null,
        machine_model: null,
        polymer_abbreviation: null,
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
        { visible: true, label: "工艺编号", prop: "condition_code", width: 240, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "模具编号", prop: "mold_no", width: 160, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具名称", prop: "mold_name", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具类别", prop: "mold_type", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模腔布局", prop: "cavity_layout", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品类别", prop: "product_category", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "注塑机品牌", prop: "machine_brand", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机型号", prop: "machine_model", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机编号", prop: "machine_device_code", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料简称", prop: "polymer_abbreviation", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料牌号", prop: "polymer_grade", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "创建日期", prop: "created_at", width: 170, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      table_size: "normal",
      show_parameter_info: false,
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
        saveColumnsSetting("process_parameter_list_col_config", this.table_columns)
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
      let table_columns = loadColumnsSetting("process_parameter_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    async getListData() {
      this.list_loading = true
      const res = await processParameterMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    toProcessParameter() {
      if (!this.$hasPermission("process_entry")) {
        return this.$message("无权限录入工艺")
      }
      this.$router.push({ path: "/process/parameter/create", })
    },
    copyProcessRecord() {
      if (this.selected_rows.length == 0) {
        this.$message("无选中项！")
        return
      }
      if (this.selected_rows.length > 1) {
        this.$message("请从工艺列表中选择一条工艺信息进行复制！")
        return
      }

      this.$confirm(`确认复制以下工艺？\r\n ${ this.selected_rows[0].process_no }`, "复制工艺", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.view_context = {
          id: this.selected_rows[0].id,
          is_dialog: true,
          dialog_title: "复制工艺信息",
          mode: "copy"
        }
        this.show_parameter_info = true
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消复制！",
        })
      })
    },
    exportProcessRecordToExcel() {
      // if (this.selected_rows.length == 0) {
      //   this.$message("无选中项。")
      //   return
      // }
      // if (this.selected_rows.length > 1) {
      //   this.$message("请选中一条进行导出")
      //   return
      // }

      // this.$confirm(`确认导出以下工艺？\r\n ${ this.selected_rows[0].process_no }`, "导出工艺", {
      //   confirmButtonText: "确定",
      //   cancelButtonText: "取消",
      //   type: "warning",
      // }).then(() => {
      //   exportReport({
      //     "resource": "process_info",
      //     "process_id": this.selected_rows[0].id
      //   }).then(res => {
      //     // console.log(res)
      //     if (res.status === 0 && res.data.url) {
      //       this.$message({ message: "导出成功。", type: "success" })
      //       window.location.href = getReportDownloadUrl(res.data.url)
      //     }
      //   })
      // }).catch((error) => {
      //   this.$message({
      //     type: "info",
      //     message: "已取消导出",
      //   })
      // })
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
    isRowSelectable(row, index) {
      // if (this.$hasPermission('project_delete')) {
      //   return true;
      // } else {
      //   return false;
      // }
      return true
    },
    editParameter(row) {
      if (!this.$hasPermission("process_list")) {
        return this.$message("无权限查看工艺详细信息")
      }
      this.view_context = {
        id: row.id,
        is_dialog: true,
        dialog_title: "更新工艺信息",
        mode: "edit"
      }
      this.show_parameter_info = true
      this.show_table_setting = false
    },
    async deleteParameter(row) {
      try {
        await this.$confirm("确认删除选中工艺记录", "删除工艺记录", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await processParameterMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功！" })
          this.getListData()
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除！" })
      }
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
      this.show_parameter_info = false
      this.show_table_setting = false

      this.getListData()
    },
  }
}
</script>

<style>

</style>

