<template>
  <div>
    <polymer-search-form
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
            @click="toAddPolymer"
          >
            添加材料
          </el-button>
          <!-- <el-button
            size="mini"
            type="primary"
            icon="el-icon-document-copy"
            style="margin: 0"
            @click="copyPolymer"
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
      @row-dblclick="updatePolymer"
      @selection-change="(val) => { selected_rows = val }"
    >
      <el-table-column
        type="selection"
        width="40"
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
          <div v-if="column.prop === 'abbreviation'">
            <el-link 
              type="primary"
              size="mini"            
              @click="updatePolymer(scope.row)"
            >
              {{ scope.row[column.prop] }}
            </el-link>
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
            @click="updatePolymer(scope.row)"
            plain
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deletePolymer(scope.row)"
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
        :page-size="query.page_size"
        :page-sizes="$store.state.app.pageSizeArray"
        :total="list_data.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
    <el-drawer
      :title="view_context.title"
      :with-header="true"
      :visible.sync="show_polymer_drawer"
      direction="rtl"
      size="90%"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>{{ view_context.title }}</span>
        </div>
      </template>
      <polymer-form 
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
import { polymerMethod, importMethod, exportListData  } from "@/api"
import { getReportDownloadUrl } from "@/utils/assert"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import { calculateTableHeight } from "@/utils/table-size"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"
import PolymerSearchForm from "./components/PolymerSearchForm.vue"
import PolymerForm from "@/views/polymerManage/PolymerForm.vue"

const rangeFormatter = (minValue, maxValue) => {
  return minValue != null && maxValue != null 
    ? `${minValue} - ${maxValue}` 
    : minValue ?? maxValue ?? ""
}

export default {
  components: { 
    ChangeTableSize,
    TableSetting,
    PolymerSearchForm, 
    PolymerForm, 
  },
  data() {
    return {
      query: {
        manufacturer: null,
        abbreviation: null,
        grade: null,
        category: null,
        data_source: null,
        level_code: null,
        vendor_code: null,

        page_no: 1,
        page_size: 100,
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
        { visible: true, label: "塑料厂商", prop: "manufacturer", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "塑料简称", prop: "abbreviation", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false }, 
        { visible: true, label: "塑料牌号", prop: "grade", width: 180, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "塑料类别", prop: "category", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "数据来源", prop: "data_source", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "等级代码", prop: "level_code", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "供应商代码", prop: "vendor_code", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "推荐成型温度(℃)", prop: "recommended_melt_temp", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料降解温度(℃)", prop: "degradation_temp", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐模具温度(℃)", prop: "recommended_mold_temp", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐顶出温度(℃)", prop: "ejection_temp", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐剪切线速度(mm/s)", prop: "recommended_shear_line_speed", width: 140, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐注射速率(cm³/s)", prop: "recommend_injection_rate", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "推荐背压(MPa)", prop: "recommend_back_pressure", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "干燥方式", prop: "drying_method", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "干燥温度(℃)", formatter: (row) => rangeFormatter(row.drying_temp_min, row.drying_temp_max), width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "干燥时间(h)", formatter: (row) => rangeFormatter(row.drying_time_min, row.drying_time_max), width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 170, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      table_size: "normal",
      show_polymer_drawer: false,
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
        saveColumnsSetting("poly_list_col_config", this.table_columns)
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
      let table_columns = loadColumnsSetting("poly_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    async getListData() {
      this.list_loading = true
      const res = await polymerMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    toAddPolymer() {
      if (!this.$hasPermission("add_polymer")) {
        return this.$message("无创建材料权限")
      }
      this.$router.push("/polymer/create")
    },
    copyPolymer() {
      if (this.selected_rows.length == 0) {
        return this.$message("无选中项。")
      }
      if (this.selected_rows.length > 1) {
        return this.$message("请从模具列表中选择一条材料信息进行复制！")
      }

      this.$confirm(`确认复制以下材料信息？\r\n ${ this.selected_rows[0].grade }`, "复制材料", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        this.view_context = {
          id: this.selected_rows[0].id,
          is_dialog: true,
          title: "复制材料信息",
          mode: "copy"
        }
        this.show_polymer_drawer = true
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
      params.append("file_type", "polymer_template")
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
          title: "从Excel导入数据",
          mode: "import",
          excel_data: res.data.polymer
        }
        this.show_polymer_drawer = true
      })
      return 0
    },
    exportPolymerToExcel() {
      // if (this.selected_rows.length == 0) {
      //   return this.$message("无选中项。")
      // }
      // if (this.selected_rows.length > 1) {
      //   return this.$message("请从模具列表中选择一条材料信息进行导出！")
      // }

      // this.$confirm(`确认导出以下材料？\r\n ${ this.selected_rows[0].grade }`, "导出材料", {
      //   confirmButtonText: "确定",
      //   cancelButtonText: "取消",
      //   type: "warning",
      // }).then(() => {
      //   exportReport({
      //     "resource": "polymer_info",
      //     "polymer_id": this.selected_rows[0].id
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
      const res = await exportListData({ resource: "polymer_list", ids })
      if (res.status === 0 && res.data.url) {
        window.location.href = getReportDownloadUrl(res.data.url)
      }
    },
    updatePolymer(row) {
      if (!this.$hasPermission("review_polymer")) {
        return this.$message("无该材料详细信息的查看权限")
      }
      this.view_context = {
        id: row.id,
        is_dialog: true,
        title: "编辑材料信息",
        mode: "edit"
      }

      this.show_polymer_drawer = true
      this.show_table_setting = false
    },
    async deletePolymer(row) {
      if (!this.$hasPermission("delete_polymer")) {
        return this.$message("无材料删除权限")
      }
      try {
        await this.$confirm(`确认删除以下材料？\r\n ${ row.grade }`, "删除材料", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await polymerMethod.delete(row.id)
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
      this.show_table_setting = false
      this.show_polymer_drawer = false

      this.getListData()
    },
  },
}
</script>

<style lang="scss" scope>

</style>
