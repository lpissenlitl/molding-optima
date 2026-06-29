<template>
  <el-card class="box-card">
    <div>
      <h3>
        用户信息
      </h3>
      <el-form 
        ref="form_info" 
        :model="user_info" 
        :rules="rules" 
        size="mini" 
        label-width="8rem"
        label-position="right"
      >
        <el-form-item 
          label="所属组织" 
          prop="organization_id"
        >
          <el-select
            style="width: 100%;"
            v-model="user_info.organization_id"
            placeholder="请选择用户所属组织"
          >
            <el-option
              v-for="item in org_list"
              :key="item.id"
              :value="item.id"
              :label="item.name"
              style="height:auto"
              hidden
            >
            </el-option>
            <el-input
              placeholder="输入关键字进行过滤"
              v-model="belong_filter_text"
            >
            </el-input>
            <el-tree
              ref="organizationTree"
              node-key="id"
              default-expand-all
              accordion
              :props="default_props"
              :data="org_tree"
              :filter-node-method="filterNode"
              :expand-on-click-node="false"
              @node-click="handleNodeClick"
            />
          </el-select>
        </el-form-item>
        <el-form-item 
          label="用户名" 
          prop="username" 
        >
          <el-input 
            style="width: 100%;"
            v-model="user_info.username"
            @input="handleUsernameInput"
            placeholder="请输入登录用户名"
          />
        </el-form-item>
        <el-form-item 
          v-if="!user_info.id" 
          label="密码" 
          prop="password" 
        >
          <el-input 
            style="width: 100%;"
            v-model.trim="user_info.password"
            oninput="value=value.replace(/[^A-Z0-9a-z!@#$%.]/g, '')"
            placeholder="请输入登录密码"
          />
        </el-form-item>
        <el-form-item 
          label="用户姓名" 
          prop="engineer_name" 
        >
          <el-input 
            style="width: 100%;"
            v-model.trim="user_info.engineer_name"
            placeholder="请输入真实姓名"
          />
        </el-form-item>
        <el-form-item 
          label="电子邮箱"
          prop="email"
        >
          <el-input
            style="width: 100%;"
            v-model="user_info.email"
            placeholder="请输入邮箱"
          />
        </el-form-item>
        <el-form-item 
          label="联系电话" 
          prop="phone" 
        >
          <el-input 
            style="width: 100%;"
            v-model="user_info.phone"
            placeholder="请输入联系电话"
          />
        </el-form-item>
        <el-form-item 
          label="飞书ID" 
          prop="feishu_id" 
        >
          <el-input 
            style="width: 100%;"
            v-model="user_info.feishu_id"
            placeholder="用于消息待办"
          />
        </el-form-item>
        <el-form-item 
          label="所属角色" 
          prop="roles"
        >
          <el-select 
            style="width: 100%;"
            v-model="user_info.roles" 
            placeholder="请选择"
            multiple 
          >
            <el-option 
              v-for="item in role_list" 
              :key="item.id" 
              :label="item.name" 
              :value="item.id"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="数据访问" 
          prop="extra_accessible_orgs"
        >
          <el-select
            style="width: 100%;"
            v-model="user_info.extra_accessible_orgs"
            placeholder="请选择"
            multiple
          >
            <el-option
              v-for="item in org_list"
              :key="item.id"
              :value="item.id"
              :label="item.name"
              style="height:auto"
              hidden
            >
            </el-option>
            <el-input
              placeholder="输入关键字进行过滤"
              v-model="access_filter_text"
            >
            </el-input>
            <el-tree
              ref="allowTree"
              node-key="id"
              accordion
              show-checkbox
              default-expand-all
              :props="default_props"
              :data="org_tree"
              :check-strictly="false"
              :filter-node-method="filterNode"
              :expand-on-click-node="false"
              @check-change="onTreeCheckChange"
            />
          </el-select>
        </el-form-item>
        <el-form-item 
          label="是否启用"
          prop="is_active"
        >
          <el-switch v-model="user_info.is_active" />
        </el-form-item>
        <el-form-item 
          label="用户有效期" 
          prop="expires_at"
        >
          <el-date-picker 
            style="width: 100%;"
            v-model="user_info.expires_at" 
            placeholder="选择日期"
            type="datetime" 
            format="yyyy-MM-dd"
            value-format="yyyy-MM-dd HH:mm:ss"
          />
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
        @click="saveUserInfo" 
      >
        {{ user_info.id ? "更  新" : "保  存" }}
      </el-button>
    </div>
  </el-card>
