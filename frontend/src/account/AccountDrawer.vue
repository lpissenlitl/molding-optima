<!--
  AccountDrawer - 账户中心
  - 顶部：头像 + 用户名 + 角色标签
  - 三个区块：个人信息（可编辑）/ 修改密码 / 账户信息（只读）
  - 底部：退出登录

  数据：
  - GET  /api/profile/              → getInfoApi()
  - PUT  /api/profile/              → updateProfileApi() (只能改 engineer_name/email/phone)
  - PUT  /api/profile/reset-password/ → userStore.updatePassword() (改密后会自动注销)

  注意事项：
  - username/role 不可改（后端白名单）
  - 改密码成功后必须跳回 /login（后端会注销所有 token）
-->
<template>
  <el-drawer
    v-model="visible"
    title="账户中心"
    direction="rtl"
    size="480px"
    :with-header="true"
    :close-on-click-modal="false"
    :destroy-on-close="false"
  >
    <div v-loading="loading" class="account">
      <!-- ============== 顶部：头像 + 用户名 + 角色 ============== -->
      <header class="account__header">
        <el-avatar :size="56" class="account__avatar">
          {{ avatarText }}
        </el-avatar>
        <div class="account__identity">
          <div class="account__name">
            {{ userStore.engineer_name || userStore.username }}
          </div>
          <div class="account__username">
            @{{ userStore.username || '未登录' }}
          </div>
          <div class="account__roles">
            <el-tag
              v-for="role in roleBadges"
              :key="role.code"
              :type="role.type"
              size="small"
              effect="light"
            >
              {{ role.label }}
            </el-tag>
          </div>
        </div>
      </header>

      <el-divider />

      <!-- ============== 区块 1：个人信息 ============== -->
      <section class="account__section">
        <h4 class="account__title">
          <AppIcon icon="mdi:account-outline" class="account__title-icon" />
          个人信息
        </h4>

        <el-form
          ref="profileFormRef"
          :model="profileForm"
          :rules="profileRules"
          label-position="top"
          size="default"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              :model-value="userStore.username"
              disabled
              placeholder="不可修改"
            />
          </el-form-item>

          <el-form-item label="工程师姓名" prop="engineer_name">
            <el-input
              v-model="profileForm.engineer_name"
              placeholder="请输入姓名"
              maxlength="50"
              clearable
            />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="profileForm.email"
              placeholder="example@domain.com"
              clearable
            />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="profileForm.phone"
              placeholder="11 位手机号"
              maxlength="11"
              clearable
            />
          </el-form-item>

          <el-form-item label="所属公司">
            <el-input :model-value="userStore.company_name || '—'" disabled />
          </el-form-item>

          <el-form-item label="所属组织">
            <el-input :model-value="userStore.organization_name || '—'" disabled />
          </el-form-item>
        </el-form>

        <div class="account__actions">
          <el-button
            type="primary"
            :loading="profileSaving"
            @click="saveProfile"
          >
            <AppIcon icon="mdi:content-save-outline" />
            保存修改
          </el-button>
        </div>
      </section>

      <el-divider />

      <!-- ============== 区块 2：修改密码 ============== -->
      <section class="account__section">
        <h4 class="account__title">
          <AppIcon icon="mdi:lock-outline" class="account__title-icon" />
          修改密码
        </h4>
        <p class="account__hint">修改成功后会自动退出登录，请用新密码重新登录</p>

        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-position="top"
          size="default"
        >
          <el-form-item label="旧密码" prop="old_password">
            <el-input
              v-model="passwordForm.old_password"
              type="password"
              placeholder="请输入当前密码"
              show-password
              autocomplete="current-password"
            />
          </el-form-item>

          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              placeholder="至少 8 位，含字母与数字"
              show-password
              autocomplete="new-password"
            />
          </el-form-item>

          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              placeholder="再次输入新密码"
              show-password
              autocomplete="new-password"
            />
          </el-form-item>
        </el-form>

        <div class="account__actions">
          <el-button
            type="warning"
            :loading="passwordSaving"
            @click="savePassword"
          >
            <AppIcon icon="mdi:shield-key-outline" />
            保存密码
          </el-button>
        </div>
      </section>

      <el-divider />

      <!-- ============== 区块 3：账户信息（只读） ============== -->
      <section class="account__section">
        <h4 class="account__title">
          <AppIcon icon="mdi:information-outline" class="account__title-icon" />
          账户信息
        </h4>

        <dl class="account__meta">
          <div class="account__meta-row">
            <dt>登录次数</dt>
            <dd>{{ userStore.login_count ?? '—' }}</dd>
          </div>
          <div class="account__meta-row">
            <dt>最后登录</dt>
            <dd>{{ formatDate(userStore.last_login_at) || '—' }}</dd>
          </div>
          <div class="account__meta-row">
            <dt>账户有效期</dt>
            <dd>
              <el-tag
                v-if="expiresAtExpired"
                type="danger"
                size="small"
              >已过期</el-tag>
              <el-tag
                v-else-if="expiresAtSoon"
                type="warning"
                size="small"
              >即将过期</el-tag>
              <span v-else>{{ formatDate(userStore.expires_at) || '长期有效' }}</span>
            </dd>
          </div>
          <div class="account__meta-row">
            <dt>Token 过期</dt>
            <dd>{{ formatDate(userStore.token_expires_at) || '—' }}</dd>
          </div>
        </dl>
      </section>

      <el-divider />

      <!-- ============== 退出登录 ============== -->
      <section class="account__section account__logout">
        <el-button
          type="danger"
          plain
          class="account__logout-btn"
          @click="handleLogout"
        >
          <AppIcon icon="mdi:logout" />
          退出登录
        </el-button>
      </section>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

