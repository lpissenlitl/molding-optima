<template>
  <div class="roleCreate">
    <el-dialog 
      v-el-drag-dialog
      :title="id?'编辑角色':'新增角色'" 
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
          <el-select v-model="detail_info.company_id">
            <el-option 
              v-for="company in company_options"
              :key="company.value"
              :label="company.label"
              :value="company.value"
            ></el-option>
          </el-select>
        </el-form-item>

        <el-form-item 
          label="角色名称" 
          prop="name"
        >
          <el-input 
            v-model="detail_info.name"
          ></el-input>
        </el-form-item>

        <el-form-item 
          label="角色描述" 
          prop="description"
        >
          <el-input 
            type="textarea" 
            :autosize="{ minRows: 2, maxRows: 4}" 
            v-model="detail_info.description"
          >
          </el-input>
        </el-form-item>

        <el-form-item 
          label="角色权限"
        >
          <el-tree 
            ref="permTree" 
            show-checkbox 
            node-key="id"
            :default-expanded-keys="[1]"
            accordion
            :data="tree_permissions" 
            :props="defaultProps"
          >
            <span class="custom-tree-node" slot-scope="{ node }">
              <span>{{ node.label }}</span>
            </span>
          </el-tree>
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
import { rolesMethod, permissionsMethod, getOptions } from '@/api'

export default {
  props: {
    showUpdate: {
      type: Boolean,
      default: false
    },
    id: {
      type: Number,
      default: null
    }
  },
  data() {
    return {
      detail_info: {
        company_id: null,
        name: null,
        description: null,
        permissions: []
      },
      rules: {
        company_id: [
          { required: true, message: '请选择企业名称', trigger: 'blur' },
        ],
        name: [
          { required: true, message: '角色名称不能为空', trigger: 'blur' }
        ]
      },
      tree_permissions: [],
      defaultProps: {
        children: 'children',
        label: 'name'
      },
      company_options: [],
      loading: false,
      showDialog: this.showUpdate,
    }
  },
  created() {
    this.initView()
  },
  mounted() {
    if (this.id) {
      this.getDetail()
    }
  },
  methods: {
    initView() {
      getOptions("company_option")
      .then(res => {
        if (res.status === 0) {
          this.company_options = res.data
        }
      })

      permissionsMethod.get()
      .then(res => {
        if (res.status === 0) {
          this.tree_permissions = res.data.permissions
        }
      })
    },
    getSelectedPermissions() {
      let checked_nodes = this.$refs.permTree.getCheckedNodes()
      this.detail_info.permissions = []
      checked_nodes.map(item => {
        if (!item.children) {
          this.detail_info.permissions.push({ permission_id: item.id })
        }
      })
    },
    getDetail() {
      rolesMethod.getDetail(this.id)
      .then(res => {
        if (res.status === 0) {
          this.detail_info = res.data
          let select_perms = []
          this.detail_info.permissions.map(item => {
            select_perms.push(item.permission_id)
          })
          this.$refs.permTree.setCheckedKeys(select_perms)
        }
      })
    },
    saveDetail() {
      this.getSelectedPermissions()
      this.$refs.form_info.validate(valid => {
        if (valid) {
          let role_info = {
            company_id: this.detail_info.company_id,
            name: this.detail_info.name,
            description: this.detail_info.description,
            permissions: this.detail_info.permissions
          }
          rolesMethod.add(role_info)
          .then(res => {
            if (res.status === 0) {
              this.$message({message: '新增角色成功。', type: 'success'})
            }
          }).finally( () => {
            this.resetView()
          })
        }
      })
    },
    updateDetail() {
      this.getSelectedPermissions()
      this.$refs.form_info.validate(valid => {
        if (valid) {
          let role_info = {
            company_id: this.detail_info.company_id,
            name: this.detail_info.name,
            description: this.detail_info.description,
            permissions: this.detail_info.permissions
          }
          rolesMethod.edit(role_info, this.id)
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
        name: null,
        description: null,
        permissions: [],
      }
      this.$refs.permTree.setCheckedKeys([])
      this.$emit('close-dialog')
    }
  },
  watch: {
    showUpdate() {
      this.showDialog = this.showUpdate
      if(this.id) {
        this.getDetail()
      }
    }
  }
}
</script>