</template>

<script>
import { 
  userMethod, 
  roleMethod,
  organizationMethod,
} from "@/api"

const initUserInfo = {
  organization_id: null,
  company_name: null,
  organization_name: null,
  engineer_name: null,
  username: null,
  password: null,
  email: null,
  phone: null,
  feishu_id: null,
  roles: [],
  extra_accessible_orgs: [],
  is_active: true,
  is_superuser: false, 
}

export default {
  name: "UserCreate",
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        title: "更新用户信息",
        mode: "create"
      })
    }
  },
  data() {
    // 密码校验
    const validatePassword = (rule, value, callback) => {
      if (!value) {
        callback(new Error("请输入初始密码"))
      } else if (value.length < 6) {
        callback(new Error("密码长度至少6位"))
      } else {
        callback()
      }
    }

    return {
      view_context: this.viewContext,
      user_info: structuredClone(initUserInfo),
      rules: {
        organization_id: [{ required: true, message: "请选择所属组织", trigger: "blur" }],
        username: [
          { required: true, message: "请输入登录用户名", trigger: "blur" },
          { 
            // 正则解释：
            // ^[a-zA-Z]          : 必须以字母开头
            // ([a-zA-Z0-9]|      : 中间可以是字母数字
            //  (?<![.@_-])       : 或者特殊符号，但前面不能紧挨着特殊符号（防止连续）
            //  [@._-]            : 特殊符号本身
            // )*                 : 中间部分重复0次或多次
            // [a-zA-Z0-9]$       : 必须以字母或数字结尾
            pattern: /^[a-zA-Z]([a-zA-Z0-9]|(?<![.@_-])[@._-])*[a-zA-Z0-9]$/, 
            message: "用户名必须以字母开头，仅支持字母、数字、_、-，且不能连续或出现在末尾",
            trigger: "blur"
          }
        ],
        password: [{ required: true, validator: validatePassword, trigger: "blur" }],
        engineer_name: [{ required: true, message: "请填入用户姓名", trigger: "blur" }],
        email: [
          { 
            type: "email", // Vue内置邮箱类型校验（简洁版）
            message: "请输入合法的电子邮箱格式", 
            trigger: "blur" 
          }
        ],
        phone: [
          { 
            pattern: /^1[3-9]\d{9}$/, 
            message: "请输入合法的11位手机号", 
            trigger: "blur" 
          }
        ],
        roles: [{ required: true, message: "请至少分配一个角色", trigger: "blur" }],
        extra_accessible_orgs: [{ required: true, message: "请至少分配一个组织用于数据访问", trigger: "blur" }],
      },
      feishu_id: [{ required: true, message: "请输入飞书ID", trigger: "blur" }],
      org_list: [],
      org_tree: [],
      role_list: [],
      belong_filter_text: "",
      access_filter_text: "",
      default_props: {
        children: "children",
        label: "name",
        id:"id",
      },
      access_org_ids: [1],
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
    belong_filter_text(val) {
      this.$refs.organizationTree.filter(val)
    },
    access_filter_text(val) {
      this.$refs.allowTree.filter(val)
    },
    "user_info.extra_accessible_orgs": function() {
      this.$refs.allowTree.setCheckedKeys(this.user_info.extra_accessible_orgs)
    }
  },
  created() {

  },
  methods: {
    handleUsernameInput(value) {
      const filtered = value.replace(/[^a-zA-Z0-9@._-]/g, "")
      this.user_info.username = filtered
    },
    async initializeView() {
      this.resetView()

      // 读取组织信息
      await this.getOrganizationInfo()

      // 读取角色信息
      await this.getRoleInfo()

      if (this.view_context.id) {
        // 通过弹出窗口进入界面
        this.user_info.id = this.view_context.id
      } else if (this.$route.query.id) {
        // 通过跳转进入界面
        this.user_info.id = Number(this.$route.query.id)
      }

      // 读取用户信息
      if (this.user_info.id) {
        await this.getUserInfo(this.user_info.id)
      }
    },
    async getOrganizationInfo() {
      this.org_list = []
      const res = await organizationMethod.get({})
      if (res.status === 0) {
        this.org_list = res.data.items
        this.constructViewModel()
      } 
    },
    async getRoleInfo() {
      this.role_list = []
      const res = await roleMethod.get({ page_no: 1, page_size: 1000 })
      if (res.status === 0) {
        this.role_list = res.data.items
      }
    },
    async getUserInfo(id) {
      if (!id) return

      const res = await userMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.user_info, res.data)
        // 获取角色信息
        this.user_info.roles = res.data.roles.map(r => r.id)
        // 获取数据访问权限信息
        this.user_info.extra_accessible_orgs = res.data.extra_accessible_orgs.map(r => r.id)
      }
    },
    constructChildren(parent) {
      // 构建子节点
      if (!parent.children) parent.children = []
      for (let i = 0; i < this.org_list.length; ++i) {
        let org_detail = this.org_list[i]
        if (org_detail.parent_id == parent.id) {
          let node = structuredClone(this.org_list[i])
          node.parent = parent
          parent.children.push(node)
          this.constructChildren(node)
        } 
      }

      parent.children.sort((a, b) => a.sort_order - b.sort_order )
    },
    constructViewModel() {
      // 构建一级节点
      let org_tree = []
      for (let i = 0; i < this.org_list.length; ++i) {
        let org_detail = this.org_list[i]
        if (org_detail.parent_id == null) {
          let node = structuredClone(this.org_list[i])
          org_tree.push(node)
          this.constructChildren(node)
        }
      }

      this.org_tree = org_tree
    },
    filterNode(value, data) {
      if (!value) return true
      if (!data.name) return false
      return data.name.indexOf(value) !== -1
    },
    handleNodeClick(data, node, el) {
      this.user_info.organization_id = data.id
      this.user_info.organization_name = data.name
      this.user_info.extra_accessible_orgs = [data.id]
    },
    onTreeCheckChange(data, checked, indeterminate) {

      // 获取所有已选中的节点
      const checked_nodes = this.$refs.allowTree.getCheckedNodes()
      const checked_keys = checked_nodes.map(node => node.id)

      // 筛选出可访问的权限节点
      const access_nodes = checked_nodes.filter(node => {
        let parent_key = node.parent_id
        while (parent_key !== null) {
          if (checked_keys.includes(parent_key)) {
            return false // 父级已选中，当前节点是子节点，过滤
          }
          parent_key = this.$refs.allowTree.getNode(parent_key).data.parent_id
        }
        return true // 无父级在选中列表，是顶级节点，保留
      })

      // 设置访问权限
      this.user_info.extra_accessible_orgs = access_nodes.map(node => node.id)
    },
    async saveUserInfo() {
      try {
        await this.$refs.form_info.validate() // 成功时 resolve，失败时 reject
      } catch (err) {
        return this.$message({ type: "error", message: "请填写完整信息！" })
      }
      
      if (this.user_info.id) {
        const res = await userMethod.edit(this.user_info, this.user_info.id)
        if (res.status === 0) {
          this.$message({ message: "编辑用户信息成功！", type: "success" })
          this.$emit("close")
        }
      } else {
        const res = await userMethod.add(this.user_info)
        if (res.status === 0) {
          this.$message({ message: "添加用户信息成功！", type: "success" })
          this.$router.push("/admin/user/list")
        }
      }
    },
    resetView() {
      this.user_info = structuredClone(initUserInfo)
    },
  }
}
</script>
<style lang="scss" scoped>
.el-card {
  max-width: 600px;
}
</style>