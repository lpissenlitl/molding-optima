<template>
  <el-card class="box-card">
    <div>
      <h3>
        角色信息
      </h3>
      <el-form 
        ref="form_info" 
        :model="role_info" 
        :rules="rules" 
        size="mini"
        label-width="6rem"
        label-position="right"
      >
        <el-form-item 
          label="角色名称" 
          prop="name"
        >
          <el-input 
            style="width: 100%;"
            v-model="role_info.name"
            placeholder="请输入角色全称"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="角色编码" 
          prop="code"
        >
          <el-input 
            style="width: 100%;"
            v-model="role_info.code"
            placeholder="唯一标识，如 ROLE_001"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="角色描述" 
          prop="description"
        >
          <el-input 
            style="width: 100%;"
            v-model="role_info.description"
            type="textarea" 
            :autosize="{ minRows: 2, maxRows: 4}" 
            placeholder="简要描述角色职责"
          >
          </el-input>
        </el-form-item>
        <el-form-item 
          label="是否启用" 
          prop="is_active"
        >
          <el-switch v-model="role_info.is_active"></el-switch>
        </el-form-item>
        <el-form-item 
          label="角色权限"
          prop="permission"
        >
          <el-tree 
            ref="permTree" 
            show-checkbox 
            node-key="code"
            accordion
            :default-expanded-keys="defaultExpandedKeys()"
            :data="permission_tree" 
            :props="default_props"
          >
            <span class="custom-tree-node" slot-scope="{ node }">
              <span>{{ node.label }}</span>
            </span>
          </el-tree>
        </el-form-item>
      </el-form>
    </div>
    <div class="floating-actions fixed right">
      <el-button 
        type="danger"
        size="small"
        @click="resetView" 
      >
        重 置
      </el-button>
      <el-button 
        type="primary" 
        size="small"
        @click="saveRoleInfo" 
      >
        {{ role_info.id ? "更  新" : "保  存" }}
      </el-button>
    </div>
  </el-card>
</template>

<script>
import { roleMethod, getPermissionTree } from "@/api"

const initRoleInfo = {
  id: null,
  name: null,
  code: null,
  description: null,
  is_active: true,
  permission_codes: []
}

export default {
  name: "RoleCreate",
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        title: "更新角色信息",
        mode: "create"
      })
    },
  },
  data() {
    return {
      view_context: this.viewContext,
      role_info: structuredClone(initRoleInfo),
      rules: {
        code: [{ required: true, message: "角色编码不能为空", trigger: "blur" }],
        name: [{ required: true, message: "角色名称不能为空", trigger: "blur" }]
      },
      permission_tree: [],
      default_props: {
        children: "children",
        label: "name"
      },
    }
  },
  watch: {
    viewContext: {
      handler: function() {
        this.view_context = this.viewContext
        this.initializeView()
      },
      deep: true,
      immediate: true
    },
  },
  mounted() {
    this.initializeView()
  },
  methods: {
    async initializeView() {
      this.resetView()

      await this.getPermissionTree()

      if (this.view_context.id) {
        this.role_info.id = this.view_context.id
      }

      if (this.role_info.id) {
        await this.getRoleInfo(this.view_context.id)
      }
    },
    defaultExpandedKeys() {
      // 只展示最外层
      return this.permission_tree.map(item => item.code)
    },
    getSelectedPermissions() {
      let checked_permissions = []
      let checked_nodes = this.$refs.permTree.getCheckedNodes()
      let half_checked_nodes = this.$refs.permTree.getHalfCheckedNodes()
      let all_selected_nodes = [...checked_nodes, ...half_checked_nodes]
      all_selected_nodes.map(item => {
        // if (!item.children || item.children.length === 0) {
        //   checked_permissions.push(item.code )
        // }
        checked_permissions.push(item.code )
      })
      return checked_permissions
    },
    selectPermissionNodes() {
      //只选择叶子节点，父节点自动半勾选或勾选

      if (!this.permission_tree || this.permission_tree === 0) {
        return
      }

      const leaf_codes = []
      const statck = [...this.permission_tree.reverse()]
      while (statck.length > 0) {
        const node = statck.pop()
        if (!node.children || node.children.length === 0) {
          leaf_codes.push(node.code)
        } else {
          statck.push(...node.children)
        }
      }
      //选中this.role_info.permission_codes中为叶子结点的节点
      this.role_info.permission_codes.forEach(code => {
        if (leaf_codes.includes(code)) {
          this.$refs.permTree.setChecked(code, true, false)
        }
      })

    },
    async getPermissionTree() {
      const res = await getPermissionTree()
      if (res.status === 0) {
        this.permission_tree = res.data
      }
    },
    async getRoleInfo(id) {
      if (!id) return

      // 获取角色信息
      const res = await roleMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.role_info, res.data)
        this.selectPermissionNodes()
        // this.$refs.permTree?.setCheckedKeys(this.role_info.permission_codes)
      }
    },
    async saveRoleInfo() {
      // 获取角色选中的所有权限

      // 2026-01-29 后端有exclude_codes，前端获取不到权限管理中的权限，角色权限更新时，会把原本已有的但在exclude_codes中的权限排除掉。
      // 暂时在前端处理：权限树节点选择操作时，不影响角色已有的但不在权限树上的权限
      const all_tree_permission_codes = []
      const getNodeAllPermissionCodes = (node) => {
        if (!node.children || node.children.length === 0) {
          all_tree_permission_codes.push(node.code)
        } else {
          all_tree_permission_codes.push(node.code)
          node.children.forEach(child => {
            getNodeAllPermissionCodes(child)
          })
        }
      }
      for (const node of this.permission_tree)
        getNodeAllPermissionCodes(node)
      const before_permission_codes = this.role_info.permission_codes
      const selected_permission_codes = this.getSelectedPermissions()
      const extra_permission_codes = before_permission_codes.filter(code => !all_tree_permission_codes.includes(code))
      const final_permission_codes =  [...new Set([...selected_permission_codes, ...extra_permission_codes])]
      this.role_info.permission_codes = final_permission_codes

      try {
        await this.$refs.form_info.validate() // 成功时 resolve，失败时 reject
      } catch (err) {
        return this.$message({ type: "error", message: "请填写完整信息！" })
      }

      if (this.role_info.id) {
        const res = await roleMethod.edit(this.role_info, this.role_info.id)
        if (res.status === 0) {
          this.$message({ message: "编辑角色信息成功！", type: "success" })
          this.$emit("close")
        }
      } else {
        const res = await roleMethod.add(this.role_info)
        if (res.status === 0) {
          this.$message({ message: "新增角色信息成功！", type: "success" })
          this.$router.push("/admin/role/list")
        }
      }
    },
    resetView() {
      this.role_info = structuredClone(initRoleInfo)
      this.$refs.permTree?.setCheckedKeys([])
    }
  }
}
</script>

<style lang="scss" scoped>
.el-card {
  max-width: 600px;
}
</style>
