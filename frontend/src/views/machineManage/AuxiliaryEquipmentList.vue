<template>
  <div>
    <BaseSearchForm
      :query="query_params"
      :items="search_items"
      @search="handleSearch"
      @reset="handleReset"
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
            @click="addAuxiliary"
          >
            添加辅助装置
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
      style="width: 100%"
      :data="list_data.items"
      :height="tableHeight"
      @row-dblclick="editAuxiliary"
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
          <div v-if="column.prop === 'equipment_name'">
            <el-link 
              type="primary"
              size="mini"            
              @click="editAuxiliary(scope.row)"
            >
              {{ scope.row[column.prop] }}
            </el-link>
          </div>
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
            @click="editAuxiliary(scope.row)"
            plain
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteAuxiliary(scope.row)"
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
      :visible.sync="show_auxiliary_info"
      direction="rtl"
      size="600px"
    >
      <el-card class="form-card" shadow="never">
        <div slot="header" class="card-header">
          <span>辅助装置信息</span>
        </div>
        <el-form
          ref="auxiliaryForm"
          :model="auxiliary"
          :rules="rules"
          label-width="100px"
          size="small"
        >
          <el-form-item 
            label="装置名称" 
            prop="equipment_name"
          >
            <el-input
              v-model="auxiliary.equipment_name"
              placeholder="例如：模温机-水式"
              clearable
            />
          </el-form-item>
          <el-form-item 
            label="装置类型" 
            prop="equipment_type"
          >
            <el-input
              v-model="auxiliary.equipment_type"
              placeholder="例如：模温机、干燥机"
              clearable
            />
          </el-form-item>
          <el-form-item 
            label="规格参数" 
            prop="specification"
          >
            <el-input
              v-model="auxiliary.specification"
              placeholder="例如：油式, 120℃ 或 M12×1.5"
              clearable
            />
          </el-form-item>
          <el-form-item 
            label="总数量" 
            prop="total_count"
          >
            <el-input-number
              v-model="auxiliary.total_count"
              :min="0"
              :precision="0"
              controls-position="right"
              style="width: 50%"
            />
          </el-form-item>
          <el-form-item 
            label="可用数量" 
            prop="available_count"
          >
            <el-input-number
              v-model="auxiliary.available_count"
              :min="0"
              :max="auxiliary.total_count"
              :precision="0"
              controls-position="right"
              style="width: 50%"
            />
          </el-form-item>
          <el-form-item 
            label="备注" 
            prop="remarks"
          >
            <el-input
              v-model="auxiliary.remarks"
              type="textarea"
              placeholder="可填写适用场景、维护要求、品牌建议等"
              :autosize="{ minRows: 2, maxRows: 10 }"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </el-card>
      <div class="drawer-footer">
        <el-button 
          @click="show_auxiliary_info = false"
          size="small"
          type="danger"
        >
          返  回
        </el-button>
        <el-button 
          @click="saveAuxiliary"
          size="small"
          type="primary"
        >
          {{ view_context.id ? '修  改' : '添  加' }}
        </el-button>
      </div>
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
import BaseSearchForm from "@/components/BaseSearchForm.vue"
import { auxiliaryMethod, exportListData } from "@/api"
import { getReportDownloadUrl } from "@/utils/assert"
import { loadColumnsSetting, saveColumnsSetting } from "@/utils/columns-setting"
import { calculateTableHeight } from "@/utils/table-size"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import TableSetting from "@/components/tableSetting/tableSetting.vue"

