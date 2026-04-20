<template>
  <div>
    <div class="toolbar">
      <el-form 
        :inline="true" 
        :model="query" 
        size="mini"
        label-width="6rem"
      >
        <el-form-item label="登录名">
          <el-input
            v-model="query.name"
            clearable 
            style="width:10rem"
          />
        </el-form-item>

        <el-form-item label="用户姓名">
          <el-input
            v-model="query.engineer" 
            clearable 
            style="width:10rem"
          />
        </el-form-item>

        <el-form-item style="float:right">
          <el-button 
            type="primary" 
            @click="getListData(true)" 
            style="width:6rem"
          >
            搜索
          </el-button>
          <el-button 
            type="danger" 
            @click="reloadListData" 
            style="width:6rem"
          >
            重置
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
            @click="addUser"
          >
            添加用户
          </el-button>
          <el-button
            type="danger"
            size="mini"
            icon="el-icon-remove"
            @click="removeUser"
          >
            删除用户
          </el-button>
        </el-button-group>
      </div>
    </div>
    <el-table
      ref="userTable"
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
        width="60"
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
                @click="updateUser(scope.row)"
              >
                {{ scope.row[column.prop] }}
              </el-link>
            </span>
            <span v-else-if="column.prop === 'enable'">
              <el-tag
                size="mini"
                :type="scope.row.enable ? 'success': 'info'"
                :hit="true"
                @click="updateUserStatus(scope.row)"
              >
                {{ scope.row.enable ? '激活' : '禁用' }}
              </el-tag>
            </span>
            <span v-else-if="column.prop === 'roles_desc'">
              {{ scope.row.is_super ? '超级管理员' : scope.row.roles_desc }}
            </span>
            <span v-else-if="column.prop === 'app_id'">
              <el-button 
                type="primary" 
                icon="el-icon-edit" 
                circle
                size="mini"
                style="margin-right: 5px;"
                @click="setAppID(scope.row)"
              ></el-button>
              {{ scope.row.app_id ? scope.row.app_id : "None" }}
            </span>
            <span v-else-if="column.prop === 'operator'">
              <el-button 
                type="primary"
                size="mini"
                @click="resetPassword(scope.row)"
              >
                重置密码
              </el-button>
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
    <user-detail
      :id="user_detail.id"
      :show-update.sync="showUserDetail"
      @close-dialog="refreshView"
    >
    </user-detail>
  </div>
</template>

<script>
import UserDetail from './subView/userDetail.vue'
import { resetPassword } from '@/api/login'
import { usersMethod, getOptions, setUserAppID } from '@/api'
import { UserModule } from '@/store/modules/user'

