<template>
  <div class="userCreate">    
    <el-dialog 
      v-el-drag-dialog
      :title="id?'编辑用户':'新增用户'" 
      :visible.sync="showDialog" 
      :show-update="showUpdate" 
      :close-on-click-modal="false"
      @close="resetView" 
    >
      <el-form 
        ref="form_info" 
        :model="detail_info" 
        :rules="rules" 
        size="mini" 
        label-width="8rem" 
      >
        <el-form-item 
          label="企业名称" 
          prop="company_id"
        >
          <el-select 
            v-model="detail_info.company_id"
            placeholder="请选择"
            style="width:20rem"
          >
            <el-option
              v-for="item in company_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item 
          label="所属组织" 
          prop="group_id"
        >
          <el-select
            ref="groupSelectTree"
            v-model="detail_info.group_id"
            placeholder="请选择"
            style="width:20rem"
          >
            <el-option
              v-for="item in group_options"
              :key="item.id"
              :value="item.id"
              :label="item.name"
              style="height:auto"
              hidden
            >
            </el-option>

            <el-input
              placeholder="输入关键字进行过滤"
              v-model="filterText"
            >
            </el-input>

            <el-tree
              ref="groupTree"
              node-key="id"
              default-expand-all
              accordion
              :data="group_tree"
              :filter-node-method="filterNode"
              :props="defaultProps"
              @node-click="handleNodeClick"
            />
          </el-select>
        </el-form-item>

        <el-form-item 
          label="真实姓名:" 
          prop="engineer" 
        >
          <el-input 
            v-model="detail_info.engineer"
            style="width:20rem" 
          ></el-input>
        </el-form-item>

        <el-form-item 
          label="登录用户名:" 
          prop="name" 
        >
          <el-input 
            v-model="detail_info.name"
            style="width:20rem" 
          ></el-input>
        </el-form-item>

        <el-form-item 
          v-if="!id" 
          label="用户密码:" 
          prop="password" 
        >
          <el-input 
            type="password"
            v-model="detail_info.password"
            style="width:20rem"
          ></el-input>
        </el-form-item>

        <el-form-item 
          label="电子邮箱:" 
          prop="email"
        >
          <el-input
            v-model="detail_info.email"
            style="width:20rem"
          ></el-input>
        </el-form-item>

        <el-form-item 
          label="联系电话:" 
          prop="phone" 
        >
          <el-input 
            v-model="detail_info.phone"
            style="width:20rem"
          ></el-input>
        </el-form-item>

        <el-form-item 
          label="数据访问" 
          prop="group_ids"
        >
          <el-select
            ref="dataAllowTree"
            v-model="detail_info.group_ids"
            placeholder="请选择"
            style="width:20rem"
            multiple
            @remove-tag="resetTreeChecked"
          >
            <el-option
              v-for="item in group_options"
              :key="item.id"
              :value="item.id"
              :label="item.name"
              style="height:auto"
              hidden
            >
            </el-option>

            <el-input
              placeholder="输入关键字进行过滤"
              v-model="filterText"
            >
            </el-input>

            <el-tree
              ref="allowTree"
              node-key="id"
              accordion
              show-checkbox
              :data="group_tree"
              :filter-node-method="filterNode"
              :props="defaultProps"
              :default-checked-keys="detail_info.group_ids"
              @check-change="handleCheckChange"
              :default-expanded-keys="[1]"
            />
          </el-select>
        </el-form-item>

        <el-form-item 
          label="关联角色:" 
          prop="role_ids"
        >
          <el-select 
            v-model="detail_info.role_ids" 
            multiple 
            placeholder="请选择"
            style="width:20rem" 
          >
            <el-option 
              v-for="item in role_options" 
              :key="item.value" 
              :label="item.label" 
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="激活">
          <el-switch 
            v-model="detail_info.enable"
          ></el-switch>
        </el-form-item>

        <el-form-item 
          v-if="is_super"
          label="超级管理员" 
        >
          <el-switch 
            v-model="detail_info.is_super" 
            :disabled="!is_super"
          ></el-switch>
        </el-form-item>
      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button 
          type="danger"
          @click="resetView" 
          size="small"
          style="width:6rem"
        >
          返  回
        </el-button>
        <el-button 
          v-if="id" 
          type="primary" 
          :loading="loading" 
          @click="updateDetail" 
          size="small"
          style="width:6rem"
        >
          更  新
        </el-button>
        <el-button
          v-else 
          type="primary" 
          :loading="loading" 
          @click="saveDetail" 
          size="small"
          style="width:6rem"
        >
          保  存
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getOptions, usersMethod, groupMethod } from '@/api'