export default {
  components: { 
    BaseSearchForm,
    ChangeTableSize,
    TableSetting 
  },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: {
        equipment_name: null,
        equipment_type: null,

        page_no: 1,
        page_size: 100
      },
      search_items: [
        { label: "设备名称", prop: "equipment_name", type: "autocomplete", query: { table: "auxiliary_equipment", column: "equipment_name" } },
        { label: "设备类型", prop: "equipment_type", type: "autocomplete", query: { table: "auxiliary_equipment", column: "equipment_type" } }
      ],
      list_data: {},
      list_loading: false,
      selected_rows: [],
      view_context: {
        id: null,
        is_dialog: null,
        title: null,
        mode: null,
      },
      table_columns: [
        { visible: true, label: "名称", prop: "equipment_name", width: 160, align: "left", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "类型", prop: "equipment_type", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "规格", prop: "specification", width: 200, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "总数量", prop: "total_count", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "可用数量", prop: "available_count", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "备注", prop: "remarks", width: 240, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 170, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "创建日期", prop: "created_at", width: 170, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      table_size: "normal",
      show_auxiliary_info: false,
      show_table_setting: false, // 显示表格设置界面
      auxiliary: { 
        id: null,
        equipment_name: "",
        equipment_type: "",
        specification: "",
        total_count: 0,
        available_count: 0,
        remarks: "",
      },
      rules: {
        equipment_name: [
          { required: true, message: "请输入装置名称", trigger: "blur" }
        ],
        equipment_type: [
          { required: true, message: "请输入装置类型", trigger: "blur" }
        ],
        total_count: [
          { required: true, message: "请输入总数量", trigger: "blur" }
        ],
        available_count: [
          { required: true, message: "请输入可用数量", trigger: "blur" }
        ]
      }
    }
  },
  computed: {
    tableHeight() { 
      return calculateTableHeight(500, 200)
    },
  },
  watch: {
    "table_columns": {
      handler: function() {
        saveColumnsSetting("aux_list_col_config", this.table_columns)
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
      let table_columns = loadColumnsSetting("aux_list_col_config")
      if (table_columns) {
        this.table_columns = table_columns
      }
    },
    async getListData(reset = false) {
      if (reset) {
        // 重置查询参数
        this.query_params.equipment_name = null
        this.query_params.equipment_type = null
        // 重置页码
        this.query_params.page_no = 1
      }
      
      // 获取查询数据
      this.list_loading = true
      const res = await auxiliaryMethod.get(this.query_params)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    handleSearch() {
      this.getListData()
    },
    handleReset() {
      this.getListData(true)
    },
    addAuxiliary() {
      if (!this.$hasPermission("add_auxiliary")) {
        return this.$message("无添加辅助装置权限")
      }
      this.view_context = {
        id: null,
        is_dialog: false,
        title: "添加辅助装置",
        mode: "add"
      }
      this.show_auxiliary_info = true
    },
    async exportListToExcel() {
      if (this.selected_rows.length == 0) {
        return this.$message("无选中项。")
      }
      const ids = this.selected_rows.map(item => item.id)
      const res = await exportListData({ resource: "auxiliary_list", ids })
      if (res.status === 0 && res.data.url) {
        window.location.href = getReportDownloadUrl(res.data.url)
      }
    },
    editAuxiliary(row) {
      if (!this.$hasPermission("review_auxiliary")) {
        return this.$message("无该辅助装置详细信息的查看权限")
      }
      this.view_context = {
        id: row.id,
        is_dialog: true,
        title: "编辑辅助装置",
        mode: "edit",
      }
      this.show_auxiliary_info = true
      this.show_table_setting = false

      this.getAuxiliary(row.id)
    },
    async getAuxiliary(id) { 
      if (!id) return

      const res = await auxiliaryMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.auxiliary, res.data)
      }
    },
    async saveAuxiliary() {
      if (!this.$hasPermission("update_auxiliary")) {
        return this.$message("无辅助装置的编辑权限")
      }
      this.auxiliary.id = this.view_context.id

      if (this.auxiliary.id) {
        const res = await auxiliaryMethod.edit(this.auxiliary, this.auxiliary.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "更新成功。" })
        }
      } else {
        const res = await auxiliaryMethod.add(this.auxiliary)
        if (res.status === 0) {
          this.$message({ type: "success", message: "添加成功。" })
        }
      }

      this.refreshView()
      this.show_auxiliary_info = false
    },
    async deleteAuxiliary(row) {
      if (!this.$hasPermission("delete_auxiliary")) {
        return this.$message("无删除辅助装置权限")
      }
      try {
        await this.$confirm(`确认删除以下辅机信息？\r\n ${ row.equipment_name }`, "删除辅机", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await auxiliaryMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
          this.getListData()
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    handleSizeChange(val) {
      this.query_params.page_size = val
      this.getListData()
    },
    handleCurrentChange (val) {
      this.query_params.page_no = val
      this.getListData()
    },
    refreshView() {
      this.view_context = {
        id: null,
        is_dialog: null,
        title: null,
        mode: null,
        excel_data: null,
      },
      this.show_table_setting = false
      this.show_auxiliary_info = false

      this.getListData()
    },
  }
}
</script>

<style lang="scss" scoped>
.form-card {
  max-width: 600px;
  margin: 0px auto;
  border: none;
}
.card-header {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}
.drawer-footer {
  position: fixed;
  bottom: 10px;
  right: 20px;
  border-top: 1px solid var(--el-border-color-light);
  background-color: var(--el-bg-color-overlay);
}
.drawer-footer .el-button {
  width: 8rem;
}
::v-deep .el-drawer__body {
  padding: 16px !important;
}
</style>