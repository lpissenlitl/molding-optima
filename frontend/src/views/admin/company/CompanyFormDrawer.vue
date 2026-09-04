<!--
  CompanyFormDrawer - 公司表单抽屉（一体化组件：el-drawer + el-form + 提交逻辑）
  - 使用方：v-model:visible 控制显示，:id 传编辑 id，@success 接收提交成功事件
  - 新建：必填公司信息 + 公司管理员账号（username + password）
  - 编辑：仅公司信息（admin_user 不在此处管理，统一在用户管理模块）
-->
<template>
  <el-drawer
    :model-value="visible"
    :title="isCreate ? '新增公司' : '编辑公司'"
    direction="rtl"
    size="640px"
    :close-on-click-modal="false"
    destroy-on-close
    @update:model-value="onVisibleChange"
  >
    <div class="drawer-body">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="right"
        v-loading="loading"
      >
    <div class="section-title">基本信息</div>

    <el-form-item label="公司名称" prop="name">
      <el-input
        v-model="form.name"
        placeholder="例如：明华精密注塑"
        maxlength="255"
        show-word-limit
      />
    </el-form-item>

    <el-form-item label="公司编码" prop="code">
      <el-input
        v-model="form.code"
        placeholder="小写字母+数字+下划线，例如：mh_precision"
        maxlength="30"
        :disabled="!isCreate"
      />
      <div v-if="!isCreate" class="field-tip">
        编码为公司唯一标识，保存后不可修改
      </div>
    </el-form-item>

    <el-form-item label="所属行业">
      <el-input
        v-model="form.industry"
        placeholder="例如：精密注塑、汽车零部件"
        maxlength="255"
      />
    </el-form-item>

    <el-form-item label="公司层级" prop="tier_level">
      <el-input-number
        v-model="form.tier_level"
        :min="1"
        :max="10"
        controls-position="right"
        style="width: 140px;"
      />
      <span class="field-tip" style="margin-left: 12px;">
        决定租户可用的权限范围（数值越大权限越多）
      </span>
    </el-form-item>

    <el-form-item label="过期时间">
      <el-date-picker
        v-model="form.expires_at"
        type="datetime"
        placeholder="选择过期时间（可选）"
        format="YYYY-MM-DD HH:mm:ss"
        value-format="YYYY-MM-DD HH:mm:ss"
        style="width: 100%;"
      />
    </el-form-item>

    <el-form-item label="公司描述">
      <el-input
        v-model="form.description"
        type="textarea"
        :rows="2"
        placeholder="可选，公司主营业务或备注"
        maxlength="512"
        show-word-limit
      />
    </el-form-item>

    <el-form-item label="是否启用">
      <el-switch
        v-model="form.is_active"
        active-text="启用"
        inactive-text="禁用"
      />
    </el-form-item>

    <!-- 创建时才需要：公司管理员子表单 -->
    <template v-if="isCreate">
      <div class="section-title">公司管理员</div>
      <div class="section-tip">
        创建公司时需指定初始管理员账号，该账号将自动拥有该公司层级内的全部权限。
        创建后可在「用户管理」模块维护。
      </div>

      <el-form-item label="账号" prop="admin_user.username">
        <el-input
          v-model="form.admin_user.username"
          placeholder="登录账号"
          maxlength="50"
          autocomplete="off"
          :readonly="readonly"
          @focus="readonly = false"
        />
      </el-form-item>

      <el-form-item label="邮箱" prop="admin_user.email">
        <el-input
          v-model="form.admin_user.email"
          placeholder="可选"
          autocomplete="off"
        />
      </el-form-item>

      <el-form-item label="密码" prop="admin_user.password">
        <el-input
          v-model="form.admin_user.password"
          type="password"
          show-password
          placeholder="至少 8 位"
          autocomplete="new-password"
          :readonly="readonly"
          @focus="readonly = false"
        />
      </el-form-item>

      <el-form-item label="确认密码" prop="admin_user.confirm_password">
        <el-input
          v-model="form.admin_user.confirm_password"
          type="password"
          show-password
          placeholder="再次输入密码"
          autocomplete="new-password"
          :readonly="readonly"
          @focus="readonly = false"
        />
      </el-form-item>
    </template>
    </el-form>
    </div>

    <template #footer>
      <el-button @click="onVisibleChange(false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { companyMethod } from '@/api'

// ============================================================================
// Props / Emits
// ============================================================================

interface Props {
  visible: boolean
  /** 编辑时传 id，null/undefined 表示创建模式 */
  id?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  id: null,
})

const emit = defineEmits<{
  'update:visible': [val: boolean]
  success: []
}>()