export default {
  props: {
    showUpdate: {
      type: Boolean,
      default: false
    },
    id: {
      type: Number,
      default: null
    },
  },
  data() {
    return {
      is_super: this.$store.state.user.userinfo.is_super,
      detail_info: {
        company_id: null,
        company_name: null,
        group_id: null,
        group_name: null,
        engineer: null,
        name: null,
        password: null,
        email: null,
        phone: null,
        role_ids: [],
        group_ids: [],
        enable: true,
        is_super: false,        
      },
      rules: {
        company_id: [
          { required: true, message: '请选择企业名称', trigger: 'blur' },
        ],
        group_id: [
          { required: true, message: '请选择组织名称', trigger: 'blur' },
        ],
        name: [
          { required: true, message: '请输入登录用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入登录密码'},
          { min: 6,message: '密码长度需要大于等于6' }
        ],
        engineer: [
          { required: true, message: '请填入用户姓名', trigger: 'blur' }
        ],
        group_ids: [
          { required: true, message: '请至少分配一个组织用于数据访问', trigger: 'blur' }
        ],
        role_ids: [
          { required: true, message: '请至少分配一个角色', trigger: 'blur' }
        ],
      },
      company_options: [],
      // department_options: [],
      group_options: [],
      role_options: [],
      defaultProps: {
        children: 'children',
        label: 'name',
        id:'id',
      },
      filterText: "",
      group_tree: [],
      loading: false,
      showDialog: this.showUpdate,
    }
  },
  created() {

  },
  mounted() {
    getOptions("company_option")
    .then(res => {
      if (res.status === 0) {
        this.company_options = res.data
      }
    })

    if (this.id) {
      this.getDetail()
    }
  },
  methods: {
    getDetail() {
      usersMethod.getDetail(this.id)
      .then(res => {
        if (res.status === 0) {
          this.detail_info = res.data
        }
      })
    },
    saveDetail() {
      this.$refs.form_info.validate(valid => {
        if (valid) {
          let user_info = {
            company_id: this.detail_info.company_id,
            group_id: this.detail_info.group_id,
            name: this.detail_info.name,
            password: this.detail_info.password,
            engineer: this.detail_info.engineer,
            email: this.detail_info.email,
            phone: this.detail_info.phone,
            enable: this.detail_info.enable,
            is_super: this.detail_info.is_super,
            group_ids: this.detail_info.group_ids,
            role_ids: this.detail_info.role_ids,
          }

          usersMethod.add(user_info)
          .then(res => {
            if (res.status === 0) {
              this.$message({message: '新增成功。', type: 'success'})
            }
          }).finally( () => {
            this.resetView()
          })
        }
      })
    },
    updateDetail() {
      this.$refs.form_info.validate(valid => {
        if (valid) {
          let user_info = {
            company_id: this.detail_info.company_id,
            group_id: this.detail_info.group_id,
            name: this.detail_info.name,
            password: this.detail_info.password,
            engineer: this.detail_info.engineer,
            email: this.detail_info.email,
            phone: this.detail_info.phone,
            enable: this.detail_info.enable,
            is_super: this.detail_info.is_super,
            group_ids: this.detail_info.group_ids,
            role_ids: this.detail_info.role_ids,
          }

          usersMethod.edit(user_info, this.id)
          .then(res => {
            if (res.status === 0) {
              this.$message({message: '编辑成功。', type: 'success'})
            }
          }).finally( () => {
            this.resetView()
          })
        }
      })
    },
    resetView() {
      this.detail_info = {
        company_id: null,
        company_name: null,
        group_id: null,
        group_name: null,
        engineer: null,
        name: null,
        password: null,
        email: null,
        phone: null,
        role_ids: [],
        group_ids: [],
        enable: true,
        is_super: false,        
      }
      this.$emit('close-dialog')
    },
    filterNode(value, data) {
      if (!value) return true;
      return data.name.indexOf(value) !== -1;
    },
    handleNodeClick(data, node, el) {
      if (data.children.length == 0) {
        this.detail_info.group_id = data.id
        this.detail_info.group_name = data.name
        this.detail_info.group_ids = [ data.id ]
      }
    },
    resetTreeChecked() {
      this.$refs.allowTree.setCheckedKeys(this.detail_info.group_ids)
    },
    handleCheckChange(data, node, el) {
      let checkedNodes = this.$refs.allowTree.getCheckedNodes(true)
      let nodeIds = []
      for (let i = 0; i < checkedNodes.length; ++i) {
        nodeIds.push(checkedNodes[i].id)
      }
      this.detail_info.group_ids = nodeIds
    },
    constructViewModel() {
      // 构建一级节点
      this.group_tree = []
      for (let i = 0; i < this.group_options.length; ++i) {
        if (!this.group_options[i].parent_id) {
          let node = JSON.parse(JSON.stringify(this.group_options[i]))
          this.group_tree.push(node)
          this.appendChildren(node)
        }
      }
    },
    appendChildren(parent) {
      // 构建子节点
      if (!parent.children) {
        parent.children = []
      }

      for (let i = 0; i < this.group_options.length; ++i) {
        if (this.group_options[i].parent_id == parent.id) {
          let node = JSON.parse(JSON.stringify(this.group_options[i]))
          parent.children.push(node)
          this.appendChildren(node)
        } 
      }
    },
    getGroupInfo(company_id) {
      this.group_options = []
      groupMethod.get({
        "company_id": company_id
      }).then(res => {
        if (res.status == 0) {
          if (res.data && res.data.total > 0) {
            this.group_options = res.data.items
            this.constructViewModel()
          }
        } 
      })
    },
    getRoleInfo(company_id) {
      this.role_options = []
      getOptions("role_option", { 
        "company_id": company_id 
      }).then(res => {
        if (res.status === 0) {
          this.role_options = res.data
        }
      })
    }
  },
  watch: {
    showUpdate() {
      this.showDialog = this.showUpdate
      if (this.id) {
        this.getDetail()
      }
    },
    filterText(val) {
      this.$refs.tree.filter(val);
    },
    "detail_info.company_id" () {
      this.getGroupInfo(this.detail_info.company_id)
      this.getRoleInfo(this.detail_info.company_id)
    },
  }
}
</script>
<style lang="scss" scoped>

</style>