// ============================================================================
// Props / Emits
// ============================================================================

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})

// ============================================================================
// 状态
// ============================================================================

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const profileSaving = ref(false)
const passwordSaving = ref(false)

// 表单：个人信息
const profileFormRef = ref<FormInstance>()
const profileForm = reactive({
  engineer_name: '',
  email: '',
  phone: '',
})

// 表单：修改密码
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

// ============================================================================
// 派生
// ============================================================================

/** 头像首字母（中文取末字首字母，英文取首字母） */
const avatarText = computed(() => {
  const name = userStore.engineer_name || userStore.username || '?'
  // 取最后一个字符（中文常用名是 2-3 字）
  return name.charAt(name.length - 1).toUpperCase()
})

/** 角色标签列表（按角色优先级排序） */
const roleBadges = computed(() => {
  const badges: Array<{ code: string; type: 'danger' | 'warning' | 'info' | 'success'; label: string }> = []
  if (userStore.is_superuser) {
    badges.push({ code: 'superuser', type: 'danger', label: '超级管理员' })
  }
  if (userStore.is_tenant_admin) {
    badges.push({ code: 'tenant_admin', type: 'warning', label: '租户管理员' })
  }
  if (userStore.is_staff) {
    badges.push({ code: 'staff', type: 'info', label: '员工' })
  }
  if (badges.length === 0) {
    badges.push({ code: 'normal', type: 'success', label: '普通用户' })
  }
  return badges
})

/** 账户有效期：是否已过期 */
const expiresAtExpired = computed(() => {
  if (!userStore.expires_at) return false
  return new Date(userStore.expires_at).getTime() < Date.now()
})

/** 账户有效期：30 天内即将过期 */
const expiresAtSoon = computed(() => {
  if (!userStore.expires_at) return false
  const ts = new Date(userStore.expires_at).getTime()
  return ts >= Date.now() && ts - Date.now() < 30 * 24 * 60 * 60 * 1000
})

// ============================================================================
// 表单规则
// ============================================================================

const profileRules: FormRules = {
  engineer_name: [
    { max: 50, message: '姓名最多 50 个字符', trigger: 'blur' },
  ],
  email: [
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
      trigger: ['blur', 'change'],
    },
  ],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的 11 位手机号',
      trigger: ['blur', 'change'],
    },
  ],
}

const validateConfirmPassword = (_rule: unknown, value: string, callback: (err?: Error) => void) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
    {
      pattern: /[A-Za-z]/,
      message: '密码必须包含字母',
      trigger: 'blur',
    },
    {
      pattern: /\d/,
      message: '密码必须包含数字',
      trigger: 'blur',
    },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// ============================================================================
