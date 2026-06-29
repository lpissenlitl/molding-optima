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
            @click="toAddCompany"
          >
            添加公司
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
      @row-dblclick="editCompany"
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
              @click="editCompany(scope.row)"
            >
              {{ scope.row[column.prop] }}
            </el-link>
          </span>
          <template v-else-if="column.prop === 'action_enter'"> 
            <el-button
              :type="isTenantAdmin(scope.row) ? 'primary' : 'success'"
              size="mini"
              @click="switchTenantAdmin(scope.row)"
              round
            >
              {{ isTenantAdmin(scope.row) ? '退出' : '接管' }}
            </el-button>
          </template>
          <el-switch
            v-else-if="column.prop === 'is_active'"
            :value="scope.row.is_active"
            :active-value="true"
            :inactive-value="false"
            active-text="启用"
            inactive-text="禁用"
            @change="switchTenantEnable(scope.row)"
          ></el-switch>
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
            @click="editCompany(scope.row)"
            plain
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteCompany(scope.row)"
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
      :visible.sync="show_company_info"
      direction="rtl"
      size="600px"
    >
      <template #title>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>{{ view_context.title }}</span>
        </div>
      </template>
      <company-create 
        @close="refreshView"
        :view-context="view_context"
      />
    </el-drawer>
  </div>
</template>

<script>
import { 
  companyMethod, enableCompany, 
  disableCompany, assumeCompany, releaseCompany
} from "@/api"
import CompanyCreate from "./CompanyCreate.vue"
import BaseSearchForm from "@/components/BaseSearchForm.vue"
import ChangeTableSize from "@/components/changeTableSize/index.vue"
import { UserModule } from "@/store/modules/user"
import { calculateTableHeight } from "@/utils/table-size"

const tier_level_map = {
  0: "基础版",
  1: "标准版",
  2: "高级版",
  3: "企业版"
}

export default {
  name: "CompanyList",
  components: { 
    CompanyCreate,
    BaseSearchForm,
    ChangeTableSize
  },
  data() {
    return {
      search_items: [
        { label: "公司名称", prop: "name", type: "autocomplete", query: { table: "company", column: "name" } },
        { label: "所属行业", prop: "industry", type: "autocomplete", query: { table: "company", column: "industry" } },
        { label: "公司状态", prop: "is_active", type: "select", options: [
          { label: "禁用", value: false },
          { label: "启用", value: true },
        ] },
      ],
      query: {
        name: null,
        industry: null,
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
        { visible: true, label: "公司名称", prop: "name", width: 200, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "所属行业", prop: "industry", width: 200, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "权限等级", prop: "tier_level", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false, map: tier_level_map }, 
        { visible: true, label: "状态", prop: "is_active", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "企业管理", prop: "action_enter", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "公司描述", prop: "description", width: 600, align: "left", header_align: "center", sortable: false, tooltip: false }
      ],
      table_size: "normal",
      show_company_info: false,
    }
  },
  computed: { 
    tableHeight() { 
      return calculateTableHeight(500, 220)
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

      const res = await companyMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }

      this.list_loading = false
    },
    toAddCompany() {
      this.$router.push("/admin/company/create")
    },
    isTenantAdmin(row) {
      const is_tenant_admin = UserModule.is_tenant_admin
      const in_tenant = UserModule.company_id == row.id
      return in_tenant && is_tenant_admin
    },
    async switchTenantAdmin(row) {
      
      try {
        // 二次确认
        let msg = ""
        let title = ""
        if (this.isTenantAdmin(row)) {
          msg = "确认退出接管【" + row.name + "】？"
          title = "退出接管"
        } else {
          msg = "确认接管【" + row.name + "】？"
          title = "接管公司"
        }

        await this.$confirm(msg, title, {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        if (this.isTenantAdmin(row)) {
        // 退出当前租户
          const res = await releaseCompany(row.id)
          if (res.status === 0) {
            this.$message({ type: "success", message: "已退出当前租户。!" })
          }
        } else {
        // 进入当前租户
          const res = await assumeCompany(row.id)
          if (res.status === 0) {
            this.$message("已进入租户【" + row.name + "】。")
          }
        }

        // 更新用户信息
        await this.$store.dispatch("GetInfo")

        this.refreshView()

      } catch (error) {
        this.$message({ type: "info", message: "取消操作" })
        return
      }
    },
    editCompany(row) {
      this.view_context = {
        id: row.id,
        is_dialog: false,
        title: "更新公司信息",
        mode: "edit"
      }
      
      this.show_company_info = true
    },
    async deleteCompany(row) {
      try {
        await this.$confirm(`确认删除当前公司【${ row.name }】`, "删除公司", {
          confirmButtonText: "确定",        
          cancelButtonText: "取消",
          type: "warning"
        })

        const res = await companyMethod.delete(row.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "删除成功!" })
        }

        this.getListData()
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })
      }
    },
    async switchTenantEnable(row) {
      const message = row.is_active === true 
        ? "此操作将禁用该公司下任何人员使用权限, 是否继续?" 
        : "此操作将解除该公司禁用状态，并恢复所有信息, 是否继续?"

      try {
        await this.$confirm(message, "切换状态", { 
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning" 
        })

        if (row.is_active === true) {
          const res = await disableCompany(row.id)
          if (res.status === 0) {
            this.$message({ type: "success", message: "已成功禁用" })
          }
        } else {
          const res = await enableCompany(row.id)
          if (res.status === 0) {
            this.$message({ type: "success", message: "已恢复启用" })
          }
        }

        this.refreshView()
      } catch (error) {
        return this.$message({ type: "info", message: "操作已取消" })
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
        mode: null
      }
      this.show_company_info = false

      this.getListData()
    },
  }
}
</script>

<style lang="scss" scoped>

</style>