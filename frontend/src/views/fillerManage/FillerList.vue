<template>
  <div>
    <filler-search-form
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
            @click="toAddFiller"
          >
            新增填充物
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
      :data="list_data.items"
      :height="tableHeight"
      @row-dblclick="editFiller"
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
          <div v-if="column.prop === 'abbreviation'">
            <el-button 
              type="text" 
              size="mini"            
              @click="editFiller(scope.row)"
            >
              <span v-if="column.options && column.options.length > 0">
                {{ column.options.find(opt => opt.value === scope.row[column.prop])?.label || scope.row[column.prop] }}
              </span>
              <span v-else>
                {{ scope.row[column.prop] }}
              </span>
            </el-button>
          </div>
          <div v-else-if="column.options && column.options.length > 0">
            {{ column.options.find(opt => opt.value === scope.row[column.prop])?.label || scope.row[column.prop] }}
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
      :visible.sync="show_filler_info"
      direction="rtl"
      size="800px"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>{{ view_context.title }}</span>
        </div>
      </template>
      <filler-create 
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
import { fillerMethod, exportListData } from "@/api"
import { getReportDownloadUrl } from "@/utils/assert"
import { fillerTypeOptions, colorOptions, shapeOptions, fillerCategoryOptions } from "@/constants/polymer-const"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import { calculateTableHeight } from "@/utils/table-size"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"
import FillerSearchForm from "./components/FillerSearchForm.vue"
import FillerCreate from "./FillerCreate.vue"

export default {
  name: "FillerList",
  components: { 
    ChangeTableSize, 
    TableSetting,
    FillerSearchForm, 
    FillerCreate, 
  },
  data() {
    return {
      query: {
        name: null,
        abbreviation: null,
        category: null,
        shape: null,

        page_no: 1,
        page_size: 100,
      },
      view_context: {
        id: null,
        is_dialog: null,
        dialog_title: null,
        mode: null,
        excel_data: null,
      },
      list_data: {},
      list_loading: false,
      selected_rows: [],
      table_columns: [
        { visible: true, label: "名称", prop: "name", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "缩写", prop: "abbreviation", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false, options: fillerTypeOptions }, 
        { visible: true, label: "类别", prop: "category", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false, options: fillerCategoryOptions }, 
        { visible: true, label: "形状", prop: "shape", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true, options: shapeOptions }, 
        { visible: true, label: "中位粒径 D50(μm)", prop: "particle_size_d50", width: 180, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "长径比", prop: "aspect_ratio", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "含水率(%)", prop: "moisture_content", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "表面处理", prop: "surface_treatment", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "密度(g/cm³)", prop: "density", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "热稳定温度(℃)", prop: "thermal_stability_temp", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "颜色", prop: "color", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true, options: colorOptions }, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      table_size: "normal",
      show_filler_info: false,
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
        saveColumnsSetting("filler_list_col_config", this.table_columns)
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
      let table_columns = loadColumnsSetting("filler_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    async getListData() { 
      this.list_loading = true
      const res = await fillerMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    toAddFiller() {
      this.$router.push("/polymer/filler/create")
    },
    async exportListToExcel() {
      if (this.selected_rows.length == 0) {
        return this.$message("无选中项。")
      }
      const ids = this.selected_rows.map(item => item.id)
      const res = await exportListData({ resource: "filler_list", ids })
      if (res.status === 0 && res.data.url) {
        window.location.href = getReportDownloadUrl(res.data.url)
      }
    },
    editFiller(row) {
      this.view_context = {
        id: row.id,
        is_dialog: true,
        dialog_title: "编辑填充物信息",
        mode: "edit"
      }
      this.show_filler_info = true
      this.show_table_setting = false
    },
    async deleteFiller(row) {
      try {
        await this.$confirm("确认删除以下填充物？", "删除填充物", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await fillerMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
          this.getListData()
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    refreshView() {
      this.view_context = {
        id: null,
        is_dialog: null,
        dialog_title: null,
        mode: null,
        excel_data: null,
      }
      this.show_filler_info = false
      this.show_table_setting = false

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

<style lang="scss" scope>

</style>