// 副作用：抽屉打开时刷新数据
// ============================================================================

watch(visible, async (open) => {
  if (!open) return
  await loadProfile()
})

async function loadProfile() {
  loading.value = true
  try {
    await userStore.fetchInfo()
    // 把 store 的值同步到本地 form（store fetchInfo 已 applyUser）
    profileForm.engineer_name = userStore.engineer_name || ''
    profileForm.email = userStore.email || ''
    profileForm.phone = userStore.phone || ''
  } catch (err) {
    // 拦截器已提示
    console.error('[AccountDrawer] loadProfile failed:', err)
  } finally {
    loading.value = false
  }
}

// ============================================================================
// 动作：保存个人信息
// ============================================================================

async function saveProfile() {
  if (!profileFormRef.value) return
  try {
    await profileFormRef.value.validate()
  } catch {
    return // 校验失败，Element Plus 已提示
  }

  profileSaving.value = true
  try {
    await request({
      url: '/api/profile/',
      method: 'put',
      data: {
        engineer_name: profileForm.engineer_name || null,
        email: profileForm.email || null,
        phone: profileForm.phone || null,
      },
    })
    // 刷新 store 拿到最新值
    await userStore.fetchInfo()
    ElMessage.success('个人信息已更新')
  } catch (err) {
    // 拦截器已提示
    console.error('[AccountDrawer] saveProfile failed:', err)
  } finally {
    profileSaving.value = false
  }
}

// ============================================================================
// 动作：修改密码
// ============================================================================

async function savePassword() {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }

  passwordSaving.value = true
  try {
    await userStore.updatePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码已修改，请重新登录')
    // 后端会注销所有 token，必须清状态 + 跳登录页
    userStore.clear()
    visible.value = false
    router.push('/login')
  } catch (err) {
    console.error('[AccountDrawer] savePassword failed:', err)
  } finally {
    passwordSaving.value = false
  }
}

// ============================================================================
// 动作：退出登录
// ============================================================================

async function handleLogout() {
  try {
    await userStore.logout()
  } catch {
    // 即便后端调用失败也清本地（用户体验优先）
  }
  userStore.clear()
  visible.value = false
  router.push('/login')
}

// ============================================================================
// 工具
// ============================================================================

function formatDate(iso?: string): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return iso
  }
}
</script>

<style scoped lang="scss">
.account {
  padding: 0 4px 24px;

  // ─────────── 顶部 ───────────
  &__header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 8px 0;
  }

  &__avatar {
    background: var(--theme-primary, #254373);
    color: #fff;
    font-size: 22px;
    font-weight: 600;
    flex-shrink: 0;
  }

  &__identity {
    flex: 1;
    min-width: 0;
  }

  &__name {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.4;
  }

  &__username {
    font-size: 13px;
    color: var(--color-text-secondary);
    line-height: 1.6;
    margin-top: 2px;
  }

  &__roles {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  // ─────────── 区块 ───────────
  &__section {
    padding: 8px 0;
  }

  &__title {
    display: flex;
    align-items: center;
    margin: 0 0 12px;
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text-primary);

    &-icon {
      margin-right: 6px;
      font-size: 18px;
      color: var(--theme-primary, #254373);
    }
  }

  &__hint {
    margin: -8px 0 12px;
    font-size: 12px;
    color: var(--color-text-secondary);
  }

  &__actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  // ─────────── 账户信息（只读 dl） ───────────
  &__meta {
    margin: 0;
    padding: 0;
  }

  &__meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px dashed var(--color-border-light, #ebeef5);

    &:last-child {
      border-bottom: none;
    }

    dt {
      font-size: 13px;
      color: var(--color-text-secondary);
      margin: 0;
    }

    dd {
      font-size: 13px;
      color: var(--color-text-primary);
      margin: 0;
      text-align: right;
    }
  }

  // ─────────── 退出登录 ───────────
  &__logout {
    text-align: center;
  }

  &__logout-btn {
    width: 100%;
    max-width: 240px;
  }
}
</style>