export default {
  components: { UserDetail },
  data() {
    return {
      query: {
        company_id: UserModule.company_id,
        department_name: null,
        name: null,
        engineer: null,
        page_size: 100, 
        page_no: 1, 
      },
      company_list: [],
      department_list: [],
      listData: {},
      listLoading: false,
      multipleSelection: [],
      user_detail: {
        id: null
      },
      columns_setting: [
        { visible: true, label: "登录名", prop: "name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "组织", prop: "group_name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "角色", prop: "roles_desc", width: 200, align: "center", header_align: "center", sortable: false, tooltip: true}, 
        { visible: true, label: "用户姓名", prop: "engineer", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "状态", prop: "enable", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "电子邮箱", prop: "email", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "电话号码", prop: "phone", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: false, label: "APP-ID", prop: "app_id", width: 200, align: "left", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "操作", prop: "operator", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false}, 
      ],
      tableHeaderStyle: { 'background-color': 'lightblue', 'color': '#000', 'font-size': '12px', 'padding': '10px 0px' },
      tableRowStyle: { },
      tableCellStyle: { 'padding': '7px 0px' },
      tableHeight: '45rem',
      showUserDetail: false,
    }
  },
  created() {
    this.initView()
  },
  mounted() {
    this.$nextTick(function() {
    this.tableHeight = window.innerHeight - this.$el.offsetTop - 150
    let self = this
    window.onresize = function() {
      self.tableHeight = window.innerHeight - self.$el.offsetTop - 150
      }
    })
    this.getListData()
  },
  methods: {
    initView() {
      // 获取部门列表(含部门id)
      getOptions("department_option", { company_id: 0 })
      .then(res => {
        if (res.status === 0) {
          this.department_list = res.data
        }
      })

      if (UserModule.is_super) {
        this.columns_setting.forEach(item => {
          if (item.prop == "app_id") {
            item.visible = true;
          }
        });
      }
    },
    getListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      this.listLoading = true
      usersMethod.get(this.query)
      .then(res => {
        if(res.status === 0) {
          this.listData = res.data
        }
      })
      .finally( () => {
        this.listLoading = false
      })
    },
    reloadListData() {
      this.query.company_id = UserModule.company_id
      this.query.department_name = null
      this.query.name = null
      this.query.engineer = null
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
    addUser() {
      this.user_detail.id = null
      this.showUserDetail = true
    },
    removeUser() {
      if (this.multipleSelection.length == 0) {
        this.$message('无选中项。');
        return
      }
      let user_id_list = []
      let user_name_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        user_id_list.push(this.multipleSelection[i].id)
        user_name_list.push(this.multipleSelection[i].engineer)
      }
      let user_name_desc = user_name_list.join("、")
      this.$confirm(`确认删除一下用户？${user_name_desc}`, '删除用户', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        usersMethod.multipleDel({
          user_id_list: user_id_list
        }).then(res => {
          if(res.status === 0){
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
      if (row.enable) {
        return true;
      } else {
        return false;
      }
    },
    handleSelectionChange(val) {
      this.multipleSelection = val;
    },
    updateUser(row) {
      this.user_detail.id = row.id
      this.showUserDetail = true
    },
    updateUserStatus(row) {
      if (row.enable == 1) {
        this.$confirm('此操作将禁用该人员使用权限, 是否继续?', '切换状态', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          usersMethod.edit({ enable: 0 }, row.id)
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
      } else if (row.enable == 0) {
        this.$confirm('此操作将启用该人员使用权限, 是否继续?', '切换状态', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          usersMethod.edit({ enable: 1 }, row.id)
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
    generateRandomString(length) {
      const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
      const timestamp = Date.now().toString(36)
      let result = timestamp;
      for (let i = 0; i < length; i++) {
          result += characters.charAt(Math.floor(Math.random() * characters.length));
      }
      return result;
    },
    setAppID(row) {
      let app_id = this.generateRandomString(10);
      this.$confirm('此操作将为该用户创建APP-ID, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        setUserAppID({ "app_id": app_id }, row.id)
        .then(res => {
          if (res.status === 0) {
            this.$message({ type: 'success', message: '创建成功!' });
            this.refreshView();
          }
        })
      }).catch(() => {
        this.$message({
          type: 'info',
          message: '操作已取消'
        });          
      });
    },
    resetPassword(row) {
      this.$prompt(`确定要重置 ${row.name} 的密码？`, '重置密码', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        inputPlaceholder: '请输入新的密码',
        type: 'warning',
        inputValidator: (value) => {
          if (!value || value.length < 6) {
            return '新密码长度需要大于等于6'
          }
          return true
        }
      }).then(({ value })=> {
        resetPassword(row.id, { new_password:value })
        .then(res => {
          if (res.status === 0) {
            let msg = '用户' + row.name + ' 密码重置成功，新密码为：' + res.data.password
            this.$message({ type: 'success', message: msg, duration: 2000, showClose: true })
          }
        })
      }).catch(() => {
        this.$message({ type: 'success', message: "操作已取消!", duration: 2000, showClose: true })
      })
    },
    rowDoubleClicked(row) {
      this.updateUser(row)
    },
    refreshView() {
      this.user_detail.id = null
      this.showUserDetail = false
      this.getListData(true)
    },
    handleSizeChange (val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange (val) {
      this.query.page_no = val
      this.getListData()
    },
  },
  watch: {

  }
}
</script>

<style lang="scss" scoped>

</style>
