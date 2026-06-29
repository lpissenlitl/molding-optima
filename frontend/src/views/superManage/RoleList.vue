<template>
  <div>
    <BaseSearchForm
      :query="query"
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
            @click="toAddRole"
          >
            添加角色
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
      @row-dblclick="editRole"
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
          <span v-if="column.prop === 'name'">
            <el-link 
              type="primary"
              size="mini"
              @click="editRole(scope.row)"
            >
              {{ scope.row[column.prop] }}
            </el-link>
          </span>
          <el-switch
            v-else-if="column.prop === 'is_active'"
            :value="scope.row.is_active"
            :active-value="true"
            :inactive-value="false"
            active-text="启用"
            inactive-text="禁用"
            @change="switchRoleEnable(scope.row)"
          ></el-switch>
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
            @click="editRole(scope.row)"
            plain
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteRole(scope.row)"
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
      :with-header="true"
      :wrapper-closable="true"
      :visible.sync="show_role_info"
      direction="rtl"
      size="600px"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>{{ view_context.title }}</span>
        </div>
      </template>
      <role-create 
        @close="refreshView"
        :view-context="view_context"
      />
    </el-drawer>
  </div>
</template>

<script>
import { roleMethod, enableRole, disableRole } from "@/api"
import { calculateTableHeight } from "@/utils/table-size"
import BaseSearchForm from "@/components/BaseSearchForm.vue"
import RoleCreate from "./RoleCreate.vue"
import ChangeTableSize from "@/components/changeTableSize/index.vue"

export default {
  name: "RoleList",
  components: { 
    BaseSearchForm,
    RoleCreate,
    ChangeTableSize
  },
  data() {
    return {
      search_items: [
        { label: "角色名称", prop: "name", type: "autocomplete", query: { table: "role", column: "name" } },
        { label: "角色状态", prop: "is_active", type: "select", options: [
          { label: "禁用", value: false },
          { label: "启用", value: true },
        ] },
      ],
      query: {
        name: null,
        is_active: null,

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
        mode: null
      },
      table_columns: [
        { visible: true, label: "角色名称", prop: "name", width: 200, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "状态", prop: "is_active", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "角色描述", prop: "description", width: 600, align: "left", header_align: "center", sortable: false, tooltip: false },
      ],
      table_size: "normal",
      show_role_info: false,
    }
  },
  computed: { 
    tableHeight() { 
      return calculateTableHeight(500, 200)
    },
  },
  mounted() {
    this.getListData()
  },
  methods: {
    handleSearch() {
      this.getListData()
    },
    handleReset() {
      this.query.page_no = 1
      this.getListData()
    },
    async getListData() {

      this.list_loading = true

      const res = await roleMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }

      this.list_loading = false
    },
    toAddRole() {
      this.$router.push("/admin/role/create")
    },
    editRole(row) {
      this.view_context = {
        id: row.id,
        is_dialog: false,
        title: "更新角色信息",
        mode: "edit"
      }
      this.show_role_info = true
    },
    async deleteRole(row) {
      try {
        await this.$confirm(`确认删除当前角色【${ row.name }】`, "删除角色", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await roleMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
          this.getListData()
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    async switchRoleEnable(row) {

      try {

        const message = row.is_active === true 
          ? "此操作将禁用该角色相关使用权限, 是否继续?" 
          : "此操作将解除该角色禁用状态，并恢复相应使用权限, 是否继续?"

        await this.$confirm(message, "切换状态", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning"
        })

        if (row.is_active == true) {
          const res = await disableRole(row.id)
          if (res.status === 0) {
            this.$message({ type: "success", message: "已成功禁用!" })
          }
        } else {
          const res = await enableRole(row.id)
          if (res.status === 0) {
            this.$message({ type: "success", message: "已成功启用!" })
          }
        }

        this.refreshView()
      } catch (error) {
        return this.$message({ type: "info", message: "操作已取消" })
      }
    },
    handleSizeChange (val) {
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
        title: null,
        mode: null
      }
      this.show_role_info = false

      this.getListData()
    },
  }
}
</script>

<style lang="scss" scoped>

</style>