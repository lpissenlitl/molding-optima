<template>
  <div class="roleInfo">
    <div class="toolbar">
      <el-form 
        :inline="true" 
        :model="query" 
        size="mini"
        label-width="6rem"
      >
        <el-form-item 
          label="企业名称"
        >
          <el-input 
            v-model="query.company_name" 
            clearable 
            style="width:10rem"
          />
        </el-form-item>

        <el-form-item 
          label="角色名称"
        >
          <el-input 
            v-model="query.name"
          ></el-input>
        </el-form-item>

        <el-form-item style="float:right">
          <el-button 
            type="primary" 
            @click="queryListData" 
            style="width:6rem"
          >
            搜 索
          </el-button>
          <el-button 
            type="danger" 
            @click="reloadListData" 
            style="width:6rem"
          >
            重 置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="row-toolbutton">
      <div style="float:left">
        <el-button-group>
          <el-button
            size="mini"
            @click="changeTableSize('small')"
          >
            small
          </el-button>
          <el-button
            size="mini"
            @click="changeTableSize('normal')"
          >
            normal
          </el-button>
          <el-button
            size="mini"
            @click="changeTableSize('large')"
          >
            large
          </el-button>
        </el-button-group>
      </div>

      <div style="float:right">
        <el-button-group>
          <el-button
            size="mini"
            type="primary"
            icon="el-icon-plus"
            @click="addRole"
          >
            添加角色
          </el-button>
          <el-button
            type="danger"
            size="mini"
            icon="el-icon-delete"
            @click="removeRole"
          >
            删除角色
          </el-button>
        </el-button-group>
      </div>
    </div>

    <el-table 
      ref="roleTable"
      v-loading="listLoading"
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      :height="tableHeight"
      :row-style="tableRowStyle"
      :cell-style="tableCellStyle"
      :header-cell-style="tableHeaderStyle"
      :data="listData.items"
      @sort-change="sortList"
      @row-dblclick="rowDoubleClicked"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="40"
        :selectable="setRowSelectable"
      >
      </el-table-column>
      <el-table-column 
        type="index"
        label="序号" 
        width="80"
        align="center"
      >
      </el-table-column>
      <template v-for="column, index in columns_setting">
        <el-table-column
          v-if="column.visible"
          :key="index"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width"
          :header-align="column.header_align"
          :align="column.align"
          :sortable="column.sortable"
          :show-overflow-tooltip="column.tooltip"
        >
          <template slot-scope="scope">
            <span v-if="column.prop === 'name'">
              <el-link 
                type="primary"
                size="mini"
                @click="updateRole(scope.row)"
              >
                {{ scope.row[column.prop] }}
              </el-link>
            </span>
            <span v-else-if="column.prop === 'deleted'">
              <el-tag 
                size="mini"
                :type="scope.row[column.prop] == 0 ? 'success' : 'info'"
                :hit="true"
                @click="updateRoleStatus(scope.row)"
              >
                {{ scope.row[column.prop] == 0 ? "启用" : "禁用" }}
              </el-tag>
            </span>
            <span v-else>
              {{ scope.row[column.prop] }}
            </span>
          </template>
        </el-table-column>
      </template>
    </el-table>
    <div class="pagination">
      <el-pagination 
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="query.page_no"
        :page-sizes="$store.state.app.pageSizeArray"
        :page-size="query.page_size"
        :total="listData.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
    <role-detail 
      :id="role_detail.id" 
      :show-update.sync="showRoleDetail" 
      @close-dialog="refreshView"
    >
    </role-detail>
  </div>
</template>

<script>
import RoleDetail from './subView/roleDetail.vue'
import { rolesMethod, } from '@/api'

