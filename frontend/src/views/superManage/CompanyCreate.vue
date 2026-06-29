<template>
  <el-card class="box-card">
    <!-- 企业基本信息 -->
    <div>
      <h3>
        企业信息
      </h3>
      <el-form 
        ref="form_info" 
        :model="company_info" 
        :rules="rules" 
        size="mini"
        label-width="6rem"
        label-position="right"
      >
        <el-form-item 
          label="公司名称" 
          prop="name"
        >
          <el-input
            style="width: 100%;"
            v-model.trim="company_info.name" 
            placeholder="请输入公司全称"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="公司编码" 
          prop="code"
        >
          <el-input 
            style="width: 100%;"
            v-model.trim="company_info.code" 
            placeholder="唯一标识，如 COM_001"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="所属行业" 
          prop="industry"
        >
          <el-input 
            style="width: 100%;"
            v-model.trim="company_info.industry" 
            placeholder="如：模具制造、"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="公司描述" 
          prop="description"
        >
          <el-input 
            style="width: 100%;"
            v-model="company_info.description"
            type="textarea" 
            :autosize="{ minRows: 2, maxRows: 4}" 
            placeholder="简要描述公司业务"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="权限等级" 
          prop="tier_level"
        >
          <el-select 
            style="width: 100%;"
            v-model="company_info.tier_level" 
            placeholder="请选择权限等级"
          >
            <el-option 
              v-for="item in tier_levels" 
              :key="item.value" 
              :label="item.label" 
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item 
          label="是否启用" 
          prop="is_active"
        >
          <el-switch v-model="company_info.is_active"></el-switch>
        </el-form-item>
        <el-form-item 
          label="公司有效期" 
          prop="expires_at"
        >
          <el-date-picker 
            style="width: 100%;"
            v-model="company_info.expires_at" 
            placeholder="选择日期"
            type="datetime" 
            format="yyyy-MM-dd"
            value-format="yyyy-MM-dd HH:mm:ss"
          />
        </el-form-item>
      </el-form>
    </div>

    <!-- 管理员账号信息（仅创建时显示） -->
    <div v-if="!company_info.id">
      <h3>
        管理员账号
      </h3>
      <el-form
        ref="admin_form"
        :model="admin_info"
        :rules="admin_rules"
        size="mini"
        label-width="6rem"
        label-position="right"
      >
        <el-form-item 
          label="用户名" 
          prop="username"
        >
          <el-input 
            style="width: 100%;"
            v-model.trim="admin_info.username" 
            @input="handleUsernameInput"
            placeholder="管理员登录账号"
          />
        </el-form-item>
        <el-form-item 
          label="邮箱" 
          prop="email"
        >
          <el-input 
            style="width: 100%;"
            v-model.trim="admin_info.email" 
            type="email"
            placeholder="用于接收系统通知"
          />
        </el-form-item>
        <el-form-item 
          label="初始密码" 
          prop="password"
        >
          <el-input 
            style="width: 100%;"
            type="text"
            :class="{ 'password-masked': is_password_masked }"
            v-model="admin_info.password"
            oninput="value=value.replace(/[^A-Z0-9a-z!@#$%.]/g, '')"
            placeholder="请输入密码"
            auto-complete="new-password"
          >
            <template #suffix>
              <span class="password-toggle" @click="togglePasswordVisibility">
                <svg-icon 
                  :name="is_password_masked ? 'eye-off' : 'eye-on'"
                  style="width: 11px; height: 11px; margin: 0 6px;"
                />
              </span>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="确认密码" 
          prop="confirm_password"
        >
          <el-input 
            style="width: 100%;"
            type="text"
            :class="{ 'password-masked': is_password_masked }"
            v-model="admin_info.confirm_password"
            oninput="value=value.replace(/[^A-Z0-9a-z!@#$%.]/g, '')"
            placeholder="请再次输入密码"
            auto-complete="new-password"
          >
            <template #suffix>
              <span class="password-toggle" @click="togglePasswordVisibility">
                <svg-icon 
                  :name="is_password_masked ? 'eye-off' : 'eye-on'"
                  style="width: 11px; height: 11px; margin: 0 6px;"
                />
              </span>
            </template>
          </el-input>
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
        @click="saveCompanyInfo" 
      >
        {{ company_info.id ? "更 新" : "保 存" }}
      </el-button>
    </div>
  </el-card>
