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
            @click="toAddUser"
          >
            添加用户
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
      @row-dblclick="editUser"
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
          <span v-if="column.prop === 'username'">
            <el-link 
              type="primary"
              size="mini"
              @click="editUser(scope.row)"
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
            @change="switchUserEnable(scope.row)"
          ></el-switch>
          <span v-else-if="column.prop === 'role_name'">
            {{ scope.row.is_superuser ? '超级管理员' : scope.row.role_name }}
          </span>
          <span v-else-if="column.prop === 'reset_password'">
            <el-button 
              type="primary"
              size="mini"
              round
              @click="resetPassword(scope.row)"
            >
              重置
            </el-button>
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
            @click="editUser(scope.row)"
            plain
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteUser(scope.row)"
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
      :visible.sync="show_user_info"
      direction="rtl"
      size="600px"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>{{ view_context.title }}</span>
        </div>
      </template>
      <user-create
        @close="refreshView"
        :view-context="view_context"
      />
    </el-drawer>
  </div>
</template>

<script>
import { userMethod, enableUser, disableUser, resetPassword } from "@/api"
import { calculateTableHeight } from "@/utils/table-size"
import BaseSearchForm from "@/components/BaseSearchForm.vue"
import UserCreate from "./UserCreate.vue"
import ChangeTableSize from "@/components/changeTableSize/index.vue"

export default {
  name: "UserList",
  components: { 
    BaseSearchForm,
    UserCreate,
    ChangeTableSize 
  },
  data() {
    return {
      search_items: [
        { label: "用户名", prop: "username", type: "autocomplete", query: { table: "user", column: "username" } },
        { label: "用户姓名", prop: "engineer_name", type: "autocomplete", query: { table: "user", column: "engineer_name" } },
        { label: "角色名称", prop: "roles__name", type: "autocomplete", query: { table: "role", column: "name" } },
        { label: "用户状态", prop: "is_active", type: "select", options: [
          { label: "禁用", value: false },
          { label: "启用", value: true },
        ] },
      ],
      query: {
        username: null,
        engineer_name: null,
        roles__name: null,
        is_active: null,

        page_size: 100, 
        page_no: 1, 
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
        { visible: true, label: "用户名", prop: "username", width: 200, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "角色名称", prop: "role_name", width: 200, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "用户姓名", prop: "engineer_name", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "状态", prop: "is_active", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "电子邮箱", prop: "email", width: 200, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "电话号码", prop: "phone", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "密码重置", prop: "reset_password", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      table_size: "normal",
      show_user_info: false,
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

      const res = await userMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
        this.list_data.items.forEach(item => {
          item.role_name = item.roles?.map(role => role.name).join(", ")
        })
      }
      this.list_loading = false
    },
    toAddUser() {
      this.$router.push("/admin/user/create")
    },
    async resetPassword(row) {
      try {
        const new_password = await this.$prompt(`确定要重置 ${row.username} 的密码？`, "重置密码", {
          confirmButtonText: "确认",
          cancelButtonText: "取消",
          inputPlaceholder: "请输入新的密码",
          type: "warning",
          inputValidator: (value) => {
            if (!value || value.length < 6) {
              return "新密码长度需要大于等于6"
            }
            return true
          }
        })

        const res = await resetPassword(row.id, { password: new_password.value })
        if (res.status === 0) {
          let msg = "用户" + row.username + " 密码重置成功，新密码为：" + new_password.value
          this.$message({ type: "success", message: msg, duration: 2000, showClose: true })
        }

      } catch (error) {
        return this.$message({ type: "info", message: "操作已取消" })
      }
    },
    editUser(row) {
      this.view_context = {
        id: row.id,
        is_dialog: true,
        title: "更新用户信息",
        mode: "edit"
      }

      this.show_user_info = true
    },
    async deleteUser(row) { 
      try {
        await this.$confirm(`确认删除当前用户【${ row.username }】`, "删除角色", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await userMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
        }

        this.getListData()
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    async switchUserEnable(row) {

      try {
        const message = row.is_active === true 
          ? "此操作将禁用该人员使用权限, 是否继续?" 
          : "此操作将解除该用户禁用状态，并恢复相应使用权限, 是否继续?"
          
        await this.$confirm(message, "切换状态", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning"
        })

        if (row.is_active == true) {
          const res = await disableUser(row.id)
          if (res.status === 0) {
            this.$message({ type: "success", message: "已成功禁用!" })
          }
        } else {
          const res = await enableUser(row.id)
          if (res.status === 0) {
            this.$message({ type: "success", message: "已成功启用!" })
          }
        }

        this.refreshView()
      } catch (error) {
        this.$message({ type: "info", message: "取消操作" })
        return
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
      this.show_user_info = false

      this.getListData()
    },
  },
}
</script>

<style lang="scss" scoped>

</style>