export default {
  components: { RoleDetail },
  data() {
    return {
      query: {
        company_name: null,
        name: null,
        page_size: 100,
        page_no: 1,
      },
      listData: {},
      listLoading: false,
      multipleSelection: [],
      role_detail: {
        id: null
      },
      columns_setting: [
        { id: 0, visible: true, label: "企业名称", prop: "company_name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { id: 1, visible: true, label: "角色名称", prop: "name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { id: 2, visible: true, label: "状态", prop: "deleted", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { id: 3, visible: true, label: "角色描述", prop: "description", width: 300, align: "left", header_align: "center", sortable: false, tooltip: false},
      ],
      tableHeaderStyle: { 'background-color': 'lightblue', 'color': '#000', 'font-size': '12px', 'padding': '10px 0px' },
      tableRowStyle: { },
      tableCellStyle: { 'padding': '7px 0px' },
      tableHeight: '45rem',
      showRoleDetail: false,
    }
  },
  created() {

  },
  mounted() {
    this.$nextTick(function() {
    this.tableHeight = window.innerHeight - this.$el.offsetTop - 160
    let self = this
    window.onresize = function() {
        self.tableHeight = window.innerHeight - self.$el.offsetTop - 160
      }
    })
    this.getListData()
  },
  methods: {
    getListData() {
      this.listLoading = true
      rolesMethod.get(this.query)
      .then(res => {
        if (res.status === 0) {
          this.listData = res.data
        }
      })
      .finally( () => {
        this.listLoading = false
      })
    },
    queryListData() {
      this.getListData()
    },
    reloadListData() {
      this.query.company_name = null
      this.query.name = null
      this.getListData()
    },
    changeTableSize(size) {
      if (size === "small") {
        this.tableCellStyle = { 'padding': '1px 0px' }
      } else if (size === "normal") {
        this.tableCellStyle = { 'padding': '7px 0px' }
      } else if (size === "large") {
        this.tableCellStyle = { 'padding': '12px 0px' }
      } else {
        ;
      }
    },
    addRole() {
      this.role_detail.id = null
      this.showRoleDetail = true
    },
    removeRole() {
      if (this.multipleSelection.length == 0) {
        this.$message('无选中项。');
        return
      }
      let role_id_list = []
      let role_name_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        role_id_list.push(this.multipleSelection[i].id)
        role_name_list.push(this.multipleSelection[i].name)
      }
      let role_name_desc = role_name_list.join("、")
      this.$confirm(`确认删除以下角色?  ${role_name_desc}`, '删除角色', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        rolesMethod.multipleDel({
          role_id_list: role_id_list
        }).then(res => {
          if(res.status === 0) {
            this.$message({ type: 'success', message: '删除成功!' })
            this.getListData()
          }
        })
      }).catch(() => {
        this.$message({
          type: 'info',
          message: '已取消删除'
        })
      })
    },
    sortList(sort) {
      this.query.$orderby = sort.prop
      this.getListData()
    },
    setRowSelectable(row, index) {
      if (row.deleted == 0) {
        return true;
      } else {
        return false;
      }
    },
    handleSelectionChange(val) {
      this.multipleSelection = val;
    },
    updateRole(row) {
      this.role_detail.id = row.id
      this.showRoleDetail = true
    },
    updateRoleStatus(row) {
      if (row.deleted == 0) {
        this.$confirm('此操作将禁用该角色相关使用权限, 是否继续?', '切换状态', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          rolesMethod.edit({ deleted: 1 }, row.id)
          .then(res => {
            if (res.status === 0) {
              this.$message({ type: 'success', message: '已成功禁用!' });
              this.refreshView()
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '操作已取消'
          });          
        });
      } else if (row.deleted == 1) {
        this.$confirm('此操作将解除该角色禁用状态，并恢复相应使用权限, 是否继续?', '切换状态', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          rolesMethod.edit({ deleted: 0 }, row.id)
          .then(res => {
            if (res.status === 0) {
              this.$message({ type: 'success', message: '已恢复启用状态!' });
              this.refreshView()
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '操作已取消'
          });          
        });
      }
    },
    rowDoubleClicked(row) {
      this.updateRole(row)
    },
    refreshView() {
      this.role_detail.id = null
      this.showRoleDetail = false
      this.getListData()
    },
    handleSizeChange (val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange (val) {
      this.query.page_no = val
      this.getListData()
    }
  }
}
</script>

<style lang="scss" scoped>

</style>