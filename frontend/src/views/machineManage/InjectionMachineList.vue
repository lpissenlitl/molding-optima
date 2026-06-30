<template>
  <div>
    <injection-search-form
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
            type="primary"
            size="mini"
            icon="el-icon-plus"
            @click="toAddMachine"
          >
            添加机器
          </el-button>
          <!-- <el-button
            size="mini"
            type="primary"
            icon="el-icon-document-copy"
            style="margin: 0"
            @click="copyMachine"
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
      :data="list_data.items"
      :height="tableHeight"
      @row-dblclick="updateMachine"
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
          <div v-if="column.prop === 'model'">
            <el-button 
              type="text" 
              size="mini"            
              @click="updateMachine(scope.row)"
            >
              {{ scope.row[column.prop] }}
            </el-button>
          </div>
          <template v-else-if="column.formatter">
            {{ column.formatter(scope.row) }}
          </template>
          <div v-else>
            {{ scope.row[column.prop] }}
          </div>
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
            @click="updateMachine(scope.row)"
            plain
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteMachine(scope.row)"
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
      :with-header="false"
      :visible.sync="show_injection_drawer"
      direction="rtl"
      size="90%"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>{{ view_context.title }}</span>
        </div>
      </template>
      <injection-machine-form 
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
import { machineMethod, exportListData, importMethod } from "@/api"
import { getReportDownloadUrl } from "@/utils/assert"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import { calculateTableHeight } from "@/utils/table-size"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"
import InjectionSearchForm from "./components/InjectionSearchForm.vue"
import InjectionMachineForm from "@/views/machineManage/InjectionMachineForm.vue"

const format = {
  oneToMany: (rel, field, sep = "/") => (row) =>
    row[rel]?.map(it => it[field]).filter(Boolean).join(sep) || ""
}

export default {
  name: "InjectionMachineList",
  components: { 
    ChangeTableSize,
    TableSetting,
    InjectionSearchForm, 
    InjectionMachineForm, 
  },
  data() {
    return {
      query: {
        brand: null,
        model: null,
        device_no: null,
        location: null,
        machine_type: null,
        drive_system: null,

        page_no: 1,
        page_size: 100
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
        { visible: true, label: "品牌", prop: "brand", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "设备型号", prop: "model", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "设备编号", prop: "device_no", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "设备位置", prop: "location", width: 200, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "设备类型", prop: "machine_type", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "驱动系统", prop: "drive_system", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "最大注射重量(g)", prop: "injection_units.max_injection_weight", formatter: format.oneToMany("injection_units", "max_injection_weight"), width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "最大注射速度(mm/s)", prop: "injection_units.max_injection_speed", formatter: format.oneToMany("injection_units", "max_injection_speed"), width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "最大注射行程(mm)", prop: "injection_units.max_injection_stroke", formatter: format.oneToMany("injection_units", "max_injection_stroke"), width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "最大注射压力(MPa)", prop: "injection_units.max_injection_pressure", formatter: format.oneToMany("injection_units", "max_injection_pressure"), width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "最大保压压力(MPa)", prop: "injection_units.max_holding_pressure", formatter: format.oneToMany("injection_units", "max_holding_pressure"), width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "最大螺杆转速(rpm)", prop: "injection_units.max_screw_rotation_speed", formatter: format.oneToMany("injection_units", "max_screw_rotation_speed"), width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "塑化能力(g/h)", prop: "injection_units.plasticizing_capacity", formatter: format.oneToMany("injection_units", "plasticizing_capacity"), width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "螺杆直径(mm)", prop: "injection_units.screw_diameter", formatter: format.oneToMany("injection_units", "screw_diameter"), width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "投产日期", prop: "commissioning_date", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 170, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      table_size: "normal",
      show_injection_drawer: false,
      show_table_setting: false, // 显示表格设置界面
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
        saveColumnsSetting("mac_list_col_config", this.table_columns)
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
      let table_columns = loadColumnsSetting("mac_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    async getListData() {
      this.list_loading = true
      const res = await machineMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    toAddMachine() {
      if (!this.$hasPermission("add_machine")) {
        return this.$message("无添加机器权限")
      }
      this.$router.push("/equipment/injection/create")
    },
    copyMachine() {
      if (this.selected_rows.length == 0) {
        return this.$message("无选中项！")
      }
      if (this.selected_rows.length > 1) {
        return this.$message("请从模具列表中选择一条设备信息进行复制！")
      }

      this.$confirm(`确认复制以下设备信息？\r\n ${ this.selected_rows[0].model }`, "复制设备信息", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.view_context = {
          id: this.selected_rows[0].id,
          is_dialog: true,
          dialog_title: "复制设备信息",
          mode: "copy"
        }
        this.show_injection_drawer = true
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
      params.append("file_type", "machine_template")
      importMethod(params).then(res => {
        if (res.data.error_message !== "") {
          this.$message({
            showClose: true,
            message: res.data.error_message,
            type: "error", 
            duration: 0,
            dangerouslyUseHTMLString: true
          })
        } 

        this.view_context = {
          id: null,
          is_dialog: true,
          dialog_title: "从Excel导入数据",
          mode: "import",
          excel_data: res.data.machine
        }
        this.show_injection_drawer = true

      })
      return 0
    },
    exportMachineToExcel() {
      // if (this.selected_rows.length == 0) {
      //   return this.$message("无选中项！")
      // }
      // if (this.selected_rows.length > 1) {
      //   return this.$message("请从模具列表中选择一条设备信息进行导出！")
      // }

      // this.$confirm(`确认导出以下机器？\r\n ${ this.selected_rows[0].model }`, "导出设备信息", {
      //   confirmButtonText: "确定",
      //   cancelButtonText: "取消",
      //   type: "warning",
      // }).then(() => {
      //   exportReport({
      //     "resource": "machine_info",
      //     "machine_id": this.selected_rows[0].id
      //   }).then(res => {
      //     if (res.status === 0 && res.data.url) {
      //       this.$message({ message: "导出成功。", type: "success" })
      //       window.location.href = getReportDownloadUrl(res.data.url)
      //     }
      //   })
      // }).catch(() => {
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
      const res = await exportListData({ resource: "injection_list", ids })
      if (res.status === 0 && res.data.url) {
        window.location.href = getReportDownloadUrl(res.data.url)
      }
    },
    updateMachine(row) {
      if (!this.$hasPermission("review_machine")) {
        return this.$message("无该机器详细信息的查看权限")
      }
      this.view_context = {
        id: row.id,
        is_dialog: true,
        dialog_title: "编辑设备信息",
        mode: "edit",
      }

      this.show_injection_drawer = true
      this.show_table_setting = false
    },
    async deleteMachine(row) {
      if (!this.$hasPermission("delete_machine")) {
        return this.$message("无删除机器权限")
      }
      try {
        await this.$confirm(`确认删除以下机器？\r\n ${ row.model }`, "删除机器", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await machineMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
          this.getListData()
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    handleSizeChange(val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange (val) {
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
      },
      this.show_table_setting = false
      this.show_injection_drawer = false

      this.getListData()
    },
  }
}
</script>

<style lang="scss" scope>

</style>