</template>

<script>
import { companyMethod } from "@/api"

const initCompanyInfo = {
  id: null,
  name: null,
  code: null,
  industry: null,
  description: null,
  tier_level: 1,
  is_active: true,
  expires_at: null,
}

const initAdminInfo = {
  username: null,
  email: null,
  password: null,
  confirm_password: null,
}

export default {
  name: "CompanyCreate",
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        title: "更新公司信息",
        mode: "create"
      })
    },
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
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.admin_info.password) {
        callback(new Error("两次密码不一致"))
      } else {
        callback()
      }
    }

    return {
      view_context: this.viewContext,
      company_info: structuredClone(initCompanyInfo),
      admin_info: structuredClone(initAdminInfo),
      pwd_type: "password",
      is_password_masked: true,
      tier_levels: [
        { label: "基础版", value: 1 },
        { label: "标准版", value: 2 },
        { label: "高级版", value: 3 },
        { label: "企业版", value: 4 }
      ],
      rules: {
        name: [{ required: true, message: "请输入公司名称", trigger: "blur" }],
        code: [{ required: true, message: "请输入公司编码", trigger: "blur" }],
        industry: [{ required: true, message: "请输入所属行业", trigger: "blur" }],
        tier_level: [{ required: true, message: "请选择公司权限等级", trigger: "change" }]
      },
      admin_rules: {
        username: [
          { required: true, message: "请输入管理员用户名", trigger: "blur" },
          { 
            pattern: /^[a-zA-Z][a-zA-Z0-9_-]{2,19}$/, 
            message: "用户名必须以字母开头，仅支持字母、数字、_、-，长度3-20位",
            trigger: "blur"
          }
        ],
        // email: [
        //   { required: true, message: "请输入邮箱", trigger: "blur" },
        //   { type: "email", message: "请输入正确邮箱格式", trigger: "blur" }
        // ],
        password: [{ validator: validatePassword, trigger: "blur" }],
        confirm_password: [{ validator: validateConfirmPassword, trigger: "blur" }]
      }
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
    handleUsernameInput(value) {
      // 只保留字母、数字、下划线、短横线
      const filtered = value.replace(/[^a-zA-Z0-9_-]/g, "")
      this.admin_info.username = filtered
    },
    togglePasswordVisibility() {
      this.is_password_masked = !this.is_password_masked
    },
    async initializeView() {
      this.resetView()

      if (this.view_context.id) {
        this.company_info.id = this.view_context.id
      }

      if (this.company_info.id) {
        await this.getCompanyInfo(this.company_info.id)
      }
    },
    async getCompanyInfo(id) {
      if (!id) return

      // 获取公司信息
      const res = await companyMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.company_info, res.data)
      }
    },
    async saveCompanyInfo() {
      try {
        
        // 验证表单
        await this.$refs.form_info.validate()

        if (!this.company_info.id) {
        // 验证管理员信息
          await this.$refs.admin_form.validate()
        }

        if (this.company_info.id) {
        // 修改公司信息
          const res = await companyMethod.edit(this.company_info, this.company_info.id)
          if (res.status === 0) {
            this.$message({ message: "更新公司信息成功!", type: "success" })
            this.$emit("close")
          }
        } else {
        // 新增公司信息
          this.company_info.admin_user = this.admin_info
          const res = await companyMethod.add(this.company_info)
          if (res.status === 0) {
            this.$message({ message: "新增公司信息成功!", type: "success" })
            this.$router.push("/admin/company/list")
          }
        }

      } catch (error) {
        this.$message({ message: "公司信息保存失败!", type: "warning" })
        return
      }
    },
    resetView() {
      this.company_info = structuredClone(initCompanyInfo)
      this.admin_info = structuredClone(initAdminInfo)
      this.is_password_masked = true
    }
  }
}
</script>

<style lang="scss" scoped>
.el-card {
  max-width: 600px;
}

.password-masked {
  -webkit-text-security: disc;
  user-select: none;
}
</style>