/** 是否为创建模式：id 为空 = 创建 */
const isCreate = computed(() => !props.id)

/** 同步可见性给外部 */
function onVisibleChange(val: boolean) {
  emit('update:visible', val)
}

// ============================================================================
// 表单数据
// ============================================================================

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const readonly = ref(true)

interface AdminUser {
  username: string
  email: string
  password: string
  confirm_password: string
}

const form = reactive({
  name: '',
  code: '',
  industry: '',
  description: '',
  tier_level: 1,
  expires_at: '' as string,
  is_active: true,
  admin_user: {
    username: '',
    email: '',
    password: '',
    confirm_password: '',
  } as AdminUser,
})

// 二次密码校验（confirm_password == password）
const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.admin_user.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  name: [
    { required: true, message: '请输入公司名称', trigger: 'blur' },
    { min: 1, max: 255, message: '公司名称长度 1-255', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入公司编码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (!value) return callback()
        const ok = /^[a-z][a-z0-9_]*$/.test(value)
        callback(ok ? undefined : new Error('编码格式：小写字母开头，仅含小写字母/数字/下划线'))
      },
      trigger: 'blur',
    },
  ],
  tier_level: [
    { required: true, message: '请设置公司层级', trigger: 'blur' },
  ],
  // admin_user（仅创建时）
  'admin_user.username': [
    { required: true, message: '请输入管理员账号', trigger: 'blur' },
    { min: 3, max: 50, message: '账号长度 3-50', trigger: 'blur' },
  ],
  'admin_user.email': [
    {
      validator: (_rule, value, callback) => {
        if (!value) return callback()
        const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
        callback(ok ? undefined : new Error('邮箱格式不正确'))
      },
      trigger: 'blur',
    },
  ],
  'admin_user.password': [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
  ],
  'admin_user.confirm_password': [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// ============================================================================
// 详情加载（编辑模式）
// ============================================================================

async function loadCompanyInfo(companyId: number) {
  loading.value = true
  try {
    const res: any = await companyMethod.getDetail(companyId)
    if (res.status === 0) {
      const c = res.data
      Object.assign(form, {
        name: c.name || '',
        code: c.code || '',
        industry: c.industry || '',
        description: c.description || '',
        tier_level: c.tier_level ?? 1,
        expires_at: c.expires_at || '',
        is_active: c.is_active !== false,
      })
    } else {
      ElMessage.error(res.msg || '加载公司详情失败')
    }
  } catch (err) {
    console.error('[CompanyFormDrawer] loadCompanyInfo failed:', err)
  } finally {
    loading.value = false
  }
}

// ============================================================================
// 生命周期 + 模式切换
// ============================================================================

/** id 变化时重新初始化（外部切换 create/edit 模式） */
watch(
  () => props.id,
  async (newId) => {
    if (newId) {
      await loadCompanyInfo(newId)
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

/** drawer 重新打开时重置 readonly（防止 Chrome 自动填充） */
watch(
  () => props.visible,
  (val) => {
    if (val) {
      readonly.value = true
    }
  }
)

function resetForm() {
  Object.assign(form, {
    name: '',
    code: '',
    industry: '',
    description: '',
    tier_level: 1,
    expires_at: '',
    is_active: true,
    admin_user: {
      username: '',
      email: '',
      password: '',
      confirm_password: '',
    },
  })
  formRef.value?.clearValidate()
}

// ============================================================================
/** 提交表单 */
async function submit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const payload: any = {
      name: form.name,
      code: form.code,
      industry: form.industry || null,
      description: form.description || null,
      tier_level: form.tier_level,
      expires_at: form.expires_at || null,
      is_active: form.is_active,
    }

    let res: any
    if (isCreate.value) {
      // 创建：必填 admin_user
      payload.admin_user = {
        username: form.admin_user.username,
        email: form.admin_user.email || null,
        password: form.admin_user.password,
        confirm_password: form.admin_user.confirm_password,
      }
      res = await companyMethod.add(payload)
    } else {
      res = await companyMethod.edit(payload, props.id!)
    }

    if (res.status === 0) {
      ElMessage.success(isCreate.value ? '创建成功' : '更新成功')
      emit('success')
      emit('update:visible', false)
    } else {
      ElMessage.error(res.msg || (isCreate.value ? '创建失败' : '更新失败'))
    }
  } catch (err) {
    console.error('[CompanyFormDrawer] submit failed:', err)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 8px 0 12px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}

.section-title:not(:first-child) {
  margin-top: 24px;
}

.section-tip {
  font-size: 12px;
  color: #909399;
  background-color: #f4f4f5;
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 16px;
  line-height: 1.6;
}

.field-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}
</style>
