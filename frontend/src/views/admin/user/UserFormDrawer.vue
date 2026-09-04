<!--
  UserFormDrawer - 用户表单抽屉（一体化组件：el-drawer + el-form + 提交逻辑）
  - 使用方：v-model:visible 控制显示，:id 传编辑 id，@success 接收提交成功事件
  - 新建：必填 username + password
  - 编辑：username 只读
-->
<template>
  <el-drawer
    :model-value="visible"
    :title="isCreate ? '新增用户' : '编辑用户'"
    direction="rtl"
    size="560px"
    :close-on-click-modal="false"
    destroy-on-close
    @update:model-value="onVisibleChange"
  >
    <div class="drawer-body">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        label-position="right"
        v-loading="loading"
      >
    <el-form-item label="账号" prop="username">
      <el-input
        v-model="form.username"
        placeholder="登录账号"
        :disabled="!isCreate"
      />
    </el-form-item>

    <el-form-item v-if="isCreate" label="密码" prop="password">
      <el-input
        v-model="form.password"
        type="password"
        show-password
        placeholder="至少 8 位，包含字母和数字"
        autocomplete="new-password"
        :readonly="password_readonly"
        @focus="password_readonly = false"
      />
    </el-form-item>

    <el-form-item label="姓名" prop="engineer_name">
      <el-input v-model="form.engineer_name" placeholder="工程师姓名" />
    </el-form-item>

    <el-form-item label="邮箱" prop="email">
      <el-input v-model="form.email" placeholder="可选" />
    </el-form-item>

    <el-form-item label="电话" prop="phone">
      <el-input v-model="form.phone" placeholder="可选" />
    </el-form-item>

    <el-form-item label="所属组织" prop="organization_id">
      <el-tree-select
        v-model="form.organization_id"
        :data="organizations"
        :props="{ value: 'id', label: 'name', children: 'children' }"
        check-strictly
        :render-after-expand="false"
        default-expand-all
        placeholder="选择组织（支持搜索）"
        clearable
        filterable
        style="width: 100%;"
      />
    </el-form-item>

    <el-form-item label="角色" prop="roles">
      <el-select
        v-model="form.roles"
        placeholder="选择角色（可多选）"
        multiple
        collapse-tags
        collapse-tags-tooltip
        filterable
        style="width: 100%;"
      >
        <el-option
          v-for="role in roles"
          :key="role.id"
          :label="role.name"
          :value="role.id"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="租户管理员" prop="is_tenant_admin">
      <el-switch
        v-model="form.is_tenant_admin"
        active-text="是"
        inactive-text="否"
      />
    </el-form-item>
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
import { roleMethod, organizationMethod, userMethod, getOrganizationTree } from '@/api'

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

/**
 * 密码输入框 readonly 控制
 * - 初始为 true：避免 Chrome/Edge 等浏览器自动填充其他已保存的密码
 * - 用户 focus 时改为 false：允许实际输入
 * - 配合 autocomplete="new-password" 双重保险
 */
const password_readonly = ref(true)

const form = reactive({
  username: '',
  password: '',
  engineer_name: '',
  email: '',
  phone: '',
  organization_id: undefined as number | undefined,
  roles: [] as number[],
  is_tenant_admin: false,
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 32, message: '账号长度 3-32 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
  ],
  engineer_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
  ],
  email: [
    {
      validator: (_rule, value, callback) => {
        if (!value) return callback()
        const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
        callback(ok ? undefined : new Error('邮箱格式不正确'))
      },
      trigger: 'blur',
    },
  ],
}

// ============================================================================
// 选项数据
// ============================================================================

const organizations = ref<any[]>([])
const roles = ref<any[]>([])

/** 加载组织树（用于 el-tree-select） */
async function loadOrganizations() {
  try {
    const res: any = await getOrganizationTree()
    if (res.status === 0) {
      // 树形结构：根节点是公司根组织，包含 children
      organizations.value = res.data ? [res.data] : []
    }
  } catch (err) {
    console.error('[UserFormDrawer] loadOrganizations failed:', err)
  }
}

/** 加载角色列表 */
async function loadRoles() {
  try {
    const res: any = await roleMethod.get({ page_size: 1000 })
    if (res.status === 0) {
      roles.value = res.data.items || []
    }
  } catch (err) {
    console.error('[UserFormDrawer] loadRoles failed:', err)
  }
}

/** 加载用户详情（编辑模式） */
async function loadUserDetail(userId: number) {
  loading.value = true
  try {
    const res: any = await userMethod.getDetail(userId)
    if (res.status === 0) {
      const u = res.data
      Object.assign(form, {
        username: u.username || '',
        password: '',
        engineer_name: u.engineer_name || '',
        email: u.email || '',
        phone: u.phone || '',
        organization_id: u.organization_id || undefined,
        roles: u.roles || [],
        is_tenant_admin: !!u.is_tenant_admin,
      })
    } else {
      ElMessage.error(res.msg || '加载用户详情失败')
    }
  } catch (err) {
    console.error('[UserFormDrawer] loadUserDetail failed:', err)
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
    // 总是重新加载下拉选项
    await Promise.all([loadOrganizations(), loadRoles()])

    if (newId) {
      await loadUserDetail(newId)
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

/** 重置表单为新建默认值 */
function resetForm() {
  Object.assign(form, {
    username: '',
    password: '',
    engineer_name: '',
    email: '',
    phone: '',
    organization_id: undefined,
    roles: [],
    is_tenant_admin: false,
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
      engineer_name: form.engineer_name || null,
      email: form.email || null,
      phone: form.phone || null,
      organization_id: form.organization_id || null,
      roles: form.roles,
      is_tenant_admin: form.is_tenant_admin,
    }

    let res: any
    if (isCreate.value) {
      payload.username = form.username
      payload.password = form.password
      res = await userMethod.add(payload)
    } else {
      // 更新：username 不可改
      res = await userMethod.edit(payload, props.id!)
    }

    if (res.status === 0) {
      ElMessage.success(isCreate.value ? '创建成功' : '更新成功')
      emit('success')
      emit('update:visible', false)
    } else {
      ElMessage.error(res.msg || (isCreate.value ? '创建失败' : '更新失败'))
    }
  } catch (err) {
    console.error('[UserFormDrawer] submit failed:', err)
  } finally {
    submitting.value = false
  }
}
</script>